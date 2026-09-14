"""Deterministic first BBW trading baseline (H1 setup, native M15 entry).

Input candle timestamps are START labels.  Consequently an H1 row at ``t``
is used at ``t + 1 hour`` and an M15 row at ``t`` at ``t + 15 minutes``.
Ranges never cross a calendar-day boundary.  The module intentionally contains
no optimization, robustness analysis, parameter search, or new indicators.
"""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path
from typing import Any

import pandas as pd

from .bbw_engine import OUTPUT_NAME, file_sha256

TRADE_COLUMNS = (
    "entry_time", "exit_time", "direction", "entry_price", "stop_price",
    "tp1", "tp2", "tp3", "result_R", "exit_reason",
)


class BaselineError(ValueError):
    """Raised when a Baseline input or causal contract is violated."""


@dataclass(frozen=True)
class BaselineConfig:
    range_min_bars: int = 6
    range_max_bars: int = 30
    range_atr_min: float = 1.0
    range_atr_max: float = 2.0
    retest_min_bars: int = 5
    retest_max_bars: int = 30
    penetration_range_pct: float = 0.20
    stop_offset: float = 4.0
    tp_levels: tuple[float, ...] = (1.0, 2.0, 3.0)
    tp_fractions: tuple[float, ...] = (0.5, 0.3, 0.2)


@dataclass(frozen=True)
class BreakoutEvent:
    timestamp: pd.Timestamp
    direction: str
    range_high: float
    range_low: float
    range_width: float


@dataclass(frozen=True)
class TradeSignal:
    timestamp: pd.Timestamp
    symbol: str
    direction: str
    entry_price: float
    range_high: float
    range_low: float
    range_width: float


def load_baseline_config(path: Path | None = None) -> BaselineConfig:
    if path is None:
        path = Path(__file__).resolve().parents[2] / "config" / "bbw_baseline.json"
    raw = json.loads(path.read_text(encoding="utf-8"))
    for key in ("tp_levels", "tp_fractions"):
        if key in raw:
            raw[key] = tuple(raw[key])
    config = BaselineConfig(**raw)
    if not (1 <= config.range_min_bars <= config.range_max_bars):
        raise BaselineError("invalid H1 range window")
    if not (1 <= config.retest_min_bars <= config.retest_max_bars):
        raise BaselineError("invalid M15 retest window")
    if len(config.tp_levels) != 3 or len(config.tp_fractions) != 3 or abs(sum(config.tp_fractions) - 1) > 1e-12:
        raise BaselineError("TP configuration must contain three levels whose fractions sum to one")
    return config


def _validate(frame: pd.DataFrame, required: set[str], name: str) -> pd.DataFrame:
    missing = required - set(frame.columns)
    if missing:
        raise BaselineError(f"{name} missing columns: {sorted(missing)}")
    work = frame.copy().reset_index(drop=True)
    work["timestamp"] = pd.to_datetime(work["timestamp"], errors="raise")
    if work.empty or work.timestamp.duplicated().any() or not work.timestamp.is_monotonic_increasing:
        raise BaselineError(f"{name} timestamps must be non-empty, unique, and increasing")
    if work.timestamp.dt.year.eq(2025).any():
        raise BaselineError("locked TRUE OOS calendar year 2025 is present")
    for column in {"open", "high", "low", "close", "volume", "atr14"} & set(work.columns):
        work[column] = pd.to_numeric(work[column], errors="raise")
    return work


def form_range(bars: pd.DataFrame, atr: float, config: BaselineConfig) -> tuple[float, float, float] | None:
    """Form a wick-based range and apply the inclusive 1--2 ATR filter."""
    if not config.range_min_bars <= len(bars) <= config.range_max_bars or pd.isna(atr) or atr <= 0:
        return None
    high, low = float(bars.high.max()), float(bars.low.min())
    width = high - low
    return (high, low, width) if config.range_atr_min * atr <= width <= config.range_atr_max * atr else None


