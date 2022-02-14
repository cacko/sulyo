from dataclasses import dataclass
from uuid import uuid4
from dataclasses_json import dataclass_json, Undefined
from enum import Enum
from typing import Optional
from pathlib import Path
from app.core.models import ErrorResult, RenderResult


class ZSONType(Enum):
    REQUEST = "request"
    RESPONSE = "response"


class CommandDefMeta(type):
    registered = []

    def triggered(cls, firestarter: str):
        fs = firestarter.lower()
        return next(
            filter(
                lambda x: any(
                    [
                        x.method.split(":")[-1] == fs,
                        len(fs) > 2 and x.method.startswith(fs),
                        len(fs) > 2 and x.method.split(
                            ":")[-1].startswith(fs)
                    ]
                ),
                cls.registered,
            ),
            None,
        )


@dataclass_json
@dataclass
class CommandDef(metaclass=CommandDefMeta):
    method: str
    desc: Optional[str] = None
    response: Optional[str] = None


@dataclass
class Attachment:
    path: Path
    type: str


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class ZSONError:
    code: int
    message: str
    meaning: str


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class ZSONMessage:
    type: ZSONType
    group: Optional[str] = None
    id: Optional[str] = None
    method: str = None
    client: Optional[str] = None

    def __post_init__(self):
        self.id = uuid4().hex

    def encode(self) -> bytes:
        return self.to_json().encode()


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class ZSONResponse(ZSONMessage):
    method: str = None
    error: Optional[ZSONError] = None
    message: Optional[str] = None
    attachment: Optional[Attachment] = None
    type: ZSONType = ZSONType.RESPONSE
    commands: Optional[list[CommandDef]] = None

    @property
    def result(self) -> RenderResult:
        attachment_path = None
        if self.attachment is not None and self.attachment.path.exists():
            attachment_path = self.attachment.path.absolute().as_posix()
        if all([not self.message, not attachment_path]):
            return ErrorResult()
        return RenderResult(
            message=self.message,
            attachment=attachment_path
        )


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class ZSONRequest(ZSONMessage):
    source: Optional[str] = None
    query: Optional[str] = None
    utf8mono: Optional[bool] = False
    type: ZSONType = ZSONType.REQUEST


class NoCommand(Exception):
    pass


class JunkMessage(Exception):
    pass
