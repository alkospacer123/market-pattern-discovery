"""Authorized Stage 8.12.4 continuous FINAM production service.

The service is deliberately separate from the historical runner.py LIVE air-gap.
It can exist only behind the exact repository-external Stage 8.12.4 durable
authorization.  Broker position is synchronous fill authority; order/trade
state is never used to invent fills.  Risk-reducing stop/emergency handling is
performed before any new entry.
"""
from __future__ import annotations

import argparse
import hashlib
import os
import re
import time
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, Callable

import pandas as pd

from .account_cleanliness import TERMINAL_ORDER_STATUSES
from .broker import compact_client_order_id
from .finam_api import (
    FinamAPI,
    FinamError,
    FinamOrderRejected,
    FinamUncertainSubmission,
)
from .funding_margin_diagnostic import ACTIVE_ACCOUNT_STATUSES
from .instrument_resolver import (
    N4,
    discover_finam_asset,
    validate_finam_binding,
)
from .live_execution import AuthorizedFinamProductionTransport
from .margin import (
    directional_initial_margin,
    parse_rest_decimal_value_object,
    portfolio_authority,
)
from .operations import InstanceLock, configure_operational_log
from .production_broker_state import (
    BrokerOrderView,
    ProductionBrokerStateError,
    active_sltp_for_trade,
    order_views,
    position_quantities,
    unique_order_by_client_id,
)
from .production_h1_cache import (
    ProductionH1Cache,
    ProductionH1CacheError,
    initialize_cache,
)
from .production_history import (
    ProductionHistoryError,
    close_index_for_frozen_t3,
    finam_completed_open_h1,
)
from .production_runtime import (
    InstrumentAuthority,
    ProductionRuntime,
    ProductionRuntimeError,
    RuntimeAction,
)
from .production_safety_gate import (
    evaluate_production_entry_gate,
    write_production_heartbeat,
)
from .readonly_supervisor import newest_expected_h1_close, trading_h1_windows
from .specification import (
    ACTIVE_IDENTITY,
    INSTRUMENTS,
    PRODUCTION_SPECIFICATION_ID,
    load_frozen_specification,
)
from .strategy_core import CompletedBar
from .trading_safety_gate import emergency_halt

MODE = "REAL_PRODUCTION_FULL_R15"
PRODUCTION_STATE_FILENAME = "stage8-12-production.sqlite3"
LOCK_FILENAME = "stage8-production.lock"
POLL_MIN_SECONDS = 30
POLL_MAX_SECONDS = 3600
DEFAULT_POLL_SECONDS = 300
DEFAULT_MAX_FAILURES = 1
POSITION_RECONCILIATION_OBSERVATIONS = 30
ORDER_RECONCILIATION_OBSERVATIONS = 30
RECONCILIATION_SLEEP_SECONDS = 2.0
H1_LOOKBACK_DAYS = 30
_COMMIT = re.compile(r"^[0-9a-f]{40}$")
_ORDER_FAILURE = frozenset({
    "REJECTED",
    "FAILED",
    "DENIED_BY_BROKER",
    "REJECTED_BY_EXCHANGE",
})
_ORDER_CANCEL = frozenset({"CANCELLED", "EXPIRED"})
_ORDER_FILLED = frozenset({"FILLED", "EXECUTED", "SL_EXECUTED", "TP_EXECUTED"})


class ProductionServiceFault(RuntimeError):
    """Audit-safe failure code that may be emitted to logs/heartbeat."""


@dataclass(frozen=True)
class BrokerSnapshot:
    account: dict[str, Any]
    positions: dict[str, int]
    orders: list[BrokerOrderView]
    realized_basis: Decimal
    available_cash: Decimal


def _runtime_action(intent: dict[str, Any]) -> RuntimeAction:
    payload = intent.get("payload")
    if not isinstance(payload, dict):
        raise ProductionServiceFault("PRODUCTION_INTENT_PAYLOAD_INVALID")
    try:
        return RuntimeAction(
            payload["kind"],
            payload.get("idempotency_key"),
            payload["instrument"],
            payload["finam_symbol"],
            payload.get("direction"),
            int(payload.get("quantity", 0)),
            payload.get("trade_id"),
            payload.get("signal_id"),
            (
                Decimal(str(payload["reference_price"]))
                if payload.get("reference_price") is not None
                else None
            ),
            (
                Decimal(str(payload["stop_price"]))
                if payload.get("stop_price") is not None
                else None
            ),
            payload.get("expected_position_quantity"),
            payload.get("reason"),
        )
    except (KeyError, TypeError, ValueError, InvalidOperation):
        raise ProductionServiceFault("PRODUCTION_INTENT_PAYLOAD_INVALID") from None


def _broker_order_id(response: Any) -> str | None:
    if not isinstance(response, dict):
        return None
    value = response.get("order_id") or response.get("orderId")
    return str(value) if isinstance(value, str) and value else None


def _entry_session_open(schedule: Any, observed_at: datetime) -> bool:
    now = observed_at.astimezone(timezone.utc)
    try:
        windows = trading_h1_windows(schedule)
    except Exception:
        raise ProductionServiceFault("PRODUCTION_ENTRY_SCHEDULE_INVALID") from None
    return any(start <= now < end for start, end in windows)


