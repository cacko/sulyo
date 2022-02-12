from asyncio import IncompleteReadError
from asyncio.streams import StreamReader, StreamWriter
from app.core.config import Config
from app.zson.models import (
    JSONRequest,
    JSONResponse,
    JSONMessage,
    Method,
)
import json
from app import log
from app.core.hash import idhash
from asyncio.streams import open_connection
from typing import Generator
from pathlib import Path
import asyncio

from client import Attachment

ETX = b"\x03"
EOF = b"\x04"


class UnknownClientException(Exception):
    pass


class ConnectionMeta(type):

    connections = {}

    def client(cls, clientId: str):
        if clientId not in cls._connections:
            raise UnknownClientException
        return cls.connections.get(clientId)


class Connection(object, metaclass=ConnectionMeta):

    __reader: StreamReader = None
    __writer: StreamWriter = None
    __clientId: str = None
    __registered: bool = False

    def __init__(
        self,
        reader: StreamReader,
        writer: StreamWriter
    ):
        self.__reader = reader
        self.__writer = writer

    @property
    def id(self) -> str:
        if not self.__clientId:
            self.__clientId = idhash(
                f"{Config.znayko.client}-{Config.znayko.phone}")
        return self.__clientId

    async def receive(self) -> Generator[str, None, None]:
        try:
            self.__reader, self.__writer = await open_connection(
                Config.znayko.host, Config.znayko.port
            )
            while True:
                try:
                    msg = await self.__reader.readuntil(ETX)
                    msg = json.loads(msg[:-1].decode())
                    log.debug(msg)
                    if not self.__registered:
                        await self.__reader.readuntil(EOF)

                        resp = JSONResponse(
                            method=Method.LOGIN,
                            clientId=self.id
                        )
                        log.debug(resp)
                        await self.send(resp)
                        self.__registered = True
                        req = JSONRequest(
                            method=Method.WIKI_ARTICLE,
                            query="sofia",
                            source="fake"
                        )
                        await self.send(req)
                        yield None
                    else:
                        if "attachment" in msg:
                            download = await self.__handleAttachment(
                                msg.get("id")
                            )
                            attachment: Attachment = Attachment.from_dict(
                                msg.get("attachment")
                            )
                            attachment.path = download
                            msg["attachment"] = attachment.to_dict()
                        yield msg
                except IncompleteReadError:
                    self.__registered = False
                    await self.reconnect()
        except Exception as e:
            raise ReceiveMessagesError(e)

    async def __handleAttachment(self, id) -> Path:
        p = Path(Config.cachable.path) / id
        with p.open("wb") as f:
            while True:
                data = await self.__reader.read(1024)
                if data.endswith(EOF):
                    f.write(data[:-1])
                    break
                f.write(data)
        return p

    async def reconnect(self):
        try:
            log.info("reconnecting")
            await asyncio.sleep(5)
            self.__reader, self.__writer = await open_connection(
                Config.znayko.host, Config.znayko.port
            )
        except Exception:
            log.info("Reconnect failed")

    async def send(self, req: JSONMessage):
        try:
            log.debug(f"sending {req}")
            self.__writer.write(req.encode() + ETX + EOF)
            await self.__writer.drain()
        except Exception:
            pass


class ReceiveMessagesError(Exception):
    pass


class SendMessageError(Exception):
    pass


class JsonRpcApiError(Exception):
    pass
