from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from market_pattern_discovery.features.feature_set import load_manifest, manifest_signature
from market_pattern_discovery.targets import HORIZONS, build_outcomes


def candles(*, periods=8, timeframe="M1", start="2026-01-05 10:00", highs=None, lows=None, closes=None):
    minutes = 1 if timeframe == "M1" else 5
    times = pd.date_range(start, periods=periods, freq=f"{minutes}min", tz="Europe/Moscow")
    closes = np.asarray(closes if closes is not None else np.arange(100, 100 + periods), dtype=float)
    highs = np.asarray(highs if highs is not None else closes + 2, dtype=float)
    lows = np.asarray(lows if lows is not None else closes - 2, dtype=float)
    return pd.DataFrame({"instrument":"CNYRUBF", "timeframe":timeframe, "open_time":times,
        "close_time":times + pd.Timedelta(minutes=minutes), "open":closes, "high":highs,
        "low":lows, "close":closes})


def test_hand_calculated_path_and_offset_boundary():
    frame = candles(highs=[999,103,108,108,107,108,109,110],
                    lows=[1,98,97,97,96,97,98,99], closes=[100,101,104,103,102,105,106,107])
    out = build_outcomes(frame)
    # The extreme current candle is deliberately excluded; H=1 is row t+1.
    assert out.loc[0,"target_future_close_1"] == 101
    assert out.loc[0,"target_future_max_high_1"] == 103
    assert out.loc[0,"target_future_min_low_1"] == 98
    assert out.loc[0,"target_future_close_3"] == 103
    assert out.loc[0,"target_future_max_high_3"] == 108
    assert out.loc[0,"target_future_min_low_3"] == 97
    assert out.loc[0,"target_long_mfe_3"] == 8
    assert out.loc[0,"target_long_mae_3"] == 3
    assert out.loc[0,"target_short_mfe_3"] == 3
    assert out.loc[0,"target_short_mae_3"] == 8
    assert out.loc[0,"target_future_range_3"] == 11
    assert out.loc[0,"target_close_location_in_future_range_3"] == pytest.approx(6/11)
    assert out.loc[0,"target_bars_to_future_high_3"] == 2  # repeated high uses first
    assert out.loc[0,"target_bars_to_future_low_3"] == 2   # repeated low uses first
    assert np.isnan(out.loc[0,"target_future_high_before_low_3"])
    assert out.loc[1,"target_bars_to_future_high_3"] == 1
    assert out.loc[1,"target_bars_to_future_low_3"] == 3
    assert out.loc[1,"target_future_high_before_low_3"] == 1


def test_flat_range_location_is_nan_and_signed_excursions_are_preserved():
    frame = candles(periods=3, highs=[100,99,98], lows=[100,99,98], closes=[100,99,98])
    out = build_outcomes(frame)
    assert np.isnan(out.loc[0,"target_close_location_in_future_range_1"])
    assert out.loc[0,"target_long_mfe_1"] == -1
    assert out.loc[0,"target_short_mae_1"] == -1


def test_end_of_day_dataset_end_gap_and_next_day_cannot_complete():
    frame = candles(periods=5)
    frame.loc[3:, "open_time"] += pd.Timedelta(days=1)
    frame.loc[3:, "close_time"] += pd.Timedelta(days=1)
    out = build_outcomes(frame)
    assert out.loc[1,"target_future_invalid_reason_3"] == "day_end"
    assert not out.loc[1,"target_future_valid_3"]
    assert np.isnan(out.loc[1,"target_future_close_3"])
    assert out.loc[4,"target_future_invalid_reason_1"] == "data_end"
    gap = candles(periods=5)
    gap.loc[2:,"open_time"] += pd.Timedelta(minutes=1)
    gap.loc[2:,"close_time"] += pd.Timedelta(minutes=1)
    got = build_outcomes(gap)
    assert got.loc[0,"target_future_invalid_reason_3"] == "gap"
    assert np.isnan(got.loc[0,"target_future_max_high_3"])


def test_target_locality_inside_changes_outside_does_not():
    frame = candles(periods=8)
    baseline = build_outcomes(frame)
    outside = frame.copy(); outside.loc[4,"high"] = 500
    assert baseline.loc[0,"target_future_max_high_3"] == build_outcomes(outside).loc[0,"target_future_max_high_3"]
    inside = frame.copy(); inside.loc[2,"high"] = 500
    assert baseline.loc[0,"target_future_max_high_3"] != build_outcomes(inside).loc[0,"target_future_max_high_3"]


@pytest.mark.parametrize("mutation,message", [
    (lambda x: x.iloc[::-1].reset_index(drop=True), "sorted"),
    (lambda x: pd.concat([x.iloc[:2],x.iloc[[1]],x.iloc[2:]],ignore_index=True), "duplicate"),
    (lambda x: x.assign(instrument=["CNYRUBF"]*(len(x)-1)+["USDRUBF"]), "mixed instruments"),
    (lambda x: x.assign(timeframe=["M1"]*(len(x)-1)+["M5"]), "mixed timeframes"),
    (lambda x: x.assign(high=[np.inf]+x.high.iloc[1:].tolist()), "finite"),
    (lambda x: x.assign(high=x.low-1), "OHLC"),
])
def test_rejects_malformed_input(mutation, message):
    with pytest.raises(ValueError, match=message): build_outcomes(mutation(candles()))


def test_output_contract_fixed_grids_and_feature_isolation():
    assert HORIZONS == {"M1":(1,3,5,10,15,30,60), "M5":(1,3,6,12)}
    frame = candles(periods=4)
    out = build_outcomes(frame)
    assert len(out) == len(frame)
    assert out.decision_time.equals(out.close_time)
    assert all(c.startswith("target_") for c in out.columns[5:])
    manifest = load_manifest()
    assert manifest["signature_sha256"] == "0b5ffb328d217e5e8d575ff0b84be794647bc0850e548b354d737ce91342024d"
    assert manifest_signature(manifest) == manifest["signature_sha256"]
    assert not any(name.startswith("target_") for name in manifest["ordered_predictive_features"])
