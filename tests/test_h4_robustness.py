"""Contract tests for the standalone, frozen H4 robustness stage."""
from __future__ import annotations

import ast
import json
from pathlib import Path

import pandas as pd
import pytest

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


def test_current_sources_equal_both_canonical_manifests():
    baseline_manifest=json.loads((h4.baseline.OUTPUT/"manifest.json").read_text())
    optimization_manifest=json.loads((h4.OPTIMIZATION/"manifest.json").read_text())
    _, verified=h4._load_verified_development(h4.APPROVED_DATA_ROOT, {
        "baseline":baseline_manifest,"optimization":optimization_manifest})
    assert verified == optimization_manifest["source_files"]
    assert verified == baseline_manifest["source_files"]


@pytest.mark.parametrize("failure", ["changed", "missing", "unexpected"])
def test_source_provenance_mismatch_fails_closed(monkeypatch, tmp_path, failure):
    source=tmp_path/"Si_H1_2023_Q1.csv"; source.write_text("current bytes")
    extra=tmp_path/"Si_H1_2023_Q2.csv"; extra.write_text("unexpected bytes")
    frame=pd.DataFrame({"close":[1.0]})
    expected=[{"instrument":"USDRUBF","alias":"Si","name":source.name,"sha256":h4._sha(source)}]
    paths=[source]
    if failure == "changed": expected[0]["sha256"]="0"*64
    elif failure == "missing": paths=[]
    else: paths.append(extra)
    monkeypatch.setattr(h4.baseline,"INSTRUMENTS",(("USDRUBF","Si"),))
    monkeypatch.setattr(h4.baseline,"load_h1_development",lambda *_: (frame if paths else None, paths))
    with pytest.raises(RuntimeError,match="^H4_ROBUSTNESS_SOURCE_HASH_MISMATCH$"):
        h4._load_verified_development(tmp_path,{"baseline":{"source_files":expected},
                                                  "optimization":{"source_files":expected}})


def test_candidate_execution_never_starts_after_provenance_failure(monkeypatch, tmp_path):
    source=tmp_path/"Si_H1_2023_Q1.csv"; source.write_text("modified")
    expected=[{"instrument":"USDRUBF","alias":"Si","name":source.name,"sha256":"0"*64}]
    provenance={"baseline":{"source_files":expected},"optimization":{"source_files":expected}}
    monkeypatch.setattr(h4,"protected_snapshot",lambda: {})
    monkeypatch.setattr(h4,"_validate_prerequisites",lambda: (provenance, []))
    monkeypatch.setattr(h4.baseline,"INSTRUMENTS",(("USDRUBF","Si"),))
    monkeypatch.setattr(h4.baseline,"load_h1_development",lambda *_: (pd.DataFrame({"close":[1.0]}),[source]))
    monkeypatch.setattr(h4.baseline,"_execute",lambda *_: pytest.fail("candidate execution began"))
    with pytest.raises(RuntimeError,match="^H4_ROBUSTNESS_SOURCE_HASH_MISMATCH$"):
        h4.run(tmp_path,tmp_path/"output")
    assert not (tmp_path/"output").exists()


def test_manifest_records_verified_current_run_sources():
    manifest=json.loads((ROOT/"manifest.json").read_text())
    assert manifest["source_hashes"] == manifest["verified_source_files"]
    assert manifest["verified_source_files"] == manifest["expected_source_files"]


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
    # Later phases may add a new subtree below a protected parent.  Verify that
    # every artifact frozen by Robustness is still byte-identical, without
    # treating the additive H4 Walk Forward output as a mutation.
    current=h4.protected_snapshot()
    for root, frozen in manifest["protected_artifact_hashes"].items():
        if isinstance(frozen, dict):
            assert {name:current[root].get(name) for name in frozen} == frozen
        else:
            assert current[root] == frozen
