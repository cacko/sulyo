from asyncio import Queue
from dataclasses import dataclass
from dataclasses_json import dataclass_json, Undefined
from typing import Generator
from sulyo.znayko.directives import Directive, NoDirective
from sulyo.znayko.models import (
    Attachment,
    CommandDef,
    JunkMessage,
    NoCommand,
    ZSONRequest
)
from sulyo.znayko.core.models import RenderResult
from sulyo.znayko.connection import Connection
import time
import logging
from typing import Optional


class Context:

    adapter = None
    group: str = None
    query: str = None
    source: str = None
    lang: str = None
    attachment: Attachment = None

    def __init__(
        self,
        adapter,
        group: str,
        query: str = None,
        source: str = None,
        lang: str = None,
        attachment: Attachment = None
    ):
        self.adapter = adapter
        self.group = group
        self.query = query
        self.source = source
        self.lang = lang
        self.attachment = attachment
        if self.attachment:
            self.attachment.path = self.attachment.filename

    async def request(self, request: ZSONRequest):
        request.group = self.group
        request.source = self.source
        if self.lang:
            request.lang = self.lang
        if self.attachment:
            request.attachment = self.attachment
            request.attachment.path = self.attachment.filename
        await Connection.send(request)

    async def respond(self, response: RenderResult, method:str=None):
        if self.attachment:
            response.attachment = self.attachment
            response.attachment.path = self.attachment.filename
        await self.adapter.send(
            receiver=self.group,
            message=response.message,
            attachment=response.attachment,
            method=method,
        )


class Typing:
    context: Context = None

    def __init__(self, context: Context):
        self.context = context

    async def __aenter__(self) -> Context:
        await self.context.api.typing(receiver=self.context.group)
        return self.context

    async def __aexit__(self, *args):
        await self.context.api.typing(receiver=self.context.group, stop=True)


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class AdapterMessage:
    group: str
    source: str
    message: str
    attachment: Optional[Attachment] = None


class Adapter:

    contacts: dict[str, str] = {}
    groups: dict[str, str] = {}

    async def send(self, receiver: str, message: str, attachment: str = None, method:str = None):
        await self.onSend(receiver, message, attachment, method)

    async def onReceive(self):
        raise NotImplementedError

    async def receive(
            self,
            queue: Queue
    ) -> Generator[AdapterMessage, None, None]:
        logging.debug(f"[Botyo] Producer #{self.__class__.__name__} started")
        Directive.load(self.contacts, self.groups)
        async for message in self.onReceive():
            try:
                msg = message.message
                if not msg:
                    continue
                try:
                    cmd, response = Directive.parse(**message.to_dict())
                    await queue.put((
                        cmd,
                        Context(
                            adapter=self,
                            group=message.group,
                            query=response,
                            source=message.source
                        ),
                        time.perf_counter())
                    )
                    continue
                except NoDirective:
                    pass
                if not Directive.isPermitted(message.group):
                    logging.info(f"not permitted {message.group}")
                    continue
                lang = "en"
                command, args = CommandDef.parse(**message.to_dict())
                if not command:
                    args = msg
                    command, lang = Directive.match(
                        commands=CommandDef.matchers,
                        **message.to_dict()
                    )
                if not command:
                    continue
                logging.info(f">> SIGNAL IN {message}")
                context = Context(
                    adapter=self,
                    group=message.group,
                    query=args,
                    lang=lang,
                    source=message.source,
                    attachment=message.attachment
                )
                await queue.put((
                    command,
                    context,
                    time.perf_counter())
                )
            except (JunkMessage, NoCommand):
                continue
