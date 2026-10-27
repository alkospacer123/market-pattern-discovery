"""CC-07 independently privileged Windows command-queue worker.

This does not run inside Streamlit. Starting the worker is a separately
authorized Intel operation after native test, ACL and SID acceptance; simply
importing or running --mode check cannot reach V20/FINAM/Windows Tasks.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone
from hashlib import sha1
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time

if __name__ == "__main__" and (__package__ or ""):
    raise RuntimeError("CC07_ENTRYPOINT_INVALID")

HOST = "URIU-PC"
OPERATOR = Path(r"C:\Control Center\cc07-operator\cc07-v20-operator.ps1")
EXPECTED_BLOB = "91a83e388978ded33525357397716d5fd509fc2a"
DATA = Path(r"C:\Control Center\data")
INBOX = DATA / "cc07-inbox"
PUBLIC = DATA / "cc07-public"
PRIVATE = DATA / "private"
POLICY = PRIVATE / "cc07-gateway-policy.json"
RELEASE = PRIVATE / "cc07-v20-release.json"
AUDIT = DATA / "control-audit" / "cc07-gateway.jsonl"
ROBOTS = ("v20-shallow", "v20-obv", "v20-inside")
ACTIONS = ("start", "pause", "stop", "restart")
HEX = re.compile(r"[a-f0-9]{32}\Z")
POLICY_FIELDS = {"schema", "approved", "operator_sid", "panel_sid", "expires_at"}
REQUEST_FIELDS = {"schema", "request_id", "robot", "action", "confirmed", "created_at"}
MAX_PENDING = 40


def parse_strict(raw, keys, maximum):
    if type(raw) is not bytes or not 0 < len(raw) <= maximum:
        raise ValueError("CC07_WIRE_SIZE")
    def pairs(items):
        d = {}
        for name, value in items:
            if name in d:
                raise ValueError("CC07_DUPLICATE_KEY")
            d[name] = value
        return d
    obj = json.loads(raw.decode("utf-8"), object_pairs_hook=pairs,
                     parse_constant=lambda _: (_ for _ in ()).throw(ValueError("CC07_NONFINITE_JSON")))
    if type(obj) is not dict or set(obj) != keys:
        raise ValueError("CC07_SCHEMA_FIELDS")
    return obj


def utc(t):
    if type(t) is not str or not 20 <= len(t) <= 42:
        raise ValueError("CC07_TIMESTAMP_INVALID")
    value = datetime.fromisoformat(t.replace("Z", "+00:00"))
    if value.tzinfo is None:
        raise ValueError("CC07_TIMESTAMP_NAIVE")
    return value.astimezone(timezone.utc)


def git_blob(path):
    b = path.read_bytes()
    if not 1000 < len(b) < 32768:
        raise ValueError("CC07_OPERATOR_SIZE")
    return sha1(b"blob " + str(len(b)).encode() + b"\0" + b).hexdigest()


def sid_for_file(path):
    """Windows ACL owner SID, never a value supplied inside the request."""
    name = str(path).replace("'", "''")
    command = ("$a=get-acl -literalpath '" + name + "' -erroraction stop;"
               "$a.getowner([security.principal.securityidentifier]).value")
    result = subprocess.run(
        ["powershell.exe", "-noprofile", "-noninteractive", "-command", command],
        capture_output=True, text=True, timeout=8, check=False,
    )
    if result.returncode != 0:
        raise ValueError("CC07_ACL_CHECK_FAILED")
    value = result.stdout.strip()
    if not re.fullmatch(r"S-[0-9]+(?:-[0-9]+)+", value):
        raise ValueError("CC07_OWNER_SID_INVALID")
    return value


def verify_acl(path, permitted_write_sids):
    """Read effective file DACL; deny untrusted write-eligible grants."""
    allowed = {"S-1-5-18", "S-1-5-32-544", *permitted_write_sids}
    for value in allowed:
        if not re.fullmatch(r"S-[0-9]+(?:-[0-9]+)+", value):
            raise ValueError("CC07_ACL_SID_INVALID")
    name = str(path).replace("'", "''")
    trusted = ",".join("'" + sid + "'" for sid in sorted(allowed))
    code = (
        "$a=get-acl -literalpath '" + name + "' -erroraction stop;"
        "$ok=@(" + trusted + ");"
        "$write=[int64][security.accesscontrol.filesystemrights]::write -bor "
        "[int64][security.accesscontrol.filesystemrights]::delete -bor "
        "[int64][security.accesscontrol.filesystemrights]::changepermissions -bor "
        "[int64][security.accesscontrol.filesystemrights]::takeownership;"
        "foreach($ace in $a.getaccessrules($true,$true,"
        "[security.principal.securityidentifier])){"
        "if($ace.accesscontroltype -eq 'Allow' -and "
        "([int64]$ace.filesystemrights -band $write) -and "
        "$ace.identityreference.value -notin $ok){throw 'untrusted_writer'}};"
        "'CC07_ACL_PASS'"
    )
    check = subprocess.run(["powershell.exe", "-noprofile",
                            "-noninteractive", "-command", code],
                           capture_output=True, text=True, timeout=12, check=False)
    if check.returncode != 0 or check.stdout.strip() != "CC07_ACL_PASS":
        raise ValueError("CC07_ACL_NOT_PROTECTED")


def validate_directory(path, owner):
    if not path.is_dir() or path.is_symlink() or sid_for_file(path) != owner:
        raise ValueError("CC07_FOLDER_OWNER_INVALID")


def policy():
    """No default grant: immutable literal policy, admin-only file/parent."""
    if os.name != "nt" or os.environ.get("COMPUTERNAME") != HOST:
        raise ValueError("CC07_WRONG_HOST")
    now = datetime.now(timezone.utc)
    if not POLICY.is_file() or POLICY.is_symlink():
        raise ValueError("CC07_POLICY_MISSING")
    row = parse_strict(POLICY.read_bytes(), POLICY_FIELDS, 1024)
    for sid in ("operator_sid", "panel_sid"):
        if type(row[sid]) is not str or not re.fullmatch(r"S-[0-9]+(?:-[0-9]+)+", row[sid]):
            raise ValueError("CC07_SID_INVALID")
    if row["schema"] != "cc.v20.gateway-policy.v1" or row["approved"] is not True:
        raise ValueError("CC07_POLICY_NOT_APPROVED")
    if not 0 < (utc(row["expires_at"]) - now).total_seconds() <= 86400:
        raise ValueError("CC07_POLICY_EXPIRED")
    admin_sids = {"S-1-5-18", "S-1-5-32-544"}
    for path in (DATA.parent, DATA, PRIVATE, POLICY, PUBLIC, AUDIT.parent):
        if path.is_symlink() or sid_for_file(path) not in admin_sids:
            raise ValueError("CC07_ADMIN_PATH_UNTRUSTED")
        verify_acl(path, set())
    if sid_for_file(INBOX) not in admin_sids or INBOX.is_symlink() or not INBOX.is_dir():
        raise ValueError("CC07_INBOX_UNTRUSTED")
    verify_acl(INBOX, {row["panel_sid"]})
    processed = INBOX / "processed"
    if processed.is_symlink() or not processed.is_dir() or sid_for_file(processed) not in admin_sids:
        raise ValueError("CC07_PROCESSED_UNTRUSTED")
    verify_acl(processed, set())
    if sid_for_file(OPERATOR) not in admin_sids or OPERATOR.is_symlink() or git_blob(OPERATOR) != EXPECTED_BLOB:
        raise ValueError("CC07_OPERATOR_UNPINNED")
    verify_acl(OPERATOR, set())
    # Effective identity is attested by the actual OS, not any panel/JSON flag.
    actor = subprocess.run(
        ["powershell.exe", "-noprofile", "-noninteractive", "-command",
         "$w=[security.principal.windowsidentity]::getcurrent();"
         "$p=[security.principal.windowsprincipal]::new($w);"
         "if(-not $p.isinrole([security.principal.windowsbuiltinrole]::administrator))"
         "{throw 'cc07_worker_elevation_required'};$w.user.value"],
        capture_output=True, text=True, timeout=8, check=False,
    )
    if actor.returncode != 0 or actor.stdout.strip() != row["operator_sid"]:
        raise ValueError("CC07_CONTROLLER_SID_MISMATCH")
    return row


def encode(row):
    data = (json.dumps(row, ensure_ascii=True, sort_keys=True, separators=(",", ":")) + "\n").encode("ascii")
    if len(data) > 1024:
        raise ValueError("CC07_OUTPUT_TOO_LARGE")
    return data


def publish(name, body):
    if not re.fullmatch(r"(gateway|receipt-[a-f0-9]{32})\.json", name):
        raise ValueError("CC07_PUBLISH_NAME_INVALID")
    target = PUBLIC / name
    temp = PUBLIC / ("." + name + "." + os.urandom(6).hex())
    with open(temp, "xb") as f:
        f.write(encode(body))
        f.flush()
        os.fsync(f.fileno())
    try:
        os.replace(temp, target)
    finally:
        if temp.exists():
            temp.unlink()


def log_event(request_id, robot, action, decision):
    record = {"utc": datetime.now(timezone.utc).isoformat(),
              "request_id": request_id, "robot": robot,
              "action": action, "decision": decision}
    with open(AUDIT, "ab") as f:
        f.write(encode(record))
        f.flush()
        os.fsync(f.fileno())


def validate_request(path, panel_sid):
    if path.is_symlink() or not path.is_file() or sid_for_file(path) != panel_sid:
        raise ValueError("CC07_REQUEST_SID_INVALID")
    if not re.fullmatch(r"[a-f0-9]{32}\.json", path.name):
        raise ValueError("CC07_REQUEST_NAME")
    row = parse_strict(path.read_bytes(), REQUEST_FIELDS, 512)
    if row["schema"] != "cc.v20.control-intent.v1" or row["confirmed"] is not True:
        raise ValueError("CC07_REQUEST_SCHEMA")
    if row["request_id"] + ".json" != path.name or row["robot"] not in ROBOTS or row["action"] not in ACTIONS:
        raise ValueError("CC07_REQUEST_SCOPE")
    age = (datetime.now(timezone.utc) - utc(row["created_at"])).total_seconds()
    if not -5 <= age <= 30:
        raise ValueError("CC07_REQUEST_STALE")
    return row


def invoke_installed(row, actor_sid):
    """The only mutating boundary; never called on worker startup/check."""
    rid, robot, action = row["request_id"], row["robot"], row["action"]
    if action != "pause":
        if RELEASE.exists():
            raise ValueError("CC07_RELEASE_ALREADY_PRESENT")
        release = {"schema": "cc.v20.release.v1", "approved": True,
                   "robot": robot, "action": action, "request_id": rid,
                   "actor_sid": actor_sid,
                   "issued_utc": datetime.now(timezone.utc).isoformat(),
                   "expires_utc": (datetime.now(timezone.utc) + timedelta(seconds=90)).isoformat()}
        with open(RELEASE, "xb") as f:
            f.write(encode(release))
            f.flush()
            os.fsync(f.fileno())
    try:
        phrase = "cc07 " + action + " " + robot + " " + rid + "\n"
        completed = subprocess.run(
            ["powershell.exe", "-noprofile", "-executionpolicy", "bypass",
             "-file", str(OPERATOR), "-mode", "execute", "-robot", robot,
             "-action", action, "-requestid", rid],
            input=phrase, capture_output=True, text=True, timeout=160,
            check=False,
        )
        evidence = completed.stdout
        if completed.returncode != 0:
            return "FAILED_UNKNOWN"
        if "cc07_result=already_halted_no_change" in evidence and action == "pause":
            return "ACCEPTED_NOT_EXECUTED"
        if "cc07_result=verified_" + action in evidence:
            return "EXECUTED"
        return "FAILED_UNKNOWN"
    finally:
        if action != "pause" and RELEASE.exists():
            RELEASE.unlink()


def already_dispatched():
    """Persistent replay latch: even an interrupted request cannot auto-repeat."""
    if not AUDIT.exists():
        return set()
    if AUDIT.is_symlink() or AUDIT.stat().st_size > 4 * 1024 * 1024:
        raise ValueError("CC07_JOURNAL_INVALID")
    result = set()
    for line in AUDIT.read_bytes().splitlines():
        row = parse_strict(line, {"utc", "request_id", "robot", "action", "decision"}, 1024)
        if row["decision"] == "DISPATCH_BEGIN":
            if type(row["request_id"]) is not str or not HEX.fullmatch(row["request_id"]):
                raise ValueError("CC07_JOURNAL_CORRUPT")
            result.add(row["request_id"])
    return result


def process_one(path, cfg, seen):

    rid = path.stem
    if not HEX.fullmatch(rid):
        return
    action, robot = "invalid", "invalid"
    outcome = "REFUSED"
    try:
        row = validate_request(path, cfg["panel_sid"])
        action, robot = row["action"], row["robot"]
        # Record acceptance before calling the independent operator. Do not
        # re-execute a request after any ambiguous crash/post-check result.
        if rid in seen:
            raise ValueError("CC07_REPLAY_REFUSED")
        log_event(rid, robot, action, "DISPATCH_BEGIN")
        seen.add(rid)  # latch after fsync and before the external action
        outcome = invoke_installed(row, cfg["operator_sid"])
    except (OSError, ValueError, subprocess.SubprocessError, TimeoutError):
        outcome = "FAILED_UNKNOWN" if action in ACTIONS else "REFUSED"
    finally:
        log_event(rid, robot, action, outcome)
        reply = {"schema": "cc.v20.control-receipt.v1", "request_id": rid,
                 "robot": robot if robot in ROBOTS else "v20-shallow",
                 "action": action if action in ACTIONS else "pause",
                 "decision": outcome,
                 "observed_at": datetime.now(timezone.utc).isoformat()}
        publish("receipt-" + rid + ".json", reply)
        # Move to admin-owned processed folder only after receipt, avoiding
        # repeated replays on normal service restart.
        processed = INBOX / "processed"
        if not processed.is_dir() or processed.is_symlink():
            raise ValueError("CC07_PROCESSED_UNAVAILABLE")
        os.replace(path, processed / path.name)


def serve():
    cfg = policy()
    if not (INBOX / "processed").is_dir():
        raise ValueError("CC07_PROCESSED_UNAVAILABLE")
    seen = already_dispatched()
    # Strictly no auto-ARM, Task start/stop or FINAM contact at startup.
    print("cc07_gateway=running_no_initial_action", flush=True)
    while True:
        now = datetime.now(timezone.utc)
        if now >= utc(cfg["expires_at"]):
            raise ValueError("CC07_POLICY_EXPIRED")
        publish("gateway.json", {"schema": "cc.v20.gateway-status.v1",
                                 "status": "ONLINE",
                                 "operator_blob": EXPECTED_BLOB,
                                 "published_at": now.isoformat(),
                                 "expires_at": (now + timedelta(seconds=15)).isoformat()})
        pending = sorted(p for p in INBOX.iterdir()
                         if p.is_file() and HEX.fullmatch(p.stem) and p.suffix == ".json")
        if len(pending) > MAX_PENDING:
            raise ValueError("CC07_INBOX_BACKPRESSURE")
        for item in pending:
            process_one(item, cfg, seen)
        time.sleep(4)


def main(argv=None):
    parser = argparse.ArgumentParser(description="CC07 isolated operator service")
    parser.add_argument("--mode", choices=("check", "serve"), default="check")
    args = parser.parse_args(argv)
    if args.mode == "check":
        print("cc07_worker=source_only_no_execution")
        print("cc07_worker_release=not_active")
        return 0
    serve()
    return 0


if __name__ == "__main__":
    sys.exit(main())
