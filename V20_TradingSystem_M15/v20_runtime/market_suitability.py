"""READONLY V20-04.2 market diagnostics; no signals, orders, thresholds or transport.

Inputs contain externally *verified* completed trading sessions with expected
M15 open labels. This function cannot prove FINAM's session-end or label
authority: caller must do that with a verified schedule/read-only source.
Only the last 20 observed, completed sessions are used for the card.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta
from math import isfinite
from statistics import median
from typing import Any, Mapping, Sequence

STEP = timedelta(minutes=15)
SESSION_OFFSET = timedelta(hours=9)  # frozen V20 observation-day key
WINDOW = 20
N4 = frozenset(("USDRUBF", "CNYRUBF", "GLDRUBF", "IMOEXF"))
STRATEGIES = ("SHALLOW_PULLBACK", "OBV_PRESSURE", "INSIDE_DAY_RELEASE")


@dataclass(frozen=True)
class M15Bar:
    open_time: datetime  # Moscow-local naive; OPEN-labelled
    open: float
    high: float
    low: float
    close: float
    volume: float


@dataclass(frozen=True)
class CompletedSession:
    day: date  # (M15 open_time - 09:00).date(), NOT calendar midnight
    expected_opens: tuple[datetime, ...]  # verified schedule incl. breaks
    bars: tuple[M15Bar, ...]
    closed_at: datetime  # externally witnessed session completion, MSK naive


def _finite(value: Any, name: str, *, positive: bool = False) -> float:
    if isinstance(value, bool):
        raise ValueError(name)
    try:
        result = float(value)
    except (ValueError, TypeError, OverflowError) as exc:
        raise ValueError(name) from exc
    if not isfinite(result) or (result <= 0 if positive else result < 0):
        raise ValueError(name)
    return result


def _time(ts: datetime) -> bool:
    return (
        isinstance(ts, datetime) and ts.tzinfo is None
        and ts.second == 0 and ts.microsecond == 0
        and ts.minute % 15 == 0
    )


def _check(sessions: Sequence[CompletedSession], as_of: datetime) -> tuple[list[CompletedSession], dict]:
    if not isinstance(as_of, datetime) or as_of.tzinfo is not None:
        raise ValueError("MOSCOW_NAIVE_AS_OF_REQUIRED")
    if as_of.second or as_of.microsecond:
        raise ValueError("AS_OF_PRECISION_INVALID")
    if not sessions:
        return [], {"observed_sessions": 0, "required_sessions": WINDOW,
                    "expected_bars": 0, "observed_bars": 0, "missing_bars": 0}
    ordered = sorted(sessions, key=lambda x: x.day)
    if [s.day for s in sessions] != [s.day for s in ordered]:
        raise ValueError("SESSIONS_NOT_ORDERED")
    if len({s.day for s in sessions}) != len(sessions):
        raise ValueError("DUPLICATE_SESSION")
    recent = ordered[-WINDOW:]
    expected_count = observed_count = missing_count = 0
    for s in recent:
        if not isinstance(s.day, date) or not isinstance(s.closed_at, datetime):
            raise ValueError("SESSION_SCHEMA_INVALID")
        if s.closed_at.tzinfo is not None or s.closed_at > as_of:
            raise ValueError("SESSION_NOT_OBSERVABLY_COMPLETE")
        expected = tuple(s.expected_opens)
        opens = tuple(b.open_time for b in s.bars)
        if not expected or tuple(sorted(expected)) != expected or len(set(expected)) != len(expected):
            raise ValueError("EXPECTED_SESSION_SCHEDULE_INVALID")
        if tuple(sorted(opens)) != opens or len(set(opens)) != len(opens):
            raise ValueError("M15_DUPLICATE_OR_UNORDERED")
        if any(not _time(x) or (x - SESSION_OFFSET).date() != s.day for x in expected):
            raise ValueError("EXPECTED_SESSION_TIME_INVALID")
        if any(x not in set(expected) for x in opens):
            raise ValueError("OBSERVATION_OUTSIDE_VERIFIED_SCHEDULE")
        if any(x + STEP > s.closed_at for x in opens):
            raise ValueError("M15_BAR_NOT_COMPLETED")
        for b in s.bars:
            o, h, l, c = (_finite(getattr(b, field), field, positive=True)
                          for field in ("open", "high", "low", "close"))
            _finite(b.volume, "volume")
            if h < max(o, l, c) or l > min(o, h, c):
                raise ValueError("M15_OHLC_INVALID")
        expected_count += len(expected)
        observed_count += len(opens)
        missing_count += len(set(expected) - set(opens))
    return recent, {"observed_sessions": len(recent), "required_sessions": WINDOW,
                    "expected_bars": expected_count, "observed_bars": observed_count,
                    "missing_bars": missing_count}


def _atr_wilder(bars: list[M15Bar]) -> float | None:
    if len(bars) < 14:
        return None
    trs = []
    prev = None
    for b in bars:
        tr = b.high - b.low if prev is None else max(
            b.high - b.low, abs(b.high - prev), abs(b.low - prev))
        trs.append(tr)
        prev = b.close
    atr = sum(trs[:14]) / 14
    for tr in trs[14:]:
        atr = (13 * atr + tr) / 14
    return atr


def _efficiency(values: list[float]) -> float | None:
    if len(values) < 2:
        return None
    travelled = sum(abs(b - a) for a, b in zip(values, values[1:]))
    return abs(values[-1] - values[0]) / travelled if travelled > 0 else 0.0


def _breakout_stats(sessions: list[CompletedSession]) -> dict[str, Any]:
    """20-prior-bar close breakout, fully observed next bar in same session only."""
    history: list[M15Bar] = []
    events = confirmed = 0
    for s in sessions:
        for i, bar in enumerate(s.bars):
            if len(history) >= 20 and i + 1 < len(s.bars):
                next_bar = s.bars[i + 1]
                if next_bar.open_time - bar.open_time == STEP:
                    past = history[-20:]
                    side = 1 if bar.close > max(x.high for x in past) else (
                        -1 if bar.close < min(x.low for x in past) else 0)
                    if side:
                        events += 1
                        if (next_bar.close - bar.close) * side > 0:
                            confirmed += 1
            history.append(bar)
    return {"completed_breakouts": events, "continuations": confirmed,
            "continuation_rate": confirmed / events if events else None,
            "reversion_or_stall_rate": (events - confirmed) / events if events else None}


def _strategy_readouts(sessions: list[CompletedSession], metrics: dict[str, Any]) -> dict:
    bars = [b for s in sessions for b in s.bars]
    up_volume = sum(b.volume for b in bars if b.close > b.open)
    down_volume = sum(b.volume for b in bars if b.close < b.open)
    directional_volume = up_volume + down_volume
    obv_pressure = ((up_volume - down_volume) / directional_volume
                    if directional_volume else None)
    inside_count = sum(
        int(s.bars and prev.bars
            and max(b.high for b in s.bars) <= max(b.high for b in prev.bars)
            and min(b.low for b in s.bars) >= min(b.low for b in prev.bars))
        for prev, s in zip(sessions, sessions[1:])
    )
    inside_pairs = sum(bool(s.bars and prev.bars)
                       for prev, s in zip(sessions, sessions[1:]))
    return {
        "SHALLOW_PULLBACK": {
            "directional_efficiency": metrics["directionality"]["session_efficiency_ratio"],
            "continuation_rate": metrics["breakouts"]["continuation_rate"]},
        "OBV_PRESSURE": {
            "signed_volume_pressure_ratio": obv_pressure,
            "continuation_rate": metrics["breakouts"]["continuation_rate"]},
        "INSIDE_DAY_RELEASE": {
            "inside_session_share": inside_count / inside_pairs if inside_pairs else None,
            "continuation_rate": metrics["breakouts"]["continuation_rate"]},
    }


def _deltas(current: Mapping[str, Any], previous: Mapping[str, Any] | None) -> dict:
    if previous is None:
        return {}
    values = {}
    for group in ("volatility", "directionality", "breakouts", "liquidity"):
        prior = previous.get("metrics", {}).get(group, {})
        for key, value in current.get(group, {}).items():
            old = prior.get(key) if isinstance(prior, dict) else None
            if (isinstance(value, (float, int)) and not isinstance(value, bool)
                    and isinstance(old, (float, int)) and not isinstance(old, bool)
                    and isfinite(value) and isfinite(old)):
                change = value - old
                values[f"{group}.{key}"] = {
                    "delta": change,
                    "movement": "increase" if change > 0 else (
                        "decrease" if change < 0 else "unchanged")}
    return values


def evaluate_market_card(
    symbol: str,
    sessions: Sequence[CompletedSession],
    *,
    as_of: datetime,
    previous: Mapping[str, Any] | None = None,
    execution_readonly: Mapping[str, Any] | None = None,
) -> dict:
    """Return serializable metrics for ALL THREE strategies; NEVER accept/filter signals.

    execution_readonly may contain price_step, tick_value_rub, roundtrip_cost_rub,
    spread_price, initial_margin_rub. Missing fields stay None/UNKNOWN.
    """
    if symbol not in N4:
        raise ValueError("SYMBOL_OUTSIDE_FROZEN_N4")
    if previous is not None:
        if previous.get("symbol") != symbol:
            raise ValueError("PREVIOUS_CARD_SYMBOL_MISMATCH")
        try:
            previous_at = datetime.fromisoformat(previous["as_of_msk"])
        except (KeyError, ValueError, TypeError) as exc:
            raise ValueError("PREVIOUS_CARD_TIMESTAMP_INVALID") from exc
        if previous_at.tzinfo is not None or previous_at >= as_of:
            raise ValueError("PREVIOUS_CARD_NOT_CAUSALLY_EARLIER")
    recent, quality = _check(sessions, as_of)
    complete = len(recent) == WINDOW and quality["missing_bars"] == 0
    bars = [b for s in recent for b in s.bars]
    atr = _atr_wilder(bars) if complete else None
    last_close = bars[-1].close if bars else None
    intraday_ranges = [(max(b.high for b in s.bars) - min(b.low for b in s.bars))
                       / s.bars[-1].close for s in recent if s.bars]
    closes = [s.bars[-1].close for s in recent if s.bars]
    breakout = _breakout_stats(recent) if complete else {
        "completed_breakouts": 0, "continuations": 0,
        "continuation_rate": None, "reversion_or_stall_rate": None}
    ticks = execution_readonly or {}
    authorized = {"price_step", "tick_value_rub", "roundtrip_cost_rub",
                  "spread_price", "initial_margin_rub"}
    if set(ticks) - authorized:
        raise ValueError("UNKNOWN_READONLY_EXECUTION_FIELD")
    ex = {k: _finite(v, k, positive=(k != "roundtrip_cost_rub" and k != "spread_price"))
          if k in ticks and ticks[k] is not None else None for k in authorized}
    cost_ratio = None
    if (atr is not None and atr > 0 and ex["price_step"] and ex["tick_value_rub"]
            and ex["roundtrip_cost_rub"] is not None):
        stop_rub = (2 * atr / ex["price_step"]) * ex["tick_value_rub"]
        cost_ratio = ex["roundtrip_cost_rub"] / stop_rub if stop_rub > 0 else None
    metrics = {
        "volatility": {
            "atr14_wilder_price": atr,
            "atr14_pct_close": atr / last_close if atr is not None else None,
            "median_intraday_range_pct": median(intraday_ranges) if complete else None},
        "directionality": {
            "session_efficiency_ratio": _efficiency(closes) if complete else None},
        "breakouts": breakout,
        "liquidity": {
            "median_m15_volume": median([b.volume for b in bars]) if complete else None,
            "observed_volume": sum(b.volume for b in bars) if complete else None,
            "price_step": ex["price_step"], "tick_value_rub": ex["tick_value_rub"],
            "spread_price": ex["spread_price"],
            "initial_margin_rub": ex["initial_margin_rub"],
            "roundtrip_cost_rub": ex["roundtrip_cost_rub"],
            "roundtrip_cost_to_2atr_stop": cost_ratio},
        "data_quality": quality,
    }
    label = "НЕ ОЦЕНЕНО" if complete else "НЕДОСТАТОЧНО ДАННЫХ"
    readouts = _strategy_readouts(recent, metrics) if complete else {
        name: {} for name in STRATEGIES}
    report = {
        "schema": "v20.market_suitability.readonly.v1",
        "symbol": symbol,
        "as_of_msk": as_of.isoformat(),
        "last_completed_session": recent[-1].day.isoformat() if recent else None,
        "session_window": WINDOW,
        "data_authority": "CALLER_VERIFIED_CLOSED_SESSIONS_REQUIRED",
        "metrics": metrics,
        "metric_changes": _deltas(metrics, previous),
        "strategies": {
            name: {"suitability": label, "diagnostics": readouts[name]}
            for name in STRATEGIES},
        "changes_are_not_suitability_verdicts": True,
        "affects_signals_or_risk": False,
        "live_authorized": False,
    }
    return report
