"""Contracts for the research-only Candidate Baseline robustness layer."""
from __future__ import annotations

from dataclasses import asdict
import hashlib
from pathlib import Path

import pandas as pd
import pytest

from bbw_system.optimization.bbw_parameter_search import _validate_train
from bbw_system.robustness import (
    RobustnessError,
    candidate_sha256,
    generate_parameter_neighborhood,
    load_candidate_config,
)
from bbw_system.robustness.bbw_candidate_robustness import COST_SCENARIOS

ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_ROOT = ROOT / "results" / "candidate_baseline" / "v1"
BASELINE = ROOT / "config" / "bbw_baseline.json"


def test_load_candidate_config_and_deterministic_hash() -> None:
    candidate = load_candidate_config(CANDIDATE_ROOT)
    assert asdict(candidate)["ema_period"] == 20
    expected = hashlib.sha256((CANDIDATE_ROOT / "CANDIDATE_CONFIG.json").read_bytes()).hexdigest()
    assert candidate_sha256(CANDIDATE_ROOT) == expected
    assert candidate_sha256(CANDIDATE_ROOT) == candidate_sha256(CANDIDATE_ROOT)


def test_cost_scenarios_are_fixed_and_not_parameter_search() -> None:
    assert COST_SCENARIOS == (("C0", 0.0), ("C0.5", 0.5), ("C1", 1.0))


def test_parameter_neighborhood_is_complete_unique_and_contains_candidate() -> None:
    candidate = load_candidate_config(CANDIDATE_ROOT)
    neighborhood = generate_parameter_neighborhood(candidate)
    assert len(neighborhood) == len(set(neighborhood)) == 32
    assert candidate in neighborhood
    assert {item.ema_period for item in neighborhood} == {20, 30}
    assert {item.range_min_bars for item in neighborhood} == {3, 4}
    assert {item.range_max_bars for item in neighborhood} == {30, 40}
    assert {item.retest_max_bars for item in neighborhood} == {30, 40}
    assert {item.atr_max for item in neighborhood} == {2.0, 3.0}


def test_loading_and_neighborhood_do_not_mutate_candidate_or_baseline() -> None:
    paths = (CANDIDATE_ROOT / "CANDIDATE_CONFIG.json", BASELINE)
    before = {path: path.read_bytes() for path in paths}
    generate_parameter_neighborhood(load_candidate_config(CANDIDATE_ROOT))
    assert all(path.read_bytes() == payload for path, payload in before.items())
    assert hashlib.sha256(BASELINE.read_bytes()).hexdigest() == (
        "8b92ba284bc7aabd6f381312762868a7d82ae5551b8bd7101d07fc959826cb68"
    )


def test_true_oos_is_rejected_before_evaluation() -> None:
    frame = pd.DataFrame({
        "timestamp": ["2025-01-02 10:00:00"], "open": [1], "high": [1],
        "low": [1], "close": [1], "volume": [1],
    })
    with pytest.raises(ValueError, match="TRUE OOS"):
        _validate_train(frame, "test")


def test_malformed_candidate_fails_closed(tmp_path: Path) -> None:
    (tmp_path / "CANDIDATE_CONFIG.json").write_text('{"ema_period": 20}', encoding="utf-8")
    with pytest.raises(RobustnessError, match="parameter names"):
        load_candidate_config(tmp_path)


def test_changed_candidate_fails_closed(tmp_path: Path) -> None:
    payload = (CANDIDATE_ROOT / "CANDIDATE_CONFIG.json").read_text(encoding="utf-8")
    (tmp_path / "CANDIDATE_CONFIG.json").write_text(
        payload.replace('"ema_period": 20', '"ema_period": 30'), encoding="utf-8")
    with pytest.raises(RobustnessError, match="frozen Candidate"):
        load_candidate_config(tmp_path)
