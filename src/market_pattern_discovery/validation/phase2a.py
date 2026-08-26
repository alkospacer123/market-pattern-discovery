"""Read-only validation of Phase 2A features on enumerated 2026 development data."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from market_pattern_discovery.data.finam import file_sha256, stitch_finam
from market_pattern_discovery.features import build_core_features
from market_pattern_discovery.validation.phase1b import FILES


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate causal Phase 2A core features on approved 2026 data only.")
    return parser.parse_args()


def _summary(source: pd.DataFrame, timeframe: str) -> tuple[dict, int]:
    built = build_core_features(source, timeframe=timeframe)
    output, metadata = built.frame, built.metadata
    features = metadata["feature_names"]
    numeric_features = output[features].select_dtypes(include=[np.number])
    values = numeric_features.to_numpy(dtype=float)
    mismatches = 0
    cutoff_reports = []
    for cutoff in (len(source) // 4, len(source) // 2, 3 * len(source) // 4):
        prefix = build_core_features(source.iloc[:cutoff].copy(), timeframe=timeframe).frame
        left = output.loc[:cutoff - 1, features].reset_index(drop=True)
        right = prefix[features].reset_index(drop=True)
        try:
            pd.testing.assert_frame_equal(left, right, check_exact=True)
            count = 0
        except AssertionError:
            count = int((~(left.eq(right) | (left.isna() & right.isna()))).to_numpy().sum())
        mismatches += count
        cutoff_reports.append({"rows": cutoff, "mismatches": count})
    finite = values[np.isfinite(values)]
    first_valid = {}
    for window in metadata["configured_windows"]["rolling"]:
        valid = output[f"atr_{window}"].first_valid_index()
        first_valid[str(window)] = None if valid is None else output.loc[valid, "close_time"].isoformat()
    report = {
        "input_rows": len(source), "output_rows": len(output), "feature_count": len(features),
        "numeric_feature_cells": int(values.size), "nan_cells": int(np.isnan(values).sum()),
        "inf_cells": int(np.isinf(values).sum()),
        "constant_feature_columns": [c for c in numeric_features if numeric_features[c].nunique(dropna=True) <= 1],
        "duplicate_feature_names": len(features) - len(set(features)), "first_valid_timestamp": first_valid,
        "feature_value_min": None if not finite.size else float(finite.min()),
        "feature_value_max": None if not finite.size else float(finite.max()),
        "memory_bytes": int(output.memory_usage(index=True, deep=True).sum()),
        "prefix_checks": cutoff_reports, "prefix_mismatches": mismatches,
    }
    if len(output) != len(source) or report["inf_cells"] or report["duplicate_feature_names"] or mismatches:
        raise RuntimeError(f"Phase 2A validation failure: {report}")
    return report, mismatches


def main() -> None:
    parse_args()
    paths = [path for groups in FILES.values() for paths in groups.values() for path in paths]
    before = {str(path): file_sha256(path) for path in paths}
    report: dict = {"feature_builder_version": "1.0", "datasets": {}, "prefix_invariance_mismatches": 0,
                    "true_oos_2025_accessed": False}
    for instrument, groups in FILES.items():
        for timeframe, sources in groups.items():
            frame = stitch_finam(sources, instrument, timeframe).frame
            summary, mismatches = _summary(frame, timeframe)
            report["datasets"][f"{instrument}_{timeframe}"] = summary
            report["prefix_invariance_mismatches"] += mismatches
    after = {str(path): file_sha256(path) for path in paths}
    if before != after:
        raise RuntimeError("source hashes changed")
    report["source_hashes_unchanged"] = True
    report["source_sha256"] = after
    output = Path("results/phase2a_feature_validation.json")
    output.parent.mkdir(exist_ok=True)
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
