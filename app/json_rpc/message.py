from ast import Str
from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from dataclasses_json import dataclass_json, Undefined
from random import choice
from enum import Enum


class Method(Enum):
    RECEIVE = "receive"


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class GroupInfo:
    groupId: str
    type: str


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class SentMessage:
    destination: Optional[str]
    destinationNumber: Optional[str]
    destinationUuid: Optional[str]
    timestamp: Optional[int]
    message: Optional[str]
    groupInfo: Optional[GroupInfo] = None


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class SyncMessage:
    sentMessage: Optional[SentMessage] = None


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class ReceiptMessage:
    when: int
    isDelivery: bool
    isRead: bool
    isViewed: bool


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class DataMessage:
    timestamp: Optional[int]
    message: Optional[str]
    groupInfo: Optional[GroupInfo] = None


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class MessageEnvelope:
    source: str
    sourceName: str
    timestamp: int
    syncMessage: Optional[SyncMessage] = None
    receiptMessage: Optional[ReceiptMessage] = None
    dataMessage: Optional[DataMessage] = None


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class MessageParams:
    account: str
    envelope: MessageEnvelope


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class Message:
    jsonrpc: float
    method: Optional[str] = None
    params: Optional[MessageParams] = None

    @property
    def group(self) -> str:
        try:
            if self.params.envelope.syncMessage is not None:
                return self.params.envelope.syncMessage.sentMessage.groupInfo.groupId
            if self.params.envelope.dataMessage is not None:
                return self.params.envelope.dataMessage.groupInfo.groupId
        except:
            return None

    @property
    def source(self) -> str:
        try:
            return self.params.envelope.source
        except:
            return None

    @property
    def message(self) -> str:
        try:
            if self.params.envelope.syncMessage is not None:
                return self.params.envelope.syncMessage.sentMessage.message
            if self.params.envelope.dataMessage is not None:
                return self.params.envelope.dataMessage.message
        except:
            return None


class NoCommand(Exception):
    pass


class JunkMessage(Exception):
    pass
