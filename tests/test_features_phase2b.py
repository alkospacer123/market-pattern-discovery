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
                          round_levels=RoundLevelConfig("0.001", "0.05"), native_m5=m5)


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


def test_cny_decimal_round_grid_tick_boundaries_and_tie():
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
    assert pd.isna(out.loc[2, "bars_since_last_touch"])  # current reference changed to 11.15
    artifacts = candles()
    artifacts.loc[0:2, "close"] = [11.10-1e-12, 11.10, 11.10+1e-12]
    artifacts.loc[0:2, "open"] = artifacts.loc[0:2, "close"]
    artifacts.loc[0:2, "high"] = artifacts.loc[0:2, "close"]+1e-5
    artifacts.loc[0:2, "low"] = artifacts.loc[0:2, "close"]-1e-5
    classified = build(artifacts).frame
    assert classified.loc[:2, "nearest_round_level"].tolist() == pytest.approx([11.10]*3)
    cny = candles()
    cny.loc[:3, "close"] = [12.600, 12.601, 12.599, 12.625]
    cny.loc[:3, "open"] = cny.loc[:3, "close"]
    cny.loc[:3, "high"] = cny.loc[:3, "close"]
    cny.loc[:3, "low"] = cny.loc[:3, "close"]
    levels = build(cny).frame
    assert levels.loc[:2, "nearest_round_level"].tolist() == pytest.approx([12.60]*3)
    assert levels.loc[0, "round_level_above"] == pytest.approx(12.65)
    assert levels.loc[3, "nearest_round_level"] == pytest.approx(12.65)


def test_si_canonical_grid_and_configuration_validation():
    frame = candles(); frame.instrument = "USDRUBF"
    frame.loc[:3, "close"] = [85.00, 85.01, 84.99, 85.05]
    frame.loc[:3, "open"] = frame.loc[:3, "close"]
    frame.loc[:3, "high"] = frame.loc[:3, "close"]
    frame.loc[:3, "low"] = frame.loc[:3, "close"]
    cfg = RoundLevelConfig("0.01", "0.10")
    out = build_features(frame, timeframe="M1", round_levels=cfg).frame
    assert cfg.round_level_step_ticks == 10
    assert out.loc[:2, "nearest_round_level"].tolist() == pytest.approx([85.0]*3)
    assert out.loc[0, "round_level_above"] == pytest.approx(85.10)
    assert out.loc[3, "nearest_round_level"] == pytest.approx(85.10)
    with pytest.raises(ValueError): RoundLevelConfig("0", "0.10")
    with pytest.raises(ValueError): RoundLevelConfig("-0.01", "0.10")
    with pytest.raises(ValueError): RoundLevelConfig("0.01", "0")
    with pytest.raises(ValueError): RoundLevelConfig("0.01", "-0.10")
    with pytest.raises(ValueError): RoundLevelConfig("0.01", "0.10", "-0.01")
    with pytest.raises(ValueError): RoundLevelConfig("0.03", "0.10")


@pytest.mark.parametrize("field", ["tick_size", "round_level_step", "touch_tolerance"])
@pytest.mark.parametrize("value", ["NaN", "Infinity", "-Infinity"])
def test_round_level_configuration_rejects_non_finite_values(field, value):
    values = {"tick_size": "0.001", "round_level_step": "0.05", "touch_tolerance": "0"}
    values[field] = value
    with pytest.raises(ValueError, match="finite"):
        RoundLevelConfig(**values)


def test_native_m5_instrument_identity_is_required():
    cny_m1 = candles(10, timeframe="M1")
    cny_m5 = candles(3, timeframe="M5")
    si_m1 = cny_m1.copy(); si_m1.instrument = "USDRUBF"
    si_m5 = cny_m5.copy(); si_m5.instrument = "USDRUBF"
    cny_config = RoundLevelConfig("0.001", "0.05")
    si_config = RoundLevelConfig("0.01", "0.10")
    assert len(build_features(cny_m1, timeframe="M1", round_levels=cny_config, native_m5=cny_m5).frame) == 10
    assert len(build_features(si_m1, timeframe="M1", round_levels=si_config, native_m5=si_m5).frame) == 10
    with pytest.raises(ValueError, match="instruments must match"):
        build_features(cny_m1, timeframe="M1", round_levels=cny_config, native_m5=si_m5)
    with pytest.raises(ValueError, match="instruments must match"):
        build_features(si_m1, timeframe="M1", round_levels=si_config, native_m5=cny_m5)


def test_historical_counts_use_current_reference_level_and_reset_by_day():
    frame = candles(70)
    # Rows 5, 7, 9 touch/cross 11.50. Other closes still select 11.50 as
    # current reference without touching it; expected values are hand specified.
    frame.loc[:9, ["open", "high", "low", "close"]] = [11.476, 11.48, 11.47, 11.476]
    for i in (5, 7, 9): frame.loc[i, ["open", "high", "low", "close"]] = [11.49, 11.51, 11.49, 11.50]
    out = build(frame).frame
    assert out.loc[9, "nearest_round_level"] == pytest.approx(11.50)
    assert out.loc[5, "touch_count_5"] == 1
    assert out.loc[7, "touch_count_5"] == 2
    assert out.loc[9, "touch_count_5"] == 3 and out.loc[9, "cross_count_5"] == 3
    assert out.loc[6, "bars_since_last_touch"] == 1
    assert out.loc[8, "bars_since_last_touch"] == 1
    assert out.loc[9, "bars_since_last_touch"] == 0
    next_day = candles(5, "2026-01-06 10:00")
    next_day.loc[0, ["open", "high", "low", "close"]] = 11.461
    combined = build(pd.concat([frame, next_day], ignore_index=True)).frame
    assert pd.isna(combined.loc[70, "bars_since_last_touch"])


def test_m5_exact_boundary_missing_day_and_cross_timeframe():
    m5 = candles(3, "2026-01-05 10:00", "M5")
    m1 = candles(7, "2026-01-05 10:04", "M1")
    out = build(m1, m5).frame
    assert out.loc[0, "m5_source_open_time"] == m5.loc[0, "open_time"]  # M1 close equality at 10:05
    assert out.loc[4, "m5_source_open_time"] == m5.loc[0, "open_time"]  # close 10:09 cannot see next M5
    assert out.loc[5, "m5_source_open_time"] == m5.loc[1, "open_time"]  # close 10:10 may
    assert out.loc[0, "direction_agreement_m1_m5"] == 1
    next_day = candles(1, "2026-01-06 10:00")
    assert pd.isna(build(next_day, m5).frame.loc[0, "m5_source_close_time"])


def test_phase2b_prefix_future_and_future_m5_invariance_and_count():
    frame = candles(90); m5 = candles(20, timeframe="M5")
    full = build(frame, m5)
    assert len(full.metadata["feature_names"]) == 241  # frozen v1.0 removes nine objective redundancies
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
