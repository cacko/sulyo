from datetime import timedelta, timezone
from app.commands.ontv.item.livescore_details import ParserDetails
from app.commands.ontv.item.player import Player
from app.commands.ontv.item.subscription import SubscribtionCache
from app.commands.ontv.models import GameNotFound
from app.core import Request
from app.commands.ontv.item.models import *
from app.core.cacheable import TimeCacheable
from app.core.text import split_with_quotes
from app.commands.ontv.item.components import ScoreFormat, ScoreRow


class Livescore(TimeCacheable):

    __request: Request = None
    LEAGUES: list[int] = []

    def __init__(self, request, settings: dict = {}):
        self.__request = request
        self.LEAGUES = settings.get("leagues", [])

    @property
    def id(self):
        return datetime.now(tz=timezone.utc).strftime("%Y%m%d")

    @property
    async def items(self) -> list[Event]:
        if not self.load():
            body = await self.__request.body
            self._struct = self.tocache(Event.schema().loads(body, many=True))
        events: list[Event] = self._struct.struct
        return list(
            filter(
                lambda x: len(self.LEAGUES) == 0 or x.idLeague in self.LEAGUES, events
            )
        )

    async def precache(self):
        now = datetime.now(tz=timezone.utc)
        timeframe = timedelta(minutes=120)
        items = filter(lambda ev: (ev.startTime - now) < timeframe, await self.items)
        for ev in items:
            cache = SubscribtionCache(ev.details)
            content: Response = await cache.content
            if not content:
                continue
            game = content.game
            if game is not None:
                Player.store(game)

    async def render(self, filt: str = "", *args, **kwargs) -> RenderResult:
        items = await self.items
        items.reverse()
        filt = split_with_quotes(filt)
        filtered: list[ScoreRow] = [
            ScoreRow(
                status=x.displayStatus,
                home=x.strHomeTeam,
                score=x.displayScore,
                away=x.strAwayTeam,
                win=x.strWinDescription if x.displayStatus == "AET" else "",
            )
            for x in sorted(items, key=lambda itm: itm.sort)
            if any(
                [
                    not filt,
                    *[
                        f.strip().lower()
                        in f"{x.strHomeTeam.lower()} {x.strAwayTeam.lower()} {x.strLeague.lower()}"
                        for f in filt
                    ],
                ]
            )
        ]
        if len(filtered) == 1:
            x = filtered[0]
            x.format = ScoreFormat.STANDALONE
            itm = next(
                filter(
                    lambda y: y.strHomeTeam == x.home and y.strAwayTeam == x.away, items
                ),
                None,
            )
            try:
                details = await ParserDetails.get(itm.details)
                if details:
                    res = [
                        x,
                        *details.rendered,
                    ]
                    return RenderResult(message="\n".join(map(str, res)))
            except GameNotFound:
                return EmptyResult()
        return (
            RenderResult(message="\n".join(map(str, filtered)))
            if len(filtered)
            else EmptyResult()
        )
