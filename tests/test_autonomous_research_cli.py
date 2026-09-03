from __future__ import annotations

import importlib.util
import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "scripts" / "run_autonomous_research.py"
SPEC = importlib.util.spec_from_file_location("run_autonomous_research", SCRIPT)
assert SPEC and SPEC.loader
cli = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(cli)


def _environment():
    environment = os.environ.copy()
    source = str(SCRIPT.parents[1] / "src")
    environment["PYTHONPATH"] = os.pathsep.join(
        filter(None, (source, environment.get("PYTHONPATH"))))
    return environment


def test_help_works():
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--help"], capture_output=True, text=True,
        env=_environment())
    assert result.returncode == 0
    assert "--data-root" in result.stdout
    assert "--mode {once,continuous}" in result.stdout
    assert "--track {known,unknown,mixed}" in result.stdout


def test_unknown_track_is_recognized_before_required_argument_validation():
    """Guard the exact invocation that exposed stale-checkout CLI behavior."""
    result = subprocess.run([
        sys.executable, str(SCRIPT), "--track", "unknown",
    ], capture_output=True, text=True, env=_environment())

    assert result.returncode != 0
    assert "the following arguments are required" in result.stderr
    assert "unrecognized arguments: --track unknown" not in result.stderr


def test_once_mode_invokes_worker(monkeypatch, tmp_path, capsys):
    calls = []

    @dataclass
    class Result:
        cycle_number: int
        status: str
        cycle_id: str
        failures: dict
        validation: dict

    class Worker:
        def __init__(self, scheduler, memory, state_directory, *, track):
            calls.append((scheduler, memory, state_directory, track))

        def run_once(self, *, cycle_number, budget):
            calls.append((cycle_number, budget))
            return Result(cycle_number, "COMPLETED", "cycle", {}, {})

    monkeypatch.setattr(cli, "AutonomousResearchWorker", Worker)
    assert cli.main([
        "--data-root", str(tmp_path / "data"),
        "--memory-root", str(tmp_path / "memory"),
        "--output-root", str(tmp_path / "output"),
        "--budget", "3", "--mode", "once",
    ]) == 0
    assert calls[-1] == (0, 3)
    assert '"status": "COMPLETED"' in capsys.readouterr().out


def test_unknown_track_is_forwarded_to_worker(monkeypatch, tmp_path):
    tracks = []

    @dataclass
    class Result:
        cycle_number: int = 0
        status: str = "SEARCH_SPACE_EXHAUSTED"
        cycle_id: str | None = None
        failures: dict = None
        validation: dict = None

    class Worker:
        def __init__(self, scheduler, memory, state_directory, *, track):
            tracks.append(track)

        def run_once(self, *, cycle_number, budget):
            return Result(failures={}, validation={})

    monkeypatch.setattr(cli, "AutonomousResearchWorker", Worker)
    assert cli.main([
        "--data-root", str(tmp_path / "data"),
        "--memory-root", str(tmp_path / "memory"),
        "--output-root", str(tmp_path / "output"),
        "--budget", "1", "--track", "unknown",
    ]) == 0
    assert tracks == ["unknown"]


def test_invalid_mode_fails(tmp_path):
    result = subprocess.run([
        sys.executable, str(SCRIPT),
        "--data-root", str(tmp_path / "data"),
        "--memory-root", str(tmp_path / "memory"),
        "--output-root", str(tmp_path / "output"),
        "--budget", "1", "--mode", "sometimes",
    ], capture_output=True, text=True, env=_environment())
    assert result.returncode != 0
    assert "invalid choice" in result.stderr


def test_invalid_track_fails(tmp_path):
    result = subprocess.run([
        sys.executable, str(SCRIPT),
        "--data-root", str(tmp_path / "data"),
        "--memory-root", str(tmp_path / "memory"),
        "--output-root", str(tmp_path / "output"),
        "--budget", "1", "--track", "experimental",
    ], capture_output=True, text=True, env=_environment())
    assert result.returncode != 0
    assert "invalid choice" in result.stderr
