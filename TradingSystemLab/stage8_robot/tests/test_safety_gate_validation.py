import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest

from TradingSystemLab.stage8_robot.safety_gate_validation import (
    PRODUCTION_HALT_INVALID,
    add_production_halt_observation,
    validate,
)
from TradingSystemLab.stage8_robot.specification import PRODUCTION_SPECIFICATION_ID
from TradingSystemLab.stage8_robot.trading_safety_gate import REPOSITORY_ROOT, write_kill_switch


def test_matrix_is_deterministic(tmp_path):
    first = validate(workspace=tmp_path / "first")
    second = validate(workspace=tmp_path / "second")
    assert first == second
    assert (first["synthetic_case_count"], first["synthetic_open_case_count"], first["synthetic_blocked_case_count"]) == (25, 1, 24)
    assert first["synthetic_matrix_validation"] == first["emergency_halt_validation"] == "PASS"
    assert "production_kill_switch_initialized" not in first


def _physical_cli(tmp_path, production_root, report=None):
    report = report or tmp_path / "external-report.json"
    completed = subprocess.run([
        sys.executable, "-m", "TradingSystemLab.stage8_robot.safety_gate_validation",
        "--runtime-root", str(tmp_path / "synthetic"),
        "--production-runtime-root", str(production_root), "--report", str(report),
    ], capture_output=True, text=True, check=False)
    return completed, report


def test_physical_report_records_only_sanitized_production_halt(tmp_path):
    production = tmp_path / "production"
    write_kill_switch(production, "HALTED", now=datetime(2030, 1, 2, tzinfo=timezone.utc))
    switch = production / "safety" / "stage8-trading-kill-switch.json"
    before = switch.read_bytes()
    completed, report = _physical_cli(tmp_path, production)
    assert completed.returncode == 0, completed.stderr
    result = json.loads(report.read_text())
    assert result["production_kill_switch_initialized"] is True
    assert result["production_kill_switch_final_state"] == "HALTED"
    assert result["production_kill_switch_valid"] is True
    assert switch.read_bytes() == before
    serialized = report.read_text().lower()
    for forbidden in ("generation", "production_runtime_root", "credential", "jwt", "dpapi"):
        assert forbidden not in serialized


@pytest.mark.parametrize("kind", ["missing", "malformed", "armed", "wrong-production"])
def test_physical_report_fails_closed_for_non_halted_switch(tmp_path, kind):
    production = tmp_path / "production"
    if kind == "malformed":
        path = production / "safety" / "stage8-trading-kill-switch.json"; path.parent.mkdir(parents=True); path.write_text("{")
    elif kind == "armed":
        write_kill_switch(production, "ARMED", allow_arm=True, now=datetime(2030, 1, 2, tzinfo=timezone.utc))
    elif kind == "wrong-production":
        path = production / "safety" / "stage8-trading-kill-switch.json"; path.parent.mkdir(parents=True)
        path.write_text(json.dumps({"schema_id":"stage8_trading_kill_switch.v1","production_specification_id":PRODUCTION_SPECIFICATION_ID+"-wrong","state":"HALTED","generation":1,"updated_utc":"2030-01-02T00:00:00+00:00"}))
    completed, report = _physical_cli(tmp_path, production)
    assert completed.returncode != 0
    assert PRODUCTION_HALT_INVALID in completed.stderr
    assert not report.exists()


def test_physical_paths_inside_repository_are_rejected(tmp_path):
    production = tmp_path / "production"
    write_kill_switch(production, "HALTED")
    completed, _ = _physical_cli(tmp_path, production, REPOSITORY_ROOT / "forbidden-report.json")
    assert completed.returncode != 0 and "STAGE8_10_6_REPOSITORY_OUTPUT_FORBIDDEN" in completed.stderr
    with pytest.raises(ValueError, match="STAGE8_10_6_PRODUCTION_RUNTIME_IN_REPOSITORY_FORBIDDEN"):
        add_production_halt_observation(validate(workspace=tmp_path / "matrix"), production_runtime_root=REPOSITORY_ROOT)
