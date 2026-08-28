"""Hard scientific gates for partitions, fingerprints, and candidate enumeration."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
import hashlib
import json
import math
from typing import Any, Iterable


class DatasetRole(StrEnum):
    DISCOVERY = "DISCOVERY"
    INTERNAL_CONFIRMATION = "INTERNAL_CONFIRMATION"
    TRUE_OOS = "TRUE_OOS"


class ExecutionMode(StrEnum):
    ARCHITECTURE = "ARCHITECTURE"
    DISCOVERY = "DISCOVERY"
    CONFIRMATION = "CONFIRMATION"
    TRUE_OOS_FINAL = "TRUE_OOS_FINAL"


class DataAccessForbidden(RuntimeError): pass
class TrueOOSAccessForbidden(DataAccessForbidden): pass
class CandidateLimitExceeded(RuntimeError): pass
class StrategyFreezeViolation(RuntimeError): pass


DISCOVERY_START = datetime.fromisoformat("2026-01-05T00:00:00+03:00")
DISCOVERY_END = datetime.fromisoformat("2026-05-16T00:00:00+03:00")


def canonical_sha256(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(payload.encode()).hexdigest()


def deterministic_candidate_id(family_id: str, parameters: dict[str, Any], *,
                               instrument: str, timeframe: str, seed: int,
                               code_version: str) -> str:
    """Content-derived scientific ID; changing any lineage input changes the ID."""
    digest = canonical_sha256({"family": family_id, "parameters": parameters,
                               "instrument": instrument, "timeframe": timeframe,
                               "seed": seed, "code_version": code_version})
    return f"{family_id}-C-{digest[:20]}"


def authorize_dataset(mode: ExecutionMode, role: DatasetRole, *, synthetic: bool = False,
                      strategy_frozen: bool = False) -> None:
    """Authorize before a loader opens anything; roles can never be relabelled."""
    if mode == ExecutionMode.ARCHITECTURE:
        if synthetic: return
        if role == DatasetRole.TRUE_OOS: raise TrueOOSAccessForbidden("TRUE OOS is inaccessible in ARCHITECTURE")
        raise DataAccessForbidden("ARCHITECTURE accepts synthetic/test data only")
    if role == DatasetRole.TRUE_OOS and mode != ExecutionMode.TRUE_OOS_FINAL:
        raise TrueOOSAccessForbidden(f"TRUE OOS is inaccessible in {mode}")
    allowed = ((mode == ExecutionMode.DISCOVERY and role == DatasetRole.DISCOVERY) or
               (mode == ExecutionMode.CONFIRMATION and role == DatasetRole.INTERNAL_CONFIRMATION and strategy_frozen) or
               (mode == ExecutionMode.TRUE_OOS_FINAL and role == DatasetRole.TRUE_OOS and strategy_frozen))
    if not allowed: raise DataAccessForbidden(f"{role} forbidden in {mode}")


def validate_discovery_interval(start: datetime, end: datetime) -> None:
    if start < DISCOVERY_START or end > DISCOVERY_END or start >= end:
        raise DataAccessForbidden("request is outside the preregistered discovery interval")


@dataclass(frozen=True)
class CountEstimate:
    family: str
    parameter_combinations: int
    instrument_variants: int
    timeframe_variants: int
    total_candidate_count: int


def estimate_candidates(families: Iterable[dict[str, Any]], *, max_per_family: int = 128,
                        max_total: int = 4096) -> list[CountEstimate]:
    estimates = []
    for family in sorted(families, key=lambda x: x["strategy_family_id"]):
        params = [p for group in family["candidate_parameter_space"].values() for p in group]
        combinations = math.prod(len(p["allowed_domain"]) for p in params)
        n_i, n_t = len(family["instrument_scope"]), len(family["timeframe_scope"])
        total = combinations * n_i * n_t
        estimates.append(CountEstimate(family["strategy_family_id"], combinations, n_i, n_t, total))
        if total > max_per_family: raise CandidateLimitExceeded(f"{family['strategy_family_id']}: {total} > {max_per_family}")
    grand = sum(x.total_candidate_count for x in estimates)
    if grand > max_total: raise CandidateLimitExceeded(f"registry: {grand} > {max_total}")
    return estimates


def verify_frozen_strategy(spec: dict[str, Any], expected_sha256: str, *, discovery_frozen: bool,
                           confirmation_frozen: bool, causal_validation_passed: bool) -> None:
    if spec.get("status") != "frozen" or not all((discovery_frozen, confirmation_frozen, causal_validation_passed)):
        raise StrategyFreezeViolation("TRUE OOS prerequisites are incomplete")
    unsigned = {k: v for k, v in spec.items() if k != "strategy_sha256"}
    actual = canonical_sha256(unsigned)
    if expected_sha256 != actual or spec.get("strategy_sha256") != actual:
        raise StrategyFreezeViolation("frozen strategy SHA-256 mismatch")
