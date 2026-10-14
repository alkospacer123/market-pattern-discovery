"""Static contract for independent Windows read-only process lineage inventory."""
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "diagnostics" / "stage8-493-process-lineage-readonly.ps1"


def test_readonly_process_inventory_cannot_mutate():
    data = SCRIPT.read_text(encoding="utf-8").lower()
    for forbidden in (
        "stop-scheduledtask", "disable-scheduledtask", "enable-scheduledtask",
        "set-scheduledtask", "start-scheduledtask", "stop-process",
        "get-tradingcredential", "get-readonlycredential", "invoke-restmethod",
        "invoke-webrequest", "set-content", "add-content", "new-item",
        "remove-item", "sqlite3", "place_order", "cancel_order",
    ):
        assert forbidden not in data
    assert "get-ciminstance -classname win32_process" in data
    assert "get-scheduledtask -taskname" in data
    assert "stop_task_authorized_by_this_probe=no" in data
    assert "commandline=$" not in data


def test_process_lineage_and_fail_closed_reporting():
    data = SCRIPT.read_text(encoding="utf-8").lower()
    for signal in ("matching_python_processes=", "candidate_${i}_pid=",
                   "candidate_${i}_parent_pid=", "candidate_${i}_parent_is_matching_python=",
                   "candidate_${i}_exact_commit_in_command=",
                   "task_restart_limit_configured=",
                   "classification=readonly_process_lineage_collected_not_isolated",
                   "kill_switch_not_halted_or_identity_invalid"):
        assert signal in data
    assert "git rev-parse @)" not in data
    assert "$pid =" not in data


def test_powershell_commands_lowercase():
    import re
    data = SCRIPT.read_text(encoding="utf-8")
    assert not re.search(r"(?m)^\s*[A-Z]+-[A-Za-z]", data)
