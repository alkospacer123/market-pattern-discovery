"""Intel FINAM real-readonly two-snapshot flatness diagnostic. Never submits orders."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import logging
import os
from pathlib import Path
import subprocess
import sys
import time

SPEC = "PROD_STAGE7_46DB784378797C7FB04636892350AFF21006D71A31F2CED9D4B974EDA2DC36B8"
IDENTITY = "TRAIL1__N4_01__FULL__R15"
LIVE_SHA = "184e8c2b8fa092a606249ff293a4f507160bff29"


class Blocked(Exception):
    pass


def require(condition, code):
    if not condition:
        raise Blocked(code)


def timestamp(value):
    try:
        result = datetime.fromisoformat(value.replace("Z", "+00:00"))
        require(result.utcoffset() is not None, "HEARTBEAT_TIMESTAMP_INVALID")
        return result.astimezone(timezone.utc)
    except (AttributeError, ValueError, TypeError):
        raise Blocked("HEARTBEAT_TIMESTAMP_INVALID") from None


def local_gate(root: Path, account_hash: str):
    switch = json.loads((root / "safety/stage8-trading-kill-switch.json").read_text(encoding="utf-8"))
    hb = json.loads((root / "diagnostics/stage8-12-4-production-heartbeat.json").read_text(encoding="utf-8"))
    require(switch.get("schema_id") == "stage8_trading_kill_switch.v1", "SWITCH_SCHEMA_INVALID")
    require(switch.get("production_specification_id") == SPEC, "SWITCH_PRODUCTION_ID_INVALID")
    require(switch.get("state") == "HALTED", "NEW_ENTRIES_NOT_HALTED")
    require(hb.get("schema_id") == "stage8_12_4_production_heartbeat.v1", "HEARTBEAT_SCHEMA_INVALID")
    require(hb.get("production_specification_id") == SPEC and hb.get("active_identity") == IDENTITY, "FROZEN_IDENTITY_INVALID")
    require(hb.get("accepted_code_commit") == LIVE_SHA, "HEARTBEAT_CODE_BINDING_INVALID")
    require(hb.get("account_hash") == account_hash, "ACCOUNT_HASH_MISMATCH")
    require(hb.get("health_status") == "HEALTHY" and hb.get("reconciliation_status") == "PASS", "HEARTBEAT_NOT_HEALTHY")
    for key in ("open_position_count", "unresolved_intent_count", "active_protective_stop_count"):
        require(type(hb.get(key)) is int and hb[key] == 0, "LOCAL_" + key.upper() + "_NOT_ZERO")
    now = datetime.now(timezone.utc)
    for key in ("timestamp", "last_successful_finam_api_contact"):
        age = (now - timestamp(hb.get(key))).total_seconds()
        require(-60 <= age <= 900, "HEARTBEAT_OR_FINAM_CONTACT_STALE")
    require(type(hb.get("position_protection")) is list and not hb["position_protection"], "LOCAL_PROTECTION_UNEXPECTED")
    return hb["cycle_count"]


def evaluate_broker(account, orders_response, expected_account, position_quantities, order_views):
    require(isinstance(account, dict) and account.get("account_id") == expected_account, "FINAM_ACCOUNT_ID_MISMATCH")
    require(account.get("status") in {"ACCOUNT_ACTIVE", "ACCOUNT_STATUS_ACTIVE"}, "FINAM_ACCOUNT_NOT_ACTIVE")
    positions = position_quantities(account)
    orders = order_views(orders_response)
    active = sum(1 for order in orders if order.active)
    return {"nonzero_positions": len(positions), "active_orders": active,
            "orders_scanned": len(orders), "flat": len(positions) == 0 and active == 0}


def run(root: Path, checkout: Path, *, secret, account, delay: float = 2):
    require(secret and account, "READONLY_CREDENTIAL_MISSING")
    sha = subprocess.check_output(["git", "-C", str(checkout), "rev-parse", "HEAD"], text=True, stderr=subprocess.DEVNULL).strip()
    require(sha == LIVE_SHA, "LIVE_CHECKOUT_COMMIT_INVALID")
    sys.path.insert(0, str(checkout))
    logging.getLogger("TradingSystemLab.stage8_robot.finam_api").setLevel(logging.CRITICAL)
    from TradingSystemLab.stage8_robot.finam_api import FinamAPI
    from TradingSystemLab.stage8_robot.production_broker_state import position_quantities, order_views

    from urllib.parse import quote

    class ReadonlyFinam(FinamAPI):
        def __init__(self, secret, account):
            super().__init__(secret)
            self.account_path = "/v1/accounts/" + quote(account, safe="")
            self.bound = False
            self.trace = []

        def _request(self, method, path, payload=None, auth=True, retries=0):
            if method == "POST" and path in {"/v1/sessions", "/v1/sessions/details"}:
                label = "SESSION"
            elif method == "GET" and self.bound and payload is None and path in {self.account_path, self.account_path + "/orders"}:
                label = "ACCOUNT" if path == self.account_path else "ORDERS"
            else:
                raise Blocked("FINAM_METHOD_OR_ENDPOINT_FORBIDDEN")
            self.trace.append(label)
            return super()._request(method, path, payload, auth, retries)

    account_hash = hashlib.sha256(account.encode("utf-8")).hexdigest()
    local_gate(root, account_hash)
    api = ReadonlyFinam(secret, account)
    api.create_session()
    details = api.session_details()
    require(isinstance(details, dict) and details.get("readonly") is True
            and isinstance(details.get("account_ids"), list)
            and details["account_ids"].count(account) == 1,
            "EXACT_READONLY_FINAM_SESSION_REQUIRED")
    api.bound = True
    print("FINAM_SESSION=EXACT_READONLY_ACCOUNT_BOUND")
    for number in (1, 2):
        local_gate(root, account_hash)
        account_response = api.account(account)
        order_response = api.orders(account)
        local_gate(root, account_hash)
        status = evaluate_broker(account_response, order_response, account, position_quantities, order_views)
        print(f"SNAPSHOT_{number}_NONZERO_POSITIONS={status['nonzero_positions']}")
        print(f"SNAPSHOT_{number}_ACTIVE_ORDERS={status['active_orders']}")
        print(f"SNAPSHOT_{number}_ORDERS_SCANNED={status['orders_scanned']}")
        require(status["flat"], "BROKER_EXPOSURE_OR_ACTIVE_ORDERS_PRESENT")
        if number == 1:
            time.sleep(delay)
    require(api.trace == ["SESSION", "SESSION", "ACCOUNT", "ORDERS", "ACCOUNT", "ORDERS"], "REQUEST_TRACE_UNEXPECTED")
    local_gate(root, account_hash)
    print("FRESH_FINAM_TWO_READONLY_SNAPSHOTS=PASS")
    print("ACCOUNT_IDENTITY_SHA_MATCH=PASS")
    print("BROKER_FLAT_AND_ZERO_ACTIVE_ORDERS=PASS")
    print("ORDER_ENDPOINT_CALLS=0")
    print("NO_TASK_SWITCH_SQLITE_MUTATION=YES")
    print("STOP_TASK_AUTHORIZED_BY_THIS_PROBE=NO")
    print("CLASSIFICATION=FRESH_FINAM_READONLY_FLAT_PASS_NOT_ISOLATED")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--runtime-root", type=Path, required=True)
    p.add_argument("--checkout", type=Path, required=True)
    args = p.parse_args()
    print("=== stage8 #493 strict finam real-readonly double flat probe ===")
    print("no live mutation no sqlite no order/cancel endpoints no task change")
    try:
        run(args.runtime_root.resolve(), args.checkout.resolve(),
            secret=os.environ.get("stage8_493_readonly_secret", ""),
            account=os.environ.get("stage8_493_readonly_account", ""))
        return 0
    except Exception as exc:
        code = str(exc) if isinstance(exc, Blocked) else "READONLY_OBSERVATION_FAILED"
        print("CLASSIFICATION=BLOCKED:" + code)
        print("NO_LIVE_CHANGES=YES")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
