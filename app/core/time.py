from datetime import datetime, timezone
from zoneinfo import ZoneInfo

ZONES = [("+44", ZoneInfo("Europe/London")), ("+359", ZoneInfo("Europe/Sofia"))]


def source_tz(source: str):
    tz = next(filter(lambda x: source.startswith(x[0]), ZONES), None)
    return tz[1] if tz else timezone.utc


def time_hhmm(dt: datetime, source: str):
    tz = source_tz(source)
    return dt.astimezone(tz).strftime("%H:%M")


def time_hhmmz(dt: datetime, source: str):
    df = dt.astimezone(source_tz(source))
    return f"{df.strftime('%H:%M')} {df.tzname()}"
