from app.core import Cachable, RenderResult, log
from hashlib import blake2b
import wikipedia
from wikipedia.exceptions import DisambiguationError
from app.core.decorators import command
from app.core.models import EmptyResult
from app.core.output import to_mono
from app.json_rpc.context import Context


class Wiki(Cachable):

    __name = None
    __id = None

    def __init__(self, name: str):
        if not name:
            raise ValueError
        self.__name = name

    def generate(self) -> str:
        try:
            result = wikipedia.summary(self.__name)
            return result
        except DisambiguationError as e:
            options = "\n".join(e.options)
            return f"Maybe you mean: {options}"
        except Exception as e:
            log.error(e, exc_info=True)
            return None

    @property
    def id(self):
        if not self.__id:
            h = blake2b(digest_size=20)
            h.update(self.__name.encode())
            self.__id = h.hexdigest()
        return self.__id

    @property
    def text(self) -> str:
        if not self.load():
            wikidata = self.generate()
            if wikidata:
                self._struct = self.tocache(wikidata)
        return self._struct


@command(
    trigger="wikipedia",
    desc="search and displayed the first match for a term from wikipedia",
)
async def wiki_command(context: Context) -> RenderResult:
    try:
        wiki = Wiki(context.query)
        text = wiki.text
        result = RenderResult(message=to_mono(text)) if text else EmptyResult()
        await context.send(result)
    except Exception as e:
        log.error(e, exc_info=True)
