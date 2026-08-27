"""Effect-record and fully-lined candidate contracts."""
from __future__ import annotations

import copy
from typing import Any

REQUIRED_LINEAGE = {"effect_id","experiment_id","method","pattern_definition","target_behavior","discovery_data_period","signatures","code_commit"}


def validate_effect_record(record: dict[str, Any]) -> None:
    required={"effect_id","experiment_id","method","pattern_definition","feature_conditions","target_behavior","instrument","timeframe","sample_size","unique_days","coverage","baseline_size","baseline_distribution","candidate_distribution","effect_metrics","uncertainty","raw_p","adjusted_q","fold_results","replication_result","multiplicity_family","rank_within_experiment","screening_status","candidate_id"}
    missing=required-record.keys()
    if missing: raise ValueError(f"effect record missing {sorted(missing)}")
    from market_pattern_discovery.discovery.execution_contract import validate_screening_status
    validate_screening_status(record["screening_status"])


def create_candidate_from_effect(effect: dict[str, Any], *, code_commit: str, signatures: dict[str,str], discovery_data_period: list[str], directory=None) -> dict[str, Any]:
    """Persist a promoted effect through the one canonical research registry."""
    from market_pattern_discovery.discovery.execution_contract import load_execution_contract
    from market_pattern_discovery.research import registry
    validate_effect_record(effect)
    if effect["screening_status"] != "promoted": raise ValueError("only promoted effects may be candidates")
    required={"hypothesis_id","feature_conditions","target_family","target_role","contrast","effect_metrics","fold_results","replication_result","uncertainty"}
    missing=required-effect.keys()
    if missing: raise ValueError(f"candidate effect lineage missing {sorted(missing)}")
    metrics=effect["effect_metrics"]
    if not {"primary_effect_signed","primary_effect_absolute"} <= metrics.keys(): raise ValueError("signed and absolute primary effects are required")
    execution=load_execution_contract()
    lineage={"hypothesis_id":effect["hypothesis_id"],"effect_id":effect["effect_id"],"experiment_id":effect["experiment_id"],"method":effect["method"],"instrument":effect["instrument"],"timeframe":effect["timeframe"],"pattern_definition":copy.deepcopy(effect["pattern_definition"]),"feature_conditions":copy.deepcopy(effect["feature_conditions"]),"target_behavior":effect["target_behavior"],"target_family":effect["target_family"],"target_role":effect["target_role"],"horizon":effect.get("horizon"),"contrast":effect["contrast"],"discovery_interval":list(discovery_data_period),"sample_size":effect["sample_size"],"unique_days":effect["unique_days"],"coverage":effect["coverage"],"primary_effect_signed":metrics["primary_effect_signed"],"primary_effect_absolute":metrics["primary_effect_absolute"],"uncertainty":copy.deepcopy(effect["uncertainty"]),"raw_p":effect["raw_p"],"adjusted_q":effect["adjusted_q"],"walk_forward_summary":copy.deepcopy(effect["fold_results"]),"replication_result":copy.deepcopy(effect["replication_result"]),"upstream_signatures":dict(signatures),"discovery_execution_signature":execution["signature_sha256"],"code_commit":code_commit}
    spec={"source_experiment_id":effect["experiment_id"],"research_track":"unknown_discovery","instrument_scope":effect["instrument"],"timeframe_scope":effect["timeframe"],"behavior_target":effect["target_behavior"],"direction_of_effect":metrics["primary_effect_signed"],"discovery_sample_size":effect["sample_size"],"discovery_effect_summary":lineage,"notes":"Phase 5B promoted effect; registry lifecycle begins discovered",**copy.deepcopy(lineage)}
    value=registry.create_candidate(spec, directory=registry.CANDIDATES if directory is None else directory)
    value.update({"effect_id":effect["effect_id"],"experiment_id":effect["experiment_id"],"method":effect["method"],"target_behavior":effect["target_behavior"],"discovery_data_period":list(discovery_data_period),"signatures":dict(signatures),"code_commit":code_commit})
    validate_candidate_lineage(value)
    return value

def validate_candidate_lineage(candidate: dict[str, Any]) -> None:
    missing=REQUIRED_LINEAGE-candidate.keys()
    if missing: raise ValueError(f"candidate lineage missing {sorted(missing)}")


def freeze_for_confirmation(candidate: dict[str, Any]) -> dict[str, Any]:
    validate_candidate_lineage(candidate); result=copy.deepcopy(candidate); result["status"]="frozen_for_confirmation"; result["frozen_definition"]=True; result["definition_at_freeze"]=copy.deepcopy(result["pattern_definition"]); return result


def assert_candidate_immutable(original: dict[str, Any], proposed: dict[str, Any]) -> None:
    if original.get("frozen_definition") and proposed.get("pattern_definition") != original.get("definition_at_freeze",original["pattern_definition"]):
        raise ValueError("frozen candidate definition changed; create a new Candidate ID")
