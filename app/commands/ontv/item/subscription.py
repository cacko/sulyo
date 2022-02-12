from datetime import datetime, timezone
import emoji
from app.commands.ontv.item.components import ScoreFormat, ScoreRow
from app.commands.ontv.item.livescore_details import ParserDetails
from app.commands.ontv.item.models import Response, Event, EventStatus, GameStatus
from app.commands.ontv.item.player import Player
from app.core import Request, Cachable, to_mono, log, RenderResult
from app.core.hash import idhash
from app.scheduler import Scheduler
import re
from enum import Enum


class JobPrefix(Enum):
    INPROGRESS = "INP"
    SCHEDULED = "SCH"


class SubscribtionCache(Cachable):

    _struct: Response = None
    __url = None
    __id = None
    __cached: Response = None

    def __init__(self, url):
        self.__url = url
        self.__cached = self.fromcache()

    @property
    def id(self):
        if not self.__id:
            self.__id = idhash(self.__url)
        return self.__id

    async def fetch(self) -> Response:
        req = Request(self.__url)
        try:
            json = await req.json
            response = Response.from_dict(json)
            return response
        except:
            return None

    @property
    async def content(self) -> Response:
        if not self._struct:
            self._struct = self.tocache(await self.fetch())
        return self._struct

    @property
    async def fresh(self) -> Response:
        self._struct = self.tocache(await self.fetch())
        return self._struct

    @property
    async def update(self) -> Response:
        if not self.__cached:
            return None
        fresh = await self.fresh
        if fresh.game is not None:
            Player.store(fresh.game)
        if len(self.__cached.events) < len(fresh.events):
            self._struct.game.events = (await self.content).events[
                len(self.__cached.events):
            ]
            return self._struct
        return None


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

    __event: Event = None
    __groupID: list = None

    def __init__(self, item: Event, groupID: list) -> None:
        self.__event = item
        self.__groupID = groupID

    @property
    def id(self):
        prefix = JobPrefix.INPROGRESS if self.inProgress else JobPrefix.SCHEDULED
        return f"{self.__class__.getGroupId(self.__groupID)}:{self.__event.id}:{prefix.value}"

    @property
    def event_name(self):
        return (
            f"{self.__event.strHomeTeam.upper()} vs {self.__event.strAwayTeam.upper()}"
        )

    def cancel(self):
        Scheduler.cancel_jobs(self.id)

    async def trigger(self):
        api = Scheduler.api

        cache = SubscribtionCache(self.__event.details)
        if update := self.updates(await cache.update):
            await api.send(self.__groupID, update)
        try:
            content = await cache.content
            if not content:
                return Scheduler.cancel_jobs(self.id)
            Player.store(content.game)
            print(content.game.shortStatusText)
            if any(
                [
                    GameStatus(content.game.shortStatusText)
                    in [
                        GameStatus.FT,
                        GameStatus.JE,
                        GameStatus.SUS,
                        GameStatus.ABD,
                        GameStatus.AET,
                        GameStatus.FN,
                    ],
                ]
            ):
                await Scheduler.api.send(self.__groupID, await self.fulltimeAnnoucement)
                Scheduler.cancel_jobs(self.id)
                log.info(f"subscription {self.event_name} in done")
        except ValueError:
            pass
        except:
            return Scheduler.cancel_jobs(self.id)

    def updates(self, updated: Response) -> str:
        if not updated:
            return None
        details = ParserDetails(None, response=updated)
        rows = details.rendered
        if not rows:
            return None
        res = ScoreRow(
            status=f"{details.game_time:.0f}",
            home=details.home.name,
            away=details.away.name,
            score=details.score,
            format=ScoreFormat.STANDALONE,
        )

        res = [*rows, res]
        return to_mono("\n".join(map(str, res)))

    @property
    async def fulltimeAnnoucement(self) -> str:
        details = await ParserDetails.get(self.__event.details)
        return to_mono(
            f"{emoji.emojize(':chequered_flag:')} FULLTIME: {self.event_name} {details.score}"
        )

    @property
    def startAnnouncement(self) -> str:
        return to_mono(
            f"{emoji.emojize(':goal_net:')} GAME STARTING: {self.event_name}"
        )

    async def start(self, announceStart=False):
        log.info(f"subscriion in live mode {self.event_name}")
        Scheduler.add_job(
            id=self.id,
            name=f"{self.event_name}",
            func=self.trigger,
            trigger="interval",
            seconds=60,
            replace_existing=True,
        )
        if announceStart:
            await Scheduler.api.send(self.__groupID, self.startAnnouncement)

    async def schedule(self):
        if self.inProgress:
            self.announceStart = True
            await self.start()
            return
        log.info(f"subscription {self.event_name} in schduled mode")
        Scheduler.add_job(
            id=self.id,
            name=f"{self.event_name}",
            func=self.start,
            trigger="date",
            replace_existing=True,
            run_date=self.__event.startTime,
            args=[True],
        )

    @property
    def isValid(self) -> bool:
        return not any([self.isCancelled, self.isPostponed, self.hasEnded])

    @property
    def inProgress(self) -> bool:
        return not any([self.notStarted, self.hasEnded])

    @property
    def isPostponed(self) -> bool:
        try:
            status = EventStatus(self.__event.strStatus)
            return status == EventStatus.PPD
        except ValueError:
            return False

    @property
    def isCancelled(self) -> bool:
        try:
            status = EventStatus(self.__event.strStatus)
            return status == EventStatus.CNL
        except ValueError:
            return False

    @property
    def notStarted(self) -> bool:
        return self.__event.startTime > datetime.now(tz=timezone.utc)

    @property
    def hasEnded(self) -> bool:
        if self.notStarted:
            return False

        status = self.__event.strStatus

        try:
            _status = EventStatus(status)
            if _status in (EventStatus.FT, EventStatus.AET, EventStatus.PPD):
                return True
            return _status == EventStatus.HT or re.match("^\d+$", status)
        except ValueError:
            return False
