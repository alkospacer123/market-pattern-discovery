"""Regression tests for the fail-closed Stage 5 checkpoint."""
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


def test_runner_remains_fail_closed_after_authentication(monkeypatch: pytest.MonkeyPatch) -> None:
    runner = _load("run_stage5_validation")
    monkeypatch.setattr(runner, "preflight", lambda: {})
    with pytest.raises(RuntimeError, match="STAGE5_FAIL_CLOSED"):
        runner.run()


def test_auditor_authentication_is_not_runner_alias() -> None:
    auditor = _load("audit_stage5_validation")
    assert auditor.authenticate_prerequisites.__module__ == "audit_stage5_validation"

