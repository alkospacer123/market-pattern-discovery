"""Roadmap 3.6: one-shot post-ARM observer for a separately authorized Intel host.

Only imports read-side production parsers. Broker network allowlist: session POST,
GET exact account, orders, and N4 schedules/bars. Never imports live_execution,
never calls order APIs, never writes live SQLite or changes Task or kill switch.
No JSON evidence or secrets are persisted by this module.
"""
from __future__ import annotations

import argparse
from decimal import Decimal, InvalidOperation
from datetime import datetime, timedelta, timezone
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys

SPEC = "PROD_STAGE7_46DB784378797C7FB04636892350AFF21006D71A31F2CED9D4B974EDA2DC36B8"
IDENTITY = "TRAIL1__N4_01__FULL__R15"
COMMIT = "3a18c8c24301c866a60f5d725de227288d48f7ec"
SYMBOLS = {
    "USDRUBF": "USDRUBF@RTSX", "CNYRUBF": "CNYRUBF@RTSX",
    "GLDRUBF": "GLDRUBF@RTSX", "IMOEXF": "IMOEXF@RTSX",
}
TERMINAL = ("CANCELLED", "REJECTED", "CLOSED", "RECONCILED")
AGE_SECONDS = 900
CLOCK_TOLERANCE = 60

class Blocked(Exception):
    pass

def require(test, code):
    if not test:
        raise Blocked(code)

def utc(value, code="TIMESTAMP_INVALID"):
    try:
        result = datetime.fromisoformat(value.replace("Z", "+00:00"))
        require(result.tzinfo is not None and result.utcoffset() is not None, code)
        return result.astimezone(timezone.utc)
    except (ValueError, AttributeError, TypeError):
        raise Blocked(code) from None

def read_json(path):
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError, UnicodeError):
        raise Blocked("LOCAL_JSON_MISSING_OR_INVALID") from None
    require(type(value) is dict, "LOCAL_JSON_NOT_OBJECT")
    return value

def local_state(root, account_hash):
    now = datetime.now(timezone.utc)
    sw = read_json(root / "safety" / "stage8-trading-kill-switch.json")
    hb = read_json(root / "diagnostics" / "stage8-12-4-production-heartbeat.json")
    require(sw.get("schema_id") == "stage8_trading_kill_switch.v1" and
            sw.get("production_specification_id") == SPEC, "SWITCH_SCHEMA_OR_SPEC_INVALID")
    require(sw.get("state") == "ARMED" and type(sw.get("generation")) is int and
            sw["generation"] == 62, "ARMED_GENERATION_NOT_62")
    require(hb.get("schema_id") == "stage8_12_4_production_heartbeat.v1" and
            hb.get("production_specification_id") == SPEC and hb.get("active_identity") == IDENTITY and
            hb.get("accepted_code_commit") == COMMIT and hb.get("account_hash") == account_hash,
            "HEARTBEAT_AUTHORITY_MISMATCH")
    require(hb.get("health_status") == "HEALTHY" and hb.get("reconciliation_status") == "PASS",
            "HEARTBEAT_HEALTH_OR_RECONCILIATION_FAILED")
    require(type(hb.get("cycle_count")) is int and hb["cycle_count"] >= 11609,
            "CYCLE_COUNT_INVALID")
    require(type(hb.get("unresolved_intent_count")) is int and hb["unresolved_intent_count"] == 0,
            "HEARTBEAT_UNRESOLVED_INTENTS")
    for k in ("timestamp", "last_successful_finam_api_contact"):
        seconds = (now - utc(hb.get(k))).total_seconds()
        require(-CLOCK_TOLERANCE <= seconds <= AGE_SECONDS, "HEARTBEAT_OR_API_CONTACT_STALE")
    require(utc(hb["timestamp"]) > utc(sw["updated_utc"]), "NO_POST_ARM_HEALTHY_CYCLE")
    require(type(hb.get("position_protection")) is list and
            type(hb.get("open_position_count")) is int and
            type(hb.get("active_protective_stop_count")) is int,
            "HEARTBEAT_POSITION_PROTECTION_INVALID")
    return sw, hb

