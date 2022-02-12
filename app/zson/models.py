from dataclasses import dataclass
from uuid import uuid4
from dataclasses_json import dataclass_json, Undefined
from enum import Enum
from typing import Optional
from pathlib import Path


class Method(Enum):
    LOGIN = "login"
    WIKI_ARTICLE = "wiki:article"
    AVATAR_MULTIAVATAR = "avatar:multiavatar"
    CONSOLE_TRACEROUTE = "console:traceroute"
    CONSOLE_TCPTRACEROUTE = "console:tcptraceroute"
    CONSOLE_DIG = "console:dig"
    CONSOLE_WHOIS = "console:whois"
    CVE = "cve"
    CVE_SUBSCRIBE = "cve:subscribe"
    CVE_UNSUBSCRIBE = "cve:unsubscribe"
    CVE_SUBSCRIPTIONS = "cve:listsubscriptions"
    GENDER_NAME = "gender:name"
    IPIFY_GEO = "ipify:get"
    LOGO_TEAM = "logo:team"
    MUSIC_SONG = "music:song"
    MUSIC_ALBUMART = "music:albumart"
    MUSIC_LYRICS = "music:lyrics"
    ONTV_COMPETITIONS = "ontv:competitions"
    ONTV_FACTS = "ontv:facts"
    ONTV_LINEUP = "ontv:lineup"
    ONTV_LIVESCORE = "ontv:livescore"
    ONTV_PLAYER = "ontv:player"
    ONTV_STATS = "ontv:stats"
    ONTV_SUBSCRIBE = "ontv:subscribe"
    ONTV_UNSUBSCRIBE = "ontv:unsubscribe"
    ONTV_SUBSCRIPTIONS = "ontv:listsubscriptions"
    ONTV_TV = "ontv:tv"
    ONTV_PRECACHE = "ontv:precache"
    PHOTO_FAKE = "photo:fake"


class JSONType(Enum):
    REQUEST = "request"
    RESPONSE = "response"


@dataclass
class Attachment:
    path: Path
    type: str


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class JSONError:
    code: int
    message: str
    meaning: str


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class JSONMessage:
    id: Optional[str] = None
    method: Optional[Method] = None
    clientId: Optional[str] = None

    def __post_init__(self):
        self.id = uuid4().hex

    def encode(self) -> bytes:
        return self.to_json().encode()


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class JSONResponse(JSONMessage):
    method: Optional[Method] = None
    error: Optional[JSONError] = None
    result: Optional[dict] = None
    message: Optional[str] = None
    attachment: Optional[Attachment] = None
    type: JSONType = JSONType.RESPONSE


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class JSONRequest(JSONMessage):
    source: Optional[str] = None
    query: Optional[str] = None
    utf8mono: Optional[bool] = True
    type: JSONType = JSONType.RESPONSE


class NoCommand(Exception):
    pass


class JunkMessage(Exception):
    pass
