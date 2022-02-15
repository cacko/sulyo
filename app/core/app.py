import time
from app.core.models import RenderResult
from app.json_rpc.message import (
    JunkMessage,
    NoCommand
)
from app.core.config import Config
from app.core.match import Match
import asyncio
from app.json_rpc import (
    JsonRpcAPI,
    JsonRpcApiError,
    ReceiveMessagesError,
    Context,
)
from app import log
from app.zson_client.connection import Connection
from app.zson_client.models import (
    ZSONRequest,
    ZSONResponse,
    CommandDef
)


class CommandMatch(Match):
    minRatio = 60
    extensionMatching = False


class AppMeta(type):
    _instance = None
    _cmdMatch: CommandMatch = None

    def __call__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(AppMeta, cls).__call__(*args, **kwargs)
        return cls._instance

    def register(cls, cmd: CommandDef):
        log.debug(f">> REGISTER {cmd}")
        cls().commands.append(cmd)
        CommandDef.registered.append(cmd)

    @property
    def cmdMatch(cls) -> CommandMatch:
        if not cls._cmdMatch:
            cls._cmdMatch = CommandMatch(
                [*filter(lambda x: len(x.desc) > 0, cls._instance.commands)]
            )
        return cls._cmdMatch


class App(object, metaclass=AppMeta):

    api: JsonRpcAPI = None
    commands: list[CommandDef] = []
    eventLoop: asyncio.AbstractEventLoop = None
    queue: asyncio.Queue = None
    groups: list[str] = []

    def __init__(self):
        self.api = JsonRpcAPI()
        self.groups = Config.signal.groups
        self.eventLoop = asyncio.get_event_loop()
        self.queue = asyncio.Queue()

    def start(self):
        self.eventLoop.create_task(self._produce_consume_messages())
        self.eventLoop.run_forever()

    def _resolve_receiver(self, receiver: str) -> str:
        if receiver not in self.groups:
            raise JsonRpcApiError("receiver is not in self.groups")
        return receiver

    async def _produce_consume_messages(self, consumers=3):
        producers = [
            asyncio.create_task(self._produce_signal(1)),
            asyncio.create_task(self._product_znayko(2)),
        ]
        consumers = [
            asyncio.create_task(self._consume(n))
            for n in range(1, consumers + 1)
        ]
        await asyncio.gather(*producers)
        await self.queue.join()
        for c in consumers:
            c.cancel()

    async def _produce_signal(self, name: int) -> None:
        log.debug(f"[Botyo] Producer #{name} started")
        try:
            async for message in self.api.receive():
                group = message.group
                if group not in self.groups:
                    continue
                try:
                    msg = message.message
                    if not msg or not msg.startswith("/"):
                        continue
                    trigger, args = [*msg.lstrip("/").split(" ", 1), ""][:2]
                    command = CommandDef.triggered(trigger)
                    if not command:
                        continue
                    log.info(f">> SIGNAL IN {message}")
                    context = Context(
                        api=self.api,
                        group=message.group,
                        query=args,
                        source=message.source
                    )
                    await self.queue.put((
                        command,
                        context,
                        time.perf_counter())
                    )
                except (JunkMessage, NoCommand):
                    continue
        except ReceiveMessagesError as e:
            raise JsonRpcApiError(f"Cannot receive messages: {e}")

    async def _product_znayko(self, name: int) -> None:
        log.debug(f"[Znayko] Producer #{name} started")
        try:
            async for response in Connection.receive():
                try:
                    if not response:
                        continue
                    if Connection.id != response.client:
                        log.warning(
                            f"Wrong clientId response {response.client}")
                        continue
                    if response.method == "login":
                        for cmd in response.commands:
                            __class__.register(cmd)
                        continue
                    if response.group not in self.groups:
                        log.warning(
                            f"Invalid response groupId -> {response.group}")
                        continue
                    await self.queue.put((
                        response,
                        Context(
                            api=self.api,
                            group=response.group,
                        ),
                        time.perf_counter())
                    )
                except Exception as e:
                    log.exception(e)
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
            if isinstance(command, ZSONResponse):
                log.debug(f">> CONSUME Response {command}")
                await context.respond(command.result)
            elif isinstance(command, CommandDef):
                log.debug(f">> CONSUME Command {command}")
                if command.response:
                    await context.respond(RenderResult(
                        message=command.response
                    ))
                else:
                    await context.request(ZSONRequest(
                        method=command.method,
                        query=context.query
                    ))
        except (JunkMessage, NoCommand) as e:
            log.error(e)
            pass
        except Exception as e:
            log.error(e, exc_info=True)
            pass
        self.queue.task_done()
