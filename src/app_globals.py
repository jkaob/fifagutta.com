import os
import json
import datetime
from zoneinfo import ZoneInfo

PASSWORD_ID = json.loads(os.getenv('FIFAGUTTA_PASSWORDS_ID_JSON'))
DEFAULT_N_DAYS = 7
YEAR = 2026

TZ = ZoneInfo("Europe/Oslo")
DEADLINE = datetime.datetime(YEAR, 4, 2, 23, 59, tzinfo=TZ)
SERIESTART = datetime.datetime(YEAR, 4, 5, 16, 00, tzinfo=TZ)
PRESEASON_END = datetime.datetime(YEAR, 4, 3, 16, 20, tzinfo=TZ)

def is_before_deadline():
    current_time = datetime.datetime.now(TZ)
    return current_time < DEADLINE

def is_before_seriestart():
    current_time = datetime.datetime.now(TZ)
    return current_time < SERIESTART

def is_preseason():
    current_time = datetime.datetime.now(TZ)
    return current_time < PRESEASON_END

