import numpy as np
import pandas as pd
import pytest

from market_pattern_discovery.features import FeatureInputError, build_core_features


def candles(count=70, start="2026-01-05 10:00", timeframe="M1"):
    minutes = 1 if timeframe == "M1" else 5
    opened = pd.date_range(start, periods=count, freq=f"{minutes}min", tz="Europe/Moscow")
    close = 10.0 + np.arange(count)
    return pd.DataFrame({
        "open": close - 0.5, "high": close + 1.0, "low": close - 1.0, "close": close,
        "volume": np.arange(1, count + 1, dtype=float), "instrument": "CNYRUBF", "timeframe": timeframe,
        "open_time": opened, "close_time": opened + pd.Timedelta(minutes=minutes),
    })


def build(frame):
    return build_core_features(frame, timeframe=frame.timeframe.iloc[0]).frame


def test_hand_calculated_geometry_returns_true_range_atr_efficiency_and_volume():
    frame = candles(21)
    frame.loc[0, ["open", "high", "low", "close"]] = [10, 13, 9, 12]
    frame.loc[1, ["open", "high", "low", "close"]] = [12, 15, 11, 14]
    result = build(frame)
    assert result.loc[0, "signed_body"] == 2
    assert result.loc[0, "upper_wick"] == 1 and result.loc[0, "lower_wick"] == 1
    assert result.loc[0, "close_position_in_range"] == pytest.approx(0.75)
    assert result.loc[1, "close_return_1"] == pytest.approx(2 / 12)
    assert result.loc[1, "log_return_1"] == pytest.approx(np.log(14 / 12))
    assert result.loc[0, "true_range"] == 4 and result.loc[1, "true_range"] == 4
    assert result.loc[4, "atr_5"] == pytest.approx((4 + 4 + 3 + 2 + 2) / 5)
    # From close 14 at row 1 to 14 at row 4: net zero, path length four.
    assert result.loc[4, "directional_efficiency_3"] == 0
    assert result.loc[4, "relative_volume_5"] == pytest.approx(5 / 3)
    expected_z = (21 - 11.5) / pd.Series(range(2, 22), dtype=float).std()
    assert result.loc[20, "volume_zscore_20"] == pytest.approx(expected_z)


def test_streaks_and_all_state_reset_at_moscow_day_boundary():
    first = candles(65, "2026-01-05 10:00")
    second = candles(65, "2026-01-06 10:00")
    frame = pd.concat([first, second], ignore_index=True)
    result = build(frame)
    assert result.loc[64, "consecutive_up_candles"] == 65
    assert result.loc[65, "consecutive_up_candles"] == 1
    assert np.isnan(result.loc[65, "close_return_1"])
    assert result.loc[65, "true_range"] == result.loc[65, "candle_range"]
    assert np.isnan(result.loc[68, "atr_5"]) and not np.isnan(result.loc[69, "atr_5"])


def test_zero_ranges_and_zero_variance_are_nan_not_infinite():
    frame = candles(70)
    frame.loc[0, ["open", "high", "low", "close"]] = 10
    frame.volume = 5
    result = build(frame)
    assert np.isnan(result.loc[0, "body_to_range"])
    assert result["volume_zscore_20"].isna().all()
    assert not np.isinf(result.select_dtypes(include=[np.number]).to_numpy()).any()


def test_prefix_future_append_and_future_perturbation_invariance():
    frame = candles(100)
    full = build(frame)
    prefix = build(frame.iloc[:60].copy())
    pd.testing.assert_frame_equal(full.iloc[:60].reset_index(drop=True), prefix.reset_index(drop=True), check_exact=True)
    changed = frame.copy()
    changed.loc[60:, ["open", "high", "low", "close", "volume"]] *= 100
    perturbed = build(changed)
    pd.testing.assert_frame_equal(full.iloc[:60].reset_index(drop=True), perturbed.iloc[:60].reset_index(drop=True), check_exact=True)


def test_previous_day_perturbation_cannot_change_next_day():
    first = candles(70, "2026-01-05 10:00")
    second = candles(70, "2026-01-06 10:00")
    original = pd.concat([first, second], ignore_index=True)
    changed = original.copy()
    changed.loc[:69, ["open", "high", "low", "close", "volume"]] *= 50
    left, right = build(original).iloc[70:].reset_index(drop=True), build(changed).iloc[70:].reset_index(drop=True)
    pd.testing.assert_frame_equal(left, right, check_exact=True)


def test_metadata_and_no_target_columns_and_row_preservation():
    frame = candles(3, timeframe="M5")
    result = build_core_features(frame, timeframe="M5")
    assert len(result.frame) == 3 == result.metadata["input_rows"] == result.metadata["output_rows"]
    assert result.metadata["feature_builder_version"] == "1.0"
    assert result.metadata["configured_windows"]["general"] == [1, 3, 5, 10, 20, 30, 60]
    assert not any("target" in name.lower() for name in result.frame)


def test_rejects_malformed_or_unordered_input():
    with pytest.raises(FeatureInputError, match="ordered"):
        build(candles(3).iloc[::-1].reset_index(drop=True))
    bad = candles(3).drop(columns="volume")
    with pytest.raises(FeatureInputError, match="missing"):
        build_core_features(bad, timeframe="M1")
