from __future__ import annotations

import hashlib
import json
import subprocess

from market_pattern_discovery.orchestration import ARTIFACT_FILES, AutonomousRunArtifacts


class EmptyMemory:
    def scientific_findings(self):
        return [{"hypothesis": {"hypothesis_id": "h-2"}},
                {"hypothesis": {"hypothesis_id": "h-1"}},
                {"hypothesis": None}]

    def strategy_candidates(self): return {}
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
    first = exporter.export(EmptyMemory(), data_manifest=data_manifest, repository=repository)
    bytes_before = {path.name: path.read_bytes() for path in output.iterdir()}
    second = exporter.export(EmptyMemory(), data_manifest=data_manifest, repository=repository)

    assert first == second
    assert {path.name for path in output.iterdir()} == {
        "manifest.json", "source_commit.txt", "data_manifest.sha256", *ARTIFACT_FILES}
    assert bytes_before == {path.name: path.read_bytes() for path in output.iterdir()}
    assert output.joinpath("source_commit.txt").read_text().strip() == commit
    assert output.joinpath("data_manifest.sha256").read_text().strip() == expected_data_digest
    assert output.joinpath("hypotheses.jsonl").read_text().splitlines() == [
        '{"hypothesis_id":"h-1"}', '{"hypothesis_id":"h-2"}']
    manifest = json.loads(output.joinpath("manifest.json").read_text())
    assert manifest["true_oos_2025_accessed"] is False
    assert manifest["zero_look_ahead"] is True
    assert manifest["artifacts"]["hypotheses.jsonl"]["records"] == 2


def test_export_requires_existing_data_manifest(tmp_path):
    exporter = AutonomousRunArtifacts(tmp_path / "run")
    try:
        exporter.export(EmptyMemory(), data_manifest=tmp_path / "missing",
                        repository=tmp_path)
    except FileNotFoundError as error:
        assert "data manifest does not exist" in str(error)
    else:
        raise AssertionError("missing data manifest must fail closed")
