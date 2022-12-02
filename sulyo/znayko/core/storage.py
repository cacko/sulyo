from typing import Iterator, Optional
from redis import StrictRedis
from redis.client import Pipeline


class StorageMeta(type):

    _instance: Optional['Storage'] = None
    _bypass = None

    def __call__(cls, *args, **kwds):
        if not cls._instance:
            cls._instance = type.__call__(cls, *args, **kwds)
        return cls._instance

    def register(cls, url, bypass=False):
        if not cls._instance:
            cls._bypass = bypass
            redis_client = StrictRedis()
            cls._redis = redis_client.from_url(url)
            cls._instance = cls()
        return cls._instance


class Storage(object, metaclass=StorageMeta):

    @classmethod
    def exists(cls, *names):
        if cls._bypass:
            return False
        return cls._redis.exists(*names)

    @classmethod
    def hscan_iter(cls, name: str,
                   match: str = None, count: int = None) -> Iterator:
        if cls._bypass:
            return False
        return cls._redis.hscan_iter(name, match, count)

    @classmethod
    def hexists(cls, name, key):
        if cls._bypass:
            return False
        return cls._redis.hexists(name, key)

    @classmethod
    def keys(cls, pattern):
        if cls._bypass:
            return None
        return cls._redis.keys(pattern)

    @classmethod
    def hkeys(cls, name):
        if cls._bypass:
            return None
        return cls._redis.hkeys(name)

    @classmethod
    def mget(cls, keys, *args) -> list:
        if cls._bypass:
            return None
        return cls._redis.mget(keys, *args)

    @classmethod
    def get(cls, name):
        if cls._bypass:
            return None
        return cls._redis.get(name)

    @classmethod
    def hgetall(cls, name):
        if cls._bypass:
            return None
        return cls._redis.hgetall(name)

    @classmethod
    def hset(cls, name: str, key: str, value: any) -> int:
        if cls._bypass:
            return None
        return cls._redis.hset(name, key, value)

    @classmethod
    def hget(cls, name: str, key: str) -> any:
        if cls._bypass:
            return None
        return cls._redis.hget(name, key)

    @classmethod
    def set(cls, name, value, *args, **kwargs):
        if cls._bypass:
            return
        return cls._redis.set(name, value, *args, **kwargs)

    @classmethod
    def lset(cls, name, index, value, *args, **kwargs):
        if cls._bypass:
            return
        return cls._redis.lset(name, index, value, *args, **kwargs)

    @classmethod
    def rename(cls, src, dst):
        if cls._bypass:
            return
        return cls._redis.rename(src, dst)

    @classmethod
    def persist(cls, name):
        if cls._bypass:
            return
        return cls._redis.persist(name)

    @classmethod
    def pipeline(cls) -> Pipeline:
        if cls._bypass:
            return
        return cls._redis.pipeline()
