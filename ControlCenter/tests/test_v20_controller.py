"""CC-06: offline refusal contract; cannot control Windows Tasks or FINAM."""
import ast
import json
import subprocess
import sys
from pathlib import Path
import pytest

from controller.v20_control import ACTIONS, ROBOTS, SCHEMA, main, preview

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize("robot", ROBOTS)
@pytest.mark.parametrize("action", ACTIONS)
def test_all_robot_actions_refused_without_side_effects(robot, action):
    out = preview(robot, action, "offline-01")
    assert set(out) == {
        "schema", "robot", "action", "request_id", "decision",
        "executed", "task_mutated", "finam_contacted", "live_authorized"
    }
    assert out == {
        "schema": SCHEMA, "robot": robot, "action": action,
        "request_id": "offline-01", "decision": "REFUSED_NOT_AUTHORIZED",
        "executed": False, "task_mutated": False,
        "finam_contacted": False, "live_authorized": False,
    }


@pytest.mark.parametrize("robot", ["V20_SHALLOW", "v20-other", "../v20-shallow", "", None, 1])
def test_unknown_robot_fails_closed(robot):
    with pytest.raises(ValueError, match="CC06_ROBOT_NOT_ALLOWED"):
        preview(robot, "start", "offline-01")


@pytest.mark.parametrize("action", ["check", "execute", "disable", "poweroff", "", None, 1])
def test_unknown_command_fails_closed(action):
    with pytest.raises(ValueError, match="CC06_ACTION_NOT_ALLOWED"):
        preview("v20-shallow", action, "offline-01")


@pytest.mark.parametrize("request_id", ["", "../config", "A", "a" * 49, None, 0])
def test_invalid_or_unbounded_request_id_fails_closed(request_id):
    with pytest.raises(ValueError, match="CC06_REQUEST_ID_INVALID"):
        preview("v20-shallow", "start", request_id)


def test_preview_cli_never_returns_execution_success(capsys):
    assert main(["--robot", "v20-obv", "--action", "stop", "--request-id", "offline-02"]) == 3
    result = json.loads(capsys.readouterr().out)
    assert result["action"] == "stop"
    assert result["executed"] is False
    assert result["task_mutated"] is False


def test_controller_has_no_task_broker_or_streamlit_capabilities():
    tree = ast.parse((ROOT / "controller" / "v20_control.py").read_text(encoding="utf-8"))
    allowed = {"__future__", "argparse", "json", "re"}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            assert all(name.name.split(".")[0] in allowed for name in node.names)
        if isinstance(node, ast.ImportFrom):
            assert node.module in allowed
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            assert node.func.attr not in {
                "run", "Popen", "system", "open", "write_text", "write_bytes",
                "Start", "Stop", "Restart", "connect", "request",
            }
    app = (ROOT / "v20_app.py").read_text(encoding="utf-8")
    assert "controller.v20_control" not in app
    assert "controller" not in {name.module for name in ast.walk(ast.parse(app))
                                if isinstance(name, ast.ImportFrom)}


def test_independent_cli_process_refuses_all_actions_without_ui(tmp_path):
    """Execute the real isolated CLI as a child, not a Streamlit or Task process."""
    script = ROOT / "controller" / "v20_control.py"
    before = sorted(tmp_path.iterdir())
    for robot in ROBOTS:
        for action in ACTIONS:
            child = subprocess.run(
                [sys.executable, "-I", "-B", str(script), "--robot", robot,
                 "--action", action, "--request-id", "offline-process-01"],
                cwd=tmp_path, capture_output=True, text=True, timeout=10, check=False,
            )
            assert child.returncode == 3
            assert child.stderr == ""
            result = json.loads(child.stdout)
            assert result["robot"] == robot and result["action"] == action
            assert result["executed"] is False and result["task_mutated"] is False
            assert result["finam_contacted"] is False and result["live_authorized"] is False
    assert sorted(tmp_path.iterdir()) == before


def test_independent_cli_rejects_invalid_robot_before_any_execution(tmp_path):
    script = ROOT / "controller" / "v20_control.py"
    child = subprocess.run(
        [sys.executable, "-I", "-B", str(script), "--robot", "../v20",
         "--action", "start", "--request-id", "offline-02"],
        cwd=tmp_path, capture_output=True, text=True, timeout=10, check=False,
    )
    assert child.returncode != 0
    assert child.stdout == ""
    assert list(tmp_path.iterdir()) == []
