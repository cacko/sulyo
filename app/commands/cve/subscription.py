from app.core.cacheable import Cachable
from app.core.hash import idhash
from app.core.models import RenderResult
from app.scheduler import Scheduler
from .components import CVEHeader
from app.core.output import to_mono
from stringcase import alphanumcase
from .models import *
from .cve import CVE


class SubscribtionCache(Cachable):

    _struct: CVEResponse = None
    __id = None
    __cached: CVEResponse = None

    def __init__(self, query: str = ""):
        self.__query = query
        self.__cached = self.fromcache()

    @property
    def id(self):
        if not self.__id:
            self.__id = idhash(self.__query)
        return self.__id

    async def fetch(self, ignoreCache=False) -> CVEResponse:
        cve = CVE(self.__query, ignoreCache=ignoreCache)
        try:
            response = await cve.response
            return response
        except:
            return None

    @property
    async def content(self) -> CVEResponse:
        if not self._struct:
            response = await self.fetch()
            self._struct = self.tocache(response)
        return self._struct

    @property
    async def fresh(self) -> CVEResponse:
        self._struct = self.tocache(await self.fetch(ignoreCache=True))
        return self._struct

    @property
    async def update(self) -> list[CVEListItem]:
        if not self.__cached:
            await self.content
            return None
        fresh = await self.fresh
        cacheIds = self.__cached.ids
        return list(
            filter(
                lambda x: not x.cve.CVE_data_meta.ID in cacheIds, fresh.result.CVE_Items
            )
        )


class SubscriptionMeta(type):
    def forGroup(cls, groupID: list) -> RenderResult:
        grouphash = cls.getGroupId(groupID)
        return RenderResult(
            message=to_mono(
                "\n".join(
                    [
                        x.name
                        for x in Scheduler.get_jobs()
                        if x.id.startswith(f"{grouphash}")
                    ]
                )
            )
        )

    def groupJobs(cls, groupID: list):
        grouphash = cls.getGroupId(groupID)
        return list(
            filter(lambda g: g.id.startswith(
                f"{grouphash}"), Scheduler.get_jobs())
        )

    def getGroupId(cls, groupdID: list):
        return idhash(f"{cls.__module__}{groupdID}")


class Subscription(metaclass=SubscriptionMeta):

    __groupID: list = None
    __query: str = ""

    def __init__(self, groupID: list, query: str = None) -> None:
        self.__groupID = groupID
        self.__query = query

    @property
    def id(self):
        return (
            f"{self.__class__.getGroupId(self.__groupID)}:{alphanumcase(self.__query)}:"
        )

    @property
    def subscription_name(self):
        return " - ".join(filter(None, ["CVE", self.__query]))

    def cancel(self):
        Scheduler.cancel_jobs(self.id)

    async def trigger(self):
        api = Scheduler.api
        cache = SubscribtionCache(self.__query)
        if update := self.updates(await cache.update):
            await api.send(self.__groupID, update)

    def updates(self, updated: list[CVEListItem]) -> str:
        if not updated:
            return None
        rows = [
            CVEHeader(x.id, x.description, x.severity, x.attackVector) for x in updated
        ]
        return "\n".join(map(str, rows))

    async def schedule(self):
        Scheduler.add_job(
            id=self.id,
            name=f"{self.subscription_name}",
            func=self.trigger,
            trigger="interval",
            minutes=20,
            replace_existing=True,
        )
