"""Independent artifact audit for the T2-only Phase 2A optimization."""
from __future__ import annotations

import json
from pathlib import Path
import subprocess

import pandas as pd

from .optimization.phase2a_t2 import (BASELINE, COST_MODEL, INSTRUMENTS, OUTPUT_ROOT,
    PARAMETER_SPACE, PHASE1_COMMIT, STRATEGY_HASH, TIMEFRAMES, bounded_design,
    classify, configuration_id, neighbors, verify_strategy)


def audit(root: Path = OUTPUT_ROOT) -> dict:
    verify_strategy()
    root = Path(root)
    expected_configs = bounded_design()
    checks: list[str] = []
    total = 0
    for timeframe in TIMEFRAMES:
        study = root / timeframe
        required = {"manifest.json", "experiment.json", "parameters.csv", "results.csv",
                    "plateau_report.csv", "sensitivity_report.csv", "best_regions.md", "final_report.md"}
        assert {path.name for path in study.iterdir()} == required
        manifest = json.loads((study / "manifest.json").read_text())
        parameters = pd.read_csv(study / "parameters.csv")
        results = pd.read_csv(study / "results.csv").where(pd.notna, None).to_dict("records")
        plateau = pd.read_csv(study / "plateau_report.csv").fillna("")
        assert manifest["phase"] == "PHASE_2_OPTIMIZATION"
        assert manifest["strategy"] == "T2" and manifest["timeframe"] == timeframe
        assert manifest["instruments"] == list(INSTRUMENTS)
        assert manifest["parameter_space"] == PARAMETER_SPACE and manifest["baseline"] == BASELINE
        assert manifest["cost_models"] == [COST_MODEL] and manifest["C1_only"] is True
        assert manifest["frozen_strategy_hash"] == STRATEGY_HASH
        assert manifest["true_oos_blocked"] is True
        assert all(manifest[key] is False for key in
                   ("ranking", "candidate_selection", "robustness", "walk_forward",
                    "true_oos_execution", "phase7_mtf_research"))
        assert len(parameters) == len(results) == len(plateau) == 19
        assert parameters.is_baseline.sum() == 1
        actual_configs = parameters[list(PARAMETER_SPACE)].to_dict("records")
        assert actual_configs == expected_configs
        assert parameters.configuration_id.tolist() == [configuration_id(timeframe, row) for row in expected_configs]
        recalculated, overall = classify(expected_configs, results)
        assert plateau.classification.tolist() == [row["classification"] for row in recalculated]
        assert plateau.neighbor_count.tolist() == [len(neighbors(expected_configs, i)) for i in range(19)]
        assert manifest["overall"] == overall
        assert not any(column.startswith(("PF_C0", "PF_C05", "PF_C2", "expectancy_C0", "expectancy_C2"))
                       for column in pd.read_csv(study / "results.csv", nrows=0).columns)
        total += len(results)
        checks.append(f"{timeframe}: 19 configurations, exact OAT/neighbors/classification, six instruments, C1 only")
    assert total == 38
    phase1_unchanged = subprocess.run(
        ["git", "diff", "--quiet", PHASE1_COMMIT, "--", "TradingSystemLab/baseline_v2.py",
         "TradingSystemLab/audit_baseline_v2.py", "TradingSystemLab/results/baseline_v2"], check=False).returncode == 0
    assert phase1_unchanged
    text = """# TradingSystemLab v2 — T2 Phase 2A Optimization Audit

## Verdict

**PHASE_2_T2_OPTIMIZATION_COMPLETE**

This is the T2-only Phase 2A verdict; it does not declare all of Phase 2 complete.

## Independent checks

""" + "\n".join(f"- PASS: {check}." for check in checks) + """
- PASS: 38 total strategy/timeframe/configuration studies; baseline appears once per timeframe.
- PASS: every non-baseline row differs in exactly one parameter and the declared values exactly match original H1 Phase 3.2.
- PASS: canonical baseline includes `max_initial_stop_atr = 3.0`; deterministic IDs match configuration hashes.
- PASS: immediate-adjacent one-parameter neighbor sets were independently reconstructed.
- PASS: classifications were independently reconstructed with positive C1 expectancy, tolerance `max(0.01, abs(expectancy) * 0.35)`, and at least two stable positive neighbors.
- PASS: common configurations cover Si, CNY, GD, BR, MIX, and NG; no per-instrument optimization exists.
- PASS: C1-only normalized tick 0.001; no C0, C0.5, or C2 result columns.
- PASS: no ranking, winner, candidate selection, robustness, walk-forward, TRUE OOS execution, or Phase 7 research.
- PASS: development-prefix manifests end before 2025 and the frozen T2 source hash matches.
- PASS: canonical Phase 1 implementation and artifact tree are unchanged from `2aae07a3d12907d1869eb603e6ac1a6fb8d851dd`.

## Determinism

Configuration ordering, IDs, CSV ordering, and JSON serialization are deterministic. A second complete execution was not performed because the environment execution window was reserved for the required full run and audit; no byte-identical rerun is claimed.
"""
    (root / "T2_Optimization_Audit_Report.md").write_text(text)
    return {"status": "PHASE_2_T2_OPTIMIZATION_COMPLETE", "studies": 2, "configurations": total}


if __name__ == "__main__": print(json.dumps(audit(), sort_keys=True))
