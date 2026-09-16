"""Deterministic, TRAIN-only robustness evaluation of Candidate Baseline v1.

This is deliberately an evaluator, not an optimizer: the complete, predefined
neighbourhood is evaluated and emitted in stable order, and no scenario is
ranked or promoted.  Trading mechanics are reused from the causal BBW baseline.
"""
from __future__ import annotations

from dataclasses import asdict
from hashlib import sha256
import itertools
import json
from pathlib import Path
from typing import Any

import pandas as pd

from ..baseline import default_baseline_config_path, load_baseline_config
from ..bbw_engine import OUTPUT_NAME, file_sha256
from ..optimization.bbw_parameter_search import (
    OptimizationParameters,
    _evaluate,
    _resolve,
    _validate_train,
    calculate_metrics,
)
from .robustness_report import build_robustness_report

CANDIDATE_NAME = "CANDIDATE_CONFIG.json"
RESULTS_NAME = "ROBUSTNESS_RESULTS.csv"
REPORT_NAME = "ROBUSTNESS_REPORT.md"
COST_SCENARIOS = (("C0", 0.0), ("C0.5", 0.5), ("C1", 1.0))
NEIGHBORHOOD = {
    "ema_period": (20, 30),
    "range_min_bars": (3, 4),
    "range_max_bars": (30, 40),
    "retest_max_bars": (30, 40),
    "atr_max": (2.0, 3.0),
}
REQUIRED_PARAMETERS = frozenset(asdict(OptimizationParameters(
    10, 1.5, 5, 3, 40, 1.0, 3.0, 20, 0.0, 3, 30, 0.2
)))
EXPECTED_CANDIDATE = OptimizationParameters(
    bbw_period=10, bbw_std=1.5, squeeze_window=5,
    range_min_bars=3, range_max_bars=40, atr_min=1.0, atr_max=3.0,
    ema_period=20, ema_slope_threshold=0.0,
    retest_min_bars=3, retest_max_bars=30, penetration=0.2,
)


class RobustnessError(ValueError):
    """Raised when the robustness safety contract cannot be satisfied."""


def _candidate_path(root: Path) -> Path:
    path = root if root.is_file() else root / CANDIDATE_NAME
    if not path.is_file():
        raise RobustnessError(f"{CANDIDATE_NAME} not found at {root}")
    return path


def candidate_sha256(root: Path) -> str:
    """Hash the candidate artifact exactly as stored (not a reserialization)."""
    return file_sha256(_candidate_path(root))


def load_candidate_config(root: Path) -> OptimizationParameters:
    """Load and strictly validate the immutable Candidate v1 parameter set."""
    path = _candidate_path(root)
    raw = json.loads(path.read_text(encoding="utf-8"))
    if set(raw) != REQUIRED_PARAMETERS:
        raise RobustnessError("candidate parameter names do not match the v1 contract")
    try:
        candidate = OptimizationParameters(**raw)
    except (TypeError, ValueError) as exc:
        raise RobustnessError(f"invalid candidate configuration: {exc}") from exc
    if candidate.atr_min > candidate.atr_max or candidate.range_min_bars > candidate.range_max_bars:
        raise RobustnessError("candidate has an invalid parameter interval")
    if candidate.retest_min_bars > candidate.retest_max_bars:
        raise RobustnessError("candidate has an invalid retest interval")
    if candidate != EXPECTED_CANDIDATE:
        raise RobustnessError("candidate values do not match frozen Candidate Baseline v1")
    return candidate


def generate_parameter_neighborhood(candidate: OptimizationParameters) -> list[OptimizationParameters]:
    """Return the fixed 2^5 local design; this function performs no search."""
    rows: list[OptimizationParameters] = []
    names = tuple(NEIGHBORHOOD)
    base = asdict(candidate)
    for values in itertools.product(*(NEIGHBORHOOD[name] for name in names)):
        changed = {**base, **dict(zip(names, values, strict=True))}
        rows.append(OptimizationParameters(**changed))
    return sorted(rows)


def _parameters_json(parameters: OptimizationParameters) -> str:
    return json.dumps(asdict(parameters), sort_keys=True, separators=(",", ":"))


