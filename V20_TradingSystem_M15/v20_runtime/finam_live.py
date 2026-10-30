"""V20-08.4: one V20 M15 FINAM live cycle, instantiated per isolated account.

Only frozen completed M15/NEXT_OPEN entries. Reuse H1 FINAM, SQLite,
market/stop/exit wire, exact broker fill and stop proofs from finam_execution.
This is NOT the technical one-off operator. Fail closed on any unowned state.
Never install/enable tasks just by importing this module.
"""
from __future__ import annotations

import argparse
from contextlib import closing
import sqlite3
from types import SimpleNamespace
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
from TradingSystemLab.stage8_robot.account_cleanliness import TERMINAL_ORDER_STATUSES
from TradingSystemLab.stage8_robot.production_broker_state import unique_order_by_client_id
from TradingSystemLab.stage8_robot.execution_grid import project_stop
from TradingSystemLab.stage8_robot.finam_api import FinamAPI, FinamError, FinamNotFound, FinamServerError, FinamTimeout, FinamRateLimit
from TradingSystemLab.stage8_robot.production_runtime import _load_registry
from TradingSystemLab.stage8_robot.trading_safety_gate import load_kill_switch, emergency_halt, write_kill_switch

from .account_risk import RiskReservation
from .finam_execution import (
    V20FinamBlocked, V20FinamReadAdapter, V20SingleTradeTransport,
    V20TradeJournal, propose_finam_m15_next_open, read_finam_m15_boundary,
    frozen_observed_session_exit,
)
from .h1_state_journal import ROBOT_STRATEGIES
from .offline_planner import N4, OfflinePlanner, STEP

# Preserve the already accepted reference runner's deterministic N4 tie order.
SYMBOLS = tuple(sorted(N4))
AUTH_SCHEMA = "v20.08.4.live_authorization.v1"
POLL_SECONDS = 30
FAST_RECONCILIATION_SECONDS = 3
NIGHT_PROTECTED_POLL_SECONDS = 120


class V20FinamSnapshotReadRetry(FinamError):
    """An untrusted initial broker snapshot: retry without entry or order POST.

    The original H1 error may contain an account path. Log only an HTTP
    status or bounded fault label, never account IDs or response bodies.
    """


