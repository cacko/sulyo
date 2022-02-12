from app.core.models import RenderResult
from app.core import Request


class BaseMeta(type):
    @property
    def apiurl(cls):
        return cls.command


class Base(object, metaclass=BaseMeta):

    args: list[str] = []

    def __init__(self, query: str):
        self.args = query.split(" ")
        self.validate()

    def validate(self):
        raise NotImplementedError

    @property
    def subPath(self) -> str:
        return " ".join(self.args)

    @property
    async def response(self) -> RenderResult:
        url = f"{self.__class__.apiurl}/{self.subPath}"
        return await Request(url).fetch()
