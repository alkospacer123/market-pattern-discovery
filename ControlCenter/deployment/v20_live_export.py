"""CC-02 V20 LIVE readonly one-shot exporter. Run as operator, never Streamlit.

Uses the immutable V20 check-only operator and reads only public cycle/kill
observations. Never reads DPAPI, FINAM, SQLite or sends trading commands.
--publish writes exclusively into an existing CC-owned folder.
"""
from __future__ import annotations
import argparse
from collections import deque
from datetime import datetime, timezone
from hashlib import sha1, sha256
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import tempfile

ROBOTS = ("v20-shallow", "v20-obv", "v20-inside")
IDS = {name: name.replace("v20-", "V20_").upper() for name in ROBOTS}
ALIASES = {name: name.replace("v20-", "V20-").upper() for name in ROBOTS}
ROOT = Path("C:/V20Lab")
DEST = Path("C:/Control Center/data/v20-readonly")
OPERATOR = ROOT / "pretrade-08/live-08/v20-08-live-operator.ps1"
PIN = "869ecc102963e070c704714a38e525215374d4ab"
BANNER = "NO_ORDER_NO_CANCEL_NO_FINAM_API_NO_SQLITE_OPEN_NO_TASK_MUTATION_NO_REARM=YES"
CODE = re.compile(r"[A-Z][A-Z0-9_]{0,47}\Z")
PASS = {"WAIT_NEXT_M15_OPEN", "NO_FROZEN_SIGNAL", "SESSION_ENTRY_LIMIT_REACHED",
        "BROKER_RECONCILED_PROTECTION_PASS", "BROKER_FLAT_NO_ACTIVE_STOP",
        "STOP_EXECUTED_FLAT", "WEEKEND_NO_NEW_ENTRIES",
        "MOEX_CLOSED_PROTECTED_MONITOR"}
PENDING = {"ENTRY_ACK_NEEDS_FILL_AND_STOP", "ENTRY_ACK_AWAIT_BROKER_FILL",
           "STOP_ACK_NEEDS_BROKER_PROOF", "EXIT_POSTED_AWAIT_BROKER_FLAT",
           "FROZEN_EXIT_ACK_KEEP_STOP_UNTIL_FLAT", "STOP_CANCEL_WAIT_BROKER_NO_RETRANSMIT",
           "CANCEL_ACK_REQUIRE_BROKER_NO_STOP_CONFIRMATION"}


def safe(path, is_dir=False):
    try:
        info = path.lstat()
        return (stat.S_ISDIR(info.st_mode) if is_dir else stat.S_ISREG(info.st_mode)) and (
            not path.is_symlink() and not (getattr(info, "st_file_attributes", 0) & 0x400))
    except OSError:
        return False


def utc(value):
    if not isinstance(value, str) or len(value) > 48:
        raise ValueError("CC02_BAD_TIMESTAMP")
    try:
        stamp = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as error:
        raise ValueError("CC02_BAD_TIMESTAMP") from error
    if stamp.utcoffset() is None:
        raise ValueError("CC02_NAIVE_TIMESTAMP")
    return stamp.astimezone(timezone.utc)


def check_operator(path=OPERATOR):
    if not safe(path) or path.stat().st_size > 32768:
        raise ValueError("CC02_OPERATOR_UNAVAILABLE")
    raw = path.read_bytes()
    blob = sha1(b"blob " + str(len(raw)).encode("ascii") + b"\0" + raw).hexdigest()
    if blob != PIN:
        raise ValueError("CC02_OPERATOR_NOT_PINNED")
    result = subprocess.run(
        ["powershell.exe", "-noprofile", "-noninteractive", "-executionpolicy",
         "bypass", "-file", str(path), "-mode", "check", "-robot", "all"],
        capture_output=True, text=True, errors="replace", timeout=100, check=False)
    # Intentional HALTED gives HEALTH_PARTIAL and exit 1. Fields still contain real facts.
    if result.returncode not in (0, 1) or len(result.stdout) > 32768 or BANNER not in result.stdout:
        raise ValueError("CC02_READONLY_OPERATOR_FAILED")
    return result.stdout


