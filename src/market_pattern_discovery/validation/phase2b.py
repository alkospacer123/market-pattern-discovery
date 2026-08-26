"""Read-only validation of Feature Builder v1.1 on enumerated 2026 data."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess

import numpy as np
import pandas as pd

from market_pattern_discovery.data.finam import file_sha256, stitch_finam
from market_pattern_discovery.features import RoundLevelConfig, build_features
from market_pattern_discovery.validation.phase1b import FILES

CONFIG = {"CNY": RoundLevelConfig("0.001", "0.05"),
          "Si": RoundLevelConfig("0.01", "0.10")}


def parse_args() -> argparse.Namespace:
    return argparse.ArgumentParser(description="Validate causal Phase 2B features on approved 2026 files.").parse_args()


def _mismatches(left: pd.DataFrame, right: pd.DataFrame) -> int:
    common = left.select_dtypes(include=[np.number]).columns.intersection(right.columns)
    a, b = left[common].reset_index(drop=True), right[common].reset_index(drop=True)
    return int((~(a.eq(b) | (a.isna() & b.isna()))).to_numpy().sum())


def main() -> None:
    parse_args()
    paths = [p for groups in FILES.values() for sources in groups.values() for p in sources]
    before = {str(p): file_sha256(p) for p in paths}
    loaded = {name: {tf: stitch_finam(sources, name, tf).frame for tf, sources in groups.items()}
              for name, groups in FILES.items()}
    report = {"feature_builder_version": "1.1", "datasets": {}, "source_hashes_unchanged": False,
              "true_oos_2025_accessed": False,
              "price_configuration": {name: {"tick_size": cfg.tick_size,
                  "round_level_step": cfg.round_level_step,
                  "round_level_step_ticks": cfg.round_level_step_ticks} for name, cfg in CONFIG.items()}}
    for name, frames in loaded.items():
        for tf, source in frames.items():
            result = build_features(source, timeframe=tf, round_levels=CONFIG[name],
                                    native_m5=frames["M5"] if tf == "M1" else None)
            out, meta = result.frame, result.metadata
            features = meta["feature_names"]
            vals = out[features].select_dtypes(include=[np.number]).to_numpy(float)
            # Bounded causal checks keep validation repeatable without multiplying
            # full-dataset memory while numerical checks above cover every row.
            cutoff = min(1000, len(source) // 2)
            prefix = build_features(source.iloc[:cutoff].copy(), timeframe=tf, round_levels=CONFIG[name],
                                    native_m5=frames["M5"] if tf == "M1" else None).frame
            prefix_mismatch = _mismatches(out.iloc[:cutoff], prefix)
            future_m5_mismatch = 0
            if tf == "M1":
                cutoff_time = source.iloc[cutoff-1].close_time
                changed_m5 = frames["M5"].copy()
                mask = changed_m5.close_time > cutoff_time
                changed_m5.loc[mask, ["open", "high", "low", "close", "volume"]] *= 10
                perturbed = build_features(source.iloc[:cutoff].copy(), timeframe=tf, round_levels=CONFIG[name], native_m5=changed_m5).frame
                future_m5_mismatch = _mismatches(prefix, perturbed)
            violations = int((out.m5_source_close_time > out.close_time).sum()) if tf == "M1" else 0
            report["datasets"][f"{name}_{tf}"] = {
                "input_rows": len(source), "output_rows": len(out), "phase2a_feature_count": len(meta["phase2a_feature_names"]),
                "structure_feature_count": len(meta["structure_feature_names"]),
                "round_level_feature_count": len(meta["round_level_feature_names"]),
                "m5_context_feature_count": len(meta["m5_context_feature_names"]),
                "cross_timeframe_feature_count": len(meta["cross_timeframe_feature_names"]),
                "total_feature_count": len(features), "nan_cells": int(np.isnan(vals).sum()),
                "inf_cells": int(np.isinf(vals).sum()), "duplicate_feature_names": len(features)-len(set(features)),
                "constant_columns": [c for c in out[features].select_dtypes(include=[np.number]) if out[c].nunique(dropna=True) <= 1],
                "m5_context_coverage": float(out.m5_source_close_time.notna().mean()) if tf == "M1" else None,
                "m5_rows_unavailable": int(out.m5_source_close_time.isna().sum()) if tf == "M1" else None,
                "m5_causal_violations": violations, "prefix_mismatches": prefix_mismatch,
                "future_m5_perturbation_mismatches": future_m5_mismatch,
            }
            if len(out) != len(source) or np.isinf(vals).any() or prefix_mismatch or future_m5_mismatch or violations:
                raise RuntimeError(f"Phase 2B validation failure for {name}_{tf}")
            del result, out, vals, prefix
    after = {str(p): file_sha256(p) for p in paths}
    if before != after:
        raise RuntimeError("source hashes changed")
    report["source_hashes_unchanged"] = True; report["source_sha256"] = after
    report["market_data_repo_clean"] = not subprocess.run(
        ["git", "-C", "/workspace/market-pattern-data", "status", "--short"], capture_output=True, text=True, check=True).stdout.strip()
    path = Path("results/phase2b_feature_validation.json"); path.parent.mkdir(exist_ok=True)
    path.write_text(json.dumps(report, indent=2, sort_keys=True)+"\n")
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
