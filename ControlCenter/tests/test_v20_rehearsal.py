"""CC-06/07: pure OFFLINE command preflight and proposed audit receipt."""
import ast
from dataclasses import replace
from pathlib import Path

import pytest

from controller.v20_control import ROBOTS, ACTIONS
from controller.v20_rehearsal import AUDIT_SCHEMA, RehearsalFacts, rehearse

ROOT = Path(__file__).resolve().parents[1]


def facts(task_state="RUNNING"):
    return RehearsalFacts(
        role="OPERATOR", identity_verified=True,
        source_verified=True, source_fresh=True, task_state=task_state,
        open_positions=0, reconciliation_pass=True, live_release_approved=True,
    )


@pytest.mark.parametrize("robot", ROBOTS)
@pytest.mark.parametrize("action", ACTIONS)
def test_all_twelve_best_case_requests_still_refuse(robot, action):
    state = "DISABLED" if action == "start" else "RUNNING"
    receipt = rehearse(robot, action, "offline-preview-01", facts(state))
    assert receipt["schema"] == AUDIT_SCHEMA
    assert receipt["robot"] == robot and receipt["action"] == action
    assert receipt["request_id"] == "offline-preview-01"
    assert receipt["decision"] == "REFUSED_OFFLINE"
    assert receipt["blockers"][-1] == "NO_APPROVED_EXECUTION_ADAPTER"
    if action == "pause":
        assert "PAUSE_SEMANTICS_NOT_APPROVED" in receipt["blockers"]
    assert receipt["executed"] is False
    assert receipt["task_mutated"] is False
    assert receipt["finam_contacted"] is False
    assert receipt["audit_persisted"] is False
    assert receipt["live_authorized"] is False


@pytest.mark.parametrize("field,value,code", (
    ("role", "VIEWER", "OPERATOR_IDENTITY_NOT_VERIFIED"),
    ("identity_verified", False, "OPERATOR_IDENTITY_NOT_VERIFIED"),
    ("source_verified", False, "TRUSTED_FRESH_SOURCE_MISSING"),
    ("source_fresh", False, "TRUSTED_FRESH_SOURCE_MISSING"),
    ("reconciliation_pass", False, "RECONCILIATION_NOT_VERIFIED"),
    ("live_release_approved", False, "LIVE_RELEASE_NOT_APPROVED"),
    ("open_positions", None, "POSITION_STATE_UNKNOWN"),
    ("open_positions", 2, "OPEN_POSITIONS_REQUIRE_PROTECTION_POLICY"),
))
def test_fail_closed_on_every_missing_fact(field, value, code):
    receipt = rehearse("v20-shallow", "stop", "offline-02", replace(facts(), **{field: value}))
    assert code in receipt["blockers"]
    assert not receipt["executed"] and not receipt["live_authorized"]


@pytest.mark.parametrize("action,state,code", (
    ("start", "RUNNING", "START_REQUIRES_DISABLED_TASK"),
    ("start", "UNKNOWN", "START_REQUIRES_DISABLED_TASK"),
    ("stop", "DISABLED", "RUNNING_TASK_NOT_CONFIRMED"),
    ("restart", "READY", "RUNNING_TASK_NOT_CONFIRMED"),
    ("pause", "RUNNING", "PAUSE_SEMANTICS_NOT_APPROVED"),
))
def test_action_state_policy(action, state, code):
    result = rehearse("v20-inside", action, "offline-03", facts(state))
    assert code in result["blockers"]
    assert "NO_APPROVED_EXECUTION_ADAPTER" in result["blockers"]


def test_nonpersistent_replay_detection_receipt():
    receipt = rehearse("v20-obv", "stop", "offline-04", facts(),
                       frozenset({"offline-04"}))
    assert receipt["blockers"][0] == "DUPLICATE_REQUEST"
    assert receipt["audit_persisted"] is False


@pytest.mark.parametrize("robot,action,req", (
    ("bad", "start", "offline-05"),
    ("v20-shallow", "check", "offline-05"),
    ("v20-shallow", "stop", "../bad"),
    ("v20-shallow", "stop", ""),
    (None, "stop", "offline-05"),
))
def test_strict_request_schema(robot, action, req):
    with pytest.raises(ValueError):
        rehearse(robot, action, req, facts())


@pytest.mark.parametrize("field,value", (
    ("role", "ADMINISTRATOR"),
    ("task_state", "LIVE"),
    ("source_verified", 1),
    ("identity_verified", None),
    ("open_positions", True),
    ("open_positions", -1),
    ("live_release_approved", "yes"),
))
def test_untrusted_facts_rejected(field, value):
    with pytest.raises(ValueError, match="CC07_FACTS_INVALID"):
        rehearse("v20-shallow", "stop", "offline-06", replace(facts(), **{field: value}))


def test_replay_input_cannot_be_a_mutable_or_malformed_set():
    for invalid in [{"offline-07"}, frozenset({"../bad"}), None]:
        with pytest.raises(ValueError, match="CC07_REPLAY_INPUT_INVALID"):
            rehearse("v20-shallow", "stop", "offline-07", facts(), invalid)


def test_no_executor_network_broker_or_file_io_in_rehearsal():
    source = ROOT / "controller" / "v20_rehearsal.py"
    tree = ast.parse(source.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            assert not node.names
        if isinstance(node, ast.ImportFrom):
            assert node.module in ("__future__", "dataclasses", "v20_control")
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            assert node.func.attr not in {
                "open", "write_text", "write_bytes", "run", "Popen", "system",
                "Start", "Stop", "Restart", "connect", "request",
            }
    assert not any(isinstance(node, (ast.AsyncFunctionDef, ast.Await)) for node in ast.walk(tree))
