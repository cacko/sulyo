from dataclasses import dataclass
from dataclasses_json import dataclass_json, Undefined
from app.zson.connection import Connection
from app.zson.models import RenderResult
from typing import Optional


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class Context:

    clientId: str = None
    query: str = None
    group: Optional[str] = None
    source: Optional[str] = None
    timezone: Optional[str] = "Europe/London"

    @property
    def connection(self) -> Connection:
        return Connection.client(self.clientId)

    async def send(self, response: RenderResult):
        await self.connection.respond(
            result=response,
        )
