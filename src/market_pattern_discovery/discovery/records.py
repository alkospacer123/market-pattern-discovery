"""Effect-record and fully-lined candidate contracts."""
from __future__ import annotations

import copy
from typing import Any

REQUIRED_LINEAGE = {"effect_id","experiment_id","method","pattern_definition","target_behavior","discovery_data_period","signatures","code_commit"}


def validate_effect_record(record: dict[str, Any]) -> None:
    required={"effect_id","experiment_id","method","pattern_definition","feature_conditions","target_behavior","instrument","timeframe","sample_size","unique_days","coverage","baseline_size","baseline_distribution","candidate_distribution","effect_metrics","uncertainty","raw_p","adjusted_q","fold_results","replication_result","multiplicity_family","rank_within_experiment","screening_status","candidate_id"}
    missing=required-record.keys()
    if missing: raise ValueError(f"effect record missing {sorted(missing)}")


def create_candidate_from_effect(effect: dict[str, Any], *, code_commit: str, signatures: dict[str,str], discovery_data_period: list[str], directory=None) -> dict[str, Any]:
    """Canonical adapter: promoted effect -> persistent research registry candidate."""
    from market_pattern_discovery.research.registry import create_candidate
    import tempfile
    from pathlib import Path
    validate_effect_record(effect)
    if effect["screening_status"] != "promoted": raise ValueError("only promoted effects may be candidates")
    spec={"source_experiment_id":effect["experiment_id"],"research_track":"unknown_discovery","pattern_definition":copy.deepcopy(effect["pattern_definition"]),"instrument_scope":effect["instrument"],"timeframe_scope":effect["timeframe"],"behavior_target":effect["target_behavior"],"direction_of_effect":effect["effect_metrics"]["primary_effect"],"discovery_sample_size":effect["sample_size"],"discovery_effect_summary":{"effect_id":effect["effect_id"],"hypothesis_id":effect.get("hypothesis_id"),"coverage":effect["coverage"],"unique_days":effect["unique_days"],"raw_p":effect["raw_p"],"adjusted_q":effect["adjusted_q"],"signatures":signatures,"discovery_execution_signature":signatures.get("discovery_execution"),"code_commit":code_commit,"discovery_period":discovery_data_period},"notes":"Phase 5B promoted effect; registry lifecycle begins discovered"}
    if directory is None:
        with tempfile.TemporaryDirectory() as tmp:
            value=create_candidate(spec, directory=Path(tmp))
    else:
        value=create_candidate(spec, directory=directory)
    value.update({"effect_id":effect["effect_id"],"experiment_id":effect["experiment_id"],"method":effect["method"],"target_behavior":effect["target_behavior"],"discovery_data_period":discovery_data_period,"signatures":signatures,"code_commit":code_commit})
    return value

def validate_candidate_lineage(candidate: dict[str, Any]) -> None:
    missing=REQUIRED_LINEAGE-candidate.keys()
    if missing: raise ValueError(f"candidate lineage missing {sorted(missing)}")


def freeze_for_confirmation(candidate: dict[str, Any]) -> dict[str, Any]:
    validate_candidate_lineage(candidate); result=copy.deepcopy(candidate); result["status"]="frozen_for_confirmation"; result["frozen_definition"]=True; result["definition_at_freeze"]=copy.deepcopy(result["pattern_definition"]); return result


def assert_candidate_immutable(original: dict[str, Any], proposed: dict[str, Any]) -> None:
    if original.get("frozen_definition") and proposed.get("pattern_definition") != original.get("definition_at_freeze",original["pattern_definition"]):
        raise ValueError("frozen candidate definition changed; create a new Candidate ID")