def parse_check(output):
    if not isinstance(output, str) or len(output) > 32768 or BANNER not in output:
        raise ValueError("CC02_BAD_CHECK")
    result = {}
    for robot in ROBOTS:
        prefix = "v20_08_5_" + robot + "_"
        fields = {}
        for line in output.splitlines():
            if line.startswith(prefix) and "=" in line and len(line) < 300:
                key, value = line[len(prefix):].split("=", 1)
                if key in fields:
                    raise ValueError("CC02_DUPLICATE_FIELD")
                fields[key] = value.strip()
        keys = ("task", "switch", "cycle_attempts_logged", "cycle",
                "last_cycle_utc", "healthy")
        if any(key not in fields for key in keys):
            raise ValueError("CC02_MISSING_CHECK_FIELDS")
        task = fields["task"].upper()
        switch = fields["switch"]
        if task not in ("RUNNING", "DISABLED", "READY", "UNKNOWN") or switch not in ("HALTED", "ARMED"):
            raise ValueError("CC02_BAD_TASK_OR_SWITCH")
        if fields["healthy"] not in ("True", "False"):
            raise ValueError("CC02_BAD_HEALTH_FLAG")
        # HALTED stops new entries but still permits PASS/PENDING protection cycles.
        if switch == "HALTED" and fields["healthy"] != "False":
            raise ValueError("CC02_HALTED_NOT_CONSISTENT")
        count = fields["cycle_attempts_logged"]
        if not count.isdecimal() or len(count) > 12 or int(count) < 1:
            raise ValueError("CC02_BAD_CYCLE_COUNT")
        result[robot] = dict(task=task, switch=switch, count=int(count),
                             last=utc(fields["last_cycle_utc"]),
                             healthy=(fields["healthy"] == "True"))
    return result


def classification(state):
    if state in PASS:
        return "PASS"
    if state in PENDING:
        return "PENDING"
    if state == "HALTED_NO_NEW_ENTRIES":
        return "HALTED"
    if state.startswith(("HALT_", "FAULT_", "FINAM_")):
        return "FAULT"
    return "UNKNOWN"


def digest(payload):
    document = {key: value for key, value in payload.items() if key != "payload_sha256"}
    return sha256(json.dumps(document, sort_keys=True, separators=(",", ":"),
                             ensure_ascii=True, allow_nan=False).encode("utf-8")).hexdigest()


def events_from_log(path, robot, count_at_check, last_at_check):
    if not safe(path) or path.stat().st_size > 64 * 1024 * 1024:
        raise ValueError("CC02_BAD_LOG")
    recent = deque(maxlen=10)
    total = 0
    with path.open("r", encoding="utf-8") as file:
        for line in file:
            if line.strip():
                total += 1
                recent.append(line)
    # New cycles while taking the snapshot are valid; rollback/truncation is not.
    if total < count_at_check or not recent:
        raise ValueError("CC02_LOG_ROLLBACK")
    events = []
    last = None
    for index, line in enumerate(recent):
        try:
            obj = json.loads(line)
        except ValueError as err:
            raise ValueError("CC02_BAD_CYCLE_JSON") from err
        if type(obj) is not dict or obj.get("robot") != robot:
            raise ValueError("CC02_LOG_IDENTITY_MISMATCH")
        state = obj.get("state")
        if type(state) is not str or not CODE.fullmatch(state):
            raise ValueError("CC02_CYCLE_CODE_INVALID")
        stamp = utc(obj.get("utc"))
        if last is not None and stamp < last:
            raise ValueError("CC02_CYCLE_TIME_ORDER")
        last = stamp
        events.append(dict(at=stamp.isoformat(), cycle=total - len(recent) + 1 + index,
                           result=classification(state), code=state))
    if last < last_at_check:
        raise ValueError("CC02_LOG_TIME_ROLLBACK")
    return events


