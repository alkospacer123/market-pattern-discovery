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
import re
from statistics import median
from typing import Any, Mapping, Sequence

STEP = timedelta(minutes=15)
SESSION_OFFSET = timedelta(hours=9)  # frozen V20 observation-day key
WINDOW = 20
METRIC_SCHEMA = "v20.market_metrics.clv_inside.v2"
# Instrument selection belongs to the operator; trading N4 remains in robots.json.
SYMBOL_PATTERN = re.compile(r"[A-Z][A-Z0-9._-]{0,31}")
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
    # Same adjust=False Wilder recurrence as frozen base.prepare; warm start
    # at the beginning of this card window, not the original archive ATR state.
    atr = trs[0]
    for tr in trs[1:]:
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
    events = confirmed = returned = 0
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
                        level = max(x.high for x in past) if side == 1 else min(x.low for x in past)
                        returned += (next_bar.close-level)*side <= 0
            history.append(bar)
    return {"completed_breakouts": events, "continuations": confirmed,
            "continuation_rate": confirmed / events if events else None,
            "return_inside_rate": returned / events if events else None,
            "reversion_or_stall_rate": (events - confirmed) / events if events else None}


def clv_pressure_prior12(bars: Sequence[M15Bar]) -> float | None:
    """Frozen cmfr at the last bar: exclude that bar, include doji volume.

    The named rolling window crosses verified session boundaries, as in run.py.
    Zero-range CLV is zero; zero total volume is unobserved, not neutral.
    """
    if len(bars) < 13:
        return None
    prior = bars[-13:-1]
    volume = sum(b.volume for b in prior)
    return (sum(((2*b.close-b.low-b.high)/(b.high-b.low)
                 if b.high > b.low else 0.0)*b.volume for b in prior) / volume
            if volume else None)


def _pressure_stats(bars: list[M15Bar]) -> dict:
    values, aligned, agreements = [], [], []
    for i in range(12, len(bars)):
        pressure = clv_pressure_prior12(bars[i-12:i+1])
        if pressure is None:
            continue
        values.append(pressure)
        # Movement over the SAME twelve prior closes, excluding the current bar.
        move = bars[i-1].close - bars[i-12].close
        if move:
            aligned.append(pressure * (1 if move > 0 else -1))
            if pressure:
                agreements.append(pressure * move > 0)
    latest = clv_pressure_prior12(bars)
    return {"prior12_pressure": latest,
            "prior12_pressure_abs": abs(latest) if latest is not None else None,
            "pressure_windows": len(values),
            "mean_abs_pressure": sum(map(abs, values))/len(values) if values else None,
            "pressure_direction_alignment": sum(aligned)/len(aligned) if aligned else None,
            "direction_pairs": len(aligned), "nonzero_direction_pairs": len(agreements),
            "direction_agreement_rate": sum(agreements)/len(agreements) if agreements else None}


def _compression_stats(sessions: list[CompletedSession]) -> dict:
    """Strict finished-day pairs; release diagnostics are already completed history.

    Daytime bounds match V4 (10:00 <= open < 18:00). Validity is V4's >=12,
    first <=10:15, last >=17:15, in addition to caller's schedule completeness.
    Release crosses use V4's 10:00..16:45 labels, without its EMA signal gate.
    """
    days = [[b for b in s.bars if 600 <= b.open_time.hour*60+b.open_time.minute < 1080]
            for s in sessions]
    valid = [len(bs) >= 12 and bs[0].open_time.hour*60+bs[0].open_time.minute <= 615
             and bs[-1].open_time.hour*60+bs[-1].open_time.minute >= 1035 for bs in days]
    bounds = [(max(b.high for b in bs), min(b.low for b in bs)) if bs else (0, 0)
              for bs in days]
    pairs, inside, ratios = 0, 0, []
    events = continued = returned = pending = 0
    latest_inside = latest_ratio = None
    for i in range(1, len(days)):
        if not (valid[i-1] and valid[i]):
            continue
        oh, ol = bounds[i-1]
        ph, pl = bounds[i]
        strict = ph < oh and pl > ol
        ratio = (ph-pl)/(oh-ol) if oh > ol else None
        pairs += 1
        inside += strict
        if ratio is not None:
            ratios.append(ratio)
        if i == len(days)-1:
            latest_inside, latest_ratio = strict, ratio
        # The pair is known BEFORE the release session starts. Never use the
        # release day to decide whether the two preceding days were inside.
        if not strict or i+1 >= len(days):
            continue
        previous_close = days[i][-1].close
        for j, bar in enumerate(days[i+1]):
            side = (1 if bar.close > ph and previous_close <= ph else
                    -1 if bar.close < pl and previous_close >= pl else 0)
            previous_close = bar.close
            if not side or bar.open_time.hour >= 17:
                continue
            if j+1 >= len(days[i+1]) or days[i+1][j+1].open_time-bar.open_time != STEP:
                pending += 1
                continue
            next_close = days[i+1][j+1].close
            events += 1
            continued += (next_close-bar.close)*side > 0
            returned += (next_close-(ph if side == 1 else pl))*side <= 0
    return {"valid_day_pairs": pairs, "strict_inside_pairs": inside,
            "inside_session_share": inside/pairs if pairs else None,
            "latest_pair_strict_inside": latest_inside,
            "latest_range_ratio": latest_ratio,
            "range_compression_ratio": median(ratios) if ratios else None,
            "completed_release_breakouts": events, "unconfirmed_release_breakouts": pending,
            "inside_release_continuation_rate": continued/events if events else None,
            "inside_release_return_rate": returned/events if events else None}


