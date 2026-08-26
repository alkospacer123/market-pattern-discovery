import numpy as np
import pandas as pd
import pytest

from market_pattern_discovery.features import RoundLevelConfig, build_features


def candles(count=70, start="2026-01-05 10:00", timeframe="M1"):
    minutes = 1 if timeframe == "M1" else 5
    opened = pd.date_range(start, periods=count, freq=f"{minutes}min", tz="Europe/Moscow")
    close = 11 + np.arange(count) * .01
    return pd.DataFrame({"open": close-.005, "high": close+.01, "low": close-.01, "close": close,
        "volume": np.arange(count, dtype=float), "instrument": "CNYRUBF", "timeframe": timeframe,
        "open_time": opened, "close_time": opened+pd.Timedelta(minutes=minutes)})


def build(frame, m5=None):
    return build_features(frame, timeframe=frame.timeframe.iloc[0],
                          round_levels=RoundLevelConfig("0.05"), native_m5=m5)


def test_manual_structure_prior_excludes_current_and_resets():
    frame = candles()
    out = build(frame).frame
    assert out.loc[4, "rolling_high_5"] == pytest.approx(11.05)
    assert out.loc[4, "rolling_low_5"] == pytest.approx(10.99)
    assert out.loc[4, "position_in_rolling_range_5"] == pytest.approx(5/6)
    assert out.loc[5, "prior_high_5"] == pytest.approx(11.05)
    frame.loc[5, ["open", "high", "low", "close"]] = [11.19, 11.21, 11.18, 11.20]
    broken = build(frame).frame
    assert broken.loc[5, "prior_high_5"] == pytest.approx(11.05)
    assert broken.loc[5, "break_above_prior_high_5"] == 1


def test_decimal_round_grid_tie_touch_cross_and_history():
    frame = candles()
    frame.loc[0, ["open", "high", "low", "close"]] = [11.1, 11.1, 11.1, 11.1]
    frame.loc[1, ["open", "high", "low", "close"]] = [11.10, 11.11, 11.09, 11.10]
    frame.loc[2, ["open", "high", "low", "close"]] = [11.124, 11.126, 11.123, 11.125]
    out = build(frame).frame
    assert out.loc[0, "nearest_round_level"] == 11.10
    assert out.loc[2, "round_level_below"] == 11.10 and out.loc[2, "round_level_above"] == 11.15
    assert out.loc[2, "nearest_round_level"] == 11.15  # midpoint ties upward
    assert out.loc[0, "signed_distance_to_nearest_round_level"] == pytest.approx(0)
    assert out.loc[1, "touches_nearest_round_level"] == 1 and out.loc[1, "crosses_nearest_round_level"] == 1
    assert out.loc[4, "touch_count_5"] == 2
    assert out.loc[2, "bars_since_last_touch"] == 1
    artifacts = candles()
    artifacts.loc[0:2, "close"] = [11.10-1e-12, 11.10, 11.10+1e-12]
    artifacts.loc[0:2, "open"] = artifacts.loc[0:2, "close"]
    artifacts.loc[0:2, "high"] = artifacts.loc[0:2, "close"]+1e-5
    artifacts.loc[0:2, "low"] = artifacts.loc[0:2, "close"]-1e-5
    classified = build(artifacts).frame
    assert classified.loc[:2, "nearest_round_level"].tolist() == pytest.approx([11.10]*3)


def test_m5_exact_boundary_missing_day_and_cross_timeframe():
    m5 = candles(3, "2026-01-05 10:00", "M5")
    m1 = candles(7, "2026-01-05 10:04", "M1")
    out = build(m1, m5).frame
    assert pd.isna(out.loc[0, "m5_source_close_time"])
    assert out.loc[1, "m5_source_open_time"] == m5.loc[0, "open_time"]  # equality at 10:05
    assert out.loc[5, "m5_source_open_time"] == m5.loc[0, "open_time"]  # 10:09 cannot see 10:05
    assert out.loc[6, "m5_source_open_time"] == m5.loc[1, "open_time"]  # 10:10 may
    assert out.loc[1, "direction_agreement_m1_m5"] == 1
    next_day = candles(1, "2026-01-06 10:00")
    assert pd.isna(build(next_day, m5).frame.loc[0, "m5_source_close_time"])


def test_phase2b_prefix_future_and_future_m5_invariance_and_count():
    frame = candles(90); m5 = candles(20, timeframe="M5")
    full = build(frame, m5)
    assert len(full.metadata["feature_names"]) == 250
    prefix = build(frame.iloc[:60].copy(), m5.iloc[:12].copy()).frame
    pd.testing.assert_frame_equal(full.frame.iloc[:60].reset_index(drop=True), prefix, check_exact=True)
    changed = m5.copy(); changed.loc[12:, ["open", "high", "low", "close", "volume"]] *= 10
    pd.testing.assert_frame_equal(full.frame.iloc[:60].reset_index(drop=True),
                                  build(frame, changed).frame.iloc[:60].reset_index(drop=True), check_exact=True)


def test_future_ohlcv_and_prior_day_perturbations_cannot_leak():
    first = candles(70); second = candles(70, "2026-01-06 10:00")
    frame = pd.concat([first, second], ignore_index=True)
    baseline = build(frame).frame
    future = frame.copy(); future.loc[60:69, ["open", "high", "low", "close", "volume"]] *= 20
    pd.testing.assert_frame_equal(baseline.iloc[:60], build(future).frame.iloc[:60], check_exact=True)
    prior = frame.copy(); prior.loc[:69, ["open", "high", "low", "close", "volume"]] *= 20
    pd.testing.assert_frame_equal(baseline.iloc[70:].reset_index(drop=True),
                                  build(prior).frame.iloc[70:].reset_index(drop=True), check_exact=True)
