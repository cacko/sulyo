from tkinter import RIGHT
from app.commands.ontv.item.livescore_details import ParserDetails
from app.core import to_mono, log
from app.commands.ontv.item.models import *
from app.core.text import Align, Column, render_columns


class Stats:

    __item: Event = None

    def __init__(self, item: Event):
        self.__item = item

    @property
    def empty(self) -> RenderResult:
        return EmptyResult()

    @property
    async def message(self) -> RenderResult:
        details = await ParserDetails.get(self.__item.details)
        if not details:
            return self.empty
        home = details.home
        away = details.away
        home_stats: list[GameStatistic] = home.statistics
        away_stats: list[GameStatistic] = away.statistics
        if any([not home_stats, not away_stats]):
            return self.empty
        header = render_columns(
            columns=(
                Column(size=25, align=Align.LEFT),
                Column(size=25, align=Align.RIGHT),
            ),
            content=[(home.name.upper(), away.name.upper())],
        )
        cols = (
            Column(size=10, align=Align.LEFT),
            Column(size=30, align=Align.CENTER),
            Column(size=10, align=Align.RIGHT),
        )
        content = [
            (h_s.value, h_s.name, a_s.value)
            for h_s, a_s in zip(home_stats, away_stats)
        ]

        return RenderResult(
            message=f"{header}\n{render_columns(cols, content)}"
        )
