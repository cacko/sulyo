from datetime import datetime, timedelta
from turtle import ontimer
from typing import Optional
from dataclasses_json import dataclass_json
from emoji.core import emojize
from app.commands.ontv.item.competitions import Competitions
from app.commands.ontv.item.lineups import Lineups
from app.commands.ontv.item.models import (
    Event,
)
from app.commands.ontv.item.player import Player
from app.commands.ontv.item.tv import TV
from app.commands.ontv.item.stats import Stats
from app.commands.ontv.item.subscription import Subscription
from app.commands.ontv.item.livescore import Livescore
from app.commands.ontv.item.facts import Facts
from app.commands.ontv.models import GameNotFound
from app.core import Request, to_mono, RenderResult
from dataclasses import dataclass
from app.core.decorators import command
from app.core.match import Match, MatchMethod
from app.core.models import EmptyResult
from app.json_rpc.context import Context, Typing
from app.scheduler import Scheduler


@dataclass
class OnTVConfig:
    api_url: str


class OnTVMeta(type):

    _instance = None

    @property
    def tv(cls) -> TV:
        return cls._instance.getTV()

    @property
    def livescore(cls) -> Livescore:
        return cls._instance.getLivescore()

    async def subscribe(cls, query: str, groupID, source) -> RenderResult:
        return await cls._instance.getSubscription(query, groupID, source)

    async def unsubscribe(cls, query: str, groupID, source) -> RenderResult:
        return await cls._instance.removeSubscription(query, groupID, source)

    def listjobs(cls, groupID) -> RenderResult:
        return Subscription.forGroup(groupID)

    async def lineups(cls, query: str, groupID, source) -> Lineups:
        return await cls._instance.getLineups(query, groupID, source)

    async def facts(cls, query: str, groupID, source) -> Facts:
        return await cls._instance.getFacts(query, groupID, source)

    async def stats(cls, query: str, groupID, source) -> Stats:
        return await cls._instance.getStats(query, groupID, source)

    async def player(cls, query: str, groupID) -> Player:
        return await cls._instance.getPlayer(query, groupID)

    async def precache(cls):
        return await cls._instance.precacheLivegames()

    def competitions(cls) -> Competitions:
        return cls._instance.getCompetitions()


class GameMatch(Match):
    minRatio = 60
    method = MatchMethod.PARTIAL


@dataclass_json
@dataclass
class GameNeedle:
    strHomeTeam: str
    strAwayTeam: Optional[str] = ""


class OnTV(object, metaclass=OnTVMeta):

    _config: OnTVConfig = None
    _app = None

    def __init__(self, app) -> None:
        self._app = app
        self._config = OnTVConfig(api_url=app.config.ONTV_API_URL)

    def __new__(cls, app, *args, **kwargs):
        if not cls._instance:
            cls._instance = object.__new__(cls, *args, **kwargs)
        return cls._instance

    @classmethod
    def register(cls, app):
        if not cls._instance:
            cls._instance = cls(app)
        return cls._instance

    def getTV(self) -> TV:
        tv = TV(
            Request(f"{self._config.api_url}/data/schedule.json"),
            self._app.config.SETTINGS.get("livescore", {}),
        )
        return tv

    def getLivescore(self) -> Livescore:
        return Livescore(
            Request(f"{self._config.api_url}/data/livescores.json"),
            self._app.config.SETTINGS.get("livescore", {}),
        )

    def getCompetitions(self) -> Competitions:
        return Competitions(
            self._app.config.COMPETITIONS_JSON,
            self._app.config.SETTINGS.get("livescore", {}).get("leagues", []),
        )

    async def __queryGame(self, query) -> Event:
        if not query.strip():
            raise GameNotFound
        items = await self.getLivescore().items
        matcher = GameMatch(haystack=items)
        game = matcher.fuzzy(GameNeedle(strHomeTeam=query))
        if not game:
            raise GameNotFound
        return game[0]

    async def getLineups(self, query: str, groupID: list, source: str) -> Lineups:
        try:
            item = await self.__queryGame(query)
            return Lineups(item)
        except GameNotFound:
            return None

    async def getFacts(self, query: str, groupID: list, source: str) -> Facts:
        item = await self.__queryGame(query)
        return Facts(item)

    async def getStats(self, query: str, groupID: list, source: str) -> Stats:
        item = await self.__queryGame(query)
        return Stats(item)

    async def removeSubscription(
        self, query: str, groupID: list, source: str
    ) -> RenderResult:
        item = await self.__queryGame(query)
        sub = Subscription(item, groupID)
        sub.cancel()
        return RenderResult(
            to_mono(f"{emojize(':dango:')} {item.strHomeTeam} vs {item.strAwayTeam}")
        )

    async def getSubscription(
        self, query: str, groupID: list, source: str
    ) -> RenderResult:
        item = await self.__queryGame(query)
        sub = Subscription(item, groupID)
        if not sub.isValid:
            return RenderResult(message=to_mono(f"Event has ended".upper()))
        await sub.schedule()
        return RenderResult(
            message=to_mono(
                f"{emojize(':bell:')} {item.strHomeTeam} vs {item.strAwayTeam}"
            )
        )

    async def getPlayer(self, query: str, groupID: list) -> Player:
        player = Player.find(query)
        if not player:
            return None
        return player


