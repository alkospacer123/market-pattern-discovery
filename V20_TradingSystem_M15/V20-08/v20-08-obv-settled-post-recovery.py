"""One-time, fail-closed correction for observed V20-OBV 2026-10-27.
NO FINAM POST/DELETE, NO Task control/ARM, NO stop modification.
Uses the preexisting launcher for FINAM GET-only, and corrects exactly
one already broker-proven stale SQLite entry-post checkpoint. Not a general
manual unhalt or database reset.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone
from decimal import Decimal
import json
import os
from pathlib import Path
import sqlite3
import subprocess

ROOT = Path(r"C:\V20Lab")
INSTANCE = ROOT / "robots" / "obv"
DB = INSTANCE / "state" / "v20-real-intents.sqlite3"
LAUNCHER = ROOT / "pretrade-08" / "live-08" / "v20-08-live-launch.ps1"
LOG = INSTANCE / "logs" / "live-m15.jsonl"
SWITCH = INSTANCE / "safety" / "stage8-trading-kill-switch.json"
PIN_LAUNCHER = "5193f70e2c5663077e35653b89f4c28201ff04cb"
PIN_EXECUTION = "9ca194c61aa9db003d298fd1a3e93cc7f8bb23c4"
PIN_LIVE = "e39a00267c91ea35dbe83d27b26d6b62179b2429"
MARKER = "UNKNOWN_POST_REQUIRE_BROKER_RECONCILIATION"
EXPECTED_ENTRY = "2026-10-27T10:30:00"
EXPECTED_STOP = Decimal("80.92")
EXPECTED_QUANTITY = 2


class RecoveryBlocked(RuntimeError):
    pass


def require(ok: bool, reason: str) -> None:
    if not ok:
        raise RecoveryBlocked("V20_OBV_RECOVERY_" + reason)


def git_hash(path: Path) -> str:
    require(path.is_file() and not path.is_symlink(), "REQUIRED_SOURCE_FILE_MISSING")
    process = subprocess.run(["git.exe", "hash-object", "--", str(path)],
                             capture_output=True, text=True, timeout=15)
    require(process.returncode == 0, "SOURCE_HASH_TOOL_FAILED")
    return process.stdout.strip().lower()


def validate_local_host() -> None:
    require(os.name == "nt" and os.environ.get("COMPUTERNAME", "").upper() == "URIU-PC", "WRONG_HOST")
    require(git_hash(LAUNCHER) == PIN_LAUNCHER, "LAUNCHER_SOURCE_CHANGED")
    source = ROOT / "pretrade-08" / "live-runtime-08" / "V20_TradingSystem_M15" / "v20_runtime"
    require(git_hash(source / "finam_execution.py") == PIN_EXECUTION, "EXECUTION_SOURCE_CHANGED")
    require(git_hash(source / "finam_live.py") == PIN_LIVE, "WORKER_SOURCE_CHANGED")
    require(DB.is_file() and not DB.is_symlink() and not DB.parent.is_symlink(), "DB_PATH_CHANGED")
    require(LOG.is_file() and not LOG.is_symlink(), "LOG_PATH_CHANGED")
    require(SWITCH.is_file() and not SWITCH.is_symlink(), "SWITCH_PATH_CHANGED")
    switch = json.loads(SWITCH.read_text(encoding="utf-8-sig"))
    require(switch.get("state") == "HALTED", "MUST_REMAIN_HALTED")
    task = subprocess.run(["powershell.exe", "-noprofile", "-noninteractive",
                           "-command", "(Get-ScheduledTask -TaskName 'v20-obv' -TaskPath '\\').State"],
                          capture_output=True, text=True, timeout=20)
    require(task.returncode == 0 and task.stdout.strip() == "Running", "WORKER_NOT_RUNNING")


def broker_get_only() -> None:
    result = subprocess.run(["powershell.exe", "-noprofile", "-noninteractive",
                             "-executionpolicy", "bypass", "-file", str(LAUNCHER),
                             "-mode", "readonly", "-robot", "v20-obv"],
                            capture_output=True, text=True, timeout=90)
    require(result.returncode == 0, "FINAM_GET_FAILED")
    lines = set(line.strip() for line in result.stdout.splitlines())
    for exact in ("v20_08_4_readonly=v20-obv ACCOUNT_BOUND",
                  "v20_08_4_positions=1", "v20_08_4_active_orders=1",
                  "v20_08_4_order_posts=zero"):
        require(exact in lines, "FINAM_POSITION_OR_STOP_COUNT_CHANGED")
    print("v20_obv_recovery_finam=PASS_GET_ONLY_ONE_POSITION_ONE_ORDER_NO_POST", flush=True)


def recent_worker_protection_observation() -> None:
    # A repeated *post-fill* exception means the existing worker already
    # proved the active broker stop and PASS risk earlier in that same cycle.
    tail = LOG.read_text(encoding="utf-8-sig").splitlines()[-12:]
    rows = []
    for line in tail:
        try:
            data = json.loads(line)
            if data.get("robot") == "v20-obv":
                rows.append(data)
        except ValueError:
            pass
    require(bool(rows), "WORKER_CYCLES_MISSING")
    last = rows[-1]
    require(last.get("state") == "HALT_V20_LIVE_POST_FILL_RISK_HALTED",
            "LATEST_WORKER_CODE_CHANGED")
    moment = datetime.fromisoformat(last["utc"])
    delta = datetime.now(timezone.utc) - moment
    require(moment.tzinfo is not None and timedelta(seconds=-5) <= delta <= timedelta(seconds=45),
            "BROKER_PROTECTION_PROOF_STALE")
    print("v20_obv_recovery_worker=PASS_RECENT_BROKER_RECONCILED_POST_FILL_ONLY", flush=True)


def inspect_state(conn: sqlite3.Connection) -> None:
    row = conn.execute("SELECT value FROM state WHERE key='database_identity'").fetchone()
    require(row is not None, "IDENTITY_NOT_FOUND")
    identity = json.loads(row[0])
    require(identity.get("robot_id") == "v20-obv"
            and identity.get("strategy") == "OBV_PRESSURE"
            and identity.get("schema_id") == "v20.h1_state_store.real_intents.v1",
            "IDENTITY_MISMATCH")
    account_hash = identity.get("account_sha256")
    require(isinstance(account_hash, str) and len(account_hash) == 64, "IDENTITY_HASH_MISSING")
    row = conn.execute("SELECT value FROM state WHERE key='execution_halt'").fetchone()
    require(row is not None and json.loads(row[0]) == MARKER, "DURABLE_HALT_CHANGED")
    intents = conn.execute("SELECT idempotency_key,payload,status,broker_order_id FROM intents").fetchall()
    require(len(intents) == 2, "UNEXPECTED_INTENT_COUNT")
    mapped = {json.loads(x[1]).get("kind"): x for x in intents}
    require(set(mapped) == {"ENTRY", "STOP"}, "UNEXPECTED_INTENT_KINDS")
    entry, stop = mapped["ENTRY"], mapped["STOP"]
    payload = json.loads(entry[1])
    stop_payload = json.loads(stop[1])
    key = entry[0]
    require(payload.get("account_sha256") == account_hash and
            payload.get("robot_id") == "v20-obv" and
            payload.get("symbol") == "USDRUBF" and
            payload.get("direction") == "SHORT" and
            payload.get("entry_at") == EXPECTED_ENTRY and
            payload.get("quantity") == EXPECTED_QUANTITY,
            "ENTRY_IDENTITY_OR_SIZE_CHANGED")
    require(entry[2] == "RECONCILED" and isinstance(entry[3], str) and bool(entry[3]),
            "ENTRY_NOT_RECONCILED")
    require(stop[0] == key + ":stop" and stop[2] in ("ACK", "RECONCILED")
            and isinstance(stop[3], str) and bool(stop[3]) and
            stop_payload.get("entry_key") == key and
            stop_payload.get("account_sha256") == account_hash,
            "STOP_NOT_BROKER_ACKNOWLEDGED")
    proof_row = conn.execute("SELECT value FROM state WHERE key=?", ("protected_fill:" + key,)).fetchone()
    require(proof_row is not None, "PROTECTED_FILL_MISSING")
    proof = json.loads(proof_row[0])
    assessment = proof.get("risk_assessment", {})
    require(proof.get("account_sha256") == account_hash
            and proof.get("broker_order_id") == entry[3]
            and proof.get("broker_stop_id") == stop[3]
            and proof.get("filled_quantity") == EXPECTED_QUANTITY
            and proof.get("broker_stop_percent") == "100"
            and Decimal(str(proof.get("installed_stop"))) == EXPECTED_STOP,
            "BROKER_STOP_PROOF_MISMATCH")
    require(assessment.get("status") == "PASS"
            and assessment.get("reason") is None
            and assessment.get("stop_conforms") is True
            and assessment.get("filled_quantity") == EXPECTED_QUANTITY
            and Decimal(str(assessment.get("projected_stop"))) == EXPECTED_STOP
            and Decimal(str(assessment.get("actual_risk"))) <= Decimal(str(assessment.get("entry_risk_cap")))
            and Decimal(str(assessment.get("actual_risk"))) <= Decimal(str(assessment.get("account_risk_cap"))),
            "RISK_STOP_OR_QUANTITY_INVALID")
    submitted = conn.execute("SELECT value FROM state WHERE key=?", ("entry_submission:" + key,)).fetchone()
    require(submitted is not None and json.loads(submitted[0]).get("account_sha256") == account_hash,
            "SUBMISSION_CHECKPOINT_MISSING")
    print("v20_obv_recovery_sqlite=PASS_RECONCILED_ENTRY_2_SHORT_AND_ACTIVE_100_PERCENT_SLTP_PROOF_RISK_PASS", flush=True)


def recover_sqlite(db: Path, execute: bool) -> None:
    uri = db.as_uri() + ("?mode=rw" if execute else "?mode=ro")
    with sqlite3.connect(uri, uri=True, timeout=12) as conn:
        conn.execute("PRAGMA busy_timeout=12000")
        if execute:
            conn.execute("BEGIN IMMEDIATE")
        else:
            conn.execute("PRAGMA query_only=ON")
        inspect_state(conn)
        if not execute:
            return
        # ONE existing key is changed to JSON null. Does not touch
        # entries, stop intents, fills, reservations, kill switch or Tasks.
        cursor = conn.execute("UPDATE state SET value='null' WHERE key='execution_halt' AND value=?",
                              (json.dumps(MARKER),))
        require(cursor.rowcount == 1, "ATOMIC_MARKER_CONFLICT")
        conn.commit()
        print("v20_obv_recovery_durable_stale_checkpoint=RESOLVED_ONLY_ONE_KEY", flush=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("verify", "recover"), default="verify")
    args = parser.parse_args()
    validate_local_host()
    broker_get_only()
    recent_worker_protection_observation()
    recover_sqlite(DB, args.mode == "recover")
    if args.mode == "recover":
        require(json.loads(SWITCH.read_text(encoding="utf-8-sig")).get("state") == "HALTED",
                "KILL_SWITCH_UNEXPECTEDLY_ARMED")
        print("v20_obv_recovery=PASS_WORKER_RUNNING_KILL_SWITCH_HALTED_STOP_UNTOUCHED_NO_POST_NO_ARM", flush=True)
    else:
        print("v20_obv_recovery_verify=PASS_GET_ONLY_NO_STATE_CHANGES", flush=True)


if __name__ == "__main__":
    main()
