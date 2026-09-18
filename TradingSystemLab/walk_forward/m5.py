"""Frozen M5 expanding-window validation for the two approved hypotheses.

This phase re-slices the already executed, cost-adjusted T2/T3 M5 ledgers.  It
does not fit anything in a train window: train rows exist only to quantify
candidate decay.  Entry eligibility is evaluated from causal, close-labelled
M5 features and every test window starts as an independent reporting slice.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import shutil
from typing import Any, Mapping

import pandas as pd

from ..timeframe_analysis.m5_entry_quality import DATA, _discover, _entry_rows, _load_bars
from ..timeframe_analysis.m5_overextension_session_candidate import (
    CANDIDATES, DEVELOPMENT_PERIOD, OPTIMIZATION, VALIDATION, _canonical_hash,
    _metrics, _session_mask, _source_hashes,
)
from ..timeframe_diagnostics.m5_full import _prepare, _write_csv

OUTPUT = Path("TradingSystemLab/results/walk_forward/M5")
STATUS = "PHASE_M5_WALK_FORWARD_COMPLETE"
TRUE_OOS_BOUNDARY = "2025-01-01"
FOLDS = (
    ("WF01", "2023-01-01", "2023-07-01", "2023-07-01", "2024-01-01"),
    ("WF02", "2023-01-01", "2024-01-01", "2024-01-01", "2024-07-01"),
    ("WF03", "2023-01-01", "2024-07-01", "2024-07-01", "2025-01-01"),
)
VARIANTS = {
    "baseline": "M5_BASELINE",
    "session_candidate": "M5_SESSION_CANDIDATE",
    "session_ema50_normal_candidate": "M5_SESSION_EMA50_NORMAL",
}
METRICS = ("trades", "PF", "expectancy_R", "net_R", "max_drawdown_R",
           "recovery_factor", "win_rate", "average_holding_time", "losing_streak",
           "top_1_positive_R_concentration", "top_5_positive_R_concentration")


def validate_fold_schedule() -> None:
    """Validate the preregistered expanding folds and the locked boundary."""
    previous_train_end = None
    boundary = pd.Timestamp(TRUE_OOS_BOUNDARY, tz="UTC")
    for name, train_start, train_end, test_start, test_end in FOLDS:
        values = [pd.Timestamp(value, tz="UTC") for value in
                  (train_start, train_end, test_start, test_end)]
        if not (name.startswith("WF") and values[0] < values[1] == values[2] < values[3]):
            raise RuntimeError("INVALID_OR_NONCAUSAL_M5_FOLD")
        if values[0] != pd.Timestamp("2023-01-01", tz="UTC") or values[3] > boundary:
            raise RuntimeError("M5_FOLD_OUTSIDE_DEVELOPMENT")
        if previous_train_end is not None and values[1] <= previous_train_end:
            raise RuntimeError("M5_TRAIN_WINDOW_NOT_EXPANDING")
        previous_train_end = values[1]


def reject_true_oos(frame: pd.DataFrame) -> None:
    """Fail closed when a candle or completed trade reaches calendar 2025."""
    boundary = pd.Timestamp(TRUE_OOS_BOUNDARY, tz="UTC")
    if isinstance(frame.index, pd.DatetimeIndex) and (frame.index >= boundary).any():
        raise ValueError("TRUE_OOS_MARKET_DATA_REJECTED")
    for column in ("entry_time", "exit_time"):
        if column in frame and (pd.to_datetime(frame[column], utc=True) >= boundary).any():
            raise ValueError("TRUE_OOS_TRADE_REJECTED")


def _select(frame: pd.DataFrame, variant: str) -> pd.DataFrame:
    mask = pd.Series(True, index=frame.index)
    if variant != "baseline":
        mask &= _session_mask(frame)
    if variant == "session_ema50_normal_candidate":
        mask &= frame.location_ema50.eq("normal")
    return frame.loc[mask].sort_values(
        ["exit_time", "strategy", "instrument", "trade_id"], kind="mergesort").reset_index(drop=True)


def _period(frame: pd.DataFrame, start: str, end: str) -> pd.DataFrame:
    stamp = pd.to_datetime(frame.entry_time, utc=True)
    selected = frame.loc[(stamp >= pd.Timestamp(start, tz="UTC")) &
                         (stamp < pd.Timestamp(end, tz="UTC"))].copy()
    reject_true_oos(selected)
    return selected


def _metric_rows(frame: pd.DataFrame, split: str) -> list[dict[str, Any]]:
    rows = [{"split": split, "dimension": "portfolio", "category": "COMBINED", **_metrics(frame)}]
    for strategy in ("T2", "T3"):
        rows.append({"split": split, "dimension": "strategy", "category": strategy,
                     **_metrics(frame.loc[frame.strategy.eq(strategy)])})
    for instrument in ("USDRUBF", "CNYRUBF"):
        rows.append({"split": split, "dimension": "instrument", "category": instrument,
                     **_metrics(frame.loc[frame.instrument.eq(instrument)])})
    for direction in ("LONG", "SHORT"):
        rows.append({"split": split, "dimension": "direction", "category": direction,
                     **_metrics(frame.loc[frame.direction.eq(direction)])})
    return rows


def _drawdown_diagnostics(frame: pd.DataFrame) -> dict[str, Any]:
    if frame.empty:
        return {"longest_recovery_trades": 0, "longest_recovery_minutes": 0.0,
                "recovery_status": "NO_TRADES"}
    equity = frame.net_R.astype(float).cumsum()
    drawdown = equity - equity.cummax().clip(lower=0)
    longest_trades, longest_minutes, unrecovered = 0, 0.0, False
    start: int | None = None
    for position, value in enumerate(drawdown):
        if value < 0 and start is None:
            start = position
        if value >= 0 and start is not None:
            longest_trades = max(longest_trades, position - start + 1)
            duration = (frame.exit_time.iloc[position] - frame.exit_time.iloc[start]).total_seconds() / 60
            longest_minutes = max(longest_minutes, float(duration))
            start = None
    if start is not None:
        unrecovered = True
        longest_trades = max(longest_trades, len(frame) - start)
        duration = (frame.exit_time.iloc[-1] - frame.exit_time.iloc[start]).total_seconds() / 60
        longest_minutes = max(longest_minutes, float(duration))
    return {"longest_recovery_trades": longest_trades,
            "longest_recovery_minutes": longest_minutes,
            "recovery_status": "UNRECOVERED" if unrecovered else "RECOVERED"}


def _run_variant(name: str, combined: pd.DataFrame, target: Path) -> list[dict[str, Any]]:
    selected = _select(combined, name)
    development = _metrics(selected)
    summary: list[dict[str, Any]] = []
    for fold, train_start, train_end, test_start, test_end in FOLDS:
        train, test = _period(selected, train_start, train_end), _period(selected, test_start, test_end)
        fold_dir = target / fold
        fold_dir.mkdir(parents=True)
        rows = _metric_rows(train, "train") + _metric_rows(test, "test")
        _write_csv(fold_dir / "metrics.csv", rows, ["split", "dimension", "category", *METRICS])
        _write_csv(fold_dir / "test_trades.csv", test, list(test.columns))
        train_metrics, test_metrics = _metrics(train), _metrics(test)
        diagnostics = _drawdown_diagnostics(test)
        decay = {"fold": fold, "development_expectancy_R": development["expectancy_R"],
                 "train_expectancy_R": train_metrics["expectancy_R"],
                 "walk_forward_expectancy_R": test_metrics["expectancy_R"],
                 "expectancy_decay_from_development_R": (
                     test_metrics["expectancy_R"] - development["expectancy_R"]
                     if None not in (test_metrics["expectancy_R"], development["expectancy_R"]) else None)}
        _write_csv(fold_dir / "decay.csv", [decay], list(decay))
        _write_csv(fold_dir / "drawdown.csv", [{"fold": fold, **test_metrics, **diagnostics}],
                   ["fold", *METRICS, *diagnostics])
        summary.append({"fold": fold, "train_start": train_start, "train_end_inclusive":
                        str(pd.Timestamp(train_end) - pd.Timedelta(days=1)).split(" ")[0],
                        "test_start": test_start, "test_end_inclusive":
                        str(pd.Timestamp(test_end) - pd.Timedelta(days=1)).split(" ")[0],
                        **test_metrics, **diagnostics})
    _write_csv(target / "summary.csv", summary,
               ["fold", "train_start", "train_end_inclusive", "test_start", "test_end_inclusive",
                *METRICS, "longest_recovery_trades", "longest_recovery_minutes", "recovery_status"])
    return summary


def _report(summaries: Mapping[str, list[dict[str, Any]]], frames: Mapping[str, pd.DataFrame]) -> str:
    lines = ["# M5 Walk-Forward Validation", "", "This is sequential validation of frozen hypotheses, not optimization or ranking.", "",
             "| Candidate | Positive folds | Negative folds | Average expectancy R | Median expectancy R | Development expectancy R | Walk-forward expectancy R |",
             "|---|---:|---:|---:|---:|---:|---:|"]
    for name in VARIANTS:
        rows = summaries[name]
        expectations = [row["expectancy_R"] for row in rows if row["expectancy_R"] is not None]
        tests = pd.concat([_period(frames[name], a, b) for _, _, _, a, b in FOLDS], ignore_index=True)
        development, walk = _metrics(frames[name]), _metrics(tests)
        positive, negative = sum(row["net_R"] > 0 for row in rows), sum(row["net_R"] < 0 for row in rows)
        average = sum(expectations) / len(expectations) if expectations else None
        median = float(pd.Series(expectations).median()) if expectations else None
        lines.append(f"| {VARIANTS[name]} | {positive} | {negative} | {average} | {median} | {development['expectancy_R']} | {walk['expectancy_R']} |")
    lines += ["", "## Diagnostics", "",
              "Per-fold files report top-1/top-5 positive-R concentration, maximum drawdown, recovery factor, and the longest recovery period. These expose dependence on isolated trades and unrecovered folds.", "",
              "All results retain the baseline cost-adjusted T2/T3 outcomes. Calendar 2025 TRUE OOS was rejected before output generation.", "",
              STATUS, ""]
    return "\n".join(lines)


def run(validation: Path = VALIDATION, optimization: Path = OPTIMIZATION, data: Path = DATA,
        output: Path = OUTPUT, market_data: Mapping[str, Any] | None = None) -> dict[str, Any]:
    validate_fold_schedule()
    validation, optimization, data, output = map(Path, (validation, optimization, data, output))
    registries = {}
    for key, identity in CANDIDATES.items():
        registries[key] = json.loads((optimization / key / "candidate_registry.json").read_text(encoding="utf-8"))
        if registries[key].get("candidate_id") != identity:
            raise ValueError(f"CANDIDATE_IDENTITY_MISMATCH:{key}")
    supplied = market_data if market_data is not None else _discover(data)
    bars, market_paths = {}, []
    for instrument in ("USDRUBF", "CNYRUBF"):
        bars[instrument], paths = _load_bars(supplied[instrument])
        reject_true_oos(bars[instrument])
        market_paths += paths
    before = _source_hashes(validation, optimization, market_paths)
    validation_manifest = validation / "manifest.json"
    before[str(validation_manifest)] = hashlib.sha256(validation_manifest.read_bytes()).hexdigest()
    prepared = {key: _prepare(validation / key / "trades.csv") for key in CANDIDATES}
    for frame in prepared.values():
        reject_true_oos(frame)
    enriched = {key: _entry_rows(frame, bars).assign(strategy=key) for key, frame in prepared.items()}
    combined = pd.concat(enriched.values(), ignore_index=True).sort_values(
        ["exit_time", "strategy", "instrument", "trade_id"], kind="mergesort").reset_index(drop=True)
    variants = {name: _select(combined, name) for name in VARIANTS}
    if output.exists():
        shutil.rmtree(output)
    output.mkdir(parents=True)
    summaries = {name: _run_variant(name, combined, output / name) for name in VARIANTS}
    candidate_definitions = {
        "M5_BASELINE": {"rules": "existing cost-adjusted T2/T3 strategy logic unchanged"},
        "M5_SESSION_CANDIDATE": {"weekdays": "Monday-Friday", "entry_start_inclusive": "10:00", "entry_end_exclusive": "17:00"},
        "M5_SESSION_EMA50_NORMAL": {"weekdays": "Monday-Friday", "entry_start_inclusive": "10:00", "entry_end_exclusive": "17:00", "ema50_distance_classification": "normal"},
    }
    fold_schedule = [{"fold": fold, "train": {"start": a, "end_inclusive": str(pd.Timestamp(b) - pd.Timedelta(days=1)).split(" ")[0]},
                      "test": {"start": c, "end_inclusive": str(pd.Timestamp(d) - pd.Timedelta(days=1)).split(" ")[0]}}
                     for fold, a, b, c, d in FOLDS]
    source_hashes = before
    manifest = {"phase": "M5_WALK_FORWARD", "status": STATUS,
                "candidate_identities": candidate_definitions, "underlying_candidate_ids": CANDIDATES,
                "fold_schedule": fold_schedule, "source_hashes": source_hashes,
                "development_period": DEVELOPMENT_PERIOD, "true_oos_boundary": TRUE_OOS_BOUNDARY,
                "deterministic": True, "optimization": False, "ranking": False,
                "parameter_change": False, "strategy_change": False, "true_oos_access": False,
                "cost_model": json.loads((validation / "manifest.json").read_text()).get("cost_model"),
                "execution_hash": _canonical_hash({"sources": source_hashes, "candidates": candidate_definitions,
                                                    "folds": fold_schedule})}
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (output / "combined_report.md").write_text(_report(summaries, variants), encoding="utf-8")
    after = _source_hashes(validation, optimization, market_paths)
    after[str(validation_manifest)] = hashlib.sha256(validation_manifest.read_bytes()).hexdigest()
    if before != after:
        raise RuntimeError("SOURCE_ARTIFACTS_MODIFIED")
    return manifest
