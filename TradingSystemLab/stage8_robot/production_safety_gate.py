"""Production-aware Stage 8.12.4 new-entry safety gate.

Unlike the historical REAL_READONLY observer gate, this gate does not require a
flat account.  A production service may legitimately carry frozen N4 positions.
It requires that those positions/orders have already reconciled against durable
production state before a fresh HEALTHY heartbeat is published.
"""
from __future__ import annotations

import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .specification import ACTIVE_IDENTITY, INSTRUMENTS, PRODUCTION_SPECIFICATION_ID
from .trading_safety_gate import (
    MAX_CLOCK_SKEW_SECONDS,
    MAX_HEARTBEAT_AGE_SECONDS,
    load_kill_switch,
)

PRODUCTION_HEARTBEAT_SCHEMA = "stage8_12_4_production_heartbeat.v1"
PRODUCTION_HEARTBEAT_FILENAME = "stage8-12-4-production-heartbeat.json"
REPOSITORY_ROOT = Path(__file__).resolve().parents[2]


class ProductionSafetyError(RuntimeError):
    pass


def _outside_repository(path: Path) -> Path:
    resolved = path.resolve()
    if resolved == REPOSITORY_ROOT or REPOSITORY_ROOT in resolved.parents:
        raise ProductionSafetyError("STAGE8_12_4_REPOSITORY_HEARTBEAT_FORBIDDEN")
    return resolved


def production_heartbeat_path(runtime_root: Path | str) -> Path:
    return (
        _outside_repository(Path(runtime_root))
        / "diagnostics"
        / PRODUCTION_HEARTBEAT_FILENAME
    )


def _timestamp(value: Any) -> datetime | None:
    if not isinstance(value, str):
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (ValueError, OverflowError):
        return None
    return parsed if parsed.tzinfo is not None and parsed.utcoffset() is not None else None

def _validated_position_protection(value: Any) -> list[dict[str, Any]]:
    """Validate one protection record per open frozen N4 position."""
    if not isinstance(value, list):
        raise ProductionSafetyError("STAGE8_12_4_POSITION_PROTECTION_INVALID")
    normalized: list[dict[str, Any]] = []
    instruments: set[str] = set()
    trade_ids: set[str] = set()
    stop_ids: set[str] = set()
    required = {
        "instrument",
        "trade_id",
        "expected_position_quantity",
        "covered_quantity",
        "active_stop_order_ids",
    }
    for row in value:
        if not isinstance(row, dict) or set(row) != required:
            raise ProductionSafetyError("STAGE8_12_4_POSITION_PROTECTION_INVALID")
        instrument = row["instrument"]
        trade_id = row["trade_id"]
        expected = row["expected_position_quantity"]
        covered = row["covered_quantity"]
        active_stop_order_ids = row["active_stop_order_ids"]
        if (
            instrument not in INSTRUMENTS
            or instrument in instruments
            or not isinstance(trade_id, str)
            or not trade_id
            or trade_id in trade_ids
            or type(expected) is not int
            or expected == 0
            or type(covered) is not int
            or covered <= 0
            or covered != abs(expected)
            or not isinstance(active_stop_order_ids, list)
            or not active_stop_order_ids
            or any(not isinstance(item, str) or not item for item in active_stop_order_ids)
            or len(set(active_stop_order_ids)) != len(active_stop_order_ids)
            or any(item in stop_ids for item in active_stop_order_ids)
        ):
            raise ProductionSafetyError("STAGE8_12_4_POSITION_PROTECTION_INVALID")
        instruments.add(instrument)
        trade_ids.add(trade_id)
        stop_ids.update(active_stop_order_ids)
        normalized.append({
            "instrument": instrument,
            "trade_id": trade_id,
            "expected_position_quantity": expected,
            "covered_quantity": covered,
            "active_stop_order_ids": list(active_stop_order_ids),
        })
    return normalized



