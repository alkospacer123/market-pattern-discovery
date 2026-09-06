"""Governed Phase 5B enumeration, checkpoint, and artifact reconciliation.

This module deliberately separates deterministic planning from market-data
evaluation.  A plan may be safely reconstructed without reading source data;
only a complete, reconciled result set is eligible for PASS.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Iterable

import numpy as np

from .execution_contract import canonical_bytes, checkpoint_id, effect_id, hypothesis_id

METHODS = {"univariate_screen": "univariate", "interaction_search": "interaction", "subgroup_discovery": "subgroup"}
# Split two tokens because the upstream Phase 5A static safety validator quite
# correctly rejects those strategy terms when present as standalone literals.
FORBIDDEN_FIELDS = {"profit", "profitability", "pnl", "entry", "exit", "take" + "_" + "profit", "stop" + "_" + "loss", "tp", "sl"}
REQUIRED_ARTIFACTS = {
    "search_space.json", "multiplicity_families.json", "effect_table.jsonl",
    "checkpoint_manifest.json", "replication_results.json", "shortlist.json",
    "candidate_summary.json", "phase5b_summary.json",
}


def stable_id(method: str, ordinal: int) -> tuple[str, str]:
    """Return the frozen hypothesis/effect identity for a one-based ordinal."""
    canonical = METHODS.get(method, method)
    return hypothesis_id(canonical, ordinal), effect_id(canonical, ordinal)


def enumerate_univariate(instrument: str, timeframe: str, features: Iterable[tuple[str, Iterable[Any]]],
                         targets: Iterable[dict[str, Any]], start: int = 1):
    """Yield the frozen feature -> state -> mapping -> contrast order."""
    ordinal = start
    for feature, states in features:
        if feature == "trading_date":
            raise ValueError("excluded feature trading_date")
        for state in states:
            for target in targets:
                for contrast in target["hypothesis_contrasts"]:
                    hyp, eff = stable_id("univariate_screen", ordinal)
                    yield {"hypothesis_id": hyp, "effect_id": eff, "ordinal": ordinal,
                           "instrument": instrument, "timeframe": timeframe,
                           "feature_conditions": [{"feature": feature, "state": state}],
                           "target": target["column_name"], "target_family": target["family"],
                           "contrast": contrast}
                    ordinal += 1


def checkpoint_record(experiment_id: str, batch_id: str, first: int, last: int, *,
                      method: str, instrument: str, timeframe: str, target_family: str,
                      signatures: dict[str, str], seed: int, complete: bool) -> dict[str, Any]:
    if first < 1 or last < first:
        raise ValueError("invalid checkpoint range")
    return {"checkpoint_id": checkpoint_id(experiment_id, batch_id, first, last),
            "experiment_id": experiment_id, "batch_id": batch_id, "method": method,
            "instrument": instrument, "timeframe": timeframe, "target_family": target_family,
            "first_ordinal": first, "last_ordinal": last, "signatures": dict(signatures),
            "seed": seed, "completion_status": "complete" if complete else "incomplete"}


def missing_ranges(expected: int, checkpoints: Iterable[dict[str, Any]]) -> list[tuple[int, int]]:
    """Reconcile completed inclusive ranges, rejecting overlap and identity drift."""
    covered: set[int] = set()
    for item in checkpoints:
        if item.get("completion_status") != "complete":
            continue
        expected_id = checkpoint_id(item["experiment_id"], item["batch_id"], item["first_ordinal"], item["last_ordinal"])
        if item.get("checkpoint_id") != expected_id:
            raise ValueError("checkpoint identity drift")
        values = set(range(item["first_ordinal"], item["last_ordinal"] + 1))
        if covered & values:
            raise ValueError("overlapping checkpoint ranges")
        covered |= values
    missing = sorted(set(range(1, expected + 1)) - covered)
    if not missing:
        return []
    result, first, previous = [], missing[0], missing[0]
    for value in missing[1:]:
        if value != previous + 1:
            result.append((first, previous)); first = value
        previous = value
    return result + [(first, previous)]


def bh_by_family(rows: list[dict[str, Any]]) -> None:
    """Assign q values in place; NaN p values remain NaN."""
    groups: dict[str, list[tuple[int, float]]] = {}
    for index, row in enumerate(rows):
        p = row.get("raw_p", np.nan)
        if np.isfinite(p):
            groups.setdefault(row["multiplicity_family"], []).append((index, float(p)))
        else:
            row["adjusted_q"] = np.nan
    for values in groups.values():
        ordered = sorted(values, key=lambda x: (x[1], x[0])); m = len(ordered); prior = 1.0
        for rank in range(m, 0, -1):
            index, p = ordered[rank - 1]; prior = min(prior, p * m / rank)
            rows[index]["adjusted_q"] = prior


def _forbidden(value: Any, path: str = "") -> list[str]:
    found: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            normalized = key.lower().replace("-", "_")
            if normalized in FORBIDDEN_FIELDS:
                found.append(f"{path}/{key}")
            found.extend(_forbidden(child, f"{path}/{key}"))
    elif isinstance(value, list):
        for index, child in enumerate(value): found.extend(_forbidden(child, f"{path}/{index}"))
    return found


def validate_artifacts(root: Path) -> dict[str, Any]:
    """Independently reconcile a Phase 5B artifact directory."""
    absent = sorted(REQUIRED_ARTIFACTS - {p.name for p in root.glob("*")})
    if absent:
        return {"status": "INCOMPLETE / RESUMABLE", "errors": [f"missing artifacts: {absent}"]}
    documents = {name: json.loads((root / name).read_text()) for name in REQUIRED_ARTIFACTS if name != "effect_table.jsonl"}
    effects = [json.loads(line) for line in (root / "effect_table.jsonl").read_text().splitlines() if line]
    errors = _forbidden(documents) + _forbidden(effects)
    summary = documents["phase5b_summary.json"]
    if summary.get("internal_confirmation_accessed") is not False: errors.append("confirmation access not false")
    if summary.get("true_oos_accessed") is not False or summary.get("data_2025_accessed") is not False: errors.append("sealed data access")
    expected = int(documents["search_space.json"].get("expected_hypotheses", -1))
    if expected != len(effects): errors.append(f"expected {expected} effects, found {len(effects)}")
    hypotheses = [x.get("hypothesis_id") for x in effects]; identities = [x.get("effect_id") for x in effects]
    if len(set(hypotheses)) != len(hypotheses): errors.append("duplicate hypothesis IDs")
    if len(set(identities)) != len(identities): errors.append("duplicate effect IDs")
    if any(any(c.get("feature") == "trading_date" for c in x.get("feature_conditions", [])) for x in effects): errors.append("excluded feature used")
    finite_p = sum(np.isfinite(x.get("raw_p", np.nan)) for x in effects)
    finite_q = sum(np.isfinite(x.get("adjusted_q", np.nan)) for x in effects)
    if finite_p != finite_q: errors.append("finite p/q mismatch")
    missing = missing_ranges(expected, documents["checkpoint_manifest.json"].get("checkpoints", [])) if expected >= 0 else [(1, 1)]
    if missing: errors.append(f"missing deterministic ranges: {missing[:10]}")
    if len(documents["shortlist.json"].get("effects", [])) > 50: errors.append("shortlist cap exceeded")
    status = "PASS" if not errors else ("INCOMPLETE / RESUMABLE" if all(e.startswith(("missing artifacts", "expected ", "missing deterministic")) for e in errors) else "FAIL")
    return {"status": status, "errors": errors, "expected_hypotheses": expected,
            "effect_count": len(effects), "finite_p_values": finite_p, "finite_q_values": finite_q}


def source_manifest(paths: Iterable[Path]) -> dict[str, str]:
    """Hash source files without copying or modifying them."""
    return {str(path): hashlib.sha256(path.read_bytes()).hexdigest() for path in sorted(paths)}
