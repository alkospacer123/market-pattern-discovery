"""Signed, read-only Behavior/Target Set v1.0 runtime contract."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from collections.abc import Sequence

MANIFEST_PATH = Path(__file__).resolve().parents[3] / "config" / "behavior_target_set_v1.json"


def canonical_bytes(manifest: dict) -> bytes:
    payload = {key: value for key, value in manifest.items() if key != "signature_sha256"}
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()


def behavior_target_signature(manifest: dict) -> str:
    return hashlib.sha256(canonical_bytes(manifest)).hexdigest()


def load_behavior_target_set(path: Path = MANIFEST_PATH) -> dict:
    manifest = json.loads(path.read_text())
    actual = behavior_target_signature(manifest)
    if actual != manifest.get("signature_sha256"):
        raise ValueError(f"Behavior/Target Set signature mismatch: {actual}")
    for timeframe in ("M1", "M5"):
        groups = ordered_groups(manifest, timeframe)
        names = [name for group in groups for name in group]
        if len(names) != len(set(names)):
            raise ValueError(f"duplicate final names for {timeframe}")
    return manifest


def ordered_groups(manifest: dict, timeframe: str) -> tuple[list[str], list[str], list[str]]:
    if timeframe not in ("M1", "M5"):
        raise ValueError(f"unsupported timeframe {timeframe!r}")
    return tuple(list(manifest[key][timeframe]) for key in (
        "ordered_phase3a_columns", "ordered_phase3b_generic_columns", "ordered_phase3b_known_columns"
    ))  # type: ignore[return-value]


def validate_ordered_columns(columns: Sequence[str], timeframe: str, *,
                             layer: str, allow_extra: bool = False,
                             manifest: dict | None = None) -> None:
    """Reject missing, duplicate, extra, or reordered contract columns."""
    contract = manifest or load_behavior_target_set()
    keys = {"phase3a": 0, "generic": 1, "known": 2}
    if layer not in keys:
        raise ValueError(f"unknown layer {layer!r}")
    expected = ordered_groups(contract, timeframe)[keys[layer]]
    actual = list(columns)
    if len(actual) != len(set(actual)):
        raise ValueError("duplicate columns")
    missing = [name for name in expected if name not in actual]
    if missing:
        raise ValueError(f"missing required columns: {missing}")
    if allow_extra:
        selected = [name for name in actual if name in set(expected)]
        if selected != expected:
            raise ValueError("required column order drift")
    elif actual != expected:
        extras = [name for name in actual if name not in set(expected)]
        if extras:
            raise ValueError(f"extra columns: {extras}")
        raise ValueError("required column order drift")
