from pathlib import Path
import tempfile
from stringcase import alphanumcase
from app.core import log
from app.core.request import Request
from app.core.decorators import command
from os import environ


class Song:

    __query: str = None
    __message: Path = None

    def __init__(self, query: str):
        self.__query = query

    @property
    def messsage(self) -> str:
        return self.__message

    @property
    def destination(self) -> Path:
        dst = Path(tempfile.gettempdir()) / f"{alphanumcase(self.__query)}.aac"
        dst.touch()
        return dst

    async def find(self) -> bool:
        try:
            req = Request(f"{environ.get('MUSIC_SERVICE')}/find/song/{self.__query}")
            multipart = await req.multipart
            for part in multipart.parts:
                content_type = part.headers.get(b"content-type", None)
                if content_type == b"audio/aac":
                    self.destination.write_bytes(part.content)
                else:
                    self.__message = part.text
            return True
        except Exception as e:
            log.debug(e, exc_info=True)
            return False
