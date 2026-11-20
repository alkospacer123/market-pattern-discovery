"""CC-04 V20-07 staging: truthful offline evidence and fail-closed boundaries."""
from datetime import datetime, timedelta, timezone
from hashlib import sha1
from pathlib import Path

import pytest
from cc import v20_staging as stage
from cc.v20_contract import ROBOTS, age, heartbeat_health


def log(robot="V20_SHALLOW", workers="0"):
    fields = {
        "V20_OP_ROBOT": stage.IDS[robot],
        "V20_OP_TASK_STATE": "Disabled",
        "V20_OP_TASK_PRINCIPAL_SID_MATCH": "PASS",
        "V20_OP_SOURCE_SHA": stage.SOURCE_SHA,
        "V20_OP_LIVE": "OFF",
        "V20_OP_TRADING_TOKEN": "NOT_CONFIGURED",
        "V20_OP_EXECUTION": "BLOCKED_PLACEHOLDER",
        "V20_OP_WORKER_PROCESS_COUNT": workers,
        "V20_OP_LAST_STATUS": "NOT_CONFIGURED_STAGING",
        "V20_OP_KILL_SWITCH": "NOT_CONFIGURED_STAGING",
        "V20_OP_LAST_CYCLES": "NOT_AVAILABLE_STAGING",
        "V20_OP_TRADES": "NOT_AVAILABLE_STAGING",
        "V20_OP_STOPS": "NOT_AVAILABLE_STAGING",
        "V20_OP_WARNINGS": "NOT_AVAILABLE_STAGING",
        "V20_OP_RECONCILIATION": "NOT_AVAILABLE_STAGING",
        "V20_OP_TASK_DISABLED": "PASS",
    }
    return "\n".join(k + "=" + v for k, v in fields.items()) + "\n"


@pytest.mark.parametrize("robot", ROBOTS)
def test_real_operator_shape_is_staging_never_healthy(robot):
    at = datetime.now(timezone.utc)
    value = stage.parse_check(log(robot), robot, at)
    assert value["status"] == "STAGING"
    assert value["task_state"] == "DISABLED"
    assert value["workers_observed"] == 0 and value["live_state"] == "OFF"
    assert value["kill_switch"] == "UNKNOWN"
    assert value["last_error_code"] == "UNKNOWN"
    assert value["reconciliation_state"] == "NOT_AVAILABLE"
    assert value["heartbeat_at"] is None
    assert heartbeat_health(value, at) == "UNKNOWN"
    assert age(value, at + timedelta(seconds=301))["status"] == "STALE"


def test_unavailable_worker_is_not_zero():
    at = datetime.now(timezone.utc)
    value = stage.parse_check(log(workers="UNAVAILABLE"), "V20_SHALLOW", at)
    assert value["workers_observed"] is None
    with pytest.raises(ValueError):
        stage.parse_check(log(workers="2"), "V20_SHALLOW", at)


@pytest.mark.parametrize("fragment", [
    "V20_OP_LIVE=OFF", "V20_OP_TASK_DISABLED=PASS",
    "V20_OP_TASK_PRINCIPAL_SID_MATCH=PASS", "V20_OP_SOURCE_SHA=" + stage.SOURCE_SHA,
    "V20_OP_KILL_SWITCH=NOT_CONFIGURED_STAGING",
    "V20_OP_RECONCILIATION=NOT_AVAILABLE_STAGING",
])
def test_missing_or_conflicting_assertion_never_produces_stage(fragment):
    at = datetime.now(timezone.utc)
    original = log()
    with pytest.raises(ValueError):
        stage.parse_check(original.replace(fragment + "\n", ""), "V20_SHALLOW", at)
    with pytest.raises(ValueError):
        stage.parse_check(original + fragment + "\n", "V20_SHALLOW", at)


def test_wrong_robot_script_and_unexpected_console_output_rejected():
    at = datetime.now(timezone.utc)
    with pytest.raises(ValueError):
        stage.parse_check(log("V20_OBV"), "V20_SHALLOW", at)
    with pytest.raises(ValueError):
        stage.parse_check("side effect!\n" + log(), "V20_SHALLOW", at)
    with pytest.raises(ValueError):
        stage.parse_check(log() + "V20_OP_START=SUCCESS\n", "V20_SHALLOW", at)


def test_verify_only_existing_check_wrapper_and_exact_controller_blob(tmp_path, monkeypatch):
    monkeypatch.setattr(stage, "OPERATOR_DIR", tmp_path)
    controller = tmp_path / "operator-v20.ps1"
    controller.write_bytes(b"# test fixture, never executed\n")
    payload = controller.read_bytes()
    blob = sha1(b"blob " + str(len(payload)).encode() + b"\0" + payload).hexdigest()
    monkeypatch.setattr(stage, "CONTROLLER_BLOB", blob)
    wrapper = tmp_path / "v20-shallow-check.ps1"
    wrapper.write_text(
        "& (Join-Path $PSScriptRoot 'operator-v20.ps1') "
        "-Robot 'v20-shallow' -Mode 'check'\nexit $LASTEXITCODE\n",
        encoding="utf-8")
    assert stage._source_verified("V20_SHALLOW")
    wrapper.write_text(wrapper.read_text(encoding="utf-8").replace("-Mode 'check'", "-Mode 'stop'"),
                       encoding="utf-8")
    assert not stage._source_verified("V20_SHALLOW")
    wrapper.write_text("& (Join-Path $PSScriptRoot 'operator-v20.ps1') -Robot "
                       "'v20-shallow' -Mode 'check'\nexit $LASTEXITCODE\n", encoding="utf-8")
    controller.write_bytes(payload + b"write-output 'mutated'\n")
    assert not stage._source_verified("V20_SHALLOW")


def test_per_robot_failure_does_not_mask_other_staging(monkeypatch):
    at = datetime.now(timezone.utc)
    def fake(robot, observed):
        if robot == "V20_OBV":
            raise_case = False  # no process invocation; an independent offline failure
            assert not raise_case
            from cc.v20_contract import unconnected
            return unconnected(robot, "OPERATOR_SID_MISMATCH")
        return stage.parse_check(log(robot), robot, observed)
    monkeypatch.setattr(stage, "check_one", fake)
    results = stage.acquire_staging(at)
    assert [results[x]["status"] for x in ROBOTS] == ["STAGING", "NOT_CONNECTED", "STAGING"]
    assert results["V20_OBV"]["reason"] == "OPERATOR_SID_MISMATCH"
