"""Causal selection adapter to the already audited M15 research feature engine.

No new indicators or breakout rules. The read-only research engine is the sole
algorithmic source during offline foundation validation. Do not import H1 code.
Only completed close-labelled M15 bars are accepted. Live FINAM data stitching
and frozen-prefix parity must be proven before attaching any order adapter.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
import hashlib
import math
from typing import Any
from zoneinfo import ZoneInfo

import pandas as pd

from .spec import (
    INSTRUMENTS, SIGNAL_START_MSK_MINUTE, SIGNAL_END_MSK_MINUTE,
    TIMEFRAME_MINUTES,
)

MOSCOW = ZoneInfo("Europe/Moscow")
REQUIRED_OHLC = ("Open", "High", "Low", "Close", "Volume")


@dataclass(frozen=True)
class M15Signal:
    signal_id: str
    instrument: str
    direction: str
    completed_at: datetime
    signal_close: float
    signal_atr14: float
    h1_available_at: datetime
    breakout_level: float


def _msk_timestamp(value: datetime) -> datetime:
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("M15_TIMEZONE_REQUIRED")
    return value.astimezone(MOSCOW)


def validate_completed_history(instrument: str, history: pd.DataFrame, observed_at: datetime) -> None:
    """Reject partial/future/duplicated bars rather than silently repairing a feed."""
    if instrument not in INSTRUMENTS:
        raise ValueError("M15_INSTRUMENT_NOT_N4")
    now = _msk_timestamp(observed_at)
    if not isinstance(history, pd.DataFrame) or history.empty:
        raise ValueError("M15_HISTORY_REQUIRED")
    if not isinstance(history.index, pd.DatetimeIndex) or history.index.tz is None:
        raise ValueError("M15_CLOSE_INDEX_TIMEZONE_REQUIRED")
    if history.index.has_duplicates or not history.index.is_monotonic_increasing:
        raise ValueError("M15_DUPLICATE_OR_NONMONOTONIC")
    if not all(field in history.columns for field in REQUIRED_OHLC):
        raise ValueError("M15_OHLC_MISSING")
    local = history.index.tz_convert(MOSCOW)
    if (local > pd.Timestamp(now)).any():
        raise ValueError("M15_FUTURE_OR_INCOMPLETE_CLOSE")
    if any(at.minute % TIMEFRAME_MINUTES or at.second or at.microsecond for at in local):
        raise ValueError("M15_CLOSE_GRID_INVALID")
    price = history.loc[:, ("Open", "High", "Low", "Close")]
    if not bool(price.notna().all().all()) or not bool((price > 0).all().all()):
        raise ValueError("M15_PRICE_INVALID")
    import numpy as np
    if not bool(np.isfinite(history.loc[:, REQUIRED_OHLC].to_numpy(dtype=float)).all()):
        raise ValueError("M15_NONFINITE_OHLCV")
    if not bool((price["High"] >= price[["Open", "Low", "Close"]].max(axis=1)).all()):
        raise ValueError("M15_HIGH_INVALID")
    if not bool((price["Low"] <= price[["Open", "High", "Close"]].min(axis=1)).all()):
        raise ValueError("M15_LOW_INVALID")
    # Original M15 research expects MSK close labels; no date/time resampling here.
    if str(history.index.tz) != "Europe/Moscow":
        raise ValueError("M15_MSK_INDEX_REQUIRED")


def latest_completed_signal(
    instrument: str,
    history: pd.DataFrame,
    observed_at: datetime,
) -> M15Signal | None:
    """Returns only the latest completed signal; never routes an order.

    Source engine is the frozen, independently validated PR #518 code.
    It calculates EMA75/ADX14/ATR14/Donchian20, causal daily-ordinal H1, and
    T3 LONG/SHORT exactly as in the selected historical build. Time gate T1
    applies to the signal's close timestamp, not the next candle's close.
    """
    validate_completed_history(instrument, history, observed_at)
    # Imported here to keep the foundation's constants and risk engine free
    # of pandas/numpy dependencies and to make the source reference explicit.
    from IntradayLab.t3_m15_t1_entry_retest_v1.primary import features

    frame = history.loc[:, REQUIRED_OHLC]
    bars = features(frame)
    if not bars:
        return None
    latest: dict[str, Any] = bars[-1]
    at = _msk_timestamp(latest["at"])
    now = _msk_timestamp(observed_at)
    if at > now:
        raise ValueError("M15_FUTURE_SIGNAL")
    if now - at >= timedelta(minutes=TIMEFRAME_MINUTES):
        # No stale re-entry while FINAM has not provided a new completed candle.
        return None
    minute = at.hour * 60 + at.minute
    if not SIGNAL_START_MSK_MINUTE <= minute < SIGNAL_END_MSK_MINUTE:
        return None
    direction = int(latest["Signal"])
    if direction not in (-1, 0, 1):
        raise ValueError("M15_SIGNAL_INVALID")
    if direction == 0:
        return None
    atr = float(latest["ATR"])
    price = float(latest["Close"])
    available = latest["H1AvailableAt"]
    if not isinstance(available, datetime):
        raise ValueError("M15_H1_CONTEXT_NOT_PUBLISHED")
    available = _msk_timestamp(available)
    if available > at:
        raise ValueError("M15_H1_LOOKAHEAD")
    breakout = float(latest["PriorHigh"] if direction == 1 else latest["PriorLow"])
    if not all(math.isfinite(v) and v > 0 for v in (atr, price, breakout)):
        raise ValueError("M15_SIGNAL_ECONOMICS_INVALID")
    side = "LONG" if direction == 1 else "SHORT"
    digest = hashlib.sha256(f"{instrument}|{at.isoformat()}|{side}|{price:.12g}".encode()).hexdigest()[:20]
    return M15Signal(f"m15:{digest}", instrument, side, at, price, atr, available, breakout)


def consecutive_next_open_allowed(signal_close: datetime, next_bar_close: datetime) -> bool:
    """Historical NEXT_OPEN adjacency only; never wait another M15 after close."""
    a, b = _msk_timestamp(signal_close), _msk_timestamp(next_bar_close)
    return (b - a).total_seconds() == TIMEFRAME_MINUTES * 60
