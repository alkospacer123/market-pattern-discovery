"""Pure strict read-only V20 snapshot contract. No market/trading/broker I/O."""
from datetime import datetime, timezone
from hashlib import sha256
import json
import re

ROBOTS = ("V20_SHALLOW", "V20_OBV", "V20_INSIDE")
LABELS = {"V20_SHALLOW": "Shallow", "V20_OBV": "OBV", "V20_INSIDE": "Inside"}
NAMES = {"V20_SHALLOW": "v20-shallow.json", "V20_OBV": "v20-obv.json",
         "V20_INSIDE": "v20-inside.json"}
SCHEMA = "cc.v20.readonly.v1"
FIELDS = {"schema_id", "robot_id", "account_alias", "observed_at", "heartbeat_at",
          "engine_state", "task_state", "kill_switch", "cycle", "positions_local",
          "stops_local", "unresolved_local", "last_error_code", "events", "payload_sha256"}
EVENT = {"at", "cycle", "result", "code"}
CODE = re.compile(r"[A-Z][A-Z0-9_]{0,47}")
ALIAS = re.compile(r"V20-[A-Z0-9_-]{2,32}")
STATES = {"HEALTHY", "HALTED", "FAULT", "UNKNOWN"}
TASKS = {"RUNNING", "DISABLED", "READY", "UNKNOWN"}
KILLS = {"ARMED", "HALTED", "UNKNOWN"}
RESULTS = {"PASS", "FAULT"}
MAX_BYTES = 32768
TTL = 300


def _pairs(items):
    result = {}
    for key, value in items:
        if key in result:
            raise ValueError("DUPLICATE_KEY")
        result[key] = value
    return result


def _bad_constant(value):
    raise ValueError("NONFINITE_JSON")


def _clock(value):
    if type(value) is not str or len(value) > 48:
        raise ValueError("INVALID_TIME")
    try:
        t = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        raise ValueError("INVALID_TIME") from None
    if t.tzinfo is None:
        raise ValueError("NAIVE_TIME")
    return t.astimezone(timezone.utc)


def _number(value):
    if value is None:
        return None
    if type(value) is not int or not 0 <= value <= 10**12:
        raise ValueError("INVALID_COUNT")
    return value


def digest(document):
    copy = {key: value for key, value in document.items() if key != "payload_sha256"}
    wire = json.dumps(copy, sort_keys=True, separators=(",", ":"), ensure_ascii=True,
                      allow_nan=False).encode("utf-8")
    return sha256(wire).hexdigest()


def unconnected(robot, reason="NOT_CONNECTED"):
    if robot not in ROBOTS:
        raise ValueError("ROBOT_NOT_ALLOWED")
    return {"robot_id": robot, "status": "NOT_CONNECTED", "reason": reason,
            "observed_at": None, "heartbeat_at": None, "cycle": None,
            "positions_local": None, "stops_local": None, "unresolved_local": None,
            "engine_state": "UNKNOWN", "task_state": "UNKNOWN", "kill_switch": "UNKNOWN",
            "last_error_code": "UNKNOWN", "events": (), "account_alias": None}


def parse(raw, robot, now, account_alias):
    """Decode a bounded, canonical-hash-checked report from a separately trusted CC source.

    Digest detects accidental corruption; authenticity relies on the pinned NTFS
    source root, trusted publisher ACL and administrator-owned installed policy.
    """
    if robot not in ROBOTS or now.tzinfo is None or type(account_alias) is not str:
        raise ValueError("BAD_INPUT")
    if type(raw) is not bytes or not 0 < len(raw) <= MAX_BYTES:
        raise ValueError("INVALID_SIZE")
    value = json.loads(raw.decode("utf-8"), object_pairs_hook=_pairs,
                       parse_constant=_bad_constant)
    if (type(value) is not dict or set(value) != FIELDS or value["schema_id"] != SCHEMA
            or value["robot_id"] != robot or value["account_alias"] != account_alias
            or not ALIAS.fullmatch(account_alias)):
        raise ValueError("IDENTITY_MISMATCH")
    if (type(value["payload_sha256"]) is not str
            or not re.fullmatch("[a-f0-9]{64}", value["payload_sha256"])
            or value["payload_sha256"] != digest(value)):
        raise ValueError("HASH_MISMATCH")
    if (value["engine_state"] not in STATES or value["task_state"] not in TASKS
            or value["kill_switch"] not in KILLS or type(value["last_error_code"]) is not str
            or not CODE.fullmatch(value["last_error_code"])):
        raise ValueError("BAD_STATE")
    now = now.astimezone(timezone.utc)
    at = _clock(value["observed_at"])
    heartbeat = _clock(value["heartbeat_at"]) if value["heartbeat_at"] is not None else None
    if (at - now).total_seconds() > 30 or (
            heartbeat is not None and (heartbeat - at).total_seconds() > 30):
        raise ValueError("FUTURE_OBSERVATION")
    cycle = _number(value["cycle"])
    positions = _number(value["positions_local"])
    stops = _number(value["stops_local"])
    unresolved = _number(value["unresolved_local"])
    events = value["events"]
    if type(events) is not list or len(events) > 10:
        raise ValueError("EVENT_COUNT")
    checked = []
    previous = None
    for event in events:
        if (type(event) is not dict or set(event) != EVENT
                or event["result"] not in RESULTS or type(event["code"]) is not str
                or not CODE.fullmatch(event["code"])):
            raise ValueError("EVENT_SCHEMA")
        event_at = _clock(event["at"])
        number = _number(event["cycle"])
        if number is None or event_at > at or (previous is not None and event_at < previous):
            raise ValueError("EVENT_ORDER")
        previous = event_at
        checked.append({"at": event_at, "cycle": number, "result": event["result"],
                        "code": event["code"]})
    age = (now - at).total_seconds()
    status = "STALE" if age > TTL or age < 0 else value["engine_state"]
    if status == "HEALTHY":
        if (heartbeat is None or not 0 <= (now - heartbeat).total_seconds() <= TTL
                or value["task_state"] != "RUNNING" or value["kill_switch"] != "ARMED"
                or unresolved is None or unresolved != 0):
            status = "UNKNOWN"
    return {"robot_id": robot, "status": status, "reason": "LOCAL_REPORT",
            "observed_at": at, "heartbeat_at": heartbeat, "cycle": cycle,
            "positions_local": positions, "stops_local": stops, "unresolved_local": unresolved,
            "engine_state": value["engine_state"], "task_state": value["task_state"],
            "kill_switch": value["kill_switch"], "last_error_code": value["last_error_code"],
            "events": tuple(checked), "account_alias": account_alias}


def age(report, now):
    """Latch STALE/UNKNOWN; never resurrect expired data after a clock rollback."""
    if report["status"] in ("STALE", "NOT_CONNECTED", "UNKNOWN"):
        return report
    if now.tzinfo is None:
        return dict(report, status="UNKNOWN")
    now = now.astimezone(timezone.utc)
    observed = report["observed_at"]
    heartbeat = report["heartbeat_at"]
    if (now < observed or (now-observed).total_seconds() > TTL
            or report["status"] == "HEALTHY" and (heartbeat is None or now < heartbeat
                                                   or (now-heartbeat).total_seconds() > TTL)):
        return dict(report, status="STALE", cycle=None, positions_local=None,
                    stops_local=None, unresolved_local=None)
    return report
