"""Contract tests for the frozen, diagnostic-only M30 robustness phase."""
import json
from pathlib import Path

import pandas as pd
import pytest

from TradingSystemLab.multitimeframe.phase73 import hash_tree
from TradingSystemLab.timeframe_analysis import m30_robustness as subject


@pytest.fixture(scope="module")
def result(tmp_path_factory):
    output = tmp_path_factory.mktemp("m30_robustness") / "output"
    before = {str(path): hash_tree(path) for path in subject._protected_paths(output)}
    manifest = subject.run(output=output)
    return output, manifest, before


def test_prerequisites_and_period_are_fail_closed():
    bm, om = subject._validate_prerequisites(subject.BASELINE, subject.OPTIMIZATION)
    assert bm["status"] == "PHASE_M30_BASELINE_COMPLETE"
    assert om["status"] == "PHASE_M30_OPTIMIZATION_COMPLETE"
    assert om["development_period"] == ["2023-01-01", "2024-12-31"]
    assert om["true_oos_cutoff"] == "2025-01-01" and om["true_oos_blocked"] is True
    assert om["one_factor_at_a_time"] and not om["cartesian_grid"] and not om["winner_selection"]


def test_predeclared_candidate_contract_is_exact():
    assert subject.PREDECLARED_CONFIGURATION_IDS == {
        "T2": "T2-M30-0008-2b0494cdd24b", "T3": "T3-M30-0020-816e9e819790"}
    registry = subject.lock_candidate_registry(subject.OPTIMIZATION)
    assert registry["T2"]["candidate_id"] == "T2_M30_candidate_v1"
    assert registry["T3"]["candidate_id"] == "T3_M30_candidate_v1"
    assert {k: v["parent_candidate_id"] for k, v in registry.items()} == {
        "T2": "T2_candidate_v1", "T3": "T3_candidate_v1"}
    assert all(v["selection_locked_before_validation"] for v in registry.values())
    assert all(v["optimization_classification"] == "ROBUST_PLATEAU" for v in registry.values())
    assert {k: v["parameter_hash"] for k, v in registry.items()} == {
        "T2": "2b0494cdd24bfbfa8ce7d657d6f83d1408f07b9f565d38d093dec5b4856e3c00",
        "T3": "816e9e819790e1523aa5408bc1437119fae03f840c9e672c74f9974983e429c3"}
    assert {k: v["parameters"] for k, v in registry.items()} == {k: v["parameters"] for k, v in subject.FROZEN.items()}
    assert {k: v["strategy_hash"] for k, v in registry.items()} == {
        "T2": "376df085cfda85eefccb31343aad40ed4fbb1078f1314496472a3a4ac9507774",
        "T3": "840dd3b2cda43fa00259445cd0a22ace6d82e677f4c793028ccc8126f9ad9a8c"}


def test_manifest_proves_no_search_and_c1_only(result):
    _, manifest, _ = result
    assert manifest["status"] == "PHASE_M30_ROBUSTNESS_COMPLETE"
    assert manifest["candidate_selection_precedes_validation"] is True
    assert manifest["cost_model"] == {"name": "H1_C1", "ticks_per_side": 1.0,
                                      "round_trip_ticks": 2.0, "additional_slippage_ticks": 0.0}
    assert all(manifest[name] is False for name in subject.FLAGS)
    assert manifest["true_oos_blocked"] is True
    assert manifest["execution"] == {"T2": "DIRECT_CLOSED_M30",
        "T3": "CLOSED_M30_WITH_CAUSAL_FOUR_M30_CONTEXT"}
    assert manifest["bootstrap"]["iterations"] == 10_000
    assert manifest["bootstrap"]["seed"] == 330_2025
    assert manifest["bootstrap"]["interpretation"] == "DIAGNOSTIC_ONLY_IID_TRADE_BOOTSTRAP"


def test_sources_match_both_committed_phases(result):
    _, manifest, _ = result
    baseline = json.loads((subject.BASELINE / "manifest.json").read_text())
    optimization = json.loads((subject.OPTIMIZATION / "manifest.json").read_text())
    assert manifest["source_files"] == baseline["source_files"] == optimization["source_files"]
    assert {row["alias"] for row in manifest["source_coverage"]} == {"Si", "CNY"}


@pytest.mark.parametrize("key", ["T2", "T3"])
def test_replay_and_required_reports(result, key):
    output, _, _ = result
    metrics = json.loads((output / key / "metrics.json").read_text())
    expected = subject.EXPECTED_REPLAY[key]
    for name, value in expected.items():
        assert metrics[name] == pytest.approx(value, abs=5e-10)
    assert set(pd.read_csv(output / key / "yearly_report.csv").year) == {2023, 2024}
    assert set(pd.read_csv(output / key / "instrument_report.csv").instrument) == {"USDRUBF", "CNYRUBF"}
    assert set(pd.read_csv(output / key / "direction_report.csv").direction) == {"LONG", "SHORT"}
    assert len(pd.read_csv(output / key / "monthly_report.csv")) == 24
    assert set(pd.read_csv(output / key / "mae_mfe_report.csv").scope) == {"ALL", "WINNERS", "LOSERS"}
    assert set(pd.read_csv(output / key / "leave_one_period_out.csv").analysis) == {
        "leave_one_quarter_out", "leave_one_year_out"}
    concentration = pd.read_csv(output / key / "concentration_report.csv").columns
    for n in (1, 3, 5, 10): assert f"top_{n}_positive_R_share" in concentration
    assert list(pd.read_csv(output / key / "baseline_vs_candidate.csv").version) == ["baseline", "candidate"]


def test_t2_baseline_candidate_equality_and_t3_is_descriptive(result):
    output, _, _ = result
    t2 = pd.read_csv(output / "T2" / "baseline_vs_candidate.csv")
    assert t2.drop(columns=["version", "candidate_id"]).iloc[0].equals(t2.drop(columns=["version", "candidate_id"]).iloc[1])
    t3 = pd.read_csv(output / "T3" / "baseline_vs_candidate.csv")
    assert set(t3.version) == {"baseline", "candidate"}
    assert not any(value in (output / "T3" / "final_report.md").read_text() for value in ("ROBUST_READY", "BORDERLINE", "REJECTED"))


def test_protected_artifacts_unchanged(result):
    output, manifest, before = result
    after = {str(path): hash_tree(path) for path in subject._protected_paths(output)}
    assert before == after == manifest["protected_artifact_hashes"]


def test_output_is_deterministic(result, tmp_path):
    first, _, _ = result
    second = tmp_path / "second"
    subject.run(output=second)
    assert hash_tree(first) == hash_tree(second)
