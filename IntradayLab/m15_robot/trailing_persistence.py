"""Persist M15 trailing only after exact active FINAM 100% SLTP confirmation.

Reuses frozen 3.5 ATR propose_trail/confirm_trail; no trading routes or
new strategy. Metadata lives in the existing account-bound journal SQLite.
Only ACTIVE single broker stop after replacement may advance this watermark.
"""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from fractions import Fraction
import hashlib
import json

from .broker_snapshot import order_views, position_quantities
from .grid_risk import TrailingState, require_on_grid
from .live_execution import M15ExecutionError, M15OutboundJournal
from .protective_gate import BrokerProtection
from .trailing_gate import PendingTrail, confirm_trail


class M15TrailPersistenceError(M15ExecutionError):
    pass


def _read(journal: M15OutboundJournal, entry_key: str) -> dict | None:
    row = journal.db.execute(
        "SELECT value FROM metadata WHERE key=?",
        ("trailing-v1:" + entry_key,),
    ).fetchone()
    if row is None:
        return None
    try:
        data = json.loads(row[0])
        if (type(data) is not dict or set(data) != {
                "entry_key", "stop_key", "stop_sha", "qty", "entry",
                "direction", "active_stop", "extreme", "last_completed"}):
            raise ValueError("metadata shape")
        state = TrailingState(
            data["symbol"] if "symbol" in data else "", data["direction"],
            Decimal(data["entry"]), Decimal(data["active_stop"]),
            Decimal(data["extreme"]), data["last_completed"],
        )
    except (TypeError, ValueError, KeyError, ArithmeticError):
        raise M15TrailPersistenceError("M15_TRAIL_DURABLE_STATE_INVALID") from None
    if (data["entry_key"] != entry_key or not isinstance(data["stop_key"], str)
            or not isinstance(data["stop_sha"], str) or len(data["stop_sha"]) != 64
            or type(data["qty"]) is not int or data["qty"] < 1
            or data["direction"] not in {"LONG", "SHORT"}
            or any(not isinstance(x, Decimal) or not x.is_finite() or x <= 0
                   for x in (state.entry, state.active_stop, state.extreme))
            or (data["last_completed"] is not None
                and not isinstance(data["last_completed"], str))):
        raise M15TrailPersistenceError("M15_TRAIL_DURABLE_STATE_INVALID")
    return data


def _state(data: dict, symbol: str) -> TrailingState:
    return TrailingState(symbol.split("@")[0], data["direction"],
                         Decimal(data["entry"]), Decimal(data["active_stop"]),
                         Decimal(data["extreme"]), data["last_completed"])


def verified_broker_trailing_state(
    *, journal: M15OutboundJournal, entry_key: str,
    account: dict, orders_response: dict,
) -> TrailingState | None:
    """After restart: verify persisted stop still active, matching FINAM GET."""
    data = _read(journal, entry_key)
    if data is None:
        return None
    entry = journal.inspect(entry_key)
    if entry is None or entry["kind"] != "ENTRY" or entry["state"] != "ACK":
        raise M15TrailPersistenceError("M15_TRAIL_ENTRY_NOT_ACKNOWLEDGED")
    symbol = entry["symbol"]
    if (not isinstance(account, dict) or not isinstance(account.get("account_id"), str)
            or hashlib.sha256(account["account_id"].encode()).hexdigest()
            != journal.account_hash or account.get("status") not in
            {"ACCOUNT_ACTIVE", "ACCOUNT_STATUS_ACTIVE"}):
        raise M15TrailPersistenceError("M15_TRAIL_ACCOUNT_UNBOUND")
    state = _state(data, symbol)
    qty = position_quantities(account).get(symbol, 0)
    if qty != (data["qty"] if state.direction == "LONG" else -data["qty"]):
        raise M15TrailPersistenceError("M15_TRAIL_POSITION_CHANGED")
    stop = journal.inspect(data["stop_key"])
    coverage = journal.db.execute(
        "SELECT broker_stop_sha256,covered_quantity_at_ack,stop_price "
        "FROM protective_coverage WHERE intent_key=?",
        (data["stop_key"],),
    ).fetchone()
    if (stop is None or stop["state"] != "ACK"
            or stop["symbol"] != symbol
            or stop["broker_order_sha256"] != data["stop_sha"]
            or coverage is None or coverage[0] != data["stop_sha"]
            or coverage[1] != data["qty"]
            or Decimal(coverage[2]) != state.active_stop):
        raise M15TrailPersistenceError("M15_TRAIL_PROTECTIVE_ACK_MISSING")
    active = [o for o in order_views(orders_response) if o.active
              and o.kind == "SLTP" and o.symbol == symbol]
    if len(active) != 1:
        raise M15TrailPersistenceError("M15_TRAIL_UNIQUE_ACTIVE_STOP_UNPROVEN")
    observed = active[0]
    payload = journal.recover_draft(data["stop_key"]).payload
    if (hashlib.sha256(observed.order_id.encode()).hexdigest() != data["stop_sha"]
            or observed.client_order_id != payload["client_order_id"]
            or observed.comment != data["stop_key"]
            or observed.side != payload["side"]
            or observed.request.get("sl_qty_measure") != "SLTP_QTY_MEASURE_PERCENT"
            or Decimal(observed.request["quantity_sl"]["value"]) != 100
            or Decimal(observed.request["sl_price"]["value"]) != state.active_stop):
        raise M15TrailPersistenceError("M15_TRAIL_ACTIVE_BROKER_STOP_CHANGED")
    return state


