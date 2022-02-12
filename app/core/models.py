from dataclasses import dataclass
from datetime import datetime
from dataclasses_json import dataclass_json, Undefined


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class TimeCache:
    timestamp: datetime
    struct: any


@dataclass
class BinaryStruct:
    binary: any
    type: str