def _result_row(scenario_id: str, scenario_type: str, parameters: OptimizationParameters,
                metrics: dict[str, Any]) -> dict[str, Any]:
    return {
        "scenario_id": scenario_id,
        "scenario_type": scenario_type,
        "parameters": _parameters_json(parameters),
        "trades": metrics["trades"],
        "winrate": metrics["winrate"],
        "mean_R": metrics["mean_R"],
        "PF": metrics["profit_factor"],
        "total_R": metrics["total_R"],
        "max_drawdown": metrics["max_drawdown"],
        "duration": metrics["avg_duration"],
    }


def run_candidate_robustness(feature_root: Path, normalized_root: Path,
                             candidate_root: Path, output_root: Path,
                             symbol: str) -> dict[str, Any]:
    """Evaluate all declared checks while preserving and re-hashing every input."""
    if symbol != "CNYRUBF":
        raise RobustnessError("robustness currently permits only CNYRUBF")
    candidate_path = _candidate_path(candidate_root)
    feature_path = _resolve(feature_root, symbol, OUTPUT_NAME)
    m15_path = _resolve(normalized_root, symbol, "M15.csv")
    baseline_path = default_baseline_config_path()
    inputs = (candidate_path, feature_path, m15_path, baseline_path)
    input_hashes = {str(path): file_sha256(path) for path in inputs}

    candidate = load_candidate_config(candidate_path)
    frozen = load_baseline_config(baseline_path)
    # Explicit separation guard: Candidate v1 must never silently become the Baseline.
    baseline_projection = (frozen.range_min_bars, frozen.range_max_bars,
                           frozen.range_atr_max, frozen.retest_max_bars)
    candidate_projection = (candidate.range_min_bars, candidate.range_max_bars,
                            candidate.atr_max, candidate.retest_max_bars)
    if candidate_projection == baseline_projection:
        raise RobustnessError("candidate is not separate from the Frozen Baseline")

    h1 = _validate_train(pd.read_csv(feature_path), "H1 features")
    m15 = _validate_train(pd.read_csv(m15_path), "M15")
    _, candidate_trades = _evaluate(candidate, h1, m15, symbol, frozen, 0.0)
    rows: list[dict[str, Any]] = []
    for scenario_id, cost in COST_SCENARIOS:
        rows.append(_result_row(scenario_id, "cost_sensitivity", candidate,
                                calculate_metrics(candidate_trades, cost)))
    neighborhood_trades: dict[str, pd.DataFrame] = {}
    for index, parameters in enumerate(generate_parameter_neighborhood(candidate), start=1):
        scenario_id = f"N{index:02d}"
        metrics, trades = _evaluate(parameters, h1, m15, symbol, frozen, 0.0)
        rows.append(_result_row(scenario_id, "parameter_neighborhood", parameters, metrics))
        neighborhood_trades[scenario_id] = trades

    columns = ("scenario_id", "scenario_type", "parameters", "trades", "winrate",
               "mean_R", "PF", "total_R", "max_drawdown", "duration")
    results = pd.DataFrame(rows, columns=columns)
    payload = results.to_csv(index=False, lineterminator="\n", float_format="%.12g").encode()
    results_hash = sha256(payload).hexdigest()
    report = build_robustness_report(
        results, candidate_trades, candidate_path, input_hashes[str(candidate_path)],
        h1.timestamp.min(), h1.timestamp.max(), input_hashes, results_hash,
    )
    output_root.mkdir(parents=True, exist_ok=True)
    (output_root / RESULTS_NAME).write_bytes(payload)
    (output_root / REPORT_NAME).write_text(report, encoding="utf-8")
    if any(file_sha256(path) != digest for path, digest in zip(inputs, input_hashes.values(), strict=True)):
        raise RobustnessError("an input was modified during robustness evaluation")
    return {"status": report.split("Final status: **", 1)[1].split("**", 1)[0],
            "scenarios": len(results), "sha256": results_hash,
            "results": str(output_root / RESULTS_NAME), "report": str(output_root / REPORT_NAME)}
