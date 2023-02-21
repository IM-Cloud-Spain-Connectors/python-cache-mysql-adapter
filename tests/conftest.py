#
# This file is part of the Ingram Micro CloudBlue RnD Integration Connectors SDK.
#
# Copyright (c) 2023 Ingram Micro. All Rights Reserved.
#
from __future__ import annotations

from abc import ABCMeta, abstractmethod
from logging import LoggerAdapter
from typing import Dict, List, Optional, Union
from unittest.mock import patch

import pytest
from rndi.cache.adapters.mysql.adapter import MySQLCacheAdapter
from rndi.cache.contracts import Cache
from rndi.cache.provider import provide_cache


@pytest.fixture
def adapters(logger):
    def __adapters() -> List[Union[Cache, HasEntry]]:
        setups = [
            {
                'CACHE_DRIVER': 'mysql',
                'CACHE_MYSQL_HOST': 'localhost',
                'CACHE_MYSQL_DATABASE': 'cache',
                'CACHE_MYSQL_USER': 'username',
                'CACHE_MYSQL_PASSWORD': 'password',
            },
        ]

        extra = {
            'mysql': provide_test_mysql_cache_adapter,
        }

        return [provide_cache(setup, logger(), extra) for setup in setups]

    return __adapters


@pytest.fixture()
def logger():
    def __logger() -> LoggerAdapter:
        with patch('logging.LoggerAdapter') as logger:
            return logger

    return __logger


@pytest.fixture
def counter():
    class Counter:
        instance: Optional[Counter] = None

        def __init__(self):
            self.count = 0

        @classmethod
        def make(cls, reset: bool = False) -> Counter:
            if not isinstance(cls.instance, Counter) or reset:
                cls.instance = Counter()
            return cls.instance

        def increase(self, step: int = 1) -> Counter:
            self.count = self.count + step
            return self

    def __(reset: bool = False) -> Counter:
        return Counter.make(reset)

    return __


class HasEntry(metaclass=ABCMeta):  # pragma: no cover
    @abstractmethod
    def get_entry(self, key: str) -> Optional[Dict[str, Union[str, int]]]:
        """
        Get an entry from the cache, not only the value.
        This is useful for testing purposes when we want to validate the TTL.
        :param key: str The key to search for.
        :return: Optional[Dict[str, Union[str, int]]] The entry if found, None otherwise.
        """


class MySQLCacheAdapterTester(MySQLCacheAdapter, HasEntry):
    def get_entry(self, key: str) -> Optional[Dict[str, Union[str, int]]]:
        cur = self.connection.cursor()
        cur.execute(self._get_sql, (key,))
        entry = cur.fetchone()
        if entry is None:
            return None

        return {
            'value': entry[0],
            'expire_at': entry[1],
        }


def provide_test_mysql_cache_adapter(config: dict) -> Cache:
    return MySQLCacheAdapterTester(
        host=config.get('CACHE_MYSQL_HOST', 'localhost'),
        database_name=config.get('CACHE_MYSQL_DATABASE', 'cache'),
        user_name=config.get('CACHE_MYSQL_USER', 'username'),
        password=config.get('CACHE_MYSQL_PASSWORD', 'password'),
    )
