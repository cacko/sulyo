from datetime import datetime, timedelta, timezone
from app.core.models import TimeCache
from app.storage import Storage
import pickle


class CacheableMeta(type):

    @property
    def hash_key(cls):
        return f"{cls.__name__}"

class Cachable(object, metaclass=CacheableMeta):

    _struct = None

    def fromcache(self):
        if data := Storage.get(self.store_key):
            return pickle.loads(data)
        return None

    def tocache(self, res):
        Storage.set(self.store_key, pickle.dumps(res))
        Storage.persist(self.store_key)
        return res

    def load(self) -> bool:
        if self._struct is not None:
            return True
        if not self.isCached:
            return False
        self._struct = self.fromcache()
        return True if self._struct else False

    @property
    def id(self):
        raise NotImplemented()

    @property
    def isCached(self) -> bool:
        return Storage.exists(self.store_key) == 1


    @property
    def store_key(self):
        return f"{self.__class__.__name__}.{self.id}"


class TimeCacheable(Cachable):

    cachetime: timedelta = timedelta(minutes=1)
    _struct: TimeCache = None

    def fromcache(self):
        if data := Storage.get(self.store_key):
            struct: TimeCache = pickle.loads(data)
            return struct if not self.isExpired(struct.timestamp) else None
        return None

    def tocache(self, res) -> TimeCache:
        timecache = TimeCache(timestamp=datetime.now(tz=timezone.utc), struct=res)
        Storage.set(self.store_key, pickle.dumps(timecache))
        Storage.persist(self.store_key)
        return timecache

    def isExpired(self, t: datetime) -> bool:
        return datetime.now(tz=timezone.utc) - t > self.cachetime

    def load(self) -> bool:
        if self._struct and self.isExpired:
            return False
        if not self.isCached:
            return False
        self._struct = self.fromcache()
        return True if self._struct else False

    @property
    def isCached(self) -> bool:
        if not Storage.exists(self.store_key) == 1:
            return False
        if data := Storage.get(self.store_key):
            struct: TimeCache = TimeCache.from_dict(pickle.loads(data))
            return not self.isExpired(struct.timestamp)
        return False
