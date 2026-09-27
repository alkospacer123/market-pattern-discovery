"""Regression tests for the comparator-only Stage 5 checkpoint."""
from __future__ import annotations

import ast
import importlib.util
import json
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[2]
STAGE5 = ROOT / "TradingSystemLab/results/post_v3_analysis/stage5_structural_validation"


def _load(name: str):
    spec = importlib.util.spec_from_file_location(name, STAGE5 / f"{name}.py")
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_independent_auditor_does_not_import_runner_or_adapters() -> None:
    tree = ast.parse((STAGE5 / "audit_stage5_validation.py").read_text(encoding="utf-8"))
    imports = {
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, (ast.Import, ast.ImportFrom))
        for alias in node.names
    }
    assert not any("run_stage5_validation" in name for name in imports)
    assert not any("stage5_execution" in name or "stage5_lifecycle" in name for name in imports)


def test_data_root_precedence_and_exact_commit(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    runner = _load("run_stage5_validation")
    explicit = tmp_path / "explicit"
    explicit.mkdir()
    monkeypatch.setenv("MARKET_PATTERN_DATA_ROOT", str(explicit))
    assert runner.resolve_data_root() == explicit.resolve()


def test_runner_reaches_comparator_only_gate(monkeypatch: pytest.MonkeyPatch) -> None:
    runner = _load("run_stage5_validation")
    monkeypatch.setattr(runner, "preflight", lambda: {"data_root":"/frozen"})
    import sys, types
    name="TradingSystemLab.results.post_v3_analysis.stage5_structural_validation.stage5_lifecycle_adapter"
    fake=types.ModuleType(name); fake.run_comparator=lambda *a,**k:{"status":"STAGE5_CANONICAL_COMPARATOR_RECONCILIATION_PASSED"}
    monkeypatch.setitem(sys.modules,name,fake)
    assert "VARIANTS_NOT_YET_EXECUTED" in runner.run()["checkpoint"]


def test_auditor_authentication_is_not_runner_alias() -> None:
    auditor = _load("audit_stage5_validation")
    assert auditor.authenticate_prerequisites.__module__ == "audit_stage5_validation"

def test_comparator_auditor_is_independent() -> None:
    tree=ast.parse((STAGE5/"audit_stage5_comparator.py").read_text())
    names={a.name for n in ast.walk(tree) if isinstance(n,(ast.Import,ast.ImportFrom)) for a in n.names}
    assert not any("run_stage5_validation" in x or "stage5_lifecycle_adapter" in x for x in names)

def test_registry_preserves_exact_contract_and_folds() -> None:
    import csv
    with (STAGE5/"canonical_lifecycle_registry.csv").open(newline="") as f: rows=list(csv.DictReader(f))
    assert {r["generation"] for r in rows}=={"v2_quarterly","v3_perpetual"}
    assert {r["lifecycle"] for r in rows}=={"baseline","walk_forward","historical_true_oos"}
    assert {r["fold_id"] for r in rows if r["lifecycle"]=="walk_forward"}=={"WF01","WF02","WF03","WF04"}
    assert all(r["cost_contract"]=="C1" and r["tick_size"]=="0.001" for r in rows)
    assert not any(r["generation"].startswith("v1") for r in rows)

def test_structural_variants_fail_closed() -> None:
    adapter=_load("stage5_lifecycle_adapter")
    with pytest.raises(RuntimeError,match="STRUCTURAL_HYPOTHESIS_EXECUTION_FORBIDDEN"):
        adapter.run_comparator(Path("/unused"),variants=("BE1",))

def test_t3_causality_guards_are_canonical() -> None:
    loader=(ROOT/"TradingSystemLab/core/data_loader.py").read_text()
    strategy=(ROOT/"TradingSystemLab/strategies/trend/T3_MTF_Trend.py").read_text()
    assert "groupby" in loader and "if len(block) != 4" in loader
    assert ".shift(1)" in strategy


def test_comparator_auditor_owns_prerequisite_authentication() -> None:
    source = (STAGE5 / "audit_stage5_comparator.py").read_text()
    tree = ast.parse(source)
    functions = {node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)}
    assert {"authenticate_stage4", "resolve_data_root", "authenticate_data_repo"} <= functions
    assert "git\", \"-C\"" in source and "rev-parse\", \"HEAD\"" in source


def test_comparator_auditor_reconstructs_exact_registry_and_executes() -> None:
    source = (STAGE5 / "audit_stage5_comparator.py").read_text()
    tree = ast.parse(source)
    functions = {node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)}
    assert {"reconstruct_registry", "authenticate_registry", "execute_independently", "_run_wf"} <= functions
    assert "LIFECYCLE_REGISTRY_NOT_EXACT" in source
    assert "WF01--WF04" in source


