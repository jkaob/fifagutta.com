import datetime
from zoneinfo import ZoneInfo

DEFAULT_N_DAYS = 7

TZ = ZoneInfo("Europe/Oslo")
DEADLINE = datetime.datetime(2026, 4, 2, 23, 59, tzinfo=TZ)
SERIESTART = datetime.datetime(2026, 4, 5, 16, 00, tzinfo=TZ)
PRESEASON_END = datetime.datetime(2026, 4, 4, 0, 0, tzinfo=TZ)

def is_before_deadline():
    current_time = datetime.datetime.now(TZ)
    return current_time < DEADLINE

def is_before_seriestart():
    current_time = datetime.datetime.now(TZ)
    return current_time < SERIESTART

def is_preseason():
    current_time = datetime.datetime.now(TZ)
    return current_time < PRESEASON_END

