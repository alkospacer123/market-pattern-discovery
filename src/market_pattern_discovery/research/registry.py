"""Version-control-friendly immutable experiment and candidate registries."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from market_pattern_discovery.features.feature_set import load_manifest, manifest_signature
from market_pattern_discovery.targets.behavior_target_set import load_behavior_target_set

ROOT = Path(__file__).resolve().parents[3]
EXPERIMENTS = ROOT / "research" / "experiments"
CANDIDATES = ROOT / "research" / "candidates"
TRACKS = {"unknown_discovery", "known_hypothesis"}
EXPERIMENT_REQUIRED = {"research_track", "research_stage", "description", "instrument_scope", "timeframe_scope",
 "discovery_period", "confirmation_period", "feature_set_version", "feature_set_signature",
 "behavior_target_set_version", "behavior_target_signature", "code_commit", "method", "method_version",
 "input_feature_subset", "output_behavior_subset", "hyperparameters", "intended_effect_metric", "statistical_test",
 "number_of_hypotheses_tested",
 "multiple_testing_family", "status", "candidate_ids_created", "notes"}

def _next_id(directory: Path, prefix: str) -> str:
    directory.mkdir(parents=True, exist_ok=True)
    used = [int(p.stem.split("-")[1]) for p in directory.glob(f"{prefix}-[0-9][0-9][0-9][0-9][0-9][0-9].json")]
    return f"{prefix}-{max(used, default=0) + 1:06d}"

def _write_new(path: Path, value: dict) -> None:
    try:
        with path.open("x") as stream: json.dump(value, stream, indent=2, sort_keys=True); stream.write("\n")
    except FileExistsError as exc:
        raise ValueError("registered specifications are immutable; create a new ID") from exc

def _validate_signatures(spec: dict) -> None:
    feature = load_manifest(); behavior = load_behavior_target_set()
    if not spec.get("feature_set_signature") or not spec.get("behavior_target_signature"):
        raise ValueError("feature and behavior signatures are required")
    if spec["feature_set_signature"] != manifest_signature(feature): raise ValueError("Feature Set signature mismatch")
    if spec["behavior_target_signature"] != behavior["signature_sha256"]: raise ValueError("Behavior/Target Set signature mismatch")

def register_experiment(specification: dict[str, Any], directory: Path = EXPERIMENTS) -> dict[str, Any]:
    missing = EXPERIMENT_REQUIRED - specification.keys()
    if missing: raise ValueError(f"missing experiment fields: {sorted(missing)}")
    if specification["research_track"] not in TRACKS: raise ValueError("invalid research track")
    if specification["research_track"] == "known_hypothesis" and not specification.get("hypothesis_id"):
        raise ValueError("known hypothesis experiments require hypothesis_id")
    if specification["research_track"] == "unknown_discovery" and specification.get("hypothesis_id"):
        raise ValueError("unknown discovery may not be retroactively assigned a hypothesis")
    if not isinstance(specification["number_of_hypotheses_tested"], int) or specification["number_of_hypotheses_tested"] < 1:
        raise ValueError("number_of_hypotheses_tested must be a positive integer")
    _validate_signatures(specification)
    value = dict(specification); value["experiment_id"] = _next_id(directory, "EXP")
    value["created_at"] = datetime.now(timezone.utc).isoformat(); value.setdefault("parent_experiment_id", None)
    _write_new(directory / f"{value['experiment_id']}.json", value)
    return value

def load_experiment(experiment_id: str, directory: Path = EXPERIMENTS) -> dict[str, Any]:
    return json.loads((directory / f"{experiment_id}.json").read_text())

def list_experiments(directory: Path = EXPERIMENTS) -> list[dict[str, Any]]:
    return [json.loads(path.read_text()) for path in sorted(directory.glob("EXP-*.json"))]

def finalize_experiment(experiment_id: str, *, status: str, candidate_ids_created: list[str],
                        results_reference: str | None = None, directory: Path = EXPERIMENTS) -> dict[str, Any]:
    """Write a separate finalization record; never modify the preregistration."""
    original = load_experiment(experiment_id, directory)
    path = directory / f"{experiment_id}.final.json"
    value = {"experiment_id": experiment_id, "specification_created_at": original["created_at"],
             "finalized_at": datetime.now(timezone.utc).isoformat(), "status": status,
             "candidate_ids_created": list(candidate_ids_created), "results_reference": results_reference}
    _write_new(path, value); return value

def create_candidate(specification: dict[str, Any], directory: Path = CANDIDATES) -> dict[str, Any]:
    required = {"source_experiment_id", "research_track", "pattern_definition", "instrument_scope", "timeframe_scope",
                "behavior_target", "direction_of_effect", "discovery_sample_size", "discovery_effect_summary", "notes"}
    missing = required - specification.keys()
    if missing: raise ValueError(f"missing candidate fields: {sorted(missing)}")
    if specification["research_track"] not in TRACKS: raise ValueError("invalid research track")
    value = dict(specification); value.update({"candidate_id": _next_id(directory, "CAND"),
        "created_at": datetime.now(timezone.utc).isoformat(), "frozen_definition": False, "status": "discovered",
        "internal_confirmation_accessed": False, "internal_confirmation_result": None,
        "true_oos_2025_accessed": False, "interpretation": None})
    _write_new(directory / f"{value['candidate_id']}.json", value); return value

def transition_candidate(candidate: dict[str, Any], new_status: str, protocol: dict[str, Any]) -> dict[str, Any]:
    allowed = protocol["candidate_lifecycle"].get(candidate["status"], [])
    if new_status not in allowed: raise ValueError(f"invalid candidate transition {candidate['status']} -> {new_status}")
    updated = dict(candidate); updated["status"] = new_status
    if new_status == "frozen_for_confirmation": updated["frozen_definition"] = True
    return updated
