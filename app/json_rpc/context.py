from app.core.models import RenderResult
from app.json_rpc.api import JsonRpcAPI
from app.zson_client.connection import Connection
from app.zson_client.models import ZSONRequest
from app import log

class Context:

    api: JsonRpcAPI = None
    group: str = None
    query: str = None
    source: str = None

    def __init__(
        self, api: JsonRpcAPI,
        group: str,
        query: str = None, source: str = None
    ):
        self.api = api
        self.group = group
        self.query = query
        self.source = source

    async def request(self, request: ZSONRequest):
        request.group = self.group
        request.source = self.source
        await Connection.send(request)

    async def respond(self, response: RenderResult):
        log.debug(f">> RESPOND {RenderResult}")
        await self.api.send(
            receiver=self.group,
            message=response.message,
            attachment=response.attachment,
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
