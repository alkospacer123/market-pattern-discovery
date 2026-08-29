"""Real governed Phase 5B autonomous discovery runner.

This module closes the gap between the frozen Phase 5A.2 execution contract and
real market-data evaluation.  It never reads INTERNAL_CONFIRMATION or TRUE_OOS.
The runner is deterministic, range-batchable, and writes only resumable
discovery artifacts under ``results/phase5b``.

Profitability is intentionally absent here.  Phase 5B discovers stable
feature->future-behaviour effects.  Executable strategy synthesis and the
PF>=2 gate are a separate downstream stage so that profitability cannot steer
the pattern search itself.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Iterator
import argparse
import hashlib
import json

import numpy as np
import pandas as pd

from market_pattern_discovery.data.finam import load_finam_window
from market_pattern_discovery.features.builder import build_features
from market_pattern_discovery.features.schema import RoundLevelConfig
from market_pattern_discovery.targets.behavior import build_behaviors
from market_pattern_discovery.discovery.protocol import (
    categorical_states, day_block_bootstrap, quantile_states,
)
from market_pattern_discovery.discovery.execution_contract import (
    canonical_bytes, effect_id, enumerate_pairs, feature_inventory,
    hypothesis_id, load_execution_contract, states_for,
    subgroup_rules,
)
from market_pattern_discovery.research.protocol import (
    AccessMode, load_protocol, request_access,
)

ROOT = Path(__file__).resolve().parents[3]
TARGET_MAPPING = ROOT / "config" / "discovery_target_mapping_v1.json"

SPECS = {
    "CNYRUBF": {"folder": "CNY", "tick": 0.001, "round_step": 0.05},
    "USDRUBF": {"folder": "Si", "tick": 0.01, "round_step": 0.10},
}
METHODS = {
    "univariate_screen": "univariate",
    "interaction_search": "interaction",
    "subgroup_discovery": "subgroup",
}


@dataclass(frozen=True)
class DiscoveryMatrix:
    instrument: str
    timeframe: str
    frame: pd.DataFrame
    states: dict[str, pd.Series]
    state_values: dict[str, list[Any]]
    targets: list[dict[str, Any]]
    provenance: list[dict[str, Any]]


def _protocol_window() -> tuple[pd.Timestamp, pd.Timestamp]:
    p = load_protocol()["discovery_period"]
    return pd.Timestamp(p["start_utc"]).tz_convert("Europe/Moscow"), pd.Timestamp(
        p["end_utc_exclusive"]
    ).tz_convert("Europe/Moscow")


def _source_paths(data_root: str | Path, instrument: str, timeframe: str) -> list[Path]:
    if instrument not in SPECS:
        raise ValueError(f"unsupported instrument {instrument}")
    root = Path(data_root) / "2026" / SPECS[instrument]["folder"]
    suffix = "_M1.csv" if timeframe == "M1" else ".csv"
    candidates = sorted(root.glob(f"*2026_Q[12]*{suffix}"))
    candidates = [p for p in candidates if ("_M1" in p.name) == (timeframe == "M1")]
    if not candidates:
        raise FileNotFoundError(f"no 2026 Q1/Q2 {timeframe} sources under {root}")
    if any("2025" in p.name for p in candidates):
        raise PermissionError("2025 TRUE OOS source path is sealed")
    return candidates


def _load_window_sources(
    data_root: str | Path, instrument: str, timeframe: str
) -> tuple[pd.DataFrame, list[dict[str, Any]]]:
    start, end = _protocol_window()
    request_access(AccessMode.DISCOVERY, (start.isoformat(), end.isoformat()))
    pieces: list[pd.DataFrame] = []
    provenance: list[dict[str, Any]] = []
    for path in _source_paths(data_root, instrument, timeframe):
        try:
            item = load_finam_window(path, instrument, timeframe, start, end)
        except Exception as exc:
            if "no rows in requested window" in str(exc):
                continue
            raise
        pieces.append(item.frame)
        provenance.extend(item.provenance)
    if not pieces:
        raise ValueError("discovery window contains no source rows")
    frame = pd.concat(pieces, ignore_index=True).sort_values(
        ["open_time", "source_filename", "source_row"], kind="mergesort"
    )
    dup = frame.duplicated("open_time", keep=False)
    for stamp, group in frame.loc[dup].groupby("open_time", sort=False):
        cols = ["open", "high", "low", "close", "volume"]
        if not (group[cols].to_numpy() == group.iloc[0][cols].to_numpy()).all():
            raise ValueError(f"conflicting discovery duplicate at {stamp}")
    frame = frame.drop_duplicates("open_time", keep="first").reset_index(drop=True)
    if frame.open_time.min() < start or frame.open_time.max() >= end:
        raise PermissionError("discovery fence violation")
    frame["moscow_trading_date"] = frame.open_time.dt.tz_convert(
        "Europe/Moscow"
    ).dt.date
    return frame, provenance


def _build_state(
    series: pd.Series, representation: str
) -> tuple[pd.Series, list[Any]]:
    if "quantile" in representation:
        state, _ = quantile_states(series)
        return state, ["LE_P10", "P10_P25", "P25_P75", "P75_P90", "GE_P90", "MISSING"]
    state = categorical_states(series)
    return state, states_for(
        {"representation": representation}, categories=state.tolist()
    )


def load_discovery_matrix(
    data_root: str | Path, instrument: str, timeframe: str
) -> DiscoveryMatrix:
    if timeframe not in {"M1", "M5"}:
        raise ValueError("timeframe must be M1 or M5")
    raw, provenance = _load_window_sources(data_root, instrument, timeframe)
    cfg = RoundLevelConfig(
        SPECS[instrument]["tick"], SPECS[instrument]["round_step"],
        SPECS[instrument]["tick"],
    )
    native_m5 = None
    if timeframe == "M1":
        native_m5, p5 = _load_window_sources(data_root, instrument, "M5")
        provenance.extend(p5)
    built = build_features(
        raw, timeframe=timeframe, round_levels=cfg, native_m5=native_m5
    )
    feature_frame = built.frame.reset_index(drop=True)
    behaviors = build_behaviors(raw, feature_frame).reset_index(drop=True)
    joined = feature_frame.copy()
    for col in behaviors.columns:
        if col not in joined:
            joined[col] = behaviors[col]
    joined["moscow_trading_date"] = raw["moscow_trading_date"].to_numpy()
    joined["timestamp"] = raw["close_time"].to_numpy()

    contract = load_execution_contract()
    inventory = feature_inventory(timeframe, included_only=True, contract=contract)
    states: dict[str, pd.Series] = {}
    values: dict[str, list[Any]] = {}
    for entry in inventory:
        name = entry["feature"]
        if name not in joined:
            raise ValueError(f"frozen feature missing from builder output: {name}")
        state, state_values = _build_state(joined[name], entry["representation"])
        states[name] = state
        values[name] = state_values

    mapping = json.loads(TARGET_MAPPING.read_text())["mapping"][timeframe]
    targets = [t for t in mapping if t.get("classification") == "generic"]
    for target in targets:
        if target["column_name"] not in joined:
            raise ValueError(f"frozen target missing: {target['column_name']}")
    return DiscoveryMatrix(
        instrument, timeframe, joined, states, values, targets, provenance
    )


def _target_binary_view(values: pd.Series, contrast: str) -> pd.Series:
    if "+1" in contrast:
        klass = 1
    elif "-1" in contrast:
        klass = -1
    elif "P(1" in contrast or "probability" in contrast.lower():
        klass = 1
    else:
        raise ValueError(f"cannot derive class from contrast: {contrast}")
    return (pd.to_numeric(values, errors="coerce") == klass).astype(float).where(
        values.notna()
    )


def _target_view(matrix: DiscoveryMatrix, target: dict, contrast: str):
    source = matrix.frame[target["column_name"]]
    if target["target_type"] == "continuous":
        return source, "continuous", "median_difference"
    return _target_binary_view(source, contrast), "binary", "probability_difference"


def _mask_for(matrix: DiscoveryMatrix, conditions: Iterable[tuple[str, Any]]) -> pd.Series:
    mask = pd.Series(True, index=matrix.frame.index)
    for feature, state in conditions:
        mask &= matrix.states[feature].eq(state)
    return mask


def _hypotheses(
    matrix: DiscoveryMatrix, method: str, contract: dict
) -> Iterator[dict[str, Any]]:
    canonical = METHODS[method]
    ordinal = 1
    if method == "univariate_screen":
        for entry in feature_inventory(matrix.timeframe, included_only=True, contract=contract):
            feature = entry["feature"]
            for state in matrix.state_values[feature]:
                for target in matrix.targets:
                    for contrast in target["hypothesis_contrasts"]:
                        yield {
                            "ordinal": ordinal, "hypothesis_id": hypothesis_id(canonical, ordinal),
                            "effect_id": effect_id(canonical, ordinal), "method": method,
                            "conditions": [(feature, state)], "target": target, "contrast": contrast,
                        }
                        ordinal += 1
        return

    eligible = feature_inventory(matrix.timeframe, included_only=True, contract=contract)
    if method == "interaction_search":
        pairs = enumerate_pairs(
            eligible, cap=contract["pairwise_selection"]["cap"],
            timeframe=matrix.timeframe, seed=contract["execution_seed"],
        )
        for a, b in pairs:
            for sa in matrix.state_values[a]:
                for sb in matrix.state_values[b]:
                    for target in matrix.targets:
                        for contrast in target["hypothesis_contrasts"]:
                            yield {
                                "ordinal": ordinal, "hypothesis_id": hypothesis_id(canonical, ordinal),
                                "effect_id": effect_id(canonical, ordinal), "method": method,
                                "conditions": [(a, sa), (b, sb)], "target": target, "contrast": contrast,
                            }
                            ordinal += 1
        return

    feature_states = [(x["feature"], matrix.state_values[x["feature"]]) for x in eligible]
    rules = subgroup_rules(
        feature_states, cap=contract["subgroup_selection"]["cap"],
        seed=contract["execution_seed"],
        depth2_fraction=contract["subgroup_selection"]["depth_allocation"]["2"],
    )
    for rule in rules:
        for target in matrix.targets:
            for contrast in target["hypothesis_contrasts"]:
                yield {
                    "ordinal": ordinal, "hypothesis_id": hypothesis_id(canonical, ordinal),
                    "effect_id": effect_id(canonical, ordinal), "method": method,
                    "conditions": list(rule), "target": target, "contrast": contrast,
                }
                ordinal += 1


def _fast_primary_effect(candidate: pd.Series, baseline: pd.Series, kind: str) -> dict[str, float]:
    a = pd.to_numeric(candidate, errors="coerce").to_numpy(float)
    b = pd.to_numeric(baseline, errors="coerce").to_numpy(float)
    a, b = a[np.isfinite(a)], b[np.isfinite(b)]
    if not len(a) or not len(b):
        raise ValueError("effect samples must be nonempty")
    if kind == "binary":
        pa, pb = float(a.mean()), float(b.mean())
        odds_a = pa / (1 - pa) if pa < 1 else np.inf
        odds_b = pb / (1 - pb) if pb < 1 else np.inf
        signed = pa - pb
        return {
            "primary_effect_signed": signed, "primary_effect_absolute": abs(signed),
            "probability_difference": signed,
            "relative_risk": pa / pb if pb else np.nan,
            "odds_ratio": odds_a / odds_b if odds_b and np.isfinite(odds_b) else np.nan,
        }
    sb = np.sort(b)
    left = np.searchsorted(sb, a, side="left")
    right = np.searchsorted(sb, a, side="right")
    superiority = float(np.mean((left + 0.5 * (right - left)) / len(sb)))
    scale = np.std(b, ddof=1) if len(b) > 1 else np.nan
    signed = float(np.median(a) - np.median(b))
    mean_diff = float(a.mean() - b.mean())
    return {
        "primary_effect_signed": signed, "primary_effect_absolute": abs(signed),
        "mean_difference": mean_diff, "median_difference": signed,
        "standardized_mean_shift": float(mean_diff / scale) if scale > 0 else np.nan,
        "probability_of_superiority": superiority,
        "q25_shift": float(np.quantile(a, .25) - np.quantile(b, .25)),
        "q75_shift": float(np.quantile(a, .75) - np.quantile(b, .75)),
    }


def _fast_null_p_value(
    frame: pd.DataFrame, mask: pd.Series, target: str, kind: str,
    replications: int = 1000, seed: int = 20260401,
) -> float:
    if len(frame) != len(mask) or not frame.index.equals(mask.index):
        raise ValueError("mask must align exactly with frame rows")
    values = pd.to_numeric(frame[target], errors="coerce")
    valid = values.notna()
    baseline = values.loc[valid]
    observed = _fast_primary_effect(values.loc[valid & mask], baseline, kind)[
        "primary_effect_signed"
    ]
    days = [
        np.flatnonzero(frame["moscow_trading_date"].eq(day).to_numpy())
        for day in pd.unique(frame["moscow_trading_date"])
    ]
    original = mask.to_numpy(dtype=bool)
    target_values = values.to_numpy(float)
    baseline_values = target_values[valid.to_numpy()]
    baseline_stat = np.median(baseline_values) if kind == "continuous" else baseline_values.mean()
    rng = np.random.default_rng(seed)
    exceed = 0
    for _ in range(replications):
        permuted = original.copy()
        for positions in days:
            shift = int(rng.integers(0, len(positions))) if len(positions) > 1 else 0
            permuted[positions] = np.roll(original[positions], shift)
        selected = valid.to_numpy() & permuted
        if not selected.any():
            raise ValueError("null replication produced an empty candidate sample")
        a = target_values[selected]
        null_effect = (
            float(np.median(a) - baseline_stat)
            if kind == "continuous"
            else float(a.mean() - baseline_stat)
        )
        exceed += abs(null_effect) >= abs(observed)
    return float((1 + exceed) / (replications + 1))


def evaluate_hypothesis(
    matrix: DiscoveryMatrix, spec: dict[str, Any], *, infer: bool = True
) -> dict[str, Any]:
    target, kind, statistic = _target_view(matrix, spec["target"], spec["contrast"])
    mask = _mask_for(matrix, spec["conditions"])
    valid = target.notna()
    candidate = valid & mask
    baseline_n = int(valid.sum())
    n = int(candidate.sum())
    days = int(matrix.frame.loc[candidate, "moscow_trading_date"].nunique())
    coverage = float(n / baseline_n) if baseline_n else 0.0
    row = {
        "hypothesis_id": spec["hypothesis_id"], "effect_id": spec["effect_id"],
        "ordinal": spec["ordinal"], "method": spec["method"],
        "instrument": matrix.instrument, "timeframe": matrix.timeframe,
        "feature_conditions": [{"feature": f, "state": s} for f, s in spec["conditions"]],
        "target": spec["target"]["column_name"], "target_family": spec["target"]["family"],
        "target_role": spec["target"]["semantic_role"], "contrast": spec["contrast"],
        "baseline_observations": baseline_n, "candidate_observations": n,
        "unique_days": days, "coverage": coverage, "status": "ineligible",
    }
    eligibility = load_execution_contract()["eligibility"]
    if (
        baseline_n < eligibility["minimum_baseline_observations"]
        or n < eligibility["minimum_candidate_observations"]
        or days < eligibility["minimum_candidate_unique_days_bootstrap"]
    ):
        return row

    effect = _fast_primary_effect(target.loc[candidate], target.loc[valid], kind)
    row.update({
        "status": "evaluated",
        "primary_effect_signed": effect["primary_effect_signed"],
        "primary_effect_absolute": effect["primary_effect_absolute"],
        "effect_metrics": effect,
        "multiplicity_family": "|".join([
            matrix.instrument, matrix.timeframe, spec["method"],
            spec["target"]["family"], spec["target"]["semantic_role"],
        ]),
    })
    if infer:
        inference_frame = pd.DataFrame({
            "moscow_trading_date": matrix.frame.loc[valid, "moscow_trading_date"],
            "_target": target.loc[valid],
        })
        uncertainty = day_block_bootstrap(
            inference_frame, mask.loc[valid], "_target", statistic=statistic,
            replications=1000, seed=load_execution_contract()["execution_seed"],
        )
        p = _fast_null_p_value(
            inference_frame, mask.loc[valid], "_target", kind=kind,
            replications=1000, seed=load_execution_contract()["execution_seed"],
        )
        row["uncertainty"] = uncertainty
        row["raw_p"] = p
    return row


def run_batch(
    data_root: str | Path, output: str | Path, instrument: str, timeframe: str,
    method: str, first: int, last: int, *, infer: bool = True,
) -> dict[str, Any]:
    if method not in METHODS:
        raise ValueError(f"unknown method {method}")
    if first < 1 or last < first:
        raise ValueError("invalid inclusive hypothesis range")
    matrix = load_discovery_matrix(data_root, instrument, timeframe)
    contract = load_execution_contract()
    output = Path(output); output.mkdir(parents=True, exist_ok=True)
    rows = []
    for spec in _hypotheses(matrix, method, contract):
        if spec["ordinal"] < first:
            continue
        if spec["ordinal"] > last:
            break
        rows.append(evaluate_hypothesis(matrix, spec, infer=infer))
    if not rows:
        raise ValueError("requested range did not intersect enumerated hypotheses")
    batch_name = f"{instrument}_{timeframe}_{method}_{first:09d}_{last:09d}"
    part = output / f"effect_table.{batch_name}.jsonl"
    with part.open("x") as stream:
        for row in rows:
            stream.write(json.dumps(row, sort_keys=True, default=str) + "\n")
    digest = hashlib.sha256(part.read_bytes()).hexdigest()
    manifest = {
        "batch_id": batch_name, "instrument": instrument, "timeframe": timeframe,
        "method": method, "first_ordinal": first, "last_ordinal": last,
        "evaluated_rows": len(rows), "inference_enabled": infer,
        "effect_part": part.name, "sha256": digest,
        "internal_confirmation_accessed": False,
        "true_oos_accessed": False, "data_2025_accessed": False,
        "source_provenance": matrix.provenance,
    }
    (output / f"checkpoint.{batch_name}.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True, default=str) + "\n"
    )
    return manifest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run a deterministic real Phase 5B batch")
    parser.add_argument("--data-root", required=True)
    parser.add_argument("--output", default="results/phase5b")
    parser.add_argument("--instrument", choices=sorted(SPECS), required=True)
    parser.add_argument("--timeframe", choices=["M1", "M5"], required=True)
    parser.add_argument("--method", choices=sorted(METHODS), required=True)
    parser.add_argument("--first", type=int, required=True)
    parser.add_argument("--last", type=int, required=True)
    parser.add_argument("--no-inference", action="store_true",
                        help="smoke only: compute effects without bootstrap/null inference")
    args = parser.parse_args(argv)
    manifest = run_batch(
        args.data_root, args.output, args.instrument, args.timeframe,
        args.method, args.first, args.last, infer=not args.no_inference,
    )
    print(json.dumps(manifest, indent=2, sort_keys=True, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
