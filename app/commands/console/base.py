from subprocess import Popen, PIPE, STDOUT
import os


class BaseMeta(type):
    @property
    def executable(cls):
        return cls.command


class Base(object, metaclass=BaseMeta):

    args: list[str] = []

    def __init__(self, query: str):
        self.args = query.split(" ")
        self.validate()

    def validate(self):
        raise NotImplemented

    @property
    def environment(self):
        return dict(
            os.environ,
            PATH=f"/home/jago/.pyenv/plugins/pyenv-virtualenv/shims:/home/jago/.pyenv/shims:/home/jago/.pyenv/bin:/home/jago/.local/bin:/usr/local/bin:/usr/bin:/bin:/usr/games",
        )

    @property
    def text(self) -> str:
        result = []
        with Popen(
            [self.__class__.executable, *self.args],
            stdout=PIPE,
            stderr=STDOUT,
            env=self.environment,
        ) as p:
            for line in iter(p.stdout.readline, b""):
                line = line.decode().strip()
                result.append(line)
            if p.returncode:
                return None
        return "\n".join(result)