def payload(robot, proof, events, observed):
    observed = observed.astimezone(timezone.utc)
    if not events or utc(events[-1]["at"]) > observed:
        raise ValueError("CC02_INVALID_OBSERVATION")
    # No independent proof of actual FINAM positions/stops from local cycle logs.
    # HALTED is a real engine state; ARMED without independent reconcile is UNKNOWN.
    engine = ("HALTED" if proof["switch"] == "HALTED" else
              "FAULT" if events[-1]["result"] == "FAULT" else "UNKNOWN")
    result = dict(
        schema_id="cc.v20.readonly.v1", robot_id=IDS[robot],
        account_alias=ALIASES[robot], observed_at=observed.isoformat(),
        heartbeat_at=events[-1]["at"], engine_state=engine,
        task_state=proof["task"], kill_switch=proof["switch"],
        cycle=events[-1]["cycle"], positions_local=None, stops_local=None,
        unresolved_local=None,
        last_error_code=(events[-1]["code"] if events[-1]["result"] == "FAULT" else "NONE"),
        events=events)
    result["payload_sha256"] = digest(result)
    return result


def collect(root, proofs, now):
    result = {}
    for robot in ROBOTS:
        home = root / "robots" / robot[4:]
        logs, safety = home / "logs", home / "safety"
        if any(not safe(path, True) for path in (root, root / "robots", home, logs, safety)):
            raise ValueError("CC02_V20_PATH_NOT_TRUSTED")
        switch_file = safety / "stage8-trading-kill-switch.json"
        if not safe(switch_file) or switch_file.stat().st_size > 4096:
            raise ValueError("CC02_SWITCH_NOT_TRUSTED")
        switch = json.loads(switch_file.read_text(encoding="utf-8"))
        if type(switch) is not dict or switch.get("state") != proofs[robot]["switch"]:
            raise ValueError("CC02_SWITCH_CHANGED")
        events = events_from_log(logs / "live-m15.jsonl", robot,
                                 proofs[robot]["count"], proofs[robot]["last"])
        result[robot] = payload(robot, proofs[robot], events, now)
    return result


def publish(reports, root):
    if not safe(root, True):
        raise ValueError("CC02_CC_FOLDER_NOT_PROVISIONED")
    for robot, report in reports.items():
        destination = root / (robot + ".json")
        if destination.is_symlink():
            raise ValueError("CC02_CC_SYMLINK")
        data = (json.dumps(report, sort_keys=True, indent=2) + "\n").encode("utf-8")
        if len(data) > 32768:
            raise ValueError("CC02_CC_PAYLOAD_OVERSIZE")
        temporary = None
        try:
            with tempfile.NamedTemporaryFile(mode="wb", dir=root, delete=False,
                                             prefix=".cc02-", suffix=".tmp") as stream:
                temporary = Path(stream.name)
                stream.write(data)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, destination)
        finally:
            if temporary is not None and temporary.exists():
                temporary.unlink()


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--publish", action="store_true")
    args = parser.parse_args(argv)
    if os.name != "nt":
        raise SystemExit("CC02_INTEL_WINDOWS_ONLY")
    proof = parse_check(check_operator())
    reports = collect(ROOT, proof, datetime.now(timezone.utc))
    if args.publish:
        publish(reports, DEST)
    for robot, report in reports.items():
        print("cc02_" + robot + "=" + report["engine_state"] +
              " task=" + report["task_state"] + " switch=" + report["kill_switch"] +
              " cycles=" + str(report["cycle"]) + " events=" + str(len(report["events"])))
    print("cc02_export=" + ("PUBLISHED_CC_OWNED" if args.publish else "PREVIEW_NO_WRITE"))
    print("cc02_no_finam_no_task_mutation_no_arm=YES")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
