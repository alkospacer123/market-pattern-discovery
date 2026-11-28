"""CC-07 admin-only V20 GUI adapter; stock operator retains trading authority.

Explicitly chosen single-account Intel deployment. The Streamlit process must
already be an elevated, locally bound administrator; no Windows identity,
FINAM token, V20 source or Task is edited by this module. Never auto-run.
"""
from __future__ import annotations

import csv
from datetime import datetime, timedelta, timezone
from hashlib import sha1
import json
import os
from pathlib import Path
import re
import secrets
import subprocess

ROBOTS = ("v20-shallow", "v20-obv", "v20-inside")
ACTIONS = ("start", "pause", "stop", "restart", "recover")
OPERATOR = Path(r"C:\Control Center\cc07-operator\cc07-v20-operator.ps1")
OPERATOR_BLOB = "27f16169c819bd06e267394215ba04a1dd7bd73c"
RELEASE = Path(r"C:\Control Center\data\private\cc07-v20-release.json")
GATEWAY_POLICY = Path(r"C:\Control Center\data\private\cc07-gateway-policy.json")
HEX = re.compile(r"[a-f0-9]{32}\Z")
SID = re.compile(r"S-[0-9]+(?:-[0-9]+)+\Z")

# These exact CC-07 codes are emitted only before any stock V20 action.
# Never label an unknown child failure as a safe preflight refusal.
RECOVER_PREFLIGHT_CODES = (
    "cc07_recovery_switch_not_halted",
    "cc07_recovery_stock_check_untrusted",
    "cc07_recovery_requires_halted_or_failed_cycle",
    "cc07_recovery_age_unknown",
    "cc07_recovery_code_missing",
    "cc07_recovery_halt_code_untrusted",
    "cc07_recovery_cycle_stale",
    "cc07_recovery_error_code_untrusted",
    "cc07_recovery_not_required",
)


def confirmation(robot, action):
    if robot not in ROBOTS or action not in ACTIONS:
        raise ValueError("CC07_ACTION_INVALID")
    return "cc07 " + action + " " + robot


def _private_folder(name):
    parent = RELEASE.parent
    if not parent.is_dir() or parent.is_symlink():
        raise ValueError("CC07_PRIVATE_UNAVAILABLE")
    folder = parent / name
    folder.mkdir(exist_ok=True)
    if not folder.is_dir() or folder.is_symlink():
        raise ValueError("CC07_PRIVATE_FOLDER_INVALID")
    return folder


def _request_file(request_id):
    if type(request_id) is not str or not HEX.fullmatch(request_id):
        raise ValueError("CC07_REQUEST_ID_INVALID")
    return _private_folder("cc07-requests") / (request_id + ".jsonl")


