"""Safety and boundary contract for the frozen T3 walk-forward."""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

from TradingSystemLab.core.backtester import Backtester
from TradingSystemLab.core.data_loader import DataLoader
from TradingSystemLab.run_t3_walk_forward import (
    COSTS, OOS_START, TICK_SIZES, apply_cost, assert_artifact_pre_oos,
    assert_pre_oos, generate_folds, load_frozen,
)
from TradingSystemLab.strategies.trend.T3_MTF_Trend import T3Parameters


ROOT = Path(__file__).parents[2]
TZ = "Europe/Moscow"


def test_frozen_parameter_parity() -> None:
    parameters, raw = load_frozen(ROOT/"TradingSystemLab/results/T3_parameter_robustness/frozen_baseline.json")
    assert parameters == T3Parameters()
    assert raw["ema_slope_definition"] == "EMA[t] - EMA[t-slope_lookback]"


def test_corrected_tick_units_and_cost_identity() -> None:
    frame = pd.DataFrame({"trade_id":["x"], "tick_size":[.001],
                          "initial_risk":[.02], "gross_R":[1.0]})
    scenarios = {name:apply_cost(frame,ticks) for name,ticks in COSTS.items()}
    assert TICK_SIZES == {"Si":.001,"CNY":.001}
    assert scenarios["C1"].cost_R.iloc[0] == pytest.approx(.1)
    assert scenarios["C2"].net_R.iloc[0] == pytest.approx(.8)
    assert all(tuple(value.trade_id) == ("x",) for value in scenarios.values())


def test_fold_generation_is_expanding_nonoverlapping_and_discards_partial() -> None:
    start=pd.Timestamp("2023-01-03 10:00",tz=TZ); end=pd.Timestamp("2024-12-31",tz=TZ)
    folds=generate_folds(start,end)
    assert len(folds)==3
    assert folds[0]["test_start"]==pd.Timestamp("2024-02-01",tz=TZ)
    assert all(f["train_start"]==start and f["train_end"]==f["test_start"] for f in folds)
    assert all(f["train_months"]>=12 and f["test_end"]==f["test_start"]+pd.DateOffset(months=3) for f in folds)
    assert all(a["test_end"]<=b["test_start"] for a,b in zip(folds,folds[1:]))
    assert folds[-1]["test_end"]==pd.Timestamp("2024-11-01",tz=TZ)


def test_fold_schedule_rejects_oos() -> None:
    with pytest.raises(ValueError,match="TRUE OOS"):
        generate_folds(pd.Timestamp("2024-01-01",tz=TZ),OOS_START)


def test_loader_and_backtester_hard_fail_on_true_oos(tmp_path: Path) -> None:
    path=tmp_path/"oos.csv"
    path.write_text("Date,Time,Open,High,Low,Close\n20250101,100000,1,2,0,1\n")
    with pytest.raises(ValueError,match="TRUE OOS"):
        DataLoader().load_csv(path)
    index=pd.date_range("2025-01-01",periods=4,freq="h",tz=TZ)
    bars=pd.DataFrame({"Open":1.,"High":2.,"Low":0.,"Close":1.},index=index)
    with pytest.raises(ValueError,match="TRUE OOS"):
        Backtester().run(object(),"Si",bars,bars)


def test_report_generation_rejects_oos() -> None:
    with pytest.raises(ValueError,match="TRUE OOS"):
        assert_artifact_pre_oos(pd.DataFrame({"entry_time":["2025-01-01T00:00:00+03:00"]}),"synthetic")
    with pytest.raises(ValueError,match="TRUE OOS"):
        assert_pre_oos([OOS_START],"synthetic")


def test_h4_only_emits_completed_blocks_and_never_crosses_day() -> None:
    day1=pd.date_range("2024-01-02 10:00",periods=5,freq="h",tz=TZ)
    day2=pd.date_range("2024-01-03 10:00",periods=3,freq="h",tz=TZ)
    index=day1.append(day2)
    bars=pd.DataFrame({"Open":range(8),"High":range(1,9),"Low":range(8),"Close":range(1,9)},index=index)
    h4=DataLoader.h4_from_h1(bars)
    assert list(h4.index)==[day1[3]]
    assert h4.iloc[0].Close==4


class _BoundaryStrategy:
    name="synthetic"
    def calculate_indicators(self,h1,h4):
        low=h1.copy(); low["ATR"]=1.; return low,h4
    def regime(self,bar): return "LONG"
    def generate_signal(self,bar,regime): return "LONG" if bar.Close>=10 else None
    def calculate_stop_loss(self,direction,entry,atr): return entry-1
    def manage_position(self,direction,extreme,atr): return extreme-1
    def exit_signal(self,direction,bar,stop): return bar.Low<=stop


def _boundary_bars() -> pd.DataFrame:
    index=pd.date_range("2024-01-01 01:00",periods=8,freq="h",tz=TZ)
    # Signals in train, first test bar, and next-fold boundary. The test trade
    # exits after its entry window, proving ownership by entry interval.
    return pd.DataFrame({"Open":[10,10,5,5,10,4,10,8],"High":[10]*8,
        "Low":[10,10,5,5,10,4,10,8],"Close":[10,10,5,10,10,4,10,8]},index=index,dtype=float)


def test_flat_start_no_train_entries_and_cross_boundary_exit() -> None:
    bars=_boundary_bars(); h4=bars.iloc[[0]].copy()
    result=Backtester().run(_BoundaryStrategy(),"Si",bars,h4,
        entry_start=bars.index[3],entry_end=bars.index[5]).trades
    assert len(result)==1
    assert result.entry_time.iloc[0]==bars.index[3]
    assert result.exit_time.iloc[0]==bars.index[5]  # exit is allowed at/after test_end


def test_next_fold_is_flat_and_does_not_duplicate_prior_trade() -> None:
    bars=_boundary_bars(); h4=bars.iloc[[0]].copy(); tester=Backtester()
    first=tester.run(_BoundaryStrategy(),"Si",bars,h4,entry_start=bars.index[3],entry_end=bars.index[5]).trades
    second=tester.run(_BoundaryStrategy(),"Si",bars,h4,entry_start=bars.index[6],entry_end=bars.index[7]).trades
    assert first.entry_time.tolist()==[bars.index[3]]
    assert second.entry_time.tolist()==[bars.index[6]]
    assert set(first.entry_time).isdisjoint(second.entry_time)


def test_first_test_bar_cannot_see_future_in_backtester() -> None:
    bars=_boundary_bars(); h4=bars.iloc[[0]].copy(); strategy=_BoundaryStrategy()
    original=Backtester().run(strategy,"Si",bars,h4,entry_start=bars.index[3],entry_end=bars.index[5]).trades
    changed=bars.copy(); changed.loc[bars.index[4]:,"High"]=999
    rerun=Backtester().run(strategy,"Si",changed,h4,entry_start=bars.index[3],entry_end=bars.index[5]).trades
    assert original.entry_time.iloc[0]==rerun.entry_time.iloc[0]==bars.index[3]


def test_fold_manifest_serialization_is_deterministic() -> None:
    folds=generate_folds(pd.Timestamp("2023-01-03",tz=TZ),pd.Timestamp("2024-12-31",tz=TZ))
    serial=lambda:json.dumps([{k:(v.isoformat() if isinstance(v,pd.Timestamp) else v) for k,v in f.items()} for f in folds],sort_keys=True)
    assert serial()==serial()
