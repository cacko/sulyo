from dataclasses import dataclass
from typing import Callable, Optional
from dataclasses_json import dataclass_json, Undefined
from app import App


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class CommandDef:
    trigger: str
    handler: Callable
    desc: Optional[str] = None
    triggerSource: Optional[bool] = False


def parametrized(dec):
    def layer(*args, **kwargs):
        def repl(f):
            return dec(f, *args, **kwargs)

        return repl

    return layer


@parametrized
def command(func, trigger: str, desc: str, triggerSource: bool = False):
    App.register(
        CommandDef(
            trigger=trigger, handler=func, desc=desc, triggerSource=triggerSource
        )
    )

    def registrar(*args):
        return func(*args)

    return registrar
