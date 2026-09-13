from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from TradingSystemLab.run_t3_extended_validation import (
    EXPECTED, ITERATIONS, SEED, bootstrap, sha256,
)
from TradingSystemLab.run_t3_walk_forward import (
    INITIAL_TRAIN_MONTHS, OOS_START, STEP_MONTHS, TEST_MONTHS, TICK_SIZES,
    _stats, apply_cost, assert_pre_oos, generate_folds, load_frozen,
)

ROOT = Path(__file__).parents[2]


def test_frozen_parameters_identity():
    parameters, _ = load_frozen(ROOT / "TradingSystemLab/results/T3_parameter_robustness/frozen_baseline.json")
    assert (parameters.ema_period, parameters.slope_lookback, parameters.adx_period) == (100, 5, 14)
    assert (parameters.adx_threshold, parameters.atr_period, parameters.atr_average_period) == (20, 14, 20)
    assert (parameters.breakout_period, parameters.stop_atr, parameters.trail_atr) == (20, 2, 3)


def test_sprint6_frozen_ledger_parity():
    trades = pd.read_csv(ROOT / "TradingSystemLab/results/T3_walk_forward/stitched_forward_trades_C1.csv")
    stats = _stats(trades)
    assert len(trades) == EXPECTED["trades"] == 39
    assert stats["PF"] == pytest.approx(EXPECTED["PF"], abs=1e-10)
    assert stats["expectancy"] == pytest.approx(EXPECTED["expectancy"], abs=1e-10)
    assert stats["net_R"] == pytest.approx(EXPECTED["net_R"], abs=1e-10)


def test_corrected_tick_sizes_and_cost_formula():
    assert TICK_SIZES == {"Si": .001, "CNY": .001}
    frame = pd.DataFrame({"tick_size":[.001], "initial_risk":[.02], "gross_R":[1.]})
    assert apply_cost(frame, 1).iloc[0].cost_R == .1


def test_fixed_expanding_complete_calendar_schedule():
    assert (INITIAL_TRAIN_MONTHS, TEST_MONTHS, STEP_MONTHS) == (12, 3, 3)
    start = pd.Timestamp("2020-01-03", tz="Europe/Moscow")
    end = pd.Timestamp("2022-12-15", tz="Europe/Moscow")
    folds = generate_folds(start, end)
    assert folds[0]["test_start"] == pd.Timestamp("2021-02-01", tz="Europe/Moscow")
    assert all(f["train_start"] == start and f["train_end"] == f["test_start"] for f in folds)
    assert all(f["test_end"] - pd.DateOffset(months=3) == f["test_start"] for f in folds)
    assert folds[-1]["test_end"] <= end
    assert folds[-1]["test_end"] + pd.DateOffset(months=3) > end


def test_true_oos_hard_fail():
    with pytest.raises(ValueError, match="TRUE OOS"):
        assert_pre_oos([OOS_START], "test")


def test_fold_and_trade_diagnostics_arithmetic():
    trades = pd.DataFrame({"fold_id":["WF01","WF01","WF02"], "net_R":[2.,-1.,1.]})
    assert _stats(trades)["net_R"] == 2
    assert _stats(trades[trades.fold_id != "WF01"])["expectancy"] == 1
    positive = trades.loc[trades.net_R > 0, "net_R"].sum()
    assert trades.loc[trades.fold_id == "WF01", "net_R"].clip(lower=0).sum()/positive == pytest.approx(2/3)
    assert trades.nlargest(1, "net_R").net_R.sum()/positive == pytest.approx(2/3)


def test_bootstraps_are_deterministic():
    values=np.array([-1., .5, 2.]); blocks=[values[:2],values[2:]]
    one, two = bootstrap(values, blocks), bootstrap(values, blocks)
    pd.testing.assert_frame_equal(one, two)
    assert set(one.seed) == {SEED} and set(one.iterations) == {ITERATIONS}


def test_dataset_hashing_is_deterministic(tmp_path):
    path=tmp_path/"data.csv"; path.write_text("a,b\n1,2\n",encoding="utf-8")
    assert sha256(path) == sha256(path)


def test_artifact_ordering_and_identity():
    for cost in ("C0", "C1", "C2"):
        paths=sorted((ROOT/"TradingSystemLab/results/T3_walk_forward/folds").glob(f"WF*_trades_{cost}.csv"))
        ids=[]
        for path in paths: ids.extend(pd.read_csv(path).trade_id)
        assert len(ids) == len(set(ids))
        if cost == "C0": baseline=ids
        else: assert ids == baseline


def test_no_binary_extended_outputs():
    forbidden={".png",".jpg",".jpeg",".gif",".webp",".pdf",".zip",".parquet"}
    output=ROOT/"TradingSystemLab/results/T3_extended_validation"
    assert not [p for p in output.rglob("*") if p.suffix.lower() in forbidden]


def test_causal_strategy_source_contract():
    source=(ROOT/"TradingSystemLab/strategies/trend/T3_MTF_Trend.py").read_text()
    assert ".shift(1)" in source
    loader=(ROOT/"TradingSystemLab/core/data_loader.py").read_text()
    assert "h4_from_h1" in loader