def ledger(root, account_hash):
    path = root / "state" / "stage8-12-production.sqlite3"
    require(path.is_file(), "PRODUCTION_LEDGER_NOT_FOUND")
    # mode=ro reads current WAL through a coherent SQLite transaction.  immutable=1
    # would silently miss uncheckpointed WAL, so it MUST NOT be used here.
    try:
        db = sqlite3.connect(path.resolve().as_uri() + "?mode=ro", uri=True, timeout=3)
        try:
            db.execute("PRAGMA query_only=ON")
            db.execute("BEGIN")
            def get(key):
                row = db.execute("SELECT value FROM state WHERE key=?", (key,)).fetchone()
                return json.loads(row[0]) if row else None
            identity = get("production_service_identity")
            require(isinstance(identity, dict) and identity.get("production_specification_id") == SPEC
                    and identity.get("active_identity") == IDENTITY and identity.get("account_hash") == account_hash,
                    "LEDGER_SERVICE_IDENTITY_MISMATCH")
            state_identity = get("database_identity")
            require(isinstance(state_identity, dict) and
                    state_identity.get("production_specification_id") == SPEC and
                    state_identity.get("active_identity") == IDENTITY,
                    "LEDGER_DATABASE_IDENTITY_MISMATCH")
            positions = get("production_positions") or {}
            require(type(positions) is dict and set(positions) <= set(SYMBOLS),
                    "LEDGER_POSITIONS_INVALID")
            keys = ",".join("?" for _ in TERMINAL)
            count = db.execute(
                f"SELECT COUNT(*) FROM intents WHERE COALESCE(status,'') NOT IN ({keys})", TERMINAL
            ).fetchone()[0]
            require(type(count) is int and count == 0, "LEDGER_UNRESOLVED_INTENTS")
            h1 = {sym:get("production_expected_h1:" + sym) for sym in SYMBOLS}
            require(all(type(v) is str for v in h1.values()), "LEDGER_N4_H1_WATERMARK_MISSING")
            cycle = get("production_service_cycle_count")
            require(type(cycle) is int, "LEDGER_CYCLE_INVALID")
            state = {"cycle": cycle, "positions": positions, "h1": h1,
                     "unresolved": count}
            db.rollback()
            return state
        finally:
            db.close()
    except Blocked:
        raise
    except (OSError, sqlite3.Error, TypeError, ValueError):
        raise Blocked("LEDGER_READONLY_SNAPSHOT_FAILED") from None

