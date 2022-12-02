from os import environ
from dataclasses import dataclass
from pathlib import Path
from typing import Optional
from dataclasses_json import dataclass_json, Undefined
from yaml import load, Loader


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class SignalConfig:
    signalcli: str
    account: str
    host: str
    attachments: str
    port: Optional[int] = None
    groups: Optional[list[str]] = None


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class ZnaykoConfig:
    host: str
    port: int
    phone: str
    client: str
    storage: str
    redis_url: str
    attachments: str


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class ConfigStruct:
    signal: SignalConfig
    znayko: ZnaykoConfig


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
    def znayko(cls) -> ZnaykoConfig:
        return cls().struct.znayko


class Config(object, metaclass=ConfigMeta):

    struct: ConfigStruct

    def __init__(self):
        settings = Path(environ.get("SETTINGS_PATH", "app/settings.yaml"))
        data = load(settings.read_text(), Loader=Loader)
        self.struct = ConfigStruct.from_dict(data)  # type: ignore
