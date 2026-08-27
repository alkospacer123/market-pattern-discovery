import copy

import numpy as np
import pandas as pd
import pytest

from market_pattern_discovery.features.feature_set import (PROVENANCE_COLUMNS, bounded_violations,
    exact_duplicate_groups, invalid_columns, load_manifest, manifest_signature)


def test_manifest_signature_is_deterministic_and_valid():
    manifest = load_manifest()
    assert manifest_signature(manifest) == manifest["signature_sha256"]
    assert manifest_signature(copy.deepcopy(manifest)) == manifest["signature_sha256"]


def test_manifest_feature_order_and_frozen_counts():
    manifest = load_manifest()
    assert len(manifest["ordered_predictive_features"]) == 241
    assert len(manifest["m5_ordered_predictive_features"]) == 220
    flattened = sum((manifest["feature_families"][key] for key in
                     ("phase2a", "structure", "round_level", "m5_context", "cross_timeframe")), [])
    assert flattened == manifest["ordered_predictive_features"]


def test_feature_order_change_is_detected_by_signature():
    manifest = load_manifest(); expected = manifest["signature_sha256"]
    manifest["ordered_predictive_features"] = list(reversed(manifest["ordered_predictive_features"]))
    assert manifest_signature(manifest) != expected


def test_exact_duplicate_all_nan_and_constant_detection():
    frame = pd.DataFrame({"a": [1.0, np.nan, 2.0], "b": [1.0, np.nan, 2.0],
                          "constant": [3, 3, 3], "empty": [np.nan] * 3})
    assert exact_duplicate_groups(frame, list(frame)) == [["a", "b"]]
    invalid = invalid_columns(frame, list(frame))
    assert invalid["all_nan"] == ["empty"]
    assert invalid["constant"] == ["constant"]


def test_duplicate_requires_identical_nan_mask():
    frame = pd.DataFrame({"a": [1.0, np.nan], "b": [1.0, 1.0]})
    assert exact_duplicate_groups(frame, ["a", "b"]) == []


def test_provenance_is_excluded_from_predictive_contract():
    manifest = load_manifest()
    assert tuple(manifest["excluded_provenance_columns"]) == PROVENANCE_COLUMNS
    assert not set(PROVENANCE_COLUMNS) & set(manifest["ordered_predictive_features"])


def test_bounded_feature_validation():
    good = pd.DataFrame({"candle_direction": [-1, 0, 1], "fraction_up_bars_5": [0, .5, 1]})
    assert bounded_violations(good, list(good)) == {}
    bad = good.copy(); bad.loc[0, "fraction_up_bars_5"] = 1.1
    assert bounded_violations(bad, list(bad)) == {"fraction_up_bars_5": 1}


def test_manifest_names_are_unique():
    names = load_manifest()["ordered_predictive_features"]
    assert len(names) == len(set(names))