def protection(hb, local_positions, broker_positions, orders):
    QTY_MEASURE, QTY_PERCENT = "SLTP_QTY_MEASURE_PERCENT", "100"
    require(set(broker_positions) <= set(SYMBOLS.values()), "BROKER_UNEXPECTED_INSTRUMENT")
    mapped = {}
    for instrument, raw in local_positions.items():
        require(type(raw) is dict and raw.get("finam_symbol") == SYMBOLS[instrument] and
                raw.get("direction") in {"LONG", "SHORT"} and
                type(raw.get("quantity")) is int and raw["quantity"] > 0,
                "LEDGER_POSITION_SCHEMA_INVALID")
        expected = raw["quantity"] if raw["direction"] == "LONG" else -raw["quantity"]
        mapped[SYMBOLS[instrument]] = expected
    require(broker_positions == mapped, "BROKER_LEDGER_POSITION_MISMATCH")
    rows = hb["position_protection"]
    require(len(rows) == len(mapped) == hb["open_position_count"],
            "HEARTBEAT_POSITION_COUNT_MISMATCH")
    active = [o for o in orders if o.active]
    require(all(o.kind == "SLTP" for o in active), "ACTIVE_REGULAR_OR_UNKNOWN_ORDER")
    stop_ids = set()
    seen = set()
    for row in rows:
        require(type(row) is dict and set(row) == {
            "instrument", "trade_id", "expected_position_quantity", "covered_quantity", "active_stop_order_ids"},
            "HEARTBEAT_STOP_RECORD_INVALID")
        sym = row["instrument"]
        require(sym in local_positions and sym not in seen,
                "HEARTBEAT_STOP_INSTRUMENT_INVALID")
        seen.add(sym)
        local = local_positions[sym]
        require(row["trade_id"] == local.get("trade_id") and
                row["expected_position_quantity"] == mapped[SYMBOLS[sym]] and
                type(row["covered_quantity"]) is int and
                row["covered_quantity"] == abs(mapped[SYMBOLS[sym]]) and
                type(row["active_stop_order_ids"]) is list and
                len(row["active_stop_order_ids"]) >= 1,
                "HEARTBEAT_STOP_COVERAGE_MISMATCH")
        require(local.get("protective_stop_state") == "ACTIVE" and
                local.get("protective_covered_quantity") == abs(mapped[SYMBOLS[sym]]) and
                local.get("protective_stop_broker_order_id") in row["active_stop_order_ids"],
                "LEDGER_PROTECTION_MISMATCH")
        stop_ids.update(row["active_stop_order_ids"])
    require(len(stop_ids) == len(active) == hb["active_protective_stop_count"],
            "ACTIVE_STOP_COUNT_MISMATCH")
    for stop in active:
        require(stop.order_id in stop_ids and stop.symbol in mapped and
                stop.kind == "SLTP" and
                type(stop.comment) is str and stop.comment.startswith("stage8.12:"),
                "ACTIVE_STOP_NOT_OWNED")
        req = stop.request
        try:
            percent_value = req.get("quantity_sl")
            price_value = req.get("sl_price")
            percent = Decimal(percent_value["value"]) if (type(percent_value) is dict and
                         set(percent_value) == {"value"} and type(percent_value["value"]) is str) else None
            price = Decimal(price_value["value"]) if (type(price_value) is dict and
                    set(price_value) == {"value"} and type(price_value["value"]) is str) else None
        except (InvalidOperation, KeyError, ValueError):
            raise Blocked("ACTIVE_STOP_PRICE_OR_PERCENT_INVALID") from None
        require(req.get("sl_qty_measure") == QTY_MEASURE and
                req.get("valid_before") == "VALID_BEFORE_GOOD_TILL_CANCEL" and
                percent == Decimal(QTY_PERCENT) and price is not None and
                price.is_finite() and price > 0,
                "ACTIVE_STOP_NOT_100PCT_GTC")
    print("N4_OPEN_POSITIONS=" + str(len(mapped)))
    print("FINAM_ACTIVE_PROTECTIVE_STOPS=" + str(len(active)))
    for key in SYMBOLS:
        print("POSITION_" + key + "=" + str(mapped.get(SYMBOLS[key], 0)))
    print("FINAM_PROTECTION_LINKAGE=PASS")

def broker(api, account_id):
    from TradingSystemLab.stage8_robot.production_broker_state import position_quantities, order_views
    require(account_id, "ACCOUNT_ID_MISSING")
    account = api.account(account_id)
    orders_payload = api.orders(account_id)
    require(type(account) is dict and account.get("account_id") == account_id and
            account.get("status") in {"ACCOUNT_ACTIVE", "ACCOUNT_STATUS_ACTIVE"},
            "BROKER_ACCOUNT_IDENTITY_OR_STATUS_INVALID")
    require(type(orders_payload) is dict and type(orders_payload.get("orders")) is list,
            "BROKER_ORDERS_COLLECTION_INVALID")
    positions = position_quantities(account)
    orders = order_views(orders_payload)
    require(len(orders) == len(orders_payload["orders"]), "BROKER_ORDERS_INCOMPLETE")
    return positions, orders

def h1_observe(api, led, now):
    from TradingSystemLab.stage8_robot.readonly_supervisor import newest_expected_h1_close, trading_h1_windows
    from TradingSystemLab.stage8_robot.finam_api import completed_h1_bars
    results = {}
    for name, symbol in SYMBOLS.items():
        schedule = api.schedule(symbol)
        expected = newest_expected_h1_close(schedule, now)
        persisted = utc(led["h1"][name], "PERSISTED_H1_INVALID")
        require(persisted <= now + timedelta(seconds=CLOCK_TOLERANCE), "H1_WATERMARK_IN_FUTURE")
        if expected is None:
            raise Blocked("H1_CURRENT_SCHEDULE_NO_COMPLETED_SESSION")
        require(persisted >= expected, "H1_LEDGER_BEHIND_SCHEDULE")
        bars = api.bars(symbol, (now-timedelta(days=7)).isoformat(),now.isoformat())
        finished = completed_h1_bars(bars, now, trading_h1_windows(schedule))
        actual = {utc(row["timestamp"]) for row in finished}
        require(expected in actual, "H1_FINAM_EXPECTED_BAR_MISSING")
        results[name] = persisted.isoformat()
    for name, value in results.items():
        print("H1_" + name + "=" + value)
    print("FINAM_N4_COMPLETED_H1=PASS")

