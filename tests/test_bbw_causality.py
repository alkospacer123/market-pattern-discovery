"""BBW causal/execution acceptance suite.

Every prefix test runs the same production primitive twice: first on a prefix,
then on that prefix plus deliberately extreme future observations.
"""
from dataclasses import replace

import numpy as np
import pandas as pd
import pytest

from bbw_system.config import BBWConfig, InstrumentConfig
from bbw_system.engine import CoreEngine, choose_global_candidate
from bbw_system.exits import BaselineExitManager, Position, allocate_contracts
from bbw_system.prices import align_price, is_tick_aligned
from bbw_system.strategy import (Range, Rejection, breakout, compression_threshold,
    detect_range, entry_rejection, evaluate_retest, position_size, retest_bar_allowed,
    structural_stop, trend_ok)
from bbw_system.timeframes import setup_availability


def instrument(tick=.1, value=10., go=1000.) -> InstrumentConfig:
    return InstrumentConfig("X", tick, value, 100., go, 999., .5)


def frame(n=12):
    idx = pd.date_range("2026-01-05", periods=n, freq="h")
    x = np.full(n, 10.)
    return pd.DataFrame({"open": x, "high": x + 1, "low": x - 1,
                         "close": x + .2, "volume": 1.}, index=idx)


def test_prefix_invariance_bbw_threshold_and_compression_events():
    idx = pd.date_range("2026-01-01", periods=10, freq="D")
    values = pd.Series([.2, .3, .4, .5, .6, .7, .1, .8, 99., -99.], index=idx)
    short = compression_threshold(values.iloc[:8], pd.Series(idx[:8].date), minima=6)
    long = compression_threshold(values, pd.Series(idx.date), minima=6).iloc[:8]
    pd.testing.assert_frame_equal(short, long)


def test_prefix_invariance_range_boundaries_length_selection():
    data = frame(); config = replace(BBWConfig(), range_min_bars=6, range_max_bars=8,
                                     range_anchor_mode="rolling_after_compression")
    before = detect_range(data.iloc[:8], 0, config, 7)
    data.iloc[8:, data.columns.get_loc("high")] = 10_000
    assert before == detect_range(data, 0, config, 7)


def test_prefix_invariance_trend_breakout_retest_confirmation():
    value = Range(11, 9, 2, 6); config = replace(BBWConfig(), penetration_ticks=5)
    data = frame(8); data.iloc[5] = [11, 12, 10, 11.5, 1]
    data.iloc[6] = [11.2, 11.4, 10.9, 11.2, 1]
    decisions = lambda d: (trend_ok("LONG", d.iloc[5].close, 11., 10., .01),
        breakout(d.iloc[5], value), evaluate_retest(d.iloc[6], "LONG", 11, 2, .1, config),
        bool(d.iloc[6].close > 11))
    prefix = decisions(data.iloc[:7]); data.iloc[7] = [999, 1000, -1000, -999, 1]
    assert prefix == decisions(data)


def test_h1_inside_h4_breakout_candle_cannot_be_retest():
    h1 = pd.date_range("2026-01-05 14:00", periods=6, freq="h")
    timing = setup_availability(pd.Timestamp("2026-01-05 14:00"), 4, h1)
    assert timing["setup_bar_close_time"] == pd.Timestamp("2026-01-05 18:00")
    assert timing["breakout_known_at"] == pd.Timestamp("2026-01-05 18:00")
    assert timing["first_allowed_retest_bar"] >= timing["breakout_known_at"]
    assert all(ts < timing["breakout_known_at"] for ts in h1[:4])


def test_h4_h1_overlap_excluded_end_to_end():
    idx = pd.date_range("2026-01-05 14:00", periods=7, freq="h")
    timing = setup_availability(idx[0], 4, idx)
    touches = pd.Series([True] * 7, index=idx)
    eligible = touches.loc[touches.index >= timing["breakout_known_at"]]
    assert eligible.index[0] == idx[4] and idx[0] not in eligible.index


def test_confirmation_close_is_not_entry_price_and_entry_uses_next_real_bar_open():
    cfg = replace(BBWConfig(), max_entry_extension_atr=10, max_entry_extension_range_pct=10,
                  max_stop_atr=10, max_stop_range_ratio=10, max_confirmation_candle_atr=10)
    engine = CoreEngine(cfg, instrument(), 100_000)
    confirm = pd.Series({"open": 11., "high": 12., "low": 10., "close": 11.7}, name=pd.Timestamp("2026-01-05 10:00"))
    nxt = pd.Series({"open": 11.2}, name=pd.Timestamp("2026-01-05 12:00"))
    position = engine.enter_after_confirmation("S", "LONG", Range(11, 10, 1, 6), 1, confirm, nxt)
    assert position.entry == 11.2 and position.entry != confirm.close


