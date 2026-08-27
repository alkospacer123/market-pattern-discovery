"""Contract-only validator for Representative Target Mapping v1.0."""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

from market_pattern_discovery.discovery.target_mapping import (
    FAMILIES,
    TIMEFRAMES,
    fdr_family_key,
    hypothesis_units,
    load_discovery_target_mapping,
    mapped_targets,
    mapping_signature,
    validate_mapping_against_behavior_set,
    verify_phase5b_contracts,
)

ROOT = Path(__file__).resolve().parents[3]


def validate() -> dict:
    mapping = load_discovery_target_mapping()
    validate_mapping_against_behavior_set(mapping)
    discovery_signature, target_mapping_signature = verify_phase5b_contracts()
    safety = mapping["safety_attestations"]
    if any(safety.values()):
        raise AssertionError("research-safety attestation violated")
    if fdr_family_key(instrument="CNYRUBF", timeframe="M1", discovery_method="RULE",
                      target_family="PATH", semantic_role="LONG_PATH_EFFICIENCY", horizon=60) \
            != "CNYRUBF|M1|RULE|PATH|LONG_PATH_EFFICIENCY@H60":
        raise AssertionError("FDR key is not deterministic")
    # This scan is deliberately limited to contract/runtime code. It never opens market rows.
    forbidden = ("feature_target_correlation", "profit_factor", "true_oos_2025.csv",
                 "internal_confirmation.csv")
    scanned = [ROOT / "config/discovery_target_mapping_v1.json",
               ROOT / "src/market_pattern_discovery/discovery/target_mapping.py"]
    for path in scanned:
        lowered = path.read_text().lower()
        if any(term in lowered for term in forbidden):
            raise AssertionError(f"forbidden discovery construct in {path}")
    market_status = subprocess.run(
        ["git", "-C", "/workspace/market-pattern-data", "status", "--short"],
        check=True, capture_output=True, text=True,
    ).stdout
    if market_status:
        raise AssertionError("source market-data repository is not clean")
    counts = {tf: len(mapped_targets(tf, mapping=mapping)) for tf in TIMEFRAMES}
    units = {tf: hypothesis_units(tf, mapping=mapping) for tf in TIMEFRAMES}
    families = {tf: {family: len(mapped_targets(tf, family, mapping))
                     for family in FAMILIES} for tf in TIMEFRAMES}
    return {
        "phase": "5A.1", "status": "PASS",
        "discovery_target_mapping_version": mapping["discovery_target_mapping_version"],
        "discovery_target_mapping_signature": mapping_signature(mapping),
        "discovery_protocol_signature": discovery_signature,
        "frozen_signatures": mapping["required_signatures"],
        "target_column_counts": counts, "hypothesis_units_per_feature_state": units,
        "family_column_counts": families,
        "representative_horizons": mapping["representative_horizons"],
        "mapped_column_existence_check": True, "timeframe_applicability_check": True,
        "removed_column_check": True, "duplicate_mapping_check": True,
        "hypothesis_accounting_deterministic": True, "fdr_grouping_complete": True,
        "feature_outcome_relationships_analyzed": False, "real_discovery_run": False,
        "internal_confirmation_accessed": False, "true_oos_2025_accessed": False,
        "profitability_used": False, "market_data_repo_clean": True,
        "scanned_contract_files": [str(path.relative_to(ROOT)) for path in scanned],
    }


def main() -> None:
    print(json.dumps(validate(), indent=2, sort_keys=True))
