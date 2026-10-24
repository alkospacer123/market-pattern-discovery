"""CC-04: one-shot staging observation from V20-07's *existing* check-only wrappers.

Never run start/stop/restart, never touch FINAM, token stores or Windows Task
state. The trusted V20 controller is checked against its accepted Git blob.
The V20 check itself enforces its task-owner SID; do not bypass that boundary.
"""
from datetime import datetime, timezone
from hashlib import sha1
import os
from pathlib import Path
import subprocess

from .v20_contract import ROBOTS, unconnected

OPERATOR_DIR = Path(r"C:\V20Lab\operator")
CONTROLLER_BLOB = "6905945c34bb14da119f6a1f7a6e3e79edf46be0"
SOURCE_SHA = "610109b736c53a5cc1025657291e272b1136b254"
IDS = {"V20_SHALLOW": "v20-shallow", "V20_OBV": "v20-obv",
       "V20_INSIDE": "v20-inside"}
FIELDS = {"V20_OP_ROBOT", "V20_OP_TASK_STATE", "V20_OP_TASK_PRINCIPAL_SID_MATCH",
          "V20_OP_SOURCE_SHA", "V20_OP_LIVE", "V20_OP_TRADING_TOKEN",
          "V20_OP_EXECUTION", "V20_OP_WORKER_PROCESS_COUNT", "V20_OP_LAST_STATUS",
          "V20_OP_KILL_SWITCH", "V20_OP_RECONCILIATION", "V20_OP_TASK_DISABLED",
          "V20_OP_TRADES", "V20_OP_STOPS", "V20_OP_WARNINGS",
          "V20_OP_LAST_CYCLES", "V20_OP_LAST_CYCLE_LINES", "V20_OP_CYCLE_AT",
          "V20_OP_CYCLE", "V20_OP_FAIL"}
SINGLES = FIELDS - {"V20_OP_CYCLE_AT", "V20_OP_CYCLE"}
MAX_OUTPUT = 8192


def _source_verified(robot):
    """No execution from a changed controller/wrapper or reparse-point leaf."""
    if robot not in IDS or OPERATOR_DIR.is_symlink():
        return False
    controller = OPERATOR_DIR / "operator-v20.ps1"
    wrapper = OPERATOR_DIR / (IDS[robot] + "-check.ps1")
    if any(p.is_symlink() or not p.is_file() for p in (controller, wrapper)):
        return False
    source = controller.read_bytes()
    if not 0 < len(source) < 32768:
        return False
    git_blob = sha1(b"blob " + str(len(source)).encode("ascii") + b"\0" + source).hexdigest()
    if git_blob != CONTROLLER_BLOB:
        return False
    expected = ("& (Join-Path $PSScriptRoot 'operator-v20.ps1') "
                "-Robot '" + IDS[robot] + "' -Mode 'check'\nexit $LASTEXITCODE")
    actual = wrapper.read_text(encoding="utf-8-sig")
    if len(actual) > 512 or actual.replace("\r\n", "\n").strip() != expected:
        return False
    return True


def parse_check(raw, robot, at):
    """Accept only a complete, self-consistent, fresh invocation result."""
    if robot not in IDS or at.tzinfo is None or type(raw) is not str or len(raw) > MAX_OUTPUT:
        raise ValueError("INVALID_OPERATOR_OUTPUT")
    values = {}
    for line in raw.splitlines():
        if not line.startswith("V20_OP_") or "=" not in line or len(line) > 512:
            raise ValueError("UNEXPECTED_OPERATOR_OUTPUT")
        key, value = line.split("=", 1)
        if key not in FIELDS or (key in SINGLES and key in values):
            raise ValueError("UNEXPECTED_OPERATOR_FIELD")
        if key not in SINGLES:  # Historical cycle details are not trusted as runtime state.
            continue
        values[key] = value.strip()
    expected = {
        "V20_OP_ROBOT": IDS[robot],
        "V20_OP_TASK_STATE": "Disabled",
        "V20_OP_TASK_PRINCIPAL_SID_MATCH": "PASS",
        "V20_OP_SOURCE_SHA": SOURCE_SHA,
        "V20_OP_LIVE": "OFF",
        "V20_OP_TRADING_TOKEN": "NOT_CONFIGURED",
        "V20_OP_EXECUTION": "BLOCKED_PLACEHOLDER",
        "V20_OP_LAST_STATUS": "NOT_CONFIGURED_STAGING",
        "V20_OP_KILL_SWITCH": "NOT_CONFIGURED_STAGING",
        "V20_OP_RECONCILIATION": "NOT_AVAILABLE_STAGING",
        "V20_OP_TASK_DISABLED": "PASS",
        "V20_OP_TRADES": "NOT_AVAILABLE_STAGING",
        "V20_OP_STOPS": "NOT_AVAILABLE_STAGING",
        "V20_OP_WARNINGS": "NOT_AVAILABLE_STAGING",
    }
    if any(values.get(k) != v for k, v in expected.items()) or "V20_OP_FAIL" in values:
        raise ValueError("INCONSISTENT_STAGING")
    workers = values.get("V20_OP_WORKER_PROCESS_COUNT")
    if workers not in ("0", "UNAVAILABLE"):
        raise ValueError("WORKER_NOT_CONFIRMED_STOPPED")
    return dict(unconnected(robot), status="STAGING",
                reason="VERIFIED_OPERATOR_STAGING", observed_at=at.astimezone(timezone.utc),
                task_state="DISABLED", workers_observed=0 if workers == "0" else None,
                live_state="OFF", execution_state="BLOCKED_PLACEHOLDER",
                reconciliation_state="NOT_AVAILABLE", last_error_code="UNKNOWN")


def check_one(robot, now):
    if robot not in ROBOTS:
        raise ValueError("ROBOT_NOT_ALLOWED")
    if os.name != "nt":
        return unconnected(robot, "WINDOWS_ONLY")
    try:
        if not _source_verified(robot):
            return unconnected(robot, "OPERATOR_SOURCE_NOT_VERIFIED")
        script = str(OPERATOR_DIR / (IDS[robot] + "-check.ps1"))
        environment = {k: os.environ[k] for k in (
            "SYSTEMROOT", "WINDIR", "SYSTEMDRIVE", "TEMP", "TMP",
            "OS", "COMPUTERNAME", "USERPROFILE", "APPDATA") if k in os.environ}
        exe = str(Path(os.environ["SYSTEMROOT"]) / "System32" / "WindowsPowerShell"
                  / "v1.0" / "powershell.exe")
        result = subprocess.run(
            [exe, "-NoProfile", "-NonInteractive",
             "-ExecutionPolicy", "Bypass", "-File", script],
            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, timeout=15,
            creationflags=subprocess.CREATE_NO_WINDOW, env=environment,
            check=False)
        if result.returncode != 0:
            if b"V20_OP_FAIL=V20_OP_OPERATOR_SID_MISMATCH" in result.stdout[:MAX_OUTPUT]:
                return unconnected(robot, "OPERATOR_SID_MISMATCH")
            return unconnected(robot, "OPERATOR_CHECK_FAILED")
        return parse_check(result.stdout.decode("utf-8-sig"), robot, now)
    except (OSError, ValueError, UnicodeError, subprocess.TimeoutExpired):
        return unconnected(robot, "OPERATOR_CHECK_UNAVAILABLE")


def acquire_staging(now):
    """Only called during the existing, explicitly pressed manual refresh."""
    return {robot: check_one(robot, datetime.now(timezone.utc)) for robot in ROBOTS}
