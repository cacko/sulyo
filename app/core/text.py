from typing import Optional
from black import re
from emoji import emojize, demojize, is_emoji
from dataclasses import dataclass
from dataclasses_json import dataclass_json, Undefined
from unidecode import unidecode
import re
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

def align_whitespace(str: str):
    return re.sub(r"\s",chr(WHITESPACE)*2,str)

def get_monospace(char: str):
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

def to_mono(text: str):
    text = emojize(unidecode(demojize(f"{text}")))
    return "".join([get_monospace(f"{x}") for x in text])

def render_columns(columns: tuple[Column], content: tuple[str], with_header=False):
    rows = [" ".join([f"{to_mono(cell)[:col.size]:{col.align}{col.size}}" for col, cell in zip(columns, cnt)]) for cnt in content]
    if with_header:
        cols = " ".join([f"{to_mono(col.title)[:col.size]:{col.align}{col.size}}" for col in columns])
        return "\n".join([align_whitespace(cols), *map(align_whitespace, rows)])
    return  "\n".join([*map(align_whitespace, rows)])

def split_with_quotes(text:str) -> list[str]:
    return [x.strip() for x in filter(lambda x: len(x.strip()) > 0, text.split('"' if '"' in text else " "))]