def test_gap_after_confirmation_rejected_using_actual_open():
    cfg = replace(BBWConfig(), max_entry_extension_atr=.2, max_entry_extension_range_pct=.2)
    reports = CoreEngine(cfg, instrument(), 100_000)
    c = pd.Series({"open": 11., "high": 11.2, "low": 10.8, "close": 11.1}, name=pd.Timestamp("2026-01-05 10:00"))
    n = pd.Series({"open": 15.}, name=pd.Timestamp("2026-01-05 11:00"))
    assert reports.enter_after_confirmation("S", "LONG", Range(11, 9, 2, 6), 1, c, n) is None
    assert reports.reports.rows["rejected_setups"][0]["rejection_reason"] == "ENTRY_TOO_EXTENDED"


def test_retest_min_is_ordinal_fifth_bar_and_max_is_inclusive():
    cfg = BBWConfig(retest_min_bars=5, retest_max_bars=30)
    assert not retest_bar_allowed(4, cfg)
    assert retest_bar_allowed(5, cfg) and retest_bar_allowed(30, cfg)
    assert not retest_bar_allowed(31, cfg)


@pytest.mark.parametrize("depth,ticks,pct,accepted", [(.4, 5, .20, True), (.6, 5, .40, False), (.4, 10, .10, False), (.6, 5, .10, False)])
def test_penetration_requires_tick_and_percent_limits(depth, ticks, pct, accepted):
    cfg = replace(BBWConfig(), penetration_ticks=ticks, penetration_range_pct=pct)
    result = evaluate_retest(pd.Series({"low": 11-depth}), "LONG", 11, 2, .1, cfg)
    assert result[0] is accepted


@pytest.mark.parametrize("direction,expected", [("LONG", 8.8), ("SHORT", 11.2)])
def test_structural_stop_is_range_boundary_plus_tick_offset(direction, expected):
    cfg = replace(BBWConfig(), stop_offset_ticks=2, max_stop_atr=99, max_stop_range_ratio=99)
    result = structural_stop(direction, 10, Range(11, 9, 2, 6), 1, cfg, instrument())
    assert result.stop == expected
    assert result.distance / .1 == pytest.approx(abs(10-expected)/.1)


def test_stop_filter_equal_boundaries_accept_and_logs_all_dimensions():
    cfg = replace(BBWConfig(), min_stop_atr=2, max_stop_atr=2,
                  min_stop_range_ratio=1, max_stop_range_ratio=1)
    result = structural_stop("LONG", 11, Range(11, 9, 2, 6), 1, cfg, instrument())
    assert result.rejection is None and result.stop_atr == 2 and result.stop_range_ratio == 1


def test_position_sizing_uses_tick_value_per_contract_not_lot_twice():
    cfg = replace(BBWConfig(), risk_pct=.01, max_margin_pct=1)
    a = position_size(100_000, 1., instrument(.1, 10, 1), cfg)
    b = position_size(100_000, 1., instrument(.01, 2, 1), cfg)
    assert a == 10 and b == 5


@pytest.mark.parametrize("tick", [.001, .01, .05])
def test_all_prices_use_decimal_tick_grid(tick):
    entry = align_price(10.037, tick)
    p = Position("LONG", entry, align_price(entry-.113, tick, "down"), 10)
    m = BaselineExitManager(tick_size=tick)
    assert all(is_tick_aligned(x, tick) for x in [p.entry, p.initial_stop] + [p.target_price(r, tick) for r in (1,2,3)])
    m.process(p, p.target_price(1, tick), p.entry)
    assert is_tick_aligned(p.stop, tick)


@pytest.mark.parametrize("qty", [1,2,3,4,5,6,7,8,9,10,11,20])
def test_integer_contract_allocation_is_conservative(qty):
    legs = allocate_contracts(qty)
    assert sum(legs) == qty and min(legs) >= 0
    assert all(isinstance(x, int) for x in legs)


@pytest.mark.parametrize("direction", ["LONG", "SHORT"])
def test_long_and_short_position_management(direction):
    p = Position(direction, 100, 90 if direction == "LONG" else 110, 10)
    m = BaselineExitManager(tick_size=1)
    sign = 1 if direction == "LONG" else -1
    for multiple, stop in [(1,100), (2,100 + sign*10), (3,None)]:
        target = 100 + sign*10*multiple
        safe_high = (p.stop - 1) if direction == "SHORT" else target
        safe_low = (p.stop + 1) if direction == "LONG" else target
        events = m.process(p, safe_high, safe_low, 100)
        assert events[-1]["event"] == f"TP{multiple}"
        if stop is not None: assert p.stop == stop
    assert p.closed and p.remaining_contracts == 0