def _night_flat_snapshot_fault(exc, *, journal, reader, now):
    """Only on a flat durable ledger and outside frozen NEXT_OPEN hours.

    A FINAM HTTP rejection of the INITIAL account/orders snapshot cannot
    authorize any trade. After broker recovery a fresh full snapshot and
    ownership proof still precede every entry. Unsettled intents, position
    management, order POST, authentication 401/403 and non-account endpoints
    remain strict HALT. The overnight 2026-10-30 archive had 3 such generic
    FinamError HALTs, but no HTTP statuses; preserve status evidence here.
    """
    msk = now.astimezone(ZoneInfo("Europe/Moscow"))
    if (10, 15) <= (msk.hour, msk.minute) <= (17, 15):
        return None
    if journal.store.get("execution_halt"):
        return None
    if any(
        row["payload"].get("kind") == "ENTRY"
        and not journal.store.get("flat_cleanup:" + row["idempotency_key"])
        for row in journal.store.all_intents()
    ):
        return None
    account = getattr(reader, "account_id", None)
    if not isinstance(account, str) or not re.fullmatch(r"[A-Za-z0-9_.-]{1,128}", account):
        return None
    expected = {"/v1/accounts/" + account, "/v1/accounts/" + account + "/orders"}
    if type(exc) is FinamNotFound and str(exc) in expected:
        return "404"
    if type(exc) is not FinamError:
        return None
    match = re.fullmatch(r"HTTP_(4[0-9]{2}):(.+)", str(exc))
    if not match or match.group(1) in {"401", "403"} or match.group(2) not in expected:
        return None
    return match.group(1)


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
            stop = next((o for o in snapshot.orders
                         if isinstance(proof, dict)
                         and o.order_id == proof.get("broker_stop_id")
                         and o.kind == "SLTP" and o.symbol == finam_symbol), None)
            # H1 _flat_cleanup_and_exit: a proved broker-flat position is
            # authoritative whether it was flattened by SLTP, a planned
            # frozen exit or manual broker action. Never cancel an active
            # stop until broker-flat and the exact stop ID are proven.
            if (stop is not None and stop.status in {"FILLED", "EXECUTED", "SL_EXECUTED"}
                    and not any(o.active and o.symbol == finam_symbol
                                for o in snapshot.orders)):
                journal.store.put("flat_cleanup:" + key, {
                    "status": "STOP_EXECUTED_FINAM_FLAT",
                    "account_sha256": journal.account_hash})
                _close_flat(journal, key)
                return "STOP_EXECUTED_FLAT"
            if isinstance(proof, dict):
                existing_cancel = journal.store.intent(key + ":cancel-after-flat")
                if existing_cancel is not None and any(
                    o.active and o.kind == "SLTP" and o.symbol == finam_symbol
                    for o in snapshot.orders
                ):
                    # One acknowledged or uncertain cancel is already durable.
                    # Do not retransmit; FINAM must prove stop inactive.
                    return "STOP_CANCEL_WAIT_BROKER_NO_RETRANSMIT"
                status = sender.cancel_stop_after_flat_once(
                    key=key, snapshot=snapshot, now=now)
                if status == "BROKER_FLAT_NO_ACTIVE_STOP":
                    _close_flat(journal, key)
                return status
            # A newly ACKed market order can be awaiting its first fill. Never
            # interpret it as a free instrument or submit another order.
            order = unique_order_by_client_id(
                list(snapshot.orders), compact_client_order_id(key))
            submission = journal.store.get("entry_submission:" + key)
            if isinstance(submission, dict) and order is not None:
                since = datetime.fromisoformat(submission["submitted_at"])
                age = now.astimezone(timezone.utc) - since.astimezone(timezone.utc)
                if (timedelta(0) <= age <= timedelta(seconds=60)
                        and row["status"] == "ACK"):
                    return "ENTRY_ACK_AWAIT_BROKER_FILL"
            raise V20FinamBlocked("V20_LIVE_UNEXPLAINED_FLAT_RECONCILE")
        journal.reconcile_order(key=key, snapshot=snapshot)
        exit_intent = journal.store.intent(key + ":frozen-exit")
        if exit_intent is not None:
            # H1 _reconcile_intents: a terminal rejected/cancelled exit with
            # exposure is a fault, NOT indefinitely "awaiting broker flat".
            # Keep the existing protective SLTP untouched; never retry POST.
            exit_order = unique_order_by_client_id(
                list(snapshot.orders), compact_client_order_id(key + ":frozen-exit"))
            if exit_order is not None:
                wire = exit_intent["payload"]["wire"]
                from TradingSystemLab.stage8_robot.production_broker_state import _contracts
                if (exit_order.kind != "REGULAR"
                        or exit_order.order_id != exit_intent["broker_order_id"]
                        or exit_order.symbol != wire["symbol"]
                        or exit_order.side != wire["side"]
                        or _contracts(exit_order.request.get("quantity"),
                                      "V20_EXIT_QTY_INVALID") !=
                           _contracts(wire["quantity"], "V20_EXIT_QTY_INVALID")):
                    raise V20FinamBlocked("V20_LIVE_EXIT_BROKER_IDENTITY_MISMATCH")
                if exit_order.status in TERMINAL_ORDER_STATUSES:
                    journal.store.put("execution_halt", "FROZEN_EXIT_BROKER_TERMINAL_WITH_POSITION")
                    raise V20FinamBlocked("V20_LIVE_EXIT_TERMINAL_POSITION_STILL_OPEN")
            elif exit_intent["status"] == "ACK":
                raise V20FinamBlocked("V20_LIVE_EXIT_ACK_MISSING_BROKER_PROOF")
            # No retransmission of an UNCERTAIN exit; keep the active stop.
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
        # Outside MOEX hours the frozen exit is not due. Do not fetch M15.
        if _closed_moex_night(now):
            continue
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



def _closed_moex_night(now: datetime) -> bool:
    clock = now.astimezone(ZoneInfo("Europe/Moscow"))
    minutes = clock.hour * 60 + clock.minute
    return not (6 * 60 + 50 <= minutes < 23 * 60 + 50)


