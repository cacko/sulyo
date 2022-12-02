from dataclasses import dataclass
from dataclasses_json import dataclass_json

@dataclass_json
@dataclass
class Config:
    host: str
    port: int
    storage: str
    client: str
    phone: str
    redis_url: str
    attachments: str
