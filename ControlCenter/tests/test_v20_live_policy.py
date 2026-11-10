"""CC-07: V20 real semantics but zero execution authority."""
from dataclasses import replace
import pytest
from controller.v20_live_policy import ROBOTS, ACTIONS, Evidence, preview

def good(**change):
    baseline = Evidence(task="RUNNING", switch="HALTED", source_age=0.0,
        task_sid_verified=True, operator_sid_verified=True,
        audited=True, confirmed=True, positions=0, active_orders=0,
        broker_age=0.0)
    return replace(baseline, **change)

@pytest.mark.parametrize("robot", ROBOTS)
@pytest.mark.parametrize("action", ACTIONS)
def test_twelve_controls_have_no_executor_even_if_all_checks_pass(robot, action):
    out = preview(robot, action, good())
    assert out["preflight_suitable"]
    assert out["decision"] == "REFUSED_NO_LIVE_ADAPTER"
    assert not out["executed"] and not out["task_mutated"]
    assert not out["finam_contacted"] and not out["arm_authorized"]

def test_pause_preserves_position_management_without_broker_snapshot():
    out = preview("v20-obv", "pause", good(positions=None, active_orders=None,
                                         broker_age=None))
    assert out["preflight_suitable"] and "WORKER_CONTINUES" in out["meaning"]

@pytest.mark.parametrize("action", ("start", "stop", "restart"))
def test_actions_which_may_stop_worker_or_arm_need_verified_flat(action):
    for change in (
        {"positions": None}, {"active_orders": None}, {"positions": 1},
        {"active_orders": 1}, {"broker_age": 40.0}
    ):
        out = preview("v20-shallow", action, good(**change))
        assert out["blockers"] and not out["preflight_suitable"]
        assert not out["executed"]

@pytest.mark.parametrize("action", ACTIONS)
def test_sid_audit_intent_staleness_and_unknown_switch_block(action):
    for change in ({"task_sid_verified": False},
                   {"operator_sid_verified": False}, {"audited": False},
                   {"confirmed": False}, {"source_age": 91.0},
                   {"switch": "UNKNOWN"}):
        assert preview("v20-inside", action, good(**change))["blockers"]

@pytest.mark.parametrize("action", ("pause", "stop", "restart"))
def test_worker_must_be_running(action):
    assert preview("v20-shallow", action, good(task="DISABLED"))["blockers"]

def test_start_and_restart_arm_by_stock_v20_operator():
    assert "ARMS" in preview("v20-shallow", "start", good())["meaning"]
    assert "ARMS" in preview("v20-shallow", "restart", good())["meaning"]
    assert preview("v20-shallow", "start", good(switch="ARMED"))["blockers"]

@pytest.mark.parametrize("robot,action", [
    ("v20-nonexistent", "start"), ("v20-obv", "arm"), ("", "pause")])
def test_only_three_robots_and_four_actions(robot, action):
    with pytest.raises(ValueError):
        preview(robot, action, good())

@pytest.mark.parametrize("bad", (True, -1, 0.1))
def test_broker_count_strict_type(bad):
    with pytest.raises(ValueError):
        preview("v20-inside", "stop", good(positions=bad))
