import time
from sulyo.signal.client import Client, Context
from .core.models import RenderResult
from .core.config import Config
from fuzzelinho import Match, MatchMethod
import asyncio
from .core.storage import Storage
from .connection import Connection
from .models import (
    JunkMessage,
    NoCommand,
    ReceiveError,
    ZSONRequest,
    ZSONResponse,
    CommandDef,
)
import logging
from .connection import ReceiveMessagesError
from typing import Optional


class CommandMatch(Match):
    minRatio = 80
    extensionMatching = False
    method = MatchMethod.PARTIALSET


class AppMeta(type):
    _instance = None
    _cmdMatch: Optional[CommandMatch] = None

    def __call__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(AppMeta, cls).__call__(*args, **kwargs)
        return cls._instance

    def register(cls, cmd: CommandDef):
        logging.debug(f">> REGISTER {cmd}")
        cls().commands.append(cmd)
        CommandDef.registered.append(cmd)

    def clearCommands(cls):
        cls().commands = []
        CommandDef.clearCommands()

    @property
    def cmdMatch(cls) -> CommandMatch:
        if not cls._cmdMatch:
            assert cls._instance
            cls._cmdMatch = CommandMatch(
                [*filter(lambda x: len(x.desc) > 0, cls._instance.commands)]
            )
        return cls._cmdMatch


class App(object, metaclass=AppMeta):

    commands: list[CommandDef] = []

    def __init__(self, config: Config, client: Client):
        Connection.setup(**config.to_dict())  # type: ignore
        Storage.register(config.redis_url)
        self.eventLoop = asyncio.get_event_loop()
        self.queue = asyncio.Queue()
        self.client = client

    def start(self):
        self.eventLoop.create_task(self._produce_consume_messages())
        self.eventLoop.run_forever()

    async def _produce_consume_messages(self, consumers=3):
        producers = [
            asyncio.create_task(self.client.receive(self.queue)),
            asyncio.create_task(self._product_znayko(2)),
        ]
        consumers = [
            asyncio.create_task(self._consume(n)) for n in range(1, consumers + 1)
        ]
        await asyncio.gather(*producers)
        await self.queue.join()
        for c in consumers:
            c.cancel()

    async def _product_znayko(self, name: int) -> None:
        logging.debug(f"[Znayko] Producer #{name} started")
        try:
            async for response in Connection.receive():
                try:
                    assert response
                    assert Connection.id == response.client
                    if response.method == "login":
                        __class__.clearCommands()
                        assert response.commands
                        for cmd in response.commands:
                            __class__.register(cmd)
                    else:
                        assert response.group
                        await self.queue.put(
                            (
                                response,
                                Context(
                                    adapter=self.client,
                                    group=response.group,
                                ),
                                time.perf_counter(),
                            )
                        )
                except AssertionError:
                    continue
                except Exception as e:
                    logging.error(e)
                    continue
        except ReceiveMessagesError as e:
            raise ReceiveError(f"Cannot receive messages: {e}")

    async def _consume(self, name: int) -> None:
        while True:
            try:
                await self._consume_new_item(name)
            except Exception:
                continue

    async def _consume_new_item(self, name: int) -> None:
        command, context, t = await self.queue.get()
        now = time.perf_counter()
        logging.info(f"Consumer #{name} got new job in {now-t:0.5f} seconds")
        try:
            if isinstance(command, ZSONResponse):
                logging.debug(f">> CONSUME Response {command}")
                await context.respond(command.result, command.method)
            elif isinstance(command, CommandDef):
                logging.debug(f">> CONSUME Command {command}")
                if command.response and command.matcher is None:
                    await context.respond(RenderResult(message=command.response))
                else:
                    await context.request(
                        ZSONRequest(method=command.method, query=context.query)
                    )
        except (JunkMessage, NoCommand) as e:
            logging.error(e)
        except Exception as e:
            logging.error(e, exc_info=True)
        finally:
            self.queue.task_done()
