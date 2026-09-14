import json
from pathlib import Path

import pandas as pd
import pytest

from TradingSystemLab.optimization.validation import reject_true_oos
from TradingSystemLab.walk_forward import phase4


def test_frozen_candidate_provenance_and_parameter_integrity():
    rows = phase4.verify_provenance(Path("TradingSystemLab/results/robustness_validation"), Path("TradingSystemLab/results/optimization"))
    assert [r["candidate_id"] for r in rows] == ["T2_candidate_v1", "T3_candidate_v1"]
    assert all(r["selection_locked_before_validation"] for r in rows)


def test_true_oos_rejection_is_hard_fail():
    with pytest.raises(ValueError, match="TRUE_OOS_BLOCKED"):
        reject_true_oos(["2025-01-01T00:00:00Z"])


def test_fold_schedule_is_causal_nonoverlapping_and_expanding():
    previous_test_end = None
    for _, train_start, train_end, test_start, test_end in phase4.SCHEDULE:
        assert train_start == "2023-01-01"
        assert pd.Timestamp(train_end) < pd.Timestamp(test_start)
        assert pd.Timestamp(test_end) < pd.Timestamp("2025-01-01")
        if previous_test_end is not None:
            assert pd.Timestamp(test_start) > pd.Timestamp(previous_test_end)
        previous_test_end = test_end


def test_schedule_uses_only_approved_development_period():
    assert phase4.SCHEDULE[0][3] == "2024-01-01"
    assert phase4.SCHEDULE[-1][4] == "2024-12-31 23:59:59"
    assert all(pd.Timestamp(row[1]) >= pd.Timestamp("2023-01-01") for row in phase4.SCHEDULE)


def test_interval_execution_has_no_future_rows_and_new_flat_state(monkeypatch):
    index = pd.date_range("2024-01-01", periods=10, freq="h", tz="UTC")
    data = {(s,"H1"):pd.DataFrame({"Open":1,"High":1,"Low":1,"Close":1},index=index) for s in ("Si","CNY")}
    calls=[]
    def fake_execute(key, config, interval):
        calls.append(interval)
        return pd.DataFrame([{"trade_id":"x","strategy_id":"T2","symbol":"Si","direction":"LONG",
            "entry_time":index[2],"exit_time":index[3],"gross_R":1.,"initial_risk_ticks":10.}])
    monkeypatch.setattr(phase4,"execute",fake_execute)
    first=phase4._run_interval("T2",{},data,"2024-01-01 01:00","2024-01-01 05:00")
    second=phase4._run_interval("T2",{},data,"2024-01-01 01:00","2024-01-01 05:00")
    assert first.equals(second) and first.entry_time.min() >= pd.Timestamp("2024-01-01 01:00",tz="UTC")
    assert calls[0] is not calls[1] and calls[0][("Si","H1")] is not calls[1][("Si","H1")]


def test_trade_identity_and_repeatable_sha256(tmp_path):
    trades=pd.DataFrame([{"fold":"WF01","trade_id":"a","symbol":"Si","entry_time":"2023-01-01T01:00Z"}])
    phase4._csv(tmp_path/"trades.csv",trades.to_dict("records"))
    assert not trades.duplicated(["fold","trade_id"]).any()
    assert phase4.artifact_sha256(tmp_path) == phase4.artifact_sha256(tmp_path)


def test_generated_manifest_forbids_optimization_and_true_oos():
    manifest=json.loads(Path("TradingSystemLab/results/walk_forward_validation/summary/manifest.json").read_text())
    assert manifest["optimization"] is False and manifest["ranking"] is False
    assert manifest["deterministic"] is True
    assert manifest["true_oos"] == {"cutoff":"2025-01-01","read":False,"status":"BLOCKED"}
