from app.core.decorators import command
from pathlib import Path
from app.core import Cachable, Request, RenderResult
from hashlib import blake2b
from app.core.models import BinaryStruct
import io
from PIL import Image
from urllib.parse import quote
import tempfile

from app.json_rpc.context import Context


class Logo(Cachable):

    _struct: BinaryStruct = None
    __name = None
    __id = None

    def __init__(self, name: str):
        if not name:
            raise ValueError
        self.__name = name

    async def generate(self) -> BinaryStruct:
        req = Request(
            f"https://ontv.cacko.net/api/assets/team/badge/{quote(self.__name)}.png"
        )
        return await req.binary

    @property
    def id(self):
        if not self.__id:
            h = blake2b(digest_size=20)
            h.update(self.__name.encode())
            self.__id = h.hexdigest()
        return self.__id

    @property
    async def content(self):
        if not self.load():
            self._struct = self.tocache(await self.generate())
        return self._struct.binary

    @property
    async def filename(self) -> Path:
        dst = Path(tempfile.gettempdir()) / f"{self.id}.png"
        if not dst.exists():
            im = Image.open(io.BytesIO(await self.content))
            im.thumbnail([200, 200], Image.BICUBIC)
            im.save(dst.as_posix())
        return dst


@command(
    trigger="logo", desc="searches and display a logo for the requested football team"
)
async def logo_command(context: Context) -> RenderResult:
    logo = Logo(context.query)
    filename = await logo.filename
    await context.send(RenderResult(attachment=filename.as_posix()))
