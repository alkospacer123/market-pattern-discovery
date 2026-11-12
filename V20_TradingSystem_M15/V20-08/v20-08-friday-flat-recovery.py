"""One-time V20 flat GLD SQLite repair; NO FINAM/POST/DELETE/Task/ARM.
Installer must prove all 3 accounts broker-flat, HALT new entries, back up
all 3 SQLite stores, then stop workers BEFORE calling --mode recover.
"""
from __future__ import annotations
import argparse
from contextlib import closing
import json
import os
from pathlib import Path
import re
import sqlite3

ROOT = Path(r"c:\v20lab")
MARKER = "UNKNOWN_POST_REQUIRE_BROKER_RECONCILIATION"
CASES = {
    "v20-shallow": ("SHALLOW_PULLBACK", "2026-10-30T12:45:00"),
    "v20-obv": ("OBV_PRESSURE", "2026-10-30T17:15:00"),
}

def need(ok, code):
    if not ok:
        raise RuntimeError(code)

def state(conn, key):
    r = conn.execute("SELECT value FROM state WHERE key=?", (key,)).fetchone()
    return json.loads(r[0]) if r else None

def verify(conn, robot):
    strategy, at = CASES[robot]
    ident = state(conn, "database_identity")
    need(isinstance(ident, dict) and ident.get("schema_id") == "v20.h1_state_store.real_intents.v1"
         and ident.get("robot_id") == robot and ident.get("strategy") == strategy,
         "IDENTITY_INVALID")
    scope = ident.get("account_sha256")
    need(isinstance(scope, str) and re.fullmatch("[0-9a-f]{64}", scope), "ACCOUNT_SCOPE_INVALID")
    need(state(conn, "execution_halt") == MARKER, "DURABLE_HALT_NOT_EXPECTED")
    rows = conn.execute("SELECT idempotency_key,payload,status,broker_order_id FROM intents").fetchall()
    need(len(rows) >= 2, "INTENTS_MISSING")
    intents, friday = {}, []
    for key, raw, status, broker_id in rows:
        need(isinstance(key, str) and key and key not in intents, "DUPLICATE_INTENT")
        payload = json.loads(raw)
        need(isinstance(payload, dict) and payload.get("kind") in
             {"ENTRY", "STOP", "FROZEN_EXIT", "STOP_CANCEL"}, "INTENT_SCHEMA_INVALID")
        need(status not in {"UNCERTAIN", "SUBMITTED", "INTENT_PERSISTED"},
             "UNKNOWN_OR_UNSETTLED_INTENT")
        intents[key] = payload, status, broker_id
        if payload["kind"] == "ENTRY" and payload.get("entry_at") == at and payload.get("symbol") == "GLDRUBF":
            friday.append((key, payload, status, broker_id))
    need(len(friday) == 1, "FRIDAY_GLD_ENTRY_NOT_UNIQUE")
    key, entry, status, broker_id = friday[0]
    need(entry.get("robot_id") == robot and entry.get("account_sha256") == scope
         and entry.get("mode") == "PRETRADE_NOT_AUTHORIZED"
         and entry.get("direction") in {"LONG", "SHORT"}
         and type(entry.get("quantity")) is int and entry["quantity"] > 0
         and status == "RECONCILED" and isinstance(broker_id, str) and bool(broker_id),
         "FRIDAY_ENTRY_NOT_RECONCILED")
    stop = intents.get(key + ":stop")
    need(stop is not None and stop[0].get("kind") == "STOP"
         and stop[0].get("entry_key") == key
         and stop[0].get("account_sha256") == scope
         and stop[1] in {"ACK", "RECONCILED"}
         and isinstance(stop[2], str) and bool(stop[2]),
         "FRIDAY_STOP_NOT_ACKNOWLEDGED")
    proof = state(conn, "protected_fill:" + key)
    need(isinstance(proof, dict) and proof.get("account_sha256") == scope
         and proof.get("broker_order_id") == broker_id
         and proof.get("broker_stop_id") == stop[2]
         and type(proof.get("filled_quantity")) is int
         and proof["filled_quantity"] == entry["quantity"]
         and proof.get("broker_stop_percent") == "100"
         and (proof.get("risk_assessment") or {}).get("status") == "PASS"
         and (proof.get("risk_assessment") or {}).get("stop_conforms") is True,
         "FRIDAY_PROTECTIVE_PROOF_INVALID")
    entry_count = 0
    for old_key, (payload, old_status, _) in intents.items():
        if payload["kind"] != "ENTRY":
            continue
        entry_count += 1
        need(old_status == "RECONCILED", "OLDER_ENTRY_NOT_RECONCILED")
        cleanup = state(conn, "flat_cleanup:" + old_key)
        need(isinstance(cleanup, dict)
             and cleanup.get("account_sha256") == scope
             and cleanup.get("status") in {"BROKER_FLAT_NO_ACTIVE_STOP", "STOP_EXECUTED_FINAM_FLAT"},
             "ENTRY_WITHOUT_BROKER_FLAT_PROOF")
    need(entry_count >= 1 and state(conn, "risk_reservations") in ({}, None),
         "UNRELEASED_RISK_RESERVATION")
    print(f"v20_reconcile_{robot}=PASS_FLAT_{entry_count}_ENTRIES_NO_UNCERTAIN", flush=True)

def run(root, robot, mode):
    path = root / "robots" / robot.removeprefix("v20-") / "state" / "v20-real-intents.sqlite3"
    need(path.is_file() and not path.is_symlink(), "DB_MISSING_OR_LINKED")
    uri = path.as_uri() + ("?mode=rw" if mode == "recover" else "?mode=ro")
    with closing(sqlite3.connect(uri, uri=True, timeout=12)) as db:
        if mode == "recover":
            db.execute("BEGIN IMMEDIATE")
        else:
            db.execute("PRAGMA query_only=ON")
        try:
            verify(db, robot)
            if mode == "recover":
                changed = db.execute(
                    "UPDATE state SET value='null' WHERE key='execution_halt' AND value=?",
                    (json.dumps(MARKER),)
                )
                need(changed.rowcount == 1, "MARKER_CHANGED_DURING_RECOVERY")
                db.commit()
                print(f"v20_reconcile_{robot}=CLEARED_ONE_DURABLE_MARKER", flush=True)
        except BaseException:
            if mode == "recover":
                db.rollback()
            raise

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--robot", choices=CASES, required=True)
    p.add_argument("--mode", choices=("verify", "recover"), default="verify")
    args = p.parse_args()
    need(os.name == "nt" and os.environ.get("COMPUTERNAME", "").upper() == "URIU-PC",
         "WRONG_PRODUCTION_HOST")
    run(ROOT, args.robot, args.mode)

if __name__ == "__main__":
    main()