def find_breakouts(h1: pd.DataFrame, config: BaselineConfig) -> list[BreakoutEvent]:
    """Find breakouts from observable prefixes; the breakout bar is excluded."""
    required = {"timestamp", "open", "high", "low", "close", "volume", "bbw", "bbw_squeeze", "ema50", "trend_direction", "atr14"}
    bars = _validate(h1, required, "H1 features")
    squeeze = bars["bbw_squeeze"]
    if not pd.api.types.is_bool_dtype(squeeze):
        mapped = squeeze.astype(str).str.strip().str.lower().map({"true": True, "false": False})
        if mapped.isna().any():
            raise BaselineError("bbw_squeeze must contain only TRUE/FALSE")
        bars["bbw_squeeze"] = mapped
    events: list[BreakoutEvent] = []
    active: int | None = None
    for i, row in bars.iterrows():
        # A new squeeze starts only when no earlier squeeze is being evaluated.
        if active is None and bool(row.bbw_squeeze):
            active = i
            continue
        if active is None:
            continue
        if row.timestamp.date() != bars.at[active, "timestamp"].date() or i - active > config.range_max_bars:
            active = i if bool(row.bbw_squeeze) else None
            continue
        candidate = bars.iloc[active:i]  # never includes the possible breakout
        value = form_range(candidate, float(row.atr14), config)
        if value is None:
            continue
        high, low, width = value
        direction = "LONG" if row.close > high else "SHORT" if row.close < low else None
        if direction is not None and row.trend_direction == direction:
            # Event timestamp is the instant at which the START-labelled H1 bar closes.
            events.append(BreakoutEvent(row.timestamp + pd.Timedelta(hours=1), direction, high, low, width))
            active = None
    return events


def find_trade_signals(events: list[BreakoutEvent], m15: pd.DataFrame, symbol: str,
                       config: BaselineConfig) -> list[TradeSignal]:
    bars = _validate(m15, {"timestamp", "open", "high", "low", "close", "volume"}, "M15")
    signals: list[TradeSignal] = []
    occupied: set[pd.Timestamp] = set()
    for event in sorted(events, key=lambda item: (item.timestamp, item.direction)):
        eligible = bars.loc[bars.timestamp.ge(event.timestamp)].head(config.retest_max_bars)
        for ordinal, (_, bar) in enumerate(eligible.iterrows(), start=1):
            level = event.range_high if event.direction == "LONG" else event.range_low
            penetration = max(0.0, level - float(bar.low)) if event.direction == "LONG" else max(0.0, float(bar.high) - level)
            touched = bar.low <= level if event.direction == "LONG" else bar.high >= level
            confirms = bar.close > level if event.direction == "LONG" else bar.close < level
            # A deep penetration or any close inside the old range invalidates the setup.
            inside_close = bar.close < level if event.direction == "LONG" else bar.close > level
            if penetration > config.penetration_range_pct * event.range_width + 1e-12 or inside_close:
                break
            if touched and ordinal >= config.retest_min_bars and confirms:
                timestamp = bar.timestamp + pd.Timedelta(minutes=15)
                if timestamp not in occupied:
                    signals.append(TradeSignal(timestamp, symbol, event.direction, float(bar.close),
                                               event.range_high, event.range_low, event.range_width))
                    occupied.add(timestamp)
                break
    return sorted(signals, key=lambda item: (item.timestamp, item.direction))


def trade_levels(signal: TradeSignal, config: BaselineConfig) -> tuple[float, float, float, float]:
    stop = signal.range_low - config.stop_offset if signal.direction == "LONG" else signal.range_high + config.stop_offset
    risk = abs(signal.entry_price - stop)
    if risk <= 0:
        raise BaselineError("entry must have positive stop distance")
    sign = 1 if signal.direction == "LONG" else -1
    targets = tuple(signal.entry_price + sign * level * risk for level in config.tp_levels)
    return (stop, *targets)


def simulate_trades(signals: list[TradeSignal], m15: pd.DataFrame, config: BaselineConfig) -> pd.DataFrame:
    """Simulate independent signals with deterministic stop-first OHLC ties."""
    bars = _validate(m15, {"timestamp", "open", "high", "low", "close", "volume"}, "M15")
    rows: list[dict[str, Any]] = []
    for signal in signals:
        stop, tp1, tp2, tp3 = trade_levels(signal, config)
        targets = (tp1, tp2, tp3)
        remaining, result_r, reached = 1.0, 0.0, 0
        exit_time, reason = signal.timestamp, "END_OF_DATA"
        future = bars.loc[(bars.timestamp + pd.Timedelta(minutes=15)).gt(signal.timestamp)]
        for _, bar in future.iterrows():
            close_time = bar.timestamp + pd.Timedelta(minutes=15)
            stop_hit = bar.low <= stop if signal.direction == "LONG" else bar.high >= stop
            if stop_hit:  # conservative, reproducible resolution of same-bar ambiguity
                result_r -= remaining
                exit_time, reason, remaining = close_time, "STOP", 0.0
                break
            while reached < 3 and ((bar.high >= targets[reached]) if signal.direction == "LONG" else (bar.low <= targets[reached])):
                fraction = config.tp_fractions[reached]
                result_r += fraction * config.tp_levels[reached]
                remaining -= fraction
                reached += 1
            if reached == 3:
                exit_time, reason, remaining = close_time, "TP3", 0.0
                break
        if remaining > 1e-12 and not future.empty:
            last = future.iloc[-1]
            risk = abs(signal.entry_price - stop)
            mark_r = (float(last.close) - signal.entry_price) / risk * (1 if signal.direction == "LONG" else -1)
            result_r += remaining * mark_r
            exit_time = last.timestamp + pd.Timedelta(minutes=15)
        rows.append({"entry_time": signal.timestamp, "exit_time": exit_time, "direction": signal.direction,
                     "entry_price": signal.entry_price, "stop_price": stop, "tp1": tp1, "tp2": tp2,
                     "tp3": tp3, "result_R": result_r, "exit_reason": reason})
    return pd.DataFrame(rows, columns=TRADE_COLUMNS)


