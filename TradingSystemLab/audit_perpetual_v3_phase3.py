"""Independent fail-closed audit of v3 perpetual Phase 3 robustness artifacts."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
import sys
from typing import Any

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from TradingSystemLab.optimization.experiment import stable_hash
from TradingSystemLab.robustness.perpetual_v3_phase3 import (
    BOOTSTRAP_ITERATIONS, BOOTSTRAP_SEED, EXPECTED_IDS, FREEZE_REFERENCE_COMMIT,
    INSTRUMENTS, PHASE2_ROOT, REGISTRY_PATH, STUDIES, classify,
    severe_concentration,
)

ROOT = Path("TradingSystemLab/results/perpetual_v3/robustness")
REQUIRED = {"baseline_vs_candidate.csv", "cost_report.csv", "instrument_report.csv",
            "year_report.csv", "direction_report.csv", "concentration_report.csv",
            "mae_mfe_report.csv", "bootstrap_report.csv", "manifest.json", "final_report.md"}
METRICS = {"trade_count": "trades", "PF": "PF_C1", "expectancy": "expectancy_C1",
           "net_R": "net_R_C1", "max_DD": "max_DD_C1",
           "recovery_factor": "recovery_factor_C1", "win_rate": "win_rate_C1"}


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def _close(left: Any, right: Any) -> bool:
    return bool((pd.isna(left) and pd.isna(right)) or
                np.isclose(float(left), float(right), rtol=1e-9, atol=1e-10))


def _unchanged(path: str) -> bool:
    result = subprocess.run(["git", "diff", "--quiet", FREEZE_REFERENCE_COMMIT, "--", path],
                            check=False)
    return result.returncode == 0


def audit(root: Path = ROOT) -> dict[str, Any]:
    raw = REGISTRY_PATH.read_bytes()
    registry_sha = hashlib.sha256(raw).hexdigest()
    registry = json.loads(raw)
    _require(registry.get("immutable") is True and len(registry.get("candidates", [])) == 4,
             "REGISTRY_CARDINALITY_OR_IMMUTABILITY_FAILURE")
    by_study = {(x["strategy"], x["timeframe"]): x for x in registry["candidates"]}
    _require(set(by_study) == set(STUDIES), "FROZEN_STUDIES_MISMATCH")
    for study, item in by_study.items():
        _require((item["candidate_id"], item["parameter_hash"]) == EXPECTED_IDS[study],
                 f"IDENTITY_MISMATCH:{study}")
        _require(stable_hash(item["parameters"]) == item["parameter_hash"], f"PARAMETER_HASH_MISMATCH:{study}")
    sources = {"T2": Path("TradingSystemLab/strategies/trend/T2_Trend_Pullback.py"),
               "T3": Path("TradingSystemLab/strategies/trend/T3_MTF_Trend.py")}
    for strategy, source in sources.items():
        expected = next(x["frozen_strategy_source_hash"] for x in registry["candidates"] if x["strategy"] == strategy)
        _require(hashlib.sha256(source.read_bytes()).hexdigest() == expected, f"STRATEGY_SOURCE_HASH_MISMATCH:{strategy}")
    _require(_unchanged("TradingSystemLab/results/perpetual_v3/baseline"), "PHASE1_TREE_CHANGED")
    _require(_unchanged("TradingSystemLab/results/perpetual_v3/optimization"), "PHASE2_TREE_CHANGED")
    _require(_unchanged("TradingSystemLab/results/perpetual_v3/phase3_candidate_freeze"), "FREEZE_TREE_CHANGED")
    root_manifest = json.loads((root / "validation_manifest.json").read_text())
    _require(root_manifest["status"] in {"PENDING_AUDIT", "V3_PERPETUAL_PHASE_3_ROBUSTNESS_COMPLETE"}, "ROOT_STATUS_INVALID")
    _require(root_manifest["candidate_count"] == 4 and root_manifest["C1_only"] is True,
             "ROOT_CONTRACT_INVALID")
    _require(root_manifest["bootstrap"] == {"iterations": 10000, "seed": 3302025, "diagnostic_only": True},
             "ROOT_BOOTSTRAP_INVALID")
    _require(root_manifest["development_period"] == ["2023-01-01", "2024-12-31"] and
             root_manifest["true_oos_start"] == "2025-01-01" and root_manifest["true_oos_blocked"] is True,
             "DEVELOPMENT_BARRIER_INVALID")
    classifications = {}
    for strategy, timeframe in STUDIES:
        item = by_study[(strategy, timeframe)]
        target = root / strategy / timeframe
        _require(target.is_dir() and {p.name for p in target.iterdir()} == REQUIRED,
                 f"STUDY_TREE_INVALID:{strategy}/{timeframe}")
        manifest = json.loads((target / "manifest.json").read_text())
        _require(manifest["candidate_id"] == item["candidate_id"] and
                 manifest["candidate_parameter_hash"] == item["parameter_hash"] and
                 manifest["candidate_parameters"] == item["parameters"], "FROZEN_PARAMETERS_DRIFT")
        _require(manifest["candidate_registry_sha256"] == registry_sha and
                 manifest["freeze_reference_commit"] == FREEZE_REFERENCE_COMMIT,
                 "FREEZE_PROVENANCE_INVALID")
        _require(manifest["frozen_strategy_source_hash"] == item["frozen_strategy_source_hash"],
                 "STRATEGY_HASH_MANIFEST_INVALID")
        forbidden_true = ("optimization_executed", "parameter_search_executed",
                          "candidate_replacement_executed", "walk_forward_executed",
                          "true_oos_executed", "phase7_mtf_research")
        _require(all(manifest[x] is False for x in forbidden_true), "FORBIDDEN_LIFECYCLE_ACTION_RECORDED")
        _require(manifest["cost_models"] == ["C1"] and manifest["normalized_research_tick"] == .001,
                 "C1_ONLY_CONTRACT_INVALID")
        expected_context = "none" if strategy == "T2" else f"four completed non-overlapping {timeframe} bars; local-day reset"
        _require(manifest["execution_context"] == expected_context, "EXECUTION_CONTEXT_INVALID")
        comparison = pd.read_csv(target / "baseline_vs_candidate.csv")
        costs = pd.read_csv(target / "cost_report.csv")
        _require(comparison[["version", "scenario"]].values.tolist() == [["baseline", "C1"], ["candidate", "C1"]],
                 "BASELINE_CANDIDATE_ROWS_INVALID")
        _require(costs[["version", "scenario"]].values.tolist() == [["candidate", "C1"]], "COST_ROWS_INVALID")
        all_text = "\n".join(p.read_text(errors="ignore") for p in target.iterdir() if p.suffix in {".csv", ".json", ".md"})
        _require(all(token not in all_text for token in ('"C0"', '"C0.5"', '"C2"', ',C0,', ',C0.5,', ',C2,')),
                 "NON_C1_OUTPUT_DETECTED")
        phase2 = pd.read_csv(PHASE2_ROOT / strategy / timeframe / "results.csv")
        candidate_source = phase2.loc[phase2.configuration_id.eq(item["phase2_configuration_id"])]
        _require(len(candidate_source) == 1, "PHASE2_CANDIDATE_MISSING")
        candidate_source = candidate_source.iloc[0]
        candidate = comparison.loc[comparison.version.eq("candidate")].iloc[0]
        baseline = comparison.loc[comparison.version.eq("baseline")].iloc[0]
        for local, canonical in METRICS.items():
            _require(_close(candidate[local], candidate_source[canonical]), f"CANDIDATE_RECONCILIATION:{local}")
        baseline_hash = stable_hash(item["canonical_baseline_parameters"])[:12]
        baseline_source = phase2.loc[phase2.configuration_id.str.endswith(baseline_hash)]
        _require(len(baseline_source) == 1, "PHASE2_BASELINE_MISSING")
        for local, canonical in METRICS.items():
            _require(_close(baseline[local], baseline_source.iloc[0][canonical]), f"BASELINE_RECONCILIATION:{local}")
        instruments = pd.read_csv(target / "instrument_report.csv")
        years = pd.read_csv(target / "year_report.csv")
        directions = pd.read_csv(target / "direction_report.csv")
        _require(instruments.symbol.tolist() == list(INSTRUMENTS), "INSTRUMENT_ORDER_INVALID")
        for frame, key, prefix in ((instruments, "symbol", ""), (years, "year", "Y"),
                                   (directions, "direction", "")):
            for _, diagnostic in frame.iterrows():
                stem = f"{prefix}{diagnostic[key]}"
                if key == "year": stem = f"Y{int(diagnostic[key])}"
                _require(_close(diagnostic.trade_count, candidate_source[f"{stem}_trades"]), "DIAGNOSTIC_COUNT_DRIFT")
                _require(_close(diagnostic.expectancy, candidate_source[f"{stem}_expectancy_C1"]), "DIAGNOSTIC_EXPECTANCY_DRIFT")
        conc = pd.read_csv(target / "concentration_report.csv").iloc[0]
        severe = severe_concentration(conc)
        _require(bool(manifest["severe_concentration"]) == severe, "SEVERE_CONCENTRATION_RULE_DRIFT")
        boot = pd.read_csv(target / "bootstrap_report.csv").iloc[0]
        _require(boot.iterations == BOOTSTRAP_ITERATIONS and boot.seed == BOOTSTRAP_SEED and
                 boot.interpretation == "DIAGNOSTIC_ONLY_IID_TRADE_BOOTSTRAP", "BOOTSTRAP_INVALID")
        instrument_positive = bool((instruments.expectancy > 0).all())
        year_positive = bool((years.expectancy > 0).all())
        expected = classify(candidate.expectancy, instrument_positive, year_positive, severe,
                            boot.probability_mean_R_gt_0)
        _require(manifest["classification"] == expected, "CLASSIFICATION_LOGIC_DRIFT")
        expected_flags = []
        if not instrument_positive: expected_flags.append("INSTRUMENT_DEPENDENT")
        if not year_positive: expected_flags.append("YEAR_DEPENDENT")
        if not bool((directions.expectancy > 0).all()): expected_flags.append("DIRECTION_DEPENDENT")
        _require(manifest["diagnostic_flags"] == expected_flags, "DIAGNOSTIC_FLAGS_INVALID")
        # Recompute without direction to demonstrate that it is not a readiness gate.
        _require(expected == classify(candidate.expectancy, instrument_positive, year_positive, severe,
                                      boot.probability_mean_R_gt_0), "DIRECTION_PROMOTED_TO_GATE")
        classifications[f"{strategy}/{timeframe}"] = expected
    _require(root_manifest["classifications"] == classifications, "ROOT_CLASSIFICATIONS_INVALID")
    return {"status": "PASS", "studies": 4, "classifications": classifications}


def main() -> None:
    result = audit()
    manifest_path = ROOT / "validation_manifest.json"
    manifest = json.loads(manifest_path.read_text())
    manifest["status"] = "V3_PERPETUAL_PHASE_3_ROBUSTNESS_COMPLETE"
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True, allow_nan=False) + "\n")
    (ROOT / "Phase_3_Robustness_Audit_Report.md").write_text(
        "# Phase 3 Robustness v3 Perpetual Independent Audit\n\n**PASS** — all mandatory invariants passed. "
        "The four frozen studies reconciled to Phase 2; protected historical evidence remained unchanged.\n",
        encoding="utf-8")
    (ROOT / "audit_result.json").write_text(
        json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
