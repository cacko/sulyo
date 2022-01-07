from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from dataclasses_json import dataclass_json, Undefined
from random import choice

from emoji import emojize

from app.core.text import to_mono


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class TimeCache:
    timestamp: datetime
    struct: any


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class Config:
    IPIFY_API_KEY: str
    REDIS_URL: str
    ONTV_API_URL: str
    SETTINGS: dict
    SOCKET_HOST: str
    SOCKET_PORT: int
    MUSIC_SERVICE: str
    GENDER_MALE_NAMES: str
    GENDER_FEMALE_NAMES: str
    COMPETITIONS_JSON: str
    SIGNAL_ACCOUNT: Optional[str] = None
    SIGNAL_GROUPS: Optional[str] = None

    def __post_init__(self):
        self.SOCKET_PORT = int(self.SOCKET_PORT)


@dataclass
class BinaryStruct:
    binary: any
    type: str


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class RenderResult:
    message: Optional[str] = ""
    attachment: Optional[str] = ""


NOT_FOUND = [
    "Няма нищо брат",
    "Отиде коня у реката",
    "...and the horse went into the river",
    "Go fish!",
    "Nod fand!",
]

@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class EmptyResult(RenderResult):
    def __post_init__(self):
        self.message = to_mono(f"{emojize(':construction:')} {choice(NOT_FOUND)}")