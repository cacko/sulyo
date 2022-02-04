from app.commands.ontv.item.livescore_details import ParserDetails
from app.commands.ontv.item.models import *
from app.core.output import Align, Column, TextOutput
from app.core import log


class Lineups:

    __item: Event = None

    def __init__(self, item: Event):
        self.__item = item

    @property
    def empty(self) -> RenderResult:
        return EmptyResult()

    @property
    async def message(self) -> RenderResult:
        details = await ParserDetails.get(self.__item.details)
        home = details.home
        away = details.away
        if any([not details.members, not home.lineups, not away.lineups]):
            return EmptyResult()
        members = {m.id: m for m in details.members}
        try:
            cols = (
                Column(size=2, align=Align.LEFT),
                Column(size=20, align=Align.LEFT),
                Column(size=20, align=Align.RIGHT),
                Column(size=2, align=Align.RIGHT),
            )
            home_starting: list[LineupMember] = self.__getStarting(home.lineups.members)
            away_starting: list[LineupMember] = self.__getStarting(away.lineups.members)
            rows = [
                (
                    members[h.id].jerseyNumber,
                    members[h.id].name,
                    members[a.id].name,
                    members[a.id].jerseyNumber,
                )
                for h, a in zip(home_starting, away_starting)
            ]
            header = TextOutput.renderColumns(
                (Column(size=22, align=Align.LEFT), Column(size=22, align=Align.RIGHT)),
                [(home.name.upper(), away.name.upper())],
            )
            return RenderResult(
                message="\n".join(
                    [header, TextOutput.renderColumns(cols, rows)]
                )
            )
        except Exception as e:
            log.exception(e.tr)
            return EmptyResult

    def __getStarting(self, members: list[LineupMember]) -> list[LineupMember]:
        return list(filter(lambda x: x.status == LineupMemberStatus.STARTING, members))
