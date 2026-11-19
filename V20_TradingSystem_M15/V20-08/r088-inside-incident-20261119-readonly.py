"""Read-only broker/SQLite preflight for 19-Nov Inside pre-POST abort incident.
No POST/DELETE, no SQLite writes, no token logging. Windows operator invokes
with account-bound DPAPI credentials already placed in process environment.
"""
from __future__ import annotations

import hashlib
import json
import os
import sqlite3
import sys
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

def need(value: bool, code: str) -> None:
    if not value:
        raise RuntimeError(code)

def main() -> int:
    need(len(sys.argv) == 3, "INSIDE_ARGUMENTS_INVALID")
    mode, database = sys.argv[1:]
    need(mode in ("pre", "post"), "INSIDE_MODE_INVALID")
    path = Path(database)
    need(path.is_file() and not path.is_symlink(), "INSIDE_SQLITE_MISSING")
    with sqlite3.connect(path.resolve().as_uri() + "?mode=ro", uri=True) as db:
        db.row_factory = sqlite3.Row
        def state(key: str):
            result = db.execute("SELECT value FROM state WHERE key=?", (key,)).fetchone()
            return json.loads(result[0]) if result else None
        identity = state("database_identity")
        need(isinstance(identity, dict) and identity.get("schema_id") == "v20.h1_state_store.real_intents.v1"
             and identity.get("robot_id") == "v20-inside", "INSIDE_SQLITE_IDENTITY_INVALID")
        account_hash = identity.get("account_sha256", "")
        need(isinstance(account_hash, str) and len(account_hash) == 64,
             "INSIDE_ACCOUNT_HASH_INVALID")
        rows = []
        for row in db.execute("SELECT idempotency_key,payload,status,broker_order_id FROM intents"):
            payload = json.loads(row["payload"])
            if payload.get("kind") == "ENTRY" and payload.get("entry_at") == "2026-11-19T13:45:00":
                rows.append((row["idempotency_key"], payload, row["status"], row["broker_order_id"]))
        usd = [row for row in rows if row[1].get("symbol") == "USDRUBF"]
        cny = [row for row in rows if row[1].get("symbol") == "CNYRUBF"]
        need(len(usd) == 1 and len(cny) == 1, "INSIDE_INCIDENT_ENTRIES_NOT_UNIQUE")
        usd_key, usd_payload, usd_status, usd_broker_id = usd[0]
        cny_key, cny_payload, cny_status, cny_broker_id = cny[0]
        need(usd_payload.get("direction") == "SHORT" and usd_payload.get("quantity") == 1
             and cny_payload.get("direction") == "SHORT" and cny_payload.get("quantity") == 20
             and cny_status == "RECONCILED" and isinstance(cny_broker_id, str)
             and cny_payload.get("finam_symbol") == "CNYRUBF@RTSX"
             and usd_payload.get("finam_symbol") == "USDRUBF@RTSX",
             "INSIDE_INCIDENT_SCOPE_MISMATCH")
        stoprow = db.execute("SELECT status,broker_order_id,payload FROM intents WHERE idempotency_key=?",
                             (cny_key + ":stop",)).fetchone()
        proof = state("protected_fill:" + cny_key)
        need(stoprow is not None and stoprow["status"] in ("ACK", "RECONCILED")
             and isinstance(proof, dict) and proof.get("broker_order_id") == cny_broker_id
             and proof.get("broker_stop_id") == stoprow["broker_order_id"]
             and proof.get("filled_quantity") == 20 and proof.get("broker_stop_percent") == "100"
             and proof.get("risk_assessment", {}).get("status") == "PASS"
             and proof.get("risk_assessment", {}).get("stop_conforms") is True
             and proof.get("account_sha256") == account_hash,
             "INSIDE_CNY_DURABLE_PROTECTION_UNVERIFIED")
        wire = json.loads(stoprow["payload"]).get("wire", {})
        need(wire.get("quantity_sl") == {"value": "100"}
             and wire.get("quantity_tp") == {"value": "100"}
             and wire.get("sl_qty_measure") == "SLTP_QTY_MEASURE_PERCENT"
             and wire.get("tp_qty_measure") == "SLTP_QTY_MEASURE_PERCENT"
             and wire.get("tp_price") == {"value": "12.053"},
             "INSIDE_CNY_TP6_WIRE_INVALID")
        need(state("execution_halt") is None, "INSIDE_DURABLE_EXECUTION_HALT_NONEMPTY")
        if mode == "pre":
            need(usd_status == "INTENT_PERSISTED" and usd_broker_id is None
                 and state("entry_submission:" + usd_key) is None
                 and state("live_post:" + usd_key) is None
                 and state("flat_cleanup:" + usd_key) is None,
                 "INSIDE_USD_MAY_HAVE_BEEN_SENT_NO_AUTO_RECOVERY")
            token = os.environ.get("V20_FINAM_TOKEN", "")
            account = os.environ.get("V20_FINAM_ACCOUNT", "")
            scope = os.environ.get("V20_FINAM_ACCOUNT_SHA256", "")
            need(token != "" and hashlib.sha256(account.encode()).hexdigest() == scope == account_hash,
                 "INSIDE_DPAPI_ACCOUNT_SCOPE_INVALID")
            from TradingSystemLab.stage8_robot.finam_api import FinamAPI
            from TradingSystemLab.stage8_robot.broker import compact_client_order_id
            from V20_TradingSystem_M15.v20_runtime.finam_execution import (
                V20FinamReadAdapter, unique_order_by_client_id,
            )
            reader = V20FinamReadAdapter(api=FinamAPI(token), robot_id="v20-inside",
                                        account_id=account, expected_account_hash=account_hash)
            reader.authenticate()
            now = datetime.now(timezone.utc)
            snapshot = reader.snapshot(now=now)
            need(not snapshot.positions.get("USDRUBF@RTSX", 0)
                 and not any(o.active and o.symbol == "USDRUBF@RTSX" for o in snapshot.orders)
                 and unique_order_by_client_id(list(snapshot.orders),
                                               compact_client_order_id(usd_key)) is None,
                 "INSIDE_USD_BROKER_ORDER_OR_POSITION_UNCERTAIN")
            active = [o for o in snapshot.orders if o.active]
            if snapshot.positions:
                need(snapshot.positions == {"CNYRUBF@RTSX": -20} and len(active) == 1,
                     "INSIDE_BROKER_POSITION_OR_ACTIVE_ORDER_CHANGED")
                stop = reader.inspect_protective_stop(
                    snapshot, entry_key=cny_key, symbol="CNYRUBF",
                    direction="SHORT", stop_price=Decimal(str(proof["installed_stop"])), now=now)
                need(stop.order_id == proof["broker_stop_id"]
                     and stop.request.get("quantity_tp") == {"value": "100"}
                     and stop.request.get("tp_qty_measure") == "SLTP_QTY_MEASURE_PERCENT"
                     and stop.request.get("tp_price") == {"value": "12.053"},
                     "INSIDE_CNY_BROKER_TP6_OR_STOP_INVALID")
                print("INSIDE_CNY_BROKER_SLTP=PASS_20_SHORT_100PCT_TP6")
            else:
                need(len(active) == 0, "INSIDE_FLAT_HAS_ACTIVE_ORDERS")
                print("INSIDE_CNY_BROKER_FLAT=PASS_NO_ACTIVE_ORDERS")
            print("INSIDE_USD_PREPOST=PASS_NEVER_SENT_BROKER_ABSENT")
            print("INSIDE_FINAM_READONLY=PASS_NO_ORDER_NO_CANCEL")
        else:
            cleanup = state("flat_cleanup:" + usd_key)
            reservations = state("risk_reservations")
            need(usd_status == "CANCELLED" and usd_broker_id is None
                 and isinstance(cleanup, dict)
                 and cleanup.get("status") == "PREPOST_ABORT_NO_FINAM_ORDER"
                 and cleanup.get("account_sha256") == account_hash
                 and isinstance(reservations, dict) and usd_key not in reservations
                 and state("entry_submission:" + usd_key) is None
                 and state("live_post:" + usd_key) is None,
                 "INSIDE_ORPHAN_NOT_DURABLY_RESOLVED")
            print("INSIDE_USD_ORPHAN=PASS_CANCELLED_PREPOST_NO_BROKER_ORDER")
        return 0

if __name__ == "__main__":
    raise SystemExit(main())
