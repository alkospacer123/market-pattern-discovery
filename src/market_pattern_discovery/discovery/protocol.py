"""Frozen, target-independent Pattern Discovery Protocol v1 utilities."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from market_pattern_discovery.research.protocol import AccessMode, load_protocol, protocol_signature, request_access

ROOT = Path(__file__).resolve().parents[3]
PATH = ROOT / "config" / "discovery_protocol_v1.json"


def _canonical(value: dict[str, Any]) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()


def discovery_signature(value: dict[str, Any]) -> str:
    unsigned = {key: item for key, item in value.items() if key != "signature_sha256"}
    return hashlib.sha256(_canonical(unsigned)).hexdigest()


def load_discovery_protocol(path: Path = PATH) -> dict[str, Any]:
    value = json.loads(path.read_text())
    if value.get("signature_sha256") != discovery_signature(value):
        raise ValueError("Discovery Protocol signature drift")
    required = value["required_signatures"]
    feature = json.loads((ROOT / "config/feature_set_v1.json").read_text())
    behavior = json.loads((ROOT / "config/behavior_target_set_v1.json").read_text())
    research = load_protocol()
    actual = {"feature_set": feature["signature_sha256"], "behavior_target_set": behavior["signature_sha256"], "research_protocol": protocol_signature(research)}
    if required != actual:
        raise ValueError("frozen input signature drift")
    return value


def quantile_states(values: pd.Series, cut_probabilities=(.1, .25, .75, .9)) -> tuple[pd.Series, tuple[float, ...]]:
    """Fit deterministic cutpoints once; ties go into the lower interval."""
    numeric = pd.to_numeric(values, errors="coerce")
    cuts = tuple(float(x) for x in numeric.dropna().quantile(cut_probabilities).to_numpy())
    labels = np.array(["LE_P10", "P10_P25", "P25_P75", "P75_P90", "GE_P90"], dtype=object)
    state = pd.Series("MISSING", index=values.index, dtype="object")
    valid = numeric.notna()
    state.loc[valid] = labels[np.searchsorted(np.asarray(cuts), numeric.loc[valid], side="left")]
    return state, cuts


def categorical_states(values: pd.Series) -> pd.Series:
    return values.astype("object").where(values.notna(), "MISSING")


def apply_cutpoints(values: pd.Series, cuts: tuple[float, ...]) -> pd.Series:
    if len(cuts) != 4:
        raise ValueError("v1 requires four frozen cutpoints")
    return quantile_states_with_cuts(values, cuts)


def quantile_states_with_cuts(values: pd.Series, cuts: tuple[float, ...]) -> pd.Series:
    numeric = pd.to_numeric(values, errors="coerce")
    labels = np.array(["LE_P10", "P10_P25", "P25_P75", "P75_P90", "GE_P90"], dtype=object)
    result = pd.Series("MISSING", index=values.index, dtype="object")
    result.loc[numeric.notna()] = labels[np.searchsorted(cuts, numeric.dropna(), side="left")]
    return result


def continuous_effect(candidate: np.ndarray, baseline: np.ndarray) -> dict[str, float]:
    a, b = np.asarray(candidate, float), np.asarray(baseline, float)
    a, b = a[np.isfinite(a)], b[np.isfinite(b)]
    if not len(a) or not len(b): raise ValueError("effect samples must be nonempty")
    superiority = (a[:, None] > b).mean() + .5 * (a[:, None] == b).mean()
    scale = np.std(b, ddof=1) if len(b) > 1 else np.nan
    return {"mean_difference": float(a.mean()-b.mean()), "median_difference": float(np.median(a)-np.median(b)),
            "standardized_mean_shift": float((a.mean()-b.mean())/scale) if scale > 0 else np.nan,
            "probability_of_superiority": float(superiority), "q25_shift": float(np.quantile(a,.25)-np.quantile(b,.25)), "q75_shift": float(np.quantile(a,.75)-np.quantile(b,.75))}


def binary_effect(candidate: np.ndarray, baseline: np.ndarray) -> dict[str, float]:
    pa, pb = float(np.mean(candidate)), float(np.mean(baseline))
    odds_a, odds_b = pa/(1-pa) if pa < 1 else np.inf, pb/(1-pb) if pb < 1 else np.inf
    return {"probability_difference": pa-pb, "relative_risk": pa/pb if pb else np.nan,
            "odds_ratio": odds_a/odds_b if odds_b and np.isfinite(odds_b) else np.nan}


def day_block_bootstrap(frame: pd.DataFrame, mask: pd.Series, target: str, statistic: str = "median_difference", *, replications: int = 1000, seed: int = 20260401) -> dict[str, Any]:
    """Resample complete Moscow trading dates; overlapping rows never split."""
    if "moscow_trading_date" not in frame: raise ValueError("Moscow trading date is required")
    days = pd.unique(frame["moscow_trading_date"]); rng = np.random.default_rng(seed); estimates=[]
    numeric = pd.to_numeric(frame[target], errors="coerce").to_numpy(float)
    membership = mask.to_numpy(bool)
    blocks = [(numeric[pos := np.flatnonzero(frame["moscow_trading_date"].eq(day).to_numpy())], membership[pos]) for day in days]
    for _ in range(replications):
        chosen = rng.integers(0, len(blocks), len(blocks))
        b = np.concatenate([blocks[index][0] for index in chosen])
        a = np.concatenate([blocks[index][0][blocks[index][1]] for index in chosen])
        a, b = a[np.isfinite(a)], b[np.isfinite(b)]
        if statistic == "probability_difference": estimates.append(float(np.mean(a)-np.mean(b)))
        elif statistic == "mean_difference": estimates.append(float(np.mean(a)-np.mean(b)))
        elif statistic == "rank_effect": estimates.append(continuous_effect(a,b)["probability_of_superiority"]-.5)
        else: estimates.append(float(np.median(a)-np.median(b)))
    values=np.asarray(estimates); return {"method":"moscow_trading_date_resampling","replications":replications,"seed":seed,"lower":float(np.quantile(values,.025)),"upper":float(np.quantile(values,.975)),"standard_error":float(values.std(ddof=1))}


def benjamini_hochberg(p_values) -> np.ndarray:
    p=np.asarray(p_values,float); result=np.full(p.shape,np.nan); valid=np.flatnonzero(np.isfinite(p))
    if np.any((p[valid] < 0) | (p[valid] > 1)): raise ValueError("p-values must be in [0, 1]")
    order=valid[np.argsort(p[valid],kind="stable")]; m=len(order)
    if m:
        ranked=p[order]*m/np.arange(1,m+1); adjusted=np.minimum.accumulate(ranked[::-1])[::-1]; result[order]=np.minimum(adjusted,1)
    return result


def exact_mask_dedupe(masks: list[np.ndarray]) -> tuple[list[int], dict[int, int]]:
    kept=[]; duplicate_of={}; seen={}
    for index, mask in enumerate(masks):
        key=np.asarray(mask,bool).tobytes()
        if key in seen: duplicate_of[index]=seen[key]
        else: seen[key]=index; kept.append(index)
    return kept, duplicate_of


def validate_rule(conditions: list[dict], maximum_depth: int = 3) -> None:
    if not conditions or len(conditions) > maximum_depth: raise ValueError("rule depth outside preregistered v1 contract")
    if any("threshold" in condition for condition in conditions): raise ValueError("arbitrary threshold optimization is forbidden")


def capped_feature_pairs(features: list[str], maximum: int, families: dict[str,str] | None=None) -> list[tuple[str,str]]:
    unique=sorted(set(features)); pairs=[]
    for i,a in enumerate(unique):
        for b in unique[i+1:]:
            if families is None or families.get(a) != families.get(b): pairs.append((a,b))
            if len(pairs) == maximum: return pairs
    return pairs


def fold_effects(frame: pd.DataFrame, mask: pd.Series, target: str, folds: list[dict], definition_source: str) -> list[dict]:
    timestamps=pd.to_datetime(frame["timestamp"],utc=True); output=[]
    for fold in folds:
        start,end=map(pd.Timestamp,fold["validate"]); rows=(timestamps>=start)&(timestamps<end); selected=rows&mask
        effect=np.nan if not selected.any() else float(frame.loc[selected,target].median()-frame.loc[rows,target].median())
        output.append({"fold_id":fold["fold_id"],"definition_source":definition_source,"validation_block":fold["validate"],"effect":effect,"coverage":float(selected.sum()/rows.sum()) if rows.sum() else 0.0,"days":int(frame.loc[selected,"moscow_trading_date"].nunique())})
    return output


def replication_semantics(pattern_definition: dict) -> str:
    return "not_tested" if pattern_definition.get("representation") in {"quantile_state","normalized_feature","categorical"} else "not_applicable"


def screen_effect(record: dict, policy: dict) -> tuple[bool,list[str]]:
    failures=[]
    if record["coverage"] < policy["minimum_coverage"]: failures.append("coverage")
    if record["unique_days"] < policy["minimum_unique_days"]: failures.append("unique_days")
    uncertainty=record.get("uncertainty",{}); values=[uncertainty.get("lower"),uncertainty.get("upper")]
    if policy["finite_uncertainty"] and not all(np.isfinite(values)): failures.append("uncertainty")
    if policy["multiplicity_complete"] and not record.get("multiplicity_family"): failures.append("multiplicity")
    # ``primary_effect_signed`` is the one canonical signed effect emitted and
    # persisted by evaluate_hypothesis.  Keeping screening on that field avoids
    # a second value which could silently drift from the scientific result.
    primary_effect = record["effect_metrics"]["primary_effect_signed"]
    effects=[x.get("effect",np.nan) for x in record.get("fold_results",[])]; sign=np.sign(primary_effect)
    if sum(np.sign(x)==sign for x in effects if np.isfinite(x)) < policy["require_same_sign_folds"]: failures.append("temporal_stability")
    threshold=policy["practical_effect_thresholds"][record["target_family"]]
    if abs(primary_effect) < threshold: failures.append("practical_effect")
    if record.get("invalidity") or record.get("leakage"): failures.append("invalidity")
    return not failures, failures


def authorize_experiment(experiment: dict) -> None:
    protocol=load_discovery_protocol(); required={"experiment_id","research_track","experiment_type","access_mode","feature_set_signature","behavior_target_signature","research_protocol_signature","method","target_family","feature_scope","multiplicity_family","seed","period"}
    missing=required-experiment.keys()
    if missing: raise ValueError(f"unregistered discovery call: missing {sorted(missing)}")
    if experiment["access_mode"] != "DISCOVERY" or experiment["method"] not in protocol["allowed_methods"]: raise PermissionError("only preregistered DISCOVERY methods are allowed")
    expected=protocol["required_signatures"]
    if (experiment["feature_set_signature"],experiment["behavior_target_signature"],experiment["research_protocol_signature"]) != (expected["feature_set"],expected["behavior_target_set"],expected["research_protocol"]): raise ValueError("experiment signature drift")
    if experiment["seed"] != protocol["bootstrap"]["seed"]: raise ValueError("seed drift")
    request_access(AccessMode.DISCOVERY, tuple(experiment["period"]))


def deterministic_kmeans(features: np.ndarray, k: int, seed: int=20260401, iterations: int=30) -> np.ndarray:
    """Small dependency-free feature-only clustering reference implementation."""
    x=np.asarray(features,float)
    if not np.isfinite(x).all(): raise ValueError("clustering input must follow frozen missingness handling")
    rng=np.random.default_rng(seed); centers=x[rng.choice(len(x),k,replace=False)].copy()
    for _ in range(iterations):
        labels=((x[:,None,:]-centers[None,:,:])**2).sum(2).argmin(1)
        new=np.vstack([x[labels==i].mean(0) if np.any(labels==i) else centers[i] for i in range(k)])
        if np.array_equal(new,centers): break
        centers=new
    return labels
