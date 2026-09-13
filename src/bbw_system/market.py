from __future__ import annotations

from datetime import time
from zoneinfo import ZoneInfo
import pandas as pd

from .config import SessionConfig


def _clock(value: str) -> time:
    return time.fromisoformat(value)


def localize_index(data: pd.DataFrame, config: SessionConfig) -> pd.DataFrame:
    out = data.copy()
    idx = pd.DatetimeIndex(out.index)
    zone = ZoneInfo(config.timezone)
    out.index = idx.tz_localize(zone) if idx.tz is None else idx.tz_convert(zone)
    return out.sort_index(kind="stable")


def in_session(ts: pd.Timestamp, config: SessionConfig) -> bool:
    session_date = trading_date(ts, config)
    if str(session_date) in config.excluded_dates:
        return False
    if session_date.weekday() in config.excluded_weekdays:
        return False
    overrides = dict(config.session_end_overrides)
    value, start = ts.timetz().replace(tzinfo=None), _clock(config.session_start)
    end = _clock(overrides.get(str(session_date), config.session_end))
    accepted = start <= value <= end if start <= end else value >= start or value <= end
    return accepted and not any(_clock(a) <= value < _clock(b) for a, b in config.excluded_intervals)


def filter_session(data: pd.DataFrame, config: SessionConfig) -> pd.DataFrame:
    localized = localize_index(data, config)
    return localized.loc[[in_session(ts, config) for ts in localized.index]]


def trading_date(ts: pd.Timestamp, config: SessionConfig):
    """Trading date is the date of the most recent configured session anchor."""
    local = ts.tz_convert(config.timezone) if ts.tzinfo else ts.tz_localize(config.timezone)
    anchor = _clock(config.session_anchor)
    return (local - pd.Timedelta(days=1)).date() if local.timetz().replace(tzinfo=None) < anchor else local.date()
