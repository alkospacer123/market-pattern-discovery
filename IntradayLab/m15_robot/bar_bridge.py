"""Fail-closed causal FINAM M15 open-label -> research M15 close-label bridge.

Source design: inspected H1 completed_h1_bars/trading_h1_windows; duration
is M15, not the H1 full-hour/shortened-session rule. Nothing here grants
trading or infers that actual FINAM M15 timestamps have been verified.

An explicit, operator-attested FINAM M15 *open-label* proof is required.
A completed M15 candle is accepted only after its immediately adjacent
next M15 bar OPEN timestamp is observed within one continuous session, OR
on the exact attested session end when schedule completion is proven (same
end-of-window authority as H1). The next candle's prices/extrema are NEVER
used. Missing intraday next bar => missing evidence; no gap synthesis or
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
    """Validate exact FINAM session boundaries; never round off-grid edges.

    Trading may end at 23:50 MSK. Reject trading-versus-clearing/auction
    overlap, merge only touching trading windows, and never invent a full
    M15 bar across an off-grid session boundary.
    """
    if not isinstance(schedule, dict) or not isinstance(schedule.get("sessions"), list):
        raise M15BarAuthorityError("M15_SCHEDULE_SCHEMA_INVALID")
    intervals: list[tuple[datetime, datetime]] = []
    all_sessions: list[tuple[datetime, datetime, str]] = []
    for row in schedule["sessions"]:
        if not isinstance(row, dict) or row.get("type") not in ALL_TYPES:
            raise M15BarAuthorityError("M15_SCHEDULE_SESSION_INVALID")
        span = row.get("interval")
        if not isinstance(span, dict):
            raise M15BarAuthorityError("M15_SCHEDULE_INTERVAL_INVALID")
        start, end = _utc(span.get("start_time")), _utc(span.get("end_time"))
        if end <= start:
            raise M15BarAuthorityError("M15_SCHEDULE_INTERVAL_ORDER_INVALID")
        kind = row["type"]
        all_sessions.append((start, end, kind))
        if kind in TRADING_TYPES:
            intervals.append((start, end))
    # Half-open intervals: an exact shared boundary is permitted, but
    # overlapping clearing/auction is never silently treated as trading.
    for i, (a, b, kind) in enumerate(all_sessions):
        for x, y, other in all_sessions[i + 1:]:
            if max(a, x) < min(b, y) and (kind in TRADING_TYPES or other in TRADING_TYPES):
                raise M15BarAuthorityError("M15_TRADING_SESSIONS_OVERLAP")
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

    for i, (opened, row) in enumerate(rows):
        closing = opened + STEP
        if closing > now:
            continue
        next_open = rows[i + 1][0] if i + 1 < len(rows) else None
        # A 23:45->00:00 interval is NOT a full M15 candle if the
        # verified session ends at 23:50. Off-grid ends are never rounded.
        if not any(start <= opened and closing <= end for start, end in windows):
            continue
        # Exact aligned session end may witness completion without next OPEN.
        end_witness = any(start <= opened and closing == end for start, end in windows)
        # Otherwise require the NEXT adjacent OPEN within the same session.
        # Never inspect the next bar's OHLCV.
        adjacency_witness = (
            next_open == closing
            and any(start <= opened and closing < end for start, end in windows)
        )
        if not (end_witness or adjacency_witness):
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