def _resolve(root: Path, symbol: str, filename: str) -> Path:
    for path in (root / filename, root / symbol / filename):
        if path.is_file():
            return path
    raise BaselineError(f"{filename} not found under {root}")


def _report(trades: pd.DataFrame, first: pd.Timestamp, last: pd.Timestamp, digest: str) -> str:
    count = len(trades)
    wins = int((trades.result_R > 0).sum()) if count else 0
    gross_win = float(trades.loc[trades.result_R > 0, "result_R"].sum()) if count else 0.0
    gross_loss = -float(trades.loc[trades.result_R < 0, "result_R"].sum()) if count else 0.0
    pf = "N/A" if gross_loss == 0 else f"{gross_win / gross_loss:.6f}"
    streak = maximum = 0
    for value in trades.result_R if count else []:
        streak = streak + 1 if value < 0 else 0
        maximum = max(maximum, streak)
    duration = ((pd.to_datetime(trades.exit_time) - pd.to_datetime(trades.entry_time)).dt.total_seconds().mean() / 60) if count else 0.0
    directions = trades.direction.value_counts() if count else {}
    return "\n".join(["# BBW Baseline Report", "", "**Scope:** first deterministic Baseline only; no Robustness or Optimization.", "",
        f"- Test period: {first.isoformat()} — {last.isoformat()}", f"- Trades: {count}",
        f"- Direction: LONG={int(directions.get('LONG', 0))}, SHORT={int(directions.get('SHORT', 0))}",
        f"- Win rate: {(100 * wins / count if count else 0):.6f}%", f"- Mean R: {(trades.result_R.mean() if count else 0):.6f}",
        f"- Profit factor: {pf}", f"- Maximum losing streak: {maximum}", f"- Mean duration: {duration:.6f} minutes",
        f"- BASELINE_TRADES.csv SHA-256: `{digest}`", "", "H1 and M15 inputs are START-labelled. Decisions use bars only after their close; ranges reset at calendar-day boundaries. Same-bar stop/target ambiguity is resolved stop-first. No commissions, slippage, trailing, news filter, or parameter search is applied in this requested first baseline.", ""])


def run_baseline(feature_root: Path, normalized_root: Path, output_root: Path,
                 symbol: str, config: BaselineConfig | None = None) -> dict[str, Any]:
    if symbol != "CNYRUBF":
        raise BaselineError("Baseline currently permits only CNYRUBF")
    config = config or load_baseline_config()
    feature_path = _resolve(feature_root, symbol, OUTPUT_NAME)
    m15_path = _resolve(normalized_root, symbol, "M15.csv")
    manifest_path = _resolve(normalized_root, symbol, "NORMALIZED_MANIFEST.json")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("instrument") != symbol or manifest.get("timestamp_semantics") != "START":
        raise BaselineError("normalized manifest instrument or timestamp semantics mismatch")
    expected_m15 = manifest.get("timeframes", {}).get("M15", {}).get("sha256")
    if not expected_m15 or file_sha256(m15_path) != expected_m15:
        raise BaselineError("normalized M15 hash does not match its manifest")
    before = {path: file_sha256(path) for path in (feature_path, m15_path)}
    h1, m15 = pd.read_csv(feature_path), pd.read_csv(m15_path)
    events = find_breakouts(h1, config)
    signals = find_trade_signals(events, m15, symbol, config)
    trades = simulate_trades(signals, m15, config)
    payload = trades.to_csv(index=False, lineterminator="\n", date_format="%Y-%m-%d %H:%M:%S", float_format="%.15g").encode("utf-8")
    digest = sha256(payload).hexdigest()
    output_root.mkdir(parents=True, exist_ok=True)
    (output_root / "BASELINE_TRADES.csv").write_bytes(payload)
    m15_times = pd.to_datetime(m15.timestamp)
    (output_root / "BASELINE_REPORT.md").write_text(_report(trades, m15_times.iloc[0], m15_times.iloc[-1] + pd.Timedelta(minutes=15), digest), encoding="utf-8")
    if any(file_sha256(path) != digest_before for path, digest_before in before.items()):
        raise BaselineError("input data mutated during Baseline execution")
    return {"trades": len(trades), "breakout_events": len(events), "trade_signals": len(signals), "sha256": digest}
