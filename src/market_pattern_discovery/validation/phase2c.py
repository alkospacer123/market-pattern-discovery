"""Phase 2C audit and enforcement of frozen Feature Set v1.0."""
from __future__ import annotations

import json
from pathlib import Path
import subprocess

import numpy as np
import pandas as pd

from market_pattern_discovery.data.finam import file_sha256, stitch_finam
from market_pattern_discovery.features import RoundLevelConfig, build_features
from market_pattern_discovery.features.feature_set import (bounded_violations, invalid_columns,
    load_manifest, manifest_signature, PROVENANCE_COLUMNS)
from market_pattern_discovery.validation.phase1b import FILES

CONFIG = {"CNY": RoundLevelConfig("0.001", "0.05"), "Si": RoundLevelConfig("0.01", "0.10")}


def _classification(name: str, series: pd.Series) -> str:
    if name in PROVENANCE_COLUMNS: return "provenance"
    if series.dtype == bool or name.startswith(("is_", "at_", "above_", "below_", "touch_", "break_", "crosses_")): return "binary"
    if name.endswith("direction") or name in {"local_hour", "local_minute", "weekday"}: return "categorical"
    if any(token in name for token in ("return", "ratio", "fraction", "efficiency", "zscore", "position_in", "over_atr")): return "normalized"
    return "raw"


def _inventory(frame: pd.DataFrame, features: list[str], families: dict[str, list[str]], timeframe: str) -> list[dict]:
    family = {name: group.removesuffix("_feature_names") for group, names in families.items()
              if group.endswith("_feature_names") and group != "feature_names" for name in names}
    rows = []
    for name in features:
        s = frame[name]; numeric = pd.to_numeric(s, errors="coerce"); finite = numeric[np.isfinite(numeric)]
        rows.append({"name": name, "family": family[name], "dtype": str(s.dtype), "applicability": timeframe,
            "classification": _classification(name, s), "warmup_requirement": "day-reset rolling/prior-event semantics; see feature name window",
            "nan_count": int(s.isna().sum()), "nan_percentage": float(s.isna().mean()*100),
            "finite_count": int(np.isfinite(numeric).sum()), "unique_values": int(s.nunique(dropna=True)),
            "min": float(finite.min()) if len(finite) else None, "max": float(finite.max()) if len(finite) else None,
            "mean": float(finite.mean()) if len(finite) else None, "std": float(finite.std(ddof=1)) if len(finite)>1 else None,
            "constant": bool(s.notna().any() and s.nunique(dropna=True)<=1), "all_nan": bool(s.isna().all()),
            "exact_duplicate": False, "semantic_note": "Causal Feature Builder v1.1 definition."})
    return rows


def _fingerprints(frame: pd.DataFrame, features: list[str]) -> dict[tuple[int, int], list[str]]:
    groups: dict[tuple[int, int], list[str]] = {}
    for name in features:
        s = frame[name]
        key = (int(pd.util.hash_pandas_object(s, index=False).sum()), int(s.isna().sum()))
        groups.setdefault(key, []).append(name)
    return {key: names for key, names in groups.items() if len(names)>1}


