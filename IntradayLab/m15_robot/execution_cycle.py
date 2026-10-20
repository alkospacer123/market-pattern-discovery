"""One M15 broker GET-only recovery cycle over the REAL outbound journal.

This is an orchestration step, not another entry strategy or a trading
permission. Existing immutable drafts, order parser, trade reconciliation
and protective ACK rules are reused. No create_session/POST/DELETE/Task/H1
operation can be invoked from this module. A permanent trading worker is
not declared ready until a separate M15 live acceptance.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
from decimal import Decimal
import hashlib
from typing import Any

from .broker_fill_readonly import ExpectedEntry
from .broker_risk_readonly import check_instrument
from .broker_snapshot import (
    order_views, position_quantities, unique_order_by_client_id,
)
from .exchange_contract import contract_from_moex_and_finam
from .finam_readonly import M15FinamReadOnlyAPI, _stamp
from .live_execution import M15OutboundJournal, M15ExecutionError
from .service_clock import M15SingleInstance, _atomic_json


class M15ReadOnlyCycleError(RuntimeError):
    pass


def reconcile_m15_readonly_once(
    *, journal: M15OutboundJournal, api: M15FinamReadOnlyAPI,
    m15_account_id: str, trade_start: str | None = None,
    trade_end: str | None = None, stop_trade_tag: str | None = None,
    limit: int = 1000, observed_at: datetime | None = None,
) -> dict:
    """Reconcile durable M15 ENTRY and 100% SLTP from one broker snapshot.

    PREPARED is NEVER sent; UNCERTAIN is NEVER retried. Only a separately
    proven broker order plus complete trade GET may append real fills, and
    only an independent ACTIVE stop GET may acknowledge protection. Recovery
    is HALTED regardless of all observed results; no new entry authorization.
    """
    if (not isinstance(journal, M15OutboundJournal)
            or type(api) is not M15FinamReadOnlyAPI
            or api.readonly_bound is not True
            or not isinstance(m15_account_id, str)
            or not m15_account_id
            or api.account_id != m15_account_id
            or hashlib.sha256(m15_account_id.encode("utf-8")).hexdigest()
            != journal.account_hash):
        raise M15ReadOnlyCycleError("M15_RECOVERY_EXACT_READONLY_ACCOUNT_REQUIRED")
    if observed_at is not None and (
            not isinstance(observed_at, datetime)
            or observed_at.tzinfo is None or observed_at.utcoffset() is None):
        raise M15ReadOnlyCycleError("M15_RECOVERY_OBSERVATION_TIME_INVALID")
    has_window = (trade_start is not None or trade_end is not None
                  or stop_trade_tag is not None)
    if has_window:
        if (not all(isinstance(x, str) and x for x in
                    (trade_start, trade_end, stop_trade_tag))
                or type(limit) is not int or not 1 <= limit <= 1000
                or ":" in stop_trade_tag or len(stop_trade_tag) > 100):
            raise M15ReadOnlyCycleError("M15_RECOVERY_TRADE_WINDOW_INVALID")
        lower, upper = _stamp(trade_start), _stamp(trade_end)
        if not lower < upper or upper - lower > timedelta(days=30):
            raise M15ReadOnlyCycleError("M15_RECOVERY_TRADE_WINDOW_INVALID")

    # Reopen/revalidate every original draft before inspecting broker state.
    # Unreadable and legacy missing drafts are not silently reconstructed.
    rows = journal.db.execute(
        "SELECT intent_key,kind,symbol,state FROM outbound ORDER BY rowid"
    ).fetchall()
    items = [(key, kind, symbol, state, journal.recover_draft(key))
             for key, kind, symbol, state in rows]
    ids = {draft.payload["client_order_id"] for _, _, _, _, draft in items}
    if len(ids) != len(items):
        raise M15ReadOnlyCycleError("M15_RECOVERY_CLIENT_ID_COLLISION")
    owned_entries = {symbol for _, kind, symbol, _, _ in items if kind == "ENTRY"}

    account = api.account(m15_account_id)
    if (not isinstance(account, dict)
            or account.get("account_id") != m15_account_id
            or account.get("status") not in
            {"ACCOUNT_ACTIVE", "ACCOUNT_STATUS_ACTIVE"}):
        raise M15ReadOnlyCycleError("M15_RECOVERY_ACCOUNT_STATUS_INVALID")
    positions = position_quantities(account)
    orders_response = api.orders(m15_account_id)
    orders = order_views(orders_response)
    # A shadow or live M15 runtime cannot adopt unexplained holdings or
    # active broker orders just because the account ID is correct.
    if any(symbol not in owned_entries for symbol in positions):
        raise M15ReadOnlyCycleError("M15_RECOVERY_FOREIGN_POSITION_HALTED")
    if any(o.active and o.client_order_id not in ids for o in orders):
        raise M15ReadOnlyCycleError("M15_RECOVERY_FOREIGN_ACTIVE_ORDER_HALTED")

    events: list[dict] = []
    for key, kind, symbol, state, draft in items:
        order = unique_order_by_client_id(orders, draft.payload["client_order_id"])
        if order is not None and (
                order.symbol != symbol or order.kind !=
                ("SLTP" if kind in {"PROTECTIVE_STOP_INSTALL",
                                   "PROTECTIVE_STOP_REPLACE"} else "REGULAR")
                or order.side != draft.payload["side"]):
            raise M15ReadOnlyCycleError("M15_RECOVERY_BROKER_ORDER_MISMATCH")
        if kind == "ENTRY":
            if state == "PREPARED":
                if order is not None:
                    raise M15ReadOnlyCycleError(
                        "M15_RECOVERY_PREPARED_ENTRY_ALREADY_AT_BROKER")
                stage = "ENTRY_PREPARED_NOT_SENT"
            elif order is None:
                stage = "ENTRY_UNCERTAIN_NO_REPOST"
            elif not has_window:
                stage = "ENTRY_ORDER_SEEN_FILL_NOT_ASSUMED"
            elif positions.get(symbol, 0) == 0:
                # An entry may have been stopped and closed; stale fill vs
                # current position must not be adopted as an open position.
                stage = "ENTRY_FLAT_REQUIRES_EXIT_PROOF"
            else:
                # Exact broker N4 tick, not a guessed executable price step.
                asset = api.asset_details(symbol)
                params = api.asset_params(symbol)
                contract = contract_from_moex_and_finam(
                    check_instrument(asset, params, symbol, m15_account_id))
                expected = ExpectedEntry(
                    account_id=m15_account_id, order_id=order.order_id,
                    symbol=symbol, side=order.side,
                    quantity=int(draft.payload["quantity"]["value"]),
                    price_step=contract.price_step,
                )
                trades = api.trades(
                    m15_account_id, start=trade_start, end=trade_end,
                    limit=limit)
                report = journal.reconcile_entry_broker_get(
                    key=key, draft=draft, expected=expected,
                    expected_client_order_id=draft.payload["client_order_id"],
                    stop_trade_tag=stop_trade_tag, account=account,
                    orders_response=orders_response,
                    trades_response=trades, start=trade_start,
                    end=trade_end, limit=limit,
                )
                stage = ("ENTRY_BROKER_FILL_RECONCILED_STOP_UNPROVEN"
                         if report["matched_quantity"] > 0
                         else "ENTRY_BROKER_NO_FILL")
        elif kind in {"PROTECTIVE_STOP_INSTALL", "PROTECTIVE_STOP_REPLACE"}:
            if state == "PREPARED":
                if order is not None:
                    raise M15ReadOnlyCycleError(
                        "M15_RECOVERY_PREPARED_STOP_ALREADY_AT_BROKER")
                stage = "STOP_PREPARED_NOT_SENT"
            elif order is None or not order.active:
                stage = "STOP_NOT_ACTIVE_NO_REPOST"
            else:
                proof = journal.reconcile_protective_broker_get(
                    key=key, draft=draft, account=account,
                    orders_response=orders_response,
                )
                if not proof.active or proof.percent != 100:
                    raise M15ReadOnlyCycleError(
                        "M15_RECOVERY_STOP_COVERAGE_UNPROVEN")
                stage = "STOP_BROKER_ACTIVE_100_PERCENT_RECONCILED"
        elif kind == "EMERGENCY_EXIT":
            # Exit/FLAT evidence is confirmed by the existing independent
            # flat-and-stop-cleanup state machine, never by HTTP order ACK.
            stage = "EXIT_FLAT_RECONCILIATION_REQUIRED"
        else:
            raise M15ReadOnlyCycleError("M15_RECOVERY_UNKNOWN_INTENT_KIND")
        # Never print broker IDs, user accounts or raw REST bodies.
        events.append({"kind": kind, "state": stage, "symbol": symbol})

    # Existing H1-derived FLAT/cleanup gate is authoritative. No synthetic
    # zero-position assumption can release a durable entry or its R15.
    # Only ENTRY ACK plus independently stored real fills + exactly one
    # acknowledged protective stop is eligible for flat reconciliation.
    if observed_at is not None:
        for entry_key, kind, symbol, state, _ in items:
            if kind != "ENTRY" or state != "ACK" or positions.get(symbol, 0) != 0:
                continue
            filled = journal.db.execute(
                "SELECT COALESCE(SUM(quantity),0) FROM broker_fills "
                "WHERE intent_key=?", (entry_key,),
            ).fetchone()[0]
            if filled == 0:
                continue
            stopped = [
                (stop_key, stop_kind) for stop_key, stop_kind, stop_symbol,
                stop_state, _ in items
                if stop_kind in {"PROTECTIVE_STOP_INSTALL", "PROTECTIVE_STOP_REPLACE"}
                and stop_symbol == symbol and stop_state == "ACK"
                and journal.db.execute(
                    "SELECT 1 FROM protective_coverage WHERE intent_key=?",
                    (stop_key,),
                ).fetchone() is not None
            ]
            if len(stopped) != 1:
                raise M15ReadOnlyCycleError("M15_RECOVERY_FLAT_STOP_AMBIGUOUS")
            stop_key = stopped[0][0]
            linked_exits = journal.db.execute(
                "SELECT intent_key FROM exit_prepost WHERE entry_key=?",
                (entry_key,),
            ).fetchall()
            if len(linked_exits) > 1:
                raise M15ReadOnlyCycleError("M15_RECOVERY_FLAT_EXIT_AMBIGUOUS")
            exit_key = linked_exits[0][0] if linked_exits else None
            report = journal.observe_flat_broker_get(
                entry_key=entry_key, stop_key=stop_key, exit_key=exit_key,
                account=account, orders_response=orders_response,
                observed_at=observed_at,
            )
            stage = ("FLAT_DURABLY_RECONCILED" if report["durable_closed"]
                     else "FLAT_ACTIVE_SLTP_CLEANUP_REQUIRED")
            events.append({"kind": "FLAT", "state": stage, "symbol": symbol})

    return {
        "status": "HALTED_READONLY_RECOVERY",
        "intent_count": len(items),
        "broker_position_count": len(positions),
        "events": events,
        "new_entries_authorized": False,
        "order_post_permitted": False,
        "stop_coverage_globally_proven": False,
        "live_authorized": False,
    }


def run_m15_readonly_recovery_once(
    *, runtime_root: Path, journal: M15OutboundJournal,
    api: M15FinamReadOnlyAPI, m15_account_id: str,
    observed_at: datetime,
    trade_start: str | None = None, trade_end: str | None = None,
    stop_trade_tag: str | None = None, limit: int = 1000,
) -> dict:
    """One OS-locked recovery poll plus separate, non-authorizing heartbeat.

    The existing native Windows process lock prevents duplicate M15 workers.
    On errors, a FAULT_HALTED heartbeat replaces a stale healthy readout.
    No external authorization, order route, H1 path or Task is touched.
    """
    if (not isinstance(runtime_root, Path)
            or not isinstance(journal, M15OutboundJournal)
            or not isinstance(observed_at, datetime)
            or observed_at.tzinfo is None
            or observed_at.utcoffset() is None):
        raise M15ReadOnlyCycleError("M15_READONLY_CYCLE_ARGUMENT_INVALID")
    root = runtime_root.resolve()
    if (runtime_root.is_symlink()
            or journal.path.parent.parent.resolve() != root):
        raise M15ReadOnlyCycleError("M15_READONLY_CYCLE_RUNTIME_MISMATCH")
    state = root / "state"
    diagnostics = root / "diagnostics"
    if state.is_symlink() or diagnostics.is_symlink():
        raise M15ReadOnlyCycleError("M15_READONLY_CYCLE_SYMLINK_DENIED")
    diagnostics.mkdir(parents=True, exist_ok=True)
    heartbeat = diagnostics / "m15-readonly-execution-recovery.json"
    base = {
        "schema_id": "m15_readonly_execution_recovery.v1",
        "observed_utc": observed_at.astimezone(timezone.utc).isoformat(),
        "live_authorized": False,
        "order_post_permitted": False,
    }
    with M15SingleInstance(state / "m15-outbound-recovery.lock"):
        try:
            result = reconcile_m15_readonly_once(
                journal=journal, api=api, m15_account_id=m15_account_id,
                trade_start=trade_start, trade_end=trade_end,
                stop_trade_tag=stop_trade_tag, limit=limit,
                observed_at=observed_at,
            )
        except Exception:
            # Never serialize a FINAM exception body, account, symbol or token.
            _atomic_json(heartbeat, base | {
                "status": "FAULT_HALTED_NO_TRADING", "intent_count": None,
                "broker_position_count": None,
            })
            raise
        _atomic_json(heartbeat, base | {
            "status": "HALTED_READONLY_RECOVERY",
            "intent_count": result["intent_count"],
            "broker_position_count": result["broker_position_count"],
        })
        return result
