from __future__ import annotations

import copy

import numpy as np
import pandas as pd
import pytest

from market_pattern_discovery.discovery.target_mapping import (
    baseline_domain,
    fdr_family_key,
    hypothesis_units,
    load_discovery_target_mapping,
    mapped_targets,
    mapping_signature,
    primary_contrasts,
    target_valid_domain,
    validate_mapping_against_behavior_set,
)


@pytest.fixture(scope="module")
def mapping():
    return load_discovery_target_mapping()


def test_mapping_deterministic_signature(mapping):
    assert mapping_signature(mapping) == mapping["signature_sha256"]
    assert mapping_signature(mapping) == mapping_signature(copy.deepcopy(mapping))


def test_m1_mapping_order(mapping):
    names = [x["column_name"] for x in mapped_targets("M1", mapping=mapping)]
    assert names[:3] == ["behavior_signed_displacement_atr_5", "behavior_signed_displacement_atr_15", "behavior_signed_displacement_atr_60"]
    assert names[-1] == "behavior_horizon_sign_changes"


def test_m5_mapping_order(mapping):
    names = [x["column_name"] for x in mapped_targets("M5", mapping=mapping)]
    assert names[:3] == ["behavior_signed_displacement_atr_1", "behavior_signed_displacement_atr_3", "behavior_signed_displacement_atr_12"]
    assert names[-1] == "behavior_horizon_sign_changes"


def test_missing_mapped_column_rejection(mapping):
    changed = copy.deepcopy(mapping); changed["mapping"]["M1"][0]["column_name"] = "does_not_exist"
    with pytest.raises(ValueError, match="missing mapped column"): validate_mapping_against_behavior_set(changed)


def test_removed_column_rejection(mapping):
    changed = copy.deepcopy(mapping); changed["mapping"]["M1"][0]["column_name"] = "behavior_path_efficiency_1"
    with pytest.raises(ValueError, match="removed column"): validate_mapping_against_behavior_set(changed)


def test_wrong_timeframe_rejection(mapping):
    changed = copy.deepcopy(mapping); changed["mapping"]["M1"][0]["timeframe"] = "M5"
    with pytest.raises(ValueError, match="wrong timeframe"): validate_mapping_against_behavior_set(changed)


def test_duplicate_mapping_rejection(mapping):
    changed = copy.deepcopy(mapping); changed["mapping"]["M1"][1]["column_name"] = changed["mapping"]["M1"][0]["column_name"]
    with pytest.raises(ValueError, match="duplicate mapped column"): validate_mapping_against_behavior_set(changed)


def test_invalid_encoding_rejection(mapping):
    changed = copy.deepcopy(mapping); direction = next(x for x in changed["mapping"]["M1"] if x["column_name"] == "label_direction_5")
    direction["encoding"]["classes"] = [0, 1]
    with pytest.raises(ValueError, match="invalid direction encoding"): validate_mapping_against_behavior_set(changed)


def test_hypothesis_unit_count(mapping):
    assert hypothesis_units("M1", mapping=mapping) == 36
    assert hypothesis_units("M5", mapping=mapping) == 36


def test_direction_has_two_primary_contrasts(mapping):
    assert len(primary_contrasts("label_direction_5", timeframe="M1", mapping=mapping)) == 2


def test_first_passage_has_two_primary_contrasts(mapping):
    assert len(primary_contrasts("label_first_passage_0p5_1", timeframe="M5", mapping=mapping)) == 2


def test_continuous_and_binary_have_one_unit(mapping):
    continuous = next(x for x in mapping["mapping"]["M1"] if x["target_type"] == "continuous")
    binary = next(x for x in mapping["mapping"]["M1"] if x["target_type"] == "binary")
    assert continuous["hypothesis_units_per_state"] == binary["hypothesis_units_per_state"] == 1


def test_nan_validity_preservation():
    frame = pd.DataFrame({"target": [1.0, np.nan, 0.0]})
    assert target_valid_domain(frame, "target").tolist() == [True, False, True]


def test_baseline_valid_domain_rule():
    frame = pd.DataFrame({"instrument": ["X"] * 4, "timeframe": ["M1"] * 4, "target": [1, np.nan, 0, 1]})
    assert baseline_domain(frame, "target", instrument="X", timeframe="M1", discovery_mask=[True, True, False, True]).tolist() == [True, False, False, True]


def test_fdr_family_key_determinism():
    args = dict(instrument="X", timeframe="M5", discovery_method="RULE", target_family="PATH", semantic_role="EFFICIENCY", horizon=12)
    assert fdr_family_key(**args) == fdr_family_key(**args) == "X|M5|RULE|PATH|EFFICIENCY@H12"


@pytest.mark.parametrize("field,value", [
    ("column_name", "changed_target"), ("horizon", 30),
    ("hypothesis_contrasts", ["changed contrast"]),
])
def test_signature_drift_after_governed_change(mapping, field, value):
    changed = copy.deepcopy(mapping); changed["mapping"]["M1"][0][field] = value
    assert mapping_signature(changed) != mapping["signature_sha256"]
