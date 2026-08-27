from __future__ import annotations

import json
from pathlib import Path

import pytest

from market_pattern_discovery.features.feature_set import load_manifest, manifest_signature
from market_pattern_discovery.research.protocol import (AccessMode, assert_discovery_period,
    assert_true_oos_not_accessed, deterministic_seed, load_protocol, protocol_signature, request_access)
from market_pattern_discovery.research.registry import (create_candidate, finalize_experiment, list_experiments,
    load_experiment, register_experiment, transition_candidate)
from market_pattern_discovery.targets.behavior_target_set import load_behavior_target_set

DISCOVERY = ("2026-02-01T00:00:00Z", "2026-03-01T00:00:00Z")
CONFIRMATION = ("2026-06-01T00:00:00Z", "2026-06-02T00:00:00Z")

def experiment(**updates):
    feature, behavior = load_manifest(), load_behavior_target_set()
    value = {"research_track": "unknown_discovery", "research_stage": "preregistered", "description": "synthetic",
      "instrument_scope": "CNY", "timeframe_scope": "M1_with_native_M5_context", "discovery_period": list(DISCOVERY),
      "confirmation_period": list(CONFIRMATION), "feature_set_version": "1.0", "feature_set_signature": manifest_signature(feature),
      "behavior_target_set_version": "1.0", "behavior_target_signature": behavior["signature_sha256"], "code_commit": "abc",
      "method": "synthetic", "method_version": "1", "random_seed": deterministic_seed(), "input_feature_subset": ["x"],
      "output_behavior_subset": ["y"], "hyperparameters": {}, "intended_effect_metric": "difference", "statistical_test": "none",
      "number_of_hypotheses_tested": 1,
      "multiple_testing_family": "synthetic-family", "status": "registered", "parent_experiment_id": None,
      "candidate_ids_created": [], "notes": "test"}
    value.update(updates); return value

def candidate():
    return {"candidate_id": "CAND-000001", "status": "frozen_for_confirmation", "frozen_definition": True}

def test_protocol_signature_deterministic():
    p = load_protocol(); assert protocol_signature(p) == protocol_signature(json.loads(json.dumps(p)))

def test_discovery_accepts_only_discovery_period():
    assert_discovery_period(DISCOVERY)
    with pytest.raises(PermissionError): assert_discovery_period(CONFIRMATION)

def test_confirmation_requires_frozen_candidate_and_audits(tmp_path):
    audit = tmp_path / "audit.jsonl"
    with pytest.raises(PermissionError): request_access(AccessMode.INTERNAL_CONFIRMATION, CONFIRMATION, audit_path=audit)
    request_access(AccessMode.INTERNAL_CONFIRMATION, CONFIRMATION, candidate=candidate(), audit_path=audit)
    with pytest.raises(PermissionError): request_access(AccessMode.INTERNAL_CONFIRMATION, DISCOVERY, candidate=candidate(), audit_path=audit)
    records = [json.loads(x) for x in audit.read_text().splitlines()]
    assert [r["approved"] for r in records] == [False, True, False]

def test_true_oos_guard_uses_synthetic_period_only(tmp_path):
    with pytest.raises(PermissionError): assert_true_oos_not_accessed(("2025-01-01T00:00:00Z", "2025-02-01T00:00:00Z"))
    with pytest.raises(PermissionError): request_access(AccessMode.TRUE_OOS,
        ("2025-01-01T00:00:00Z", "2025-02-01T00:00:00Z"), candidate=candidate(), audit_path=tmp_path/"audit")

def test_descriptive_mode_allows_2026_but_not_predictive_selection():
    request_access(AccessMode.DESCRIPTIVE_DEVELOPMENT, DISCOVERY)
    assert "predictive feature-to-outcome" in load_protocol()["access_modes"]["DESCRIPTIVE_DEVELOPMENT"]

def test_lifecycle_forward_and_backward_rejection():
    p = load_protocol(); c = {"status": "discovered", "frozen_definition": False}
    c = transition_candidate(c, "screened", p); c = transition_candidate(c, "frozen_for_confirmation", p)
    assert c["frozen_definition"]
    with pytest.raises(ValueError): transition_candidate(c, "discovered", p)

def test_registry_immutable_and_new_id_required(tmp_path):
    first = register_experiment(experiment(), tmp_path); assert load_experiment(first["experiment_id"], tmp_path) == first
    second = register_experiment(experiment(description="changed"), tmp_path)
    assert (first["experiment_id"], second["experiment_id"]) == ("EXP-000001", "EXP-000002")
    finalize_experiment(first["experiment_id"], status="done", candidate_ids_created=[], directory=tmp_path)
    with pytest.raises(ValueError): finalize_experiment(first["experiment_id"], status="changed", candidate_ids_created=[], directory=tmp_path)

def test_finalization_is_separate(tmp_path):
    first = register_experiment(experiment(), tmp_path); before = load_experiment(first["experiment_id"], tmp_path)
    finalize_experiment(first["experiment_id"], status="complete", candidate_ids_created=[], directory=tmp_path)
    assert load_experiment(first["experiment_id"], tmp_path) == before

def test_known_unknown_separation(tmp_path):
    with pytest.raises(ValueError): register_experiment(experiment(hypothesis_id="KH-X-001"), tmp_path)
    known = experiment(research_track="known_hypothesis", hypothesis_id="KH-X-001")
    assert register_experiment(known, tmp_path)["research_track"] == "known_hypothesis"

def test_deterministic_seed(): assert deterministic_seed() == 20260401 == load_protocol()["default_seed"]

@pytest.mark.parametrize("field", ["feature_set_signature", "behavior_target_signature"])
def test_missing_signatures_rejected(tmp_path, field):
    value = experiment(); value.pop(field)
    with pytest.raises(ValueError): register_experiment(value, tmp_path)

@pytest.mark.parametrize("field", ["feature_set_signature", "behavior_target_signature"])
def test_signature_mismatch_rejected(tmp_path, field):
    with pytest.raises(ValueError): register_experiment(experiment(**{field: "0" * 64}), tmp_path)

def test_candidate_defaults_and_ids(tmp_path):
    spec = {"source_experiment_id": "EXP-000001", "research_track": "unknown_discovery", "pattern_definition": "machine rule",
      "instrument_scope": "CNY", "timeframe_scope": "M1", "behavior_target": "behavior_x", "direction_of_effect": "positive",
      "discovery_sample_size": {"raw_observation_count": 10, "unique_trading_days": 2}, "discovery_effect_summary": {}, "notes": ""}
    value = create_candidate(spec, tmp_path)
    assert value["candidate_id"] == "CAND-000001" and value["true_oos_2025_accessed"] is False and value["interpretation"] is None

def test_list_experiments_is_id_sorted(tmp_path):
    register_experiment(experiment(), tmp_path); register_experiment(experiment(), tmp_path)
    assert [x["experiment_id"] for x in list_experiments(tmp_path)] == ["EXP-000001", "EXP-000002"]
