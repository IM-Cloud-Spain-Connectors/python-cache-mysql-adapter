#
# This file is part of the Ingram Micro CloudBlue RnD Integration Connectors SDK.
#
# Copyright (c) 2023 Ingram Micro. All Rights Reserved.
#
import time
from typing import Any, Optional

import jsonpickle
from mysql.connector import connect, connection, IntegrityError
from rndi.cache.contracts import Cache


def provide_mysql_cache_adapter(config: dict) -> Cache:
    return MySQLCacheAdapter(
        host=config.get('CACHE_MYSQL_HOST', 'localhost'),
        database_name=config.get('CACHE_MYSQL_DATABASE', 'cache'),
        user_name=config.get('CACHE_MYSQL_USER', 'username'),
        password=config.get('CACHE_MYSQL_PASSWORD', 'password'),
    )


class MySQLCacheAdapter(Cache):
    _connection = None

    _create_sql = (
        'CREATE TABLE IF NOT EXISTS `entries`('
        '`key` VARCHAR(30) NOT NULL, '
        '`value` VARCHAR(30), '
        '`expire_at` INTEGER, '
        'PRIMARY KEY (`key`))'
    )
    _create = (
        'create table if not exists entries (`key` varchar(255) primary key,'
        ' value varchar(255), expire_at integer)'
    )
    _create_index = 'ALTER TABLE `entries` ADD INDEX (`key`)'

    _get_sql = 'SELECT value, expire_at FROM entries WHERE `key` = %s'
    _del_sql = 'DELETE FROM entries WHERE `key` = %s'
    _del_expired_sql = 'DELETE FROM entries WHERE %s >= expire_at'
    _insert_sql = 'INSERT INTO `entries` (`key`, `value`, `expire_at`) VALUES (%s, %s, %s)'
    _clear_sql = 'DELETE FROM entries'
    _replace_sql = 'REPLACE INTO `entries` (`key`, `value`, `expire_at`) VALUES (%s, %s, %s)'

    def __init__(
            self,
            host: str,
            database_name: str,
            user_name: str,
            password: str,
            ttl: int = 900,
            port: int = 3306,
    ):
        self.database_name = database_name
        self.user_name = user_name
        self.password = password
        self.host = host
        self.ttl = ttl
        self.port = port

    @property
    def connection(self) -> connection:
        """
        Returns the Connection object.
        :return: connection
        """
        if self._connection:
            return self._connection

        new_connection = connect(
            host=self.host,
            database=self.database_name,
            user=self.user_name,
            password=self.password,
            port=self.port,
        )

        cur = new_connection.cursor()
        cur.execute(self._create)
        cur.execute(self._create_index)

        self._connection = new_connection

        return self._connection

    def has(self, key: str) -> bool:
        return self.get(key) is not None

    def get(self, key: str, default: Any = None, ttl: Optional[int] = None) -> Any:
        try:
            cur = self.connection.cursor()
            cur.execute(self._get_sql, (key,))
            row = cur.fetchone()
            if row is None:
                raise StopIteration

            # entry[1] is the expire_at column, if the current time is greater than the expire_at
            # then delete the entry because it is expired.
            if round(time.time()) >= row[1]:
                cur.execute(self._del_sql, (key,))
                raise StopIteration

            if ttl is not None:
                cur.execute(self._replace_sql, (key, row[0], ttl + round(time.time())))

            return jsonpickle.decode(row[0])
        except StopIteration:
            ttl = self.ttl
            value = default() if callable(default) else default

            if isinstance(value, tuple):
                value, ttl = value

        return value if value is None else self.put(key, value, ttl)

    def put(self, key: str, value: Any, ttl: Optional[int] = None) -> Any:
        serialized = jsonpickle.encode(value)
        expire_at = (self.ttl if ttl is None else ttl) + round(time.time())

        cursor = self.connection.cursor()

        try:
            cursor.execute(self._insert_sql, (key, serialized, expire_at))
        except IntegrityError:
            cursor.execute(self._replace_sql, (key, serialized, expire_at))

        return value

    def delete(self, key: str) -> None:
        cursor = self.connection.cursor()
        cursor.execute(self._del_sql, (key,))

    def flush(self, expired_only: bool = False) -> None:
        cursor = self.connection.cursor()
        if expired_only:
            cursor.execute(self._del_expired_sql, (round(time.time()),))
        else:
            cursor.execute(self._clear_sql, ())

    def __del__(self):
        if self.connection:
            self.connection.close()