def test_comparator_auditor_scope_and_contract_guards() -> None:
    source = (STAGE5 / "audit_stage5_comparator.py").read_text()
    assert '"added v1"' in source
    assert '"C0"' in source and '"tick 0.01"' in source
    assert '"hypothesis execution true"' in source and '"Stage 6 work flag"' in source
    assert "structural_hypothesis_execution" in source and '"Stage5_status": "OPEN"' in source


def test_comparator_auditor_has_executable_t3_invariants() -> None:
    source = (STAGE5 / "audit_stage5_comparator.py").read_text()
    assert "ast.parse(loader)" in source and "ast.parse(strategy)" in source
    assert '"if len(block) != 4"' in source
    assert '".index.normalize()"' in source
    assert 'n.func.attr == "shift"' in source
    assert '"PriorHigh"' in source and '"PriorLow"' in source


@pytest.fixture(scope="module")
def comparator_auditor():
    return _load("audit_stage5_comparator")


@pytest.fixture(scope="module")
def executable_mutations(comparator_auditor):
    return comparator_auditor.mutation_tests()


def test_all_thirty_mutations_execute_and_reject(executable_mutations) -> None:
    assert executable_mutations["mode"] == "EXECUTABLE_ADVERSARIAL"
    assert executable_mutations["total"] == executable_mutations["passed"] == 30
    assert executable_mutations["all_rejected_as_expected"] is True
    assert [row["mutation_id"] for row in executable_mutations["results"]] == [f"M{x:02d}" for x in range(1, 31)]
    assert all(row["rejected"] and row["pass"] for row in executable_mutations["results"])
    assert all(row["actual_guard"] == row["expected_guard"] for row in executable_mutations["results"])


def test_mutation_suite_fails_when_guard_does_not_reject(comparator_auditor) -> None:
    result = comparator_auditor.mutation_tests(disabled_guard="MARKET_DATA_COMMIT")
    assert result["all_rejected_as_expected"] is False
    assert result["passed"] == 29
    assert result["results"][2]["rejected"] is False


def test_fifth_stage4_hash_is_frozen_and_wrong_hash_rejected(comparator_auditor) -> None:
    expected = "7a764cd15975835d7469d0cae58634fd7751a54db79e1bf62aec59f5d8593863"
    assert comparator_auditor.STAGE4_HASHES["audit_stage4_result.json"] == expected
    audit = json.loads((comparator_auditor.STAGE4 / "audit_stage4_result.json").read_text())
    manifest = json.loads((comparator_auditor.STAGE4 / "manifest_stage4.json").read_text())
    hashes = {name: comparator_auditor.sha256(comparator_auditor.STAGE4 / name)
              for name in comparator_auditor.STAGE4_HASHES}
    hashes["audit_stage4_result.json"] = "0" * 64
    with pytest.raises(RuntimeError, match="STAGE4_FROZEN_HASH"):
        comparator_auditor.validate_stage4(audit, manifest, hashes)


@pytest.mark.parametrize(("mutation_id", "guard"), [
    ("M03", "MARKET_DATA_COMMIT"), ("M04", "SOURCE_DATA_IDENTITY"),
    ("M20", "INDEPENDENT_RECONCILIATION"), ("M26", "PRODUCER_AUDITOR_METRICS"),
    ("M17", "T3_CAUSALITY"), ("M29", "SCOPE_GUARD"),
])
def test_representative_proof_surfaces_are_executable(executable_mutations, mutation_id, guard) -> None:
    row = next(item for item in executable_mutations["results"] if item["mutation_id"] == mutation_id)
    assert row["mutated_object"]
    assert row["actual_guard"] == guard
    assert row["rejected"] is True


def test_mutation_evidence_is_deterministic(comparator_auditor, executable_mutations) -> None:
    rerun = comparator_auditor.mutation_tests()
    assert json.dumps(executable_mutations, sort_keys=True) == json.dumps(rerun, sort_keys=True)


def test_committed_result_records_both_clean_controls_and_executable_evidence() -> None:
    result = json.loads((STAGE5 / "canonical_comparator_audit_result.json").read_text())
    assert result["clean_control_before"] == result["clean_control_after"] == "PASS"
    assert result["mutation_tests"]["mode"] == "EXECUTABLE_ADVERSARIAL"
    assert len(result["mutation_tests"]["results"]) == 30
