from app.commands.ontv.item.livescore_details import ParserDetails
from app.core import Request
from app.commands.ontv.item.models import *
from app.core.cacheable import Cachable
from pathlib import Path
import tempfile
from dataclasses_json import dataclass_json, Undefined
from app.core.match import Match, MatchMethod
from app.core.output import Align, Column, TextOutput
from enum import Enum
import pickle
from unidecode import unidecode

from app.storage import Storage

jsonfile = Path(__file__).parent.parent / "leagues.json"
COUNTRIES = {
    x.id: x.country_name
    for x in CompetitionItem.schema().loads(jsonfile.read_text(), many=True)
}


class InternationalCompetitions(Enum):
    AFRICA = "Africa"
    EUROPE = "Europe"
    INTERNATIONAL = "International"


class PlayerMatch(Match):
    minRatio = 80
    method = MatchMethod.WRATIO


@dataclass_json
@dataclass
class PlayerNeedle:
    name: str


class PlayerImage(Cachable):

    member: GameMember = None
    team: str = None
    URL_TEMPLATE = "https://imagecache.365scores.com/image/upload/f_png,w_200,h_200,c_limit,q_auto:eco,dpr_2,d_Athletes:{member.athleteId}.png,r_max,c_thumb,g_face,z_0.65/v{member.imageVersion}/Athletes/{team}/{member.athleteId}"

    def __init__(self, member, team: str = None):
        self.member = member
        self.team = team

    @property
    def id(self):
        return f"{self.member.id}-{self.team}" if self.team else self.member.id

    @property
    def image_url(self):
        return self.URL_TEMPLATE.format(member=self.member, team=self.team)

    @property
    async def image(self) -> Path:
        dst = Path(tempfile.gettempdir()) / f"{self.store_key}.png"
        if not dst.exists():
            req = Request(self.image_url)
            binary = await req.binary
            dst.write_bytes(binary.binary)
        return dst


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class PlayerGame:
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
    shortStatusText: str
    gameTimeAndStatusDisplayType: int
    gameTime: int
    gameTimeDisplay: str


@dataclass_json
@dataclass
class PlayerStruct:
    game: PlayerGame
    member: GameMember
    lineupMember: LineupMember


class Player(Cachable):

    _struct: PlayerStruct = None

    def __init__(
        self, game: PlayerGame, member: GameMember, lineupMember: LineupMember
    ):
        self._struct = PlayerStruct(game=game, member=member, lineupMember=lineupMember)

    @classmethod
    def store(cls, game: GameDetails):
        try:
            members = game.members
            for lineupMember in [
                *game.homeCompetitor.lineups.members,
                *game.awayCompetitor.lineups.members,
            ]:
                member = next(filter(lambda x: x.id == lineupMember.id, members), None)
                game = PlayerGame.from_dict(game.to_dict())
                obj = cls(game, member, lineupMember)
                obj.tocache(obj._struct)
        except AttributeError:
            pass

    @classmethod
    def find(cls, query):
        haystack = [PlayerNeedle(name=k.decode()) for k in Storage.hkeys(cls.hash_key)]
        matches = PlayerMatch(haystack=haystack).fuzzy(PlayerNeedle(name=query))
        if not matches:
            return None
        data = Storage.hget(cls.hash_key, matches[0].name.encode())
        if not data:
            return None
        struct = PlayerStruct.from_dict(pickle.loads(data))
        return cls(
            game=struct.game, member=struct.member, lineupMember=struct.lineupMember
        )

    def fromcache(self):
        if data := Storage.hget(__class__.hash_key, self.id):
            return PlayerStruct.from_dict(pickle.loads(data))
        return None

    def tocache(self, res):
        Storage.pipeline().hset(
            __class__.hash_key, self.id, pickle.dumps(res.to_dict())
        ).persist(__class__.hash_key).execute()
        return res

    def load(self) -> bool:
        if self._struct is not None:
            return True
        if not self.isCached:
            return False
        self._struct = self.fromcache()
        return True if self._struct else False

    @property
    def isCached(self) -> bool:
        return Storage.hexists(self.store_key, self.id) == 1

    @property
    def id(self):
        return unidecode(self._struct.member.name)

    @property
    def empty(self) -> RenderResult:
        return EmptyResult()

    @property
    async def image(self) -> Path:
        team = "NationalTeam" if self.isNationalTeam else None
        model = PlayerImage(self._struct.member, team=team)
        return await model.image

    @property
    def isNationalTeam(self) -> bool:
        country_name = COUNTRIES.get(self._struct.game.competitionId, "")
        if not country_name:
            return False
        try:
            international = InternationalCompetitions(country_name)
            return True
        except:
            return False

    @property
    async def message(self) -> RenderResult:
        image = await self.image
        header = f"{to_mono(self._struct.member.name.upper())[:25]:^25}"
        content = ""
        lineupMember: LineupMember = self._struct.lineupMember
        if lineupMember.stats:
            columns = [
                Column(size=25, align=Align.LEFT),
                Column(size=10, align=Align.RIGHT),
            ]
            stats = ((s.name, s.value) for s in lineupMember.stats)
            content = TextOutput.renderColumns(columns=columns, content=stats)
        else:
            content = f"No stats yet"
        return RenderResult(
            message=f"{header}{content}",
            attachment=image.as_posix(),
        )
