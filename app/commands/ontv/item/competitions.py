from os import environ
from pathlib import Path

from black import json
from app.commands.ontv.item.livescore_details import ParserDetails
from app.core import to_mono
from app.commands.ontv.item.models import *


class Competitions:

    jsonpath: str = None
    leagues: list[int] = []

    def __init__(self, jsonpath, leagues: list[int]):
        self.jsonpath = jsonpath
        self.leagues = leagues

    @property
    def jsonfile(self) -> Path:
        jsonfile = Path(__file__).parent.parent / self.jsonpath
        if not jsonfile.exists():
            return
        return jsonfile

    @property
    def empty(self) -> RenderResult:
        return EmptyResult()

    @property
    def competitions(self) -> list[CompetitionItem]:
        data = self.jsonfile.read_text()
        return CompetitionItem.schema().loads(data, many=True)

    @property
    def current(self) -> list[CompetitionItem]:
        all = self.competitions
        return list(filter(lambda x: x.id in self.leagues, all))

    def message(self, query:str = "") -> RenderResult:
        comps = self.current
        comps = sorted(comps, key=lambda x: f"{x.country_name} {x.league_name}")
        return RenderResult(
            message=to_mono(
                "\n".join([f"{c.country_name.upper()} {c.league_name} " for c in comps])
            )
        )
