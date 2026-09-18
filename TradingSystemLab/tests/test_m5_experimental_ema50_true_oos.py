from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

from TradingSystemLab.multitimeframe.phase73 import hash_tree
from TradingSystemLab.true_oos import m5 as primary
from TradingSystemLab.true_oos.m5_experimental_ema50 import (
    CANDIDATE_ID, CLASSIFICATION, EMA_DEFINITION, PRIMARY, STATUS, _normal,
    validate_snapshot, verify_provenance,
)


def _bars(index: pd.DatetimeIndex) -> pd.DataFrame:
    return pd.DataFrame({"Open": 1., "High": 2., "Low": .5, "Close": 1.5}, index=index)


def test_exact_pre_oos_identity_session_and_ema_provenance() -> None:
    frozen = verify_provenance()
    assert STATUS == "PHASE_M5_EXPERIMENTAL_EMA50_NORMAL_TRUE_OOS_COMPLETE"
    assert CLASSIFICATION == "EXPERIMENTAL_PRE_REGISTERED_COMPARATOR"
    assert CANDIDATE_ID in frozen["wf_manifest"]["candidate_identities"]
    assert frozen["definition"] == {"weekdays": "Monday-Friday", "entry_start_inclusive": "10:00",
                                    "entry_end_exclusive": "17:00", "ema50_distance_classification": "normal"}
    assert EMA_DEFINITION == {"normalization": "absolute_close_minus_ema50_divided_by_atr14",
                              "near": "<=0.5", "normal": ">0.5 and <=1.5", "extended": ">1.5"}
    assert _normal(pd.Series({"Close": 101., "EMA50": 100., "ATR": 1.}))
    assert not _normal(pd.Series({"Close": 100.5, "EMA50": 100., "ATR": 1.}))
    assert not _normal(pd.Series({"Close": 101.50001, "EMA50": 100., "ATR": 1.}))


def test_candidate_strategy_parameter_hashes_and_snapshot_are_primary() -> None:
    frozen = verify_provenance()
    manifest = frozen["primary_manifest"]
    assert manifest["underlying_candidate_ids"] == primary.CANDIDATES
    assert manifest["frozen_parameter_hashes"] == frozen["parameter_hashes"]
    assert manifest["strategy_hashes"] == frozen["strategy_hashes"]
    loaded = validate_snapshot(Path("/workspace/market-pattern-data"), manifest["true_oos_source_hashes"])
    coverage = {"start": min(v[0].index.min() for v in loaded.values()).isoformat(),
                "end": max(v[0].index.max() for v in loaded.values()).isoformat()}
    assert coverage == manifest["true_oos_coverage"]


def test_oos_boundary_duplicate_and_non_monotonic_rejection() -> None:
    with pytest.raises(ValueError, match="DEVELOPMENT"):
        primary.validate_true_oos_candles(_bars(pd.date_range("2024-12-31 23:55", periods=2, freq="5min", tz="Europe/Moscow")))
    stamp = pd.Timestamp("2025-01-02", tz="Europe/Moscow")
    with pytest.raises(ValueError, match="ORDER_OR_DUPLICATE"):
        primary.validate_true_oos_candles(_bars(pd.DatetimeIndex([stamp, stamp])))
    with pytest.raises(ValueError, match="ORDER_OR_DUPLICATE"):
        primary.validate_true_oos_candles(_bars(pd.date_range(stamp, periods=2, freq="5min")[::-1]))


def test_primary_immutability_and_recorded_determinism() -> None:
    before = hash_tree(PRIMARY)
    frozen_one, frozen_two = verify_provenance(), verify_provenance()
    assert frozen_one["primary_tree_hash"] == frozen_two["primary_tree_hash"] == before
    assert frozen_one["walk_forward_hash"] == frozen_two["walk_forward_hash"]
    assert hash_tree(PRIMARY) == before


def test_completed_manifest_has_required_safety_flags_when_present() -> None:
    path = Path("TradingSystemLab/results/true_oos_validation/M5_EXPERIMENTAL_EMA50_NORMAL/manifest.json")
    if not path.exists():
        pytest.skip("real comparator has not been run")
    manifest = json.loads(path.read_text())
    assert manifest["pre_registered_before_true_oos"] is True
    for key in ("primary_candidate", "production_candidate_selection", "optimization_performed", "ranking_performed",
                "parameter_change", "strategy_change", "session_change", "ema_threshold_change", "candidate_reselection",
                "true_oos_used_for_training", "true_oos_used_for_optimization", "true_oos_used_for_selection",
                "primary_m5_true_oos_artifacts_modified"):
        assert manifest[key] is False
