from app.core import Request, to_mono, time_hhmm, time_hhmmz, source_tz, RenderResult
from dataclasses import dataclass, field
from dataclasses_json import dataclass_json, config, Undefined
from datetime import datetime, timedelta, timezone
from marshmallow import fields
from app.core.text import Align, Column, align_whitespace, render_columns


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class Event:
    id: str
    event_id: int
    name: str
    time: datetime = field(
        metadata=config(
            encoder=datetime.isoformat,
            decoder=datetime.fromisoformat,
            mm_field=fields.DateTime(format="iso", tzinfo=timezone.utc),
        )
    )
    channels: list[str]
    tvchannels: list[int]
    sport: str
    country: str
    season: str
    home_team: str = ""
    away_team: str = ""
    league_id: int = 0
    league_name: str = ""
    has_expired: bool = False

    def __post_init__(self):
        self.has_expired = (
            datetime.now(tz=timezone.utc) - timedelta(hours=3) > self.time
        )


class TV:

    __request: Request
    LEAGUES: list[int] = []

    def __init__(self, request: Request, settings: dict = {}):
        self.__request = request
        self.LEAGUES = settings.get("leagues", [])

    @property
    async def events(self) -> list[Event]:
        body = await self.__request.body
        events: list[Event] = Event.schema().loads(body, many=True)
        return filter(
            lambda x: all([not x.has_expired, x.league_id in self.LEAGUES]), events
        )

    async def render(
        self, filt: str = "", groupdId="", source: str = ""
    ) -> RenderResult:
        events = list(
            filter(
                lambda ev: any(
                    [
                        not len(filt),
                        filt.lower() in ev.name.lower(),
                        filt.lower() in ev.league_name.lower(),
                    ]
                ),
                await self.events,
            )
        )
        if not events:
            return RenderResult(message="Няма нищо брат")
        elif len(events) == 1:
            columns = ["Time", "Event", "Comp", "onTV"]
            values = [
                [
                    f"{time_hhmm(ev.time, source)} {source_tz(source)}",
                    ev.name,
                    ev.league_name,
                    " ^ ".join(ev.channels),
                ]
                for ev in events
            ]
            return RenderResult(
                message="\n".join(
                    [
                        "\n".join(
                            map(
                                align_whitespace,
                                [
                                    f"{to_mono(t.lower()):>7} {to_mono(v.upper()):<7}"
                                    for t, v in zip(columns, row)
                                ],
                            )
                        )
                        for row in values
                    ]
                )
            )
        else:
            columns = (
                Column(title="Time", size=10, align=Align.CENTER),
                Column(title="Event"),
            )
            values = [
                [time_hhmmz(ev.time, source=source), ev.name.upper()] for ev in events
            ]
            return RenderResult(message=render_columns(columns, values, with_header=True))