def _closed_night_protected(journal: V20LiveJournal, snapshot) -> bool:
    """Slow down only after a fresh full broker snapshot and verified 100% SLTP.

    _follow_existing() must already have reconciled every position and stop.
    Any unsettled entry/exit or active non-stop order keeps strict polling.
    """
    if (not any(snapshot.positions.values()) or journal.store.get("execution_halt")
            or any(o.active and o.kind != "SLTP" for o in snapshot.orders)):
        return False
    for row in _entries(journal):
        key = row["idempotency_key"]
        if journal.store.get("flat_cleanup:" + key):
            continue
        symbol = row["payload"]["finam_symbol"]
        stop = journal.store.intent(key + ":stop")
        proof = journal.store.get("protected_fill:" + key)
        if (not snapshot.positions.get(symbol, 0)
                or row["status"] != "RECONCILED"
                or journal.store.intent(key + ":frozen-exit") is not None
                or journal.store.intent(key + ":cancel-after-flat") is not None
                or not stop or stop["status"] not in ("ACK", "RECONCILED")
                or not isinstance(proof, dict)
                or proof.get("filled_quantity") != abs(snapshot.positions[symbol])
                or proof.get("broker_stop_percent") != "100"
                or not any(o.active and o.kind == "SLTP" and o.symbol == symbol
                           and o.order_id == proof.get("broker_stop_id")
                           for o in snapshot.orders)):
            return False
    return True


def _night_protected_sleep_seconds(now: datetime) -> float:
    """Never let a 120s overnight sleep delay the 06:50 MSK full check."""
    if not _closed_moex_night(now):
        return 0.0
    clock = now.astimezone(ZoneInfo("Europe/Moscow"))
    opening = clock.replace(hour=6, minute=50, second=0, microsecond=0)
    if (clock.hour, clock.minute) >= (23, 50):
        opening += timedelta(days=1)
    return min(NIGHT_PROTECTED_POLL_SECONDS,
               max(0.0, (opening - clock).total_seconds()))


def _closed_night_without_live_exposure(journal: V20LiveJournal, now: datetime) -> bool:
    """Skip broker polling only while MOEX futures is closed and V20 is flat.

    Weekday MOEX closed interval: 23:50..06:50 Moscow. In particular, this
    must never suppress broker follow-up for an entry, stop, exit or uncertain
    operation. On the next open full broker reconciliation runs BEFORE entry.
    No alternate trading calendar, service or strategy timing is introduced.
    """
    if not _closed_moex_night(now):
        return False
    if journal.store.get("execution_halt"):
        return False
    intents = journal.store.all_intents()
    if any(
        not isinstance(row.get("payload"), dict)
        or row["payload"].get("kind") not in {"ENTRY", "STOP", "FROZEN_EXIT", "STOP_CANCEL"}
        for row in intents
    ):
        return False
    # A pending entry always needs broker reconciliation, regardless of
    # whether its journal row has all fields (a corrupt entry still fails
    # closed in the normal broker path).
    if any(row["payload"]["kind"] == "ENTRY"
           and not journal.store.get("flat_cleanup:" + row["idempotency_key"])
           for row in intents):
        return False
    entries = _entries(journal)
    if intents and not entries:
        return False  # Orphan order/stop without an entry: do not skip.
    return True


