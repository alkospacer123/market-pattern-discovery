"""Signed representative target mapping for governed Phase 5B discovery."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Iterable

import pandas as pd

from market_pattern_discovery.discovery.protocol import (
    discovery_signature,
    load_discovery_protocol,
)
from market_pattern_discovery.research.protocol import load_protocol, protocol_signature
from market_pattern_discovery.targets.behavior_target_set import load_behavior_target_set

ROOT = Path(__file__).resolve().parents[3]
PATH = ROOT / "config" / "discovery_target_mapping_v1.json"
TIMEFRAMES = ("M1", "M5")
FAMILIES = ("DIRECTIONAL", "VOLATILITY", "PATH", "FIRST_PASSAGE", "MULTI_HORIZON")


def canonical_mapping_bytes(mapping: dict[str, Any]) -> bytes:
    """Return canonical unsigned JSON bytes; the signature never signs itself."""
    unsigned = {key: value for key, value in mapping.items() if key != "signature_sha256"}
    return json.dumps(unsigned, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()


def mapping_signature(mapping: dict[str, Any] | None = None) -> str:
    value = mapping if mapping is not None else json.loads(PATH.read_text())
    return hashlib.sha256(canonical_mapping_bytes(value)).hexdigest()


def _frozen_signatures() -> dict[str, str]:
    feature = json.loads((ROOT / "config" / "feature_set_v1.json").read_text())
    target_definitions = json.loads((ROOT / "config" / "target_definitions_v1.json").read_text())
    behavior = load_behavior_target_set()
    discovery = load_discovery_protocol()
    return {
        "feature_set": feature["signature_sha256"],
        "behavior_target_set": behavior["signature_sha256"],
        "target_definitions": target_definitions["signature_sha256"],
        "research_protocol": protocol_signature(load_protocol()),
        "discovery_protocol": discovery_signature(discovery),
    }


def load_discovery_target_mapping(path: Path = PATH, *, validate: bool = True) -> dict[str, Any]:
    value = json.loads(path.read_text())
    if value.get("signature_sha256") != mapping_signature(value):
        raise ValueError("Discovery Target Mapping signature drift")
    if value.get("required_signatures") != _frozen_signatures():
        raise ValueError("Discovery Target Mapping frozen input signature drift")
    if validate:
        validate_mapping_against_behavior_set(value)
    return value


def mapped_targets(timeframe: str, family: str | None = None,
                   mapping: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    if timeframe not in TIMEFRAMES:
        raise ValueError(f"unsupported timeframe {timeframe!r}")
    if family is not None and family not in FAMILIES:
        raise ValueError(f"unsupported target family {family!r}")
    value = mapping or load_discovery_target_mapping()
    return [dict(item) for item in value["mapping"][timeframe]
            if family is None or item["family"] == family]


def primary_contrasts(column: str, *, timeframe: str | None = None,
                      mapping: dict[str, Any] | None = None) -> list[str]:
    value = mapping or load_discovery_target_mapping()
    matches = [item for tf in TIMEFRAMES for item in value["mapping"][tf]
               if item["column_name"] == column and (timeframe is None or tf == timeframe)]
    if not matches:
        raise KeyError(column)
    unique = {tuple(item["hypothesis_contrasts"]) for item in matches}
    if len(unique) != 1:
        raise ValueError(f"timeframe-dependent contrasts require an explicit timeframe: {column}")
    return list(next(iter(unique)))


def hypothesis_units(timeframe: str, family: str | None = None,
                     mapping: dict[str, Any] | None = None) -> int:
    return sum(item["hypothesis_units_per_state"]
               for item in mapped_targets(timeframe, family, mapping))


def target_valid_domain(frame: pd.DataFrame, column: str) -> pd.Series:
    """Preserve the frozen NaN domain rather than manufacturing a class zero."""
    if column not in frame:
        raise KeyError(column)
    return frame[column].notna()


def baseline_domain(frame: pd.DataFrame, column: str, *, instrument: str,
                    timeframe: str, discovery_mask: Iterable[bool]) -> pd.Series:
    required = {"instrument", "timeframe", column}
    if missing := required.difference(frame.columns):
        raise KeyError(f"missing baseline fields: {sorted(missing)}")
    period = pd.Series(discovery_mask, index=frame.index, dtype=bool)
    return (frame["instrument"].eq(instrument) & frame["timeframe"].eq(timeframe)
            & period & target_valid_domain(frame, column))


def fdr_family_key(*, instrument: str, timeframe: str, discovery_method: str,
                   target_family: str, semantic_role: str, horizon: int | None) -> str:
    if timeframe not in TIMEFRAMES or target_family not in FAMILIES:
        raise ValueError("invalid FDR family component")
    role = semantic_role if horizon is None else f"{semantic_role}@H{horizon}"
    return "|".join((instrument, timeframe, discovery_method, target_family, role))


def validate_mapping_against_behavior_set(mapping: dict[str, Any],
                                           behavior: dict[str, Any] | None = None) -> None:
    contract = behavior or load_behavior_target_set()
    if set(mapping.get("canonical_families", {})) != set(FAMILIES):
        raise ValueError("canonical target-family drift")
    if set(mapping.get("mapping", {})) != set(TIMEFRAMES):
        raise ValueError("mapping must contain exactly M1 and M5")
    removed = {item["name"] for item in contract["removals"]}
    expected_horizons = {"M1": {5, 15, 60}, "M5": {1, 3, 12}}
    direction_encoding = {"classes": [-1, 0, 1], "meanings": {"-1": "down", "0": "unchanged", "1": "up"}, "nan": "invalid; excluded, never converted to class 0"}
    passage_encoding = {"classes": [-1, 0, 1], "meanings": {"-1": "lower first", "0": "neither", "1": "upper first"}, "nan": "same-candle ambiguity or invalid; excluded, never converted to class 0"}
    for timeframe in TIMEFRAMES:
        retained = set(contract["ordered_phase3b_generic_columns"][timeframe])
        other = set(contract["ordered_phase3b_generic_columns"][TIMEFRAMES[1 - TIMEFRAMES.index(timeframe)]])
        items = mapping["mapping"][timeframe]
        names = [item["column_name"] for item in items]
        if len(names) != len(set(names)):
            raise ValueError(f"duplicate mapped column for {timeframe}")
        for item in items:
            name = item["column_name"]
            if item["timeframe"] != timeframe:
                raise ValueError(f"wrong timeframe on {name}")
            if name in removed:
                raise ValueError(f"removed column mapped: {name}")
            if name not in retained:
                reason = "wrong-timeframe" if name in other else "missing"
                raise ValueError(f"{reason} mapped column: {name}")
            if item.get("classification") != "generic" or name.startswith("target_"):
                raise ValueError(f"non-generic/provenance column mapped: {name}")
            horizon = item.get("horizon")
            if horizon is not None and horizon not in expected_horizons[timeframe]:
                raise ValueError(f"nonrepresentative horizon on {name}")
            contrasts = item.get("hypothesis_contrasts", [])
            if not contrasts or item.get("hypothesis_units_per_state") != len(contrasts) or item.get("multiplicity_units") != len(contrasts):
                raise ValueError(f"hypothesis-unit mismatch on {name}")
            if name.startswith("label_direction_") and (item.get("encoding") != direction_encoding or len(contrasts) != 2):
                raise ValueError(f"invalid direction encoding/contrasts on {name}")
            if name.startswith("label_first_passage_") and (item.get("encoding") != passage_encoding or len(contrasts) != 2):
                raise ValueError(f"invalid first-passage encoding/contrasts on {name}")
            expected_units = 2 if item["target_type"] == "multiclass" else 1
            if len(contrasts) != expected_units:
                raise ValueError(f"target-type hypothesis-unit mismatch on {name}")
    if not mapping.get("baseline_policy") or not mapping.get("valid_domain_policy"):
        raise ValueError("baseline and valid-domain policies are required")
    fields = mapping.get("multiplicity_policy", {}).get("family_key_fields")
    if fields != ["instrument", "timeframe", "discovery_method", "target_family", "target_role_or_horizon"]:
        raise ValueError("FDR grouping rule drift")


def verify_phase5b_contracts() -> tuple[str, str]:
    """Load both mandatory signed inputs before any Phase 5B operation."""
    protocol = load_discovery_protocol()
    mapping = load_discovery_target_mapping()
    return discovery_signature(protocol), mapping_signature(mapping)
