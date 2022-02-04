from app.commands.cve.models import CVEResponse
from app.core import Request
from datetime import datetime, timedelta, timezone
from app.core.cacheable import TimeCacheable
from app.core.output import to_mono
from .components import CVEHeader
from stringcase import alphanumcase
from app.core import log


class CVE(TimeCacheable):
    cachetime: timedelta = timedelta(minutes=30)

    __query: str = None
    __ignoreCache: bool = False

    def __init__(self, query: str = None, ignoreCache: bool = False) -> None:
        self.__query = query
        self.__ignoreCache = ignoreCache
        super().__init__()

    @property
    def id(self):
        if self.__query:
            return f"query{alphanumcase(self.__query)}"
        return "recent"

    async def fetch(self):
        args = {}
        if self.__query:
            args["keyword"] = self.__query
        req = Request("https://services.nvd.nist.gov/rest/json/cves/1.0", params=args)
        json = await req.json
        log.warning(f"fetch size {len(json['result'])}")
        return self.tocache(CVEResponse.from_dict(json))

    @property
    async def response(self) -> CVEResponse:
        if self.__ignoreCache or (not self.load()):
            log.warning(f"trigger fetch")
            self._struct = await self.fetch()
        return self._struct.struct

    @property
    async def message(self):
        response: CVEResponse = await self.response
        rows = [
            CVEHeader(cve.id, cve.description, cve.severity, cve.attackVector)
            for cve in response.result.CVE_Items
        ]
        return "\n".join(map(str, rows))
