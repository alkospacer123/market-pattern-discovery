from __future__ import annotations

import hashlib
from pathlib import Path

import pandas as pd
import pytest

from TradingSystemLab.multitimeframe.phase73 import hash_tree
from TradingSystemLab.timeframe_analysis.m5_intratrade_path import run


def _inputs(root: Path):
    validation = root / "validation"
    row = {"trade_id": "x", "instrument": "USDRUBF", "direction": "LONG",
           "entry_time": "2024-01-02T10:00:00+03:00", "entry_price": 100,
           "initial_stop": 98, "initial_risk_points": 2,
           "exit_time": "2024-01-02T10:30:00+03:00", "exit_price": 102,
           "exit_reason": "TARGET", "net_R": 1.0}
    for strategy in ("T2", "T3"):
        path = validation / strategy / "trades.csv"
        path.parent.mkdir(parents=True)
        pd.DataFrame([row | {"trade_id": strategy}]).to_csv(path, index=False)
    index = pd.date_range("2024-01-02 10:00", periods=7, freq="5min", tz="Europe/Moscow")
    usd = pd.DataFrame({"Open": [100] * 7, "High": [200, 101, 102, 103, 104, 105, 999],
                        "Low": [1, 99, 98, 98, 98, 98, 1], "Close": [100, 101, 102, 102, 102, 102, 999]}, index=index)
    cny = usd.copy()
    return validation, {"USDRUBF": usd, "CNYRUBF": cny}


def test_diagnostic_is_causal_read_only_and_deterministic(tmp_path: Path) -> None:
    validation, market = _inputs(tmp_path)
    before = hash_tree(validation)
    output = tmp_path / "output"
    manifest = run(validation=validation, output=output, market_data=market)
    first = hash_tree(output)
    run(validation=validation, output=output, market_data=market)
    assert first == hash_tree(output)
    assert before == hash_tree(validation)
    assert manifest["status"] == "PHASE_M5_INTRATRADE_PATH_COMPLETE"
    assert manifest["diagnostic_only"] and manifest["deterministic"]
    assert not manifest["optimization"] and not manifest["strategy_changes"]
    assert {p.name for p in (output / "T2").iterdir()} == {
        "checkpoint_metrics.csv", "duration_bucket_report.csv", "early_failure_report.csv", "winner_loser_path.csv"}
    checkpoint = pd.read_csv(output / "T2/checkpoint_metrics.csv")
    five = checkpoint.query("dimension == 'ALL' and checkpoint_minutes == 5").iloc[0]
    # Exactly one candle is available at 10:05; later candles (including the
    # deliberately extreme final one) cannot affect this checkpoint.
    assert float(five.average_MAE_R) == pytest.approx(49.5)
    assert float(five.average_unrealized_R) == pytest.approx(0)


def test_true_oos_market_data_is_rejected_before_output(tmp_path: Path) -> None:
    validation, market = _inputs(tmp_path)
    market["USDRUBF"] = market["USDRUBF"].set_axis(
        pd.date_range("2025-01-01", periods=7, freq="5min", tz="Europe/Moscow"))
    output = tmp_path / "output"
    with pytest.raises(ValueError, match="TRUE_OOS"):
        run(validation=validation, output=output, market_data=market)
    assert not output.exists()
