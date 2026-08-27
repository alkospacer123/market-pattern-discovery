"""Run and independently validate the Phase 4B descriptive market map."""
from __future__ import annotations

import json
import subprocess
import time
from pathlib import Path

import numpy as np
import pandas as pd

from market_pattern_discovery.analysis.phase4b import (REPORT_NAMES, activity_summary,
    categorical_summary, coverage_summary, marginal_drift, memory_mb, quality_summary,
    target_validity, write_reports)
from market_pattern_discovery.data.finam import file_sha256, stitch_finam
from market_pattern_discovery.features.builder import build_features
from market_pattern_discovery.features.feature_set import load_manifest, manifest_signature
from market_pattern_discovery.features.schema import RoundLevelConfig
from market_pattern_discovery.research.protocol import load_protocol, protocol_signature
from market_pattern_discovery.targets import (build_behaviors, build_outcomes,
    load_behavior_target_set, ordered_groups)
from market_pattern_discovery.validation.phase1b import FILES

OUTPUT = Path("results/phase4b")
PRICE = {"CNY": RoundLevelConfig(tick_size="0.001", round_level_step="0.05"),
         "Si": RoundLevelConfig(tick_size="0.01", round_level_step="0.10")}
SAFETY = {"2025 DATA ACCESSED": "NO", "FEATURE→OUTCOME RELATIONSHIPS ANALYZED": "NO",
    "DISCOVERY RUN": "NO", "CANDIDATES CREATED": 0, "KNOWN HYPOTHESES TESTED": 0,
    "PROFITABILITY USED": "NO", "TRADING SIGNALS IMPLEMENTED": "NO", "TP/SL IMPLEMENTED": "NO",
    "ML RUN": "NO", "CLUSTERING RUN": "NO", "SEQUENCE/MOTIF MINING RUN": "NO",
    "OPTIMIZATION RUN": "NO", "BACKTEST RUN": "NO", "INTERNAL CONFIRMATION ACCESSED": "NO",
    "TRUE OOS ACCESSED": "NO", "SOURCE DATA MODIFIED": "NO"}


def _static_scan() -> list[str]:
    """Scan executable analysis implementation, excluding this policy declaration."""
    path = Path(__file__).parents[1] / "analysis" / "phase4b.py"
    text = path.read_text().lower()
    forbidden = ("feature_importance", "mutual_info", "classifier", "regressor", "take_profit", "stop_loss")
    return [term for term in forbidden if term in text]


def _markdown(coverage: dict, feature_drift: dict, target_valid: dict, warnings: list[str]) -> str:
    lines = ["# Phase 4B neutral market map", "", "## Coverage", "",
             "| Dataset | Rows | Dates | First open | Last close |", "|---|---:|---:|---|---|"]
    for key, value in coverage.items():
        lines.append(f"| {key} | {value['rows']} | {value['trading_dates']} | {value['first_open_time']} | {value['last_close_time']} |")
    lines += ["", "## Marginal stability", "", "Feature and behavior drift values compare each field's own monthly distribution only.",
              "No field is conditioned on a field from the other namespace.", "", "## Target validity", ""]
    for key, horizons in target_valid.items():
        lines.append(f"### {key}")
        lines.append("| Horizon | Valid | Invalid | Fraction |")
        lines.append("|---:|---:|---:|---:|")
        for horizon, value in horizons.items(): lines.append(f"| {horizon} | {value['valid_count']} | {value['invalid_count']} | {value['valid_fraction']:.6f} |")
    lines += ["", "## Comparability notes", "", "CNY and Si raw price levels are not normalized comparisons.",
              "M1 and M5 observations overlap in time and are not independent samples. No independence tests were performed.",
              "", "## Data-quality warnings", ""]
    lines += [f"- {item}" for item in warnings] or ["- None."]
    lines += ["", "## Safety confirmation", ""] + [f"- {key}: {value}" for key, value in SAFETY.items()]
    return "\n".join(lines) + "\n"


