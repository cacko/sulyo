
from os import environ
from dataclasses import dataclass
from pathlib import Path
from dataclasses_json import dataclass_json, Undefined
import toml


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class RedisConfig:
    url: str


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class SignalConfig:
    groups: list[str]
    host: str
    port: int


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class ZnaykoConfig:
    host: str
    port: int
    phone: str
    client: str


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class CachableConfig:
    path: str


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class ConfigStruct:
    redis: RedisConfig
    signal: SignalConfig
    znayko: ZnaykoConfig
    cachable: CachableConfig


class ConfigMeta(type):
    _instance = None

    def __call__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(ConfigMeta, cls).__call__(*args, **kwargs)
        return cls._instance

    @property
    def redis(cls) -> RedisConfig:
        return cls().struct.redis

    @property
    def signal(cls) -> SignalConfig:
        return cls().struct.signal

    @property
    def znayko(cls) -> ZnaykoConfig:
        return cls().struct.znayko

    @property
    def cachable(cls) -> CachableConfig:
        return cls().struct.cachable


class Config(object, metaclass=ConfigMeta):

    truct: ConfigStruct = None

    def __init__(self):
        settings = Path(environ.get("SETTINGS_PATH", "app/settings.toml"))
        self.struct = ConfigStruct.from_dict(toml.loads(settings.read_text()))