@command(
    trigger="tv",
    desc="shows schedudle for the day, suplliying a second argument return detailed info the matches",
)
async def tv_command(context: Context) -> RenderResult:
    schedule = OnTV.tv
    response = await schedule.render(context.query, context.group, context.source)
    await context.send(response)


@command(
    trigger="livescore",
    desc="shows livescore for the day, suplliying a second argument return detailed info the matches",
)
async def livescore_command(context: Context) -> RenderResult:
    livescore = OnTV.livescore
    response = await livescore.render(context.query, context.group, context.source)
    await context.send(response)


@command(
    trigger="subscribe",
    desc="subscribes the channels for the live updates during the game",
)
async def subscribe_command(context: Context) -> RenderResult:
    response = await OnTV.subscribe(context.query, context.group, context.source)
    await context.send(response)


@command(trigger="unsubscribe", desc="cancels a subscribtion")
async def unsubscribe_command(context: Context) -> RenderResult:
    response = await OnTV.unsubscribe(context.query, context.group, context.source)
    await context.send(response)


@command(trigger="listsubs", desc="show all subscriptions in the channel")
async def subscriptions_command(context: Context) -> RenderResult:
    response = OnTV.listjobs(context.group)
    await context.send(response)


@command(trigger="competitions", desc="show all compeittiions currently tracked")
async def competitions_command(context: Context) -> RenderResult:
    competitions = OnTV.competitions()
    response = competitions.message(context.query)
    await context.send(response)


@command(trigger="lineups", desc="show for the first matching game")
async def lineups_command(context: Context) -> RenderResult:
    lineups = await OnTV.lineups(context.query, context.group, context.source)
    if lineups:
        message = await lineups.message
        await context.send(message)


@command(trigger="facts", desc="facts for the first matching game")
async def facts_command(context: Context) -> RenderResult:
    facts = await OnTV.facts(context.query, context.group, context.source)
    await context.send(await facts.message)


@command(trigger="stats", desc="stats for the first matching game")
async def stats_command(context: Context) -> RenderResult:
    stats = await OnTV.stats(context.query, context.group, context.source)
    await context.send(await stats.message)


@command(trigger="player", desc="player stat")
async def player_command(context: Context) -> RenderResult:
    try:
        async with Typing(context) as ctx:
            player = await OnTV.player(ctx.query, ctx.group)
            message = await player.message
            await ctx.send(message)
    except:
        await context.send(EmptyResult())


@command(trigger="precache", desc="")
async def precache_command(context: Context) -> RenderResult:
    Scheduler.add_job(
        id="precache_players",
        name=f"precache players",
        func=OnTV.livescore.precache,
        trigger="interval",
        minutes=20,
        replace_existing=True,
    )
