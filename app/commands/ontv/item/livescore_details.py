from datetime import datetime
from hashlib import blake2b
from app.commands.ontv.item.models import *
from app.commands.ontv.models import GameNotFound
from app.core import Request
from typing import Optional
from dataclasses import dataclass
from dataclasses_json import dataclass_json, Undefined
from unidecode import unidecode
from app.core import log
from datetime import timezone
from app.core.cacheable import TimeCacheable
from app.core.models import TimeCache
from app.core.text import align_whitespace

@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class ParserDetailsResponse:
    events: Optional[list[DetailsEvent]] = None

class ParserDetails(TimeCacheable):

    __url: str
    _struct: TimeCache = None
    __id: str = None
    
    def __init__(self, url: str, response: Response = None):
        self.__url = url
        if response is not None:
            self._struct = TimeCache(timestamp=datetime.now(timezone.utc), struct=response)

    @classmethod
    async def get(cls, url:str, response: Response = None):
        obj = cls(url, response)
        await obj.refresh()
        return obj


    async def refresh(self):
        if self.load():
            return
        try:
            req = Request(self.__url)
            json = await req.json
            res = Response.from_dict(json)
            self._struct = self.tocache(res)
        except Exception as e:
            log.error(e, exc_info=True)
            self._struct = None
            raise GameNotFound

    @property
    def id(self):
        if not self.__id:
            h = blake2b(digest_size=20)
            h.update(self.__url.encode())
            self.__id = h.hexdigest()
        return self.__id

    @property
    def events(self) -> list[DetailsEvent]:
        try:
            res = []
            competitors = {
                self._struct.struct.game.homeCompetitor.id: self._struct.struct.game.homeCompetitor,
                self._struct.struct.game.awayCompetitor.id: self._struct.struct.game.awayCompetitor,
            }
            members = { m.id:m for m in self._struct.struct.game.members }
            if not self._struct.struct.game.events:
                return []
            for ev in self._struct.struct.game.events:
                match ev.competitorId:
                    case self._struct.struct.game.homeCompetitor.id:
                        position = Position.HOME
                    case self._struct.struct.game.awayCompetitor.id:
                        position = Position.AWAY
                    case _:
                        position = Position.NONE
                res.append(DetailsEvent(
                    time=ev.gameTime, 
                    action=ev.eventType.name,
                    position=position,
                    team=competitors[ev.competitorId].name,
                    player=unidecode(members[ev.playerId].displayName),
                    order=ev.order))
            return sorted(res, reverse=True, key=lambda x: x.order)
        except:
            return []

    @property
    def score(self) -> str:
        return f"{self.home.score:.0f}:{self.away.score:.0f}"

    @property
    def members(self) -> list[GameMember]:
        return self._struct.struct.game.members

    @property
    def home(self) -> GameCompetitor:
        if not self._struct.struct.game:
            return None
        return self._struct.struct.game.homeCompetitor

    @property
    def game_time(self) -> int:
        if not self._struct.struct.game:
            return None
        return self._struct.struct.game.gameTime

    @property
    def facts(self) -> list[GameFact]:
        if not self._struct.struct.game:
            return None
        return self._struct.struct.game.matchFacts

    @property
    def away(self) -> GameCompetitor:
        if not self._struct.struct.game:
            return None
        return self._struct.struct.game.awayCompetitor

    @property
    def event_name(self) -> str:
        if self.home and self.away:
            return unidecode(f"{self.home.name.upper()} vs {self.away.name.upper()}")
        return "Unknown"

    @property
    def rendered(self) -> list[str]:
        res = []
        for ev in self.events:
            if ev.position == Position.HOME:
                row = f"{to_mono(f'{ev.time:<5.0f}')}{to_mono(ev.icon + ev.player):<55}"
                res.append(align_whitespace(f"{row:<60}"))
            elif ev.position == Position.AWAY:
                row = f"{to_mono(ev.player + ev.icon):>55}{to_mono(f'{ev.time:>5.0f}')}"
                res.append(align_whitespace(f"{to_mono(row):>60}"))
            else:
                row = f"{to_mono(f'{ev.time:5.0f}')}{ev.icon}"
                res.append(align_whitespace(f"{to_mono(row):^60}"))
        return res

