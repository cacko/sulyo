import asyncio
from .message import Message
import json
from uuid import uuid4
from sulyo.config import Config
from sulyo.znayko.connection import ReceiveMessagesError
import logging


from asyncio import Queue
from sulyo.znayko.directives import Directive, NoDirective
from sulyo.znayko.models import (
    Attachment,
    CommandDef,
    JunkMessage,
    NoCommand,
    MessageConsumed,
    ZSONRequest,
)
from sulyo.znayko.core.models import RenderResult
from sulyo.znayko.connection import Connection
import time
import logging
from typing import Optional


class Context:

    group: str = None
    query: str = None
    source: str = None
    lang: str = None
    attachment: Attachment = None

    def __init__(
        self,
        adapter: "Client",
        group: str,
        query: str = None,
        source: str = None,
        lang: str = None,
        attachment: Attachment = None,
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

    async def respond(self, response: RenderResult, method: str = None):
        if self.attachment:
            response.attachment = self.attachment
            response.attachment.path = self.attachment.filename
        await self.adapter.send(
            receiver=self.group,
            message=response.message,
            attachment=response.attachment,
            method=method,
        )


class Client:

    contacts: dict[str, str] = {}
    groups: dict[str, str] = {}

    async def handleDirective(self, message: Message):
        try:
            cmd, response = Directive.parse(
                message=message.message,
                group=message.group,
                source=message.source,
            )
            await self.queue.put(
                (
                    cmd,
                    Context(
                        adapter=self,
                        group=message.group,
                        query=response,
                        source=message.source,
                    ),
                    time.perf_counter(),
                )
            )
            raise MessageConsumed
        except NoDirective:
            pass

    async def handleCommand(self, message: Message):
        lang = "en"
        command, args = CommandDef.parse(message=message.message)
        if not command:
            args = message.message
            command, lang = Directive.match(
                commands=CommandDef.matchers,
                message=message.message,
                group=message.group,
                source=message.source,
            )
        assert command
        logging.info(f">> SIGNAL IN {message}")
        context = Context(
            adapter=self,
            group=message.group,
            query=args,
            lang=lang,
            source=message.source,
            attachment=message.attachment,
        )
        await self.queue.put((command, context, time.perf_counter()))
        raise MessageConsumed

    async def receive(self, queue: Queue):
        Directive.load(self.contacts, self.groups)
        self.queue = queue
        try:
            self.reader, self.writer = await asyncio.open_unix_connection(
                Config.signal.host
            )
            while True:
                try:
                    msg = await self.reader.readline()
                    message = Message.from_dict(json.loads(msg))  # type: ignore
                    assert message.message
                    await self.handleDirective(message)
                    assert Directive.isPermitted(message.group)
                    await self.handleCommand(message)
                except AssertionError:
                    pass
                except MessageConsumed:
                    pass
                except (JunkMessage, NoCommand):
                    pass
        except Exception as e:
            raise ReceiveMessagesError(e)

    async def send(
        self,
        receiver: str,
        message: str,
        attachment: Optional[str] = None,
        method: Optional[str] = None,
    ):
        try:
            message_params = {"groupId": receiver, "message": ""}
            if message:
                message_params["message"] = message
            if attachment:
                message_params["attachment"] = attachment
            req = (
                json.dumps(
                    {
                        "jsonrpc": "2.0",
                        "method": "send",
                        "id": uuid4().hex,
                        "params": message_params,
                    }
                )
                + "\n"
            )
            self.writer.write(req.encode())
            await self.writer.drain()
        except Exception:
            pass


class JsonRpcApiError(Exception):
    pass
