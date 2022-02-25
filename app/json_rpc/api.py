from tokenize import group
from typing import Generator
from app import log
import asyncio
from app.json_rpc.message import Message
import json
from uuid import uuid4
from app.config import Config
from botyo.adapter import Adapter, AdapterMessage
from botyo.zson_client.connection import ReceiveMessagesError


class JsonRpcAPI(Adapter):

    reader = None
    writer = None

    async def onReceive(self) -> Generator[Message, None, None]:
        try:
            self.reader, self.writer = await asyncio.open_unix_connection(
                Config.signal.host
            )
            while True:
                msg = await self.reader.readline()
                message: Message = Message.from_dict(json.loads(msg))
                if message.method and group in Config.signal.groups:
                    yield AdapterMessage(
                        group=message.group,
                        source=message.source,
                        message=message.message
                    )
        except Exception as e:
            raise ReceiveMessagesError(e)

    async def onSend(self, receiver: str,
                     message: str, attachment: str = None):
        message_params = {"groupId": receiver, "message": ""}
        if message:
            message_params["message"] = message
        if attachment:
            message_params.setdefault("attachment", attachment)
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
        try:
            self.writer.write(req.encode())
            await self.writer.drain()
        except Exception:
            pass

    async def typing(self, receiver: str, stop=False):
        message_params = {"groupId": receiver}
        if stop:
            message_params["stop"] = "true"

        req = (
            json.dumps(
                {
                    "jsonrpc": "2.0",
                    "method": "sendTyping",
                    "id": uuid4().hex,
                    "params": message_params,
                }
            )
            + "\n"
        )

        try:
            self.writer.write(req.encode())
            await self.writer.drain()
        except Exception as e:
            log.exception(e, exc_info=True)


class JsonRpcApiError(Exception):
    pass
