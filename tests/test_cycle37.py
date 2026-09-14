import json

import pandas as pd

from market_pattern_discovery.research.cycle37 import (Candidate, causal_levels,
    enumerate_candidates, rejection_mask, simulate)


def protocol():
    return json.loads(open("config/cycle37_structural_rejection_family.json", encoding="utf-8").read())


def frame(freq="5min", periods=65):
    ts = pd.date_range("2026-01-06 09:00", periods=periods, freq=freq, tz="Europe/Moscow")
    return pd.DataFrame({"timestamp": ts, "open": 10.02, "high": 10.03,
                         "low": 10.01, "close": 10.02, "volume": 1})


def test_grid_keeps_four_families_independent():
    candidates = enumerate_candidates(protocol(), "CNYRUBF")
    assert len(candidates) == 4 * 2 * 4 * 3 * 3 * 3
    assert all("OR" not in candidate.structure for candidate in candidates)


def test_rolling_level_excludes_setup_and_resets_day():
    bars = frame()
    bars.loc[:29, "low"] = range(30)
    levels = causal_levels(bars, "ROLL30", "LONG", .05)
    assert pd.isna(levels.iloc[29])
    assert levels.iloc[30] == 0
    bars.loc[60:, "timestamp"] += pd.Timedelta(days=1)
    assert causal_levels(bars, "ROLL30", "LONG", .05).iloc[60:].isna().all()


def test_rejection_is_based_on_completed_setup_ohlc():
    bars = frame(periods=2)
    bars.loc[1, ["open", "high", "low", "close"]] = [10.01, 10.03, 9.99, 10.02]
    mask = rejection_mask(bars, pd.Series([10.0, 10.0]), "LONG", "sweep_reclaim")
    assert mask.tolist() == [False, True]


def test_m1_entry_is_not_before_m5_completion_and_stop_wins_tie():
    p = protocol(); candidate = Candidate("ROUND", "LONG", "sweep_reclaim", "0900_1200", 8, 3)
    m1 = frame("1min", 12)
    m1.loc[:, ["open", "high", "low", "close"]] = [10.0, 10.1, 9.9, 10.0]
    signal = pd.DataFrame({"setup_open": [m1.timestamp.iloc[0]],
                           "signal_time": [m1.timestamp.iloc[5]], "level": [10.0]})
    trades = simulate(m1, signal, candidate, p, "CNYRUBF")
    assert trades[0]["entry_time"] == m1.timestamp.iloc[5]
    assert trades[0]["exit_reason"] == "stop"
