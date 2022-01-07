from email import message
from pickletools import uint4
from typing import Generator, Optional
from app.core import log
import asyncio
from jsonrpcclient import request_json
from app.json_rpc.message import Message
import json
from uuid import uuid4
from app.core.text import to_mono
from rich import print_json


class JsonRpcAPI:

    __host: str = None
    __port: int = None
    __phone: str = None
    reader = None
    writer = None

    def __init__(self, service_host: str, service_port: int, phone_number: str = ""):
        self.__host = service_host
        self.__port = service_port
        self.__phone = phone_number

    async def receive(self) -> Generator[Message, None, None]:
        try:
            self.reader, self.writer = await asyncio.open_unix_connection(self.__host)
            while True:
                msg = await self.reader.readline()
                message = Message.from_dict(json.loads(msg))
                if message.method:
                    yield message
        except Exception as e:
            raise ReceiveMessagesError(e)

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

    async def send(self, receiver: str, message: str, attachment: str = None):
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
        except:
            pass


class ReceiveMessagesError(Exception):
    pass


class SendMessageError(Exception):
    pass


class JsonRpcApiError(Exception):
    pass
