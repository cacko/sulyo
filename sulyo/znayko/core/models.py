from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Any
from dataclasses_json import dataclass_json, Undefined
from emoji import emojize
from random import choice


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class TimeCache:
    timestamp: datetime
    struct: Any


@dataclass
class BinaryStruct:
    binary: Any
    type: str


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class RenderResult:
    message: Optional[str] = None
    attachment: Optional[str] = None


NOT_FOUND = [
    "Няма нищо брат",
    "Отиде коня у реката",
    "...and the horse went into the river",
    "Go fish!",
    "Nod fand!",
]


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class ErrorResult(RenderResult):
    def __post_init__(self):
        if not self.message:
            self.message = choice(NOT_FOUND)
        self.message = f"{emojize(':warning:')} {self.message}"
