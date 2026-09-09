from __future__ import annotations
import pandas as pd

TZ = "Europe/Moscow"
DEV_START = pd.Timestamp("2026-01-01 00:00:00", tz=TZ)
DEV_END = pd.Timestamp("2026-08-31 23:59:59.999999", tz=TZ)

def require_aware(value: pd.Timestamp) -> None:
    if value.tzinfo is None:
        raise ValueError("timestamp must be timezone-aware")

def require_development(values: pd.Series | pd.DatetimeIndex) -> None:
    if values.dt.tz is None if isinstance(values, pd.Series) else values.tz is None:
        raise ValueError("timestamps must be timezone-aware")
    if ((values < DEV_START) | (values > DEV_END)).any():
        raise ValueError("timestamp outside inclusive development interval (2025 TRUE OOS is locked)")

def sequential_split(values: pd.Series, split: pd.Timestamp) -> tuple[pd.Series, pd.Series]:
    require_aware(split)
    if values.dt.tz is None or not values.is_monotonic_increasing:
        raise ValueError("ordered timezone-aware timestamps required")
    return values < split, values >= split
