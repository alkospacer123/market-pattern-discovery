"""Signed, target-independent Discovery Execution Contract v1.0 runtime."""
from __future__ import annotations

import hashlib
import itertools
import json
import math
from pathlib import Path
from typing import Any, Iterable, Sequence

import numpy as np
import pandas as pd

from .protocol import apply_cutpoints, benjamini_hochberg, binary_effect, continuous_effect, quantile_states
from market_pattern_discovery.research.protocol import load_protocol, protocol_signature

ROOT = Path(__file__).resolve().parents[3]
PATH = ROOT / "config" / "discovery_execution_v1.json"
METHOD_LETTERS = {"univariate": "U", "interaction": "I", "subgroup": "S"}
SCREENING_STATUSES = frozenset({"enumerated", "ineligible", "evaluated", "screened_out", "screened", "promoted", "duplicate_mask"})
SCREENING_TRANSITIONS = {
    "enumerated": {"ineligible", "evaluated", "duplicate_mask"},
    "ineligible": set(), "evaluated": {"screened_out", "screened"},
    "screened_out": set(), "screened": {"promoted", "screened_out"},
    "promoted": set(), "duplicate_mask": set(),
}

def canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()

def execution_signature(value: dict) -> str:
    return hashlib.sha256(canonical_bytes({k: v for k, v in value.items() if k != "signature_sha256"})).hexdigest()

def load_execution_contract(path: Path = PATH) -> dict:
    value = json.loads(path.read_text())
    if execution_signature(value) != value.get("signature_sha256"):
        raise ValueError("Discovery Execution signature drift")
    files = {"feature_set": "feature_set_v1.json", "behavior_target_set": "behavior_target_set_v1.json", "target_definitions": "target_definitions_v1.json", "discovery_protocol": "discovery_protocol_v1.json", "discovery_target_mapping": "discovery_target_mapping_v1.json"}
    for key, filename in files.items():
        if json.loads((ROOT / "config" / filename).read_text())["signature_sha256"] != value["upstream_signatures"][key]:
            raise ValueError(f"{key} signature drift")
    if protocol_signature(load_protocol()) != value["upstream_signatures"]["research_protocol"]:
        raise ValueError("research_protocol signature drift")
    return value

def feature_inventory(timeframe: str, *, included_only: bool = False, contract: dict | None = None) -> list[dict]:
    rows = (contract or load_execution_contract())["feature_inventory"][timeframe]
    return [row for row in rows if not included_only or row["representation"] != "excluded"]

def canonical_categories(values: Iterable) -> list:
    values = list(values); valid = [x for x in values if not pd.isna(x)]
    return sorted(set(valid), key=canonical_bytes) + (["MISSING"] if any(pd.isna(x) for x in values) else [])

def states_for(entry: dict, categories: Iterable = (), *, contract: dict | None = None) -> list:
    if entry["representation"] == "excluded": return []
    order = (contract or load_execution_contract())["state_order"][entry["representation"]]
    return list(order) if isinstance(order, list) else canonical_categories(categories)

def hypothesis_id(method: str, ordinal: int) -> str:
    if ordinal < 1: raise ValueError("ordinal starts at one")
    return f"HYP-{METHOD_LETTERS[method]}-{ordinal:09d}"

def effect_id(method: str, ordinal: int) -> str:
    return hypothesis_id(method, ordinal).replace("HYP", "EFF", 1)

def _rank(seed: int, *identity: Any) -> str:
    return hashlib.sha256(canonical_bytes([seed, *identity])).hexdigest()

def enumerate_pairs(features: Sequence[str] | Sequence[dict], cap: int = 500, *, timeframe: str = "M1", seed: int = 20260401) -> list[tuple[str, str]]:
    """Hash-rank every eligible i<j pair; input order supplies canonical indices."""
    rows = [({"feature": x, "representation": "continuous_quantile"} if isinstance(x, str) else x) for x in features]
    eligible = [(i, x["feature"]) for i, x in enumerate(rows) if x.get("representation") != "excluded"]
    ranked = [(_rank(seed, timeframe, i, a, j, b), i, j, a, b) for (i, a), (j, b) in itertools.combinations(eligible, 2)]
    ranked.sort()
    return [(a, b) for _, _, _, a, b in ranked[:cap]]

