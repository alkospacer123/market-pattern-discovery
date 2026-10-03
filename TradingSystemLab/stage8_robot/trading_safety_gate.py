"""Offline, fail-closed Stage 8.10.6 new-entry safety gate.

This module has no broker, order, authentication, or network capability.  The
kill switch inhibits new entries only; it neither authorizes nor implements
exits/cancels.  Those semantics belong to separately authorized later stages.
"""
from __future__ import annotations

import json
import os
import re
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .specification import PRODUCTION_SPECIFICATION_ID

KILL_SWITCH_SCHEMA = "stage8_trading_kill_switch.v1"
KILL_SWITCH_FILENAME = "stage8-trading-kill-switch.json"
HEARTBEAT_FILENAME = "stage8-heartbeat.json"
MAX_HEARTBEAT_AGE_SECONDS = 900
MAX_CLOCK_SKEW_SECONDS = 60
REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
REPOSITORY_OUTPUT_FORBIDDEN = "STAGE8_10_6_REPOSITORY_OUTPUT_FORBIDDEN"
ARM_NOT_AUTHORIZED = "STAGE8_TRADING_KILL_SWITCH_ARM_NOT_AUTHORIZED"
_HASH = re.compile(r"^[0-9A-Fa-f]{64}$")


def _outside_repository(path: Path) -> Path:
    resolved = path.resolve()
    if resolved == REPOSITORY_ROOT or REPOSITORY_ROOT in resolved.parents:
        raise ValueError(REPOSITORY_OUTPUT_FORBIDDEN)
    return resolved


def kill_switch_path(runtime_root: Path | str) -> Path:
    return _outside_repository(Path(runtime_root)) / "safety" / KILL_SWITCH_FILENAME


def heartbeat_path(runtime_root: Path | str) -> Path:
    return _outside_repository(Path(runtime_root)) / "diagnostics" / HEARTBEAT_FILENAME


def _timestamp(value: Any) -> datetime | None:
    if not isinstance(value, str):
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (ValueError, OverflowError):
        return None
    return parsed if parsed.tzinfo is not None and parsed.utcoffset() is not None else None


def load_kill_switch(runtime_root: Path | str) -> tuple[dict[str, Any] | None, str | None]:
    path = kill_switch_path(runtime_root)
    if not path.is_file():
        return None, "KILL_SWITCH_MISSING"
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return None, "KILL_SWITCH_INVALID"
    if not isinstance(value, dict) or value.get("schema_id") != KILL_SWITCH_SCHEMA:
        return None, "KILL_SWITCH_INVALID"
    if value.get("production_specification_id") != PRODUCTION_SPECIFICATION_ID:
        return None, "KILL_SWITCH_PRODUCTION_ID_MISMATCH"
    if value.get("state") not in {"HALTED", "ARMED"}:
        return None, "KILL_SWITCH_INVALID"
    if type(value.get("generation")) is not int or value["generation"] < 1 or _timestamp(value.get("updated_utc")) is None:
        return None, "KILL_SWITCH_INVALID"
    return value, None


def write_kill_switch(runtime_root: Path | str, state: str, *, allow_arm: bool = False,
                      now: datetime | None = None) -> dict[str, Any]:
    """Atomically publish state; ARMED requires explicit synthetic/future opt-in."""
    if state not in {"HALTED", "ARMED"}:
        raise ValueError("STAGE8_TRADING_KILL_SWITCH_STATE_INVALID")
    if state == "ARMED" and allow_arm is not True:
        raise PermissionError(ARM_NOT_AUTHORIZED)
    destination = kill_switch_path(runtime_root)  # validate before mkdir
    previous, _ = load_kill_switch(runtime_root)
    generation = previous["generation"] + 1 if previous else 1
    observed = now or datetime.now(timezone.utc)
    if observed.tzinfo is None or observed.utcoffset() is None:
        raise ValueError("STAGE8_TRADING_KILL_SWITCH_TIMESTAMP_INVALID")
    record = {"schema_id": KILL_SWITCH_SCHEMA,
              "production_specification_id": PRODUCTION_SPECIFICATION_ID,
              "state": state, "generation": generation,
              "updated_utc": observed.astimezone(timezone.utc).isoformat()}
    destination.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=f".{KILL_SWITCH_FILENAME}.", suffix=".tmp",
                                               dir=destination.parent)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as stream:
            json.dump(record, stream, sort_keys=True, separators=(",", ":"))
            stream.write("\n"); stream.flush(); os.fsync(stream.fileno())
        os.replace(temporary, destination)
        try:
            directory_fd = os.open(destination.parent, os.O_RDONLY)
            try: os.fsync(directory_fd)
            finally: os.close(directory_fd)
        except OSError:
            pass
    finally:
        try: os.unlink(temporary)
        except FileNotFoundError: pass
    return record


def emergency_halt(runtime_root: Path | str, *, now: datetime | None = None) -> dict[str, Any]:
    return write_kill_switch(runtime_root, "HALTED", now=now)


