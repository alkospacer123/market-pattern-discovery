"""CC-02 V20 LIVE snapshot: real HALTED is valid, never broker-health proof."""
import json
from datetime import datetime, timezone
from pathlib import Path

import pytest
from cc.v20_contract import parse, heartbeat_health
from deployment.v20_live_export import ROBOTS, BANNER, parse_check, collect, digest

NOW = datetime(2026, 10, 27, 12, 30, tzinfo=timezone.utc)


def official_check():
    lines = [BANNER]
    for robot in ROBOTS:
        prefix = "v20_08_5_" + robot + "_"
        fields = dict(task="Running", switch="HALTED", cycle_attempts_logged="2",
                      cycle="HALTED", last_cycle_utc="2026-10-27T12:29:58+00:00",
                      healthy="False")
        lines.extend(prefix + key + "=" + value for key, value in fields.items())
    return "\n".join(lines)


def prepare(tmp_path):
    for robot in ROBOTS:
        folder = tmp_path / "robots" / robot[4:]
        (folder / "logs").mkdir(parents=True)
        (folder / "safety").mkdir()
        (folder / "safety" / "stage8-trading-kill-switch.json").write_text(
            '{"state":"HALTED"}', encoding="utf-8")
        (folder / "logs" / "live-m15.jsonl").write_text(
            "\n".join(json.dumps({"robot":robot, "utc":when, "state":state}) for when,state in [
                ("2026-10-27T12:29:55+00:00", "NO_FROZEN_SIGNAL"),
                ("2026-10-27T12:29:58+00:00", "HALTED_NO_NEW_ENTRIES")
            ]) + "\n", encoding="utf-8")


def test_all_three_real_halted_keep_green_heartbeat(tmp_path):
    prepare(tmp_path)
    proof = parse_check(official_check())
    snapshots = collect(tmp_path, proof, NOW)
    assert len(snapshots) == 3
    for robot, data in snapshots.items():
        assert data["engine_state"] == "HALTED"
        assert data["task_state"] == "RUNNING" and data["kill_switch"] == "HALTED"
        assert data["cycle"] == 2
        assert [e["result"] for e in data["events"]] == ["PASS", "HALTED"]
        assert data["positions_local"] is None and data["stops_local"] is None
        assert data["payload_sha256"] == digest(data)
        parsed = parse(json.dumps(data).encode(), data["robot_id"], NOW, data["account_alias"])
        assert parsed["status"] == "HALTED"
        assert heartbeat_health(parsed, NOW) == "HEALTHY"


def test_new_cycle_append_during_check_is_allowed(tmp_path):
    prepare(tmp_path)
    robot = "v20-inside"
    log = tmp_path / "robots" / "inside" / "logs" / "live-m15.jsonl"
    with log.open("a", encoding="utf-8") as out:
        out.write(json.dumps({"robot":robot, "utc":"2026-10-27T12:29:59+00:00",
                              "state":"HALTED_NO_NEW_ENTRIES"}) + "\n")
    reports = collect(tmp_path, parse_check(official_check()), NOW)
    assert reports[robot]["cycle"] == 3


def test_source_switch_changed_fail_closed(tmp_path):
    prepare(tmp_path)
    p = tmp_path / "robots" / "obv" / "safety" / "stage8-trading-kill-switch.json"
    p.write_text('{"state":"ARMED"}', encoding="utf-8")
    with pytest.raises(ValueError, match="SWITCH_CHANGED"):
        collect(tmp_path, parse_check(official_check()), NOW)


def test_source_robot_changed_fail_closed(tmp_path):
    prepare(tmp_path)
    p = tmp_path / "robots" / "inside" / "logs" / "live-m15.jsonl"
    p.write_text(p.read_text().replace("v20-inside", "v20-obv"), encoding="utf-8")
    with pytest.raises(ValueError, match="IDENTITY"):
        collect(tmp_path, parse_check(official_check()), NOW)


def test_halted_not_misclassified_as_healthy():
    with pytest.raises(ValueError, match="HALTED_NOT_CONSISTENT"):
        parse_check(official_check().replace(
            "v20_08_5_v20-inside_healthy=False",
            "v20_08_5_v20-inside_healthy=True"))


def test_readonly_exports_do_not_arm_or_touch_tasks():
    source = (Path(__file__).resolve().parents[1] /
              "deployment" / "v20_live_export.py").read_text(encoding="utf-8")
    assert '["powershell.exe", "-noprofile", "-noninteractive", "-executionpolicy",' in source
    assert '"-mode", "check", "-robot", "all"' in source
    assert "Start-ScheduledTask" not in source
    assert "Stop-ScheduledTask" not in source
    assert "FinamAPI" not in source

def test_halted_worker_can_continue_protecting_position_with_pass_cycle():
    # Intentional HALTED stops only new entries, not reconciliation/SLTP care.
    check = official_check().replace(
        "v20_08_5_v20-obv_cycle=HALTED", "v20_08_5_v20-obv_cycle=PASS"
    )
    parsed = parse_check(check)
    assert parsed["v20-obv"]["switch"] == "HALTED"
    assert parsed["v20-obv"]["healthy"] is False

