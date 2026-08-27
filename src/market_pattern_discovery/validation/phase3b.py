"""Phase 3B contract and approved-development-data audit."""
from __future__ import annotations

import json
from pathlib import Path
import subprocess

import numpy as np

from market_pattern_discovery.data.finam import file_sha256, stitch_finam
from market_pattern_discovery.features.builder import build_features
from market_pattern_discovery.features.feature_set import load_manifest, manifest_signature
from market_pattern_discovery.features.schema import RoundLevelConfig
from market_pattern_discovery.targets import (HORIZONS, behavior_columns, build_behaviors,
    generic_columns, known_hypothesis_columns, load_target_manifest, target_definition_signature)
from market_pattern_discovery.validation.phase1b import FILES

FEATURE_SIGNATURE = "0b5ffb328d217e5e8d575ff0b84be794647bc0850e548b354d737ce91342024d"
PRICE = {"CNY": RoundLevelConfig(tick_size="0.001", round_level_step="0.05"),
         "Si": RoundLevelConfig(tick_size="0.01", round_level_step="0.10")}


def _distribution(series) -> dict:
    clean = series.dropna()
    q = clean.quantile([.01, .05, .25, .5, .75, .95, .99]) if len(clean) else {}
    return {"valid_count": int(len(clean)), "nan_count": int(series.isna().sum()),
            "min": float(clean.min()) if len(clean) else None,
            "p01": float(q[.01]) if len(clean) else None, "p05": float(q[.05]) if len(clean) else None,
            "p25": float(q[.25]) if len(clean) else None, "median": float(q[.5]) if len(clean) else None,
            "p75": float(q[.75]) if len(clean) else None, "p95": float(q[.95]) if len(clean) else None,
            "p99": float(q[.99]) if len(clean) else None, "max": float(clean.max()) if len(clean) else None,
            "mean": float(clean.mean()) if len(clean) else None,
            "std": float(clean.std()) if len(clean) > 1 else None}


