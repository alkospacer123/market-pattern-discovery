from dataclasses import asdict
import hashlib
from pathlib import Path

from TradingSystemLab.optimization.phase2a_t2 import (BASELINE, COST_MODEL, FROZEN_TICK_SIZE,
    INSTRUMENTS, PARAMETER_SPACE, STRATEGY_HASH, TIMEFRAMES, bounded_design, classify,
    configuration_id, neighbors)
from TradingSystemLab.strategies.trend.T2_Trend_Pullback import T2Parameters


def test_scope_design_and_common_six_instrument_configuration():
    assert TIMEFRAMES == ("M30", "H1")
    assert INSTRUMENTS == ("Si", "CNY", "GD", "BR", "MIX", "NG")
    configs = bounded_design()
    assert len(configs) == 19 and len(configs) * len(TIMEFRAMES) == 38
    assert configs.count(BASELINE) == 1
    assert all(sum(row[name] != BASELINE[name] for name in PARAMETER_SPACE) == 1
               for row in configs if row != BASELINE)
    assert all(len({configuration_id(tf, row) for row in configs}) == 19 for tf in TIMEFRAMES)


def test_exact_original_space_baseline_and_c1_contract():
    assert PARAMETER_SPACE == {"ema_fast": [15, 20, 25, 30], "ema_trend": [40, 50, 60],
        "ema_slow": [150, 200, 250], "adx_threshold": [15, 20, 25, 30],
        "impulse_distance_atr": [0.3, 0.5, 0.7], "confirmation_window": [2, 3, 4],
        "max_initial_stop_atr": [2.0, 2.5, 3.0], "trailing_atr": [2.0, 3.0, 4.0]}
    assert BASELINE["max_initial_stop_atr"] == 3.0
    assert BASELINE == {name: getattr(T2Parameters(), name) for name in PARAMETER_SPACE}
    assert COST_MODEL == {"name": "C1", "ticks_per_side": 1, "round_trip_ticks": 2,
                          "additional_slippage_ticks": 0}
    assert FROZEN_TICK_SIZE == 0.001


def test_immediate_neighbors_and_exact_plateau_threshold():
    configs = [{"x": 1}, {"x": 2}, {"x": 3}]
    from TradingSystemLab.optimization import phase2a_t2
    old = phase2a_t2.PARAMETER_SPACE
    phase2a_t2.PARAMETER_SPACE = {"x": [1, 2, 3]}
    try:
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
        phase2a_t2.PARAMETER_SPACE = old


def test_frozen_strategy_hash_and_phase1_tree_are_untouched():
    path = Path("TradingSystemLab/strategies/trend/T2_Trend_Pullback.py")
    assert hashlib.sha256(path.read_bytes()).hexdigest() == STRATEGY_HASH
    assert asdict(T2Parameters())["max_initial_stop_atr"] == 3.0
