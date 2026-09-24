"""Artifact-only Phase 3 candidate freeze (never executes a strategy).

Candidate identities are declarations, not the output of a metric-driven
procedure.  Only committed Phase 2 CSV evidence is read.
"""
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
from typing import Any

PHASE2_REFERENCE_COMMIT = "9206e2f2ca9a6524ddf78ba473b9b882938aefc6"
PREDECLARED_CANDIDATES = (
    ("T2_M30_candidate_v2", "T2", "M30", "T2-M30-7c89b4a215cd"),
    ("T2_H1_candidate_v2", "T2", "H1", "T2-H1-a98459cab4f2"),
    ("T3_M30_candidate_v2", "T3", "M30", "T3-M30-0050d828c1a8"),
    ("T3_H1_candidate_v2", "T3", "H1", "T3-H1-aeeb96942cf3"),
)
STRATEGY_FILES = {
    "T2": "TradingSystemLab/strategies/trend/T2_Trend_Pullback.py",
    "T3": "TradingSystemLab/strategies/trend/T3_MTF_Trend.py",
}
STRATEGY_HASHES = {
    "T2": "376df085cfda85eefccb31343aad40ed4fbb1078f1314496472a3a4ac9507774",
    "T3": "840dd3b2cda43fa00259445cd0a22ace6d82e677f4c793028ccc8126f9ad9a8c",
}
BASELINES = {
    "T2": {"ema_fast": 20, "ema_trend": 50, "ema_slow": 200,
           "adx_threshold": 20.0, "impulse_distance_atr": 0.5,
           "confirmation_window": 3, "max_initial_stop_atr": 3.0,
           "trailing_atr": 3.0},
    "T3": {"ema_period": 100, "adx_threshold": 20.0, "breakout_period": 20,
           "atr_average_period": 20, "stop_atr": 2.0, "trail_atr": 3.0},
}
CHANGES = {
    "T2_M30_candidate_v2": ("adx_threshold", 25),
    "T2_H1_candidate_v2": ("ema_fast", 25),
    "T3_M30_candidate_v2": ("ema_period", 75),
    "T3_H1_candidate_v2": ("atr_average_period", 30),
}
REASONS = {
    "T2_M30_candidate_v2": "Predeclared plateau member selected for cross-instrument/year balance; all instruments, years, and both directions have positive expectancy. Its drawdown is larger than Baseline and it does not dominate every metric; it was not selected by maximum PF and used no validation/future data.",
    "T2_H1_candidate_v2": "Predeclared plateau member with every year and both directions positive; five instruments are positive and the sole negative is near zero. Drawdown is lower than Baseline; it was not selected by maximum PF and used no validation/future data.",
    "T3_M30_candidate_v2": "Predeclared plateau member with every instrument, year, and both directions positive and lower drawdown than Baseline; it was not selected by maximum PF and used no validation/future data.",
    "T3_H1_candidate_v2": "Predeclared plateau member with every instrument, year, and both directions positive and lower drawdown than Baseline; it was not selected by maximum PF and used no validation/future data.",
}


def stable_hash(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"),
                         ensure_ascii=False, allow_nan=False).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _value(text: str) -> int | float:
    number = float(text)
    return int(number) if number.is_integer() else number


def _one(path: Path, configuration_id: str) -> dict[str, str]:
    with path.open(newline="", encoding="utf-8") as handle:
        matches = [row for row in csv.DictReader(handle)
                   if row["configuration_id"] == configuration_id]
    if len(matches) != 1:
        raise RuntimeError(f"EXPECTED_EXACTLY_ONE_ROW:{path}:{configuration_id}")
    return matches[0]


def build_registry(project_root: Path) -> dict[str, Any]:
    """Resolve the four declarations from Phase 2 parameter rows only."""
    records = []
    for candidate_id, strategy, timeframe, configuration_id in PREDECLARED_CANDIDATES:
        study = project_root / "TradingSystemLab/results/optimization_v2" / strategy / timeframe
        row = _one(study / "parameters.csv", configuration_id)
        parameters = dict(BASELINES[strategy])
        changed_name, changed_value = CHANGES[candidate_id]
        parameters[changed_name] = changed_value
        persisted = {key: float(value) for key, value in row.items()
                     if key not in {"configuration_id", "is_baseline"}}
        if set(persisted) != set(parameters) or any(persisted[key] != parameters[key] for key in parameters):
            raise RuntimeError(f"PHASE2_PARAMETER_MISMATCH:{configuration_id}")
        source_hash = hashlib.sha256((project_root / STRATEGY_FILES[strategy]).read_bytes()).hexdigest()
        if source_hash != STRATEGY_HASHES[strategy]:
            raise RuntimeError(f"{strategy}_FROZEN_STRATEGY_HASH_MISMATCH")
        records.append({
            "candidate_id": candidate_id, "strategy": strategy, "timeframe": timeframe,
            "phase2_configuration_id": configuration_id,
            "parameters": parameters, "parameter_hash": stable_hash(parameters),
            "canonical_baseline_parameters": BASELINES[strategy],
            "canonical_baseline_parameter_hash": stable_hash(BASELINES[strategy]),
            "frozen_strategy_source_hash": source_hash,
            "phase2_classification": "ROBUST_PLATEAU",
            "selection_reason": REASONS[candidate_id],
            "selection_method": "explicit_predeclared_identifier_without_metric_ranking",
            "validation_data_used_for_selection": False,
            "selection_locked_before_validation": True,
            "robustness_executed": False, "walk_forward_executed": False,
            "true_oos_executed": False, "true_oos_blocked": True,
            "phase2_reference_commit": PHASE2_REFERENCE_COMMIT,
        })
    return {"schema_version": 1, "immutable": True, "candidates": records}


def write_registry(project_root: Path) -> Path:
    output = project_root / "TradingSystemLab/results/phase3_candidate_freeze/candidate_registry.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(build_registry(project_root), indent=2) + "\n", encoding="utf-8")
    return output


if __name__ == "__main__":
    write_registry(Path(__file__).resolve().parents[1])
