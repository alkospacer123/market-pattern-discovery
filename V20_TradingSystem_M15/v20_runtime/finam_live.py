"""V20-08.4: one V20 M15 FINAM live cycle, instantiated per isolated account.

Only frozen completed M15/NEXT_OPEN entries. Reuse H1 FINAM, SQLite,
market/stop/exit wire, exact broker fill and stop proofs from finam_execution.
This is NOT the technical one-off operator. Fail closed on any unowned state.
Never install/enable tasks just by importing this module.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone
from decimal import Decimal
import hashlib
import json
import logging
import os
from pathlib import Path
import re
import time
from zoneinfo import ZoneInfo
from fractions import Fraction

from TradingSystemLab.stage8_robot.broker import compact_client_order_id
from TradingSystemLab.stage8_robot.execution_grid import project_stop
from TradingSystemLab.stage8_robot.finam_api import FinamAPI
from TradingSystemLab.stage8_robot.production_runtime import _load_registry
from TradingSystemLab.stage8_robot.trading_safety_gate import load_kill_switch, emergency_halt

from .account_risk import RiskReservation
from .finam_execution import (
    V20FinamBlocked, V20FinamReadAdapter, V20SingleTradeTransport,
    V20TradeJournal, propose_finam_m15_next_open, read_finam_m15_boundary,
    frozen_observed_session_exit,
)
from .h1_state_journal import ROBOT_STRATEGIES
from .offline_planner import N4, OfflinePlanner, STEP

SYMBOLS = ("USDRUBF", "CNYRUBF", "GLDRUBF", "IMOEXF")
DEFAULT_COSTS = {"USDRUBF": "8.34", "CNYRUBF": "2.02",
                 "GLDRUBF": "3.64", "IMOEXF": "4.16"}
AUTH_SCHEMA = "v20.08.4.live_authorization.v1"
POLL_SECONDS = 3


class V20LiveJournal(V20TradeJournal):
    """Uses the PRE-EXISTING real V20 SQLite, identity and H1 InstanceLock."""
    live_runtime = True


def _safe_auth(path: Path, *, journal: V20LiveJournal, source: str) -> dict:
    expected = journal.instance_root / "safety" / "v20-live-authorization.json"
    if (path != expected or not expected.is_file() or expected.is_symlink()
            or expected.parent.is_symlink()
            or not re.fullmatch(r"[a-f0-9]{40}", source)):
        raise V20FinamBlocked("V20_LIVE_AUTH_FILE_REQUIRED")
    try:
        data = json.loads(expected.read_text(encoding="utf-8"))
    except (OSError, ValueError, UnicodeError):
        raise V20FinamBlocked("V20_LIVE_AUTH_CORRUPT") from None
    required = {
        "schema": AUTH_SCHEMA, "robot_id": journal.robot_id,
        "account_sha256": journal.account_hash, "source_commit": source,
        "owner_approved": True, "execution_mode": "V20_FROZEN_M15_LIVE",
        "risk_fraction": "0.015", "initial_stop_atr": "2",
        "signals": "FROZEN_COMPLETED_M15_NEXT_OPEN",
        "symbols": list(SYMBOLS),
    }
    if (not isinstance(data, dict)
            or set(data) != set(required) | {"roundtrip_cost_rub"}
            or any(data.get(k) != value for k, value in required.items())):
        raise V20FinamBlocked("V20_LIVE_AUTH_SCOPE_INVALID")
    costs = data["roundtrip_cost_rub"]
    if not isinstance(costs, dict) or set(costs) != set(SYMBOLS):
        raise V20FinamBlocked("V20_LIVE_COSTS_MISSING")
    for symbol in SYMBOLS:
        try:
            number = Decimal(str(costs[symbol]))
        except (TypeError, ArithmeticError, ValueError):
            raise V20FinamBlocked("V20_LIVE_COST_INVALID") from None
        if not number.is_finite() or number <= 0:
            raise V20FinamBlocked("V20_LIVE_COST_INVALID")
    return data


def _entries(journal: V20LiveJournal):
    result = []
    for row in journal.store.all_intents():
        if row["payload"].get("kind") == "ENTRY":
            payload = row["payload"]
            if (payload.get("mode") != "PRETRADE_NOT_AUTHORIZED"
                    or payload.get("robot_id") != journal.robot_id
                    or payload.get("account_sha256") != journal.account_hash
                    or payload.get("symbol") not in N4):
                raise V20FinamBlocked("V20_LIVE_LEDGER_FOREIGN_ENTRY")
            result.append(row)
    return result


def _ownership(journal: V20LiveJournal, snapshot) -> list[dict]:
    """Reject any broker exposure not explicitly represented by V20 intents."""
    entries = _entries(journal)
    current_symbols = {}
    expected_orders = {}
    for row in entries:
        key, payload = row["idempotency_key"], row["payload"]
        symbol = payload["finam_symbol"]
        if symbol != _load_registry()[payload["symbol"]]["finam_symbol"]:
            raise V20FinamBlocked("V20_LIVE_BROKER_SYMBOL_MISMATCH")
        if journal.store.get("flat_cleanup:" + key):
            continue
        if symbol in current_symbols:
            raise V20FinamBlocked("V20_LIVE_TWO_POSITIONS_SAME_INSTRUMENT")
        current_symbols[symbol] = row
        for suffix, kind in (("", "REGULAR"), (":stop", "SLTP"),
                             (":frozen-exit", "REGULAR")):
            intent_key = key + suffix
            if (suffix == "" or journal.store.intent(intent_key) is not None):
                client = compact_client_order_id(intent_key)
                if client in expected_orders:
                    raise V20FinamBlocked("V20_LIVE_CLIENT_ORDER_COLLISION")
                expected_orders[client] = (symbol, kind)
    for symbol, position in snapshot.positions.items():
        if not position:
            continue
        row = current_symbols.get(symbol)
        if row is None:
            raise V20FinamBlocked("V20_LIVE_UNOWNED_BROKER_POSITION")
        payload = row["payload"]
        if ((position > 0) != (payload["direction"] == "LONG")
                or abs(position) > payload["quantity"]):
            raise V20FinamBlocked("V20_LIVE_BROKER_POSITION_SIDE_OR_SIZE")
    active_seen = set()
    for order in snapshot.orders:
        if not order.active:
            continue
        owner = expected_orders.get(order.client_order_id)
        if (owner is None or order.client_order_id in active_seen
                or owner != (order.symbol, order.kind)):
            raise V20FinamBlocked("V20_LIVE_FOREIGN_OR_DUPLICATE_ACTIVE_ORDER")
        active_seen.add(order.client_order_id)
    return entries


class V20LiveTransport(V20SingleTradeTransport):
    """Minimal authorized V20 LIVE adaptation of already proven H1 order code."""
    _live_mode = True

    def __init__(self, journal: V20LiveJournal, reader: V20FinamReadAdapter,
                 *, source: str):
        if not isinstance(journal, V20LiveJournal):
            raise V20FinamBlocked("V20_LIVE_JOURNAL_REQUIRED")
        super().__init__(journal=journal, reader=reader, accepted_commit=source)
        self.auth_path = journal.instance_root / "safety" / "v20-live-authorization.json"
        self.source = source
        self.auth = _safe_auth(self.auth_path, journal=journal, source=source)

    def _permit(self, *, key: str, kind: str) -> dict:
        _safe_auth(self.auth_path, journal=self.journal, source=self.source)
        if kind not in ("ENTRY", "PROTECTIVE_STOP", "FROZEN_EXIT"):
            raise V20FinamBlocked("V20_LIVE_OPERATION_FORBIDDEN")
        row = self.journal.store.intent(key)
        if (row is None or row["payload"].get("kind") != "ENTRY"
                or row["payload"].get("account_sha256") != self.journal.account_hash):
            raise V20FinamBlocked("V20_LIVE_ENTRY_UNKNOWN")
        payload = row["payload"]
        return {"instrument": payload["symbol"], "direction": payload["direction"],
                "max_quantity": payload["quantity"],
                "max_risk_rub": str(Decimal("0.015") * self.reader.snapshot(
                    now=datetime.now(timezone.utc)).realized_equity)}

    def _entry(self, key: str, *, snapshot, now: datetime):
        self._permit(key=key, kind="ENTRY")
        self.reader._fresh(snapshot, now)
        refreshed = self.reader.snapshot(now=now)
        if (refreshed.positions != snapshot.positions
                or refreshed.orders != snapshot.orders
                or refreshed.realized_equity != snapshot.realized_equity
                or refreshed.available_cash != snapshot.available_cash):
            raise V20FinamBlocked("V20_LIVE_BROKER_CHANGED_BEFORE_ENTRY")
        _ownership(self.journal, refreshed)
        row = self.journal.store.intent(key)
        if row is None or row["status"] != "INTENT_PERSISTED":
            raise V20FinamBlocked("V20_LIVE_ENTRY_ALREADY_SUBMITTED")
        p = row["payload"]
        if (refreshed.positions.get(p["finam_symbol"], 0) != 0
                or any(o.active and o.symbol == p["finam_symbol"]
                       for o in refreshed.orders)):
            raise V20FinamBlocked("V20_LIVE_INSTRUMENT_OCCUPIED")
        if self.journal.store.get("execution_halt") is not None:
            raise V20FinamBlocked("V20_LIVE_JOURNAL_HALTED")
        entry_at = datetime.fromisoformat(p["entry_at"])
        boundary = entry_at.replace(tzinfo=ZoneInfo("Europe/Moscow")).astimezone(timezone.utc)
        if not timedelta(0) <= datetime.now(timezone.utc) - boundary <= timedelta(seconds=60):
            raise V20FinamBlocked("V20_LIVE_NEXT_OPEN_EXPIRED")
        reservation = RiskReservation.restore(
            self.journal.store.get("risk_reservations", {}).get(key))
        if reservation.reserved_risk > refreshed.realized_equity * Decimal("0.015"):
            raise V20FinamBlocked("V20_LIVE_SINGLE_TRADE_RISK_EXCEEDED")
        return p


def _close_flat(journal: V20LiveJournal, key: str):
    with journal.store.transaction():
        if journal.store.get("flat_cleanup:" + key) is None:
            raise V20FinamBlocked("V20_LIVE_CLOSURE_NOT_BROKER_PROVEN")
        reserved = journal.store.get("risk_reservations", {})
        reserved.pop(key, None)
        journal.store.put("risk_reservations", reserved)


def _follow_existing(sender: V20LiveTransport, now: datetime, snapshot) -> str:
    journal, reader = sender.journal, sender.reader
    entries = _ownership(journal, snapshot)
    for row in entries:
        key, payload = row["idempotency_key"], row["payload"]
        if journal.store.get("flat_cleanup:" + key):
            continue
        finam_symbol = payload["finam_symbol"]
        position = snapshot.positions.get(finam_symbol, 0)
        if not position:
            if row["status"] in ("INTENT_PERSISTED", "UNCERTAIN", "SUBMITTED"):
                journal.reconcile_order(key=key, snapshot=snapshot)
                raise V20FinamBlocked("V20_LIVE_ENTRY_RECONCILIATION_REQUIRED")
            exit_intent = journal.store.intent(key + ":frozen-exit")
            proof = journal.store.get("protected_fill:" + key)
            if exit_intent is not None and isinstance(proof, dict):
                status = sender.cancel_stop_after_flat_once(
                    key=key, snapshot=snapshot, now=now)
                if status == "BROKER_FLAT_NO_ACTIVE_STOP":
                    _close_flat(journal, key)
                return status
            stop = next((o for o in snapshot.orders
                         if isinstance(proof, dict)
                         and o.order_id == proof.get("broker_stop_id")
                         and o.kind == "SLTP" and o.symbol == finam_symbol), None)
            if (stop is not None and stop.status in {"FILLED", "EXECUTED"}
                    and not any(o.active and o.symbol == finam_symbol
                                for o in snapshot.orders)):
                journal.store.put("flat_cleanup:" + key, {
                    "status": "STOP_EXECUTED_FINAM_FLAT",
                    "account_sha256": journal.account_hash})
                _close_flat(journal, key)
                return "STOP_EXECUTED_FLAT"
            # A nonterminal market entry may still be awaiting fill; do not
            # place another market order or infer a clean account from it.
            raise V20FinamBlocked("V20_LIVE_UNEXPLAINED_FLAT_RECONCILE")
        journal.reconcile_order(key=key, snapshot=snapshot)
        if journal.store.intent(key + ":frozen-exit") is not None:
            # Never retransmit exit. Keep its active stop until broker-flat.
            return "EXIT_POSTED_AWAIT_BROKER_FLAT"
        stop_intent = journal.store.intent(key + ":stop")
        if stop_intent is None:
            submitted = journal.store.get("entry_submission:" + key)
            if not isinstance(submitted, dict):
                raise V20FinamBlocked("V20_LIVE_ENTRY_POST_CHECKPOINT_MISSING")
            fills = reader.inspect_entry_fills(
                snapshot, entry_key=key, symbol=payload["symbol"],
                direction=payload["direction"],
                requested_quantity=payload["quantity"],
                submitted_at=datetime.fromisoformat(submitted["submitted_at"]),
                now=now)
            if (fills.get("matched_quantity") != abs(position)
                    or not fills.get("matched_unique_fills")):
                raise V20FinamBlocked("V20_LIVE_FILL_PROOF_REQUIRED")
            exact = sum((int(f["quantity"]) * Fraction(f["price"])
                         for f in fills["matched_unique_fills"]), Fraction(0)) / abs(position)
            side = 1 if payload["direction"] == "LONG" else -1
            price = project_stop(
                payload["direction"], exact - side * 2 * Fraction(payload["atr14"]),
                Decimal(_load_registry()[payload["symbol"]]["price_step"]))
            sender.submit_protection_once(
                key=key, snapshot=snapshot, stop_price=price, now=now)
            return "STOP_ACK_NEEDS_BROKER_PROOF"
        if stop_intent["status"] not in ("ACK", "RECONCILED"):
            raise V20FinamBlocked("V20_LIVE_STOP_POST_UNKNOWN_NO_RETRY")
        journal.observe_protected_entry(
            key=key, reader=reader, snapshot=snapshot, now=now)
        if journal.store.get("execution_halt"):
            raise V20FinamBlocked("V20_LIVE_POST_FILL_RISK_HALTED")
        clock = now.astimezone(ZoneInfo("Europe/Moscow"))
        if (clock.minute % 15 or clock.second >= 60):
            continue
        entry_at = datetime.fromisoformat(payload["entry_at"])
        start = entry_at.replace(tzinfo=ZoneInfo("Europe/Moscow")).astimezone(timezone.utc)
        boundary = read_finam_m15_boundary(
            reader, symbol=payload["symbol"], from_utc=start-STEP,
            now=now, require_adjacent_completed=False)
        due = frozen_observed_session_exit(boundary, entry_open_msk=entry_at)
        if due == "EXIT_AT_THIRD_OBSERVED_SESSION_OPEN":
            sender.submit_frozen_exit_once(
                key=key, boundary=boundary, snapshot=snapshot, now=now)
            return "FROZEN_EXIT_ACK_KEEP_STOP_UNTIL_FLAT"
        if due != "HOLD_UNTIL_THIRD_OBSERVED_SESSION":
            journal.store.put("execution_halt", "FROZEN_EXIT_OPEN_MISSED")
            raise V20FinamBlocked("V20_LIVE_FROZEN_EXIT_DEADLINE_MISSED")
    return "BROKER_RECONCILED_PROTECTION_PASS"


def run_cycle(sender: V20LiveTransport, now: datetime) -> str:
    journal, reader = sender.journal, sender.reader
    _safe_auth(sender.auth_path, journal=journal, source=sender.source)
    snapshot = reader.snapshot(now=now)
    state = _follow_existing(sender, now, snapshot)
    if state != "BROKER_RECONCILED_PROTECTION_PASS":
        return state
    switch, error = load_kill_switch(journal.instance_root)
    if (error or not switch or switch.get("state") != "ARMED"
            or journal.store.get("execution_halt")):
        return "HALTED_NO_NEW_ENTRIES"
    msk = now.astimezone(ZoneInfo("Europe/Moscow"))
    if msk.minute % 15 or msk.second >= 60:
        return "WAIT_NEXT_M15_OPEN"
    day = OfflinePlanner._session_key(msk.replace(tzinfo=None)).isoformat()
    if len(journal.store.get("session_entries", {}).get(day, [])) >= 2:
        return "SESSION_ENTRY_LIMIT_REACHED"
    current_open = {
        row["payload"]["symbol"] for row in _entries(journal)
        if not journal.store.get("flat_cleanup:" + row["idempotency_key"])
    }
    same_session = {
        journal.store.intent(key)["payload"]["symbol"]
        for key in journal.store.get("session_entries", {}).get(day, [])
    }
    for symbol in SYMBOLS:
        if symbol in current_open or symbol in same_session:
            continue
        cost = Decimal(str(sender.auth["roundtrip_cost_rub"][symbol]))
        # FINAM M15 witness must be fresh; an absent/newly delayed Open
        # yields NO ORDER rather than a synthetic or late fill.
        try:
            draft = propose_finam_m15_next_open(
                reader, symbol=symbol, from_utc=now-timedelta(days=20),
                now=now, cost_per_contract=cost)
        except V20FinamBlocked as exc:
            if str(exc) in ("NEXT_OPEN_CURRENT_OPEN_MISSING", "M15_CURRENT_OPEN_NOT_PUBLISHED"):
                continue
            raise
        if draft is None:
            continue
        signal, candidate, authority, broker = draft
        _ownership(journal, broker)
        key = journal.prepare_entry(
            signal=signal, entry=candidate,
            authority=authority, snapshot=broker)
        sender.submit_entry_once(
            key=key, snapshot=reader.snapshot(now=now), now=now)
        return "ENTRY_ACK_NEEDS_FILL_AND_STOP"
    return "NO_FROZEN_SIGNAL"


def run(*, root: Path, robot: str, source: str, once: bool = False) -> int:
    account = os.environ.get("V20_FINAM_ACCOUNT", "")
    token = os.environ.get("V20_FINAM_TOKEN", "")
    scope = os.environ.get("V20_FINAM_ACCOUNT_SHA256", "")
    if (root.name.casefold() != "v20lab" or not root.is_absolute()
            or robot not in ROBOT_STRATEGIES or not token
            or not re.fullmatch(r"[A-Za-z0-9_.-]{1,128}", account)
            or not re.fullmatch(r"[0-9a-f]{64}", scope)
            or hashlib.sha256(account.encode()).hexdigest() != scope):
        raise V20FinamBlocked("V20_LIVE_SCOPE_INVALID")
    logging.getLogger("TradingSystemLab.stage8_robot.finam_api").setLevel(logging.ERROR)
    with V20LiveJournal(root, robot, account) as journal:
        api = FinamAPI(token)
        reader = V20FinamReadAdapter(
            api=api, robot_id=robot, account_id=account,
            expected_account_hash=scope)
        sender = V20LiveTransport(journal, reader, source=source)
        reader.authenticate()
        logs = journal.instance_root / "logs"
        if logs.is_symlink():
            raise V20FinamBlocked("V20_LIVE_LOG_PATH_LINK")
        logs.mkdir(parents=True, exist_ok=True)
        output = logs / "live-m15.jsonl"
        if output.is_symlink():
            raise V20FinamBlocked("V20_LIVE_LOG_FILE_LINK")
        while True:
            now = datetime.now(timezone.utc)
            try:
                state = run_cycle(sender, now)
            except BaseException as exc:
                # A failure cannot result in re-posting a market order. The
                # H1 broker-side protective stop must remain untouched.
                emergency_halt(journal.instance_root)
                label = str(exc)
                state = label if re.fullmatch(r"[A-Z0-9_]{1,100}", label) else type(exc).__name__
                with output.open("a", encoding="utf-8") as f:
                    f.write(json.dumps({"utc": now.isoformat(), "robot": robot,
                                        "state": "HALT_" + state}, sort_keys=True)+"\n")
                raise
            with output.open("a", encoding="utf-8") as f:
                f.write(json.dumps({"utc": now.isoformat(), "robot": robot,
                                    "state": state}, sort_keys=True)+"\n")
            if once:
                return 0
            time.sleep(POLL_SECONDS)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--robot", choices=sorted(ROBOT_STRATEGIES), required=True)
    parser.add_argument("--source-commit", required=True)
    parser.add_argument("--once", action="store_true")
    args = parser.parse_args()
    try:
        return run(root=args.root, robot=args.robot,
                   source=args.source_commit, once=args.once)
    except Exception as exc:
        label = str(exc)
        print("v20_08_4_live=HOLD_" + (
            label if re.fullmatch(r"[A-Z0-9_]{1,100}", label)
            else type(exc).__name__), flush=True)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
