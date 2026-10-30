"""CC-07 operator control semantics. Pure OFFLINE preflight; no executor."""
from dataclasses import dataclass
import math

ROBOTS = ("v20-shallow", "v20-obv", "v20-inside")
ACTIONS = ("start", "pause", "stop", "restart")
MEANING = {
    "start": "V20_START_ARMS",
    "pause": "V20_STOP_HALTS_NEW_ENTRIES_WORKER_CONTINUES",
    "stop": "HALT_THEN_REQUIRE_FINAM_FLAT_THEN_STOP_WORKER",
    "restart": "V20_RESTART_REQUIRES_FINAM_FLAT_AND_ARMS",
}

@dataclass(frozen=True)
class Evidence:
    task: str
    switch: str
    source_age: float | None
    task_sid_verified: bool
    operator_sid_verified: bool
    audited: bool
    confirmed: bool
    positions: int | None = None
    active_orders: int | None = None
    broker_age: float | None = None

def _fresh(x, limit):
    return (type(x) in (int, float) and math.isfinite(x)
            and -5 <= x <= limit)

def preview(robot: str, action: str, facts: Evidence) -> dict:
    if type(robot) is not str or robot not in ROBOTS:
        raise ValueError("CC07_ROBOT_INVALID")
    if type(action) is not str or action not in ACTIONS:
        raise ValueError("CC07_ACTION_INVALID")
    if type(facts) is not Evidence or facts.task not in (
        "RUNNING", "READY", "DISABLED", "UNKNOWN"
    ) or facts.switch not in ("HALTED", "ARMED", "UNKNOWN"):
        raise ValueError("CC07_FACTS_INVALID")
    if any(type(x) is not bool for x in (
        facts.task_sid_verified, facts.operator_sid_verified,
        facts.audited, facts.confirmed
    )):
        raise ValueError("CC07_FLAGS_INVALID")
    for count in (facts.positions, facts.active_orders):
        if count is not None and (type(count) is not int or count < 0):
            raise ValueError("CC07_BROKER_COUNT_INVALID")
    blockers = []
    if not facts.task_sid_verified or not facts.operator_sid_verified:
        blockers.append("IDENTITY_NOT_VERIFIED")
    if not facts.audited:
        blockers.append("DURABLE_AUDIT_REQUIRED")
    if not facts.confirmed:
        blockers.append("OPERATOR_CONFIRMATION_REQUIRED")
    if not _fresh(facts.source_age, 90):
        blockers.append("TELEMETRY_STALE")
    if facts.switch == "UNKNOWN":
        blockers.append("SWITCH_UNKNOWN")
    if action == "pause":
        if facts.task != "RUNNING":
            blockers.append("RUNNING_WORKER_REQUIRED")
    elif action == "start":
        if facts.switch != "HALTED" or facts.task not in (
            "RUNNING", "READY", "DISABLED"
        ):
            blockers.append("START_STATE_INVALID")
    elif facts.task != "RUNNING":
        blockers.append("RUNNING_WORKER_REQUIRED")
    if action != "pause":
        # CC-02 local JSONL is NOT broker protection evidence.
        if not _fresh(facts.broker_age, 30):
            blockers.append("BROKER_READONLY_STALE")
        if facts.positions is None or facts.active_orders is None:
            blockers.append("BROKER_STATE_UNKNOWN")
        elif facts.positions != 0 or facts.active_orders != 0:
            blockers.append("BROKER_NOT_FLAT")
    return {
        "robot": robot, "action": action, "meaning": MEANING[action],
        "blockers": tuple(blockers), "preflight_suitable": not blockers,
        "decision": "REFUSED_NO_LIVE_ADAPTER", "executed": False,
        "task_mutated": False, "finam_contacted": False, "arm_authorized": False,
    }
