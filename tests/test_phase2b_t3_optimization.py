from dataclasses import asdict
import hashlib
from pathlib import Path

import pandas as pd

from TradingSystemLab.baseline_v2 import four_bar_context
from TradingSystemLab.optimization.phase2b_t3 import (BASELINE, COST_MODEL, FROZEN_TICK_SIZE,
    INSTRUMENTS, PARAMETER_SPACE, STRATEGY_HASH, TIMEFRAMES, bounded_design, classify,
    configuration_id, neighbors)
from TradingSystemLab.strategies.trend.T3_MTF_Trend import T3Parameters


def test_scope_design_and_common_six_instrument_configuration():
    assert TIMEFRAMES == ("M30", "H1")
    assert INSTRUMENTS == ("Si", "CNY", "GD", "BR", "MIX", "NG")
    configs = bounded_design()
    assert len(configs) == 22 and len(configs) * len(TIMEFRAMES) == 44
    assert configs.count(BASELINE) == 1
    assert all(sum(row[name] != BASELINE[name] for name in PARAMETER_SPACE) == 1
               for row in configs if row != BASELINE)
    assert all(len({configuration_id(tf, row) for row in configs}) == 22 for tf in TIMEFRAMES)


def test_exact_original_space_baseline_and_c1_contract():
    assert PARAMETER_SPACE == {
        "ema_period": [50, 75, 100, 150, 200], "adx_threshold": [15, 20, 25, 30],
        "breakout_period": [10, 20, 30, 40, 55], "atr_average_period": [10, 20, 30, 50],
        "stop_atr": [1.5, 2.0, 2.5, 3.0], "trail_atr": [2.0, 2.5, 3.0, 3.5, 4.0]}
    assert BASELINE["ema_period"] == 100 and BASELINE != {**BASELINE, "ema_period": 75}
    assert BASELINE == {name: getattr(T3Parameters(), name) for name in PARAMETER_SPACE}
    assert COST_MODEL == {"name": "C1", "ticks_per_side": 1, "round_trip_ticks": 2,
                          "additional_slippage_ticks": 0}
    assert FROZEN_TICK_SIZE == 0.001


def test_immediate_neighbors_and_exact_plateau_threshold():
    from TradingSystemLab.optimization import phase2b_t3
    old = phase2b_t3.PARAMETER_SPACE
    phase2b_t3.PARAMETER_SPACE = {"x": [1, 2, 3]}
    try:
        configs = [{"x": 1}, {"x": 2}, {"x": 3}]
        assert neighbors(configs, 1) == [0, 2]
        results = [{"configuration_id": str(i), "expectancy_C1": value, "PF_C1": 1.1}
                   for i, value in enumerate((0.066, 0.1, 0.134))]
        rows, overall = classify(configs, results)
        assert abs(rows[1]["stability_tolerance"] - 0.035) < 1e-15
        assert rows[1]["stable_positive_neighbors"] == 2
        assert rows[1]["classification"] == overall == "ROBUST_PLATEAU"
        results[0]["expectancy_C1"] = 0.064
        assert classify(configs, results)[0][1]["classification"] == "LOCAL_SPIKE"
    finally:
        phase2b_t3.PARAMETER_SPACE = old


def test_four_bar_context_is_separate_causal_and_day_bounded():
    index = pd.to_datetime(["2024-01-01 10:00", "2024-01-01 10:30", "2024-01-01 11:00",
                            "2024-01-01 11:30", "2024-01-01 12:00",
                            "2024-01-02 10:00", "2024-01-02 10:30", "2024-01-02 11:00",
                            "2024-01-02 11:30"], utc=True)
    frame = pd.DataFrame({"Open": range(9), "High": range(1, 10), "Low": range(9),
                          "Close": range(1, 10)}, index=index)
    context = four_bar_context(frame)
    assert context is not frame
    assert context.index.tolist() == [index[3], index[8]]
    assert context.iloc[0].Open == 0 and context.iloc[0].Close == 4


def test_frozen_strategy_hash_and_defaults():
    path = Path("TradingSystemLab/strategies/trend/T3_MTF_Trend.py")
    assert hashlib.sha256(path.read_bytes()).hexdigest() == STRATEGY_HASH
    assert asdict(T3Parameters())["ema_period"] == 100