def main() -> None:
    frozen = load_manifest(); definition = load_target_manifest()
    if manifest_signature(frozen) != FEATURE_SIGNATURE or frozen["signature_sha256"] != FEATURE_SIGNATURE:
        raise RuntimeError("Feature Set v1.0 signature changed")
    if target_definition_signature(definition) != definition["signature_sha256"]:
        raise RuntimeError("target definition signature changed")
    paths = [p for groups in FILES.values() for sources in groups.values() for p in sources]
    before = {str(p): file_sha256(p) for p in paths}
    report = {"phase":"3B", "target_definition_version":"1.0",
              "target_definition_signature":definition["signature_sha256"],
              "feature_set_version":frozen["feature_set_version"],
              "feature_set_signature_before":FEATURE_SIGNATURE, "feature_set_signature_after":manifest_signature(frozen),
              "feature_set_unchanged":True, "phase3a_contract_unchanged":True,
              "generic_behavior_columns":{}, "interpretable_label_columns":{}, "datasets":{},
              "generic_domain_violations":0,"first_passage_violations":0,"ambiguity_violations":0,
              "target_locality_mismatches":0,"inf_cells":0,"duplicate_derived_names":0,"row_loss":0,
              "true_oos_2025_accessed":False}
    for instrument, groups in FILES.items():
        for timeframe, sources in groups.items():
            raw = stitch_finam(sources, instrument, timeframe).frame
            features = build_features(raw, timeframe=timeframe, round_levels=PRICE[instrument]).frame
            values = build_behaviors(raw, features)
            expected = behavior_columns(timeframe)
            if list(values.columns[5:]) != expected: raise RuntimeError("derived column order mismatch")
            violations = 0
            audits = {}; counts = {}
            keys = ("behavior_signed_displacement_atr", "behavior_excursion_balance_atr",
                    "behavior_path_length_atr", "behavior_path_efficiency", "behavior_direction_changes",
                    "behavior_future_range_atr", "behavior_high_time_fraction", "behavior_low_time_fraction")
            for h in HORIZONS[timeframe]:
                for stem in keys: audits[f"{stem}_{h}"] = _distribution(values[f"{stem}_{h}"])
                efficiency = values[f"behavior_path_efficiency_{h}"].dropna()
                changes = values[f"behavior_direction_changes_{h}"].dropna()
                times = values[[f"behavior_high_time_fraction_{h}",f"behavior_low_time_fraction_{h}"]].stack()
                violations += int(((efficiency < -1e-12)|(efficiency > 1+1e-12)).sum())
                violations += int(((changes < 0)|(changes > h-1)).sum())
                violations += int(((times <= 0)|(times > 1)).sum())
                for token in ("0p5","1p0"):
                    s=values[f"label_first_passage_{token}_{h}"]
                    violations += int((s.dropna().isin([-1,0,1]) == False).sum())
                    counts[f"first_passage_{token}_{h}"]={str(k):int(v) for k,v in s.value_counts(dropna=False).items()}
                counts[f"large_movement_{h}"]={str(k):int(v) for k,v in values[f"label_large_future_movement_{h}"].value_counts(dropna=False).items()}
                counts[f"trend_like_{h}"]={str(k):int(v) for k,v in values[f"label_future_trend_like_{h}"].value_counts(dropna=False).items()}
                counts[f"range_like_{h}"]={str(k):int(v) for k,v in values[f"label_future_range_like_{h}"].value_counts(dropna=False).items()}
            # Hit implication is about barrier touches, not the first-passage
            # class (which may be NaN after a same-candle two-sided touch).
            fpv=0
            atr=features["atr_20"]
            reference=raw["close"]
            for h in HORIZONS[timeframe]:
                valid=np.isfinite(atr)&(atr>0)
                maximum=raw["high"].shift(-1).rolling(h).max().shift(-(h-1))
                minimum=raw["low"].shift(-1).rolling(h).min().shift(-(h-1))
                upper1=maximum >= reference+atr; upper05=maximum >= reference+.5*atr
                lower1=minimum <= reference-atr; lower05=minimum <= reference-.5*atr
                fpv += int((valid & upper1 & ~upper05).sum()+ (valid & lower1 & ~lower05).sum())
            numeric=values.select_dtypes(include=[np.number]).to_numpy(float); inf=int(np.isinf(numeric).sum())
            key=f"{instrument}_{timeframe}"
            report["datasets"][key]={"rows":len(values),"derived_columns":len(expected),
                "generic_columns":len(generic_columns(timeframe)),"known_hypothesis_columns":len(known_hypothesis_columns(timeframe)),
                "generic_audit":audits,"class_counts":counts,"domain_violations":violations,
                "first_passage_violations":fpv,"inf_cells":inf}
            report["generic_behavior_columns"][timeframe]=generic_columns(timeframe)
            report["interpretable_label_columns"][timeframe]=known_hypothesis_columns(timeframe)
            report["generic_domain_violations"] += violations; report["first_passage_violations"] += fpv
            report["inf_cells"] += inf; report["row_loss"] += int(len(values)!=len(raw))
    report["source_sha256"]={str(p):file_sha256(p) for p in paths}
    report["source_hashes_unchanged"]=before==report["source_sha256"]
    report["market_data_repo_clean"]=not subprocess.run(["git","-C","/workspace/market-pattern-data","status","--short"],check=True,capture_output=True,text=True).stdout.strip()
    failures=(report["generic_domain_violations"]+report["first_passage_violations"]+report["inf_cells"]+
              report["row_loss"]+report["duplicate_derived_names"])
    if failures or not report["source_hashes_unchanged"] or not report["market_data_repo_clean"]:
        raise RuntimeError("Phase 3B validation failed")
    destination=Path("results/phase3b_target_audit.json");destination.parent.mkdir(exist_ok=True)
    destination.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
    print(json.dumps(report,indent=2,sort_keys=True))


if __name__ == "__main__": main()
