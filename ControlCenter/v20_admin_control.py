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
ACTIONS = ("start", "pause", "stop", "restart")
OPERATOR = Path(r"C:\Control Center\cc07-operator\cc07-v20-operator.ps1")
OPERATOR_BLOB = "91a83e388978ded33525357397716d5fd509fc2a"
RELEASE = Path(r"C:\Control Center\data\private\cc07-v20-release.json")
GATEWAY_POLICY = Path(r"C:\Control Center\data\private\cc07-gateway-policy.json")
HEX = re.compile(r"[a-f0-9]{32}\Z")
SID = re.compile(r"S-[0-9]+(?:-[0-9]+)+\Z")


def confirmation(robot, action):
    if robot not in ROBOTS or action not in ACTIONS:
        raise ValueError("CC07_ACTION_INVALID")
    return "cc07 " + action + " " + robot


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
    """One confirmed request; SUCCESS only after pinned CC-07 operator proof.

    No dispatch on page load. NEVER retry an ambiguous failure automatically.
    """
    if type(robot) is not str or robot not in ROBOTS:
        return {"decision": "REFUSED_INVALID_ROBOT"}
    if type(action) is not str or action not in ACTIONS:
        return {"decision": "REFUSED_INVALID_ACTION"}
    if type(typed) is not str or typed != confirmation(robot, action):
        return {"decision": "REFUSED_CONFIRMATION"}
    if not admin_ready():
        return {"decision": "REFUSED_ADMIN_OPERATOR_NOT_READY"}
    request_id = secrets.token_hex(16)
    if not HEX.fullmatch(request_id):
        return {"decision": "REFUSED_REQUEST_ID"}
    release_created = False
    dispatched = False
    try:
        if action != "pause":
            _release(robot, action, request_id, _actor_sid())
            release_created = True
        # Do NOT use -NonInteractive: the frozen CC-07 operator requires a
        # second, exact Read-Host confirmation from redirected stdin.
        args = ["powershell.exe", "-noprofile", "-executionpolicy", "bypass",
                "-file", str(OPERATOR), "-mode", "execute",
                "-robot", robot, "-action", action, "-requestid", request_id]
        dispatched = True
        result = subprocess.run(
            args, input=typed + " " + request_id + "\n",
            text=True, capture_output=True, timeout=180, check=False,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
        if result.returncode == 0:
            if "cc07_result=verified_" + action in result.stdout.splitlines():
                return {"decision": "EXECUTED", "request_id": request_id}
            if (action == "pause"
                    and "cc07_result=already_halted_no_change" in result.stdout.splitlines()):
                return {"decision": "ALREADY_HALTED", "request_id": request_id}
        return {"decision": "FAILED_UNKNOWN", "request_id": request_id}
    except (OSError, ValueError, subprocess.SubprocessError):
        return {"decision": "FAILED_UNKNOWN" if dispatched else "REFUSED_PREFLIGHT"}
    finally:
        if release_created:
            # Remove only the release created for this exact request.
            try:
                doc = json.loads(RELEASE.read_text(encoding="utf-8"))
                if doc.get("request_id") == request_id:
                    RELEASE.unlink()
            except (OSError, ValueError):
                pass
