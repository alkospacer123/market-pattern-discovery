"""Causal selection adapter to the already audited M15 research feature engine.

No new indicators or breakout rules. The read-only research engine is the sole
algorithmic source during offline foundation validation. Do not import H1 code.
Only completed close-labelled M15 bars are accepted. Live FINAM data stitching
and frozen-prefix parity must be proven before attaching any order adapter.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal, InvalidOperation
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


@dataclass(frozen=True)
class M15VerifiedNextOpen:
    """Real FINAM next-candle OPEN reference, not a signal-close substitute.

    This is verified read-side evidence only; broker order permission and
    exact R15/GO sizing remain independent gates.
    """
    signal: M15Signal
    reference_open: Decimal
    observed_at: datetime


def _latest_verified_finam_observation(
    *, api: Any, m15_account_id: str, instrument: str,
    authenticated_seed: pd.DataFrame, observed_at: datetime,
    interval_start: str, interval_end: str,
    verified_open_labels: bool = False,
    require_next_open: bool = False,
) -> M15Signal | M15VerifiedNextOpen | None:
    """M15-only same-session FINAM bars -> completed bars -> frozen T1 signal.

    The seed is the independently authenticated, append-only research history;
    broker recent M15 data must overlap its last candle byte-for-value after
    parsing. Never bootstrap features from just FINAM's last-30-days slice.
    No signal here authorizes ENTRY, writes SQLite or invokes any order method.
    """
    from .bar_bridge import completed_close_labeled_m15
    from .continuation import immutable_prefix_splice
    from .finam_readonly import M15FinamReadOnlyAPI, _stamp
    from .finam_trading import M15FinamTradingAPI
    if verified_open_labels is not True:
        raise ValueError("M15_LIVE_BROKER_OPEN_LABEL_PROOF_REQUIRED")
    if instrument not in INSTRUMENTS:
        raise ValueError("M15_LIVE_SIGNAL_NOT_N4")
    if (type(api) not in (M15FinamReadOnlyAPI, M15FinamTradingAPI)
            or not isinstance(m15_account_id, str) or not m15_account_id):
        raise ValueError("M15_SIGNAL_FINAM_M15_SESSION_REQUIRED")
    if type(api) is M15FinamReadOnlyAPI and (
            api.account_id != m15_account_id or api.readonly_bound is not True):
        raise ValueError("M15_SIGNAL_READONLY_ACCOUNT_UNBOUND")
    if not isinstance(observed_at, datetime) or observed_at.tzinfo is None:
        raise ValueError("M15_SIGNAL_OBSERVATION_TIME_INVALID")
    start, end = _stamp(interval_start), _stamp(interval_end)
    if not start < end or (end - start) > timedelta(days=30):
        raise ValueError("M15_SIGNAL_FINAM_BARS_INTERVAL_INVALID")
    symbol = instrument + "@RTSX"
    account = api.account(m15_account_id)
    if (not isinstance(account, dict)
            or account.get("account_id") != m15_account_id
            or account.get("status") not in {"ACCOUNT_ACTIVE", "ACCOUNT_STATUS_ACTIVE"}):
        raise ValueError("M15_SIGNAL_ACCOUNT_IDENTITY_INVALID")
    schedule = api.schedule(symbol)
    broker_bars = api.bars_m15(symbol, interval_start, interval_end)
    if broker_bars.get("symbol") != symbol:
        raise ValueError("M15_SIGNAL_FINAM_SYMBOL_MISMATCH")
    newer = completed_close_labeled_m15(
        broker_bars, schedule, observed_at=observed_at,
        verified_open_labels=True)
    if newer.empty:
        return None
    history = immutable_prefix_splice(authenticated_seed, newer)
    signal = latest_completed_signal(instrument, history, observed_at)
    if signal is None or not require_next_open:
        return signal
    # NEXT_OPEN is the actual broker OPEN of the bar opening at the
    # signal's close. Never use signal_close as an executable price.
    if signal.completed_at != history.index[-1].to_pydatetime():
        raise ValueError("M15_NEXT_OPEN_SIGNAL_NOT_LAST_COMPLETED")
    from .bar_bridge import _utc
    matching = [
        row for row in broker_bars["bars"]
        if _utc(row["timestamp"]) == signal.completed_at.astimezone(
            ZoneInfo("UTC"))
    ]
    if len(matching) != 1:
        raise ValueError("M15_NEXT_OPEN_BROKER_OPEN_NOT_PROVEN")
    obj = matching[0].get("open")
    if (not isinstance(obj, dict) or set(obj) != {"value"}
            or not isinstance(obj["value"], str)):
        raise ValueError("M15_NEXT_OPEN_PRICE_SCHEMA_INVALID")
    try:
        reference = Decimal(obj["value"])
    except InvalidOperation:
        raise ValueError("M15_NEXT_OPEN_PRICE_INVALID") from None
    if not reference.is_finite() or reference <= 0:
        raise ValueError("M15_NEXT_OPEN_PRICE_INVALID")
    return M15VerifiedNextOpen(signal, reference, observed_at)


def latest_verified_finam_signal(
    *, api: Any, m15_account_id: str, instrument: str,
    authenticated_seed: pd.DataFrame, observed_at: datetime,
    interval_start: str, interval_end: str,
    verified_open_labels: bool = False,
) -> M15Signal | None:
    """Existing no-order signal interface; uses exact same FINAM GET chain."""
    evidence = _latest_verified_finam_observation(
        api=api, m15_account_id=m15_account_id, instrument=instrument,
        authenticated_seed=authenticated_seed, observed_at=observed_at,
        interval_start=interval_start, interval_end=interval_end,
        verified_open_labels=verified_open_labels,
        require_next_open=False,
    )
    return evidence


def latest_verified_finam_entry(
    *, api: Any, m15_account_id: str, instrument: str,
    authenticated_seed: pd.DataFrame, observed_at: datetime,
    interval_start: str, interval_end: str,
    verified_open_labels: bool = False,
) -> M15VerifiedNextOpen | None:
    """Exact broker NEXT_OPEN within the first 30s; otherwise skip, never catch up.

    Returns evidence for downstream PREPARED R15 calculations, not permission
    to POST a trading order.
    """
    evidence = _latest_verified_finam_observation(
        api=api, m15_account_id=m15_account_id, instrument=instrument,
        authenticated_seed=authenticated_seed, observed_at=observed_at,
        interval_start=interval_start, interval_end=interval_end,
        verified_open_labels=verified_open_labels,
        require_next_open=True,
    )
    if evidence is None:
        return None
    seconds = (evidence.observed_at.astimezone(ZoneInfo("UTC"))
               - evidence.signal.completed_at.astimezone(ZoneInfo("UTC"))).total_seconds()
    return evidence if 0 <= seconds <= 30 else None


def consecutive_next_open_allowed(signal_close: datetime, next_bar_close: datetime) -> bool:
    """Historical NEXT_OPEN adjacency only; never wait another M15 after close."""
    a, b = _msk_timestamp(signal_close), _msk_timestamp(next_bar_close)
    return (b - a).total_seconds() == TIMEFRAME_MINUTES * 60
