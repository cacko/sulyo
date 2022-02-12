import time
import asyncio
from asyncio import IncompleteReadError, open_connection
from typing import Generator
import logging
from os import environ
import json
from uuid import uuid4
from dataclasses import dataclass
from dataclasses_json import dataclass_json, Undefined
from enum import Enum
from typing import Optional
from pathlib import Path
from emoji import emojize
from random import choice

from hashlib import blake2b


def idhash(text, size=20):
    h = blake2b(digest_size=size)
    h.update(text.encode())
    return h.hexdigest()


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
class RenderResult:
    method: Method
    message: Optional[str] = ""
    attachment: Optional[Attachment] = None


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
        self.message = f"{emojize(':construction:')} {choice(NOT_FOUND)}"


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
    clientId: Optional[str] = None
    message: Optional[str] = None
    attachment: Optional[Attachment] = None
    type: JSONType = JSONType.RESPONSE
    id: Optional[str] = None


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class JSONRequest(JSONMessage):
    method: Optional[Method] = None
    source: Optional[str] = None
    clientId: Optional[str] = None
    query: Optional[str] = None
    utf8mono: Optional[bool] = True
    type: JSONType = JSONType.RESPONSE


class NoCommand(Exception):
    pass


class JunkMessage(Exception):
    pass


logging.basicConfig(
    level=getattr(logging, environ.get("BOTYO_LOG_LEVEL", "WARN")),
    format="%(filename)s %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("BOTYO")


ETX = b"\x03"
EOF = b"\x04"


class JsonRpcAPI:

    __host: str = None
    __port: int = None
    reader = None
    writer = None
    __registered = False
    __id: str = None

    def __init__(self, host: str, port: int):
        self.__host = host
        self.__port = port

    def id(self) -> str:
        if not self.__id:
            self.__id = idhash("BOTYO-+447479303304")
        return self.__id

    async def receive(self) -> Generator[str, None, None]:
        try:
            self.reader, self.writer = await open_connection(
                self.__host, self.__port
            )
            while True:
                try:
                    msg = await self.reader.readuntil(ETX)
                    msg = json.loads(msg[:-1].decode())
                    print(msg)
                    if not self.__registered:
                        await self.reader.readuntil(EOF)

                        resp = JSONResponse(
                            method=Method.LOGIN,
                            clientId=self.id
                        )
                        print(resp)
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
                            p = Path("./cache") / msg.get("id")
                            with p.open("wb") as f:
                                while True:
                                    data = self.reader.read(1024)
                                    if data.endswith(EOF):
                                        f.write(data[:-1])
                                        break
                                    f.write(data)
                            print(p)
                        yield msg
                except IncompleteReadError:
                    self.__registered = False
                    await self.reconnect()
        except Exception as e:
            raise ReceiveMessagesError(e)

    async def reconnect(self):
        try:
            log.info("reconnecting")
            await asyncio.sleep(5)
            self.reader, self.writer = await open_connection(
                self.__host, self.__port
            )
        except Exception:
            log.info("Reconnect failed")

    async def send(self, req: JSONMessage):
        try:
            log.info(f"sending {req}")
            self.writer.write(req.encode() + ETX + EOF)
            await self.writer.drain()
        except Exception:
            pass


class ReceiveMessagesError(Exception):
    pass


class SendMessageError(Exception):
    pass


class JsonRpcApiError(Exception):
    pass


class ClientMeta(type):
    _instance = None

    def __call__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(ClientMeta, cls).__call__(*args, **kwargs)
        return cls._instance

    async def send(cls, message: str):
        await cls._instance.api.send(message)


class Client(object, metaclass=ClientMeta):

    eventLoop: asyncio.AbstractEventLoop = None
    queue: asyncio.Queue = None
    api: JsonRpcAPI = None

    def __init__(self, host, port):
        self.api = JsonRpcAPI(host, port)
        self.eventLoop = asyncio.get_event_loop()
        self.queue = asyncio.Queue()

    def start(self):
        self.eventLoop.create_task(self._produce_consume_messages())
        self.eventLoop.run_forever()
        self.eventLoop.create_task(self.random())

    async def random(self):
        pass
        # await self.api.send(f"{json.dumps({'id': uuid4().hex})}")
        # for x in range(10):
        #     time.sleep(x + 1)
        #     await self.api.send("bla bla")

    def _resolve_receiver(self, receiver: str) -> str:
        if receiver not in self.groups:
            raise JsonRpcApiError("receiver is not in self.groups")
        return receiver

    async def _produce_consume_messages(self, producers=1, consumers=3):
        producers = [
            asyncio.create_task(
                self._produce(n)) for n in range(1, producers + 1
                                                 )
        ]
        consumers = [
            asyncio.create_task(
                self._consume(n)) for n in range(1, consumers + 1)
        ]
        await asyncio.gather(*producers)
        await self.queue.join()
        for c in consumers:
            c.cancel()

    async def _produce(self, name: int) -> None:
        log.info(f"[Botyo] Producer #{name} started")
        try:
            async for message in self.api.receive():
                await self.queue.put((message, time.perf_counter()))
        except ReceiveMessagesError as e:
            raise JsonRpcApiError(f"Cannot receive messages: {e}")

    async def _consume(self, name: int) -> None:
        while True:
            try:
                await self._consume_new_item(name)
            except Exception:
                continue

    async def _consume_new_item(self, name: int) -> None:
        message, t = await self.queue.get()
        print(message)
        now = time.perf_counter()
        log.info(f"Consumer #{name} got new job in {now-t:0.5f} seconds")
        try:
            await self.random()
        except SendMessageError as e:
            log.error(f"SendMessageError: {e}")
            log.error(e, exc_info=True)
        except Exception as e:
            log.error(f"Error: {e}")
            log.error(e, exc_info=True)
        self.queue.task_done()


if __name__ == "__main__":
    client = Client("127.0.0.1", 7777)
    client.start()