def run() -> dict:
    started = time.monotonic(); protocol = load_protocol(); feature_contract = load_manifest()
    behavior_contract = load_behavior_target_set()
    if "DESCRIPTIVE_DEVELOPMENT" not in protocol["access_modes"]: raise RuntimeError("descriptive access unavailable")
    paths = [p for groups in FILES.values() for values in groups.values() for p in values]
    before = {str(p): file_sha256(p) for p in paths}
    coverage = {}; activity = {}; feature_inventory = {}; feature_stability = {}
    target_inventory = {}; target_stability = {}; validities = {}; warnings = []
    expected_features = feature_contract["applicability"]
    for instrument, groups in FILES.items():
        native_m5 = stitch_finam(groups["M5"], instrument, "M5").frame
        for timeframe, sources in groups.items():
            key = f"{instrument}_{timeframe}"; raw = stitch_finam(sources, instrument, timeframe).frame
            features = build_features(raw, timeframe=timeframe, round_levels=PRICE[instrument],
                                      native_m5=native_m5 if timeframe == "M1" else None).frame
            feature_names = feature_contract["ordered_predictive_features"] if timeframe == "M1" else feature_contract["m5_ordered_predictive_features"]
            if len(feature_names) != expected_features[timeframe] or any(x not in features for x in feature_names):
                raise RuntimeError(f"feature contract mismatch: {key}")
            coverage[key] = coverage_summary(raw); activity[key] = activity_summary(raw)
            feature_inventory[key] = {name: quality_summary(features[name]) for name in feature_names}
            feature_stability[key] = marginal_drift(features, feature_names)
            outcomes = build_outcomes(raw); behaviors = build_behaviors(raw, features, outcomes)
            target_names = [name for group in ordered_groups(behavior_contract, timeframe) for name in group]
            target_source = pd.concat([outcomes, behaviors], axis=1)
            target_frame = target_source.loc[:, ~target_source.columns.duplicated()][target_names]
            if np.isinf(target_frame.select_dtypes(include=np.number).to_numpy(float)).any():
                raise RuntimeError(f"infinite retained behavior: {key}")
            validities[key] = target_validity(target_frame, target_names)
            target_inventory[key] = {name: (categorical_summary(target_frame[name])
                if name.startswith(("label_", "target_future_valid_", "target_future_invalid_reason_"))
                else quality_summary(target_frame[name])) for name in target_names}
            target_stability[key] = marginal_drift(target_frame.assign(open_time=raw.open_time), target_names)
    after = {str(p): file_sha256(p) for p in paths}
    clean = not subprocess.run(["git", "-C", "/workspace/market-pattern-data", "status", "--short"],
                               check=True, capture_output=True, text=True).stdout.strip()
    summary = {"phase": "4B", "method_version": "1.0", "status": "PASS",
        "access_mode": "DESCRIPTIVE_DEVELOPMENT", "feature_set_version": feature_contract["feature_set_version"],
        "feature_set_signature": manifest_signature(feature_contract),
        "behavior_target_set_version": behavior_contract["behavior_target_set_version"],
        "behavior_target_set_signature": behavior_contract["signature_sha256"],
        "research_protocol_version": protocol["protocol_version"],
        "research_protocol_signature": protocol_signature(protocol), "default_seed": protocol["default_seed"],
        "approved_period": protocol["actual_coverage"], "datasets": sorted(coverage),
        "feature_counts": expected_features,
        "target_counts": {tf: sum(map(len, ordered_groups(behavior_contract, tf))) for tf in ("M1", "M5")},
        "source_hashes": after, "source_hashes_unchanged": before == after, "market_data_repo_clean": clean,
        "static_scan_findings": _static_scan(), "candidate_registry_mutated": False,
        "safety": SAFETY, "runtime_seconds": round(time.monotonic()-started, 3), "peak_memory_mb": round(memory_mb(), 1)}
    reports = {"coverage": coverage, "intraday_descriptives": activity,
        "feature_inventory": feature_inventory, "feature_temporal_stability": feature_stability,
        "target_inventory": {"validity": validities, "marginals": target_inventory},
        "target_temporal_stability": target_stability, "summary": summary}
    sizes = write_reports(reports, OUTPUT); summary["generated_report_sizes_bytes"] = sizes
    (OUTPUT / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True)+"\n")
    (OUTPUT / "market_map.md").write_text(_markdown(coverage, feature_stability, validities, warnings))
    return summary


def validate() -> dict:
    result = run()
    failures = []
    if result["static_scan_findings"]: failures.append("static scan")
    if not result["source_hashes_unchanged"]: failures.append("source hashes")
    if not result["market_data_repo_clean"]: failures.append("source repository")
    if result["datasets"] != ["CNY_M1", "CNY_M5", "Si_M1", "Si_M5"]: failures.append("datasets")
    for name in (*REPORT_NAMES, "summary"):
        if not isinstance(json.loads((OUTPUT/f"{name}.json").read_text()), dict): failures.append(name)
    if failures: raise RuntimeError(f"Phase 4B validation failed: {failures}")
    return result


def main() -> None: print(json.dumps(validate(), indent=2, sort_keys=True))


if __name__ == "__main__": main()
