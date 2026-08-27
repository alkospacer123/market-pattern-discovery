"""Frozen Feature Set v1.0 manifest and objective audit helpers."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

MANIFEST_PATH = Path(__file__).resolve().parents[3] / "config" / "feature_set_v1.json"
PROVENANCE_COLUMNS = ("m5_source_open_time", "m5_source_close_time")


def load_manifest(path: Path = MANIFEST_PATH) -> dict[str, Any]:
    return json.loads(path.read_text())


def signature_payload(manifest: dict[str, Any]) -> bytes:
    """Canonical bytes covered by the signature (excluding the signature itself)."""
    payload = {key: value for key, value in manifest.items() if key != "signature_sha256"}
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()


def manifest_signature(manifest: dict[str, Any]) -> str:
    return hashlib.sha256(signature_payload(manifest)).hexdigest()


def exact_duplicate_groups(frame: pd.DataFrame, columns: list[str], *, atol: float = 1e-12) -> list[list[str]]:
    """Return true value duplicates; NaN masks must match exactly."""
    groups: list[list[str]] = []
    consumed: set[str] = set()
    for i, left in enumerate(columns):
        if left in consumed:
            continue
        matches = [left]
        a = pd.to_numeric(frame[left], errors="coerce").to_numpy(float)
        for right in columns[i + 1:]:
            if right in consumed:
                continue
            b = pd.to_numeric(frame[right], errors="coerce").to_numpy(float)
            if np.array_equal(np.isnan(a), np.isnan(b)) and np.allclose(a, b, rtol=0.0, atol=atol, equal_nan=True):
                matches.append(right); consumed.add(right)
        if len(matches) > 1:
            groups.append(matches); consumed.update(matches)
    return groups


def invalid_columns(frame: pd.DataFrame, columns: list[str]) -> dict[str, Any]:
    numeric = frame[columns].apply(pd.to_numeric, errors="coerce")
    return {
        "all_nan": [c for c in columns if frame[c].isna().all()],
        "constant": [c for c in columns if frame[c].notna().any() and frame[c].nunique(dropna=True) <= 1],
        "inf_cells": int(np.isinf(numeric.to_numpy(float)).sum()),
        "duplicate_column_names": len(columns) - len(set(columns)),
    }


def bounded_violations(frame: pd.DataFrame, columns: list[str]) -> dict[str, int]:
    """Validate documented binary, direction, fraction and position domains."""
    result: dict[str, int] = {}
    for name in columns:
        values = pd.to_numeric(frame[name], errors="coerce").dropna()
        if name == "candle_direction" or name.endswith("_direction"):
            count = int((~values.isin([-1, 0, 1])).sum())
        elif "fraction_up" in name or "fraction_down" in name or "position_in_" in name:
            count = int(((values < -1e-12) | (values > 1 + 1e-12)).sum())
        elif frame[name].dtype == bool or name.startswith(("is_", "at_", "above_", "below_", "touches_")):
            count = int((~values.isin([0, 1])).sum())
        else:
            continue
        if count:
            result[name] = count
    return result