class ProductionService:
    def __init__(
        self,
        *,
        runtime_root: Path | str,
        data_root: Path | str,
        accepted_commit: str,
        api: Any,
        account_id: str,
        poll_seconds: int = DEFAULT_POLL_SECONDS,
        clock: Callable[[], datetime] | None = None,
        sleeper: Callable[[float], None] = time.sleep,
    ):
        commit = str(accepted_commit).strip().lower()
        if not _COMMIT.fullmatch(commit):
            raise ProductionServiceFault("PRODUCTION_ACCEPTED_COMMIT_INVALID")
        if not account_id:
            raise ProductionServiceFault("PRODUCTION_ACCOUNT_REQUIRED")
        if not POLL_MIN_SECONDS <= poll_seconds <= POLL_MAX_SECONDS:
            raise ProductionServiceFault("PRODUCTION_POLL_SECONDS_INVALID")

        self.root = Path(runtime_root)
        self.data_root = Path(data_root)
        self.accepted_commit = commit
        self.api = api
        self.account_id = str(account_id)
        self.account_hash = hashlib.sha256(self.account_id.encode("utf-8")).hexdigest()
        self.poll_seconds = poll_seconds
        self.clock = clock or (lambda: datetime.now(timezone.utc))
        self.sleeper = sleeper
        for name in ("state", "audit", "logs", "diagnostics", "backups", "safety"):
            (self.root / name).mkdir(parents=True, exist_ok=True)

        # Constructor itself is authorization-gated before any live transport is
        # usable. Cache/state are external durable authorities, not Git outputs.
        self.transport = AuthorizedFinamProductionTransport(
            api=self.api,
            account_id=self.account_id,
            runtime_root=self.root,
            accepted_commit=self.accepted_commit,
        )
        initialize_cache(self.root, self.data_root)
        self.cache = ProductionH1Cache(self.root)
        self.runtime = ProductionRuntime(
            self.root / "state" / PRODUCTION_STATE_FILENAME
        )
        self.logger = configure_operational_log(
            self.root / "logs" / "stage8-production.log"
        )
        self.cycle_count = 0
        self.consecutive_failures = 0
        self.last_position_protection: list[dict[str, Any]] = []
        self.last_api_contact = self.clock().astimezone(timezone.utc)
        self.startup_pending_cleanup_complete = False
        self.transport.connect()

    def close(self) -> None:
        try:
            self.runtime.close()
        finally:
            self.cache.close()
            for handler in self.logger.handlers:
                handler.flush()
                handler.close()
            self.logger.handlers.clear()

    def _session_safe(self) -> None:
        details = self.api.session_details()
        ids = details.get("account_ids") if isinstance(details, dict) else None
        if (
            not isinstance(ids, list)
            or [str(value) for value in ids].count(self.account_id) != 1
        ):
            raise ProductionServiceFault("PRODUCTION_ACCOUNT_NOT_EXACTLY_ENUMERATED")
        if details.get("readonly") is not False:
            raise ProductionServiceFault("PRODUCTION_TRADING_TOKEN_NOT_WRITE_CAPABLE")

    def _realized_basis(self, account: dict[str, Any]) -> Decimal:
        try:
            equity = parse_rest_decimal_value_object(
                account.get("equity"), positive=True
            )
            unrealized = parse_rest_decimal_value_object(
                account.get("unrealized_profit")
            )
            explained = Decimal(
                str(self.runtime.store.get("explained_external_cash_flows", "0"))
            )
        except (ValueError, InvalidOperation):
            raise ProductionServiceFault("PRODUCTION_REALIZED_EQUITY_AUTHORITY_INVALID") from None
        basis = equity - unrealized - explained
        if not basis.is_finite() or basis <= 0:
            raise ProductionServiceFault("PRODUCTION_REALIZED_EQUITY_AUTHORITY_INVALID")
        return basis

    def _snapshot(self) -> BrokerSnapshot:
        self._session_safe()
        account = self.api.account(self.account_id)
        self.last_api_contact = self.clock().astimezone(timezone.utc)
        if (
            not isinstance(account, dict)
            or account.get("status") not in ACTIVE_ACCOUNT_STATUSES
        ):
            raise ProductionServiceFault("PRODUCTION_REAL_ACCOUNT_NOT_ACTIVE")
        try:
            positions = position_quantities(account)
            orders = order_views(self.api.orders(self.account_id))
            available = portfolio_authority(account).available_cash
        except (ProductionBrokerStateError, ValueError) as exc:
            raise ProductionServiceFault(str(exc)) from None
        if available < 0:
            raise ProductionServiceFault("PRODUCTION_AVAILABLE_CASH_INVALID")
        return BrokerSnapshot(
            account=account,
            positions=positions,
            orders=orders,
            realized_basis=self._realized_basis(account),
            available_cash=available,
        )

    def _instrument_data(
        self, now: datetime
    ) -> tuple[
        dict[str, InstrumentAuthority],
        dict[str, pd.DataFrame],
        dict[str, Any],
    ]:
        assets = self.api.assets_all_active()
        if not isinstance(assets, list):
            raise ProductionServiceFault("PRODUCTION_ACTIVE_ASSET_CATALOG_INVALID")
        authorities: dict[str, InstrumentAuthority] = {}
        histories: dict[str, pd.DataFrame] = {}
        schedules: dict[str, Any] = {}
        start = (now.astimezone(timezone.utc) - timedelta(days=H1_LOOKBACK_DAYS)).isoformat()
        end = now.astimezone(timezone.utc).isoformat()

        for instrument in INSTRUMENTS:
            frozen = self.runtime.registry[instrument]
            asset, reason = discover_finam_asset(instrument, assets)
            if reason or not isinstance(asset, dict):
                raise ProductionServiceFault("PRODUCTION_N4_BINDING_INVALID")
            symbol = asset.get("symbol")
            if not isinstance(symbol, str):
                raise ProductionServiceFault("PRODUCTION_N4_BINDING_INVALID")
            params = self.api.asset_params(symbol, self.account_id)
            schedule = self.api.schedule(symbol)
            schedules[instrument] = schedule
            binding = validate_finam_binding(
                instrument,
                asset,
                params,
                schedule,
                self.api.asset(symbol, self.account_id),
            ).to_dict()
            if (
                not str(binding.get("status", "")).startswith("AUTHENTICATED_")
                or binding.get("is_tradable") is not True
                or binding.get("finam_symbol") != frozen["finam_symbol"]
                or binding.get("mic") != frozen["mic"]
                or str(binding.get("security_id")) != frozen["security_id"]
                or str(binding.get("trade_lot_size"))
                != frozen["quantity_granularity"]
            ):
                raise ProductionServiceFault("PRODUCTION_N4_BINDING_INVALID")
            try:
                authority = InstrumentAuthority(
                    instrument=instrument,
                    finam_symbol=frozen["finam_symbol"],
                    price_step=Decimal(frozen["price_step"]),
                    tick_value=Decimal(frozen["tick_value"]),
                    trade_lot_size=int(frozen["quantity_granularity"]),
                    long_initial_margin=directional_initial_margin(params, "LONG"),
                    short_initial_margin=directional_initial_margin(params, "SHORT"),
                )
            except (KeyError, ValueError, InvalidOperation):
                raise ProductionServiceFault("PRODUCTION_N4_MARGIN_AUTHORITY_INVALID") from None
            authorities[instrument] = authority

            try:
                windows = trading_h1_windows(schedule)
                response = self.api.bars(symbol, start, end)
                live = finam_completed_open_h1(response, now, windows)
                expected = newest_expected_h1_close(schedule, now)
            except Exception as exc:
                code = str(exc)
                if not code.startswith("STAGE8_12_4_"):
                    code = "PRODUCTION_H1_AUTHORITY_INVALID"
                raise ProductionServiceFault(code) from None

            if expected is not None:
                expected_open = pd.Timestamp(expected).tz_convert("Europe/Moscow")
                if expected_open not in live.index:
                    raise ProductionServiceFault("PRODUCTION_STALE_COMPLETED_H1_DATA")
            try:
                self.cache.merge_finam(instrument, live)
                histories[instrument] = close_index_for_frozen_t3(
                    self.cache.frame(instrument)
                )
            except (ProductionH1CacheError, ProductionHistoryError) as exc:
                raise ProductionServiceFault(str(exc)) from None

        return authorities, histories, schedules

    def _activation_initialize(
        self,
        snapshot: BrokerSnapshot,
        histories: dict[str, pd.DataFrame],
    ) -> None:
        existing = self.runtime.store.get("production_activation_watermarks")
        if existing is not None:
            if existing.get("accepted_commit") != self.accepted_commit:
                raise ProductionServiceFault("PRODUCTION_ACTIVATION_COMMIT_MISMATCH")
            return
        if (
            self.runtime.open_positions()
            or self.runtime.store.unresolved_intent_count() != 0
            or snapshot.positions
            or any(order.active for order in snapshot.orders)
        ):
            raise ProductionServiceFault("PRODUCTION_INITIAL_ACTIVATION_ACCOUNT_NOT_CLEAN")
        current = self.runtime.current_realized_equity()
        if current is None:
            self.runtime.set_realized_equity(snapshot.realized_basis)
        elif current != snapshot.realized_basis:
            raise ProductionServiceFault("UNEXPLAINED_REALIZED_EQUITY_DISCREPANCY")
        watermarks = {
            instrument: histories[instrument].index[-1]
            for instrument in INSTRUMENTS
        }
        self.runtime.initialize_activation_watermarks(
            watermarks, accepted_commit=self.accepted_commit
        )

    def _action_order(
        self, snapshot: BrokerSnapshot, action: RuntimeAction
    ) -> BrokerOrderView | None:
        if not action.idempotency_key:
            return None
        return unique_order_by_client_id(
            snapshot.orders, compact_client_order_id(action.idempotency_key)
        )

    def _wait_for_position(
        self, action: RuntimeAction
    ) -> BrokerSnapshot:
        last = self._snapshot()
        expected = action.expected_position_quantity
        for index in range(POSITION_RECONCILIATION_OBSERVATIONS):
            quantity = last.positions.get(action.finam_symbol, 0)
            if quantity == expected:
                return last
            if quantity not in {0, expected}:
                raise ProductionServiceFault(
                    "PRODUCTION_POSITION_AUTHORITY_UNEXPECTED_QUANTITY"
                )
            if index + 1 < POSITION_RECONCILIATION_OBSERVATIONS:
                self.sleeper(RECONCILIATION_SLEEP_SECONDS)
                last = self._snapshot()
        return last

    def _wait_for_flat(self, action: RuntimeAction) -> BrokerSnapshot:
        last = self._snapshot()
        for index in range(POSITION_RECONCILIATION_OBSERVATIONS):
            quantity = last.positions.get(action.finam_symbol, 0)
            if quantity == 0:
                return last
            expected = (
                action.quantity
                if action.direction == "LONG"
                else -action.quantity
            )
            if quantity != expected:
                raise ProductionServiceFault(
                    "PRODUCTION_POSITION_AUTHORITY_UNEXPECTED_QUANTITY"
                )
            if index + 1 < POSITION_RECONCILIATION_OBSERVATIONS:
                self.sleeper(RECONCILIATION_SLEEP_SECONDS)
                last = self._snapshot()
        return last

    def _proven_active_stop(
        self, snapshot: BrokerSnapshot, action: RuntimeAction
    ) -> BrokerOrderView | None:
        if not action.trade_id or not action.idempotency_key:
            raise ProductionServiceFault("PROTECTIVE_STOP_IDENTITY_INVALID")
        owned = active_sltp_for_trade(
            snapshot.orders,
            trade_id=action.trade_id,
            symbol=action.finam_symbol,
        )
        client_id = compact_client_order_id(action.idempotency_key)
        matches = [
            order
            for order in owned
            if order.client_order_id == client_id
            and order.comment == action.idempotency_key
        ]
        if len(matches) > 1:
            raise ProductionServiceFault(
                "PRODUCTION_DUPLICATE_ACTIVE_PROTECTIVE_STOP_IDENTITY"
            )
        return matches[0] if matches else None

    def _wait_for_stop(
        self, action: RuntimeAction
    ) -> tuple[BrokerSnapshot, BrokerOrderView | None]:
        last = self._snapshot()
        for index in range(ORDER_RECONCILIATION_OBSERVATIONS):
            view = self._proven_active_stop(last, action)
            if view is not None:
                return last, view
            terminal = self._action_order(last, action)
            if terminal is not None and not terminal.active:
                return last, terminal
            if index + 1 < ORDER_RECONCILIATION_OBSERVATIONS:
                self.sleeper(RECONCILIATION_SLEEP_SECONDS)
                last = self._snapshot()
        return last, None

    def _terminalize_failed_order(
        self, intent: dict[str, Any], order: BrokerOrderView
    ) -> bool:
        key = intent["idempotency_key"]
        if order.status in _ORDER_FAILURE:
            self.runtime.store.transition_intent(key, "REJECTED", order.order_id)
            return True
        if order.status in _ORDER_CANCEL:
            self.runtime.store.transition_intent(key, "CANCELLED", order.order_id)
            return True
        return False

    def _submit_stop(
        self, action: RuntimeAction, observed_quantity: int
    ) -> bool:
        if not action.idempotency_key:
            raise ProductionServiceFault("PROTECTIVE_STOP_KEY_MISSING")
        intent = self.runtime.store.intent(action.idempotency_key)
        if intent is None:
            raise ProductionServiceFault("PROTECTIVE_STOP_INTENT_NOT_FOUND")
        if intent["status"] == "INTENT_PERSISTED":
            self.runtime.store.transition_intent(action.idempotency_key, "SUBMITTED")
            try:
                response = self.transport.submit_protective_stop(
                    action,
                    observed_position_quantity=observed_quantity,
                )
            except FinamOrderRejected:
                self.runtime.reject_protective_stop(action.idempotency_key)
                return False
            except FinamUncertainSubmission:
                self.runtime.store.transition_intent(
                    action.idempotency_key, "UNCERTAIN"
                )
            else:
                self.runtime.store.transition_intent(
                    action.idempotency_key,
                    "ACK",
                    _broker_order_id(response),
                )

        snapshot, view = self._wait_for_stop(action)
        if view is not None and view.active:
            self.runtime.confirm_protective_stop(
                action.idempotency_key, view.order_id
            )
            return True
        if view is not None and self._terminalize_failed_order(
            self.runtime.store.intent(action.idempotency_key), view
        ):
            self.runtime.reject_protective_stop(action.idempotency_key)
            return False
        return False

    def _submit_emergency_exit(
        self, action: RuntimeAction, observed_quantity: int
    ) -> BrokerSnapshot:
        if not action.idempotency_key:
            raise ProductionServiceFault("EMERGENCY_EXIT_KEY_MISSING")
        intent = self.runtime.store.intent(action.idempotency_key)
        if intent is None:
            raise ProductionServiceFault("EMERGENCY_EXIT_INTENT_NOT_FOUND")
        if observed_quantity == 0:
            if intent["status"] != "RECONCILED":
                self.runtime.store.transition_intent(
                    action.idempotency_key, "FILL", intent.get("broker_order_id")
                )
                self.runtime.store.transition_intent(
                    action.idempotency_key,
                    "RECONCILED",
                    intent.get("broker_order_id"),
                )
            return self._snapshot()

        if intent["status"] == "INTENT_PERSISTED":
            self.runtime.store.transition_intent(action.idempotency_key, "SUBMITTED")
            try:
                response = self.transport.submit_emergency_exit(
                    action, observed_position_quantity=observed_quantity
                )
            except FinamOrderRejected:
                self.runtime.store.transition_intent(
                    action.idempotency_key, "REJECTED"
                )
                raise ProductionServiceFault(
                    "PRODUCTION_EMERGENCY_EXIT_REJECTED"
                ) from None
            except FinamUncertainSubmission:
                self.runtime.store.transition_intent(
                    action.idempotency_key, "UNCERTAIN"
                )
            else:
                self.runtime.store.transition_intent(
                    action.idempotency_key,
                    "ACK",
                    _broker_order_id(response),
                )

        snapshot = self._wait_for_flat(action)
        if snapshot.positions.get(action.finam_symbol, 0) != 0:
            raise ProductionServiceFault(
                "PRODUCTION_EMERGENCY_EXIT_RECONCILIATION_TIMEOUT"
            )
        current = self.runtime.store.intent(action.idempotency_key)
        if current and current["status"] != "RECONCILED":
            self.runtime.store.transition_intent(
                action.idempotency_key,
                "FILL",
                current.get("broker_order_id"),
            )
            self.runtime.store.transition_intent(
                action.idempotency_key,
                "RECONCILED",
                current.get("broker_order_id"),
            )
        return snapshot

    def _ensure_stop_or_exit(
        self, action: RuntimeAction, snapshot: BrokerSnapshot
    ) -> BrokerSnapshot:
        quantity = snapshot.positions.get(action.finam_symbol, 0)
        expected = (
            action.quantity if action.direction == "LONG" else -action.quantity
        )
        if quantity == 0:
            return snapshot
        if quantity != expected:
            raise ProductionServiceFault(
                "PRODUCTION_POSITION_AUTHORITY_UNEXPECTED_QUANTITY"
            )
        if self._submit_stop(action, quantity):
            return self._snapshot()

        refreshed = self._snapshot()
        quantity = refreshed.positions.get(action.finam_symbol, 0)
        if quantity == 0:
            return refreshed

        active_backstops = active_sltp_for_trade(
            refreshed.orders,
            trade_id=action.trade_id,
            symbol=action.finam_symbol,
        )
        if action.kind == "PROTECTIVE_STOP_REPLACE" and active_backstops:
            # A rejected tighter replacement may safely fall back to the older
            # 100%-current-position stop. An unresolved uncertain replacement,
            # however, keeps new entries halted until reconciled.
            intent = self.runtime.store.intent(action.idempotency_key)
            if intent and intent["status"] == "REJECTED":
                return refreshed
            raise ProductionServiceFault(
                "PRODUCTION_REPLACEMENT_STOP_RECONCILIATION_REQUIRED"
            )

        emergency = self.runtime.require_emergency_exit(
            action.instrument,
            reason="PROTECTIVE_STOP_UNPROVEN",
        )
        return self._submit_emergency_exit(emergency, quantity)

    def _reconcile_entry_intent(
        self, intent: dict[str, Any], snapshot: BrokerSnapshot
    ) -> BrokerSnapshot:
        action = _runtime_action(intent)
        quantity = snapshot.positions.get(action.finam_symbol, 0)
        expected = action.expected_position_quantity
        if quantity == expected:
            stop = self.runtime.confirm_entry_position(
                intent["idempotency_key"], quantity
            )
            refreshed = self._snapshot()
            if stop is not None:
                return self._ensure_stop_or_exit(stop, refreshed)
            return refreshed
        if quantity not in {0, expected}:
            raise ProductionServiceFault(
                "PRODUCTION_POSITION_AUTHORITY_UNEXPECTED_QUANTITY"
            )

        if intent["status"] == "INTENT_PERSISTED":
            # Persist-before-submit proves this stale startup intent was never
            # POSTed. Never transmit a historical entry on restart.
            self.runtime.store.transition_intent(
                intent["idempotency_key"], "CANCELLED"
            )
            return snapshot

        converged = self._wait_for_position(action)
        quantity = converged.positions.get(action.finam_symbol, 0)
        if quantity == expected:
            stop = self.runtime.confirm_entry_position(
                intent["idempotency_key"], quantity
            )
            refreshed = self._snapshot()
            if stop is not None:
                return self._ensure_stop_or_exit(stop, refreshed)
            return refreshed

        view = self._action_order(converged, action)
        if view is not None and self._terminalize_failed_order(intent, view):
            return converged
        raise ProductionServiceFault(
            "PRODUCTION_ENTRY_RECONCILIATION_REQUIRED"
        )

    def _reconcile_stop_intent(
        self, intent: dict[str, Any], snapshot: BrokerSnapshot
    ) -> BrokerSnapshot:
        action = _runtime_action(intent)
        quantity = snapshot.positions.get(action.finam_symbol, 0)
        if quantity == 0:
            view = self._action_order(snapshot, action)
            if view is not None and self._terminalize_failed_order(intent, view):
                return snapshot
            if intent["status"] == "INTENT_PERSISTED":
                self.runtime.store.transition_intent(
                    intent["idempotency_key"], "CANCELLED"
                )
                return snapshot
            raise ProductionServiceFault(
                "PRODUCTION_FLAT_STOP_INTENT_RECONCILIATION_REQUIRED"
            )
        expected = (
            action.quantity if action.direction == "LONG" else -action.quantity
        )
        if quantity != expected:
            raise ProductionServiceFault(
                "PRODUCTION_POSITION_AUTHORITY_UNEXPECTED_QUANTITY"
            )

        active_view = self._proven_active_stop(snapshot, action)
        if active_view is not None:
            self.runtime.confirm_protective_stop(
                action.idempotency_key, active_view.order_id
            )
            return snapshot
        view = self._action_order(snapshot, action)
        if view is not None and self._terminalize_failed_order(intent, view):
            self.runtime.reject_protective_stop(action.idempotency_key)
            if action.kind == "PROTECTIVE_STOP_INSTALL":
                emergency = self.runtime.require_emergency_exit(
                    action.instrument,
                    reason="INITIAL_PROTECTIVE_STOP_REJECTED",
                )
                return self._submit_emergency_exit(emergency, quantity)
            return snapshot
        return self._ensure_stop_or_exit(action, snapshot)

    def _reconcile_emergency_intent(
        self, intent: dict[str, Any], snapshot: BrokerSnapshot
    ) -> BrokerSnapshot:
        action = _runtime_action(intent)
        quantity = snapshot.positions.get(action.finam_symbol, 0)
        return self._submit_emergency_exit(action, quantity)

    def _reconcile_unresolved(
        self, snapshot: BrokerSnapshot
    ) -> BrokerSnapshot:
        for _ in range(16):
            unresolved = self.runtime.store.unresolved_intents()
            if not unresolved:
                return snapshot
            prior = [
                (row["idempotency_key"], row["status"])
                for row in unresolved
            ]
            for intent in unresolved:
                kind = intent["payload"].get("kind")
                if kind == "ENTRY":
                    snapshot = self._reconcile_entry_intent(intent, snapshot)
                elif kind in {
                    "PROTECTIVE_STOP_INSTALL",
                    "PROTECTIVE_STOP_REPLACE",
                }:
                    snapshot = self._reconcile_stop_intent(intent, snapshot)
                elif kind == "EMERGENCY_EXIT_REQUIRED":
                    snapshot = self._reconcile_emergency_intent(intent, snapshot)
                else:
                    raise ProductionServiceFault(
                        "PRODUCTION_UNRESOLVED_INTENT_KIND_INVALID"
                    )
            current = [
                (row["idempotency_key"], row["status"])
                for row in self.runtime.store.unresolved_intents()
            ]
            if current == prior:
                raise ProductionServiceFault(
                    "PRODUCTION_UNRESOLVED_INTENT_RECONCILIATION_STALLED"
                )
            snapshot = self._snapshot()
        raise ProductionServiceFault(
            "PRODUCTION_UNRESOLVED_INTENT_RECONCILIATION_LIMIT"
        )

    def _cancel_active_stops_after_flat(
        self,
        *,
        instrument: str,
        trade_id: str,
        symbol: str,
        snapshot: BrokerSnapshot,
    ) -> BrokerSnapshot:
        active = active_sltp_for_trade(
            snapshot.orders, trade_id=trade_id, symbol=symbol
        )
        for stop in active:
            try:
                self.transport.cancel_protective_stop_after_flat(
                    stop.order_id, observed_position_quantity=0
                )
            except FinamError:
                # A stop may have become terminal between GET and DELETE.
                pass
        if not active:
            return snapshot

        last = self._snapshot()
        for index in range(ORDER_RECONCILIATION_OBSERVATIONS):
            remaining = active_sltp_for_trade(
                last.orders, trade_id=trade_id, symbol=symbol
            )
            if not remaining:
                return last
            if index + 1 < ORDER_RECONCILIATION_OBSERVATIONS:
                self.sleeper(RECONCILIATION_SLEEP_SECONDS)
                last = self._snapshot()
        raise ProductionServiceFault(
            "PRODUCTION_PROTECTIVE_STOP_TERMINAL_PROOF_TIMEOUT"
        )

    def _close_flat_local_positions(
        self, snapshot: BrokerSnapshot
    ) -> BrokerSnapshot:
        for instrument, position in sorted(
            self.runtime.open_positions().items()
        ):
            symbol = position["finam_symbol"]
            quantity = snapshot.positions.get(symbol, 0)
            if quantity != 0:
                continue
            trade_id = position["trade_id"]
            # Any emergency intent is position-authoritatively filled when the
            # exact broker position is flat.
            for intent in self.runtime.store.unresolved_intents():
                if (
                    intent["payload"].get("kind") == "EMERGENCY_EXIT_REQUIRED"
                    and intent["payload"].get("trade_id") == trade_id
                ):
                    self.runtime.store.transition_intent(
                        intent["idempotency_key"],
                        "FILL",
                        intent.get("broker_order_id"),
                    )
                    self.runtime.store.transition_intent(
                        intent["idempotency_key"],
                        "RECONCILED",
                        intent.get("broker_order_id"),
                    )
            snapshot = self._cancel_active_stops_after_flat(
                instrument=instrument,
                trade_id=trade_id,
                symbol=symbol,
                snapshot=snapshot,
            )
            refreshed = self._snapshot()
            if refreshed.positions.get(symbol, 0) != 0:
                raise ProductionServiceFault(
                    "PRODUCTION_POSITION_REAPPEARED_DURING_CLOSEOUT"
                )
            self.runtime.broker_exit_observed(
                instrument,
                realized_equity_after_exit=refreshed.realized_basis,
                protective_stop_terminal=True,
            )
            snapshot = refreshed
        return snapshot

    def _validate_local_positions(
        self, snapshot: BrokerSnapshot
    ) -> None:
        local = self.runtime.open_positions()
        expected_symbols = {
            value["finam_symbol"]: (
                int(value["quantity"])
                if value["direction"] == "LONG"
                else -int(value["quantity"])
            )
            for value in local.values()
        }
        for symbol, quantity in snapshot.positions.items():
            if symbol not in expected_symbols:
                raise ProductionServiceFault(
                    "PRODUCTION_UNEXPECTED_BROKER_POSITION"
                )
            if expected_symbols[symbol] != quantity:
                raise ProductionServiceFault(
                    "PRODUCTION_POSITION_AUTHORITY_UNEXPECTED_QUANTITY"
                )
        for symbol, expected in expected_symbols.items():
            actual = snapshot.positions.get(symbol, 0)
            if actual not in {0, expected}:
                raise ProductionServiceFault(
                    "PRODUCTION_POSITION_AUTHORITY_UNEXPECTED_QUANTITY"
                )

    def _position_protection(
        self, snapshot: BrokerSnapshot
    ) -> list[dict[str, Any]]:
        protection: list[dict[str, Any]] = []
        allowed_stop_ids: set[str] = set()
        for instrument, position in sorted(
            self.runtime.open_positions().items()
        ):
            symbol = position["finam_symbol"]
            expected = (
                int(position["quantity"])
                if position["direction"] == "LONG"
                else -int(position["quantity"])
            )
            actual = snapshot.positions.get(symbol, 0)
            if actual != expected:
                raise ProductionServiceFault(
                    "PRODUCTION_POSITION_NOT_EXACT_FOR_HEARTBEAT"
                )
            if position.get("protective_stop_state") != "ACTIVE":
                raise ProductionServiceFault(
                    "PRODUCTION_PROTECTIVE_STOP_NOT_ACTIVE"
                )
            stops = active_sltp_for_trade(
                snapshot.orders,
                trade_id=position["trade_id"],
                symbol=symbol,
            )
            if not stops:
                raise ProductionServiceFault(
                    "PRODUCTION_ACTIVE_PROTECTIVE_STOP_MISSING"
                )
            latest_id = position.get("protective_stop_broker_order_id")
            latest = next(
                (stop for stop in stops if stop.order_id == latest_id),
                None,
            )
            if latest is None:
                raise ProductionServiceFault(
                    "PRODUCTION_EFFECTIVE_PROTECTIVE_STOP_MISSING"
                )
            expected_side = (
                "SIDE_SELL"
                if position["direction"] == "LONG"
                else "SIDE_BUY"
            )
            if any(stop.side != expected_side for stop in stops):
                raise ProductionServiceFault(
                    "PRODUCTION_PROTECTIVE_STOP_SIDE_MISMATCH"
                )
            try:
                broker_price = parse_rest_decimal_value_object(
                    latest.request.get("sl_price"), positive=True
                )
                local_price = Decimal(
                    str(position["protective_stop_price"])
                )
            except (ValueError, InvalidOperation, KeyError):
                raise ProductionServiceFault(
                    "PRODUCTION_PROTECTIVE_STOP_PRICE_INVALID"
                ) from None
            if broker_price != local_price:
                raise ProductionServiceFault(
                    "PRODUCTION_EFFECTIVE_PROTECTIVE_STOP_PRICE_MISMATCH"
                )
            ids = sorted(stop.order_id for stop in stops)
            allowed_stop_ids.update(ids)
            protection.append({
                "instrument": instrument,
                "trade_id": position["trade_id"],
                "expected_position_quantity": expected,
                "covered_quantity": abs(expected),
                "active_stop_order_ids": ids,
            })

        all_intents = {
            compact_client_order_id(row["idempotency_key"])
            for row in self.runtime.store.all_intents()
            if row["payload"].get("kind")
            in {"ENTRY", "EMERGENCY_EXIT_REQUIRED"}
        }
        for order in snapshot.orders:
            if not order.active:
                continue
            if order.kind == "REGULAR":
                if order.client_order_id not in all_intents:
                    raise ProductionServiceFault(
                        "PRODUCTION_UNEXPECTED_ACTIVE_REGULAR_ORDER"
                    )
            elif order.order_id not in allowed_stop_ids:
                raise ProductionServiceFault(
                    "PRODUCTION_UNEXPECTED_ACTIVE_SLTP_ORDER"
                )
        return protection

    def _publish_heartbeat(
        self,
        *,
        healthy: bool,
        protection: list[dict[str, Any]],
        failure_code: str | None = None,
    ) -> None:
        write_production_heartbeat(
            self.root,
            accepted_commit=self.accepted_commit,
            account_hash=self.account_hash,
            reconciliation_status="PASS" if healthy else "FAULT",
            unresolved_intent_count=self.runtime.store.unresolved_intent_count(),
            health_status="HEALTHY" if healthy else "UNHEALTHY",
            cycle_count=self.cycle_count,
            last_api_contact=self.last_api_contact,
            position_protection=protection,
            failure_code=failure_code,
            consecutive_failures=self.consecutive_failures,
            now=self.clock().astimezone(timezone.utc),
        )
        self.last_position_protection = list(protection)

    def _manage_positions(
        self,
        snapshot: BrokerSnapshot,
        histories: dict[str, pd.DataFrame],
    ) -> BrokerSnapshot:
        for instrument in sorted(self.runtime.open_positions()):
            position = self.runtime.open_positions()[instrument]
            symbol = position["finam_symbol"]
            expected = (
                int(position["quantity"])
                if position["direction"] == "LONG"
                else -int(position["quantity"])
            )
            if snapshot.positions.get(symbol, 0) != expected:
                continue
            execution, _ = self.runtime.context_builder.build(
                histories[instrument],
                self.clock().astimezone(timezone.utc),
            )
            prior_text = self.runtime.store.get(
                f"last_managed_h1:{instrument}"
            )
            if not isinstance(prior_text, str):
                raise ProductionServiceFault(
                    "PRODUCTION_MANAGEMENT_WATERMARK_MISSING"
                )
            prior = pd.Timestamp(prior_text)
            for stamp, row in execution.loc[execution.index > prior].iterrows():
                if pd.isna(row.ATR):
                    raise ProductionServiceFault(
                        "PRODUCTION_MANAGEMENT_ATR_UNAVAILABLE"
                    )
                current_snapshot = self._snapshot()
                quantity = current_snapshot.positions.get(symbol, 0)
                if quantity == 0:
                    snapshot = self._close_flat_local_positions(
                        current_snapshot
                    )
                    break
                if quantity != expected:
                    raise ProductionServiceFault(
                        "PRODUCTION_POSITION_AUTHORITY_UNEXPECTED_QUANTITY"
                    )
                bar = CompletedBar(
                    stamp.to_pydatetime(),
                    float(row.Open),
                    float(row.High),
                    float(row.Low),
                    float(row.Close),
                    float(row.ATR),
                )
                action = self.runtime.manage_completed_bar(
                    instrument,
                    bar,
                    observed_position_quantity=quantity,
                )
                if action is None:
                    snapshot = current_snapshot
                    continue
                if action.kind == "PROTECTIVE_STOP_REPLACE":
                    snapshot = self._ensure_stop_or_exit(
                        action, current_snapshot
                    )
                elif action.kind == "EMERGENCY_EXIT_REQUIRED":
                    snapshot = self._submit_emergency_exit(
                        action, quantity
                    )
                    snapshot = self._close_flat_local_positions(snapshot)
                    break
                else:
                    raise ProductionServiceFault(
                        "PRODUCTION_MANAGEMENT_ACTION_INVALID"
                    )
        return snapshot

    def _require_realized_basis(self, snapshot: BrokerSnapshot) -> Decimal:
        persisted = self.runtime.current_realized_equity()
        if persisted is None:
            raise ProductionServiceFault(
                "PRODUCTION_REALIZED_EQUITY_NOT_INITIALIZED"
            )
        if snapshot.realized_basis != persisted:
            raise ProductionServiceFault(
                "UNEXPLAINED_REALIZED_EQUITY_DISCREPANCY"
            )
        return persisted

    def _submit_new_entry(
        self,
        action: RuntimeAction,
        now: datetime,
    ) -> BrokerSnapshot:
        if not action.idempotency_key:
            raise ProductionServiceFault("PRODUCTION_ENTRY_KEY_MISSING")
        intent = self.runtime.store.intent(action.idempotency_key)
        if intent is None or intent["status"] != "INTENT_PERSISTED":
            raise ProductionServiceFault("PRODUCTION_ENTRY_INTENT_STATE_INVALID")
        self.runtime.store.transition_intent(action.idempotency_key, "SUBMITTED")
        try:
            response = self.transport.submit_entry(action, now=now)
        except FinamOrderRejected:
            self.runtime.store.transition_intent(
                action.idempotency_key, "REJECTED"
            )
            return self._snapshot()
        except FinamUncertainSubmission:
            self.runtime.store.transition_intent(
                action.idempotency_key, "UNCERTAIN"
            )
        else:
            self.runtime.store.transition_intent(
                action.idempotency_key,
                "ACK",
                _broker_order_id(response),
            )

        snapshot = self._wait_for_position(action)
        expected = action.expected_position_quantity
        if snapshot.positions.get(action.finam_symbol, 0) != expected:
            raise ProductionServiceFault(
                "PRODUCTION_ENTRY_POSITION_RECONCILIATION_TIMEOUT"
            )
        stop = self.runtime.confirm_entry_position(
            action.idempotency_key,
            expected,
        )
        refreshed = self._snapshot()
        if stop is not None:
            refreshed = self._ensure_stop_or_exit(stop, refreshed)
        return refreshed

    def cycle(self) -> None:
        now = self.clock().astimezone(timezone.utc)
        snapshot = self._snapshot()
        authorities, histories, schedules = self._instrument_data(now)
        self._activation_initialize(snapshot, histories)
        if not self.startup_pending_cleanup_complete:
            for instrument in INSTRUMENTS:
                self.runtime.discard_orphan_pending_signal(instrument)
            self.startup_pending_cleanup_complete = True

        # Recover any durable pre-crash intents before interpreting new H1.
        snapshot = self._reconcile_unresolved(snapshot)
        snapshot = self._close_flat_local_positions(snapshot)
        snapshot = self._reconcile_unresolved(snapshot)
        self._validate_local_positions(snapshot)

        # Persisted realized equity excludes all current unrealized PnL.
        realized = self._require_realized_basis(snapshot)

        # Every live local position must have broker-proven protection before
        # any H1 management or any new signal can proceed.
        protection = self._position_protection(snapshot)
        snapshot = self._manage_positions(snapshot, histories)
        snapshot = self._close_flat_local_positions(self._snapshot())
        snapshot = self._reconcile_unresolved(snapshot)
        self._validate_local_positions(snapshot)
        realized = self._require_realized_basis(snapshot)
        protection = self._position_protection(snapshot)

        self.cycle_count += 1
        self.consecutive_failures = 0
        self._publish_heartbeat(healthy=True, protection=protection)

        gate = evaluate_production_entry_gate(
            runtime_root=self.root,
            now=now,
            expected_commit=self.accepted_commit,
            expected_account_hash=self.account_hash,
            execution_authorized=True,
        )
        if gate.get("entry_gate_open") is not True:
            # HALTED or otherwise blocked means no historical signal may linger
            # for a later re-arm. Existing positions were already managed above.
            for instrument in INSTRUMENTS:
                if instrument not in self.runtime.open_positions():
                    self.runtime.consume_entry_bar(
                        instrument, histories[instrument].index[-1]
                    )
            self.logger.info(
                "PRODUCTION_CYCLE_PASS_NO_ENTRY cycle=%d reasons=%s",
                self.cycle_count,
                ",".join(gate.get("reason_codes") or []),
            )
            return

        budget = self.runtime.begin_batch(
            realized_equity=realized,
            available_cash=snapshot.available_cash,
        )
        signals = []
        for instrument in INSTRUMENTS:
            if instrument in self.runtime.open_positions():
                continue
            signal = self.runtime.build_latest_signal(
                instrument, histories[instrument], now
            )
            if signal is not None:
                signals.append(signal)
        signals.sort(
            key=lambda signal: (
                signal.timestamp,
                signal.instrument,
                signal.trade_id,
            )
        )

        for signal in signals:
            # Fresh broker schedule immediately precedes any possible POST.
            schedule = self.api.schedule(
                authorities[signal.instrument].finam_symbol
            )
            post_now = self.clock().astimezone(timezone.utc)
            if not _entry_session_open(schedule, post_now):
                self.runtime.discard_pending_signal(signal)
                continue

            # A prior entry in the same batch changes broker exposure/protection.
            # Re-publish exact reconciliation before the next new entry.
            current = self._snapshot()
            self._validate_local_positions(current)
            current_protection = self._position_protection(current)
            self._publish_heartbeat(
                healthy=True, protection=current_protection
            )
            gate = evaluate_production_entry_gate(
                runtime_root=self.root,
                now=post_now,
                expected_commit=self.accepted_commit,
                expected_account_hash=self.account_hash,
                execution_authorized=True,
            )
            if gate.get("entry_gate_open") is not True:
                self.runtime.discard_pending_signal(signal)
                continue

            action = self.runtime.plan_entry(
                signal,
                authorities[signal.instrument],
                realized_equity=realized,
                budget=budget,
            )
            if action.kind != "ENTRY":
                continue
            current = self._submit_new_entry(action, post_now)
            current = self._close_flat_local_positions(current)
            current = self._reconcile_unresolved(current)
            self._validate_local_positions(current)
            current_protection = self._position_protection(current)
            self._publish_heartbeat(
                healthy=True, protection=current_protection
            )

        final = self._snapshot()
        final = self._close_flat_local_positions(final)
        final = self._reconcile_unresolved(final)
        self._validate_local_positions(final)
        self._require_realized_basis(final)
        final_protection = self._position_protection(final)
        self._publish_heartbeat(healthy=True, protection=final_protection)
        self.logger.info(
            "PRODUCTION_CYCLE_PASS cycle=%d positions=%d",
            self.cycle_count,
            len(final_protection),
        )

    def run(self, *, once: bool = False) -> int:
        while True:
            try:
                self.cycle()
            except Exception as exc:
                self.consecutive_failures += 1
                try:
                    emergency_halt(self.root)
                except Exception:
                    pass
                code = str(exc)
                if not (
                    isinstance(
                        exc,
                        (
                            ProductionServiceFault,
                            ProductionRuntimeError,
                            ProductionBrokerStateError,
                            ProductionHistoryError,
                            ProductionH1CacheError,
                        ),
                    )
                    and code
                    and len(code) <= 128
                ):
                    code = "STAGE8_12_4_PRODUCTION_CYCLE_FAILED"
                try:
                    self._publish_heartbeat(
                        healthy=False,
                        protection=self.last_position_protection,
                        failure_code=code,
                    )
                except Exception:
                    pass
                self.logger.error(
                    "PRODUCTION_SAFETY_FAULT code=%s cycle=%d",
                    code,
                    self.cycle_count,
                )
                return 1
            if once:
                return 0
            self.sleeper(self.poll_seconds)


