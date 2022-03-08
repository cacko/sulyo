
from os import environ
from dataclasses import dataclass
from pathlib import Path
from typing import Optional
from dataclasses_json import dataclass_json, Undefined
import toml


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class SignalConfig:
    signalcli: str
    account: str
    host: str
    port: Optional[int] = None


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class BotyoConfig:
    host: str
    port: int
    phone: str
    client: str
    storage: str
    redis_url: str


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class ConfigStruct:
    signal: SignalConfig
    botyo: BotyoConfig


class ConfigMeta(type):
    _instance = None

    def __call__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(ConfigMeta, cls).__call__(*args, **kwargs)
        return cls._instance

    @property
    def signal(cls) -> SignalConfig:
        return cls().struct.signal

    @property
    def botyo(cls) -> BotyoConfig:
        return cls().struct.botyo


class Config(object, metaclass=ConfigMeta):

    truct: ConfigStruct = None

    def __init__(self):
        settings = Path(environ.get("SETTINGS_PATH", "app/settings.toml"))
        self.struct = ConfigStruct.from_dict(toml.loads(settings.read_text()))