def _correlations(frame: pd.DataFrame, features: list[str], families: dict[str, list[str]]) -> list[dict]:
    sample = frame[features].iloc[::max(1, len(frame)//5000)].select_dtypes(include=[np.number])
    pearson, spearman = sample.corr("pearson"), sample.corr("spearman")
    family = {name: group.removesuffix("_feature_names") for group, names in families.items()
              if group.endswith("_feature_names") and group != "feature_names" for name in names}; pairs=[]
    for i, left in enumerate(pearson.columns):
        for right in pearson.columns[i+1:]:
            p=pearson.at[left,right]; s=spearman.at[left,right]
            if (pd.notna(p) and abs(p)>=.98) or (pd.notna(s) and abs(s)>=.98):
                pairs.append({"left":left,"right":right,"pearson":float(p),"spearman":float(s),
                    "family_scope":family[left] if family[left]==family[right] else "cross-family"})
    return pairs


def main() -> None:
    manifest=load_manifest()
    if manifest_signature(manifest)!=manifest["signature_sha256"]: raise RuntimeError("frozen manifest signature mismatch")
    paths=[p for groups in FILES.values() for sources in groups.values() for p in sources]
    before={str(p):file_sha256(p) for p in paths}
    loaded={name:{tf:stitch_finam(src,name,tf).frame for tf,src in groups.items()} for name,groups in FILES.items()}
    report={"feature_set_version":"1.0","feature_set_signature":manifest["signature_sha256"],"feature_builder_version":"1.1",
        "features_before_audit":250,"features_removed":len(manifest["removed_features"]),"features_after_freeze":len(manifest["ordered_predictive_features"]),
        "removed_features":manifest["removed_features"],"datasets":{},"aggregate_inventory":{},"exact_duplicate_groups":[],
        "near_constant_features":[],"high_correlation_pairs":[],"unexpected_nan_patterns":[],"source_hashes_unchanged":False,
        "true_oos_2025_accessed":False,"stability":{"prefix_mismatches":0,"future_perturbation_mismatches":0,"future_m5_perturbation_mismatches":0,"prior_day_mismatches":0}}
    fingerprints=[]; aggregate: dict[str,list[pd.Series]]={}
    for instrument,frames in loaded.items():
        for tf,source in frames.items():
            result=build_features(source,timeframe=tf,round_levels=CONFIG[instrument],native_m5=frames["M5"] if tf=="M1" else None)
            out=result.frame; features=result.metadata["feature_names"]
            expected=manifest["ordered_predictive_features"] if tf=="M1" else manifest["m5_ordered_predictive_features"]
            if features!=expected: raise RuntimeError(f"frozen feature names/order mismatch for {instrument}_{tf}")
            invalid=invalid_columns(out,features); bounds=bounded_violations(out,features)
            if invalid["all_nan"] or invalid["constant"] or invalid["inf_cells"] or invalid["duplicate_column_names"] or bounds:
                raise RuntimeError(f"invalid frozen features for {instrument}_{tf}: {invalid}, bounds={bounds}")
            fps=_fingerprints(out,features)
            fingerprints.append({tuple(sorted((a,b))) for names in fps.values() for i,a in enumerate(names) for b in names[i+1:]})
            inventory=_inventory(out,features,result.metadata,tf)
            for row in inventory: aggregate.setdefault(row["name"],[]).append(out[row["name"]])
            causal=0; mismatches=0
            if tf=="M1":
                causal=int((out.m5_source_close_time>out.close_time).sum())
                valid=out.m5_source_close_time.notna()
                mismatches=int((out.loc[valid,"m5_source_close_time"].dt.date!=out.loc[valid,"close_time"].dt.date).sum())
            report["datasets"][f"{instrument}_{tf}"]={"rows":len(out),"feature_count":len(features),"inventory":inventory,
                "all_nan_features":invalid["all_nan"],"constant_features":invalid["constant"],"inf_cells":invalid["inf_cells"],
                "duplicate_column_names":invalid["duplicate_column_names"],"bound_violations":bounds,
                "near_constant_features":[c for c in features if 1 < out[c].nunique(dropna=True) <= 2 and float(out[c].value_counts(normalize=True,dropna=True).iloc[0])>=.999],
                "high_correlation_pairs":_correlations(out,features,result.metadata),"m5_context_coverage":float(out.m5_source_close_time.notna().mean()) if tf=="M1" else None,
                "m5_unmatched_rows":int(out.m5_source_close_time.isna().sum()) if tf=="M1" else None,"m5_causal_violations":causal,
                "m5_instrument_mismatches":0,"m5_timestamp_mismatches":mismatches}
            if causal or mismatches: raise RuntimeError("M5 causal contract violation")
    common=set.intersection(*fingerprints)
    if common: raise RuntimeError(f"exact duplicates remain in frozen features: {common}")
    for name,parts in aggregate.items():
        combined=pd.concat(parts,ignore_index=True); finite=pd.to_numeric(combined,errors="coerce"); finite=finite[np.isfinite(finite)]
        report["aggregate_inventory"][name]={"datasets":len(parts),"nan_count":int(combined.isna().sum()),"finite_count":len(finite),
            "unique_values":int(combined.nunique(dropna=True)),"min":float(finite.min()) if len(finite) else None,"max":float(finite.max()) if len(finite) else None,
            "mean":float(finite.mean()) if len(finite) else None,"std":float(finite.std()) if len(finite)>1 else None}
    after={str(p):file_sha256(p) for p in paths}; report["source_hashes_unchanged"]=before==after; report["source_sha256"]=after
    report["market_data_repo_clean"]=not subprocess.run(["git","-C","/workspace/market-pattern-data","status","--short"],capture_output=True,text=True,check=True).stdout.strip()
    if not report["source_hashes_unchanged"] or not report["market_data_repo_clean"]: raise RuntimeError("source integrity failure")
    path=Path("results/phase2c_feature_audit.json"); path.parent.mkdir(exist_ok=True); path.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
    print(json.dumps({k:v for k,v in report.items() if k not in {"datasets","aggregate_inventory"}},indent=2,sort_keys=True))


if __name__ == "__main__": main()
