from __future__ import annotations

import json

import numpy as np
import pandas as pd
import pytest

from market_pattern_discovery.features.feature_set import load_manifest, manifest_signature
from market_pattern_discovery.targets import (HORIZONS, behavior_columns, build_behaviors,
    build_outcomes, generic_columns, known_hypothesis_columns, load_target_manifest,
    outcome_columns, target_definition_signature)


def candles(closes, *, timeframe="M1", highs=None, lows=None):
    c=np.asarray(closes,float); minute=1 if timeframe=="M1" else 5
    opened=pd.date_range("2026-01-05 09:00",periods=len(c),freq=f"{minute}min",tz="Europe/Moscow")
    high=np.asarray(highs if highs is not None else c,float)
    low=np.asarray(lows if lows is not None else c,float)
    return pd.DataFrame({"instrument":"CNYRUBF","timeframe":timeframe,"open_time":opened,
        "close_time":opened+pd.Timedelta(minutes=minute),"open":c,"high":high,"low":low,"close":c})


def build(frame, atr=1.0, delta=1.0):
    features=pd.DataFrame({"atr_20":np.full(len(frame),atr),"close_delta_1":np.full(len(frame),delta)})
    return build_behaviors(frame,features)


def test_manifest_and_signature_are_deterministic_and_frozen_feature_is_unchanged():
    manifest=load_target_manifest()
    assert target_definition_signature(manifest)==manifest["signature_sha256"]
    assert manifest["target_definition_version"]=="1.0"
    assert manifest_signature(load_manifest())=="0b5ffb328d217e5e8d575ff0b84be794647bc0850e548b354d737ce91342024d"
    assert manifest["atr_reference_feature"]=="atr_20"


def test_column_order_count_and_generic_known_partition():
    assert len(behavior_columns("M1"))==180
    assert len(behavior_columns("M5"))==108
    for tf in HORIZONS:
        all_columns=behavior_columns(tf)
        assert all_columns==load_target_manifest()["ordered_columns"][tf]
        assert not set(generic_columns(tf)) & set(known_hypothesis_columns(tf))
        assert set(generic_columns(tf)) | set(known_hypothesis_columns(tf))==set(all_columns)
        assert len(all_columns)==len(set(all_columns))


@pytest.mark.parametrize("closes,expected_length,expected_efficiency,changes,persistence,direction",[
    ([100,101,102,103,104],3,1,0,1,1),
    ([100,99,98,97,96],3,1,0,1,-1),
    ([100,101,100,101,100],3,1/3,2,2/3,1),
    ([100,100,100,100,100],0,np.nan,np.nan,np.nan,0),
    ([100,101,101,100,102],2,0,1,.5,0),
])
def test_manual_generic_close_paths(closes,expected_length,expected_efficiency,changes,persistence,direction):
    out=build(candles(closes),atr=1)
    assert out.loc[0,"behavior_path_length_atr_3"]==expected_length
    if np.isnan(expected_efficiency): assert np.isnan(out.loc[0,"behavior_path_efficiency_3"])
    else: assert out.loc[0,"behavior_path_efficiency_3"]==pytest.approx(expected_efficiency)
    if np.isnan(changes): assert np.isnan(out.loc[0,"behavior_direction_changes_3"])
    else: assert out.loc[0,"behavior_direction_changes_3"]==changes
    if np.isnan(persistence): assert np.isnan(out.loc[0,"behavior_direction_persistence_3"])
    else: assert out.loc[0,"behavior_direction_persistence_3"]==pytest.approx(persistence)
    assert out.loc[0,"label_direction_3"]==direction


def test_excursions_repeated_extremes_order_location_and_large_range_tiny_finish():
    frame=candles([100,100.1,100.2,100.1],highs=[100,102,102,101],lows=[100,99,98,99])
    out=build(frame,atr=2)
    assert out.loc[0,"behavior_up_excursion_atr_3"]==1
    assert out.loc[0,"behavior_down_excursion_atr_3"]==1
    assert out.loc[0,"behavior_excursion_balance_atr_3"]==0
    assert out.loc[0,"behavior_high_time_fraction_3"]==pytest.approx(1/3)
    assert out.loc[0,"behavior_low_time_fraction_3"]==pytest.approx(2/3)
    assert out.loc[0,"label_extreme_order_3"]==1
    assert out.loc[0,"label_future_active_nondirectional_3"]==1


