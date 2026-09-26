"""Regression tests for the comparator-only Stage 5 checkpoint."""
from __future__ import annotations

import ast
import importlib.util
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
