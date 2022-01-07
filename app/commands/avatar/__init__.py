from pathlib import Path
from app.core import Cachable, RenderResult
from hashlib import blake2b
from app.core import BinaryStruct
from cairosvg import svg2png
from multiavatar.multiavatar import multiavatar
from app.core.decorators import command
from app.json_rpc.context import Context


class Avatar(Cachable):

    _struct: BinaryStruct = None
    __name = None
    __id = None

    def __init__(self, name: str):
        if not name:
            raise ValueError
        self.__name = name

    def generate(self) -> BinaryStruct:
        avatar = multiavatar(self.__name, None, None)
        return BinaryStruct(binary=avatar.encode(), type="image/svg+xml")

    @property
    def id(self):
        if not self.__id:
            h = blake2b(digest_size=20)
            h.update(self.__name.encode())
            self.__id = h.hexdigest()
        return self.__id

    @property
    def content(self):
        if not self.load():
            self._struct = self.tocache(self.generate())
        return self._struct.binary

    @property
    def filename(self) -> Path:
        dst = Path("/tmp") / f"{self.__name}.png"
        if not dst.exists():
            svg2png(
                bytestring=self.content,
                write_to=dst.as_posix(),
                output_height=200,
                output_width=200,
            )
        return dst


@command(trigger="avatar", desc="generates random avatar for the arguments supplied")
async def avatar_command(context: Context) -> RenderResult:
    avatar = Avatar(context.query)
    dst = avatar.filename
    response = RenderResult(
        attachment=dst.as_posix()
    )
    await context.send(response)