def write_production_heartbeat(
    runtime_root: Path | str,
    *,
    accepted_commit: str,
    account_hash: str,
    reconciliation_status: str,
    unresolved_intent_count: int,
    health_status: str,
    cycle_count: int,
    last_api_contact: datetime,
    position_protection: list[dict[str, Any]],
    failure_code: str | None = None,
    consecutive_failures: int = 0,
    now: datetime | None = None,
) -> dict[str, Any]:
    observed = now or datetime.now(timezone.utc)
    if observed.tzinfo is None or observed.utcoffset() is None:
        raise ProductionSafetyError("STAGE8_12_4_HEARTBEAT_TIMESTAMP_INVALID")
    if last_api_contact.tzinfo is None or last_api_contact.utcoffset() is None:
        raise ProductionSafetyError("STAGE8_12_4_API_CONTACT_TIMESTAMP_INVALID")
    if reconciliation_status not in {"PASS", "FAULT"}:
        raise ProductionSafetyError("STAGE8_12_4_RECONCILIATION_STATUS_INVALID")
    if health_status not in {"HEALTHY", "UNHEALTHY"}:
        raise ProductionSafetyError("STAGE8_12_4_HEALTH_STATUS_INVALID")
    if failure_code is not None and (
        not isinstance(failure_code, str)
        or not failure_code
        or len(failure_code) > 128
    ):
        raise ProductionSafetyError("STAGE8_12_4_FAILURE_CODE_INVALID")
    if type(consecutive_failures) is not int or consecutive_failures < 0:
        raise ProductionSafetyError("STAGE8_12_4_FAILURE_COUNT_INVALID")
    for scalar, code in (
        (unresolved_intent_count, "STAGE8_12_4_UNRESOLVED_COUNT_INVALID"),
        (cycle_count, "STAGE8_12_4_CYCLE_COUNT_INVALID"),
    ):
        if type(scalar) is not int or scalar < 0:
            raise ProductionSafetyError(code)
    protection = _validated_position_protection(position_protection)
    open_position_count = len(protection)
    active_protective_stop_count = sum(
        len(row["active_stop_order_ids"]) for row in protection
    )
    value = {
        "schema_id": PRODUCTION_HEARTBEAT_SCHEMA,
        "production_specification_id": PRODUCTION_SPECIFICATION_ID,
        "active_identity": ACTIVE_IDENTITY,
        "accepted_code_commit": accepted_commit,
        "account_hash": account_hash,
        "timestamp": observed.astimezone(timezone.utc).isoformat(),
        "last_successful_finam_api_contact": last_api_contact.astimezone(timezone.utc).isoformat(),
        "reconciliation_status": reconciliation_status,
        "unresolved_intent_count": unresolved_intent_count,
        "health_status": health_status,
        "cycle_count": cycle_count,
        "open_position_count": open_position_count,
        "active_protective_stop_count": active_protective_stop_count,
        "position_protection": protection,
        "failure_code": failure_code,
        "consecutive_failures": consecutive_failures,
    }
    destination = production_heartbeat_path(runtime_root)
    destination.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(
        prefix=f".{PRODUCTION_HEARTBEAT_FILENAME}.", suffix=".tmp", dir=destination.parent
    )
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as stream:
            json.dump(value, stream, sort_keys=True, separators=(",", ":"))
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, destination)
    finally:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass
    return value