def interaction_states(a: Iterable, b: Iterable) -> list[tuple[Any, Any]]:
    return list(itertools.product(a, b))

def _balanced_combinations(names: list[str], depth: int, seed: int):
    """Yield cyclically balanced combinations lazily; never materialize the universe."""
    canonical_index = {name: index for index, name in enumerate(names)}
    ordered = sorted(names, key=lambda name: _rank(seed, "feature", name))
    n = len(ordered); seen = set()
    offsets = range(1, n) if depth == 2 else itertools.product(range(1, n), repeat=2)
    for offset in offsets:
        gaps = (offset,) if depth == 2 else offset
        for start in range(n):
            indices = [start]
            for gap in gaps: indices.append((indices[-1] + gap) % n)
            if len(set(indices)) != depth: continue
            combo = tuple(sorted((ordered[i] for i in indices), key=canonical_index.__getitem__))
            if combo not in seen:
                seen.add(combo); yield combo
        if len(seen) == math.comb(n, depth): return

def subgroup_rules(features: Sequence[tuple[str, Sequence]], cap: int = 100000, *, seed: int = 20260401, depth2_fraction: float = 0.5) -> list[tuple[tuple[str, Any], ...]]:
    """Coverage-balanced, target-free depth allocation and hash-ranked state rules."""
    clean = [(name, list(states)) for name, states in features if name != "trading_date" and states]
    state_map = dict(clean); names = [x[0] for x in clean]
    allocations = {2: int(cap * depth2_fraction), 3: cap - int(cap * depth2_fraction)}; selected = []
    for depth in (2, 3):
        rules = []
        for combo in _balanced_combinations(names, depth, seed + depth):
            for states in itertools.product(*(state_map[name] for name in combo)):
                rule = tuple(zip(combo, states)); rules.append((_rank(seed, "rule", depth, rule), rule))
                if len(rules) >= allocations[depth] * 4: break
            if len(rules) >= allocations[depth] * 4: break
        rules.sort(key=lambda item: item[0]); selected.extend(rule for _, rule in rules[:allocations[depth]])
    return selected[:cap]

def univariate_count(inventory: list[dict], state_counts: dict[str, int], target_units: int) -> int:
    return sum(state_counts[x["feature"]] for x in inventory if x["representation"] != "excluded") * target_units

def interaction_state_count(pairs, state_counts, target_units):
    return sum(state_counts[a] * state_counts[b] for a, b in pairs) * target_units

def fit_full_discovery(values: pd.Series): return quantile_states(values)
def fit_train_apply_validate(train: pd.Series, validate: pd.Series):
    train_state, cuts = quantile_states(train); return train_state, apply_cutpoints(validate, cuts), cuts

def primary_effect(candidate, baseline, kind="continuous"):
    details = continuous_effect(candidate, baseline) if kind == "continuous" else binary_effect(candidate, baseline)
    signed = details["median_difference" if kind == "continuous" else "probability_difference"]
    return {"primary_effect_signed": signed, "primary_effect_absolute": abs(signed), **details}

