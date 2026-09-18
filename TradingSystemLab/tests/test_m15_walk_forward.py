from __future__ import annotations

import hashlib
from pathlib import Path

import pandas as pd
import pytest

from TradingSystemLab.multitimeframe.phase71 import STRATEGY_SHA256
from TradingSystemLab.walk_forward.m15 import (
    EXPECTED, T2WalkForwardAdapter, generate_folds, reject_true_oos,
    validate_prerequisites, verdict,
)


ROOT = Path("TradingSystemLab")


def test_prerequisites_and_frozen_identities_are_exact():
    _, _, _, registries = validate_prerequisites()
    for key in ("T2", "T3"):
        assert tuple(registries[key][name] for name in
                     ("candidate_id", "configuration_id", "parameter_hash")) == EXPECTED[key]


def test_frozen_t2_source_hash_is_unchanged():
    source = ROOT / "strategies/trend/T2_Trend_Pullback.py"
    assert hashlib.sha256(source.read_bytes()).hexdigest() == STRATEGY_SHA256["T2"]


def test_h1_scheduler_is_expanding_nonoverlapping_and_rejects_partial_window():
    timezone = "Europe/Moscow"
    folds = generate_folds(pd.Timestamp("2023-01-03 09:15", tz=timezone),
                           pd.Timestamp("2025-01-01", tz=timezone))
    assert [(f["fold_id"], f["test_start"].date().isoformat(), f["test_end"].date().isoformat())
            for f in folds] == [("WF01", "2024-02-01", "2024-05-01"),
                               ("WF02", "2024-05-01", "2024-08-01"),
                               ("WF03", "2024-08-01", "2024-11-01")]
    assert all(f["train_start"] == folds[0]["train_start"] and f["initial_state"] == "FLAT" for f in folds)
    assert all(a["test_end"] <= b["test_start"] for a, b in zip(folds, folds[1:]))
    partial = generate_folds(pd.Timestamp("2023-01-03 09:15", tz=timezone),
                             pd.Timestamp("2024-10-31", tz=timezone))
    assert len(partial) == 2


def test_true_oos_is_rejected():
    with pytest.raises(ValueError, match="TRUE_OOS"):
        reject_true_oos([pd.Timestamp("2025-01-01", tz="UTC")])


def test_t2_adapter_warms_before_boundary_but_starts_iteration_flat(monkeypatch):
    index = pd.date_range("2023-12-31 20:00", periods=8, freq="15min", tz="Europe/Moscow")
    candles = pd.DataFrame({"Open": range(8), "High": range(1, 9), "Low": range(8),
                            "Close": range(8)}, index=index, dtype=float)
    start, end = index[4], index[7]
    adapter = T2WalkForwardAdapter(None, start, end)
    monkeypatch.setattr(T2WalkForwardAdapter.__mro__[1], "calculate_indicators",
                        lambda self, frame: frame.assign(EMA20=1, EMA50=1, EMA200=1,
                                                        ATR=1, ADX=30, ATRMean20=1))
    calculated = adapter.calculate_indicators(candles)
    assert calculated.index[0] == start
    assert adapter.is_pullback(calculated.iloc[-1], "LONG") is False


@pytest.mark.parametrize("aggregate,expected", [
    ({"trades": 50, "expectancy_R": .1, "PF": 1.3, "net_R": 5}, "WALK_FORWARD_PASS"),
    ({"trades": 40, "expectancy_R": .1, "PF": 1.3, "net_R": 4}, "WALK_FORWARD_BORDERLINE"),
    ({"trades": 50, "expectancy_R": -.1, "PF": .9, "net_R": -5}, "WALK_FORWARD_FAIL"),
])
def test_h1_verdict_logic(aggregate, expected):
    instruments = [{"trades": 25, "expectancy_R": .1}, {"trades": 10, "expectancy_R": -.2}]
    assert verdict(3, aggregate, 2 / 3, .5, instruments) == expected
    assert verdict(2, aggregate, 1, .2, instruments) == "INSUFFICIENT_HISTORY"
