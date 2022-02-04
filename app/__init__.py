import time
from dataclasses_json import dataclass_json
from app.json_rpc.message import JunkMessage, Message, NoCommand
from app.scheduler import Scheduler
from app.core.models import Config
from app.core.match import Match
from dataclasses import dataclass
from typing import Callable
from app.core import log
import asyncio
from app.json_rpc import (
    JsonRpcAPI,
    JsonRpcApiError,
    ReceiveMessagesError,
    Context,
)
from app.core import log
from apscheduler.schedulers.asyncio import AsyncIOScheduler


class CommandDefMeta(type):
    registered = []

    def triggered(cls, firestarter: str, message: Message):
        fs = firestarter.lower()
        print(message)
        return next(
            filter(
                lambda x: any(
                    [
                        x.trigger.startswith("+") and x.trigger != message.source,
                        len(x.trigger) == 2 and fs == x.trigger.lower(),
                        len(fs) > 2 and x.trigger.lower().startswith(fs),
                    ]
                ),
                cls.registered,
            ),
            None,
        )


@dataclass_json
@dataclass
class CommandDef(metaclass=CommandDefMeta):
    trigger: str
    handler: Callable


class CommandMatch(Match):
    minRatio = 60
    extensionMatching = False


@dataclass_json
@dataclass
class CommandMatchNeedle:
    trigger: str


class AppMeta(type):
    _instance = None
    _cmdMatch: CommandMatch = None

    def __call__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(AppMeta, cls).__call__(*args, **kwargs)
        return cls._instance

    def register(cls, cmd: CommandDef):
        cls._instance.commands.append(cmd)
        CommandDef.registered.append(cmd)

    @property
    def cmdMatch(cls) -> CommandMatch:
        if not cls._cmdMatch:
            cls._cmdMatch = CommandMatch(
                [*filter(lambda x: len(x.desc) > 0, cls._instance.commands)]
            )
        return cls._cmdMatch


class App(object, metaclass=AppMeta):

    config: Config = None
    api: JsonRpcAPI = None
    commands: list[CommandDef] = []
    eventLoop: asyncio.AbstractEventLoop = None
    queue: asyncio.Queue = None
    scheduler: Scheduler = None
    groups: list[str] = []

    def __init__(self, config: Config):
        self.api = JsonRpcAPI(
            config.SOCKET_HOST, config.SOCKET_PORT, config.SIGNAL_ACCOUNT
        )
        self.config = config
        self.groups = config.SIGNAL_GROUPS.split(",")
        self.eventLoop = asyncio.get_event_loop()
        self.queue = asyncio.Queue()

    def register_scheduler(self):
        scheduler = AsyncIOScheduler(event_loop=self.eventLoop)
        self.scheduler = Scheduler(scheduler, self.config.REDIS_URL, self.api)

    def start(self):
        self.eventLoop.create_task(self._produce_consume_messages())
        self.scheduler.start()
        self.eventLoop.run_forever()

    def _resolve_receiver(self, receiver: str) -> str:
        if receiver not in self.groups:
            raise JsonRpcApiError("receiver is not in self.groups")
        return receiver

    async def _produce_consume_messages(self, producers=1, consumers=3) -> None:
        producers = [
            asyncio.create_task(self._produce(n)) for n in range(1, producers + 1)
        ]
        consumers = [
            asyncio.create_task(self._consume(n)) for n in range(1, consumers + 1)
        ]
        await asyncio.gather(*producers)
        await self.queue.join()
        for c in consumers:
            c.cancel()

    async def _produce(self, name: int) -> None:
        log.info(f"[Botyo] Producer #{name} started")
        try:
            command = next(
                filter(lambda x: x.trigger == "precache", self.commands), None
            )
            context = Context(self.api, "", query="", source="")
            await self.queue.put((command, context, time.perf_counter()))
            async for message in self.api.receive():
                group = message.group
                if group not in self.groups:
                    continue
                try:
                    msg = message.message
                    if not msg:
                        continue
                    trigger, args = [*msg.split(" ", 1), ""][:2]
                    
                    command = CommandDef.triggered(trigger, message)
                    if not command:
                        continue
                    context = Context(
                        self.api, message.group, query=args, source=message.source
                    )
                    await self.queue.put((command, context, time.perf_counter()))
                except (JunkMessage, NoCommand):
                    continue
        except ReceiveMessagesError as e:
            raise JsonRpcApiError(f"Cannot receive messages: {e}")

    async def _consume(self, name: int) -> None:
        while True:
            try:
                await self._consume_new_item(name)
            except Exception:
                continue

    async def _consume_new_item(self, name: int) -> None:
        command, context, t = await self.queue.get()

        now = time.perf_counter()
        log.info(f"Consumer #{name} got new job in {now-t:0.5f} seconds")
        try:
            await command.handler(context)
        except (JunkMessage, NoCommand) as e:
            pass
        except Exception as e:
            log.error(f"[{command.__class__.__name__}] Error: {e}")
            log.error(e, exc_info=True)
            pass
        self.queue.task_done()
