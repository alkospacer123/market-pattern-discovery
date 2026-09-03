from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from market_pattern_discovery.strategy_discovery.candidate_generator import (
    CandidateRegistryViolation,
    generate_candidates,
)
from market_pattern_discovery.strategy_discovery.governance import (
    CandidateLimitExceeded,
    canonical_sha256,
)


ROOT = Path(__file__).parents[2]


def registry():
    return json.loads(
        (ROOT / "config/phase6a/strategy_candidate_registry_v1.json").read_text()
    )


def test_generator_is_complete_deterministic_and_content_addressed():
    first = generate_candidates(registry(), seed=617, code_version="test-revision")
    second = generate_candidates(registry(), seed=617, code_version="test-revision")
    assert first == second
    assert len(first) == 236
    assert len({candidate["candidate_id"] for candidate in first}) == len(first)
    assert first == sorted(
        first,
        key=lambda item: (
            item["parent_family_id"],
            item["instrument"],
            item["timeframe"],
            tuple(item["parameters"]),
        ),
    )
    for candidate in first:
        unsigned = {k: v for k, v in candidate.items() if k != "candidate_sha256"}
        assert candidate["candidate_sha256"] == canonical_sha256(unsigned)
        assert candidate["creation_stage"] == "architecture"
        assert candidate["status"] == "generated"


def test_identity_changes_with_governed_inputs():
    baseline = generate_candidates(registry(), code_version="one")[0]
    changed_seed = generate_candidates(registry(), seed=618, code_version="one")[0]
    changed_code = generate_candidates(registry(), code_version="two")[0]
    assert len({baseline["candidate_id"], changed_seed["candidate_id"], changed_code["candidate_id"]}) == 3


def test_generator_rejects_results_tampering_and_unbounded_enumeration():
    with_results = registry()
    with_results["real_results_included"] = True
    with pytest.raises(CandidateRegistryViolation):
        generate_candidates(with_results, code_version="test")

    tampered = copy.deepcopy(registry())
    tampered["families"][0]["family_name"] = "changed after freeze"
    with pytest.raises(CandidateRegistryViolation, match="fingerprint mismatch"):
        generate_candidates(tampered, code_version="test")

    with pytest.raises(CandidateLimitExceeded):
        generate_candidates(registry(), code_version="test", max_total=1)


def test_parameter_domains_are_not_selected_or_reordered_by_results():
    small = registry()
    small["families"] = [copy.deepcopy(small["families"][0])]
    family = small["families"][0]
    family["candidate_parameter_space"]["core_parameters"][0]["allowed_domain"] = [10, 5]
    unsigned = {key: value for key, value in family.items() if key != "fingerprint"}
    family["fingerprint"] = canonical_sha256(unsigned)
    candidates = generate_candidates(small, code_version="test")
    assert [candidate["parameters"]["lookback_bars"] for candidate in candidates[:2]] == [10, 5]
