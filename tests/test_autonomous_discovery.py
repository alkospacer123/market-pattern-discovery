from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from market_pattern_discovery.discovery.phase5b_runner import (
    DiscoveryMatrix, _build_state, _fast_primary_effect,
)
from market_pattern_discovery.strategy_discovery.autonomous import (
    _direction, _pattern_mask, _simulate_raw, load_synthesis_config,
)


def test_autonomous_config_freezes_pf_two_and_safety():
    cfg = load_synthesis_config()
    assert cfg["discovery_gate"]["base_profit_factor"] == 2.0
    assert cfg["discovery_gate"]["stress_profit_factor"] == 1.5
    assert cfg["safety"]["internal_confirmation_accessed"] is False
    assert cfg["safety"]["true_oos_2025_accessed"] is False
    assert cfg["safety"]["profitability_may_not_feed_back_into_phase5b_pattern_enumeration"] is True


def test_binary_states_match_frozen_string_order():
    state, values = _build_state(pd.Series([0.0, 1.0, np.nan, 1.0]), "binary")
    assert values == ["0", "1", "MISSING"]
    assert state.tolist() == ["0", "1", "MISSING", "1"]


def test_fast_continuous_effect_matches_direct_small_sample():
    a = pd.Series([1.0, 2.0, 3.0])
    b = pd.Series([0.0, 1.0, 2.0, 3.0])
    result = _fast_primary_effect(a, b, "continuous")
    assert result["median_difference"] == pytest.approx(np.median(a) - np.median(b))
    brute = np.mean([(x > y) + 0.5 * (x == y) for x in a for y in b])
    assert result["probability_of_superiority"] == pytest.approx(brute)


def test_direction_is_machine_effect_derived():
    long_effect = {
        "target_family": "DIRECTIONAL",
        "target": "behavior_signed_displacement_atr_30",
        "contrast": "continuous",
        "primary_effect_signed": 0.2,
    }
    short_fp = {
        "target_family": "FIRST_PASSAGE",
        "target": "label_first_passage_0p5_60",
        "contrast": "P(-1) versus baseline",
        "primary_effect_signed": 0.1,
    }
    assert _direction(long_effect) == 1
    assert _direction({**long_effect, "primary_effect_signed": -0.2}) == -1
    assert _direction(short_fp) == -1


def test_pattern_mask_signals_only_false_to_true_and_day_reset():
    frame = pd.DataFrame({
        "moscow_trading_date": [
            pd.Timestamp("2026-01-05").date(),
            pd.Timestamp("2026-01-05").date(),
            pd.Timestamp("2026-01-05").date(),
            pd.Timestamp("2026-01-06").date(),
        ]
    })
    matrix = DiscoveryMatrix(
        "CNYRUBF", "M1", frame,
        {"x": pd.Series(["A", "A", "B", "A"])},
        {"x": ["A", "B"]}, [], [],
    )
    effect = {"feature_conditions": [{"feature": "x", "state": "A"}]}
    assert _pattern_mask(matrix, effect).tolist() == [True, False, False, True]


def test_simulator_uses_next_open_and_stop_first_tie():
    day = pd.Timestamp("2026-01-05").date()
    times = pd.date_range("2026-01-05 10:00", periods=4, freq="1min", tz="Europe/Moscow")
    frame = pd.DataFrame({
        "open_time": times,
        "close_time": times + pd.Timedelta(minutes=1),
        "open": [10.0, 10.0, 10.0, 10.0],
        "high": [10.0, 10.0, 11.1, 10.0],
        "low": [10.0, 10.0, 8.9, 10.0],
        "close": [10.0, 10.0, 10.0, 10.0],
        "atr_20": [1.0] * 4,
        "moscow_trading_date": [day] * 4,
    })
    signal = np.array([True, False, False, False])
    raw = _simulate_raw(frame, signal, 1, 0.1, stop_atr=1.0, target_r=1.0, max_hold=3)
    assert len(raw) == 1
    assert raw.iloc[0].entry_time == times[1]
    assert raw.iloc[0].exit_reason == "STOP_FIRST_TIE"
    assert raw.iloc[0].raw_exit == pytest.approx(9.0)
