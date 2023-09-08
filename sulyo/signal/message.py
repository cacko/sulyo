from dataclasses import dataclass
from typing import Optional
from dataclasses_json import dataclass_json, Undefined
from enum import Enum


class RPCMethod(Enum):
    RECEIVE = "receive"


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class GroupInfo:
    groupId: str
    type: str


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class Attachment:
    contentType: str
    filename: str
    id: str
    size: int


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class SentMessage:
    destination: Optional[str]
    destinationNumber: Optional[str]
    destinationUuid: Optional[str]
    timestamp: Optional[int]
    message: Optional[str]
    groupInfo: Optional[GroupInfo] = None
    attachments: Optional[list[Attachment]] = None


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
class MessageParamsResult:
    account: str
    envelope: MessageEnvelope


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class MessageParams:
    subscription: int
    result: MessageParamsResult


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class Message:
    jsonrpc: float
    method: Optional[str] = None
    params: Optional[MessageParams] = None

    @property
    def group(self) -> Optional[str]:
        try:
            assert self.params
            envelope = self.params.result.envelope
            if envelope.syncMessage is not None:
                assert envelope.syncMessage.sentMessage
                try:
                    assert envelope.syncMessage.sentMessage.groupInfo
                    return envelope.syncMessage.sentMessage.groupInfo.groupId
                except AssertionError:
                    assert envelope.syncMessage.sentMessage.destination
                    return envelope.syncMessage.sentMessage.destination
            if envelope.dataMessage is not None:
                assert envelope.dataMessage.groupInfo
                return envelope.dataMessage.groupInfo.groupId
        except AssertionError:
            return None

    @property
    def source(self) -> Optional[str]:
        try:
            assert self.params
            return self.params.result.envelope.source
        except AssertionError:
            return None

    @property
    def message(self) -> Optional[str]:
        try:
            assert self.params
            envelope = self.params.result.envelope
            if envelope.syncMessage is not None:
                assert envelope.syncMessage.sentMessage
                return envelope.syncMessage.sentMessage.message
            if envelope.dataMessage is not None:
                return envelope.dataMessage.message
        except AssertionError:
            return None

    @property
    def attachment(self) -> Optional[Attachment]:
        try:
            assert self.params
            envelope = self.params.result.envelope
            assert envelope.syncMessage
            assert envelope.syncMessage.sentMessage
            assert envelope.syncMessage.sentMessage.attachments
            return envelope.syncMessage.sentMessage.attachments[0]
        except AssertionError:
            return None