def evaluate_production_entry_gate(
    *,
    runtime_root: Path | str,
    now: datetime,
    expected_commit: str,
    expected_account_hash: str,
    execution_authorized: bool,
) -> dict[str, Any]:
    reasons: list[str] = []
    result: dict[str, Any] = {
        "entry_gate_open": False,
        "decision": "BLOCKED",
        "reason_codes": reasons,
        "kill_switch_state": None,
        "execution_authorized": execution_authorized is True,
        "heartbeat_fresh": False,
        "api_contact_fresh": False,
    }
    if now.tzinfo is None or now.utcoffset() is None:
        reasons.append("PRODUCTION_HEARTBEAT_NOW_INVALID")

    try:
        switch, switch_error = load_kill_switch(runtime_root)
    except Exception:
        switch, switch_error = None, "KILL_SWITCH_INVALID"
    if switch_error:
        reasons.append(switch_error)
    else:
        result["kill_switch_state"] = switch["state"]
        if switch["state"] != "ARMED":
            reasons.append("KILL_SWITCH_NOT_ARMED")
    if execution_authorized is not True:
        reasons.append("EXECUTION_NOT_AUTHORIZED")

    try:
        value = json.loads(
            production_heartbeat_path(runtime_root).read_text(encoding="utf-8")
        )
    except (OSError, UnicodeError, json.JSONDecodeError, ProductionSafetyError):
        value = None
        reasons.append("PRODUCTION_HEARTBEAT_INVALID")

    if isinstance(value, dict):
        checks = (
            (value.get("schema_id") == PRODUCTION_HEARTBEAT_SCHEMA, "PRODUCTION_HEARTBEAT_SCHEMA_INVALID"),
            (value.get("production_specification_id") == PRODUCTION_SPECIFICATION_ID, "PRODUCTION_HEARTBEAT_PRODUCTION_ID_MISMATCH"),
            (value.get("active_identity") == ACTIVE_IDENTITY, "PRODUCTION_HEARTBEAT_IDENTITY_MISMATCH"),
            (value.get("accepted_code_commit") == expected_commit, "PRODUCTION_HEARTBEAT_COMMIT_MISMATCH"),
            (value.get("account_hash") == expected_account_hash, "PRODUCTION_HEARTBEAT_ACCOUNT_MISMATCH"),
            (value.get("reconciliation_status") == "PASS", "PRODUCTION_RECONCILIATION_NOT_PASS"),
            (value.get("health_status") == "HEALTHY", "PRODUCTION_HEARTBEAT_NOT_HEALTHY"),
            (type(value.get("unresolved_intent_count")) is int and value.get("unresolved_intent_count") == 0, "UNRESOLVED_PRODUCTION_INTENTS_PRESENT"),
            (type(value.get("cycle_count")) is int and value.get("cycle_count") >= 1, "PRODUCTION_CYCLE_COUNT_INVALID"),
            (type(value.get("open_position_count")) is int and value.get("open_position_count") >= 0, "PRODUCTION_POSITION_COUNT_INVALID"),
            (type(value.get("active_protective_stop_count")) is int and value.get("active_protective_stop_count") >= 0, "PRODUCTION_STOP_COUNT_INVALID"),
        )
        for valid, code in checks:
            if not valid:
                reasons.append(code)

        try:
            protection = _validated_position_protection(
                value.get("position_protection")
            )
        except ProductionSafetyError:
            protection = None
            reasons.append("PRODUCTION_POSITION_PROTECTION_INVALID")
        if protection is not None:
            derived_positions = len(protection)
            derived_stops = sum(
                len(row["active_stop_order_ids"]) for row in protection
            )
            if value.get("open_position_count") != derived_positions:
                reasons.append("PRODUCTION_POSITION_COUNT_MISMATCH")
            if value.get("active_protective_stop_count") != derived_stops:
                reasons.append("PRODUCTION_STOP_COUNT_MISMATCH")

        stamp = _timestamp(value.get("timestamp"))
        contact = _timestamp(value.get("last_successful_finam_api_contact"))
        if stamp is None:
            reasons.append("PRODUCTION_HEARTBEAT_TIMESTAMP_INVALID")
        elif now.tzinfo is not None:
            age = (now - stamp).total_seconds()
            if age < -MAX_CLOCK_SKEW_SECONDS:
                reasons.append("PRODUCTION_HEARTBEAT_CLOCK_SKEW")
            elif age > MAX_HEARTBEAT_AGE_SECONDS:
                reasons.append("PRODUCTION_HEARTBEAT_STALE")
            else:
                result["heartbeat_fresh"] = True
        if contact is None:
            reasons.append("PRODUCTION_API_CONTACT_TIMESTAMP_INVALID")
        elif now.tzinfo is not None:
            age = (now - contact).total_seconds()
            if age < -MAX_CLOCK_SKEW_SECONDS:
                reasons.append("PRODUCTION_API_CONTACT_CLOCK_SKEW")
            elif age > MAX_HEARTBEAT_AGE_SECONDS:
                reasons.append("PRODUCTION_API_CONTACT_STALE")
            else:
                result["api_contact_fresh"] = True

    reasons[:] = list(dict.fromkeys(reasons))
    opened = not reasons
    result["entry_gate_open"] = opened
    result["decision"] = "OPEN" if opened else "BLOCKED"
    return result