def evaluate_new_entry_gate(*, runtime_root: Path | str, now: datetime,
                            execution_authorized: bool = False) -> dict[str, Any]:
    """Answer local eligibility only.  Every error and non-exact value blocks."""
    reasons: list[str] = []
    result: dict[str, Any] = {
        "production_specification_id": PRODUCTION_SPECIFICATION_ID,
        "kill_switch_state": None, "kill_switch_valid": False,
        "execution_authorized": execution_authorized is True,
        "heartbeat_valid": False, "heartbeat_fresh": False,
        "api_contact_fresh": False, "health_status": None,
        "reconciliation_status": None, "observer_entries_enabled": None,
        "unresolved_order_count": None, "consecutive_failures": None,
        "account_hash_valid": False,
    }
    if now.tzinfo is None or now.utcoffset() is None:
        reasons.append("HEARTBEAT_INVALID")
    try:
        switch, switch_error = load_kill_switch(runtime_root)
    except Exception:
        switch, switch_error = None, "KILL_SWITCH_INVALID"
    if switch_error: reasons.append(switch_error)
    else:
        result["kill_switch_valid"] = True; result["kill_switch_state"] = switch["state"]
        if switch["state"] == "HALTED": reasons.append("KILL_SWITCH_HALTED")
    if execution_authorized is not True: reasons.append("EXECUTION_NOT_AUTHORIZED")

    try:
        path = heartbeat_path(runtime_root)
        if not path.is_file():
            reasons.append("HEARTBEAT_MISSING"); heartbeat = None
        else:
            heartbeat = json.loads(path.read_text(encoding="utf-8"))
            if not isinstance(heartbeat, dict): raise ValueError
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError):
        heartbeat = None; reasons.append("HEARTBEAT_INVALID")
    except Exception:
        heartbeat = None; reasons.append("HEARTBEAT_INVALID")
    if heartbeat is not None:
        result.update(health_status=heartbeat.get("health_status"), reconciliation_status=heartbeat.get("reconciliation_status"),
                      observer_entries_enabled=heartbeat.get("entries_enabled"), unresolved_order_count=heartbeat.get("unresolved_order_count"),
                      consecutive_failures=heartbeat.get("consecutive_failures"))
        checks = [
            (heartbeat.get("production_id") == PRODUCTION_SPECIFICATION_ID, "HEARTBEAT_PRODUCTION_ID_MISMATCH"),
            (heartbeat.get("mode") == "REAL_READONLY", "HEARTBEAT_MODE_INVALID"),
            (heartbeat.get("health_status") == "HEALTHY", "HEARTBEAT_NOT_HEALTHY"),
            (heartbeat.get("reconciliation_status") == "PASS", "RECONCILIATION_NOT_PASS"),
            (heartbeat.get("entries_enabled") is False, "OBSERVER_ENTRIES_ENABLED"),
            (type(heartbeat.get("unresolved_order_count")) is int and heartbeat.get("unresolved_order_count") == 0, "UNRESOLVED_ORDERS_PRESENT"),
            (heartbeat.get("failure_code") is None, "FAILURE_LATCH_PRESENT"),
            (type(heartbeat.get("consecutive_failures")) is int and heartbeat.get("consecutive_failures") == 0, "CONSECUTIVE_FAILURES_NONZERO"),
            (type(heartbeat.get("cycle_count")) is int and heartbeat.get("cycle_count") >= 1, "CYCLE_COUNT_INVALID"),
        ]
        for valid, code in checks:
            if not valid: reasons.append(code)
        stamp = _timestamp(heartbeat.get("timestamp")); contact = _timestamp(heartbeat.get("last_successful_finam_api_contact"))
        if stamp is None: reasons.append("HEARTBEAT_INVALID")
        elif now.tzinfo is not None:
            age = (now - stamp).total_seconds()
            if age < -MAX_CLOCK_SKEW_SECONDS: reasons.append("HEARTBEAT_CLOCK_SKEW")
            elif age > MAX_HEARTBEAT_AGE_SECONDS: reasons.append("HEARTBEAT_STALE")
            else: result["heartbeat_fresh"] = True
        if contact is None: reasons.append("HEARTBEAT_INVALID")
        elif now.tzinfo is not None:
            age = (now - contact).total_seconds()
            if age < -MAX_CLOCK_SKEW_SECONDS: reasons.append("FINAM_CONTACT_CLOCK_SKEW")
            elif age > MAX_HEARTBEAT_AGE_SECONDS: reasons.append("FINAM_CONTACT_STALE")
            else: result["api_contact_fresh"] = True
        result["account_hash_valid"] = isinstance(heartbeat.get("account_hash"), str) and bool(_HASH.fullmatch(heartbeat["account_hash"]))
        if not result["account_hash_valid"]: reasons.append("ACCOUNT_HASH_INVALID")
        result["heartbeat_valid"] = not any(code in reasons for code in ("HEARTBEAT_INVALID", "HEARTBEAT_MISSING"))
    reasons = list(dict.fromkeys(reasons))
    opened = not reasons
    result.update(entry_gate_open=opened, decision="OPEN" if opened else "BLOCKED", reason_codes=reasons)
    return result