def _strategy_readouts(sessions: list[CompletedSession], metrics: dict[str, Any]) -> dict:
    common = {
        "atr14_pct_close": metrics["volatility"]["atr14_pct_close"],
        "directional_efficiency": metrics["directionality"]["session_efficiency_ratio"],
        "continuation_rate": metrics["breakouts"]["continuation_rate"],
        "pressure_direction_alignment": metrics["volume_pressure"]["pressure_direction_alignment"],
        "range_compression_ratio": metrics["compression"]["range_compression_ratio"],
    }
    result = {name: dict(common) for name in STRATEGIES}
    result["OBV_PRESSURE"].update(metrics["volume_pressure"])
    result["INSIDE_DAY_RELEASE"].update(metrics["compression"])
    return result


def _deltas(current: Mapping[str, Any], previous: Mapping[str, Any] | None) -> dict:
    if previous is None:
        return {}
    values = {}
    for group in ("volatility", "directionality", "breakouts", "volume_pressure", "compression", "liquidity"):
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
    expected_session_days: Sequence[date] | None = None,
) -> dict:
    """Return serializable metrics for ALL THREE strategies; NEVER accept/filter signals.

    execution_readonly may contain price_step, tick_value_rub, lot_size, roundtrip_cost_rub,
    spread_price, initial_margin_rub. Missing fields stay None/UNKNOWN.
    """
    if not isinstance(symbol, str) or SYMBOL_PATTERN.fullmatch(symbol) is None:
        raise ValueError("INVALID_MARKET_ANALYSIS_SYMBOL")
    if previous is not None:
        if previous.get("metric_schema") != METRIC_SCHEMA:
            raise ValueError("PREVIOUS_CARD_METRIC_SCHEMA_MISMATCH")
        if previous.get("symbol") != symbol:
            raise ValueError("PREVIOUS_CARD_SYMBOL_MISMATCH")
        try:
            previous_at = datetime.fromisoformat(previous["as_of_msk"])
        except (KeyError, ValueError, TypeError) as exc:
            raise ValueError("PREVIOUS_CARD_TIMESTAMP_INVALID") from exc
        if previous_at.tzinfo is not None or previous_at >= as_of:
            raise ValueError("PREVIOUS_CARD_NOT_CAUSALLY_EARLIER")
    recent, quality = _check(sessions, as_of)
    missing_days = 0
    if expected_session_days is not None:
        calendar = list(expected_session_days)
        if (any(not isinstance(d, date) or isinstance(d, datetime) for d in calendar)
                or calendar != sorted(set(calendar))
                or any(d > as_of.date() for d in calendar)):
            raise ValueError("EXPECTED_SESSION_DAYS_INVALID")
        observed = {s.day for s in sessions}
        if not observed <= set(calendar):
            raise ValueError("SESSION_OUTSIDE_VERIFIED_CALENDAR")
        missing_days = len(set(calendar[-WINDOW:]) - observed)
    quality["missing_sessions"] = missing_days
    quality["session_calendar"] = ("EXPLICIT_EXPECTED_DAYS" if expected_session_days is not None
                                   else "CALLER_ASSERTS_NO_OMITTED_SESSIONS")
    complete = len(recent) == WINDOW and quality["missing_bars"] == 0 and missing_days == 0
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
                  "spread_price", "initial_margin_rub", "lot_size"}
    if set(ticks) - authorized:
        raise ValueError("UNKNOWN_READONLY_EXECUTION_FIELD")
    ex = {k: _finite(ticks[k], k, positive=(k != "roundtrip_cost_rub" and k != "spread_price"))
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
        "volume_pressure": _pressure_stats(bars) if complete else {},
        "compression": _compression_stats(recent) if complete else {},
        "liquidity": {
            "median_m15_volume": median([b.volume for b in bars]) if complete else None,
            "observed_volume": sum(b.volume for b in bars) if complete else None,
            "price_step": ex["price_step"], "tick_value_rub": ex["tick_value_rub"],
            "lot_size": ex["lot_size"],
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
        "schema": "v20.market_suitability.readonly.v2",
        "metric_schema": METRIC_SCHEMA,
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
        "unrestricted_diagnostic_universe": True,
        "trading_instrument_authority": "OPERATOR_ONLY",
        "affects_signals_or_risk": False,
        "live_authorized": False,
    }
    return report
