# Python Cache MySQL Adapter

[![Test and Analysis](https://github.com/othercodes/python-cache-mysql-adapter/actions/workflows/test.yml/badge.svg)](https://github.com/othercodes/python-cache-mysql-adapter/actions/workflows/test.yml)

Provides a MySQL implementation of the Cache Interface for Python.

## Installation

The easiest way to install the Cache MySQL Adapter is to get the latest version from PyPI:

```bash
# using poetry
poetry add rndi-cache-mysql-adapter
# using pip
pip install rndi-cache-mysql-adapter
```

## The Contract

The used interface is `rndi.cache.contracts.Cache`.

## The Adapter

Just initialize the class you want and use the public methods:

```python
from rndi.cache.contracts import Cache
from rndi.cache.adapters.mysql.adapter import MySQLCacheAdapter


def some_process_that_requires_cache(cache: Cache):
    # retrieve the data from cache, ir the key is not cached yet and the default 
    # value is a callable the cache will use it to compute and cache the value
    user = cache.get('user-id', lambda: db_get_user('user-id'))

    print(user)


# inject the desired cache adapter.
cache = MySQLCacheAdapter(
    'localhost',
    'database_name',
    'username',
    'password',
    ttl=900,  # optional
    port=3306  # optional
)
some_process_that_requires_cache(cache)
```

