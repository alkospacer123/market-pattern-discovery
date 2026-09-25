import ast
import hashlib
import json
import shutil
from pathlib import Path

import pandas as pd
import pytest

from TradingSystemLab.true_oos.perpetual_v3_phase5 import (
    BOOTSTRAP_ITERATIONS, BOOTSTRAP_SEED, EXPECTED_IDENTITIES, FROZEN_TICK_SIZE,
    INSTRUMENTS, STUDIES, TRUE_OOS_START, classify, four_bar_context,
    DATA_ROOT, OUTPUT_ROOT, load_frozen_registry, load_true_oos, run,
)
from TradingSystemLab.audit_perpetual_v3_phase5 import audit, research_artifact_hashes

REGISTRY = Path("TradingSystemLab/results/perpetual_v3/phase3_candidate_freeze/candidate_registry.json")


def test_frozen_contract():
    assert STUDIES == (("T2", "M30"), ("T2", "H1"), ("T3", "M30"), ("T3", "H1"))
    assert INSTRUMENTS == ("USDRUBF", "CNYRUBF", "GLDRUBF", "IMOEXF")
    assert TRUE_OOS_START == pd.Timestamp("2025-01-01", tz="Europe/Moscow")
    assert (BOOTSTRAP_ITERATIONS, BOOTSTRAP_SEED, FROZEN_TICK_SIZE) == (10_000, 5_102_025, .001)

@pytest.mark.parametrize("mutation", ["candidate_id", "parameter_hash", "parameters"])
def test_registry_mutations_fail_closed(tmp_path, mutation):
    data = json.loads(REGISTRY.read_text())
    data["candidates"][0][mutation] = "mutated" if mutation != "parameters" else {"ema_fast": 999}
    path = tmp_path / "registry.json"; path.write_text(json.dumps(data))
    with pytest.raises(RuntimeError): load_frozen_registry(path)


def test_context_is_cold_complete_local_day_blocks():
    idx = pd.date_range("2025-01-01 10:30", periods=5, freq="30min", tz="Europe/Moscow")
    frame = pd.DataFrame({"Open":range(5), "High":range(1,6), "Low":range(5), "Close":range(1,6)}, index=idx)
    context = four_bar_context(frame)
    assert len(context) == 1 and context.index[0] == idx[3] and context.index.min() >= TRUE_OOS_START


def test_exact_classification_boundaries_and_gates():
    good = {"total_trades":50, "expectancy":.1}
    assert classify(good, .95, 5, 3, True, True, .1) == "PASS"
    assert classify({**good,"total_trades":49}, .95, 5, 3, True, True, .1) == "BORDERLINE"
    assert classify({**good,"expectancy":0}, .99, 5, 5, True, True, .1) == "FAIL"
    assert classify(good, .50, 5, 5, True, True, .1) == "FAIL"
    for args in ((.94,5,5,True,True,.1),(.99,5,2,True,True,.1),(.99,5,5,False,True,.1),(.99,5,5,True,False,.1),(.99,5,5,True,True,0)):
        assert classify(good, *args) == "BORDERLINE"


def test_manifests_enforce_lifecycle_and_provenance():
    root = Path("TradingSystemLab/results/perpetual_v3/true_oos")
    summary = json.loads((root/"summary/manifest.json").read_text())
    assert summary["development_rows_admitted"] == 0 and summary["cold_start"] and summary["start_state"] == "FLAT"
    assert summary["C1_only"] and not summary["optimization"] and not summary["ranking"] and not summary["candidate_replacement"]
    assert summary["bootstrap"] == {"diagnostic_only":True,"iterations":10_000,"seed":5_102_025}
    for strategy, timeframe in STUDIES:
        study = json.loads((root/strategy/timeframe/"manifest.json").read_text())
        assert study["walk_forward_reference_commit"] == "d5aa616186c2750d5f0b0b9c60eddbf5d096c98f"
        assert study["candidate_id"] == EXPECTED_IDENTITIES[(strategy,timeframe)][0]
        assert study["development_rows_admitted"] == 0 and not study["development_state_reused"]


def test_trade_ids_and_oos_boundary():
    root = Path("TradingSystemLab/results/perpetual_v3/true_oos")
    for strategy, timeframe in STUDIES:
        trades = pd.read_csv(root/strategy/timeframe/"trades.csv")
        assert trades.trade_id.is_unique
        assert pd.to_datetime(trades.entry_time, utc=True).ge(TRUE_OOS_START.tz_convert("UTC")).all()
        assert pd.to_datetime(trades.exit_time, utc=True).ge(TRUE_OOS_START.tz_convert("UTC")).all()


def test_auditor_semantics_are_independent_of_production_runner():
    path = Path("TradingSystemLab/audit_perpetual_v3_phase5.py")
    tree = ast.parse(path.read_text(encoding="utf-8"))
    imports = {node.module or "" for node in ast.walk(tree)
               if isinstance(node, ast.ImportFrom)}
    assert "TradingSystemLab.true_oos.perpetual_v3_phase5" not in imports
    source = path.read_text(encoding="utf-8")
    for name in ("summary", "bootstrap", "classify", "execute", "load_true_oos", "reports"):
        assert f"import {name}" not in source


