"""27 Oct 2026: broker historical GET-only replay of 3 ACTUAL V20 M15 entries.
Reuses the exact frozen V20-03 research AST signal, never a new formula.
Loads V20 state SQLite read-only. No FINAM trading POST/cancel/stop, no Task
calls, no H1 or LIVE source edits, no prints of account/token/order IDs.
"""
from __future__ import annotations

from contextlib import closing
from datetime import datetime, timedelta, timezone
from decimal import Decimal
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import sys
from zoneinfo import ZoneInfo

from TradingSystemLab.stage8_robot.finam_api import FinamAPI
from TradingSystemLab.stage8_robot.execution_grid import initial_projection
from TradingSystemLab.stage8_robot.production_runtime import _load_registry
from V20_TradingSystem_M15.v20_runtime.finam_execution import (
    V20FinamReadAdapter, read_finam_m15_boundary,
)
from V20_TradingSystem_M15.v20_runtime.frozen_adapter import completed_signal

ROOT = Path(r"C:\V20Lab")
CASES = {
    "v20-shallow": ("SHALLOW_PULLBACK", "GLDRUBF", "SHORT", "2026-10-27T11:00:00", 13),
    "v20-obv": ("OBV_PRESSURE", "USDRUBF", "SHORT", "2026-10-27T10:30:00", 2),
    "v20-inside": ("INSIDE_DAY_RELEASE", "GLDRUBF", "SHORT", "2026-10-27T11:00:00", 13),
}
MSK = ZoneInfo("Europe/Moscow")


def need(condition, msg):
    if not condition:
        raise RuntimeError("V20_FROZEN_SIGNAL_AUDIT_" + msg)


