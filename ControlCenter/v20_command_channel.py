"""CC-07 UI-to-controller command requests, never command execution.

Untrusted Streamlit does not invoke shell/FINAM/Tasks or read the controller's
admin-only release or audit. The independent privileged worker is the sole
authority; this UI only writes bounded intent to its separately ACL-protected
inbox. Without a fresh admin-owned gateway attestation it FAILS CLOSED.
"""
from __future__ import annotations

from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import secrets

from cc.providers.windows_file import read_windows

ROBOT_NAMES = ("v20-shallow", "v20-obv", "v20-inside")
ACTIONS = ("start", "pause", "stop", "restart")
SCHEMA = "cc.v20.control-intent.v1"
GATEWAY_SCHEMA = "cc.v20.gateway-status.v1"
RECEIPT_SCHEMA = "cc.v20.control-receipt.v1"
OPERATOR_BLOB = "91a83e388978ded33525357397716d5fd509fc2a"
STATUS_ROOT = r"C:\Control Center\data\cc07-public"
REQUEST_ROOT = Path(r"C:\Control Center\data\cc07-inbox")
REQ_ID = re.compile(r"[a-f0-9]{32}\Z")
STATUS_KEYS = {"schema", "status", "operator_blob", "published_at", "expires_at"}
RECEIPT_KEYS = {"schema", "request_id", "robot", "action", "decision", "observed_at"}
DECISIONS = {"ACCEPTED_NOT_EXECUTED", "REFUSED", "EXECUTED", "FAILED_UNKNOWN"}


def _utc(value):
    if type(value) is not str or not 20 <= len(value) <= 40:
        raise ValueError("CC07_TIME_INVALID")
    t = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if t.tzinfo is None:
        raise ValueError("CC07_TIME_NAIVE")
    return t.astimezone(timezone.utc)


def confirmation(robot, action):
    if robot not in ROBOT_NAMES or action not in ACTIONS:
        raise ValueError("CC07_ACTION_INVALID")
    return "cc07 " + action + " " + robot


def gateway_ready(now=None):
    """Only a fresh, admin-owned ACL-verified status can unlock intent UI."""
    if os.name != "nt":
        return False
    when = datetime.now(timezone.utc) if now is None else now
    if when.tzinfo is None:
        return False
    try:
        raw = read_windows(STATUS_ROOT, "gateway.json", 1024, admin_policy=True)
        status = json.loads(raw.decode("utf-8"))
        if (type(status) is not dict or set(status) != STATUS_KEYS
                or status["schema"] != GATEWAY_SCHEMA
                or status["status"] != "ONLINE"
                or status["operator_blob"] != OPERATOR_BLOB):
            return False
        created = _utc(status["published_at"])
        expires = _utc(status["expires_at"])
        age = (when.astimezone(timezone.utc) - created).total_seconds()
        remaining = (expires - when.astimezone(timezone.utc)).total_seconds()
        return -5 <= age <= 15 and 0 < remaining <= 20 and expires > created
    except (OSError, ValueError, TypeError, KeyError, UnicodeError):
        return False


def submit(robot, action, typed, *, now=None, id_factory=None):
    """Queue one confirmed request; returning QUEUED never means EXECUTED."""
    if type(robot) is not str or robot not in ROBOT_NAMES:
        return {"decision": "REFUSED_INVALID_ROBOT"}
    if type(action) is not str or action not in ACTIONS:
        return {"decision": "REFUSED_INVALID_ACTION"}
    if type(typed) is not str or typed != confirmation(robot, action):
        return {"decision": "REFUSED_CONFIRMATION"}
    if not gateway_ready(now):
        return {"decision": "REFUSED_GATEWAY_OFFLINE"}
    request_id = secrets.token_hex(16) if id_factory is None else id_factory()
    if type(request_id) is not str or REQ_ID.fullmatch(request_id) is None:
        return {"decision": "REFUSED_REQUEST_ID"}
    when = datetime.now(timezone.utc) if now is None else now.astimezone(timezone.utc)
    req = {"schema": SCHEMA, "request_id": request_id, "robot": robot,
           "action": action, "confirmed": True, "created_at": when.isoformat()}
    path = REQUEST_ROOT / (request_id + ".json")
    try:
        if not REQUEST_ROOT.is_dir() or REQUEST_ROOT.is_symlink():
            return {"decision": "REFUSED_INBOX_UNAVAILABLE"}
        data = (json.dumps(req, sort_keys=True, separators=(",", ":")) + "\n").encode("ascii")
        if len(data) > 512:
            return {"decision": "REFUSED_SIZE"}
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
        if hasattr(os, "O_BINARY"):
            flags |= os.O_BINARY
        fd = os.open(path, flags, 0o600)
        try:
            with os.fdopen(fd, "wb") as f:
                f.write(data)
                f.flush()
                os.fsync(f.fileno())
        except BaseException:
            try:
                path.unlink()
            except OSError:
                pass
            raise
        return {"decision": "QUEUED_NOT_EXECUTED", "request_id": request_id}
    except (OSError, ValueError):
        return {"decision": "REFUSED_INBOX_UNAVAILABLE"}


def receipt(request_id):
    """Explicit bounded readonly query; no polling or execution."""
    if os.name != "nt" or type(request_id) is not str or not REQ_ID.fullmatch(request_id):
        return {"decision": "RECEIPT_UNAVAILABLE"}
    try:
        raw = read_windows(STATUS_ROOT, "receipt-" + request_id + ".json",
                           1024, admin_policy=True)
        value = json.loads(raw.decode("utf-8"))
        if (type(value) is not dict or set(value) != RECEIPT_KEYS
                or value["schema"] != RECEIPT_SCHEMA
                or value["request_id"] != request_id
                or value["robot"] not in ROBOT_NAMES
                or value["action"] not in ACTIONS
                or value["decision"] not in DECISIONS):
            return {"decision": "RECEIPT_INVALID"}
        _utc(value["observed_at"])
        return value
    except (OSError, ValueError, TypeError, KeyError, UnicodeError):
        return {"decision": "RECEIPT_UNAVAILABLE"}
