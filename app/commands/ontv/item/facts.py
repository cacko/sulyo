from queue import Empty
from app.commands.ontv.item.livescore_details import ParserDetails
from app.commands.ontv.item.models import *
from app.core.cacheable import Cachable
from stringcase import alphanumcase


class Facts(Cachable):

    __item: ParserDetails = None
    _struct: list[GameFact] = None

    def __init__(self, item: Event):
        self.__item = item

    @property
    def id(self):
        raise f"facts:{self.__item.idEvent}"

    @property
    async def message(self) -> str:
        if not self.load():
            details = await ParserDetails.get(self.__item.details)
            self._struct: list[GameFact] = self.tocache(details.facts)
        if not self._struct:
            return None
        return "\n\n".join([x.text for x in self._struct])
