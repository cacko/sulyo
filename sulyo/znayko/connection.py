from asyncio import IncompleteReadError
from asyncio.streams import StreamReader, StreamWriter
from .models import (
    ZSONRequest,
    ZSONResponse,
    ZSONMessage,
    ZSONType,
)
from typing import Optional
import logging
from asyncio.streams import open_connection
from typing import AsyncGenerator, Union, Generator
from pathlib import Path
import asyncio
from corestring import string_hash
from binascii import hexlify, unhexlify

DEFAULT_LIMIT = 2**25
BYTEORDER = "little"
CHUNKSIZE = 2**12


class UnknownClientException(Exception):
    pass


class ConnectionMeta(type):

    _instance = None
    _id = None
    _host = None
    _port = None
    _storage = None
    _client = None
    _phone = None
    _attachments = None

    def __call__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(ConnectionMeta, cls).__call__(*args, **kwargs)
        return cls._instance

    def setup(cls, host, port, storage, client, phone, attachments, **kwds):
        cls._host = host
        cls._port = port
        cls._storage = storage
        cls._client = client
        cls._phone = phone
        cls._attachments = attachments

    async def receive(cls) -> AsyncGenerator[ZSONResponse, None]:
        async for response in cls().onReceive():
            yield response

    async def send(cls, request: ZSONRequest):
        await cls().onSend(request)

    @property
    def id(cls) -> str:
        if not cls._id:
            cls._id = string_hash(f"{cls._client}-{cls._phone}")
        return cls._id


class Connection(object, metaclass=ConnectionMeta):

    __registered: bool = False

    async def onReceive(self) -> AsyncGenerator[ZSONResponse, None]:
        try:
            await self.connect()
            while True:
                try:
                    partSize = await self.__partSize
                    if not partSize:
                        continue
                    logging.debug(f">> RECEIVE PartSize={partSize}")
                    data = await self.__reader.readexactly(partSize)
                    msg_json = data.decode()
                    logging.debug(f">> {msg_json}")
                    message: ZSONMessage = ZSONMessage.from_json(msg_json)  # type: ignore
                    assert message.ztype == ZSONType.RESPONSE
                    if message.method == "login":
                        self.__registered = True
                    if not self.__registered:
                        logging.warning(">> RECEIVE Ignoring non registered message")
                        raise UnknownClientException
                    response: ZSONResponse = ZSONResponse.from_json(msg_json) #type: ignore
                    if response.attachment:
                        download = await self.__handleAttachment(
                            Path(response.attachment.path).name
                        )
                        if not download:
                            response.attachment = None
                        else:
                            response.attachment.path = download
                        logging.warning(response)
                    logging.debug(">> RESPONSE PROCESSED")
                    yield response
                except AssertionError:
                    pass
                except IncompleteReadError:
                    self.__registered = False
                    await self.connect(reconnect=True)
        except Exception as e:
            self.__registered = False
            await self.connect(reconnect=True)
            raise ReceiveMessagesError(e)

    @property
    async def __partSize(self) -> int:
        data = await self.__reader.readexactly(4)
        return int.from_bytes(data, byteorder=BYTEORDER, signed=False)

    async def __handleAttachment(self, name) -> Optional[Path]:
        try:
            assert __class__._storage
            cache_path = Path(__class__._storage)
            if not cache_path.exists():
                cache_path.mkdir(parents=True)
            p = cache_path / name
            with p.open("wb") as f:
                size = await self.__partSize
                size = size * 2
                logging.debug(f">> ATTACHMENT size={size}")
                while size:
                    to_read = CHUNKSIZE if size > CHUNKSIZE else size
                    chunk = await self.__reader.read(to_read)
                    size -= len(chunk)
                    if size % 2:
                        chunk = chunk[:-1]
                    f.write(unhexlify(chunk))
            return p
        except AssertionError:
            return None
        except Exception as e:
            logging.exception(e)
            return None

    async def connect(self, reconnect=False):
        try:
            if reconnect:
                logging.debug("reconnecting")
                await asyncio.sleep(5)
            self.__reader, self.__writer = await open_connection(
                __class__._host, __class__._port, limit=DEFAULT_LIMIT
            )
            if not self.__registered:
                await self.onSend(
                    ZSONRequest(
                        method="login",
                    )
                )
        except Exception:
            logging.debug("Reconnect failed")

    async def onSend(self, req: Union[ZSONRequest, ZSONResponse]):
        try:
            req.client = __class__.id
            logging.debug(f">> SEND {req}")
            try:
                assert req.attachment
                assert req.attachment.filename
                req.attachment.path = Path(req.attachment.filename)
            except AssertionError:
                pass
            data = req.encode()
            size = len(data).to_bytes(4, byteorder=BYTEORDER, signed=False)
            logging.debug(f">> SEND {len(data)}")
            self.__writer.write(size)
            self.__writer.write(data)
            assert req.attachment
            assert req.attachment.id
            assert __class__._attachments
            p = Path(__class__._attachments) / req.attachment.id
            assert req.attachment.filename
            req.attachment.path = Path(req.attachment.filename)
            size = p.stat().st_size
            logging.debug(f">> SEND {size} ATTACGHMENT")
            self.__writer.write(
                size.to_bytes(4, byteorder=BYTEORDER, signed=False),
            )
            with p.open("rb") as f:
                while size:
                    to_read = CHUNKSIZE if size > CHUNKSIZE else size
                    chunk = f.read(to_read)
                    if chunk % 2:
                        chunk = chunk[:-1]
                    self.__writer.write(hexlify(chunk))
                    size -= to_read
            logging.debug(f">> Send attachment {size}")
            await self.__writer.drain()
        except AssertionError:
            return
        except Exception as e:
            logging.exception(e)


class ReceiveMessagesError(Exception):
    pass


class SendMessageError(Exception):
    pass


class ZsonApiError(Exception):
    pass
