from app.core.output import Align, Column, TextOutput
from collections import namedtuple

CVEBasics = namedtuple(
    "CVEBasics", "id,description,severity,attackVector", defaults=[""]
)


class CVEHeader:

    row: CVEBasics = None

    def __init__(self, id, description, severity, attackVector):
        self.row = CVEBasics(
            id=id, description=description, severity=severity, 
            attackVector=attackVector
        )

    def __str__(self) -> str:
        cols = (
            Column(size=15, align=Align.LEFT),
            Column(size=30, align=Align.RIGHT),
            Column(size=15, align=Align.RIGHT),
        )
        row = (
            self.row.id,
            self.row.severity.upper(),
            self.row.attackVector.upper(),
        )
        return f"{TextOutput.renderColumns(cols, [row])}\n{TextOutput.toMono(self.row.description)}"