def _request_event(request_id, phase, **fields):
    path = _request_file(request_id)
    row = dict(schema="cc.v20.command-journal.v1", request_id=request_id,
               utc=datetime.now(timezone.utc).isoformat(), phase=phase, **fields)
    data = (json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n").encode("ascii")
    if len(data) > 2048:
        raise ValueError("CC07_REQUEST_JOURNAL_EVENT_SIZE")
    flags = os.O_WRONLY | os.O_CREAT | os.O_APPEND | getattr(os, "O_BINARY", 0)
    fd = os.open(path, flags, 0o600)
    try:
        if os.write(fd, data) != len(data):
            raise OSError("CC07_REQUEST_JOURNAL_SHORT_WRITE")
        os.fsync(fd)
    finally:
        os.close(fd)


def _request_events(request_id):
    path = _request_file(request_id)
    if not path.exists():
        return []
    if path.is_symlink() or path.stat().st_size > 65536:
        raise ValueError("CC07_REQUEST_JOURNAL_INVALID")
    events = []
    with path.open("r", encoding="ascii") as stream:
        for raw in stream:
            row = json.loads(raw)
            if (type(row) is not dict
                    or row.get("schema") != "cc.v20.command-journal.v1"
                    or row.get("request_id") != request_id
                    or type(row.get("phase")) is not str):
                raise ValueError("CC07_REQUEST_JOURNAL_RECORD_INVALID")
            events.append(row)
    if len(events) > 24:
        raise ValueError("CC07_REQUEST_JOURNAL_TOO_LARGE")
    return events


def _release_request():
    if not RELEASE.exists():
        return None
    if RELEASE.is_symlink() or RELEASE.stat().st_size > 1024:
        raise ValueError("CC07_RELEASE_RECOVERY_INVALID")
    row = json.loads(RELEASE.read_text(encoding="ascii"))
    request_id = row.get("request_id") if type(row) is dict else None
    if type(request_id) is not str or not HEX.fullmatch(request_id):
        raise ValueError("CC07_RELEASE_RECOVERY_INVALID")
    return row


def recovery_status():
    """Durable crash follow-up; never repeats or clears the original command."""
    pending = []
    release = _release_request()
    release_id = release.get("request_id") if release is not None else None
    folder = _private_folder("cc07-requests")
    for path in sorted(folder.glob("*.jsonl")):
        request_id = path.name[:-6]
        if not HEX.fullmatch(request_id):
            raise ValueError("CC07_REQUEST_JOURNAL_NAME_INVALID")
        events = _request_events(request_id)
        if not events or any(row["phase"] == "resolved" for row in events):
            continue
        finished = [row for row in events if row["phase"] == "finished"]
        decision = finished[-1].get("decision") if finished else None
        known = decision in {"EXECUTED", "ALREADY_HALTED", "REFUSED_PREFLIGHT"}
        if not known or release_id == request_id:
            pending.append((request_id, decision or "INTERRUPTED"))
    if release_id is not None and all(request_id != release_id for request_id, _ in pending):
        events = _request_events(release_id)
        if not any(row["phase"] == "resolved" for row in events):
            pending.append((release_id, "RELEASE_RECOVERY_REQUIRED"))
    if not pending:
        return {"decision": "RECOVERY_CLEAR"}
    request_id, phase = sorted(pending)[0]
    return {"decision": "RECOVERY_REQUIRED", "request_id": request_id, "phase": phase}


def _archive_release(request_id):
    release = _release_request()
    if release is None:
        return
    if release["request_id"] != request_id:
        raise ValueError("CC07_RELEASE_RECOVERY_ID_MISMATCH")
    destination = _private_folder("cc07-release-history") / (request_id + ".json")
    if destination.exists() or destination.is_symlink():
        raise ValueError("CC07_RELEASE_HISTORY_EXISTS")
    os.rename(RELEASE, destination)


def resolve_recovery(request_id, typed):
    """Archive evidence only after explicit independent operator reconciliation.

    This never dispatches the old action or creates ARM/Task/broker authority.
    """
    if not admin_ready():
        return {"decision": "REFUSED_ADMIN_OPERATOR_NOT_READY"}
    status = recovery_status()
    if status["decision"] == "RECOVERY_CLEAR":
        return {"decision": "ALREADY_RESOLVED", "request_id": request_id}
    if status.get("request_id") != request_id:
        return {"decision": "REFUSED_RECOVERY_ORDER", "request_id": request_id}
    release = _release_request()
    events = _request_events(request_id)
    prepared = next((row for row in events if row["phase"] == "prepared"), None)
    if prepared is None and type(release) is dict and release.get("request_id") == request_id:
        prepared = release
    if type(prepared) is not dict:
        return {"decision": "REFUSED_RECOVERY_IDENTITY"}
    robot, action = prepared.get("robot"), prepared.get("action")
    if robot not in ROBOTS or action not in ACTIONS:
        return {"decision": "REFUSED_RECOVERY_IDENTITY"}
    expected = "cc07 resolve " + robot + " " + action + " " + request_id
    if typed != expected:
        return {"decision": "REFUSED_CONFIRMATION", "request_id": request_id}
    _archive_release(request_id)
    _request_event(request_id, "resolved", robot=robot, action=action,
                   resolution="OPERATOR_TASK_SWITCH_AUDIT_AND_BROKER_RECONCILED_NO_RETRY")
    return {"decision": "RECONCILED_NO_RETRY", "request_id": request_id}


def _environment():
    if os.name != "nt" or os.environ.get("COMPUTERNAME", "").upper() != "URIU-PC":
        return False
    try:
        import ctypes
        if not ctypes.windll.shell32.IsUserAnAdmin():
            return False
        if not OPERATOR.is_file() or OPERATOR.is_symlink():
            return False
        b = OPERATOR.read_bytes()
        if not 1000 < len(b) < 32768:
            return False
        if sha1(b"blob " + str(len(b)).encode("ascii") + b"\0" + b).hexdigest() != OPERATOR_BLOB:
            return False
        # Do not run two control channels simultaneously.
        policy = json.loads(GATEWAY_POLICY.read_text(encoding="utf-8"))
        return policy.get("approved") is False
    except (OSError, ValueError, AttributeError, TypeError, KeyError):
        return False


def admin_ready():
    """Read-only, fail-closed readiness of the installed stock authority."""
    return _environment()


def _actor_sid():
    result = subprocess.run(["whoami.exe", "/user", "/fo", "csv", "/nh"],
                            capture_output=True, text=True, timeout=10,
                            check=False)
    if result.returncode != 0:
        raise ValueError("CC07_ACTOR_UNAVAILABLE")
    rows = list(csv.reader(result.stdout.splitlines()))
    if len(rows) != 1 or len(rows[0]) != 2 or SID.fullmatch(rows[0][1]) is None:
        raise ValueError("CC07_ACTOR_SID_INVALID")
    return rows[0][1]


def _release(robot, action, request_id, actor_sid):
    if not RELEASE.parent.is_dir() or RELEASE.parent.is_symlink():
        raise ValueError("CC07_PRIVATE_UNAVAILABLE")
    now = datetime.now(timezone.utc)
    row = {
        "schema": "cc.v20.release.v1", "approved": True,
        "robot": robot, "action": action, "request_id": request_id,
        "actor_sid": actor_sid, "issued_utc": now.isoformat(),
        "expires_utc": (now + timedelta(seconds=90)).isoformat(),
    }
    data = (json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n").encode("ascii")
    if len(data) > 1024:
        raise ValueError("CC07_RELEASE_SIZE")
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_BINARY", 0)
    fd = os.open(RELEASE, flags, 0o600)
    try:
        with os.fdopen(fd, "wb") as out:
            out.write(data)
            out.flush()
            os.fsync(out.fileno())
    except BaseException:
        RELEASE.unlink(missing_ok=True)
        raise


def submit(robot, action, typed):
    """One confirmed request; ambiguous outcomes remain durable across restart."""
    if type(robot) is not str or robot not in ROBOTS:
        return {"decision": "REFUSED_INVALID_ROBOT"}
    if type(action) is not str or action not in ACTIONS:
        return {"decision": "REFUSED_INVALID_ACTION"}
    if type(typed) is not str or typed != confirmation(robot, action):
        return {"decision": "REFUSED_CONFIRMATION"}
    if not admin_ready():
        return {"decision": "REFUSED_ADMIN_OPERATOR_NOT_READY"}
    try:
        pending = recovery_status()
    except (OSError, ValueError, TypeError, KeyError):
        return {"decision": "RECOVERY_REQUIRED", "phase": "DURABLE_STATE_UNTRUSTED"}
    if pending["decision"] != "RECOVERY_CLEAR":
        return pending
    request_id = secrets.token_hex(16)
    if not HEX.fullmatch(request_id):
        return {"decision": "REFUSED_REQUEST_ID"}
    release_created = False
    dispatched = False
    outcome = {"decision": "FAILED_UNKNOWN", "request_id": request_id}
    try:
        _request_event(request_id, "prepared", robot=robot, action=action)
        if action != "pause":
            _release(robot, action, request_id, _actor_sid())
            release_created = True
            _request_event(request_id, "release_created", robot=robot, action=action)
        args = ["powershell.exe", "-noprofile", "-executionpolicy", "bypass",
                "-file", str(OPERATOR), "-mode", "execute",
                "-robot", robot, "-action", action, "-requestid", request_id]
        _request_event(request_id, "dispatched", robot=robot, action=action)
        dispatched = True
        result = subprocess.run(
            args, input=typed + " " + request_id + "\n",
            text=True, capture_output=True, timeout=180, check=False,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
        if result.returncode == 0:
            if "cc07_result=verified_" + action in result.stdout.splitlines():
                outcome = {"decision": "EXECUTED", "request_id": request_id}
            elif (action == "pause"
                    and "cc07_result=already_halted_no_change" in result.stdout.splitlines()):
                outcome = {"decision": "ALREADY_HALTED", "request_id": request_id}
        if (outcome["decision"] == "FAILED_UNKNOWN" and action == "recover"
                and result.returncode != 0):
            stderr = getattr(result, "stderr", "") or ""
            if isinstance(stderr, str):
                for code in RECOVER_PREFLIGHT_CODES:
                    if code in stderr:
                        outcome = {"decision": "REFUSED_PREFLIGHT",
                                   "code": code, "request_id": request_id}
                        break
    except (OSError, ValueError, subprocess.SubprocessError):
        outcome = {"decision": "FAILED_UNKNOWN" if dispatched else "REFUSED_PREFLIGHT",
                   "request_id": request_id}
    try:
        _request_event(request_id, "finished", robot=robot, action=action,
                       decision=outcome["decision"])
        if release_created and outcome["decision"] != "FAILED_UNKNOWN":
            _archive_release(request_id)
    except (OSError, ValueError, TypeError, KeyError):
        outcome = {"decision": "FAILED_UNKNOWN", "request_id": request_id}
    return outcome
