from queue import Empty
from app.commands.ontv.item.livescore_details import ParserDetails
from app.core import to_mono, log
from app.commands.ontv.item.models import *


class Facts:

    __item: ParserDetails = None

    def __init__(self, item: Event):
        self.__item = item

    @property
    def empty(self) -> RenderResult:
        return EmptyResult()

    @property
    async def message(self) -> RenderResult:
        details = await ParserDetails.get(self.__item.details)
        facts: list[GameFact] = details.facts
        return RenderResult(message=to_mono("\n\n".join([x.text for x in facts])))