def record_verified_trailing_state(
    *, journal: M15OutboundJournal, entry_key: str, stop_key: str,
    account: dict, orders_response: dict,
    price_step: Decimal, initial: TrailingState | None = None,
    pending: PendingTrail | None = None,
) -> TrailingState:
    """Persist initial state or a 3.5ATR ratchet after FINAL active broker GET.

    The replacement must already have its separate SLTP ACK, and the old
    broker SLTP must no longer be active; never promote a provisional trail.
    """
    entry = journal.inspect(entry_key)
    stop = journal.inspect(stop_key)
    if (entry is None or entry["kind"] != "ENTRY" or entry["state"] != "ACK"
            or stop is None or stop["kind"] not in
            {"PROTECTIVE_STOP_INSTALL", "PROTECTIVE_STOP_REPLACE"}
            or stop["state"] != "ACK" or stop["symbol"] != entry["symbol"]):
        raise M15TrailPersistenceError("M15_TRAIL_BROKER_ACK_REQUIRED")
    symbol = entry["symbol"]
    signed = position_quantities(account).get(symbol, 0)
    if signed == 0:
        raise M15TrailPersistenceError("M15_TRAIL_NO_OPEN_POSITION")
    q = abs(signed)
    old = _read(journal, entry_key)
    if old is None:
        if (initial is None or pending is not None
                or stop["kind"] != "PROTECTIVE_STOP_INSTALL"
                or initial.instrument + "@RTSX" != symbol
                or initial.direction != ("LONG" if signed > 0 else "SHORT")
                or initial.last_survived_m15_close is not None
                or initial.extreme != initial.entry):
            raise M15TrailPersistenceError("M15_TRAIL_INITIAL_STATE_INVALID")
        fills = journal.db.execute(
            "SELECT quantity,price FROM broker_fills WHERE intent_key=?",
            (entry_key,),
        ).fetchall()
        if sum(x[0] for x in fills) != q or not fills:
            raise M15TrailPersistenceError("M15_TRAIL_INITIAL_FILLS_UNPROVEN")
        weighted = sum((Fraction(price) * qty for qty, price in fills),
                       Fraction(0)) / q
        # Only exact fractional VWAP can be represented as the initial
        # Decimal trailing reference. No guessed/rounded fill is accepted.
        if Fraction(initial.entry) != weighted:
            raise M15TrailPersistenceError("M15_TRAIL_INITIAL_VWAP_UNPROVEN")
        candidate = initial
    else:
        if initial is not None or pending is None or not pending.replace_required:
            raise M15TrailPersistenceError("M15_TRAIL_PENDING_REPLACEMENT_REQUIRED")
        previous = _state(old, symbol)
        if (pending.before != previous
                or hashlib.sha256(pending.broker_stop_id_at_proposal.encode()).hexdigest()
                != old["stop_sha"] or pending.broker_position_qty != old["qty"]
                or stop_key == old["stop_key"]):
            raise M15TrailPersistenceError("M15_TRAIL_PREVIOUS_STATE_CHANGED")
        observed_id = journal.db.execute(
            "SELECT broker_stop_sha256 FROM protective_coverage WHERE intent_key=?",
            (stop_key,),
        ).fetchone()
        if observed_id is None:
            raise M15TrailPersistenceError("M15_TRAIL_NEW_STOP_NOT_ACKNOWLEDGED")
        broker = BrokerProtection(
            broker_order_id=next(
                (o.order_id for o in order_views(orders_response)
                 if hashlib.sha256(o.order_id.encode()).hexdigest() == observed_id[0]),
                ""), stop_price=pending.candidate.active_stop,
            percent=100, covered_quantity_at_ack=q, active=True)
        candidate = confirm_trail(
            pending, observed_stop=broker, observed_stop_count=1,
            broker_position_qty=q, price_step=price_step)
    require_on_grid(candidate.active_stop, price_step)
    if (not candidate.entry.is_finite() or not candidate.extreme.is_finite()
            or candidate.entry <= 0 or candidate.extreme <= 0):
        raise M15TrailPersistenceError("M15_TRAIL_PRICES_INVALID")
    next_data = {
        "entry_key": entry_key, "stop_key": stop_key,
        "stop_sha": stop["broker_order_sha256"], "qty": q,
        "entry": str(candidate.entry), "direction": candidate.direction,
        "active_stop": str(candidate.active_stop),
        "extreme": str(candidate.extreme),
        "last_completed": candidate.last_survived_m15_close,
    }
    key = "trailing-v1:" + entry_key
    journal.db.execute("BEGIN IMMEDIATE")
    try:
        current = _read(journal, entry_key)
        if current != old:
            raise M15TrailPersistenceError("M15_TRAIL_CONCURRENT_STATE_CHANGED")
        if old is not None and (candidate.active_stop <
                                Decimal(old["active_stop"])
                                if candidate.direction == "LONG" else
                                candidate.active_stop >
                                Decimal(old["active_stop"])):
            raise M15TrailPersistenceError("M15_TRAIL_STOP_WIDENING")
        journal.db.execute(
            "INSERT INTO metadata(key,value) VALUES(?,?) "
            "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
            (key, json.dumps(next_data, sort_keys=True, separators=(",", ":"))),
        )
        # Validation uses the persisted stop/coverage and exact broker GET,
        # inside this transaction. Any missing broker proof rolls back.
        verified = verified_broker_trailing_state(
            journal=journal, entry_key=entry_key, account=account,
            orders_response=orders_response)
        if verified != candidate:
            raise M15TrailPersistenceError("M15_TRAIL_DURABLE_VERIFY_MISMATCH")
        journal.db.execute("COMMIT")
    except Exception:
        if journal.db.in_transaction:
            journal.db.execute("ROLLBACK")
        raise
    return candidate


