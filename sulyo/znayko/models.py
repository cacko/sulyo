from dataclasses import dataclass
from uuid import uuid4
from dataclasses_json import dataclass_json, Undefined
from enum import Enum
from typing import Optional
from pathlib import Path
from .core.models import ErrorResult, RenderResult
from fuzzelinho import Match, MatchMethod
import logging

class ZSONType(Enum):
    REQUEST = "request"
    RESPONSE = "response"


@dataclass_json
@dataclass
class Chat:
    msg: str


class ChatMatch(Match):
    minRatio = 95
    method = MatchMethod.WRATIO


class CommandDefMeta(type):
    registered = []
    _trans = None

    def parse(cls, message: str, **kwds) -> tuple[Optional["CommandDef"], Optional[str]]:
        message = message.lower()
        if message.startswith("/"):
            trigger, args = [*message.lstrip("/").split(" ", 1), ""][:2]
            triggers = filter(lambda x: not x.matcher, cls.registered)
            return (
                next(
                    filter(
                        lambda x: any(
                            [
                                x.method.split(":")[-1] == trigger,
                                len(trigger) > 2
                                and (
                                    x.method
                                    if ":" in trigger
                                    else x.method.split(":")[-1]
                                ).startswith(trigger),
                            ]
                        ),
                        triggers,
                    ),
                    None,
                ),
                args,
            )
        cmds = filter(lambda x: x.matcher is not None, cls.registered)
        for cmd in cmds:
            matcher = ChatMatch(haystack=[Chat(msg=cmd.matcher)])
            if matcher.fuzzy(Chat(msg=message)):
                return cmd, message
        return None, None

    def clearCommands(cls):
        cls.registered = []

    @property
    def textGenerate(cls) -> Optional["CommandDef"]:
        return next(filter(lambda x: x.method == "text:generate", cls.registered), None)

    @property
    def matchers(cls) -> list["CommandDef"]:
        return list(filter(lambda x: x.matcher, cls.registered))

    def transliterate(cls, txt: str):
        if not cls._trans:
            lat = "qwertyuiopasdfghjkl`zxcvbnm"
            cyr = "явертъуиопасдфгхйклчзьцжбнм"
            cls._trans = txt.maketrans(cyr, lat)
        return txt.translate(cls._trans)


class ZSONMatcher(Enum):
    PHRASE = "phrase"
    SOURCE = "source"


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class CommandDef(metaclass=CommandDefMeta):
    method: str
    desc: Optional[str] = None
    response: Optional[str] = None
    matcher: Optional[str] = None


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class Attachment:
    path: Path
    contentType: str
    duration: Optional[int] = None
    filename: Optional[str] = None
    width: Optional[int] = None
    height: Optional[int] = None
    id: Optional[str] = None


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class ZSONError:
    code: int
    message: str
    meaning: str


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class ZSONMessage:
    ztype: ZSONType
    group: Optional[str] = None
    id: Optional[str] = None
    method: Optional[str] = None
    client: Optional[str] = None

    def __post_init__(self):
        self.id = uuid4().hex

    def encode(self) -> bytes:
        return self.to_json().encode() # type: ignore

@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class ZSONResponse(ZSONMessage):
    method: Optional[str] = None
    error: Optional[ZSONError] = None
    message: Optional[str] = None
    attachment: Optional[Attachment] = None
    ztype: ZSONType = ZSONType.RESPONSE
    commands: Optional[list[CommandDef]] = None

    @property
    def result(self) -> RenderResult:
        logging.debug(self)
        attachment_path = None
        if self.attachment is not None and self.attachment.path.exists():
            attachment_path = self.attachment.path.absolute().as_posix()
        if all([not self.message, not attachment_path]):
            return ErrorResult()
        return RenderResult(message=self.message, attachment=attachment_path)


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class ZSONRequest(ZSONMessage):
    source: Optional[str] = None
    query: Optional[str] = None
    lang: Optional[str] = None
    attachment: Optional[Attachment] = None
    utf8mono: Optional[bool] = False
    ztype: ZSONType = ZSONType.REQUEST


class NoCommand(Exception):
    pass


class JunkMessage(Exception):
    pass


class ReceiveError(Exception):
    pass


class MessageConsumed(Exception):
    pass