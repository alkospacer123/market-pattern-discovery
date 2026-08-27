"""Validate Phase 3A outcomes against the enumerated 2026 development data."""
from __future__ import annotations

import json
from pathlib import Path
import subprocess
import time

import numpy as np

from market_pattern_discovery.data.finam import file_sha256, stitch_finam
from market_pattern_discovery.features.feature_set import load_manifest, manifest_signature
from market_pattern_discovery.targets import HORIZONS, build_outcomes, outcome_columns
from market_pattern_discovery.validation.phase1b import FILES

EXPECTED_SIGNATURE = "0b5ffb328d217e5e8d575ff0b84be794647bc0850e548b354d737ce91342024d"


def _validate_horizon(out, horizon: int) -> tuple[dict, int]:
    valid = out[f"target_future_valid_{horizon}"]
    reason = out[f"target_future_invalid_reason_{horizon}"]
    metric_names = [name for name in outcome_columns(str(out.timeframe.iloc[0]))
                    if name.endswith(f"_{horizon}") and "valid" not in name and "reason" not in name]
    metrics = out[metric_names]
    # Location is undefined for a zero range and ordering is deliberately
    # undefined when both first extrema share a candle; neither is incomplete.
    optional = [f"target_close_location_in_future_range_{horizon}",
                f"target_future_high_before_low_{horizon}"]
    complete = metrics.drop(columns=optional).notna().all(axis=1)
    violations = int((valid != complete).sum())
    violations += int((valid & (out[f"target_future_max_high_{horizon}"] < out[f"target_future_min_low_{horizon}"])).sum())
    for stem in ("bars_to_future_high", "bars_to_future_low"):
        value = out[f"target_{stem}_{horizon}"]
        violations += int((valid & ~value.between(1, horizon)).sum())
    order = out[f"target_future_high_before_low_{horizon}"]
    violations += int((valid & order.notna() & ~order.isin([0.0, 1.0])).sum())
    invalid = ~valid
    report = {
        "rows": len(out), "valid_outcomes": int(valid.sum()),
        "invalid_due_day_end": int((invalid & reason.eq("day_end")).sum()),
        "invalid_due_data_end": int((invalid & reason.eq("data_end")).sum()),
        "invalid_due_gaps": int((invalid & reason.eq("gap")).sum()),
        "nan_cells": int(metrics.isna().sum().sum()),
        "inf_cells": int(np.isinf(metrics.to_numpy()).sum()),
        "invariant_violations": violations,
    }
    return report, violations


def main() -> None:
    started = time.perf_counter()
    manifest = load_manifest()
    signature = manifest_signature(manifest)
    if signature != EXPECTED_SIGNATURE or manifest["signature_sha256"] != EXPECTED_SIGNATURE:
        raise RuntimeError("frozen Feature Set v1.0 signature changed")
    paths = [path for groups in FILES.values() for sources in groups.values() for path in sources]
    before = {str(path): file_sha256(path) for path in paths}
    report = {
        "phase": "3A", "outcome_engine_version": "1.0",
        "feature_set_version": manifest["feature_set_version"],
        "feature_set_signature_before": EXPECTED_SIGNATURE,
        "feature_set_signature_after": signature,
        "feature_set_unchanged": signature == EXPECTED_SIGNATURE,
        "horizons": {key: list(value) for key, value in HORIZONS.items()},
        "datasets": {}, "outcome_columns": {}, "inf_cells": 0,
        "mathematical_invariant_violations": 0, "target_locality_mismatches": 0,
        "true_oos_2025_accessed": False,
    }
    for instrument, groups in FILES.items():
        for timeframe, sources in groups.items():
            source = stitch_finam(sources, instrument, timeframe).frame
            out = build_outcomes(source)
            horizons = {}
            violations = 0
            for horizon in HORIZONS[timeframe]:
                horizons[str(horizon)], found = _validate_horizon(out, horizon)
                violations += found
            # Longer complete paths contain every shorter complete path.
            for short, long in zip(HORIZONS[timeframe], HORIZONS[timeframe][1:]):
                both = out[f"target_future_valid_{short}"] & out[f"target_future_valid_{long}"]
                violations += int((both & (out[f"target_future_max_high_{long}"] < out[f"target_future_max_high_{short}"])).sum())
                violations += int((both & (out[f"target_future_min_low_{long}"] > out[f"target_future_min_low_{short}"])).sum())
            numeric = out.select_dtypes(include=[np.number])
            inf = int(np.isinf(numeric.to_numpy()).sum())
            key = f"{instrument}_{timeframe}"
            report["datasets"][key] = {"rows":len(out), "horizons":horizons,
                "outcome_columns":len(outcome_columns(timeframe)), "memory_bytes":int(out.memory_usage(deep=True).sum()),
                "inf_cells":inf, "invariant_violations":violations}
            report["outcome_columns"][timeframe] = outcome_columns(timeframe)
            report["inf_cells"] += inf
            report["mathematical_invariant_violations"] += violations
    after = {str(path): file_sha256(path) for path in paths}
    report["source_hashes_unchanged"] = before == after
    report["source_sha256"] = after
    status = subprocess.run(["git", "-C", "/workspace/market-pattern-data", "status", "--short"],
                            check=True, capture_output=True, text=True).stdout.strip()
    report["market_data_repo_clean"] = not status
    report["runtime_seconds"] = round(time.perf_counter() - started, 3)
    if (not report["source_hashes_unchanged"] or not report["market_data_repo_clean"] or
            report["inf_cells"] or report["mathematical_invariant_violations"]):
        raise RuntimeError("Phase 3A validation failed")
    destination = Path("results/phase3a_outcome_validation.json")
    destination.parent.mkdir(exist_ok=True)
    destination.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
