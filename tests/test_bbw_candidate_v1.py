"""Contract checks for the research-only Candidate Baseline v1 artifact."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path


CONFIG = Path("config/bbw_candidate_v1.json")
ARTIFACT_ROOT = Path("results/candidate_baseline/v1")
EXPECTED_SHA256 = "1be187b9dad663cb8864f4701b97343ad4c9a5923b06bfc2c319432f00ce6b0b"
EXPECTED_PARAMETERS = {
    "atr_max": 3.0,
    "atr_min": 1.0,
    "bbw_period": 10,
    "bbw_std": 1.5,
    "ema_period": 20,
    "ema_slope_threshold": 0.0,
    "penetration": 0.2,
    "range_max_bars": 40,
    "range_min_bars": 3,
    "retest_max_bars": 30,
    "retest_min_bars": 3,
    "squeeze_window": 5,
}
FROZEN_BASELINE = {
    "atr_max": 2.0, "atr_min": 1.0, "bbw_period": 10, "bbw_std": 2.0,
    "ema_period": 50, "ema_slope_threshold": 0.001, "penetration": 0.2,
    "range_max_bars": 30, "range_min_bars": 6, "retest_max_bars": 30,
    "retest_min_bars": 5, "squeeze_window": 10,
}
R2_STABLE_REGION = {
    "atr_max": {3.0}, "atr_min": {1.0}, "bbw_period": {10}, "bbw_std": {1.5},
    "ema_period": {20}, "ema_slope_threshold": {0.0}, "penetration": {0.2},
    "range_max_bars": {40}, "range_min_bars": {3},
    "retest_max_bars": {30, 40, 50}, "retest_min_bars": {3},
    "squeeze_window": {5},
}


def _load(path: Path = CONFIG) -> dict[str, float | int]:
    return json.loads(path.read_text(encoding="utf-8"))


def test_candidate_config_is_valid_and_exact() -> None:
    candidate = _load()
    assert candidate == EXPECTED_PARAMETERS
    assert set(candidate) == set(R2_STABLE_REGION)
    assert all(type(value) in (int, float) for value in candidate.values())
    assert candidate["atr_min"] <= candidate["atr_max"]
    assert candidate["range_min_bars"] <= candidate["range_max_bars"]
    assert candidate["retest_min_bars"] <= candidate["retest_max_bars"]


def test_candidate_hash_is_deterministic_and_artifact_is_identical() -> None:
    payload = CONFIG.read_bytes()
    artifact = ARTIFACT_ROOT / "CANDIDATE_CONFIG.json"
    assert artifact.read_bytes() == payload
    assert hashlib.sha256(payload).hexdigest() == EXPECTED_SHA256
    assert hashlib.sha256(CONFIG.read_bytes()).hexdigest() == EXPECTED_SHA256


def test_candidate_belongs_to_r2_stable_region() -> None:
    candidate = _load()
    assert all(candidate[name] in allowed for name, allowed in R2_STABLE_REGION.items())


def test_candidate_remains_separate_from_frozen_baseline_and_existing_artifact() -> None:
    candidate = _load()
    assert candidate != FROZEN_BASELINE
    assert CONFIG != Path("config/bbw_baseline.json")
    # Pin the pre-candidate artifact: creating the candidate must never rewrite it.
    frozen_payload = Path("config/bbw_baseline.json").read_bytes()
    assert hashlib.sha256(frozen_payload).hexdigest() == (
        "8b92ba284bc7aabd6f381312762868a7d82ae5551b8bd7101d07fc959826cb68"
    )


def test_report_records_research_only_status_and_hash() -> None:
    report = (ARTIFACT_ROOT / "CANDIDATE_REPORT.md").read_text(encoding="utf-8")
    assert "RESEARCH_CANDIDATE" in report
    assert "Optimization R2" in report
    assert EXPECTED_SHA256 in report
    assert "Robustness testing only" in report
