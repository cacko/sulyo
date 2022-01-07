from typing import Optional
from datetime import datetime, timezone
from dataclasses import dataclass, field
from dataclasses_json import dataclass_json, config, Undefined
from marshmallow import fields
from enum import IntEnum, Enum
from app.core.models import *
from string import punctuation
import re
import emoji
from stringcase import constcase


class EventStatus(Enum):
    HT = "HT"
    FT = "FT"
    PPD = "PPD"
    CNL = "CNL"
    AET = "AET"
    NS = "NS"


class GameStatus(Enum):
    FT = "Ended"
    JE = "Just Ended"
    SUS = "Susp"
    ABD = "Aband."
    AET = "After Pen"
    UNKNOWN = ""
    NS = "NS"
    FN = "Final"


class OrderWeight(Enum):
    INPLAY = 1
    HT = pow(2, 1)
    LIVE = pow(2, 1)
    FT = pow(2, 2)
    EAT = pow(2, 3)
    ET = pow(2, 3)
    NS = pow(2, 3)
    PPD = pow(2, 4)
    JUNK = pow(2, 5)


class LineupMemberStatus(IntEnum):
    STARTING = 1
    SUBSTITUTE = 2
    MISSING = 3
    MANAGEMENT = 4
    DOUBTHFUL = 5


