"""Focused tests for durable CC-06/07 OFFLINE journal, no executor."""
import ast
from dataclasses import replace
from pathlib import Path
import sqlite3

import pytest

from controller.v20_control import ACTIONS, ROBOTS
from controller.v20_offline_journal import DB_NAME, OfflineJournal
from controller.v20_rehearsal import RehearsalFacts


def facts(state="RUNNING"):
    return RehearsalFacts(
        role="OPERATOR", identity_verified=True,
        source_verified=True, source_fresh=True,
        task_state=state, open_positions=0,
        reconciliation_pass=True, live_release_approved=True,
    )


@pytest.fixture
def journal(tmp_path):
    return OfflineJournal(tmp_path, frozenset({"operator-one"}))


@pytest.mark.parametrize("robot", ROBOTS)
@pytest.mark.parametrize("action", ACTIONS)
def test_all_12_combinations_always_refuse_and_audit(journal, robot, action):
    state = "DISABLED" if action == "start" else "RUNNING"
    receipt = journal.submit(robot, action, f"{robot}-{action}",
                             "operator-one", facts(state), facts(state))
    assert receipt["decision"] == "REFUSED_OFFLINE"
    assert receipt["audit_persisted"] is True
    assert receipt["executed"] is False
    assert receipt["task_mutated"] is False
    assert receipt["finam_contacted"] is False
    assert receipt["live_authorized"] is False
    assert "LIVE_RELEASE_NOT_APPROVED" in receipt["blockers"]
    assert "NO_APPROVED_EXECUTION_ADAPTER" in receipt["blockers"]
    assert receipt["post_check"] == "SIMULATED_UNCHANGED"


def test_duplicate_refused_after_new_instance(tmp_path):
    first = OfflineJournal(tmp_path, frozenset({"operator-one"}))
    a = first.submit("v20-obv", "start", "repeat-01",
                     "operator-one", facts("DISABLED"))
    second = OfflineJournal(tmp_path, frozenset({"operator-one"}))
    b = second.submit("v20-inside", "stop", "repeat-01",
                      "operator-one", facts())
    assert a["decision"] == "REFUSED_OFFLINE"
    assert b["decision"] == "REFUSED_DUPLICATE"
    assert b["blockers"][0] == "DUPLICATE_REQUEST"
    assert [r["decision"] for r in second.recent()] == [
        "REFUSED_DUPLICATE", "REFUSED_OFFLINE"
    ]


def test_operator_and_source_gates(journal):
    unauthorized = journal.submit("v20-shallow", "stop", "no-operator-01",
                                  "outsider", facts())
    assert "OPERATOR_IDENTITY_NOT_VERIFIED" in unauthorized["blockers"]
    unavailable = journal.submit(
        "v20-inside", "restart", "source-missing-01", "operator-one",
        replace(facts(), source_verified=False, source_fresh=False)
    )
    assert "TRUSTED_FRESH_SOURCE_MISSING" in unavailable["blockers"]


def test_hypothetical_postcheck_mismatch(journal):
    receipt = journal.submit(
        "v20-shallow", "restart", "post-mismatch-01",
        "operator-one", facts(), facts("DISABLED")
    )
    assert receipt["post_check"] == "SIMULATED_UNEXPECTED_CHANGE"
    assert "POST_STATE_MISMATCH" in receipt["blockers"]
    assert journal.recent(1)[0]["post_check"] == receipt["post_check"]


def test_competing_writer_fails_closed_and_does_not_log_false_success(journal):
    lock = sqlite3.connect(str(journal.path), isolation_level=None, timeout=0)
    try:
        lock.execute("BEGIN IMMEDIATE")
        receipt = journal.submit("v20-obv", "stop", "concurrent-01",
                                 "operator-one", facts())
        assert receipt["decision"] == "REFUSED_AUDIT_UNAVAILABLE"
        assert receipt["audit_persisted"] is False
        assert receipt["executed"] is False
    finally:
        lock.rollback()
        lock.close()
    assert journal.recent() == []


def test_invalid_requests_rejected_and_symlink_forbidden(tmp_path, journal):
    with pytest.raises(ValueError):
        journal.submit("../bad", "start", "bad-01", "operator-one", facts())
    with pytest.raises(ValueError):
        journal.submit("v20-obv", "start", "bad-02", "../bad", facts())
    with pytest.raises(ValueError):
        journal.recent(1000)
    other = tmp_path / "other"
    other.mkdir()
    try:
        (other / DB_NAME).symlink_to(journal.path)
    except (OSError, NotImplementedError):
        pytest.skip("Symlinks not supported here")
    with pytest.raises(ValueError, match="SYMLINK"):
        OfflineJournal(other)


def test_module_has_no_runtime_execution_imports():
    path = Path(__file__).resolve().parents[1] / "controller" / "v20_offline_journal.py"
    tree = ast.parse(path.read_text(encoding="utf-8"))
    allowed = {"__future__", "dataclasses", "datetime", "json", "pathlib",
               "sqlite3", "v20_control", "v20_rehearsal"}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            assert all(item.name in allowed for item in node.names)
        if isinstance(node, ast.ImportFrom):
            assert node.module in allowed
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            assert node.func.attr not in {
                "run", "Popen", "system", "Start", "Stop", "Restart",
                "create_order", "start_task"
            }
