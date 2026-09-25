"""Regression tests for the artifact-only independent Phase 5 closeout."""
from __future__ import annotations

import ast
import hashlib
import json
import shutil
import subprocess
from pathlib import Path

import pandas as pd
import pytest

from TradingSystemLab import audit_phase5_true_oos_v2 as closeout


ROOT = Path("TradingSystemLab/results/true_oos_v2")
EXPECTED = {"T2/M30": "BORDERLINE", "T2/H1": "BORDERLINE",
            "T3/M30": "BORDERLINE", "T3/H1": "BORDERLINE"}


def test_audit_is_independent_and_has_no_execution_imports():
    path = Path(closeout.__file__)
    tree = ast.parse(path.read_text(encoding="utf-8"))
    imported = {node.module or "" for node in ast.walk(tree)
                if isinstance(node, ast.ImportFrom)}
    assert "TradingSystemLab.true_oos.phase5_v2" not in imported
    source = path.read_text(encoding="utf-8")
    assert all(f"import {name}" not in source for name in ("summary", "bootstrap", "classify"))
    assert "load_true_oos" not in source
    assert "execute(" not in source


def test_independent_reconstruction_matches_all_committed_evidence():
    result = closeout.audit()
    assert result == {"status": "V2_FIVE_STAGE_CYCLE_CLOSEOUT_COMPLETE",
                      "classifications": EXPECTED}


def test_protected_phase_trees_are_unchanged():
    for commit, path in closeout.PROTECTED:
        assert subprocess.run(["git", "diff", "--quiet", commit, "--", path],
                              check=False).returncode == 0


def _copy_results(tmp_path: Path) -> Path:
    target = tmp_path / "true_oos_v2"
    shutil.copytree(ROOT, target)
    return target


def _rehash(root: Path, relative: str) -> None:
    manifest_path = root / "summary/manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["artifact_sha256"][relative] = hashlib.sha256((root / relative).read_bytes()).hexdigest()
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")


@pytest.mark.parametrize("kind,expected_error", [
    ("metric", "AGGREGATE"),
    ("bootstrap", "BOOTSTRAP"),
    ("classification", "CLASSIFICATION_INVALID"),
])
def test_corrupt_semantic_evidence_fails_closed(tmp_path: Path, kind: str, expected_error: str):
    root = _copy_results(tmp_path)
    if kind == "metric":
        relative = "T2/M30/metrics.json"
        value = json.loads((root / relative).read_text())
        value["aggregate"]["expectancy"] += 1
        (root / relative).write_text(json.dumps(value))
    elif kind == "bootstrap":
        relative = "T2/M30/bootstrap_report.csv"
        value = pd.read_csv(root / relative)
        value.loc[0, "probability_mean_R_gt_0"] = 0.1
        value.to_csv(root / relative, index=False)
    else:
        relative = "T2/M30/metrics.json"
        value = json.loads((root / relative).read_text())
        value["classification"] = "PASS"
        (root / relative).write_text(json.dumps(value))
    _rehash(root, relative)
    with pytest.raises(RuntimeError, match=expected_error):
        closeout.audit(root, check_git_trees=False)


def test_corrupt_artifact_hash_fails_closed(tmp_path: Path):
    root = _copy_results(tmp_path)
    manifest_path = root / "summary/manifest.json"
    manifest = json.loads(manifest_path.read_text())
    manifest["artifact_sha256"]["T2/M30/trades.csv"] = "0" * 64
    manifest_path.write_text(json.dumps(manifest))
    with pytest.raises(RuntimeError, match="ARTIFACT_HASH_INVALID"):
        closeout.audit(root, check_git_trees=False)


def test_state_documents_have_no_stale_current_claims():
    closeout._documentation_checks()
