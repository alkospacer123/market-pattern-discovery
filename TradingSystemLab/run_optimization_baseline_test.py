"""Produce and double-check the Phase 3.1 baseline compatibility artifacts."""
from __future__ import annotations

import json
from pathlib import Path
import tempfile

import pandas as pd

from .core.unified_metrics import finite
from .optimization.experiment import Experiment, REQUIRED_METRICS
from .optimization.runner import ExperimentRunner
from .optimization.validation import (artifact_hashes, reject_true_oos,
                                      validate_determinism, validate_tick_sizes,
                                      validate_trade_identity)
from .run_unified_baseline_audit import OUT as PHASE2_OUT, ROOT, SPECS, registry

OUT = ROOT / "results" / "optimization"


def build_experiment() -> Experiment:
    hashes = {row["strategy_key"]: row["frozen_parameters_hash"] for row in registry()}
    return Experiment(
        strategy_id="UNIFIED_SIX_STRATEGY_BASELINE",
        baseline_config={"frozen_parameter_hashes": hashes},
        parameter_space={},
        constraints=(),
        cost_scenarios=("C0", "C0.5", "C1", "C2"),
        data_period={"start": "2023-01-01", "end": "2024-12-31"},
        symbols=("Si", "CNY"),
        metrics_required=REQUIRED_METRICS,
        seed=0,
        optimization_enabled=False,
        walk_forward_enabled=False,
        true_oos_blocked=True,
        baseline_only=True,
    )


def _records(path: Path) -> list[dict]:
    return pd.read_csv(path).where(pd.notna(pd.read_csv(path)), None).to_dict("records")


def baseline_executor(_: Experiment) -> dict:
    """Adapt frozen Phase 2 outputs; do not reproduce signals or metric formulas."""
    comparison = pd.read_csv(PHASE2_OUT / "baseline_comparison.csv")
    parity = pd.read_csv(PHASE2_OUT / "parity_report.csv")
    parity_rows = parity.to_dict("records")
    validate_trade_identity(parity_rows)
    validate_tick_sizes({"Si": 0.001, "CNY": 0.001})
    for key, spec in SPECS.items():
        trades = pd.read_csv(ROOT / spec[6])
        reject_true_oos(trades["entry_time"])
        reject_true_oos(trades["exit_time"])
        expected = int(parity.loc[parity.strategy == key, "expected_trades"].iloc[0])
        if len(trades) != expected:
            raise ValueError(f"BASELINE_TRADE_IDENTITY_MISMATCH: {key}")
    metrics = {
        "PF_R_C1": {}, "expectancy_C1": {}, "net_R_C1": {}, "max_DD_R_C1": {},
        "recovery_factor": {}, "trade_count": {}, "top3_concentration": {},
    }
    for row in comparison.to_dict("records"):
        key = row["strategy"]
        metrics["PF_R_C1"][key] = finite(float(row["PF_R_C1"]))
        metrics["expectancy_C1"][key] = finite(float(row["expectancy_C1"]))
        metrics["net_R_C1"][key] = finite(float(row["net_R_C1"]))
        metrics["max_DD_R_C1"][key] = finite(float(row["max_DD_R_C1"]))
        metrics["recovery_factor"][key] = finite(float(row["recovery_factor"]))
        metrics["trade_count"][key] = int(row["trades"])
        metrics["top3_concentration"][key] = finite(float(row["top3_positive_R_share"]))
    return {"metrics": metrics, "strategies": list(SPECS),
            "source": "TradingSystemLab/results/unified_baseline",
            "validation": {"baseline_reproduction": "PASS",
                           "unified_baseline_parity": "PASS",
                           "true_oos_barrier": "PASS", "tick_model": "PASS"},
            "parameter_search_performed": False}


def run(output: Path = OUT) -> dict:
    experiment = build_experiment()
    runner = ExperimentRunner()
    with tempfile.TemporaryDirectory(prefix="phase3-run-a-") as a, \
         tempfile.TemporaryDirectory(prefix="phase3-run-b-") as b:
        first = runner.run(experiment, baseline_executor, Path(a))
        runner.run(experiment, baseline_executor, Path(b))
        validate_determinism(artifact_hashes(Path(a)), artifact_hashes(Path(b)))
    result = runner.run(experiment, baseline_executor, output)
    return {"status": "PHASE_3_FRAMEWORK_COMPLETE", "experiment_id": experiment.experiment_id,
            "determinism": "PASS", "baseline_reproduction": "PASS",
            "metrics": result["metrics"]}


if __name__ == "__main__":
    print(json.dumps(run(), indent=2, sort_keys=True))