def run_cycle(sender: V20LiveTransport, now: datetime) -> str:
    journal, reader = sender.journal, sender.reader
    reader._m15_timestamp_diagnostic = None
    reader._closed_night_flat_no_get = False
    _safe_auth(sender.auth_path, journal=journal, source=sender.source)
    # The broker is closed at 23:50..06:50 MSK. No frozen new entry/exit
    # can happen then. When ALL prior entry/stop intents are durably closed,
    # skip FINAM GET altogether; leave the existing worker and switch intact.
    # Any live/unsettled exposure continues H1-style FINAM reconciliation.
    if _closed_night_without_live_exposure(journal, now):
        switch, error = load_kill_switch(journal.instance_root)
        if error or not switch or switch.get("state") != "ARMED":
            return "HALTED_NO_NEW_ENTRIES"
        reader._closed_night_flat_no_get = True
        return "WAIT_NEXT_M15_OPEN"
    # H1 handles any FINAM cycle read failure in the shared outer loop:
    # record a fault, retry in 3 seconds, and do not submit a new entry.
    try:
        snapshot = reader.snapshot(now=now)
    except FinamError as exc:
        # Preserve previously approved 400/408 initial-snapshot retry.
        match = re.match(r"^HTTP_(400|408):", str(exc)) if type(exc) is FinamError else None
        if match is not None:
            raise V20FinamSnapshotReadRetry("FINAM_SNAPSHOT_HTTP_" + match.group(1)) from exc
        # 2026-10-30: a 5xx storm followed by a generic account/order GET 4xx
        # on each bot. With no unsettled durable entry and outside the entry
        # window, retry the full snapshot rather than permanently HALT.
        # No trade or stop action is authorized without a successful NEW
        # full snapshot and position/stop ownership reconciliation.
        status = _night_flat_snapshot_fault(exc, journal=journal, reader=reader, now=now)
        if status is None:
            raise
        raise V20FinamSnapshotReadRetry("FINAM_NIGHT_SNAPSHOT_HTTP_" + status) from exc
    state = _follow_existing(sender, now, snapshot)
    if state != "BROKER_RECONCILED_PROTECTION_PASS":
        return state
    switch, error = load_kill_switch(journal.instance_root)
    if (error or not switch or switch.get("state") != "ARMED"
            or journal.store.get("execution_halt")):
        return "HALTED_NO_NEW_ENTRIES"
    # Fresh FINAM position/stop reconciliation above; no M15 requests at night.
    if _closed_moex_night(now) and _closed_night_protected(journal, snapshot):
        # Existing operator/Control Center already classifies this as PASS.
        return "BROKER_RECONCILED_PROTECTION_PASS"
    msk = now.astimezone(ZoneInfo("Europe/Moscow"))
    if msk.minute % 15 or msk.second >= 60:
        return "WAIT_NEXT_M15_OPEN"
    # Frozen Shallow/OBV signal bars start no later than 17:00 MSK;
    # Inside Day ends earlier. NEXT_OPEN entries are thus 10:15..17:15.
    # Keep broker account/position/SLTP reconciliation ABOVE this guard.
    # Outside the entry window, do not request FINAM M15 bars simply to
    # discover a signal that the frozen rules cannot possibly generate.
    if not ((10, 15) <= (msk.hour, msk.minute) <= (17, 15)):
        return "WAIT_NEXT_M15_OPEN"
    day = OfflinePlanner._session_key(msk.replace(tzinfo=None, second=0, microsecond=0)).isoformat()
    if len(journal.store.get("session_entries", {}).get(day, [])) >= 2:
        return "SESSION_ENTRY_LIMIT_REACHED"
    current_open = {
        row["payload"]["symbol"] for row in _entries(journal)
        if not journal.store.get("flat_cleanup:" + row["idempotency_key"])
    }
    same_session = set()
    for key in journal.store.get("session_entries", {}).get(day, []):
        previous = journal.store.intent(key)
        if previous is None or previous["payload"].get("kind") != "ENTRY":
            raise V20FinamBlocked("V20_LIVE_SESSION_INDEX_CORRUPT")
        same_session.add(previous["payload"]["symbol"])
    boundary_id = msk.replace(tzinfo=None, second=0, microsecond=0).isoformat()
    for symbol in SYMBOLS:
        if (symbol in current_open or symbol in same_session
                or journal.store.get("live_decision:" + symbol) == boundary_id):
            continue
        cost = Decimal(str(sender.auth["roundtrip_cost_rub"][symbol]))
        # FINAM M15 witness must be fresh; an absent/newly delayed Open
        # yields NO ORDER rather than a synthetic or late fill.
        try:
            draft = propose_finam_m15_next_open(
                reader, symbol=symbol, from_utc=now-timedelta(days=20),
                now=now, cost_per_contract=cost,
                broker_ownership=lambda snap: _ownership(journal, snap))
        except V20FinamBlocked as exc:
            if str(exc) in ("M15_NEXT_OPEN_WITNESS_MISSING",
                            "M15_FINAL_COMPLETED_BAR_MISSING"):
                continue
            if str(exc) == "M15_FINAM_TIMESTAMP_OUT_OF_RANGE":
                # A rejected timestamp is NOT a valid frozen NEXT_OPEN witness.
                # Skip the whole attempt (including later symbols, preserving
                # N4 signal priority), without any entry intent or POST.
                # The next polling cycle may retry inside the 60s boundary.
                # Never catch this error in _follow_existing: open positions,
                # protective SLTP and frozen exits stay strictly fail-closed.
                return "M15_TIMESTAMP_UNTRUSTED_NO_ENTRY"
            raise
        except ValueError as exc:
            if str(exc) == "INSUFFICIENT_RISK_OR_MARGIN_CAPACITY":
                journal.store.put("live_decision:" + symbol, boundary_id)
                continue
            raise
        if draft is None:
            journal.store.put("live_decision:" + symbol, boundary_id)
            continue
        signal, candidate, authority, broker = draft
        # Durable decision cursor before creating any irreversible FINAM
        # intention. A crash cannot replay the same frozen NEXT_OPEN.
        journal.store.put("live_decision:" + symbol, boundary_id)
        _ownership(journal, broker)
        key = journal.prepare_entry(
            signal=signal, entry=candidate,
            authority=authority, snapshot=broker)
        sender.submit_entry_once(
            key=key, snapshot=reader.snapshot(now=now), now=now)
        return "ENTRY_ACK_NEEDS_FILL_AND_STOP"
    return "NO_FROZEN_SIGNAL"