def _required_environment(environment: dict[str, str]) -> tuple[str, str]:
    if environment.get("FINAM_MODE") != MODE:
        raise ProductionServiceFault("REAL_PRODUCTION_MODE_REQUIRED")
    if environment.get("PRODUCTION_SPECIFICATION_ID") != PRODUCTION_SPECIFICATION_ID:
        raise ProductionServiceFault("PRODUCTION_SPECIFICATION_ID_REQUIRED")
    if environment.get("PRODUCTION_IDENTITY") != ACTIVE_IDENTITY:
        raise ProductionServiceFault("PRODUCTION_IDENTITY_REQUIRED")
    secret = environment.get("FINAM_API_SECRET", "")
    account = environment.get("FINAM_REAL_ACCOUNT_ID", "")
    if not secret:
        raise ProductionServiceFault("FINAM_API_SECRET_MISSING")
    if not account:
        raise ProductionServiceFault("FINAM_REAL_ACCOUNT_ID_MISSING")
    return secret, account


def run_from_environment(
    runtime_root: Path,
    data_root: Path,
    accepted_commit: str,
    *,
    once: bool = False,
    poll_seconds: int = DEFAULT_POLL_SECONDS,
    api_factory=FinamAPI,
    environment: dict[str, str] | None = None,
    clock: Callable[[], datetime] | None = None,
    sleeper: Callable[[float], None] = time.sleep,
) -> int:
    environment = dict(os.environ if environment is None else environment)
    lock = InstanceLock(Path(runtime_root) / "state" / LOCK_FILENAME)
    lock.acquire()
    service = None
    try:
        secret, account = _required_environment(environment)
        spec = load_frozen_specification()
        if (
            spec.production_id != PRODUCTION_SPECIFICATION_ID
            or spec.identity != ACTIVE_IDENTITY
            or tuple(spec.instruments) != tuple(N4)
        ):
            raise ProductionServiceFault("FROZEN_PRODUCTION_AUTHORITY_INVALID")
        service = ProductionService(
            runtime_root=runtime_root,
            data_root=data_root,
            accepted_commit=accepted_commit,
            api=api_factory(secret),
            account_id=account,
            poll_seconds=poll_seconds,
            clock=clock,
            sleeper=sleeper,
        )
        return service.run(once=once)
    except Exception:
        try:
            emergency_halt(runtime_root)
        except Exception:
            pass
        raise
    finally:
        if service is not None:
            service.close()
        lock.release()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Authorized Stage 8.12.4 FULL/R15 FINAM production service"
    )
    parser.add_argument("--runtime-root", type=Path, required=True)
    parser.add_argument("--data-root", type=Path, required=True)
    parser.add_argument("--accepted-commit", required=True)
    parser.add_argument("--once", action="store_true")
    parser.add_argument(
        "--poll-seconds", type=int, default=DEFAULT_POLL_SECONDS
    )
    args = parser.parse_args(argv)
    try:
        return run_from_environment(
            args.runtime_root,
            args.data_root,
            args.accepted_commit,
            once=args.once,
            poll_seconds=args.poll_seconds,
        )
    except Exception as exc:
        code = str(exc)
        if not code or len(code) > 128:
            code = "STAGE8_12_4_PRODUCTION_STARTUP_FAILED"
        print(code)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
