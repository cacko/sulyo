from ast import alias
from app.core.text import Align, Column, render_columns, to_mono
from collections import namedtuple
from enum import Enum

ScoreData = namedtuple("ScoreData", "status,home,score,away,win", defaults=[""])


class ScoreFormat(Enum):
    STANDALONE = 1
    LIST = 2


class ScoreRow:

    row: ScoreData = None
    format: ScoreFormat = ScoreFormat.LIST

    def __init__(
        self,
        status,
        score,
        home,
        away,
        win: str = "",
        format: ScoreFormat = ScoreFormat.LIST,
    ):
        self.format = format
        self.row = ScoreData(status=status, score=score, home=home, away=away, win=win)

    def __str__(self) -> str:
        if self.format == ScoreFormat.STANDALONE:
            cols = (
                Column(size=25, align=Align.LEFT),
                Column(size=5, align=Align.RIGHT),
                Column(size=6, align=Align.RIGHT),
                Column(size=25, align=Align.RIGHT),
            )
            row = (
                self.row.home.upper(),
                self.row.status,
                self.row.score,
                self.row.away.upper(),
            )
        elif self.format == ScoreFormat.LIST:
            cols = (
                Column(size=25, align=Align.RIGHT),
                Column(size=6, align=Align.CENTER),
                Column(size=25, align=Align.LEFT),
                Column(size=6, align=Align.RIGHT),
            )
            row = (
                self.row.home.upper(),
                self.row.score,
                self.row.away.upper(),
                self.row.status,
            )
        else:
            raise NotImplemented
        res = [render_columns(cols, [row])]
        if self.row.win:
            res.append(
                render_columns(
                    [Column(size=sum([x.size for x in cols]), align=Align.CENTER)],
                    [self.row.win],
                )
            )
        return "\n".join(res)

    @property
    def home(self):
        return self.row.home

    @property
    def away(self):
        return self.row.away

    @property
    def status(self):
        return self.row.status

    @property
    def score(self):
        return self.row.status

    @property
    def win(self):
        return self.row.win
