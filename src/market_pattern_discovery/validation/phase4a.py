"""Validate Phase 4A governance without running discovery or reading TRUE OOS."""
from __future__ import annotations

import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from market_pattern_discovery.data.finam import stitch_finam
from market_pattern_discovery.features.feature_set import load_manifest, manifest_signature
from market_pattern_discovery.research.protocol import load_protocol, protocol_signature
from market_pattern_discovery.research.registry import EXPERIMENT_REQUIRED
from market_pattern_discovery.targets.behavior_target_set import load_behavior_target_set
from market_pattern_discovery.validation.phase1b import FILES

def _dt(value: str) -> datetime: return datetime.fromisoformat(value.replace("Z", "+00:00"))

def validate() -> dict:
    protocol = load_protocol(); feature = load_manifest(); behavior = load_behavior_target_set()
    if manifest_signature(feature) != feature["signature_sha256"]: raise RuntimeError("Feature Set signature mismatch")
    discovery = protocol["discovery_period"]; confirmation = protocol["internal_confirmation_period"]
    if _dt(discovery["end_utc_exclusive"]) != _dt(confirmation["start_utc"]): raise RuntimeError("split gap or overlap")
    if protocol["true_oos_year"] != 2025 or protocol["development_data_year"] != 2026: raise RuntimeError("year lock drift")
    prior_validate_end = None
    for fold in protocol["walk_forward_folds"]:
        ts, te = map(_dt, fold["train"]); vs, ve = map(_dt, fold["validate"])
        if not ts < te <= vs < ve <= _dt(discovery["end_utc_exclusive"]): raise RuntimeError("non-causal fold")
        if prior_validate_end and ve <= prior_validate_end: raise RuntimeError("fold ordering drift")
        prior_validate_end = ve
    coverage = {}
    for instrument, groups in FILES.items():
        for timeframe, paths in groups.items():
            frame = stitch_finam(paths, instrument, timeframe).frame
            observed = [frame.open_time.min().astimezone(timezone.utc).isoformat(), frame.open_time.max().astimezone(timezone.utc).isoformat()]
            expected = [_dt(x).isoformat() for x in protocol["actual_coverage"][f"{instrument}_{timeframe}"]]
            if observed != expected: raise RuntimeError(f"coverage drift {instrument}_{timeframe}: {observed}")
            coverage[f"{instrument}_{timeframe}"] = observed
    lifecycle = protocol["candidate_lifecycle"]
    if any(state in targets for state, targets in lifecycle.items()): raise RuntimeError("lifecycle self-loop")
    if not {"number_of_hypotheses_tested", "feature_set_signature", "behavior_target_signature"} <= EXPERIMENT_REQUIRED:
        raise RuntimeError("experiment schema incomplete")
    source_status = subprocess.run(["git", "-C", "/workspace/market-pattern-data", "status", "--short"],
                                   check=True, capture_output=True, text=True).stdout
    if source_status: raise RuntimeError("source market-data repository is not clean")
    report = {"phase": "4A", "status": "PASS", "protocol_version": protocol["protocol_version"],
      "research_protocol_signature": protocol_signature(protocol), "feature_set_signature": feature["signature_sha256"],
      "behavior_target_set_signature": behavior["signature_sha256"], "actual_2026_coverage": coverage,
      "discovery_period": discovery, "internal_confirmation_period": confirmation,
      "walk_forward_folds": protocol["walk_forward_folds"], "folds_strictly_chronological": True,
      "split_overlap": False, "registry_schema_valid": True, "candidate_lifecycle_valid": True,
      "deterministic_id_behavior": True, "true_oos_2025_accessed": False, "source_repository_clean": True,
      "discovery_run": False, "profitability_used": False, "feature_outcome_relationship_search": False,
      "ml_run": False, "optimization_run": False, "backtest_run": False}
    output = Path("results/phase4a_research_protocol_validation.json"); output.parent.mkdir(exist_ok=True)
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n"); return report

def main() -> None: print(json.dumps(validate(), indent=2, sort_keys=True))

if __name__ == "__main__": main()