def record_verified_trail_hold(
    *, journal: M15OutboundJournal, entry_key: str,
    pending: PendingTrail, account: dict, orders_response: dict,
    price_step: Decimal,
) -> TrailingState:
    """Advance survived-candle extrema/watermark if broker STOP needs no change.

    Reuses already broker-confirmed ACTIVE 100% SLTP, never submits an order.
    No watermark is advanced until current FINAM GET proves the old stop is
    still the sole active protection with exact covered contracts.
    """
    if not isinstance(pending, PendingTrail) or pending.replace_required:
        raise M15TrailPersistenceError("M15_TRAIL_HOLD_PROPOSAL_REQUIRED")
    old = _read(journal, entry_key)
    confirmed = verified_broker_trailing_state(
        journal=journal, entry_key=entry_key,
        account=account, orders_response=orders_response,
    )
    if (old is None or confirmed is None or pending.before != confirmed
            or pending.broker_position_qty != old["qty"]
            or hashlib.sha256(pending.broker_stop_id_at_proposal.encode()).hexdigest()
            != old["stop_sha"]):
        raise M15TrailPersistenceError("M15_TRAIL_HOLD_BROKER_STATE_MISMATCH")
    stop = next((x for x in order_views(orders_response)
                 if x.active and x.kind == "SLTP"
                 and hashlib.sha256(x.order_id.encode()).hexdigest() == old["stop_sha"]),
                None)
    if stop is None:
        raise M15TrailPersistenceError("M15_TRAIL_HOLD_ACTIVE_STOP_MISSING")
    proof = BrokerProtection(stop.order_id, confirmed.active_stop, 100, old["qty"], True)
    candidate = confirm_trail(
        pending, observed_stop=proof, observed_stop_count=1,
        broker_position_qty=old["qty"], price_step=price_step)
    if (candidate.active_stop != confirmed.active_stop
            or candidate.last_survived_m15_close == confirmed.last_survived_m15_close):
        raise M15TrailPersistenceError("M15_TRAIL_HOLD_BAR_NOT_ADVANCED")
    changed = dict(old)
    changed["extreme"] = str(candidate.extreme)
    changed["last_completed"] = candidate.last_survived_m15_close
    key = "trailing-v1:" + entry_key
    journal.db.execute("BEGIN IMMEDIATE")
    try:
        if _read(journal, entry_key) != old:
            raise M15TrailPersistenceError("M15_TRAIL_HOLD_STATE_CONFLICT")
        journal.db.execute(
            "UPDATE metadata SET value=? WHERE key=?",
            (json.dumps(changed,sort_keys=True,separators=(",", ":")),key),
        )
        verified = verified_broker_trailing_state(
            journal=journal, entry_key=entry_key,
            account=account, orders_response=orders_response)
        if verified != candidate:
            raise M15TrailPersistenceError("M15_TRAIL_HOLD_VERIFY_FAILED")
        journal.db.execute("COMMIT")
    except Exception:
        if journal.db.in_transaction:
            journal.db.execute("ROLLBACK")
        raise
    return candidate