def verify(checkout, root, account, secret):
    require(checkout.is_dir() and root.is_dir(), "CHECKOUT_OR_RUNTIME_MISSING")
    proc = subprocess.run(["git", "-C", str(checkout), "rev-parse", "HEAD"],
                          text=True, capture_output=True, check=False)
    require(proc.returncode == 0 and proc.stdout.strip() == COMMIT,
            "PINNED_EXECUTABLE_COMMIT_MISMATCH")
    sys.path.insert(0, str(checkout))
    from TradingSystemLab.stage8_robot.finam_api import FinamAPI
    class ReadonlyAPI(FinamAPI):
        def __init__(self, secret, account_id):
            super().__init__(secret)
            self.account_path = "/v1/accounts/" + account_id
            self.allow = {self.account_path, self.account_path + "/orders"}
            self.allow.update("/v1/assets/" + s + "/schedule" for s in SYMBOLS.values())
        def _request(self, method, path, payload=None, auth=True, retries=0):
            if method == "POST" and path in {"/v1/sessions", "/v1/sessions/details"}:
                pass
            elif method == "GET" and payload is None and (path in self.allow or
                   any(path.startswith("/v1/instruments/" + s + "/bars?") for s in SYMBOLS.values())):
                pass
            else:
                raise Blocked("FORBIDDEN_FINAM_REQUEST")
            return super()._request(method, path, payload, auth, retries)
    digest = hashlib.sha256(account.encode("utf-8")).hexdigest()
    sw1, hb1 = local_state(root, digest)
    db1 = ledger(root, digest)
    require(hb1["cycle_count"] == db1["cycle"], "CYCLE_LEDGER_HEARTBEAT_MISMATCH")
    api = ReadonlyAPI(secret, account)
    api.create_session()
    details = api.session_details()
    require(isinstance(details, dict) and details.get("readonly") is True and
            type(details.get("account_ids")) is list and details["account_ids"].count(account) == 1,
            "SESSION_NOT_EXACT_REAL_READONLY")
    print("FINAM_SESSION=EXACT_REAL_READONLY")
    now = datetime.now(timezone.utc)
    h1_observe(api, db1, now)
    broker_positions, orders = broker(api, account)
    protection(hb1, db1["positions"], broker_positions, orders)
    # Recheck broker read side for transient changes while the robot is live.
    positions2, orders2 = broker(api, account)
    require(positions2 == broker_positions and
            [(v.order_id,v.status) for v in orders2 if v.active] ==
            [(v.order_id,v.status) for v in orders if v.active],
            "BROKER_CHANGED_DURING_OBSERVATION")
    sw2, hb2 = local_state(root, digest)
    db2 = ledger(root, digest)
    # Healthy cycles may advance naturally, but if state changes require retry.
    require(sw2 == sw1 and hb2 == hb1 and db2 == db1,
            "LOCAL_STATE_CHANGED_DURING_OBSERVATION")
    print("READONLY_SQLITE_WAL_INTENTS=PASS")
    print("POST_ARMED_HEALTHY_H1_RECONCILIATION=PASS")
    print("KILL_SWITCH=ARMED_GENERATION_62_UNCHANGED")
    print("ORDER_ENDPOINT_CALLS=0")
    print("SQLITE_DML_TASK_REARM_OR_CANCEL=0")
    print("CLASSIFICATION=ROADMAP36_POST_ARM_INDEPENDENT_READONLY_PASS")

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--runtime-root", type=Path, required=True)
    p.add_argument("--checkout", type=Path, required=True)
    args = p.parse_args()
    print("=== Roadmap 3.6 post-ARM one-shot FINAM READONLY observation ===")
    print("SESSION_POST_ONLY_ACCOUNT_ORDERS_N4_SCHEDULE_AND_BARS_GET_ONLY")
    try:
        verify(args.checkout.resolve(), args.runtime_root.resolve(),
               os.environ.get("TSL36_READONLY_ACCOUNT", ""),
               os.environ.get("TSL36_READONLY_SECRET", ""))
        return 0
    except Blocked as exc:
        print("CLASSIFICATION=BLOCKED:" + str(exc))
        return 1
    except Exception:
        print("CLASSIFICATION=BLOCKED:READONLY_OBSERVATION_EXCEPTION")
        return 1

if __name__ == "__main__":
    raise SystemExit(main())