def test_same_candle_extremes_and_barriers_are_ambiguous():
    frame=candles([100,100,100,100],highs=[100,101,100,100],lows=[100,99,100,100])
    out=build(frame)
    assert np.isnan(out.loc[0,"label_extreme_order_3"])
    assert np.isnan(out.loc[0,"label_first_passage_0p5_3"])
    assert np.isnan(out.loc[0,"label_first_passage_1p0_3"])


@pytest.mark.parametrize("highs,lows,expected",[
    ([100,100.5,100,100],[100,100,100,100],1),
    ([100,100,100,100],[100,99.5,100,100],-1),
    ([100,100.4,100,100],[100,99.6,100,100],0),
    ([100,100,100.5,100],[100,99.5,100,100],-1),
])
def test_first_passage_exact_touch_neither_and_order(highs,lows,expected):
    out=build(candles([100]*4,highs=highs,lows=lows))
    assert out.loc[0,"label_first_passage_0p5_3"]==expected


def test_first_passage_event_after_h_is_ignored_and_locality_holds():
    a=candles([100]*8,highs=[100,100,100,100,102,100,100,100],lows=[100]*8)
    b=a.copy(); b.loc[4:,"high"]=110
    left,right=build(a),build(b)
    assert left.loc[0,"label_first_passage_0p5_3"]==right.loc[0,"label_first_passage_0p5_3"]==0
    b.loc[2,"high"]=101
    assert build(b).loc[0,"label_first_passage_0p5_3"]==1


def test_atr_nan_zero_and_invalid_horizon_propagate_nan():
    frame=candles([100,101,102,103])
    for atr in (0,np.nan):
        out=build(frame,atr=atr)
        assert np.isnan(out.loc[0,"behavior_signed_displacement_atr_3"])
        assert np.isnan(out.loc[0,"label_first_passage_0p5_3"])
    out=build(frame)
    assert np.isnan(out.loc[1,"label_direction_3"])
    assert np.isnan(out.loc[1,"behavior_path_length_atr_3"])


def test_shape_immediate_delayed_reversal_signs_and_nonoverlap_speeds():
    # Anchor closes are manually fixed at H5=2, H15=-1, H60=4 ATR.
    close=np.full(65,100.0); close[1:6]=102; close[6:16]=99; close[16:61]=104
    out=build(candles(close),atr=1)
    assert out.loc[0,"behavior_early_displacement_atr"]==2
    assert out.loc[0,"behavior_mid_displacement_atr"]==-1
    assert out.loc[0,"behavior_late_displacement_atr"]==4
    assert out.loc[0,"behavior_early_to_mid_increment_atr"]==-3
    assert out.loc[0,"behavior_mid_to_late_increment_atr"]==5
    assert out.loc[0,"behavior_horizon_sign_changes"]==2
    assert out.loc[0,"behavior_late_increment_speed_atr_per_min"]==pytest.approx(5/45)


def test_phase3a_contract_and_feature_namespace_isolation():
    before={tf:outcome_columns(tf) for tf in HORIZONS}
    assert before=={tf:outcome_columns(tf) for tf in HORIZONS}
    frozen=json.dumps(load_manifest())
    assert "behavior_" not in frozen and "label_" not in frozen
    import market_pattern_discovery.features.builder as builder
    assert "targets" not in open(builder.__file__).read()


def test_malformed_inputs_are_rejected():
    frame=candles([100,101,102,103])
    with pytest.raises(ValueError,match="row counts"): build_behaviors(frame,pd.DataFrame({"atr_20":[1],"close_delta_1":[1]}))
    with pytest.raises(ValueError,match="atr_20"): build_behaviors(frame,pd.DataFrame({"close_delta_1":[1]*4}))
