from typing import AsyncGenerator
import asyncio
from app.signal.message import Message
import json
from uuid import uuid4
from app.config import Config
from botyo_client.adapter import Adapter, AdapterMessage, Attachment as AdapterAttachment
from botyo_client.connection import ReceiveMessagesError
import logging


class Client(Adapter):

    reader = None
    writer = None

    async def onReceive(self) -> AsyncGenerator[AdapterMessage, None]:
        try:
            self.reader, self.writer = await asyncio.open_unix_connection(
                Config.signal.host
            )
            while True:
                msg = await self.reader.readline()
                message: Message = Message.from_dict(json.loads(msg))  # type: ignore
                att = None
                if message.attachment:
                    att = AdapterAttachment(
                        path=message.attachment.filename,
                        contentType=message.attachment.contentType,
                        id=message.attachment.id,
                        filename=message.attachment.filename
                    )
                yield AdapterMessage(
                    group=message.group,
                    source=message.source,
                    message=message.message,
                    attachment=att,
                )
        except Exception as e:
            raise ReceiveMessagesError(e)

    async def onSend(
        self, receiver: str, message: str, attachment: str = None, method: str = None
    ):
        if method and method == "nowplaying":
            return
            # req = (
            #     json.dumps(
            #         {
            #             "jsonrpc": "2.0",
            #             "method": "updateProfile",
            #             "id": uuid4().hex,
            #             "params": {
            #                 "about": message
            #             },
            #         }
            #     )
            #     + "\n"
            # )
        else:
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
            logging.exception(e, exc_info=True)


class JsonRpcApiError(Exception):
    pass
