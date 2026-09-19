"""Contract tests for the standalone, frozen H4 robustness stage."""
from __future__ import annotations

import ast
import json
from pathlib import Path

import pandas as pd

from TradingSystemLab.timeframe_robustness import h4


ROOT = Path("TradingSystemLab/results/timeframe_robustness/H4")


def test_static_methodology_and_no_other_timeframe_engine():
    tree = ast.parse(Path(h4.__file__).read_text())
    imports = [ast.unparse(node) for node in ast.walk(tree) if isinstance(node, (ast.Import, ast.ImportFrom))]
    assert h4.METHODOLOGICAL_SOURCE == "H1_PHASE_3_3"
    assert not any(token in " ".join(imports).lower() for token in ("m30", "m15", "m5", "m1"))
    assert "timeframe_validation import h4_baseline" in " ".join(imports)


def test_candidates_are_exactly_predeclared_and_not_searchable():
    assert h4.FROZEN["T2"]["configuration_id"] == "T2-H4-0008-2b0494cdd24b"
    assert h4.FROZEN["T3"]["configuration_id"] == "T3-H4-0003-9b1e60957d91"
    assert h4.FROZEN["T2"]["parameter_hash"] == "2b0494cdd24bfbfa8ce7d657d6f83d1408f07b9f565d38d093dec5b4856e3c00"
    assert h4.FROZEN["T3"]["parameter_hash"] == "9b1e60957d918a086d58a9a721faa60c5dbd66d73721b08c733be460c930215f"
    assert not any(hasattr(h4, name) for name in ("optimize", "search", "rank_candidates", "fallback_candidate"))


def test_registry_and_canonical_optimization_provenance():
    manifest=json.loads((ROOT/"manifest.json").read_text()); registry=json.loads((ROOT/"candidate_registry.json").read_text())
    assert manifest["optimization_merge_commit"] == h4.OPTIMIZATION_COMMIT
    assert manifest["candidate_selection_precedes_validation"] is True
    assert {r["candidate_id"] for r in registry} == {"T2_H4_candidate_v1", "T3_H4_candidate_v1"}
    assert all(r["selection_locked_before_validation"] and r["timeframe"] == "H4" for r in registry)
    for row in registry:
        plateau=pd.read_csv(h4.OPTIMIZATION/row["strategy"]/"plateau_report.csv")
        assert plateau.loc[plateau.configuration_id.eq(row["source_h4_optimization_configuration_id"]),"classification"].tolist()==["ROBUST_PLATEAU"]


def test_period_cost_bootstrap_and_prohibited_actions():
    manifest=json.loads((ROOT/"manifest.json").read_text())
    assert manifest["development_period"] == ["2023-01-01", "2024-12-31"]
    assert manifest["true_oos_cutoff"] == "2025-01-01" and manifest["true_oos_blocked"] is True
    assert manifest["cost_scenarios"] == ["C1"] and manifest["cost_model"] == "H1_C1"
    assert manifest["bootstrap"] == {"seed":3302025,"iterations":10000,"diagnostic_only":True}
    assert not manifest["optimization_performed"] and not manifest["parameter_search_expanded"]
    assert not manifest["candidate_ranking"] and not manifest["candidate_fallback"] and not manifest["walk_forward_executed"]


def test_all_diagnostics_and_exact_classification_rules():
    manifest=json.loads((ROOT/"manifest.json").read_text())
    for key in ("T2","T3"):
        target=ROOT/key
        for name in ("baseline_vs_candidate.csv","instrument_report.csv","year_report.csv","direction_report.csv",
                     "concentration_report.csv","bootstrap_report.csv","dependence_report.csv","mae_mfe_report.csv"):
            assert (target/name).is_file()
        instruments=pd.read_csv(target/"instrument_report.csv"); years=pd.read_csv(target/"year_report.csv")
        directions=pd.read_csv(target/"direction_report.csv"); conc=pd.read_csv(target/"concentration_report.csv").iloc[0]
        boot=pd.read_csv(target/"bootstrap_report.csv").iloc[0]
        c1=pd.read_csv(target/"baseline_vs_candidate.csv").query("version == 'candidate'").iloc[0]
        ready=(c1.expectancy>0 and conc.top_3_positive_R_share<=.5 and conc.expectancy_C1_without_top3>0 and
               (instruments.expectancy>0).all() and (years.expectancy>0).all() and boot.probability_mean_R_gt_0>.5)
        expected="ROBUST_READY" if ready else ("BORDERLINE" if c1.expectancy>0 else "REJECTED")
        assert manifest["classifications"][key] == expected
        # Direction is diagnostic only and therefore deliberately absent above.
        if (directions.expectancy<=0).any(): assert "DIRECTION_DEPENDENT" in manifest["diagnostic_flags"][key]


def test_h4_identity_causal_context_and_protected_hashes():
    manifest=json.loads((ROOT/"manifest.json").read_text())
    assert manifest["phase"]=="H4_ROBUSTNESS" and manifest["timeframe"]=="H4"
    assert "TimeframeAdapter(\"D1\").execution(h1)" in Path("TradingSystemLab/timeframe_validation/h4_baseline.py").read_text()
    assert manifest["strategy_hashes"] == h4.STRATEGY_SHA256
    assert manifest["protected_artifact_hashes"] == h4.protected_snapshot()
