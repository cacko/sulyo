from pathlib import Path
import tempfile
from stringcase import alphanumcase
from app.core import log
from app.core.request import Request
from os import environ
from PIL import Image
import io


class AlbumArt:

    __query: str = None
    __message: Path = None

    def __init__(self, query: str):
        self.__query = query

    @property
    def messsage(self) -> str:
        return self.__message

    @property
    def destination(self) -> Path:
        dst = Path(tempfile.gettempdir()) / f"albumart-{alphanumcase(self.__query)}.png"
        return dst

    async def find(self) -> bool:
        try:
            if self.destination.exists():
                return True
            req = Request(
                f"{environ.get('MUSIC_SERVICE')}/find/albumart/{self.__query}"
            )
            image = await req.binary
            if not image:
                return False
            im = Image.open(io.BytesIO(image.binary))
            im.thumbnail([500, 500], Image.BICUBIC)
            im.save(self.destination.as_posix(), format="png")
            return True
        except Exception as e:
            log.debug(e, exc_info=True)
            return False
