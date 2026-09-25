"""Fail-closed independent audit of v3 perpetual Phase 2A T2 artifacts."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
from typing import Any

import pandas as pd

from .core.unified_metrics import stats
from .optimization.experiment import stable_hash

ROOT = Path("TradingSystemLab/results/perpetual_v3/optimization/T2")
PHASE1 = Path("TradingSystemLab/results/perpetual_v3/baseline/T2")
BASE_COMMIT = "a9c9815a9865a2c20fa555292de2c9924aadca96"
STRATEGY_HASH = "376df085cfda85eefccb31343aad40ed4fbb1078f1314496472a3a4ac9507774"
DATA_COMMIT = "50f1fd2178c18b7ab3bd969be82ad01f47a34745"
TIMEFRAMES = ("M30", "H1")
INSTRUMENTS = ("USDRUBF", "CNYRUBF", "GLDRUBF", "IMOEXF")
SPACE = {
    "ema_fast": [15, 20, 25, 30], "ema_trend": [40, 50, 60],
    "ema_slow": [150, 200, 250], "adx_threshold": [15, 20, 25, 30],
    "impulse_distance_atr": [0.3, 0.5, 0.7], "confirmation_window": [2, 3, 4],
    "max_initial_stop_atr": [2.0, 2.5, 3.0], "trailing_atr": [2.0, 3.0, 4.0],
}
BASELINE = {"ema_fast": 20, "ema_trend": 50, "ema_slow": 200,
            "adx_threshold": 20.0, "impulse_distance_atr": 0.5,
            "confirmation_window": 3, "max_initial_stop_atr": 3.0, "trailing_atr": 3.0}
PROTECTED = (
    "TradingSystemLab/results/perpetual_v3/baseline",
    "TradingSystemLab/results/baseline_v2", "TradingSystemLab/results/optimization_v2",
    "TradingSystemLab/results/phase3_candidate_freeze", "TradingSystemLab/results/robustness_v2",
    "TradingSystemLab/results/walk_forward_v2", "TradingSystemLab/results/true_oos_v2",
    "TradingSystemLab/results/true_oos_validation",
)
REQUIRED = {"experiment.json", "manifest.json", "parameters.csv", "results.csv",
            "plateau_report.csv", "sensitivity_report.csv", "best_regions.md", "final_report.md"}


def design() -> list[dict[str, Any]]:
    rows = [dict(BASELINE)]
    for name in sorted(SPACE):
        rows.extend({**BASELINE, name: value} for value in SPACE[name] if value != BASELINE[name])
    return sorted(rows, key=lambda row: json.dumps(row, sort_keys=True, separators=(",", ":")))


def adjacent(configs: list[dict[str, Any]], index: int) -> list[int]:
    found = []
    for other_index, other in enumerate(configs):
        differing = [name for name in SPACE if configs[index][name] != other[name]]
        if len(differing) == 1:
            values = SPACE[differing[0]]
            if abs(values.index(configs[index][differing[0]]) - values.index(other[differing[0]])) == 1:
                found.append(other_index)
    return found


def close(actual: Any, expected: Any, tolerance: float = 1e-10) -> bool:
    if pd.isna(actual) and pd.isna(expected):
        return True
    return abs(float(actual) - float(expected)) <= tolerance


def phase1_metrics(timeframe: str) -> dict[str, Any]:
    trades = pd.concat([pd.read_csv(PHASE1 / timeframe / symbol / "trades.csv")
                        for symbol in INSTRUMENTS], ignore_index=True)
    trades = trades.sort_values(["exit_time", "symbol", "trade_id"], kind="mergesort")
    values = trades.net_R.astype(float)
    summary = stats(values)
    return {"trades": summary["trades"], "PF_C1": summary["PF_R"],
            "expectancy_C1": summary["expectancy"], "net_R_C1": summary["net_R"],
            "max_DD_C1": summary["max_DD_R"], "recovery_factor_C1": summary["recovery_factor"],
            "win_rate_C1": summary["winrate"]}


def audit(root: Path = ROOT, *, check_protected: bool = True, write_report: bool = True) -> dict[str, Any]:
    root = Path(root)
    strategy = Path("TradingSystemLab/strategies/trend/T2_Trend_Pullback.py")
    assert hashlib.sha256(strategy.read_bytes()).hexdigest() == STRATEGY_HASH
    manifest = json.loads((root / "manifest.json").read_text())
    exact = {"generation": "v3_perpetual", "phase": "PHASE_2_OPTIMIZATION",
             "subphase": "PHASE_2A_T2", "strategy": "T2", "timeframes": list(TIMEFRAMES),
             "instruments": list(INSTRUMENTS), "data_commit": DATA_COMMIT,
             "development_period": ["2023-01-01", "2024-12-31"],
             "strategy_source_hash": STRATEGY_HASH, "optimization_design": "BASELINE_PLUS_ONE_FACTOR_AT_A_TIME",
             "configurations_per_study": 19, "studies": 2, "total_configuration_studies": 38,
             "C1_only": True, "normalized_research_tick": 0.001, "true_oos_start": "2025-01-01",
             "true_oos_blocked": True, "ranking": False, "candidate_selection": False,
             "robustness": False, "walk_forward": False, "true_oos_execution": False, "mtf": False,
             "status": "V3_PERPETUAL_PHASE_2A_T2_COMPLETE"}
    for key, value in exact.items():
        assert manifest.get(key) == value, key
    expected_configs = design()
    assert len(expected_configs) == len({stable_hash(row) for row in expected_configs}) == 19
    verdicts = {}
    for timeframe in TIMEFRAMES:
        study = root / timeframe
        assert {path.name for path in study.iterdir()} == REQUIRED
        experiment = json.loads((study / "experiment.json").read_text())
        study_manifest = json.loads((study / "manifest.json").read_text())
        assert experiment["strategy"] == "T2" and experiment["timeframe"] == timeframe
        assert experiment["instruments"] == list(INSTRUMENTS)
        assert experiment["parameter_space"] == SPACE and experiment["baseline"] == BASELINE
        assert experiment["development_interval"] == ["2023-01-01", "2024-12-31"]
        assert study_manifest["data_commit"] == DATA_COMMIT
        assert study_manifest["frozen_strategy_hash"] == STRATEGY_HASH
        assert study_manifest["C1_only"] is True and study_manifest["normalized_research_tick"] == .001
        assert study_manifest["true_oos_blocked"] is True
        for key in ("ranking", "candidate_selection", "robustness", "walk_forward", "true_oos_execution", "phase7_mtf_research"):
            assert study_manifest[key] is False
        parameters = pd.read_csv(study / "parameters.csv")
        results_frame = pd.read_csv(study / "results.csv")
        plateau = pd.read_csv(study / "plateau_report.csv").fillna("")
        assert len(parameters) == len(results_frame) == len(plateau) == 19
        assert int(parameters.is_baseline.sum()) == 1
        configs = parameters[list(SPACE)].to_dict("records")
        assert configs == expected_configs
        assert not parameters.configuration_id.duplicated().any()
        ids = [f"T2-{timeframe}-{stable_hash(config)[:12]}" for config in expected_configs]
        assert parameters.configuration_id.tolist() == ids
        for config, baseline_flag in zip(configs, parameters.is_baseline):
            differences = sum(config[name] != BASELINE[name] for name in SPACE)
            assert differences == (0 if baseline_flag else 1)
            assert all(config[name] in SPACE[name] for name in SPACE)
        forbidden = ("rank", "score", "winner", "recommended_configuration", "candidate")
        assert not any(any(word in column.lower() for word in forbidden) for column in results_frame.columns)
        results = results_frame.where(pd.notna(results_frame), None).to_dict("records")
        expected_plateau = []
        for index, result in enumerate(results):
            neighbors = adjacent(configs, index)
            positive_neighbors = [j for j in neighbors if results[j]["expectancy_C1"] is not None and results[j]["expectancy_C1"] > 0]
            positive = result["expectancy_C1"] is not None and result["expectancy_C1"] > 0
            tolerance = max(.01, abs(result["expectancy_C1"]) * .35) if positive else None
            stable = [j for j in positive_neighbors if abs(results[j]["expectancy_C1"] - result["expectancy_C1"]) <= tolerance]
            classification = "ROBUST_PLATEAU" if positive and len(stable) >= 2 else "LOCAL_SPIKE" if positive else "NO_EDGE"
            expected_plateau.append((";".join(ids[j] for j in neighbors), len(neighbors), len(positive_neighbors), len(stable), tolerance, classification))
        for actual, expected in zip(plateau.to_dict("records"), expected_plateau):
            assert actual["neighbor_ids"] == expected[0]
            assert actual["neighbor_count"] == expected[1] and actual["positive_neighbors"] == expected[2]
            assert actual["stable_positive_neighbors"] == expected[3]
            assert close(actual["stability_tolerance"] or None, expected[4])
            assert actual["classification"] == expected[5]
        classifications = plateau.classification.tolist()
        overall = "ROBUST_PLATEAU" if "ROBUST_PLATEAU" in classifications else "LOCAL_SPIKE" if "LOCAL_SPIKE" in classifications else "NO_EDGE"
        assert study_manifest["overall"] == overall
        baseline_index = parameters.index[parameters.is_baseline].item()
        baseline_result = results[baseline_index]
        for key, value in phase1_metrics(timeframe).items():
            assert close(baseline_result[key], value), f"baseline:{timeframe}:{key}"
        expected_sensitivity = []
        for name in sorted(SPACE):
            for value in SPACE[name]:
                sample = [result for config, result in zip(configs, results) if config[name] == value]
                values = [row["expectancy_C1"] for row in sample if row["expectancy_C1"] is not None]
                expected_sensitivity.append((name, value, len(sample), sum(x > 0 for x in values) / len(values), sum(values) / len(values)))
        sensitivity = pd.read_csv(study / "sensitivity_report.csv")
        assert len(sensitivity) == len(expected_sensitivity)
        for actual, expected in zip(sensitivity.to_dict("records"), expected_sensitivity):
            assert actual["parameter"] == expected[0] and close(actual["value"], expected[1])
            assert actual["configurations"] == expected[2] and close(actual["positive_C1_share"], expected[3])
            assert close(actual["mean_expectancy_C1"], expected[4])
        robust_ids = [ids[i] for i, value in enumerate(classifications) if value == "ROBUST_PLATEAU"]
        regions = (study / "best_regions.md").read_text()
        assert all(f"`{identifier}`" in regions for identifier in robust_ids)
        assert sum(line.startswith("- `T2-") for line in regions.splitlines()) == len(robust_ids)
        assert "No ranking or candidate selection" in (study / "final_report.md").read_text()
        verdicts[timeframe] = {"classification": overall, "robust_plateaus": len(robust_ids)}
    if check_protected:
        result = subprocess.run(["git", "diff", "--quiet", BASE_COMMIT, "--", *PROTECTED], check=False)
        assert result.returncode == 0, "PROTECTED_RESULTS_CHANGED"
    if write_report:
        lines = ["# T2 v3 Perpetual Phase 2A Independent Audit", "", "**PASS — V3_PERPETUAL_PHASE_2A_T2_COMPLETE**", "",
                 "Independently reconstructed the 19-row OAT design, parameter hashes, immediate-neighbor graph, 35% stability rule, classifications, sensitivity rows, and Phase 1 aggregate metrics.", "",
                 f"- M30: {verdicts['M30']['classification']}; {verdicts['M30']['robust_plateaus']} ROBUST_PLATEAU configurations.",
                 f"- H1: {verdicts['H1']['classification']}; {verdicts['H1']['robust_plateaus']} ROBUST_PLATEAU configurations.",
                 "- Phase 1 and protected v1/v2 result trees are unchanged.",
                 "- TRUE OOS was blocked; no ranking, candidate selection, Robustness, or walk-forward execution occurred.", ""]
        (root / "T2_Optimization_Audit_Report.md").write_text("\n".join(lines))
    return {"status": "V3_PERPETUAL_PHASE_2A_T2_COMPLETE", "audit": "PASS", "configurations": 38, **verdicts}


if __name__ == "__main__":
    print(json.dumps(audit(), sort_keys=True))
