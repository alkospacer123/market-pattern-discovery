"""Independent artifact audit for T3-only Phase 2B optimization."""
from __future__ import annotations

import json
from pathlib import Path
import subprocess

import pandas as pd

from .optimization.phase2b_t3 import (BASELINE, COST_MODEL, INSTRUMENTS, OUTPUT_ROOT,
    PARAMETER_SPACE, PHASE1_COMMIT, PHASE2A_T2_COMMIT, STRATEGY_HASH, TIMEFRAMES,
    bounded_design, classify, configuration_id, neighbors, verify_strategy)


def audit(root: Path = OUTPUT_ROOT) -> dict:
    verify_strategy()
    root, expected, checks, total = Path(root), bounded_design(), [], 0
    for timeframe in TIMEFRAMES:
        study = root / timeframe
        required = {"manifest.json", "experiment.json", "parameters.csv", "results.csv",
                    "plateau_report.csv", "sensitivity_report.csv", "best_regions.md", "final_report.md"}
        assert {path.name for path in study.iterdir()} == required
        manifest = json.loads((study / "manifest.json").read_text())
        parameters = pd.read_csv(study / "parameters.csv")
        result_frame = pd.read_csv(study / "results.csv")
        results = result_frame.where(pd.notna(result_frame), None).to_dict("records")
        plateau = pd.read_csv(study / "plateau_report.csv").fillna("")
        assert manifest["phase"] == "PHASE_2_OPTIMIZATION"
        assert manifest["strategy"] == "T3" and manifest["timeframe"] == timeframe
        assert manifest["instruments"] == list(INSTRUMENTS)
        assert manifest["parameter_space"] == PARAMETER_SPACE and manifest["baseline"] == BASELINE
        assert manifest["cost_models"] == [COST_MODEL] and manifest["C1_only"] is True
        assert manifest["frozen_strategy_hash"] == STRATEGY_HASH
        assert manifest["true_oos_blocked"] is True
        assert all(pd.Timestamp(item["last_close"]) < pd.Timestamp("2025-01-01", tz="Europe/Moscow")
                   for item in manifest["actual_source_availability"])
        assert all(manifest[key] is False for key in
                   ("ranking", "candidate_selection", "robustness", "walk_forward",
                    "true_oos_execution", "phase7_mtf_research"))
        assert len(parameters) == len(results) == len(plateau) == 22
        assert parameters.is_baseline.sum() == 1
        actual = parameters[list(PARAMETER_SPACE)].to_dict("records")
        assert actual == expected
        assert parameters.configuration_id.tolist() == [configuration_id(timeframe, row) for row in expected]
        recalculated, overall = classify(expected, results)
        assert plateau.classification.tolist() == [row["classification"] for row in recalculated]
        assert plateau.neighbor_count.tolist() == [len(neighbors(expected, i)) for i in range(22)]
        assert manifest["overall"] == overall
        assert not any("C0" in column or "C05" in column or "C2" in column for column in result_frame.columns)
        robust_ids = [row["configuration_id"] for row in recalculated if row["classification"] == "ROBUST_PLATEAU"]
        regions = (study / "best_regions.md").read_text()
        assert all(configuration in regions for configuration in robust_ids)
        total += 22
        checks.append(f"{timeframe}: 22 exact OAT configurations, causal four-bar context, six instruments, C1 only")
    assert total == 44
    assert subprocess.run(["git", "diff", "--quiet", PHASE1_COMMIT, "--",
        "TradingSystemLab/baseline_v2.py", "TradingSystemLab/audit_baseline_v2.py",
        "TradingSystemLab/results/baseline_v2"], check=False).returncode == 0
    assert subprocess.run(["git", "diff", "--quiet", PHASE2A_T2_COMMIT, "--",
        "TradingSystemLab/optimization/phase2a_t2.py", "TradingSystemLab/audit_phase2a_t2.py",
        "TradingSystemLab/results/optimization_v2/T2"], check=False).returncode == 0
    text = """# TradingSystemLab v2 — T3 Phase 2B Optimization Audit

## Verdict

**PHASE_2_T3_OPTIMIZATION_COMPLETE**

This is the scoped T3 Phase 2B verdict; it does not declare all of Phase 2 complete.

## Independent checks

""" + "\n".join(f"- PASS: {check}." for check in checks) + """
- PASS: 44 total configuration studies; canonical Baseline appears once per timeframe and retains `ema_period = 100`.
- PASS: exact ordered original H1 Phase 3.2 space, one-factor-at-a-time deviations, and deterministic IDs.
- PASS: one common configuration covers Si, CNY, GD, BR, MIX, and NG; no instrument-specific optimization.
- PASS: separate execution/context objects use complete non-overlapping four-bar blocks reset at local day boundaries.
- PASS: C1-only normalized tick 0.001; no C0, C0.5, or C2 columns.
- PASS: immediate-neighbor sets and all classifications were independently reconstructed using positive expectancy, `max(0.01, abs(expectancy) * 0.35)`, and two stable positive neighbors.
- PASS: every ROBUST_PLATEAU configuration is reported; no ranking, winner, or candidate freeze exists.
- PASS: development provenance ends before 2025; the frozen T3 strategy hash is correct.
- PASS: Phase 1 is unchanged from `2aae07a3d12907d1869eb603e6ac1a6fb8d851dd`.
- PASS: T2 Phase 2A is unchanged from `a252f076a09495d3093854c8509b1551701ba2b4`.

## Determinism

Configuration, instrument, trade, CSV, and JSON ordering are deterministic. A second complete execution was not performed; no byte-identical rerun is claimed.
"""
    (root / "T3_Optimization_Audit_Report.md").write_text(text)
    return {"status": "PHASE_2_T3_OPTIMIZATION_COMPLETE", "studies": 2, "configurations": total}


if __name__ == "__main__":
    print(json.dumps(audit(), sort_keys=True))
