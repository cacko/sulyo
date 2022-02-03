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
                Column(size=25, align=Align.LEFT),
                Column(size=12, align=Align.CENTER),
            )
            row = (
                self.row.home.upper(),
                self.row.away.upper(),
                f"{self.row.score} {self.row.status}",
            )
        else:
            raise NotImplemented
        return render_columns(cols, [row]) + to_mono(self.row.win)

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