def test_two_actual_isolated_generations_and_canonical_closeout(tmp_path):
    first, second = tmp_path / "first", tmp_path / "second"
    run(DATA_ROOT, first)
    first_hashes = research_artifact_hashes(first)
    run(DATA_ROOT, second)
    assert len(first_hashes) == 50
    assert first_hashes == research_artifact_hashes(second)

    result = audit(first, check_git_trees=False)
    manifest = json.loads((first / "summary/manifest.json").read_text())
    assert manifest["status"] == "V3_PERPETUAL_PHASE_5_TRUE_OOS_COMPLETE"
    assert manifest["second_complete_execution_compared"] is True
    assert manifest["independently_regenerated_artifact_count"] == 50
    assert result["status"] == "V3_PERPETUAL_PHASE_5_TRUE_OOS_AUDIT_PASSED"
    assert result["closeout_consistency"] == "PASS"
    assert result["compared_artifact_sha256"] == first_hashes


def test_canonical_metrics_classification_and_coverage_do_not_drift():
    expected = {
        ("T2", "M30"): (361, 1.17764719099, .0919196380323, 33.1829893297, -29.8417906145, 1.11196374770, .8273, "BORDERLINE"),
        ("T2", "H1"): (172, 1.75760449523, .381021700154, 65.5357324265, -12.6292149420, 5.18921664788, .9919, "BORDERLINE"),
        ("T3", "M30"): (369, 1.97656824882, .424043791811, 156.472159178, -17.8307473060, 8.77541229726, 1., "PASS"),
        ("T3", "H1"): (199, 2.24544369911, .424276655880, 84.4310545202, -11.9772400216, 7.04929135328, .9999, "PASS"),
    }
    for (strategy, timeframe), values in expected.items():
        target = OUTPUT_ROOT / strategy / timeframe
        metrics = json.loads((target / "metrics.json").read_text())
        aggregate = metrics["aggregate"]
        assert aggregate["total_trades"] == values[0]
        assert tuple(aggregate[key] for key in
                     ("PF", "expectancy", "net_R", "max_drawdown", "recovery_factor")) == pytest.approx(values[1:6], abs=1e-9)
        assert metrics["bootstrap_probability_mean_R_gt_0"] == values[6]
        assert metrics["classification"] == values[7]
    manifest = json.loads((OUTPUT_ROOT / "summary/manifest.json").read_text())
    counts = {timeframe: {symbol: row["admitted_oos_rows"]
                          for symbol, row in coverage.items()}
              for timeframe, coverage in manifest["coverage"].items()}
    assert counts == {"M30": {"USDRUBF": 13715, "CNYRUBF": 13750,
                               "GLDRUBF": 15175, "IMOEXF": 15195},
                      "H1": {"USDRUBF": 7058, "CNYRUBF": 7093,
                              "GLDRUBF": 7834, "IMOEXF": 7853}}
    assert sum(sum(values.values()) for values in counts.values()) == 87673
    assert {row["first_admitted_oos_close"] for coverage in manifest["coverage"].values()
            for row in coverage.values()} == {"2025-01-03T10:00:00+03:00"}
    assert {row["last_admitted_oos_close"] for coverage in manifest["coverage"].values()
            for row in coverage.values()} == {"2026-09-16T00:00:00+03:00"}


def _copy_results(tmp_path: Path) -> Path:
    root = tmp_path / "true_oos"
    shutil.copytree(OUTPUT_ROOT, root)
    return root


@pytest.mark.parametrize("relative,mutate,error", [
    ("T2/M30/metrics.json", lambda value: value["aggregate"].__setitem__("expectancy", 99), "AGGREGATE"),
    ("T2/M30/metrics.json", lambda value: value.__setitem__("classification", "PASS"), "CLASSIFICATION_INVALID"),
    ("T2/M30/manifest.json", lambda value: value.__setitem__("candidate_id", "corrupt"), "FROZEN_IDENTITY_INVALID"),
    ("T2/M30/manifest.json", lambda value: value.__setitem__("frozen_parameter_hash", "0" * 64), "FROZEN_IDENTITY_INVALID"),
])
def test_json_mutations_fail_closed(tmp_path, relative, mutate, error):
    root = _copy_results(tmp_path)
    path = root / relative
    value = json.loads(path.read_text()); mutate(value); path.write_text(json.dumps(value))
    manifest_path = root / "summary/manifest.json"
    manifest = json.loads(manifest_path.read_text())
    manifest["artifact_sha256"][relative] = hashlib.sha256(path.read_bytes()).hexdigest()
    manifest_path.write_text(json.dumps(manifest))
    with pytest.raises(RuntimeError, match=error):
        audit(root, check_git_trees=False, finalize=False)


@pytest.mark.parametrize("relative,column,error", [
    ("T2/M30/bootstrap_report.csv", "probability_mean_R_gt_0", "BOOTSTRAP"),
    ("T2/M30/concentration_report.csv", "net_R_without_top5", "CONCENTRATION"),
])
def test_csv_mutations_fail_closed(tmp_path, relative, column, error):
    root = _copy_results(tmp_path); path = root / relative
    frame = pd.read_csv(path); frame.loc[0, column] += 1; frame.to_csv(path, index=False)
    manifest_path = root / "summary/manifest.json"
    manifest = json.loads(manifest_path.read_text())
    manifest["artifact_sha256"][relative] = hashlib.sha256(path.read_bytes()).hexdigest()
    manifest_path.write_text(json.dumps(manifest))
    with pytest.raises(RuntimeError, match=error):
        audit(root, check_git_trees=False, finalize=False)


def test_corrupt_declared_artifact_hash_fails_closed(tmp_path):
    root = _copy_results(tmp_path); path = root / "summary/manifest.json"
    manifest = json.loads(path.read_text())
    manifest["artifact_sha256"]["T2/M30/trades.csv"] = "0" * 64
    path.write_text(json.dumps(manifest))
    with pytest.raises(RuntimeError, match="ARTIFACT_HASH_INVALID"):
        audit(root, check_git_trees=False, finalize=False)