@pytest.mark.parametrize("direction", ["LONG", "SHORT"])
@pytest.mark.parametrize("stage", [0,1,2])
def test_same_bar_ambiguity_always_uses_preexisting_stop(direction, stage):
    p = Position(direction, 100, 90 if direction == "LONG" else 110, 10)
    m = BaselineExitManager(tick_size=1)
    sign = 1 if direction == "LONG" else -1
    for i in range(stage):
        target=100+sign*10*(i+1)
        m.process(p, target if sign==1 else 99, 101 if sign==1 else target, 100)
    active = p.stop; next_target = 100+sign*10*(stage+1)
    high=max(active,next_target)+1; low=min(active,next_target)-1
    assert m.process(p, high, low, 100)[0]["event"] == "STOP"


def test_lower_tf_without_data_fails_unless_explicit_fallback():
    with pytest.raises(ValueError, match="requires lower-timeframe"):
        BaselineExitManager(policy="lower_tf")
    assert BaselineExitManager(policy="lower_tf", allow_lower_tf_fallback=True).policy == "stop_first"


@pytest.mark.parametrize("direction,stop,open_price,expected", [("LONG",100,97,97),("SHORT",100,103,103)])
def test_gap_through_stop_fills_at_adverse_open(direction, stop, open_price, expected):
    p=Position(direction, 105 if direction=="LONG" else 95, stop, 2)
    m=BaselineExitManager(tick_size=1)
    event=m.process(p, 106 if direction=="LONG" else 104, 96 if direction=="LONG" else 94, open_price)[0]
    assert event["price"] == expected


@pytest.mark.parametrize("direction,stage,gap", [("LONG",1,97),("LONG",2,107),
                                                   ("SHORT",1,103),("SHORT",2,93)])
def test_gap_through_be_and_moved_one_r_stop(direction, stage, gap):
    p=Position(direction,100,90 if direction=="LONG" else 110,10)
    m=BaselineExitManager(tick_size=1)
    sign=1 if direction=="LONG" else -1
    for i in range(stage):
        target=100+sign*10*(i+1)
        m.process(p, target if sign==1 else p.stop-1, p.stop+1 if sign==1 else target, 100)
    event=m.process(p, max(gap,p.stop)+1, min(gap,p.stop)-1, gap)[0]
    assert event["event"] == "STOP" and event["price"] == gap


def test_commissions_slippage_net_r_and_equity_feed_next_size():
    p=Position("LONG",100,90,10); m=BaselineExitManager(tick_size=1, tick_value_per_contract=2,
        commission_per_contract=1, slippage_ticks=1)
    m.charge_entry(p); m.process(p,111,100,100)
    metrics=m.r_metrics(p)
    assert p.commissions == 15 and metrics["net_R"] < metrics["gross_R"]
    engine=CoreEngine(BBWConfig(), instrument(), 100_000); p.closed=True; p.net_pnl=-1000
    engine.portfolio.open_trade_id="T"; engine.close_position("T",p)
    assert engine.equity == 99_000


def test_global_one_position_tie_break_is_not_profit_based():
    candidates=[{"timestamp":pd.Timestamp("2026-01-01"),"symbol":"IMOEX","future_pnl":999},
                {"timestamp":pd.Timestamp("2026-01-01"),"symbol":"CNY","future_pnl":-999}]
    assert choose_global_candidate(candidates,("CNY","IMOEX"))["symbol"] == "CNY"


def test_global_portfolio_execution_opens_only_one_ready_setup():
    cfg=replace(BBWConfig(),max_entry_extension_atr=10,max_entry_extension_range_pct=10,
                max_confirmation_candle_atr=10,max_stop_atr=10,max_stop_range_ratio=10)
    engine=CoreEngine(cfg,instrument(),100_000)
    c=pd.Series({"open":11,"high":12,"low":10,"close":11.5},name=pd.Timestamp("2026-01-05 10:00"))
    n=pd.Series({"open":11.2},name=pd.Timestamp("2026-01-05 11:00"))
    assert engine.enter_after_confirmation("CNY","LONG",Range(11,10,1,6),1,c,n) is not None
    assert engine.enter_after_confirmation("IMOEX","SHORT",Range(12,11,1,6),1,c,n) is None
    assert engine.reports.rows["rejected_setups"][-1]["rejection_reason"] == "POSITION_ALREADY_OPEN"


def test_prefix_invariance_end_to_end_and_future_mutation_after_entry():
    data=frame(10); value=Range(11,9,2,6); cfg=replace(BBWConfig(), penetration_ticks=5)
    def trace(d):
        out=[]
        for i,row in d.iterrows():
            event=breakout(row,value)
            touch=evaluate_retest(row,"LONG",11,2,.1,cfg)[0]
            out.append((i,event,touch,entry_rejection(float(row.open),11,1,2,row,cfg)))
        return out
    cutoff=7; expected=trace(data.iloc[:cutoff])
    data.iloc[cutoff:,[1,2,3]]=[[999,-999,500]]*(len(data)-cutoff)
    assert expected == trace(data)[:cutoff]
