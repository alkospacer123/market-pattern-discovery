from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pandas as pd
import pytest

from TradingSystemLab.multitimeframe.phase71 import STRATEGY_SHA256
from TradingSystemLab.optimization.experiment import stable_hash
from TradingSystemLab.walk_forward.m30 import (
    EXPECTED, INITIAL_TRAIN_MONTHS, STEP_MONTHS, TEST_MONTHS,
    T2WalkForwardAdapter, generate_folds, reject_true_oos,
    validate_prerequisites, verdict,
)

ROOT = Path("TradingSystemLab")


def test_exact_prerequisites_candidate_provenance_and_source_snapshot():
    baseline, optimization, robustness, registries = validate_prerequisites()
    assert [baseline["status"], optimization["status"], robustness["status"]] == [
        "PHASE_M30_BASELINE_COMPLETE", "PHASE_M30_OPTIMIZATION_COMPLETE",
        "PHASE_M30_ROBUSTNESS_COMPLETE"]
    for manifest in (baseline, optimization, robustness):
        assert manifest["development_period"] == ["2023-01-01", "2024-12-31"]
        assert manifest["true_oos_cutoff"] == "2025-01-01"
        assert manifest["true_oos_blocked"] is True
        assert manifest["source_files"] == baseline["source_files"]
    parameters = {
        "T2": {"adx_threshold": 20, "confirmation_window": 3, "ema_fast": 20,
               "ema_slow": 200, "ema_trend": 50, "impulse_distance_atr": .5,
               "max_initial_stop_atr": 2.5, "trailing_atr": 3},
        "T3": {"adx_threshold": 25, "atr_average_period": 20, "breakout_period": 20,
               "ema_period": 75, "stop_atr": 2.0, "trail_atr": 3.0},
    }
    for key in ("T2", "T3"):
        row = registries[key]
        assert (row["candidate_id"], row["optimization_configuration_id"], row["parameter_hash"]) == EXPECTED[key]
        assert row["parent_candidate_id"] == f"{key}_candidate_v1"
        assert row["parameters"] == parameters[key]
        assert stable_hash(row["parameters"]) == EXPECTED[key][2]
        assert row["strategy_hash"] == STRATEGY_SHA256[key]
        assert row["selection_locked_before_validation"] is True


def test_h1_scheduler_exact_expanding_three_folds_and_discards_partial():
    tz = "Europe/Moscow"
    assert (INITIAL_TRAIN_MONTHS, TEST_MONTHS, STEP_MONTHS) == (12, 3, 3)
    start = pd.Timestamp("2023-01-03 09:30", tz=tz)
    folds = generate_folds(start, pd.Timestamp("2025-01-01", tz=tz))
    assert [(x["fold_id"], str(x["test_start"].date()), str(x["test_end"].date())) for x in folds] == [
        ("WF01", "2024-02-01", "2024-05-01"),
        ("WF02", "2024-05-01", "2024-08-01"),
        ("WF03", "2024-08-01", "2024-11-01")]
    assert all(x["train_start"] == start and x["train_end"] == x["test_start"] for x in folds)
    assert all(x["initial_state"] == "FLAT" for x in folds)
    assert len(generate_folds(start, pd.Timestamp("2024-10-31", tz=tz))) == 2


def test_true_oos_boundaries_fail_closed():
    with pytest.raises(ValueError, match="TRUE_OOS"):
        reject_true_oos([pd.Timestamp("2025-01-01", tz="UTC")])


def test_t2_boundary_adapter_uses_history_only_for_warmup(monkeypatch):
    index = pd.date_range("2024-01-31 22:00", periods=8, freq="30min", tz="Europe/Moscow")
    candles = pd.DataFrame({"Open": range(8), "High": range(1, 9), "Low": range(8), "Close": range(8)}, index=index, dtype=float)
    adapter = T2WalkForwardAdapter(None, index[4], index[7])
    monkeypatch.setattr(T2WalkForwardAdapter.__mro__[1], "calculate_indicators",
        lambda self, f: f.assign(EMA20=1, EMA50=1, EMA200=1, ATR=1, ADX=30, ATRMean20=1))
    assert adapter.calculate_indicators(candles).index[0] == index[4]
    assert adapter.is_pullback(adapter.calculate_indicators(candles).iloc[-1], "LONG") is False


@pytest.mark.parametrize("aggregate,positive,top1,instruments,expected", [
    ({"trades": 50, "expectancy_R": .1, "PF": 1.21, "net_R": 5}, .6, .69,
     [{"trades": 20, "expectancy_R": .1}, {"trades": 19, "expectancy_R": -1}], "WALK_FORWARD_PASS"),
    ({"trades": 49, "expectancy_R": .1, "PF": 1.21, "net_R": 5}, 1, .2, [], "WALK_FORWARD_BORDERLINE"),
    ({"trades": 50, "expectancy_R": 0, "PF": 1, "net_R": 0}, 1, .2, [], "WALK_FORWARD_FAIL"),
])
def test_exact_h1_verdict_contract(aggregate, positive, top1, instruments, expected):
    assert verdict(3, aggregate, positive, top1, instruments) == expected
    assert verdict(2, aggregate, positive, top1, instruments) == "INSUFFICIENT_HISTORY"


def test_committed_output_contract_and_ledger_ownership():
    root = ROOT / "results/walk_forward/M30"
    manifest = json.loads((root / "manifest.json").read_text())
    assert manifest["status"] == "PHASE_M30_WALK_FORWARD_COMPLETE"
    assert manifest["cost_model"] == {"name": "H1_C1", "ticks_per_side": 1.0,
        "round_trip_ticks": 2.0, "additional_slippage_ticks": 0.0}
    false_flags = ("optimization", "parameter_change", "strategy_change", "filter_search",
                   "ranking", "candidate_selection", "portfolio", "true_oos_access",
                   "true_oos_used_for_training", "true_oos_used_for_selection")
    assert all(manifest[x] is False for x in false_flags)
    assert manifest["parameters_frozen"] and manifest["flat_start_each_fold"] and manifest["causal_warmup_only"]
    for key in ("T2", "T3"):
        ledger = pd.read_csv(root / key / "stitched_forward_trades.csv")
        assert not ledger.trade_id.duplicated().any()
        assert not ledger[["instrument", "entry_time"]].duplicated().any()
        schedule = {x["fold_id"]: x for x in manifest["fold_schedule"]}
        for fold, rows in ledger.groupby("fold_id"):
            entry = pd.to_datetime(rows.entry_time, utc=True)
            assert (entry >= pd.Timestamp(schedule[fold]["test_start"]).tz_convert("UTC")).all()
            assert (entry < pd.Timestamp(schedule[fold]["test_end"]).tz_convert("UTC")).all()
        assert (pd.to_datetime(ledger.exit_time, utc=True) < pd.Timestamp("2025-01-01", tz="UTC")).all()
