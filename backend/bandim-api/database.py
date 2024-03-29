import logging
from typing import Union, Any

from redis import asyncio as aioredis

from sqlmodel import SQLModel, create_engine

# from sqlalchemy import create_engine
# from sqlalchemy.ext.declarative import declarative_base
# from sqlalchemy.orm import sessionmaker
from settings import (
    REDIS_HOST,
    REDIS_PORT,
    REDIS_DB,
    # POSTGRES_USER,
    # POSTGRES_PASSWORD,
    # POSTGRES_PORT,
    # POSTGRES_DB,
)


class RedisCache:

    def __init__(self, url: str) -> None:
        self.url = url
        self.redis_cache = None

    async def init_cache(self) -> None:
        pool = aioredis.ConnectionPool.from_url(self.url)
        self.redis_cache = aioredis.Redis.from_pool(pool)

    async def keys(self, pattern: str) -> Union[None, Any]:
        if self.redis_cache is not None:
            return await self.redis_cache.keys(pattern)
        else:
            logging.debug(
                "A Redis connection pool has not yet been initialized. "
                + "Used keys can thus not be retrieved from Redis. "
                + "Please call method .init_cache()",
            )
            return None

    async def set(self, key: str, value: Any, expire: int = 0) -> Union[None, bool]:
        if self.redis_cache is not None:
            return await self.redis_cache.set(
                key=key,
                value=value,
                expire=expire,
            )
        else:
            logging.debug(
                "A Redis connection pool has not yet been initialized. "
                + "A key-value pair can thus not be set in Redis. "
                + "Please call method .init_cache()",
            )
            return None

    async def get(self, key: str) -> Union[None, Any]:
        if self.redis_cache is not None:
            return await self.redis_cache.get(key=key)
        else:
            logging.debug(
                "A Redis connection pool has not yet been initialized. "
                + "A value can thus not retrieved from Redis. "
                + "Please call method .init_cache()",
            )
            return None

    async def close(self) -> None:
        if self.redis_cache is not None:
            await self.redis_cache.close()
            await self.redis_cache.wait_closed()
        else:
            logging.debug(
                "A Redis connection pool has not yet been initialized. "
                + "The connection to Redis can thus not be closed. "
                + "Please call method .init_cache()",
            )
            return None


SQLALCHEMY_DATABASE_URL = f"sqlite:///bandim.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL)

# def create_db_and_tables():
#     SQLModel.metadata.create_all(engine)

# REDIS_DATABASE_URL = f'redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}?encoding=utf-8'
REDIS_DATABASE_URL = f"redis://{REDIS_HOST}:{REDIS_PORT}"
print("REDIS_DATABASE_URL: ", REDIS_DATABASE_URL)
redis_cache = RedisCache(url=REDIS_DATABASE_URL)
