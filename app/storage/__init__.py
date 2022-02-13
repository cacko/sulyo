from typing import Iterator
from redis import StrictRedis
from redis.client import Pipeline
from app.core.config import Config


class StorageMeta(type):
    pass


class Storage(object, metaclass=StorageMeta):

    _redis: StrictRedis = None
    _instance = None
    bypass = False

    def __init__(self, app) -> None:
        redis_client = StrictRedis()
        self._redis = redis_client.from_url(Config.redis.url)

    def __new__(cls, app, *args, **kwargs):
        if not cls._instance:
            cls._instance = object.__new__(cls, *args, **kwargs)
        return cls._instance

    @classmethod
    def register(cls, app):
        if not cls._instance:
            cls._instance = cls(app)
        return cls._instance

    @classmethod
    def exists(cls, *names):
        if cls._instance.bypass:
            return False
        return cls._instance._redis.exists(*names)

    @classmethod
    def hscan_iter(cls, name: str,
                   match: str = None, count: int = None) -> Iterator:
        if cls._instance.bypass:
            return False
        return cls._instance._redis.hscan_iter(name, match, count)

    @classmethod
    def hexists(cls, name, key):
        if cls._instance.bypass:
            return False
        return cls._instance._redis.hexists(name, key)

    @classmethod
    def keys(cls, pattern):
        if cls._instance.bypass:
            return None
        return cls._instance._redis.keys(pattern)

    @classmethod
    def hkeys(cls, name):
        if cls._instance.bypass:
            return None
        return cls._instance._redis.hkeys(name)

    @classmethod
    def mget(cls, keys, *args) -> list:
        if cls._instance.bypass:
            return None
        return cls._instance._redis.mget(keys, *args)

    @classmethod
    def get(cls, name):
        if cls._instance.bypass:
            return None
        return cls._instance._redis.get(name)

    @classmethod
    def hgetall(cls, name):
        if cls._instance.bypass:
            return None
        return cls._instance._redis.hgetall(name)

    @classmethod
    def hset(cls, name: str, key: str, value: any) -> int:
        if cls._instance.bypass:
            return None
        return cls._instance._redis.hset(name, key, value)

    @classmethod
    def hget(cls, name: str, key: str) -> any:
        if cls._instance.bypass:
            return None
        return cls._instance._redis.hget(name, key)

    @classmethod
    def set(cls, name, value, *args, **kwargs):
        if cls._instance.bypass:
            return
        return cls._instance._redis.set(name, value, *args, **kwargs)

    @classmethod
    def lset(cls, name, index, value, *args, **kwargs):
        if cls._instance.bypass:
            return
        return cls._instance._redis.lset(name, index, value, *args, **kwargs)

    @classmethod
    def rename(cls, src, dst):
        if cls._instance.bypass:
            return
        return cls._instance._redis.rename(src, dst)

    @classmethod
    def persist(cls, name):
        if cls._instance.bypass:
            return
        return cls._instance._redis.persist(name)

    @classmethod
    def pipeline(cls) -> Pipeline:
        if cls._instance.bypass:
            return
        return cls._instance._redis.pipeline()