def null_p_value(frame: pd.DataFrame, mask: pd.Series, target: str, kind="continuous", replications=1000, seed=20260401):
    """Within-day circular block randomization.

    H0 is invariance to the within-day phase of the complete candidate-membership
    sequence. Each day's mask is circularly shifted against that same day's fixed
    outcomes, preserving row count, mask autocorrelation, day boundaries and row
    identity. Exchangeability assumes phase stationarity within a Moscow day.
    """
    if len(frame) != len(mask) or not frame.index.equals(mask.index): raise ValueError("mask must align exactly with frame rows")
    valid = frame[target].notna(); observed = primary_effect(frame.loc[valid & mask, target], frame.loc[valid, target], kind)["primary_effect_signed"]
    day_positions = [np.flatnonzero(frame["moscow_trading_date"].eq(day).to_numpy()) for day in pd.unique(frame["moscow_trading_date"])]
    original = mask.to_numpy(dtype=bool); rng = np.random.default_rng(seed); null = []
    for _ in range(replications):
        permuted = original.copy()
        for positions in day_positions:
            shift = int(rng.integers(0, len(positions))) if len(positions) > 1 else 0
            permuted[positions] = np.roll(original[positions], shift)
        candidate = valid.to_numpy() & permuted
        if not candidate.any(): null.append(np.nan); continue
        null.append(primary_effect(frame.loc[candidate, target], frame.loc[valid, target], kind)["primary_effect_signed"])
    finite = np.asarray([x for x in null if np.isfinite(x)])
    if len(finite) != replications: raise ValueError("null replication produced an empty candidate sample")
    return float((1 + np.count_nonzero(np.abs(finite) >= abs(observed))) / (replications + 1))

def same_direction_summary(full_effect: float, folds: list[float]) -> dict:
    valid = np.asarray([x for x in folds if np.isfinite(x)]); same = int(np.count_nonzero((np.sign(valid) == np.sign(full_effect)) & (valid != 0) & (full_effect != 0)))
    return {"valid_fold_count": len(valid), "same_direction_fold_count": same, "median_fold_effect": float(np.median(valid)) if len(valid) else np.nan, "worst_signed_fold_effect": float(np.min(valid * np.sign(full_effect))) if len(valid) else np.nan, "fold_effect_dispersion": float(np.std(valid, ddof=1)) if len(valid) > 1 else np.nan}

def validate_screening_status(status: str) -> None:
    if status not in SCREENING_STATUSES: raise ValueError(f"unknown screening status: {status}")
def validate_screening_transition(before: str, after: str) -> None:
    validate_screening_status(before); validate_screening_status(after)
    if after not in SCREENING_TRANSITIONS[before]: raise ValueError(f"invalid screening transition {before} -> {after}")
def classify_replication(source, effect, coverage, days, uncertainty_finite, transferable=True, tested=True):
    if not transferable: return "not_applicable"
    if not tested or not np.isfinite(effect): return "not_tested"
    if np.sign(effect) != np.sign(source) or effect == 0: return "failed_replication"
    if coverage >= .01 and days >= 10 and uncertainty_finite and abs(effect) >= .5 * abs(source): return "strong_replication"
    return "directionally_consistent" if coverage >= .01 and days >= 10 else "failed_replication"
def checkpoint_id(experiment_id, batch_id, first, last): return hashlib.sha256(canonical_bytes([experiment_id, batch_id, first, last])).hexdigest()[:24]

def semantic_readiness(contract: dict) -> dict[str, bool]:
    inventories = contract.get("feature_inventory", {}); types = set(contract.get("representation_types", []))
    flat = [x for rows in inventories.values() for x in rows]
    return {
        "feature_inventory": set(inventories) == {"M1", "M5"} and [len(inventories[x]) for x in ("M1", "M5")] == [241, 220],
        "feature_typing": all(x.get("representation") in types for x in flat),
        "identifier_exclusion": all(next(x for x in inventories[tf] if x["feature"] == "trading_date")["representation"] == "excluded" for tf in inventories),
        "pair_selection": contract.get("pairwise_selection", {}).get("method") == "canonical_sha256_rank_all_i_lt_j",
        "subgroup_selection": contract.get("subgroup_selection", {}).get("depth_allocation") == {"2": 0.5, "3": 0.5},
        "null_inference": contract.get("null", {}).get("method") == "within_day_circular_membership_shift",
        "screening_schema": set(contract.get("statuses", [])) == SCREENING_STATUSES,
        "candidate_persistence": contract.get("candidate_path", "").startswith("promoted effect -> research.registry.create_candidate"),
        "artifact_reconciliation": len(contract.get("artifact_schemas", [])) == 8,
    }
def remaining_execution_degrees(contract: dict) -> list[str]: return sorted(name for name, passed in semantic_readiness(contract).items() if not passed)
