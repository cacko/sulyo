from typing import Optional
from black import re
from emoji import emojize, demojize, is_emoji
from dataclasses import dataclass
from dataclasses_json import dataclass_json, Undefined
from unidecode import unidecode
import re
from PIL import Image, ImageDraw, ImageFont
import tempfile
from pathlib import Path
from hashlib import blake2b

class Align:
    LEFT = "<"
    RIGHT = ">"
    CENTER = "^"

@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class Column:
    size: int = 25
    align: Align = Align.LEFT
    title: Optional[str] = " "
    spacing: int = 0

CAPITALS = range(ord("A"), ord("Z") + 1)  # 120432
SMALL = range(ord("a"), ord("z") + 1)  # 120458
NUMBERS = range(ord("0"), ord("9") + 1)  # 120822
MAPS = {
    45: 65123, # -
    32: 32, # space
    124: 65372, # |
    58: 8758, # :
    94: 10032, # ^
    37: 65130, # %
    40: 32, # (
    41: 32,  # )
    47: 32, # /
}

WHITESPACE = 8287

NEWLINE = [10, 13]

NOTCOMPATIBLE = ""


class OutputMeta(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(OutputMeta, cls).__call__(*args, **kwargs)
        return cls._instances[cls]
    
    def renderColumns(cls, cols: list[Column], content: list[str], with_header=False):
        return cls().render_columns(cols, content, with_header)
    
    def image(cls, text) -> Path:
        return cls().to_image(text)

    def toMono(cls, text):
        return cls().to_mono(text)
    
    def alignWhitespace(cls, text):
        return cls().align_whitespace(text)
    
    def splitWithQuotes(cls, text):
        return cls().split_with_quotes(text)

class Output(object, metaclass=OutputMeta):
    
    utf8mono: bool = True
    
    def to_image(self, text: str) -> Path:
        id = blake2b(digest_size=20)
        id.update(text.encode())
        output_filename = Path(tempfile.tempdir) / f"{id.hexdigest()}.png"
        im = Image.new('RGBA', (1000, 800), (45,108,234, 255))
        draw = ImageDraw.Draw(im)
        try:
            monoFont = ImageFont.truetype(font='./SourceCodePro-Medium.ttf', size=20)
            draw.text((50, 10), text, fill='white', font=monoFont)
        except Exception as ex:
            draw.text((10, 10), text, fill='white')
        im.save(output_filename)
        return output_filename

    def align_whitespace(self, str: str):
        if not self.utf8mono:
            return str
        return re.sub(r"\s",chr(WHITESPACE)*2,str)

    def get_monospace(self, char: str):
        if is_emoji(char):
            return char
        code = ord(char)
        match code:
            case code if code in CAPITALS:
                return chr(120432 + code - ord("A"))
            case code if code in SMALL:
                return chr(120458 + code - ord("a"))
            case code if code in NUMBERS:
                return chr(120822 + code - ord("0"))
            case code if code in MAPS:
                return chr(MAPS[ord(char)])
            case code if code in NEWLINE:
                return char
        return NOTCOMPATIBLE

    def to_mono(self, text: str):
        text = emojize(unidecode(demojize(f"{text}")))
        if not self.utf8mono:
            return text
        return "".join([self.get_monospace(f"{x}") for x in text])

    def render_columns(self, columns: tuple[Column], content: tuple[str], with_header=False, utf8mono=True):
        rows = [" ".join([f"{self.to_mono(cell)[:col.size]:{col.align}{col.size}}" for col, cell in zip(columns, cnt)]) for cnt in content]
        if with_header:
            cols = " ".join([f"{self.to_mono(col.title)[:col.size]:{col.align}{col.size}}" for col in columns])
            return "\n".join([self.align_whitespace(cols), *map(self.align_whitespace, rows)])
        return  "\n".join([*map(self.align_whitespace, rows)])

    def split_with_quotes(self, text:str) -> list[str]:
        return [x.strip() for x in filter(lambda x: len(x.strip()) > 0, text.split('"' if '"' in text else " "))]


class ImageOutput(Output):
    utf8mono = False

class TextOutput(Output):
    utf8mono = True

def to_mono(text):
    return TextOutput.toMono(text)

def align_whitespace(text):
    return TextOutput.alignWhitespace(text)

def split_with_quotes(text):
    return TextOutput.splitWithQuotes(text)