def operator_switch(*, root: Path, robot: str, source: str, arm: bool) -> int:
    """Owner-scoped V20-only ARMED/HALTED, never a broker order."""
    if (root.name.casefold() != "v20lab" or not root.is_absolute()
            or robot not in ROBOT_STRATEGIES):
        raise V20FinamBlocked("V20_LIVE_SWITCH_SCOPE_INVALID")
    account = os.environ.get("V20_FINAM_ACCOUNT", "")
    token = os.environ.get("V20_FINAM_TOKEN", "")
    scope = os.environ.get("V20_FINAM_ACCOUNT_SHA256", "")
    if (not re.fullmatch(r"[A-Za-z0-9_.-]{1,128}", account)
            or hashlib.sha256(account.encode()).hexdigest() != scope):
        raise V20FinamBlocked("V20_LIVE_SWITCH_ACCOUNT_INVALID")
    instance = root / "robots" / robot.removeprefix("v20-")
    identity = SimpleNamespace(instance_root=instance, robot_id=robot,
                               account_hash=scope)
    _safe_auth(instance/"safety"/"v20-live-authorization.json",
               journal=identity, source=source)
    if not arm:
        emergency_halt(instance)
        print("v20_08_4_switch=HALTED_" + robot, flush=True)
        return 0
    if not token:
        raise V20FinamBlocked("V20_LIVE_ARM_TOKEN_MISSING")
    switch, error = load_kill_switch(instance)
    if error or switch is None or switch.get("state") != "HALTED":
        raise V20FinamBlocked("V20_LIVE_ARM_REQUIRES_HALTED")
    dbpath = instance / "state" / "v20-real-intents.sqlite3"
    if not dbpath.is_file() or dbpath.is_symlink():
        raise V20FinamBlocked("V20_LIVE_REAL_JOURNAL_REQUIRED")
    with closing(sqlite3.connect(dbpath.as_uri()+"?mode=ro", uri=True)) as db:
        row = db.execute("SELECT value FROM state WHERE key='database_identity'").fetchone()
        expected = {"schema_id": "v20.h1_state_store.real_intents.v1",
                    "robot_id": robot, "strategy": ROBOT_STRATEGIES[robot],
                    "account_sha256": scope, "mode": "V20_PRETRADE_UNAUTHORIZED"}
        if row is None or json.loads(row[0]) != expected:
            raise V20FinamBlocked("V20_LIVE_JOURNAL_IDENTITY_MISMATCH")
        blocked = db.execute("SELECT value FROM state WHERE key='execution_halt'").fetchone()
        if blocked is not None and json.loads(blocked[0]) is not None:
            raise V20FinamBlocked("V20_LIVE_DURABLE_HALT_REQUIRES_RECOVERY")
    reader = V20FinamReadAdapter(
        api=FinamAPI(token), robot_id=robot, account_id=account,
        expected_account_hash=scope)
    reader.authenticate()
    broker = reader.snapshot(now=datetime.now(timezone.utc))
    if not broker.clean:
        raise V20FinamBlocked("V20_LIVE_ARM_REQUIRES_CLEAN_BROKER")
    write_kill_switch(instance, "ARMED", allow_arm=True)
    print("v20_08_4_switch=ARMED_" + robot + "_BROKER_CLEAN", flush=True)
    return 0


