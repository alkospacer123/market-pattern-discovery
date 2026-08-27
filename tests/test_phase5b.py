import json
from pathlib import Path
import numpy as np
import pytest
from market_pattern_discovery.discovery.phase5b import (bh_by_family, checkpoint_record,
    enumerate_univariate, missing_ranges, stable_id, validate_artifacts)

def test_enumeration_ids_order_and_exclusion():
    targets = [{"column_name":"future_range_5", "family":"VOLATILITY", "hypothesis_contrasts":["median"]}]
    rows = list(enumerate_univariate("CNY", "M1", [("atr_14", ["LE_P10", "MISSING"])], targets))
    assert [x["hypothesis_id"] for x in rows] == ["HYP-U-000000001", "HYP-U-000000002"]
    assert stable_id("interaction_search", 7) == ("HYP-I-000000007", "EFF-I-000000007")
    with pytest.raises(ValueError, match="excluded"): list(enumerate_univariate("CNY", "M1", [("trading_date", [1])], targets))

def test_checkpoint_resume_no_drift_and_missing_ranges():
    args = dict(method="univariate_screen", instrument="CNY", timeframe="M1", target_family="PATH", signatures={"x":"y"}, seed=20260401)
    a = checkpoint_record("EXP-1", "a", 1, 2, complete=True, **args)
    b = checkpoint_record("EXP-1", "b", 4, 5, complete=True, **args)
    assert missing_ranges(5, [a, b]) == [(3, 3)]
    assert missing_ranges(2, [a]) == []
    a["checkpoint_id"] = "drift"
    with pytest.raises(ValueError, match="identity drift"): missing_ranges(2, [a])

def test_bh_family_and_nan_preservation():
    rows = [{"multiplicity_family":"a", "raw_p":.01}, {"multiplicity_family":"a", "raw_p":.04},
            {"multiplicity_family":"b", "raw_p":np.nan}]
    bh_by_family(rows)
    assert [x["adjusted_q"] for x in rows[:2]] == [.02, .04]
    assert np.isnan(rows[2]["adjusted_q"])

def _artifacts(root: Path, effects: list[dict], expected=None):
    expected = len(effects) if expected is None else expected
    docs = {"search_space.json":{"expected_hypotheses":expected}, "multiplicity_families.json":{},
      "checkpoint_manifest.json":{"checkpoints":[checkpoint_record("EXP-1","all",1,expected,method="univariate_screen",instrument="CNY",timeframe="M1",target_family="PATH",signatures={},seed=20260401,complete=True)]} if expected else {"checkpoints":[]},
      "replication_results.json":{}, "shortlist.json":{"effects":[]}, "candidate_summary.json":{},
      "phase5b_summary.json":{"internal_confirmation_accessed":False,"true_oos_accessed":False,"data_2025_accessed":False}}
    root.mkdir();
    for name, value in docs.items(): (root/name).write_text(json.dumps(value))
    (root/"effect_table.jsonl").write_text("".join(json.dumps(x)+"\n" for x in effects))

def test_validator_reconciliation_partial_and_safety(tmp_path):
    effect={"hypothesis_id":"HYP-U-000000001","effect_id":"EFF-U-000000001","feature_conditions":[],"raw_p":.1,"adjusted_q":.1}
    root=tmp_path/"ok"; _artifacts(root,[effect]); assert validate_artifacts(root)["status"] == "PASS"
    root=tmp_path/"partial"; _artifacts(root,[effect],2); assert validate_artifacts(root)["status"] == "INCOMPLETE / RESUMABLE"
    root=tmp_path/"leak"; _artifacts(root,[{**effect,"profitability":1}]); assert validate_artifacts(root)["status"] == "FAIL"
    root=tmp_path/"date"; _artifacts(root,[{**effect,"feature_conditions":[{"feature":"trading_date"}]}]); assert validate_artifacts(root)["status"] == "FAIL"
