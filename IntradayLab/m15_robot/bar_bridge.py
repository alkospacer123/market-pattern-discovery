"""Fail-closed causal FINAM M15 open-label -> research M15 close-label bridge.

Source design: inspected H1 completed_h1_bars/trading_h1_windows; duration
is M15, not the H1 full-hour/shortened-session rule. Nothing here grants
trading or infers that actual FINAM M15 timestamps have been verified.

An explicit, operator-attested FINAM M15 *open-label* proof is required.
A completed M15 candle is accepted only after its immediately adjacent
next M15 bar OPEN timestamp was observed in the same continuous trading
window. That next candle's price/extrema are NEVER used. Missing next
bar => missing evidence, NOT assumed completion. No gap synthesis or
repacking across session boundaries. Output timestamps are M15 CLOSE MSK.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation
import math
from zoneinfo import ZoneInfo
from typing import Any

import pandas as pd

STEP = timedelta(minutes=15)
MOSCOW = ZoneInfo("Europe/Moscow")
TRADING_TYPES = frozenset({"EARLY_TRADING", "CORE_TRADING", "LATE_TRADING"})
NONTRADING_TYPES = frozenset({"OPENING_AUCTION", "CLEARING", "CLOSED"})
ALL_TYPES = TRADING_TYPES | NONTRADING_TYPES


class M15BarAuthorityError(RuntimeError):
    pass


def _utc(value: Any) -> datetime:
    if not isinstance(value, str):
        raise M15BarAuthorityError("M15_TIMESTAMP_FORMAT_INVALID")
    try:
        out = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        raise M15BarAuthorityError("M15_TIMESTAMP_FORMAT_INVALID") from None
    if out.tzinfo is None or out.utcoffset() is None:
        raise M15BarAuthorityError("M15_TIMESTAMP_TZ_REQUIRED")
    return out.astimezone(timezone.utc)


def _value(raw: Any) -> float:
    if not isinstance(raw, dict) or set(raw) != {"value"} or not isinstance(raw["value"], str):
        raise M15BarAuthorityError("M15_REST_PRICE_SCHEMA_INVALID")
    try:
        val = Decimal(raw["value"])
    except InvalidOperation:
        raise M15BarAuthorityError("M15_REST_PRICE_INVALID") from None
    if not val.is_finite() or val <= 0:
        raise M15BarAuthorityError("M15_REST_PRICE_INVALID")
    out = float(val)
    if not math.isfinite(out) or out <= 0:
        raise M15BarAuthorityError("M15_REST_PRICE_FLOAT_RANGE")
    return out


def trading_windows(schedule: Any) -> tuple[tuple[datetime, datetime], ...]:
    """H1-style validated FINAM session windows, M15-grid alignment.

    Validate every session including non-trading ones; reject overlap of
    trading windows, while merge touching trading windows. Only exact
    continuous trading intervals may witness M15 completed candles.
    """
    if not isinstance(schedule, dict) or not isinstance(schedule.get("sessions"), list):
        raise M15BarAuthorityError("M15_SCHEDULE_SCHEMA_INVALID")
    intervals: list[tuple[datetime, datetime]] = []
    for row in schedule["sessions"]:
        if not isinstance(row, dict) or row.get("type") not in ALL_TYPES:
            raise M15BarAuthorityError("M15_SCHEDULE_SESSION_INVALID")
        span = row.get("interval")
        if not isinstance(span, dict):
            raise M15BarAuthorityError("M15_SCHEDULE_INTERVAL_INVALID")
        start, end = _utc(span.get("start_time")), _utc(span.get("end_time"))
        if end <= start:
            raise M15BarAuthorityError("M15_SCHEDULE_INTERVAL_ORDER_INVALID")
        if row["type"] not in TRADING_TYPES:
            continue
        if any((x.second or x.microsecond or x.minute % 15) for x in (start, end)):
            raise M15BarAuthorityError("M15_SCHEDULE_GRID_INVALID")
        intervals.append((start, end))
    out: list[tuple[datetime, datetime]] = []
    for a, b in sorted(intervals):
        if out and a < out[-1][1]:
            raise M15BarAuthorityError("M15_TRADING_SESSIONS_OVERLAP")
        if out and a == out[-1][1]:
            out[-1] = (out[-1][0], b)
        else:
            out.append((a, b))
    if not out:
        raise M15BarAuthorityError("M15_NO_TRADING_SESSIONS")
    return tuple(out)


def completed_close_labeled_m15(
    response: Any,
    schedule: Any,
    *,
    observed_at: datetime,
    verified_open_labels: bool = False,
) -> pd.DataFrame:
    """Strictly complete, adjacent-bar-proven OHLCV with Moscow CLOSE index.

    Assumes the observed source timestamps are FINAM bar OPEN only when
    independently established by operator and explicitly passed true.
    This boolean is NOT live permission; the caller must keep separate
    explicit evidence for the assertion (not provided by this module).
    """
    if verified_open_labels is not True:
        raise M15BarAuthorityError("M15_BROKER_LABEL_AUTHORITY_NOT_VERIFIED")
    if not isinstance(observed_at, datetime) or observed_at.tzinfo is None or observed_at.utcoffset() is None:
        raise M15BarAuthorityError("M15_OBSERVATION_TZ_REQUIRED")
    now = observed_at.astimezone(timezone.utc)
    if not isinstance(response, dict) or not isinstance(response.get("bars"), list):
        raise M15BarAuthorityError("M15_BARS_SCHEMA_INVALID")
    windows = trading_windows(schedule)
    previous: datetime | None = None
    accepted: list[tuple[datetime, dict[str, Any]]] = []
    rows: list[tuple[datetime, dict[str, Any]]] = []
    for row in response["bars"]:
        if not isinstance(row, dict):
            raise M15BarAuthorityError("M15_BARS_ROW_INVALID")
        opened = _utc(row.get("timestamp"))
        # A just-opened next candle at now is a valid publication witness.
        if opened > now:
            raise M15BarAuthorityError("M15_BROKER_FUTURE_OPEN")
        if opened.minute % 15 or opened.second or opened.microsecond:
            raise M15BarAuthorityError("M15_BROKER_OPEN_GRID_INVALID")
        if previous is not None and opened <= previous:
            raise M15BarAuthorityError("M15_BROKER_OPEN_DUPLICATE_OR_UNSORTED")
        previous = opened
        in_window = any(start <= opened < end for start, end in windows)
        if not in_window:
            raise M15BarAuthorityError("M15_BAR_OUTSIDE_TRADING_WINDOW")
        # No next candle is needed to validate the open timestamp itself.
        rows.append((opened, row))

    for (opened, row), (next_open, _) in zip(rows, rows[1:]):
        closing = opened + STEP
        if next_open != closing or closing > now:
            continue
        # Adjacent bars must both belong to one *same* continuous trading window.
        if not any(start <= opened and next_open < end for start, end in windows):
            continue
        vals = {key: _value(row.get(key.lower())) for key in ("Open", "High", "Low", "Close")}
        if not (vals["High"] >= max(vals["Open"], vals["Low"], vals["Close"])
                and vals["Low"] <= min(vals["Open"], vals["High"], vals["Close"])):
            raise M15BarAuthorityError("M15_BROKER_OHLC_INVALID")
        volume = row.get("volume")
        if not isinstance(volume, dict) or set(volume) != {"value"}:
            raise M15BarAuthorityError("M15_BROKER_VOLUME_SCHEMA_INVALID")
        try:
            vol = Decimal(volume["value"])
        except (InvalidOperation, TypeError):
            raise M15BarAuthorityError("M15_BROKER_VOLUME_INVALID") from None
        if not vol.is_finite() or vol < 0:
            raise M15BarAuthorityError("M15_BROKER_VOLUME_INVALID")
        vol_float = float(vol)
        if not math.isfinite(vol_float):
            raise M15BarAuthorityError("M15_BROKER_VOLUME_FLOAT_RANGE")
        vals["Volume"] = vol_float
        accepted.append((closing.astimezone(MOSCOW), vals))
    index = pd.DatetimeIndex([t for t, _ in accepted], tz=MOSCOW)
    values = [v for _, v in accepted]
    return pd.DataFrame(values, index=index, columns=("Open", "High", "Low", "Close", "Volume"))
