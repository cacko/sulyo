
from subprocess import Popen, PIPE, STDOUT
import os
from pathlib import Path
class Lyrics:

    __query: str = None
    __message: Path = None

    IGNORED = ["Tekst piosenki:", "Dodaj", "Historia"]
    REPLACED = ["lyrics: fetched lyrics:", "lyrics: lyrics already present:"]

    def __init__(self, query: str):
        self.__query = query

    @property
    def environment(self):
        return dict(
            os.environ,
            PATH=f"/home/jago/.pyenv/plugins/pyenv-virtualenv/shims:/home/jago/.pyenv/shims:/home/jago/.pyenv/bin:/home/jago/.local/bin:/usr/local/bin:/usr/bin:/bin:/usr/games",
        )

    @property
    def text(self) -> str:
        return ""
        ## taq 4ikliq trqbqva da e na extender-a
        # if not self.__message:
        #     result = []
        #     with Popen(
        #         ["beet", "lyrics", "-p", f"title:{self.__query.strip()}"],
        #         stdout=PIPE,
        #         stderr=STDOUT,
        #         env=self.environment,
        #     ) as p:
        #         for line in iter(p.stdout.readline, b""):
        #             line = line.decode().strip()
        #             if any([x in line for x in self.IGNORED]):
        #                 continue
        #             if prefix := next(
        #                 filter(lambda x: line.startswith(x), self.REPLACED), None
        #             ):
        #                 line = line.removeprefix(prefix).strip()
        #                 line = f"{line.upper()}\n"
        #             result.append(line)
        #         if p.returncode:
        #             return None
        #         self.__message = "\n".join(result)
        # return self.__message

