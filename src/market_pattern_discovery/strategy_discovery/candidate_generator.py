"""Deterministic, registry-only Phase 6A candidate generation.

This module expands a preregistered strategy-family registry.  It deliberately
does not accept market data, outcomes, scores, or backtest results.
"""
from __future__ import annotations

from itertools import product
from typing import Any, Iterable, Mapping

from .governance import (
    CandidateLimitExceeded,
    canonical_sha256,
    deterministic_candidate_id,
    estimate_candidates,
)


class CandidateRegistryViolation(ValueError):
    """Raised when an input is not a valid frozen architecture registry."""


def _parameters(family: Mapping[str, Any]) -> Iterable[dict[str, Any]]:
    definitions = sorted(
        (
            parameter
            for group in family["candidate_parameter_space"].values()
            for parameter in group
        ),
        key=lambda parameter: parameter["name"],
    )
    names = [parameter["name"] for parameter in definitions]
    if len(names) != len(set(names)):
        raise CandidateRegistryViolation(
            f"{family['strategy_family_id']}: duplicate parameter name"
        )
    domains = [parameter["allowed_domain"] for parameter in definitions]
    if any(not domain for domain in domains):
        raise CandidateRegistryViolation(
            f"{family['strategy_family_id']}: parameter domain is empty"
        )
    for values in product(*domains):
        yield dict(zip(names, values, strict=True))


def generate_candidates(
    registry: Mapping[str, Any],
    *,
    seed: int = 617,
    code_version: str,
    max_per_family: int = 128,
    max_total: int = 4096,
) -> list[dict[str, Any]]:
    """Expand the frozen registry without consulting observations or results.

    Output order and identities depend only on registry content, ``seed``, and
    ``code_version``.  Candidate-count limits are checked before any candidate
    is emitted, preventing a partial or silently truncated search space.
    """
    if registry.get("phase") != "6A" or registry.get("real_results_included") is not False:
        raise CandidateRegistryViolation(
            "candidate generation requires a result-free Phase 6A registry"
        )
    if not code_version:
        raise CandidateRegistryViolation("code_version must be non-empty")

    families = list(registry.get("families", ()))
    estimate_candidates(
        families, max_per_family=max_per_family, max_total=max_total
    )
    generated: list[dict[str, Any]] = []
    seen_ids: set[str] = set()

    for family in sorted(families, key=lambda item: item["strategy_family_id"]):
        family_id = family["strategy_family_id"]
        unsigned_family = {key: value for key, value in family.items() if key != "fingerprint"}
        if family.get("fingerprint") != canonical_sha256(unsigned_family):
            raise CandidateRegistryViolation(f"{family_id}: fingerprint mismatch")
        if family.get("preregistered_before_results") is not True:
            raise CandidateRegistryViolation(f"{family_id}: family was not preregistered")

        for instrument in sorted(family["instrument_scope"]):
            for timeframe in sorted(family["timeframe_scope"]):
                for parameters in _parameters(family):
                    candidate_id = deterministic_candidate_id(
                        family_id,
                        parameters,
                        instrument=instrument,
                        timeframe=timeframe,
                        seed=seed,
                        code_version=code_version,
                    )
                    if candidate_id in seen_ids:
                        raise CandidateRegistryViolation(f"duplicate candidate: {candidate_id}")
                    seen_ids.add(candidate_id)
                    candidate = {
                        "candidate_id": candidate_id,
                        "parent_family_id": family_id,
                        "origin_track": family["origin_track"],
                        "instrument": instrument,
                        "timeframe": timeframe,
                        "parameters": parameters,
                        "seed": seed,
                        "code_version": code_version,
                        "family_fingerprint": family["fingerprint"],
                        "creation_stage": "architecture",
                        "status": "generated",
                    }
                    candidate["candidate_sha256"] = canonical_sha256(candidate)
                    generated.append(candidate)
    return generated


__all__ = ["CandidateRegistryViolation", "generate_candidates"]
