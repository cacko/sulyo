from asyncio import IncompleteReadError
from asyncio.streams import StreamReader, StreamWriter
from app.core.config import Config
from app.zson_client.models import (
    ZSONRequest,
    ZSONResponse,
    ZSONMessage,
    ZSONType,
)
from app import log
from app.core.hash import idhash
from asyncio.streams import open_connection
from typing import Generator
from pathlib import Path
import asyncio
from binascii import unhexlify

DEFAULT_LIMIT = 2 ** 25
BYTEORDER = "little"
CHUNKSIZE = 2 ** 12


class UnknownClientException(Exception):
    pass


class ConnectionMeta(type):

    _instance = None
    _id = None

    def __call__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(ConnectionMeta, cls).__call__(
                *args, **kwargs
            )
        return cls._instance

    async def receive(cls) -> Generator[ZSONResponse, None, None]:
        async for response in cls().onReceive():
            yield response

    async def send(cls, request: ZSONRequest):
        await cls().onSend(request)

    @property
    def id(self) -> str:
        if not self._id:
            self._id = idhash(
                f"{Config.znayko.client}-{Config.znayko.phone}")
        return self._id


class Connection(object, metaclass=ConnectionMeta):

    __reader: StreamReader = None
    __writer: StreamWriter = None
    __registered: bool = False
    __connected: bool = False

    async def onReceive(self) -> Generator[ZSONResponse, None, None]:
        try:
            await self.connect()
            while True:
                try:
                    partSize = await self.__partSize
                    if not partSize:
                        continue
                    log.info(f">> RECEIVE PartSize={partSize}")
                    data = await self.__reader.readexactly(partSize)
                    msg_json = data.decode()
                    message: ZSONMessage = ZSONMessage.from_json(msg_json)
                    if message.ztype == ZSONType.REQUEST:
                        yield None
                    elif message.ztype == ZSONType.RESPONSE:
                        if message.method == "login":
                            self.__registered = True
                        if not self.__registered:
                            log.warning(
                                ">> RECEIVE Ignoring non registered message")
                            raise UnknownClientException
                        response: ZSONResponse = ZSONResponse.from_json(
                            msg_json)
                        if response.attachment:
                            download = await self.__handleAttachment(
                                Path(response.attachment.path).name
                            )
                            response.attachment.path = download
                        log.debug(">> RESPONSE PROCESSED")
                        yield response
                except IncompleteReadError:
                    self.__registered = False
                    self.__connected = False
                    await self.connect(reconnect=True)
        except Exception as e:
            raise ReceiveMessagesError(e)

    @property
    async def __partSize(self) -> int:
        data = await self.__reader.readexactly(4)
        return int.from_bytes(data, byteorder=BYTEORDER, signed=False)

    async def __handleAttachment(self, name) -> Path:
        cache_path = Path(Config.cachable.path)
        if not cache_path.exists():
            cache_path.mkdir(parents=True)
        p = cache_path / name
        with p.open("wb") as f:
            size = await self.__partSize
            size = size * 2
            log.info(f">> ATTACHMENT size={size}")
            while size:
                to_read = CHUNKSIZE if size > CHUNKSIZE else size
                chunk = await self.__reader.read(to_read)
                size -= len(chunk)
                f.write(unhexlify(chunk))
        return p

    async def connect(self, reconnect=False):
        try:
            if reconnect:
                log.info("reconnecting")
                await asyncio.sleep(5)
            self.__reader, self.__writer = await open_connection(
                Config.znayko.host, Config.znayko.port, limit=DEFAULT_LIMIT
            )
            if not self.__registered:
                await self.onSend(ZSONRequest(
                    method="login",
                ))
        except Exception:
            log.info("Reconnect failed")

    async def onSend(self, req: ZSONMessage):
        try:
            req.client = __class__.id
            log.debug(f">> SEND {req}")
            data = req.encode()
            size = len(data).to_bytes(
                4, byteorder=BYTEORDER, signed=False
            )
            log.info(f">> SEND {len(data)}")
            self.__writer.write(size)
            self.__writer.write(data)
            await self.__writer.drain()
        except Exception as e:
            log.exception(e)
            pass


class ReceiveMessagesError(Exception):
    pass


class SendMessageError(Exception):
    pass


class ZsonApiError(Exception):
    pass
