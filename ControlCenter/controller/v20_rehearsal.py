"""CC-06/07 OFFLINE authorization/state-machine rehearsal.

Only validates hypothetical facts and returns a proposed audit receipt.
No Windows Task, FINAM, tokens, filesystem, network, or execution adapter.
A passing preflight NEVER authorizes a real command.
"""
from __future__ import annotations

from dataclasses import dataclass

from .v20_control import ACTIONS, REQUEST_ID, ROBOTS

ROLES = ("VIEWER", "OPERATOR")
TASK_STATES = ("DISABLED", "READY", "RUNNING", "UNKNOWN")
AUDIT_SCHEMA = "cc.v20.control-audit-preview.v1"


@dataclass(frozen=True)
class RehearsalFacts:
    """Untrusted *simulated* inputs. Do not promote them to operating authority."""

    role: str
    identity_verified: bool
    source_verified: bool
    source_fresh: bool
    task_state: str
    open_positions: int | None
    reconciliation_pass: bool
    live_release_approved: bool


def _validate(robot: str, action: str, request_id: str, facts: RehearsalFacts) -> None:
    if type(robot) is not str or robot not in ROBOTS:
        raise ValueError("CC07_ROBOT_NOT_ALLOWED")
    if type(action) is not str or action not in ACTIONS:
        raise ValueError("CC07_ACTION_NOT_ALLOWED")
    if type(request_id) is not str or REQUEST_ID.fullmatch(request_id) is None:
        raise ValueError("CC07_REQUEST_ID_INVALID")
    if type(facts) is not RehearsalFacts or facts.role not in ROLES or facts.task_state not in TASK_STATES:
        raise ValueError("CC07_FACTS_INVALID")
    if any(type(getattr(facts, field)) is not bool for field in (
        "identity_verified", "source_verified", "source_fresh",
        "reconciliation_pass", "live_release_approved"
    )):
        raise ValueError("CC07_FACTS_INVALID")
    if facts.open_positions is not None and (
        type(facts.open_positions) is not int or not 0 <= facts.open_positions <= 10**12
    ):
        raise ValueError("CC07_FACTS_INVALID")


def rehearse(robot: str, action: str, request_id: str, facts: RehearsalFacts,
             seen_request_ids: frozenset[str] = frozenset()) -> dict:
    """Build a deterministic, non-persistent audit *preview*; NEVER dispatch.

    All supplied facts are hypothetical, including identity/authorization.
    In production a separately approved broker-independent controller must
    collect and attest these facts and persist audit records atomically.
    """
    _validate(robot, action, request_id, facts)
    if type(seen_request_ids) is not frozenset or any(
        type(x) is not str or REQUEST_ID.fullmatch(x) is None for x in seen_request_ids
    ):
        raise ValueError("CC07_REPLAY_INPUT_INVALID")
    blockers = []
    if request_id in seen_request_ids:
        blockers.append("DUPLICATE_REQUEST")
    if facts.role != "OPERATOR" or not facts.identity_verified:
        blockers.append("OPERATOR_IDENTITY_NOT_VERIFIED")
    if not facts.source_verified or not facts.source_fresh:
        blockers.append("TRUSTED_FRESH_SOURCE_MISSING")
    if not facts.reconciliation_pass:
        blockers.append("RECONCILIATION_NOT_VERIFIED")
    if not facts.live_release_approved:
        blockers.append("LIVE_RELEASE_NOT_APPROVED")
    if facts.open_positions is None:
        blockers.append("POSITION_STATE_UNKNOWN")
    elif facts.open_positions != 0:
        # STOP/RESTART must not strand a position; PAUSE semantics also unknown.
        blockers.append("OPEN_POSITIONS_REQUIRE_PROTECTION_POLICY")

    if action == "start" and facts.task_state != "DISABLED":
        blockers.append("START_REQUIRES_DISABLED_TASK")
    elif action in ("stop", "restart") and facts.task_state != "RUNNING":
        blockers.append("RUNNING_TASK_NOT_CONFIRMED")
    elif action == "pause":
        blockers.append("PAUSE_SEMANTICS_NOT_APPROVED")

    # No combination of simulated inputs may produce an executable decision.
    blockers.append("NO_APPROVED_EXECUTION_ADAPTER")
    return {
        "schema": AUDIT_SCHEMA,
        "robot": robot, "action": action, "request_id": request_id,
        "decision": "REFUSED_OFFLINE",
        "blockers": blockers,
        "executed": False, "task_mutated": False, "finam_contacted": False,
        "audit_persisted": False, "live_authorized": False,
    }
