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
            elif positions.get(symbol, 0) == 0:
                # FINAM still lists a live stop after position became FLAT.
                # Existing flat/cleanup authority handles that orphan. Never
                # claim coverage of zero contracts or cancel without approval.
                stage = "STOP_ORPHAN_ACTIVE_AFTER_FLAT"
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

    # Durable 3.5 ATR state is admitted only when current FINAM GET still
    # proves the exact sole active 100% SLTP for the bound M15 position.
    # No candle extremum, stop change or watermark is invented here.
    from .trailing_persistence import verified_broker_trailing_state
    if observed_at is not None:
        for entry_key, kind, symbol, state, _ in items:
            if kind != "ENTRY" or positions.get(symbol, 0) == 0:
                continue
            confirmed = verified_broker_trailing_state(
                journal=journal, entry_key=entry_key,
                account=account, orders_response=orders_response)
            if confirmed is not None:
                events.append({
                    "kind": "TRAIL",
                    "state": "TRAIL_CONFIRMED_BROKER_STOP_UNCHANGED",
                    "symbol": symbol,
                    "last_completed": confirmed.last_survived_m15_close,
                })

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


def prepare_next_verified_m15_trail(
    *, journal: M15OutboundJournal, api: M15FinamReadOnlyAPI,
    m15_account_id: str, entry_key: str, drafts: Any,
    authenticated_seed: Any, interval_start: str, interval_end: str,
    observed_at: datetime, verified_open_labels: bool = False,
) -> dict:
    """FINAM completed M15 -> frozen ATR 3.5 -> durable stop DRAFT or hold.

    This is GET-only for broker IO, never POST/DELETE or an SLTP ACK.
    One adjacent completed bar at a time; a missed completed-bar chain
    cannot be silently compressed into one hindsight trailing decision.
    A new stop stays PREPARED until independently authorized transmission
    and later broker ACTIVE GET. Existing confirmed stop remains unchanged.
    """
    from .trade_draft_contract import M15OfflineTradeDrafts
    from .feature_adapter import (
        M15VerifiedTrailBar, latest_verified_finam_trail_bar,
    )
    from .trailing_persistence import (
        verified_broker_trailing_state, record_verified_trail_hold,
    )
    from .protective_gate import BrokerProtection
    if (not isinstance(journal, M15OutboundJournal)
            or type(api) is not M15FinamReadOnlyAPI
            or api.readonly_bound is not True
            or not isinstance(m15_account_id, str) or not m15_account_id
            or api.account_id != m15_account_id
            or hashlib.sha256(m15_account_id.encode()).hexdigest()
            != journal.account_hash
            or not isinstance(drafts, M15OfflineTradeDrafts)
            or drafts.execution_authorized is not False):
        raise M15ReadOnlyCycleError("M15_TRAIL_NEXT_BAR_ACCOUNT_OR_DRAFT_INVALID")
    entry = journal.inspect(entry_key)
    if entry is None or entry["kind"] != "ENTRY" or entry["state"] != "ACK":
        raise M15ReadOnlyCycleError("M15_TRAIL_NEXT_BAR_ENTRY_NOT_ACK")
    instrument = entry["symbol"].split("@")[0]
    account = api.account(m15_account_id)
    orders_response = api.orders(m15_account_id)
    confirmed = verified_broker_trailing_state(
        journal=journal, entry_key=entry_key,
        account=account, orders_response=orders_response)
    if confirmed is None:
        raise M15ReadOnlyCycleError("M15_TRAIL_NEXT_BAR_INITIAL_STOP_NOT_CONFIRMED")
    bar = latest_verified_finam_trail_bar(
        api=api, m15_account_id=m15_account_id,
        instrument=instrument, authenticated_seed=authenticated_seed,
        observed_at=observed_at, interval_start=interval_start,
        interval_end=interval_end,
        verified_open_labels=verified_open_labels)
    if bar is None:
        return {"state": "TRAIL_NO_FRESH_COMPLETED_BAR", "symbol": entry["symbol"]}
    if type(bar) is not M15VerifiedTrailBar or bar.instrument != instrument:
        raise M15ReadOnlyCycleError("M15_TRAIL_COMPLETED_SOURCE_MISMATCH")
    if bar.observed_at != observed_at:
        raise M15ReadOnlyCycleError("M15_TRAIL_OBSERVATION_CHANGED")
    previous = confirmed.last_survived_m15_close
    if previous is not None:
        at = datetime.fromisoformat(previous)
        if at.tzinfo is None or at.utcoffset() is None:
            raise M15ReadOnlyCycleError("M15_TRAIL_WATERMARK_INVALID")
        if bar.completed_at <= at:
            return {"state": "TRAIL_ALREADY_PROCESSED", "symbol": entry["symbol"]}
        if (bar.previous_completed_at.astimezone(timezone.utc)
                != at.astimezone(timezone.utc)):
            raise M15ReadOnlyCycleError("M15_TRAIL_UNPROCESSED_BAR_GAP")
    else:
        fills = journal.db.execute(
            "SELECT trade_timestamp FROM broker_fills WHERE intent_key=?",
            (entry_key,)).fetchall()
        if not fills:
            raise M15ReadOnlyCycleError("M15_TRAIL_ENTRY_FILLS_MISSING")
        try:
            last_fill = max(datetime.fromisoformat(x[0].replace("Z","+00:00"))
                            for x in fills)
        except (ValueError, TypeError, AttributeError):
            raise M15ReadOnlyCycleError("M15_TRAIL_FILL_TIME_INVALID") from None
        if last_fill.tzinfo is None or last_fill.utcoffset() is None:
            raise M15ReadOnlyCycleError("M15_TRAIL_FILL_TIME_UNBOUND")
        gap = (bar.previous_completed_at.astimezone(timezone.utc)
               - last_fill.astimezone(timezone.utc)).total_seconds()
        if not 0 <= gap <= 30 * 60:
            raise M15ReadOnlyCycleError("M15_TRAIL_FIRST_FULL_BAR_NOT_PROVEN")
    symbol = entry["symbol"]
    asset = api.asset_details(symbol)
    params = api.asset_params(symbol)
    contract = contract_from_moex_and_finam(
        check_instrument(asset, params, symbol, m15_account_id))
    orders = order_views(orders_response)
    active = [o for o in orders if o.kind == "SLTP" and o.active
              and o.symbol == symbol]
    if len(active) != 1:
        raise M15ReadOnlyCycleError("M15_TRAIL_ACTIVE_STOP_NOT_UNIQUE")
    covered = abs(position_quantities(account).get(symbol,0))
    stop = BrokerProtection(
        active[0].order_id, confirmed.active_stop, 100, covered, True)
    stop_key = "m15:trail:" + hashlib.sha256(
        (entry_key + "|" + bar.completed_at.isoformat()).encode()
    ).hexdigest()[:24]
    pending, draft = journal.prepare_trailing_sltp_from_broker(
        drafts=drafts, stop_key=stop_key,
        confirmed=confirmed, broker_stop=stop,
        broker_position_qty=covered,
        completed_at=bar.completed_at, high=bar.high,
        low=bar.low, atr=bar.atr14,
        price_step=contract.price_step, survived_completed_bar=True)
    if draft is None:
        state = record_verified_trail_hold(
            journal=journal, entry_key=entry_key, pending=pending,
            account=account, orders_response=orders_response,
            price_step=contract.price_step)
        return {
            "state": "TRAIL_COMPLETED_HOLD_BROKER_CONFIRMED",
            "symbol": symbol,
            "confirmed_at": state.last_survived_m15_close,
        }
    # No POST and no change to confirmed trailing state; only a
    # deterministic, restart-recoverable PREPARED protective draft.
    return {
        "state": "TRAIL_REPLACE_PREPARED_NO_POST",
        "symbol": symbol,
        "draft_key": stop_key,
        "confirmed_stop_unchanged": str(confirmed.active_stop),
        "candidate_stop": str(pending.candidate.active_stop),
        "order_post_permitted": False,
    }


def run_m15_readonly_recovery_once(
    *, runtime_root: Path, journal: M15OutboundJournal,
    api: M15FinamReadOnlyAPI, m15_account_id: str,
    observed_at: datetime,
    trade_start: str | None = None, trade_end: str | None = None,
    stop_trade_tag: str | None = None, limit: int = 1000,
    trailing_request: dict | None = None,
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
            if trailing_request is not None:
                if not isinstance(trailing_request, dict):
                    raise M15ReadOnlyCycleError("M15_TRAIL_REQUEST_INVALID")
                trailing = prepare_next_verified_m15_trail(
                    journal=journal, api=api,
                    m15_account_id=m15_account_id,
                    observed_at=observed_at, **trailing_request)
                result["events"].append({"kind": "TRAIL", **trailing})
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