class ActionIcon(Enum):
    SUBSTITUTION = ":ON!_arrow:"
    GOAL = ":soccer_ball:"
    YELLOW__CARD = ":yellow_square:"
    RED__CARD = ":red_square:"
    WOODWORK = ":palm_tree:"
    PENALTY__MISS = ":cross_mark:"
    GOAL__DISSALOWED = ":double_exclamation_mark:"


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class CompetitionItem:
    id: int
    league_id: int
    league_name: str
    country_id: int
    country_name: str
    sport_id: int
    sport_name: str


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class Event:
    id: str
    idEvent: int
    strSport: str
    idLeague: int
    strLeague: str
    idHomeTeam: int
    idAwayTeam: int
    strHomeTeam: str
    strAwayTeam: str
    strStatus: str
    startTime: datetime = field(
        metadata=config(
            encoder=datetime.isoformat,
            decoder=datetime.fromisoformat,
            mm_field=fields.DateTime(format="iso", tzinfo=timezone.utc),
        )
    )
    intHomeScore: Optional[int] = -1
    intAwayScore: Optional[int] = -1
    sort: int = 0
    details: Optional[str] = None
    displayScore: Optional[str] = ""
    displayStatus: Optional[str] = ""
    source: Optional[str] = ""
    strWinDescription: Optional[str] = ""

    def __post_init__(self):
        delta = (datetime.now(timezone.utc) - self.startTime).total_seconds() / 60
        try:
            self.displayStatus = GameStatus(self.strStatus)
            if delta < 0 and self.displayStatus in [GameStatus.UNKNOWN, GameStatus.NS]:
                self.displayStatus = self.startTime.strftime("%H:%M")
            else:
                self.displayStatus = self.displayStatus.name
        except:
            self.displayStatus = self.strStatus
        try:
            if re.match("^\d+$", self.strStatus):
                self.sort = OrderWeight.INPLAY.value * int(self.strStatus)
                self.displayStatus = f"{self.strStatus}"
            else:
                self.sort = OrderWeight[
                    self.strStatus.translate(punctuation).upper()
                ].value * abs(delta)
        except KeyError:
            self.sort = OrderWeight.JUNK.value * abs(delta)
        if any([self.intAwayScore == -1, self.intHomeScore == -1]):
            self.displayScore = ""
        else:
            self.displayScore = f"{self.intHomeScore}:{self.intAwayScore}"


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class Sport:
    id: int
    name: str
    nameForURL: str
    totalGames: Optional[int] = 0
    liveGames: Optional[int] = 0


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class Country:
    id: int
    name: str
    nameForURL: int
    totalGames: Optional[int] = 0
    liveGames: Optional[int] = 0


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class Competitor:
    id: int
    countryId: int
    sportId: int
    name: str
    nameForURL: str
    type: int
    color: str
    mainCompetitionId: int
    popularityRank: Optional[int] = None


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class Competition:
    id: int
    countryId: int
    sportId: int
    name: str
    hasStandings: bool
    hasBrackets: bool
    nameForURL: str
    color: str
    totalGames: Optional[int] = 0
    liveGames: Optional[int] = 0
    hasActiveGames: Optional[bool] = False
    popularityRank: Optional[int] = None

    @property
    def flag(self) -> str:
        pass


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class GameMember:
    competitorId: Optional[int] = None
    name: Optional[str] = None
    id: Optional[int] = None
    shortName: Optional[str] = None
    nameForURL: Optional[str] = None
    imageVersion: Optional[int] = 0
    athleteId: Optional[int] = 0
    jerseyNumber: Optional[int] = 0

    @property
    def displayName(self) -> str:
        return self.shortName if self.shortName else self.name


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class LineupPosition:
    id: int
    name: str


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class MemberStat:
    value: str
    name: str
    shortName: Optional[str] = None


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class LineupMember:
    id: int
    status: LineupMemberStatus
    statusText: str
    position: Optional[LineupPosition] = None
    stats: Optional[list[MemberStat]] = None


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class Lineup:
    status: Optional[str] = None
    formation: Optional[str] = None
    hasFieldPositions: Optional[bool] = False
    members: Optional[list[LineupMember]] = None


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class GameStatistic:
    id: int
    name: str
    categoryId: int
    categoryName: str
    value: str
    isMajor: Optional[bool]
    valuePercentage: Optional[int]
    isPrimary: Optional[bool]


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class GameCompetitor:
    id: Optional[int] = None
    countryId: Optional[int] = None
    sportId: Optional[int] = None
    name: Optional[str] = None
    score: Optional[int] = None
    isQualified: Optional[bool] = None
    toQualify: Optional[bool] = None
    isWinner: Optional[bool] = None
    type: Optional[int] = None
    imageVersion: Optional[int] = None
    mainCompetitionId: Optional[int] = None
    redCards: Optional[int] = None
    popularityRank: Optional[int] = None
    lineups: Optional[Lineup] = None
    statistics: Optional[list[GameStatistic]] = None

    @property
    def flag(self) -> str:
        pass


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class OddsRate:
    decimal: Optional[float] = None
    fractional: Optional[str] = None
    american: Optional[str] = None


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class OddsOptions:
    num: int
    rate: OddsRate


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class Odds:
    lineId: int
    gameId: int
    bookmakerId: int
    lineTypeId: int
    options: list[OddsOptions]


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class GameFact:
    id: str
    text: str


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class Game:
    id: int
    sportId: int
    competitionId: int
    competitionDisplayName: str
    startTime: datetime = field(
        metadata=config(
            encoder=datetime.isoformat,
            decoder=datetime.fromisoformat,
            mm_field=fields.DateTime(format="iso"),
        )
    )
    statusGroup: int
    statusText: str
    shortStatusText: str
    gameTimeAndStatusDisplayType: int
    gameTime: int
    gameTimeDisplay: str
    homeCompetitor: GameCompetitor
    awayCompetitor: GameCompetitor
    odds: Optional[Odds] = None
    seasonNum: Optional[int] = 0
    stageNum: Optional[int] = 0
    justEnded: Optional[bool] = None
    hasLineups: Optional[bool] = None
    hasMissingPlayers: Optional[bool] = None
    hasFieldPositions: Optional[bool] = None
    hasTVNetworks: Optional[bool] = None
    hasBetsTeaser: Optional[bool] = None
    matchFacts: Optional[list[GameFact]] = None


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class GameEventType:
    id: Optional[int] = None
    name: Optional[str] = None
    subTypeId: Optional[int] = None


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class GameEvent:
    competitorId: int
    eventType: GameEventType
    statusId: Optional[int] = 0
    stageId: Optional[int] = 0
    order: Optional[int] = 0
    num: Optional[int] = 0
    gameTime: Optional[int] = 0
    addedTime: Optional[int] = 0
    gameTimeDisplay: Optional[str] = None
    gameTimeAndStatusDisplayType: Optional[int] = 0
    playerId: Optional[int] = 0
    isMajor: Optional[bool] = None


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class GameDetails(Game):
    events: Optional[list[GameEvent]] = None
    members: Optional[list[GameMember]] = None
    homeCompetitor: Optional[GameCompetitor] = None
    awayCompetitor: Optional[GameCompetitor] = None


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class Response:
    lastUpdateId: int
    requestedUpdateId: int
    game: GameDetails

    @property
    def events(self) -> list[Event]:
        if not self.game:
            return []
        if not self.game.events:
            return []
        if not isinstance(self.game.events, list):
            return []
        return self.game.events


class Position(Enum):
    HOME = 1
    AWAY = 2
    NONE = 3


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class DetailsEvent:
    time: str
    action: str
    order: int
    team: Optional[str] = None
    player: Optional[str] = None
    position: Optional[Position] = None

    @property
    def icon(self) -> str:
        try:
            action = ActionIcon[constcase(self.action)]
            return emoji.emojize(action.value)
        except KeyError:
            return self.action.upper()