def run(*, root: Path, robot: str, source: str, once: bool = False,
        readonly: bool = False) -> int:
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
    if readonly:
        # Separate GET-only health path deliberately does not acquire the
        # live H1 InstanceLock or consult/change its safety switch.
        reader = V20FinamReadAdapter(
            api=FinamAPI(token), robot_id=robot, account_id=account,
            expected_account_hash=scope)
        reader.authenticate()
        snap = reader.snapshot(now=datetime.now(timezone.utc))
        print("v20_08_4_readonly=" + robot + " ACCOUNT_BOUND", flush=True)
        print("v20_08_4_positions=" + str(len(snap.positions)), flush=True)
        print("v20_08_4_active_orders=" + str(sum(o.active for o in snap.orders)),
              flush=True)
        print("v20_08_4_order_posts=zero", flush=True)
        return 0
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
            except Exception as exc:
                # Reuse H1 ProductionService.run(): a failed FINAM cycle
                # records a fault and retries after 3s, never exits its Task.
                # Preserve V20's stronger existing fail-closed switch for
                # non-transient order/stop/ownership and state failures.
                transient = isinstance(exc, (FinamServerError, FinamTimeout, FinamRateLimit, V20FinamSnapshotReadRetry))
                if not transient:
                    # H1 keeps the durable HALT stable; a repeating fault
                    # must not publish a new kill-switch generation every 3s.
                    current, switch_error = load_kill_switch(journal.instance_root)
                    if switch_error or current is None or current["state"] != "HALTED":
                        emergency_halt(journal.instance_root)
                label = str(exc)
                state = label if re.fullmatch(r"[A-Z0-9_]{1,100}", label) else type(exc).__name__
                # A generic H1 FinamError often embeds the account path,
                # so log a useful HTTP code only, without path or identity.
                http_code = re.match(r"^HTTP_([0-9]{3}):", label) if type(exc) is FinamError else None
                if http_code is not None:
                    state = "FINAM_HTTP_" + http_code.group(1)
                event = {"utc": now.isoformat(), "robot": robot,
                         "state": ("FAULT_" if transient else "HALT_") + state}
                detail = getattr(reader, "_m15_timestamp_diagnostic", None)
                if state == "M15_FINAM_TIMESTAMP_OUT_OF_RANGE" and isinstance(detail, dict):
                    event["m15_rejected_bar"] = detail
                with output.open("a", encoding="utf-8") as f:
                    f.write(json.dumps(event, sort_keys=True)+"\n")
                if once:
                    return 1
                time.sleep(FAST_RECONCILIATION_SECONDS)
                continue
            event = {"utc": now.isoformat(), "robot": robot, "state": state}
            if getattr(reader, "_closed_night_flat_no_get", False):
                event["broker_cycle"] = "MOEX_CLOSED_FLAT_NO_FINAM_GET"
            if state == "BROKER_RECONCILED_PROTECTION_PASS":
                event["broker_cycle"] = "MOEX_CLOSED_PROTECTED_120S"
            detail = getattr(reader, "_m15_timestamp_diagnostic", None)
            if state == "M15_TIMESTAMP_UNTRUSTED_NO_ENTRY" and isinstance(detail, dict):
                event["m15_rejected_bar"] = detail
            with output.open("a", encoding="utf-8") as f:
                f.write(json.dumps(event, sort_keys=True)+"\n")
            if once:
                return 0
            time.sleep(FAST_RECONCILIATION_SECONDS if state in (
                "ENTRY_ACK_NEEDS_FILL_AND_STOP", "ENTRY_ACK_AWAIT_BROKER_FILL",
                "STOP_ACK_NEEDS_BROKER_PROOF", "FROZEN_EXIT_ACK_KEEP_STOP_UNTIL_FLAT",
                "EXIT_POSTED_AWAIT_BROKER_FLAT",
                "STOP_CANCEL_WAIT_BROKER_NO_RETRANSMIT") else
                _night_protected_sleep_seconds(datetime.now(timezone.utc))
                if state == "BROKER_RECONCILED_PROTECTION_PASS" else POLL_SECONDS)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--robot", choices=sorted(ROBOT_STRATEGIES), required=True)
    parser.add_argument("--source-commit", required=True)
    parser.add_argument("--once", action="store_true")
    parser.add_argument("--readonly", action="store_true")
    parser.add_argument("--arm", action="store_true")
    parser.add_argument("--halt", action="store_true")
    args = parser.parse_args()
    try:
        if args.arm or args.halt:
            if args.arm and args.halt:
                raise V20FinamBlocked("V20_LIVE_SWITCH_MODE_CONFLICT")
            return operator_switch(root=args.root, robot=args.robot,
                                   source=args.source_commit, arm=args.arm)
        return run(root=args.root, robot=args.robot,
                   source=args.source_commit, once=args.once,
                   readonly=args.readonly)
    except Exception as exc:
        label = str(exc)
        print("v20_08_4_live=HOLD_" + (
            label if re.fullmatch(r"[A-Z0-9_]{1,100}", label)
            else type(exc).__name__), flush=True)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
