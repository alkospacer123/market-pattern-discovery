"""Fail-closed and mutation tests for v3 perpetual Phase 4."""
from copy import deepcopy
import json
from pathlib import Path

import pandas as pd
import pytest

from TradingSystemLab.audit_perpetual_v3_phase4 import audit, research_artifact_hashes
from TradingSystemLab.robustness.perpetual_v3_phase3 import load_frozen_registry
from TradingSystemLab.walk_forward.perpetual_v3_phase4 import (
    EXPECTED_IDS, OUTPUT_ROOT, REGISTRY_PATH, SCHEDULE, STUDIES, classify,
    full_parameters, _verify_before_data,
    run,
)


def test_exact_frozen_registry_consumption():
    rows, _ = load_frozen_registry(REGISTRY_PATH)
    assert [(x["strategy"], x["timeframe"]) for x in rows] == list(STUDIES)
    assert {(x["candidate_id"], x["parameter_hash"]) for x in rows} == set(EXPECTED_IDS.values())

@pytest.mark.parametrize("field,value", [("candidate_id", "replacement"), ("parameter_hash", "0"*64)])
def test_candidate_or_parameter_mutation_rejected(tmp_path, field, value):
    payload = json.loads(REGISTRY_PATH.read_text()); payload["candidates"][0][field] = value
    path = tmp_path / "registry.json"; path.write_text(json.dumps(payload))
    with pytest.raises(RuntimeError): load_frozen_registry(path)

def test_full_parameters_include_canonical_defaults():
    rows, _ = load_frozen_registry(REGISTRY_PATH)
    t2 = full_parameters("T2", rows[0]["parameters"])
    assert (t2["adx_period"], t2["atr_period"], t2["atr_regime_window"], t2["impulse_lookback"], t2["stop_buffer_atr"]) == (14,14,20,10,.1)
    t3 = full_parameters("T3", rows[2]["parameters"])
    assert (t3["slope_lookback"], t3["adx_period"], t3["atr_period"]) == (5,14,14)

def test_exact_original_h1_schedule_and_no_shortening():
    assert len(SCHEDULE) == 4 and all(x[1] == "2023-01-01" for x in SCHEDULE)
    assert [x[3][:7] for x in SCHEDULE] == ["2024-01", "2024-04", "2024-07", "2024-10"]
    assert all(pd.Timestamp(x[4]) < pd.Timestamp("2025-01-01") for x in SCHEDULE)
    assert all(pd.Timestamp(SCHEDULE[i][4]) < pd.Timestamp(SCHEDULE[i+1][3]) for i in range(3))

def test_classification_rule_boundaries():
    base={"trades":50,"expectancy":.1}; positive=[.1]*4
    assert classify(base,.75,.70,positive,4)=="WALK_FORWARD_PASS"
    assert classify({**base,"trades":49},.75,.70,positive,4)=="WALK_FORWARD_BORDERLINE"
    assert classify({**base,"expectancy":-.01},.75,.70,positive,4)=="WALK_FORWARD_FAIL"
    assert classify(base,.25,.70,positive,4)=="WALK_FORWARD_FAIL"

def test_committed_cost_context_oos_and_forward_only_contract():
    root=json.loads((OUTPUT_ROOT/"validation_manifest.json").read_text())
    assert root["C1_only"] and root["normalized_research_tick"] == .001
    assert not root["optimization"] and not root["candidate_replacement"] and not root["true_oos_read"]
    for strategy,timeframe in STUDIES:
        target=OUTPUT_ROOT/strategy/timeframe
        trades=pd.read_csv(target/"trades.csv"); folds=pd.read_csv(target/"folds.csv")
        assert not trades.duplicated(["fold","trade_id"]).any()
        assert pd.to_datetime(trades.exit_time,utc=True).lt(pd.Timestamp("2025-01-01",tz="UTC")).all()
        assert folds.status.eq("COMPLETE").all() and folds.included_in_pass.all()
        manifest=json.loads((target/"manifest.json").read_text())
        assert manifest["cost_model"]=="C1" and manifest["normalized_tick"]==.001
        assert manifest["true_oos_status"]=="BLOCKED_NOT_READ_NOT_EXECUTED"
        if strategy=="T3": assert "four completed non-overlapping" in manifest["t3_execution_context"]

def test_independent_audit_reconciles_all_artifacts():
    result = audit()
    assert result["status"] == "V3_PERPETUAL_PHASE_4_WALK_FORWARD_AUDIT_PASSED"
    assert result["closeout_consistency"] == "PASS"


def test_two_isolated_generations_and_closeout_are_reproducible(tmp_path):
    first, second = tmp_path / "first", tmp_path / "second"
    run(output=first)
    first_hashes = research_artifact_hashes(first)
    run(output=second)
    assert first_hashes == research_artifact_hashes(second)
    audit(first)
    manifests = [json.loads((first / name).read_text()) for name in
                 ("summary/manifest.json", "validation_manifest.json")]
    assert manifests[0] == manifests[1]
    assert manifests[0]["status"] == "V3_PERPETUAL_PHASE_4_WALK_FORWARD_COMPLETE"
    assert manifests[0]["second_complete_execution_compared"] is True
    assert manifests[0]["reproducibility_note"] == manifests[1]["reproducibility_note"]
    for report in (first / "Final_Walk_Forward_Report.md",
                   first / "summary/Final_Walk_Forward_Report.md"):
        assert report.read_text().rstrip().endswith("V3_PERPETUAL_PHASE_4_WALK_FORWARD_COMPLETE")


def test_canonical_metrics_and_classifications_do_not_drift():
    expected = {
        ("T2", "M30"): (193, 1.70741299686, .31812238663, 61.3976206195, -7.4489014096, 8.2425068132, "WALK_FORWARD_BORDERLINE"),
        ("T2", "H1"): (85, 2.41850664449, .568312563729, 48.306567917, -7.37014448231, 6.55435833489, "WALK_FORWARD_BORDERLINE"),
        ("T3", "M30"): (171, 1.60064574312, .272899850925, 46.6658745082, -18.3781479418, 2.53920442124, "WALK_FORWARD_BORDERLINE"),
        ("T3", "H1"): (66, 3.29825125816, .580199228678, 38.2931490927, -2.33918741216, 16.3702783683, "WALK_FORWARD_PASS"),
    }
    for study, values in expected.items():
        metrics = json.loads((OUTPUT_ROOT / study[0] / study[1] / "metrics.json").read_text())
        aggregate = metrics["aggregate"]["C1"]
        assert aggregate["trades"] == values[0]
        assert tuple(aggregate[key] for key in
                     ("PF", "expectancy", "net_R", "max_drawdown", "recovery_factor")) == pytest.approx(values[1:6], abs=1e-9)
        assert metrics["verdict"] == values[6]
