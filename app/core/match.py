from typing import Generator
from dataclasses_json import dataclass_json
from thefuzz import fuzz
import re
from stringcase import snakecase
from enum import Enum


class MatchMeta(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        id = hash(repr(kwargs.get("haystack")))
        if id not in cls._instances:
            cls._instances[id] = super(
                MatchMeta, cls).__call__(*args, **kwargs)
        return cls._instances[id]


class MatchMethod(Enum):
    TOKENSET = "token_set_ratio"
    PARTIAL = "partial_ratio"
    PARTIALSET = "partial_token_sort_ratio"
    WRATIO = "WRatio"


class Match(object, metaclass=MatchMeta):

    haystack = []
    cache = {}
    ext_pattern = re.compile(r"([\d+]+)")
    minRatio = 90
    extensionMatching = True
    method: MatchMethod = MatchMethod.PARTIALSET

    def __init__(self, haystack):
        self.haystack = haystack

    def fuzzy(self, needle: dataclass_json) -> list:
        cacheKey = snakecase(f"{needle} {'_'.join(needle.to_dict().values())}")
        if cacheKey not in self.cache:
            self.cache[cacheKey] = [
                *reversed(
                    [
                        *map(
                            lambda h: h.pop(),
                            sorted(
                                [[ratio, hs]
                                    for hs, ratio in self.__ratios(needle)],
                                key=lambda x: x[0],
                            ),
                        )
                    ]
                )
            ]
        return self.cache[cacheKey]

    def __ratios(self, needle) -> Generator[tuple[any, int], None, None]:
        keys = needle.to_dict().keys()
        query = " ".join(needle.to_dict().values())
        for hs in self.haystack:
            ratio = getattr(fuzz, self.method.value)(
                query, " ".join(getattr(hs, k) for k in keys)
            )
            if ratio >= self.minRatio:
                yield hs, ratio
