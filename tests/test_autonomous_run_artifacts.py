from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

from market_pattern_discovery.orchestration import ARTIFACT_FILES, AutonomousRunArtifacts


class EmptyMemory:
    def research_attempts(self): return []
    def knowledge_records(self): return []
    def scientific_findings(self):
        return [{"hypothesis": {"hypothesis_id": "h-2"}},
                {"hypothesis": {"hypothesis_id": "h-1"}},
                {"hypothesis": None}]

    def strategy_candidates(self): return {}
    def trading_candidates(self): return {}
    def executable_signal_definitions(self): return {}
    def backtest_results(self): return {}
    def validation_reports(self): return {}
    def strategy_rankings(self): return {}


def test_export_creates_complete_deterministic_data_free_bundle(tmp_path):
    repository = tmp_path / "repo"
    repository.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=repository, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.invalid"],
                   cwd=repository, check=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=repository, check=True)
    (repository / "tracked").write_text("code\n", encoding="utf-8")
    subprocess.run(["git", "add", "tracked"], cwd=repository, check=True)
    subprocess.run(["git", "commit", "-qm", "fixture"], cwd=repository, check=True)
    commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=repository,
                            check=True, capture_output=True, text=True).stdout.strip()
    data_manifest = tmp_path / "external-data-manifest.json"
    data_manifest.write_text('{"files":["outside-repository.csv"]}\n', encoding="utf-8")
    expected_data_digest = hashlib.sha256(data_manifest.read_bytes()).hexdigest()
    output = tmp_path / "autonomous_runs"

    exporter = AutonomousRunArtifacts(output)
    first = exporter.export(EmptyMemory(), data_manifest=data_manifest, repository=repository,
                            run_id="test-run", seed=17)
    run = output / "test-run"
    bytes_before = {path.name: path.read_bytes() for path in run.iterdir()}
    second = exporter.export(EmptyMemory(), data_manifest=data_manifest, repository=repository,
                             run_id="test-run", seed=17)

    assert first == second
    assert {path.name for path in run.iterdir()} == {
        "manifest.json", "source_commit.txt", "data_manifest.sha256", *ARTIFACT_FILES,
        "audit_metadata.json", "direction_bias_report.json", "horizon_report.json"}
    assert bytes_before == {path.name: path.read_bytes() for path in run.iterdir()}
    assert run.joinpath("source_commit.txt").read_text().strip() == commit
    assert run.joinpath("data_manifest.sha256").read_text().strip() == expected_data_digest
    assert run.joinpath("hypotheses.jsonl").read_text().splitlines() == [
        '{"hypothesis_id":"h-1"}', '{"hypothesis_id":"h-2"}']
    manifest = json.loads(run.joinpath("manifest.json").read_text())
    assert manifest["status"] == "READY_FOR_AUDIT"
    assert manifest["true_oos_2025_accessed"] is False
    assert manifest["zero_look_ahead"] is True
    assert manifest["artifacts"]["hypotheses.jsonl"]["records"] == 2
    assert AutonomousRunArtifacts.verify(run) == manifest


def test_export_requires_existing_data_manifest(tmp_path):
    exporter = AutonomousRunArtifacts(tmp_path / "run")
    try:
        exporter.export(EmptyMemory(), data_manifest=tmp_path / "missing",
                        repository=tmp_path)
    except FileNotFoundError as error:
        assert "data manifest does not exist" in str(error)
    else:
        raise AssertionError("missing data manifest must fail closed")


def test_bundle_survives_process_boundary(tmp_path):
    """Process A writes and exits; unrelated Process B verifies disk bytes."""
    repository = tmp_path / "repo"
    repository.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=repository, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.invalid"], cwd=repository, check=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=repository, check=True)
    (repository / "tracked").write_text("code\n")
    subprocess.run(["git", "add", "tracked"], cwd=repository, check=True)
    subprocess.run(["git", "commit", "-qm", "fixture"], cwd=repository, check=True)
    data_manifest = tmp_path / "data.json"
    data_manifest.write_text('{"locked_year":2025}\n')
    root = tmp_path / "persistent"
    process_a = """
from market_pattern_discovery.orchestration import AutonomousRunArtifacts
class M:
 def research_attempts(self): return []
 def knowledge_records(self): return []
 def scientific_findings(self): return []
 def trading_candidates(self): return {}
 def strategy_candidates(self): return {}
 def executable_signal_definitions(self): return {}
 def backtest_results(self): return {}
 def validation_reports(self): return {}
 def strategy_rankings(self): return {}
AutonomousRunArtifacts(r'%s').export(M(), data_manifest=r'%s', repository=r'%s', run_id='process-test', seed=1)
""" % (root, data_manifest, repository)
    environment = {**os.environ, "PYTHONPATH": str(Path(__file__).parents[1] / "src")}
    subprocess.run([sys.executable, "-c", process_a], check=True, env=environment)
    process_b = """
from market_pattern_discovery.orchestration import AutonomousRunArtifacts
m = AutonomousRunArtifacts.verify(r'%s')
assert m['status'] == 'READY_FOR_AUDIT'
print('PERSISTENCE TEST PASS')
""" % (root / "process-test")
    result = subprocess.run([sys.executable, "-c", process_b], check=True, env=environment,
                            capture_output=True, text=True)
    assert result.stdout.strip() == "PERSISTENCE TEST PASS"
    assert AutonomousRunArtifacts(root).latest() == root / "process-test"


def test_ready_for_audit_fails_closed_without_files_or_hashes(tmp_path):
    run = tmp_path / "broken"
    run.mkdir()
    (run / "manifest.json").write_text(json.dumps({
        "status": "READY_FOR_AUDIT", "source_commit": "abc",
        "data_manifest_sha256": "def", "artifacts": {},
    }))
    try:
        AutonomousRunArtifacts.verify(run)
    except ValueError as error:
        assert "required artifacts absent" in str(error)
    else:
        raise AssertionError("READY_FOR_AUDIT without artifacts must fail closed")
