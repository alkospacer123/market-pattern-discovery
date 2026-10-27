"""Read-only V20 M15 incident view across THREE isolated robot ledgers.
No network, FINAM tokens, DPAPI, orders, Task control, or SQLite writes.
Prints no account hash, broker IDs, client IDs, trade IDs or personal data.
Read-only broker position/stop count must be checked separately from FINAM.
"""
from __future__ import annotations
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path
import json
import os
import sqlite3

ROOT = Path(r"C:\V20Lab")
ROBOTS = {"v20-shallow": "SHALLOW_PULLBACK", "v20-obv": "OBV_PRESSURE", "v20-inside": "INSIDE_DAY_RELEASE"}

def die(code):
    raise RuntimeError("V20_MULTI_RO_" + code)

def ledger(robot, strategy):
    home = ROOT / "robots" / robot.removeprefix("v20-")
    path = home / "state" / "v20-real-intents.sqlite3"
    log = home / "logs" / "live-m15.jsonl"
    switch = home / "safety" / "stage8-trading-kill-switch.json"
    for p in (path, log, switch):
        if not p.is_file() or p.is_symlink() or p.parent.is_symlink():
            die("UNTRUSTED_OR_MISSING_PATH_" + robot)
    with closing(sqlite3.connect(path.as_uri() + "?mode=ro", uri=True, timeout=5)) as db:
        db.execute("PRAGMA query_only=ON")
        identrow = db.execute("SELECT value FROM state WHERE key='database_identity'").fetchone()
        if not identrow:
            die("IDENTITY_MISSING_" + robot)
        identity = json.loads(identrow[0])
        if (identity.get("robot_id") != robot or identity.get("strategy") != strategy
                or identity.get("schema_id") != "v20.h1_state_store.real_intents.v1"):
            die("IDENTITY_CHANGED_" + robot)
        prefix = "v20_multi_" + robot + "_"
        print(prefix + "identity=PASS")
        s = json.loads(switch.read_text(encoding="utf-8-sig"))
        print(prefix + "switch=" + str(s.get("state")))
        row = db.execute("SELECT value FROM state WHERE key='execution_halt'").fetchone()
        flag = json.loads(row[0]) if row else None
        print(prefix + "execution_halt=" + str(flag))
        rows = db.execute("SELECT idempotency_key,payload,status FROM intents ORDER BY updated_at,idempotency_key").fetchall()
        entries = [(key,json.loads(payload),status) for key,payload,status in rows
                   if json.loads(payload).get("kind") == "ENTRY"]
        print(prefix + "entry_count=" + str(len(entries)))
        for n,(key,payload,status) in enumerate(entries,1):
            tag = prefix + "entry_" + str(n) + "_"
            for field in ("symbol","direction","entry_at","quantity","atr14","initial_stop"):
                print(tag + field + "=" + str(payload.get(field)))
            print(tag + "status=" + str(status))
            stop = next((st for st in rows if st[0] == key+":stop"),None)
            print(tag + "stop_intent_status=" + (str(stop[2]) if stop else "MISSING"))
            protected = db.execute("SELECT value FROM state WHERE key=?",("protected_fill:"+key,)).fetchone()
            if protected:
                v=json.loads(protected[0])
                print(tag + "protected_fill_quantity=" + str(v.get("filled_quantity")))
                print(tag + "installed_stop=" + str(v.get("installed_stop")))
                print(tag + "sltp_percent=" + str(v.get("broker_stop_percent")))
                assessment=v.get("risk_assessment") or {}
                for field in ("status","reason","actual_risk","entry_risk_cap","account_risk_cap","stop_conforms"):
                    print(tag + "risk_" + field + "=" + str(assessment.get(field)))
            else:
                print(tag+"protected_fill=NOT_IN_SQLITE")
    with log.open("r",encoding="utf-8-sig") as f:
        from collections import deque
        tail=deque(f, maxlen=6)
    for raw in tail:
        try:
            row=json.loads(raw)
        except ValueError:
            continue
        if row.get("robot")==robot and row.get("state"):
            print(prefix+"recent_cycle="+str(row.get("utc"))+" "+str(row["state"]))

def main():
    if os.name != "nt" or os.environ.get("COMPUTERNAME","").upper() != "URIU-PC":
        die("WRONG_HOST")
    for robot,strategy in ROBOTS.items():
        ledger(robot,strategy)
    print("v20_multi_readonly=PASS_NO_FINAM_NO_ORDER_NO_SQLITE_WRITE_NO_TASK_CHANGE")

if __name__=="__main__":
    main()
