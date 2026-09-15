"""Bounded sensitivity search around the unchanged BBW Baseline.

All indicators are calculated from the current and earlier START-labelled H1
bars.  Trading decisions remain delegated to :mod:`bbw_system.baseline`; this
module varies only parameters which already exist in that baseline/feature
definition.  Calendar year 2025 is rejected before any search is performed.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, replace
from hashlib import sha256
import json
from pathlib import Path
from typing import Any, Iterable

import numpy as np
import pandas as pd

from ..baseline import (
    BaselineConfig, find_breakouts, find_trade_signals, load_baseline_config,
    simulate_trades,
)
from ..bbw_engine import OUTPUT_NAME, file_sha256
from .optimization_report import build_report

RESULT_COLUMNS = (
    "parameter_id", "parameters_json", "trades", "breakout_count", "winrate",
    "mean_R", "profit_factor", "total_R", "max_drawdown", "avg_duration",
)
TRAIN_START = pd.Timestamp("2023-01-03")
TRAIN_END_EXCLUSIVE = pd.Timestamp("2025-01-01")
DEFAULT_GRID_LIMIT = 256


class OptimizationError(ValueError):
    """Raised when controlled-optimization safety contracts are violated."""


@dataclass(frozen=True, order=True)
class OptimizationParameters:
    bbw_period: int
    bbw_std: float
    squeeze_window: int
    range_min_bars: int
    range_max_bars: int
    atr_min: float
    atr_max: float
    ema_period: int
    ema_slope_threshold: float
    retest_min_bars: int
    retest_max_bars: int
    penetration: float


SPACE = {
    "bbw_period": (5, 10, 15, 20),
    "bbw_std": (1.5, 2.0, 2.5),
    "squeeze_window": (5, 10, 15, 20),
    "range_min_bars": (4, 6, 8, 10),
    "range_max_bars": (20, 30, 40),
    "atr_min": (0.5, 0.75, 1.0),
    "atr_max": (1.5, 2.0, 3.0),
    "ema_period": (30, 50, 100),
    "ema_slope_threshold": (0.0, 0.0005, 0.001),
    "retest_window": ((3, 20), (5, 30), (5, 40)),
    "penetration": (0.10, 0.20, 0.30),
}


def _json(parameters: OptimizationParameters) -> str:
    return json.dumps(asdict(parameters), sort_keys=True, separators=(",", ":"))


def _parameter_id(parameters: OptimizationParameters) -> str:
    return sha256(_json(parameters).encode()).hexdigest()[:16]


def generate_parameter_grid(limit: int | None = DEFAULT_GRID_LIMIT) -> list[OptimizationParameters]:
    """Return a reproducible bounded grid, sampled evenly from the full grid.

    Invalid range pairs (minimum greater than maximum) are omitted.  The frozen
    baseline combination is always included.  No random generator is used.
    Passing ``None`` returns the complete Cartesian grid.
    """
    import itertools

    names = tuple(SPACE)
    full: list[OptimizationParameters] = []
    for values in itertools.product(*(SPACE[name] for name in names)):
        item = dict(zip(names, values, strict=True))
        retest_min, retest_max = item.pop("retest_window")
        parameters = OptimizationParameters(**item, retest_min_bars=retest_min, retest_max_bars=retest_max)
        if parameters.range_min_bars <= parameters.range_max_bars and parameters.atr_min <= parameters.atr_max:
            full.append(parameters)
    full.sort()
    if limit is None or limit >= len(full):
        return full
    if limit < 1:
        raise OptimizationError("grid limit must be positive")
    indices = np.linspace(0, len(full) - 1, limit, dtype=int)
    selected = {full[int(index)] for index in indices}
    baseline = OptimizationParameters(10, 2.0, 10, 6, 30, 1.0, 2.0, 50, 0.001, 5, 30, 0.20)
    selected.add(baseline)
    ordered = sorted(selected)
    if len(ordered) > limit:
        # Drop the last non-baseline item, preserving a stable cardinality.
        ordered.remove(next(item for item in reversed(ordered) if item != baseline))
    return ordered


def _validate_train(frame: pd.DataFrame, name: str) -> pd.DataFrame:
    required = {"timestamp", "open", "high", "low", "close", "volume"}
    missing = required - set(frame)
    if missing:
        raise OptimizationError(f"{name} missing columns: {sorted(missing)}")
    work = frame.copy()
    work["timestamp"] = pd.to_datetime(work["timestamp"], errors="raise")
    if work.empty or work.timestamp.duplicated().any() or not work.timestamp.is_monotonic_increasing:
        raise OptimizationError(f"{name} timestamps must be non-empty, unique, and increasing")
    if work.timestamp.dt.year.eq(2025).any():
        raise OptimizationError("locked TRUE OOS calendar year 2025 is present")
    if work.timestamp.min() < TRAIN_START or work.timestamp.max() >= TRAIN_END_EXCLUSIVE:
        raise OptimizationError("optimization input must be within TRAIN 2023-01-03 through 2024-12-31")
    return work


def calculate_candidate_features(source: pd.DataFrame, parameters: OptimizationParameters) -> pd.DataFrame:
    """Recalculate candidate features using backward-looking windows only."""
    work = _validate_train(source, "H1 features")
    close = pd.to_numeric(work.close, errors="raise").astype(float)
    middle = close.rolling(parameters.bbw_period, min_periods=parameters.bbw_period).mean()
    deviation = close.rolling(parameters.bbw_period, min_periods=parameters.bbw_period).std(ddof=0)
    work["bbw"] = 2 * parameters.bbw_std * deviation / middle

    thresholds = pd.Series(np.nan, index=work.index)
    dates = work.timestamp.dt.date
    observed: list[object] = []
    values: dict[object, list[float]] = {}
    for index in work.index:
        day = dates.at[index]
        if not observed or observed[-1] != day:
            observed.append(day); values[day] = []
        if pd.notna(work.at[index, "bbw"]):
            values[day].append(float(work.at[index, "bbw"]))
        if len(observed) >= parameters.squeeze_window:
            history = [value for date in observed[-parameters.squeeze_window:] for value in values[date]]
            if len(history) >= 6:
                thresholds.at[index] = float(np.ceil(np.mean(sorted(history)[:6]) * 1000) / 1000)
    work["bbw_squeeze"] = (work.bbw < thresholds).fillna(False)
    ema = close.ewm(span=parameters.ema_period, adjust=False, min_periods=parameters.ema_period).mean()
    work["ema50"] = ema  # baseline's frozen input-column name
    work["ema_slope"] = ema - ema.shift(10)
    minimum = close.abs() * parameters.ema_slope_threshold
    work["trend_direction"] = np.select(
        [work.ema_slope > minimum, work.ema_slope < -minimum], ["LONG", "SHORT"], default="FLAT"
    )
    if "atr14" not in work:
        raise OptimizationError("H1 feature input has no causal atr14")
    return work


def calculate_metrics(trades: pd.DataFrame, cost_r: float = 0.0) -> dict[str, float | int]:
    results = pd.to_numeric(trades.get("result_R", pd.Series(dtype=float)), errors="raise") - cost_r
    count = len(results)
    wins, losses = results[results > 0], results[results < 0]
    gross_loss = -float(losses.sum())
    equity = results.cumsum()
    drawdown = equity.cummax().clip(lower=0) - equity if count else pd.Series(dtype=float)
    duration = (pd.to_datetime(trades.exit_time) - pd.to_datetime(trades.entry_time)).dt.total_seconds() / 60 if count else []
    return {
        "trades": count,
        "winrate": float((results > 0).mean()) if count else 0.0,
        "mean_R": float(results.mean()) if count else 0.0,
        "profit_factor": float(wins.sum() / gross_loss) if gross_loss else (float("inf") if len(wins) else 0.0),
        "total_R": float(results.sum()),
        "max_drawdown": float(drawdown.max()) if count else 0.0,
        "avg_duration": float(np.mean(duration)) if count else 0.0,
    }


def _resolve(root: Path, symbol: str, filename: str) -> Path:
    for path in (root / filename, root / symbol / filename):
        if path.is_file():
            return path
    raise OptimizationError(f"{filename} not found under {root}")


def _config_path(root: Path) -> Path:
    if root.is_file():
        return root
    for path in (
        root / "BASELINE_CONFIG.json",
        root / "bbw_baseline.json",
        root / "config" / "bbw_baseline.json",
    ):
        if path.is_file():
            return path
    raise OptimizationError(f"baseline config not found under {root}")


def _evaluate(parameters: OptimizationParameters, h1: pd.DataFrame, m15: pd.DataFrame,
              symbol: str, frozen: BaselineConfig, cost_r: float) -> tuple[dict[str, Any], pd.DataFrame]:
    features = calculate_candidate_features(h1, parameters)
    config = replace(frozen, range_min_bars=parameters.range_min_bars,
                     range_max_bars=parameters.range_max_bars, range_atr_min=parameters.atr_min,
                     range_atr_max=parameters.atr_max, retest_min_bars=parameters.retest_min_bars,
                     retest_max_bars=parameters.retest_max_bars,
                     penetration_range_pct=parameters.penetration)
    events = find_breakouts(features, config)
    signals = find_trade_signals(events, m15, symbol, config)
    trades = simulate_trades(signals, m15, config)
    row: dict[str, Any] = {"parameter_id": _parameter_id(parameters), "parameters_json": _json(parameters),
                           "breakout_count": len(events), **calculate_metrics(trades, cost_r)}
    return row, trades


def run_optimization(feature_root: Path, normalized_root: Path, baseline_root: Path,
                     output_root: Path, symbol: str, *, grid_limit: int = DEFAULT_GRID_LIMIT,
                     transaction_cost_r: float = 0.0, slippage_r: float = 0.0,
                     grid: Iterable[OptimizationParameters] | None = None) -> dict[str, Any]:
    """Execute controlled TRAIN-only research and write deterministic artifacts."""
    if symbol != "CNYRUBF":
        raise OptimizationError("optimization currently permits only CNYRUBF")
    if transaction_cost_r < 0 or slippage_r < 0:
        raise OptimizationError("cost and slippage must be non-negative")
    feature_path = _resolve(feature_root, symbol, OUTPUT_NAME)
    m15_path = _resolve(normalized_root, symbol, "M15.csv")
    config_path = _config_path(baseline_root)
    inputs = (feature_path, m15_path, config_path)
    before = {path: file_sha256(path) for path in inputs}
    h1 = _validate_train(pd.read_csv(feature_path), "H1 features")
    m15 = _validate_train(pd.read_csv(m15_path), "M15")
    frozen = load_baseline_config(config_path)
    candidates = list(grid) if grid is not None else generate_parameter_grid(grid_limit)
    rows: list[dict[str, Any]] = []
    baseline_metrics: dict[str, Any] | None = None
    baseline_parameters = OptimizationParameters(10, 2.0, 10, frozen.range_min_bars, frozen.range_max_bars,
        frozen.range_atr_min, frozen.range_atr_max, 50, 0.001, frozen.retest_min_bars,
        frozen.retest_max_bars, frozen.penetration_range_pct)
    for parameters in sorted(candidates):
        row, _ = _evaluate(parameters, h1, m15, symbol, frozen, transaction_cost_r + slippage_r)
        rows.append(row)
        if parameters == baseline_parameters:
            baseline_metrics = row
    if baseline_metrics is None:
        baseline_metrics, _ = _evaluate(baseline_parameters, h1, m15, symbol, frozen,
                                         transaction_cost_r + slippage_r)
    results = pd.DataFrame(rows, columns=RESULT_COLUMNS).sort_values("parameter_id").reset_index(drop=True)
    payload = results.to_csv(index=False, lineterminator="\n", float_format="%.12g").encode()
    digest = sha256(payload).hexdigest()
    output_root.mkdir(parents=True, exist_ok=True)
    (output_root / "BBW_OPTIMIZATION_RESULTS.csv").write_bytes(payload)
    report = build_report(results, baseline_metrics, digest, transaction_cost_r, slippage_r)
    (output_root / "BBW_OPTIMIZATION_REPORT.md").write_text(report, encoding="utf-8")
    if any(file_sha256(path) != old_hash for path, old_hash in before.items()):
        raise OptimizationError("an input file was modified during optimization")
    return {"combinations": len(results), "sha256": digest,
            "results": str(output_root / "BBW_OPTIMIZATION_RESULTS.csv")}
