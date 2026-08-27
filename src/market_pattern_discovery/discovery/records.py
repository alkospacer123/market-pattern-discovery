"""Effect-record and fully-lined candidate contracts."""
from __future__ import annotations

import copy
from typing import Any

REQUIRED_LINEAGE = {"effect_id","experiment_id","method","pattern_definition","target_behavior","discovery_data_period","signatures","code_commit"}


def validate_effect_record(record: dict[str, Any]) -> None:
    required={"effect_id","experiment_id","method","pattern_definition","feature_conditions","target_behavior","instrument","timeframe","sample_size","unique_days","coverage","baseline_size","baseline_distribution","candidate_distribution","effect_metrics","uncertainty","raw_p","adjusted_q","fold_results","replication_result","multiplicity_family","rank_within_experiment","screening_status","candidate_id"}
    missing=required-record.keys()
    if missing: raise ValueError(f"effect record missing {sorted(missing)}")


def create_candidate_from_effect(effect: dict[str, Any], *, code_commit: str, signatures: dict[str,str], discovery_data_period: list[str]) -> dict[str, Any]:
    validate_effect_record(effect)
    if effect["screening_status"] != "promoted": raise ValueError("only screened effects may be candidates")
    value={"effect_id":effect["effect_id"],"experiment_id":effect["experiment_id"],"method":effect["method"],"pattern_definition":copy.deepcopy(effect["pattern_definition"]),"target_behavior":effect["target_behavior"],"discovery_data_period":discovery_data_period,"signatures":signatures,"code_commit":code_commit,"status":"screened","frozen_definition":False}
    validate_candidate_lineage(value); return value


def validate_candidate_lineage(candidate: dict[str, Any]) -> None:
    missing=REQUIRED_LINEAGE-candidate.keys()
    if missing: raise ValueError(f"candidate lineage missing {sorted(missing)}")


def freeze_for_confirmation(candidate: dict[str, Any]) -> dict[str, Any]:
    validate_candidate_lineage(candidate); result=copy.deepcopy(candidate); result["status"]="frozen_for_confirmation"; result["frozen_definition"]=True; result["definition_at_freeze"]=copy.deepcopy(result["pattern_definition"]); return result


def assert_candidate_immutable(original: dict[str, Any], proposed: dict[str, Any]) -> None:
    if original.get("frozen_definition") and proposed.get("pattern_definition") != original.get("definition_at_freeze",original["pattern_definition"]):
        raise ValueError("frozen candidate definition changed; create a new Candidate ID")