def main():
    need(os.name == "nt" and os.environ.get("COMPUTERNAME", "").upper() == "URIU-PC",
         "INTEL_SCOPE")
    need(len(sys.argv) == 2 and sys.argv[1] in CASES, "ROBOT_ARGUMENT")
    robot = sys.argv[1]
    strategy, symbol, direction, entry_msk, quantity = CASES[robot]
    account = os.environ.get("V20_FINAM_ACCOUNT", "")
    token = os.environ.get("V20_FINAM_TOKEN", "")
    account_hash = os.environ.get("V20_FINAM_ACCOUNT_SHA256", "")
    need(bool(token) and hashlib.sha256(account.encode()).hexdigest() == account_hash,
         "BROKER_CREDENTIAL_SCOPE")
    dbpath = ROOT / "robots" / robot.removeprefix("v20-") / "state" / "v20-real-intents.sqlite3"
    need(dbpath.is_file() and not dbpath.is_symlink(), "SQLITE_MISSING")
    with closing(sqlite3.connect(dbpath.as_uri() + "?mode=ro", uri=True, timeout=5)) as db:
        db.execute("PRAGMA query_only=ON")
        ident = db.execute("SELECT value FROM state WHERE key='database_identity'").fetchone()
        need(ident is not None, "IDENTITY_MISSING")
        ident = json.loads(ident[0])
        need(ident.get("robot_id") == robot
             and ident.get("strategy") == strategy
             and ident.get("account_sha256") == account_hash,
             "ACCOUNT_STRATEGY_IDENTITY_MISMATCH")
        entries = []
        for encoded, status, key in db.execute("SELECT payload,status,idempotency_key FROM intents"):
            payload = json.loads(encoded)
            if payload.get("kind") == "ENTRY":
                entries.append((payload, status, key))
        need(len(entries) == 1, "EXPECTED_EXACT_ONE_ENTRY")
        entry, status, key = entries[0]
        need(status == "RECONCILED"
             and entry.get("symbol") == symbol
             and entry.get("direction") == direction
             and entry.get("entry_at") == entry_msk
             and entry.get("quantity") == quantity,
             "INTENT_FROZEN_SCOPE_CHANGED")
        submitted = db.execute("SELECT value FROM state WHERE key=?",
                               ("entry_submission:" + key,)).fetchone()
        need(submitted is not None, "SUBMISSION_CHECKPOINT_MISSING")
        submitted = json.loads(submitted[0])
        need(submitted.get("account_sha256") == account_hash,
             "SUBMISSION_ACCOUNT_CHANGED")
        submitted_at = datetime.fromisoformat(submitted["submitted_at"]).astimezone(timezone.utc)
        entry_at = datetime.fromisoformat(entry_msk).replace(tzinfo=MSK).astimezone(timezone.utc)
        lag = (submitted_at - entry_at).total_seconds()
        need(0 <= lag <= 60, "POST_OUTSIDE_NEXT_OPEN_MINUTE")
        record_atr = Decimal(entry["atr14"])
        reference = Decimal(entry["reference_entry"])
        stored_stop = Decimal(entry["initial_stop"])
    print("v20_audit_" + robot + "_entry_scope=PASS_FROZEN_INTENT_RECONCILED")
    print("v20_audit_" + robot + "_post_seconds_after_open=" + str(round(lag, 3)))
    # At the historical signal time, only historical broker bars are supplied
    # to the EXACT same M15 boundary and frozen AST code as autonomous V20.
    # This is a later GET replay, not a byte-for-byte capture of the past GET.
    audit_now = entry_at + timedelta(seconds=30)
    reader = V20FinamReadAdapter(
        api=FinamAPI(token), robot_id=robot, account_id=account,
        expected_account_hash=account_hash,
    )
    reader.authenticate()
    boundary = read_finam_m15_boundary(
        reader, symbol=symbol, from_utc=audit_now-timedelta(days=20),
        now=audit_now,
    )
    need(boundary.at_msk.isoformat() == entry_msk, "BOUNDARY_MISMATCH")
    sig = completed_signal(symbol, strategy, boundary.completed,
                           observed_at=boundary.at_msk)
    need(sig is not None, "HISTORICAL_FROZEN_SIGNAL_ABSENT")
    expected_side = -1 if direction == "SHORT" else 1
    need(sig.side == expected_side and sig.signal_bar_open + timedelta(minutes=15) ==
         boundary.at_msk, "SIDE_OR_IMMEDIATE_NEXT_OPEN_MISMATCH")
    actual_atr = Decimal(sig.atr14)
    # The original live candle query was several seconds before the market
    # POST. Tolerate <1e-8 ATR shift from a different 20-day warmup cutoff.
    difference = abs(actual_atr - record_atr)
    print("v20_audit_" + robot + "_frozen_side=SHORT")
    print("v20_audit_" + robot + "_signal_bar_msk=" + sig.signal_bar_open.isoformat())
    print("v20_audit_" + robot + "_completed_bars=" + str(len(boundary.completed)))
    print("v20_audit_" + robot + "_replay_atr14=" + str(actual_atr))
    print("v20_audit_" + robot + "_intent_atr14=" + str(record_atr))
    print("v20_audit_" + robot + "_atr_difference=" + str(difference))
    need(difference <= Decimal("0.00000001"), "FROZEN_ATR_NOT_REPRODUCED")
    witnessed = boundary.witnessed_open
    print("v20_audit_" + robot + "_broker_next_open=" + str(witnessed))
    print("v20_audit_" + robot + "_durable_reference_open=" + str(reference))
    need(witnessed == reference, "NEXT_OPEN_PRICE_MISMATCH")
    raw = reference - Decimal(expected_side)*Decimal(2)*record_atr
    executable, _ = initial_projection(direction, reference, raw,
                                       Decimal(_load_registry()[symbol]["price_step"]))
    print("v20_audit_" + robot + "_durable_initial_stop=" + str(stored_stop))
    need(executable == stored_stop, "INITIAL_2ATR_STOP_MISMATCH")
    print("v20_audit_" + robot + "=PASS_FROZEN_SIGNAL_NEXT_OPEN_ATR_INITIAL_STOP_FINAM_GET_ONLY")


if __name__ == "__main__":
    main()
