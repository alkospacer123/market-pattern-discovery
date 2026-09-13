"""Regression and research-safety checks for Sprint 6.1 diagnostics."""
from __future__ import annotations

import hashlib
from pathlib import Path

import pandas as pd
import pytest

from TradingSystemLab.run_t3_walk_forward_diagnostics import ITERATIONS, SEED, bootstrap, run
from TradingSystemLab.strategies.trend.T3_MTF_Trend import T3Parameters

ROOT=Path(__file__).parents[2]
SOURCE=ROOT/"TradingSystemLab/results/T3_walk_forward"
DATA=Path("/workspace/market-pattern-data")


@pytest.fixture(scope="module")
def generated(tmp_path_factory):
    if not DATA.exists(): pytest.skip("read-only market data is unavailable")
    out=tmp_path_factory.mktemp("t3-diagnostics")
    run(DATA,out,SOURCE)
    return out


def test_original_39_trade_identities_are_unchanged(generated):
    original=pd.read_csv(SOURCE/"stitched_forward_trades_C1.csv")
    features=pd.read_csv(generated/"entry_regime_features.csv")
    distribution=pd.read_csv(generated/"trade_distribution.csv")
    assert len(original)==39
    assert features.trade_id.tolist()==original.trade_id.tolist()==distribution.trade_id.tolist()


def test_original_fold_metrics_are_reproduced(generated):
    frame=pd.read_csv(generated/"fold_decomposition.csv").set_index("fold_id")
    expected={"WF01":(13,.194498,-.576535,-7.494950),
              "WF02":(12,6.145223,1.931504,23.178045),
              "WF03":(14,1.945839,.271151,3.796117)}
    for fold,(n,pf,mean,total) in expected.items():
        assert frame.loc[fold,"trades"]==n
        assert frame.loc[fold,"PF_C1"]==pytest.approx(pf,abs=1e-6)
        assert frame.loc[fold,"expectancy_C1"]==pytest.approx(mean,abs=1e-6)
        assert frame.loc[fold,"net_R"]==pytest.approx(total,abs=1e-6)


def test_no_strategy_parameter_modification():
    assert T3Parameters()==T3Parameters(ema_period=100,slope_lookback=5,adx_period=14,
        adx_threshold=20,atr_period=14,atr_average_period=20,breakout_period=20,
        stop_atr=2,trail_atr=3)


def test_entry_features_are_causal_and_pre_oos(generated):
    frame=pd.read_csv(generated/"entry_regime_features.csv",parse_dates=["entry_time","signal_time","feature_time"])
    assert (frame.feature_time<=frame.signal_time).all() # last fully closed H4 state
    assert (frame.signal_time==frame.entry_time).all()   # closed H1 signal/entry convention
    assert (frame.entry_time.dt.year<2025).all()
    assert frame[["H4_close","EMA100","ADX14","ATR14","Donchian_upper","Donchian_lower"]].notna().all().all()
    assert (frame.initial_risk_R==1).all()


def test_leave_one_fold_out_is_direct_arithmetic(generated):
    trades=pd.read_csv(SOURCE/"stitched_forward_trades_C1.csv")
    report=pd.read_csv(generated/"leave_one_fold_out.csv").set_index("subset")
    for fold in ("WF01","WF02","WF03"):
        part=trades[trades.fold_id!=fold]
        row=report.loc[f"WITHOUT_{fold}"]
        assert row.trades==len(part)
        assert row.net_R_C1==pytest.approx(part.net_R.sum())
        assert row.expectancy_C1==pytest.approx(part.net_R.mean())


def test_trade_concentration_is_direct_arithmetic(generated):
    trades=pd.read_csv(SOURCE/"stitched_forward_trades_C1.csv")
    wins=trades.loc[trades.net_R>0,"net_R"].sort_values(ascending=False)
    row=pd.read_csv(generated/"trade_concentration.csv").iloc[0]
    for n in (1,3,5): assert row[f"top_{n}_share_positive_R"]==pytest.approx(wins.head(n).sum()/wins.sum())
    assert row.net_R_without_best_trade==pytest.approx(trades.net_R.sum()-wins.iloc[0])


def test_bootstrap_is_deterministic():
    values=pd.Series([-.5,.2,1.0]).to_numpy(); folds=[values[:1],values[1:]]
    one=bootstrap(values,folds,SEED,ITERATIONS); two=bootstrap(values,folds,SEED,ITERATIONS)
    pd.testing.assert_frame_equal(one,two)


def test_artifacts_are_deterministic_and_text_only(generated,tmp_path):
    other=tmp_path/"again"; run(DATA,other,SOURCE)
    first={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in generated.iterdir() if p.is_file()}
    second={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in other.iterdir() if p.is_file()}
    assert first==second
    allowed={".csv",".json",".md",".svg"}
    assert all(p.suffix in allowed and b"\x00" not in p.read_bytes() for p in generated.iterdir() if p.is_file())
