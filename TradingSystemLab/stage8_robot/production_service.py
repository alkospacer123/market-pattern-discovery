"""Continuous Stage 8.12.4 FULL/R15 production service.

The service is deliberately split from the broker-neutral ProductionRuntime.
It consumes durable runtime actions only after exact Stage 8.12.4 authorization,
reconciles every broker transition, maintains exact H1 indicator continuity,
and fails closed to HALTED on ambiguous state.  No signal or sizing rule lives
here.
"""
from __future__ import annotations

import argparse
import hashlib
import os
import sqlite3
import time
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any, Callable

import pandas as pd

from .account_cleanliness import ACTIVE_ORDER_STATUSES, TERMINAL_ORDER_STATUSES
from .broker import compact_client_order_id
from .finam_api import (
    FinamAPI,
    FinamOrderRejected,
    FinamUncertainSubmission,
)
from .funding_margin_diagnostic import ACTIVE_ACCOUNT_STATUSES
from .instrument_resolver import (
    MOEX_REFERENCE,
    discover_finam_asset,
    validate_finam_binding,
)
from .live_execution import AuthorizedFinamProductionTransport, LiveExecutionError
from .margin import (
    directional_initial_margin,
    portfolio_authority,
)
from .operations import InstanceLock, configure_operational_log
from .production_authorization import load_authorization
from .production_broker_state import (
    BrokerOrderView,
    ProductionBrokerStateError,
    broker_realized_basis,
    order_for_intent,
    order_views,
    position_quantities,
    protected_stop_ids_for_position,
    require_no_external_cash_flows,
    require_no_unknown_active_orders,
)
from .production_history import (
    ProductionHistoryError,
    update_production_h1,
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
from .readonly_supervisor import trading_h1_windows, newest_expected_h1_close
from .specification import (
    ACTIVE_IDENTITY,
    INSTRUMENTS,
    PRODUCTION_SPECIFICATION_ID,
    load_frozen_specification,
)
from .strategy_core import CompletedBar
from .trading_safety_gate import write_kill_switch

MODE = "STAGE8_12_4_FULL_R15_PRODUCTION"
PRODUCTION_STATE_FILENAME = "stage8-12-production.sqlite3"
DEFAULT_POLL_SECONDS = 300
POLL_MIN_SECONDS = 30
POLL_MAX_SECONDS = 3600
DEFAULT_BACKOFF_SECONDS = 30
PENDING_POLL_SECONDS = 5
SUBMISSION_RECONCILIATION_POLLS = 5
SUBMISSION_RECONCILIATION_SLEEP_SECONDS = 1
FILLED_ORDER_STATUSES = frozenset({"FILLED", "EXECUTED", "SL_EXECUTED", "TP_EXECUTED"})
REJECTED_ORDER_STATUSES = frozenset({
    "REJECTED", "FAILED", "DENIED_BY_BROKER", "REJECTED_BY_EXCHANGE",
    "CANCELLED", "EXPIRED", "DISABLED",
})


class ProductionServiceFault(RuntimeError):
    def __init__(self, code: str, *, halt: bool = True, pending: bool = False):
        super().__init__(code)
        self.halt = halt
        self.pending = pending


def _runtime_action(payload: dict[str, Any]) -> RuntimeAction:
    try:
        return RuntimeAction(
            payload["kind"],
            payload.get("idempotency_key"),
            payload["instrument"],
            payload["finam_symbol"],
            payload.get("direction"),
            int(payload["quantity"]),
            payload.get("trade_id"),
            payload.get("signal_id"),
            Decimal(str(payload["reference_price"]))
            if payload.get("reference_price") is not None else None,
            Decimal(str(payload["stop_price"]))
            if payload.get("stop_price") is not None else None,
            payload.get("expected_position_quantity"),
            payload.get("reason"),
        )
    except (KeyError, TypeError, ValueError):
        raise ProductionServiceFault("LOCAL_INTENT_PAYLOAD_INVALID") from None


def _order_id_from_response(response: Any) -> str:
    if not isinstance(response, dict):
        raise ProductionServiceFault("BROKER_ORDER_ACK_INVALID")
    value = response.get("order_id")
    if not isinstance(value, str) or not value:
        raise ProductionServiceFault("BROKER_ORDER_ACK_ID_MISSING")
    return value


def _expected_quantity(position: dict[str, Any]) -> int:
    try:
        quantity = int(position["quantity"])
        direction = position["direction"]
    except (KeyError, TypeError, ValueError):
        raise ProductionServiceFault("LOCAL_POSITION_STATE_INVALID") from None
    if quantity <= 0 or direction not in {"LONG", "SHORT"}:
        raise ProductionServiceFault("LOCAL_POSITION_STATE_INVALID")
    return quantity if direction == "LONG" else -quantity


class ProductionService:
    def __init__(
        self,
        *,
        runtime_root: Path,
        data_root: Path,
        api: Any,
        account_id: str,
        accepted_commit: str,
        poll_seconds: int = DEFAULT_POLL_SECONDS,
        clock: Callable[[], datetime] | None = None,
        sleeper: Callable[[float], None] = time.sleep,
    ):
        if not POLL_MIN_SECONDS <= poll_seconds <= POLL_MAX_SECONDS:
            raise ProductionServiceFault("PRODUCTION_POLL_SECONDS_INVALID")
        self.root = Path(runtime_root)
        self.data_root = Path(data_root)
        for name in ("state", "audit", "logs", "diagnostics", "backups", "safety"):
            (self.root / name).mkdir(parents=True, exist_ok=True)
        self.api = api
        self.account_id = str(account_id)
        if not self.account_id:
            raise ProductionServiceFault("PRODUCTION_ACCOUNT_REQUIRED")
        self.account_hash = hashlib.sha256(self.account_id.encode("utf-8")).hexdigest()
        self.accepted_commit = str(accepted_commit).strip().lower()
        self.clock = clock or (lambda: datetime.now(timezone.utc))
        self.sleeper = sleeper
        self.poll_seconds = poll_seconds
        self.logger = configure_operational_log(
            self.root / "logs" / "stage8-production.log"
        )
        self.runtime = ProductionRuntime(
            self.root / "state" / PRODUCTION_STATE_FILENAME
        )
        self.authorization = load_authorization(
            self.root,
            expected_commit=self.accepted_commit,
            expected_account_hash=self.account_hash,
        )
        self.transport = AuthorizedFinamProductionTransport(
            api=self.api,
            account_id=self.account_id,
            runtime_root=self.root,
            accepted_commit=self.accepted_commit,
        )
        self.cycle_count = int(self.runtime.store.get("production_cycle_count", 0) or 0)
        self.last_protection: list[dict[str, Any]] = []
        self.last_broker_open_count = 0
        self.last_api_contact: datetime = self.clock().astimezone(timezone.utc)

    def close(self) -> None:
        self.runtime.close()
        for handler in self.logger.handlers:
            handler.flush()
            handler.close()
        self.logger.handlers.clear()

    def connect(self) -> None:
        spec = load_frozen_specification()
        if (
            spec.production_id != PRODUCTION_SPECIFICATION_ID
            or spec.identity != ACTIVE_IDENTITY
            or tuple(spec.instruments) != tuple(INSTRUMENTS)
        ):
            raise ProductionServiceFault("FROZEN_PRODUCTION_AUTHORITY_INVALID")
        self.transport.connect()

    def _transaction_start(self) -> datetime:
        authorized = self.authorization.get("authorized_utc")
        if not isinstance(authorized, str):
            raise ProductionServiceFault("PRODUCTION_AUTHORIZATION_TIMESTAMP_INVALID")
        try:
            authorization_time = datetime.fromisoformat(
                authorized.replace("Z", "+00:00")
            )
        except ValueError:
            raise ProductionServiceFault("PRODUCTION_AUTHORIZATION_TIMESTAMP_INVALID") from None
        if authorization_time.tzinfo is None:
            raise ProductionServiceFault("PRODUCTION_AUTHORIZATION_TIMESTAMP_INVALID")
        persisted = self.runtime.store.get("last_transaction_scan_utc")
        if persisted is None:
            return authorization_time.astimezone(timezone.utc)
        try:
            prior = datetime.fromisoformat(str(persisted).replace("Z", "+00:00"))
        except ValueError:
            raise ProductionServiceFault("TRANSACTION_SCAN_STATE_INVALID") from None
        if prior.tzinfo is None:
            raise ProductionServiceFault("TRANSACTION_SCAN_STATE_INVALID")
        return max(
            authorization_time.astimezone(timezone.utc),
            prior.astimezone(timezone.utc) - timedelta(minutes=5),
        )

    def _scan_external_cash_flows(self, now: datetime) -> None:
        start = self._transaction_start()
        if start > now:
            raise ProductionServiceFault("TRANSACTION_SCAN_CLOCK_INVALID")
        response = self.api.transactions(
            self.account_id, start.isoformat(), now.isoformat(), limit=1000
        )
        try:
            require_no_external_cash_flows(response)
        except ProductionBrokerStateError as exc:
            raise ProductionServiceFault(str(exc)) from None
        self.runtime.store.put("last_transaction_scan_utc", now.isoformat())

    def _financial_authority(self, account: dict[str, Any], now: datetime):
        self._scan_external_cash_flows(now)
        try:
            realized = broker_realized_basis(account)
            portfolio = portfolio_authority(account)
        except (ProductionBrokerStateError, ValueError) as exc:
            raise ProductionServiceFault(str(exc)) from None
        starting = self.runtime.store.get("starting_realized_equity")
        if starting is None:
            if self.runtime.open_positions() or self.runtime.store.unresolved_intent_count():
                raise ProductionServiceFault(
                    "REALIZED_EQUITY_INITIALIZATION_REQUIRES_CLEAN_LOCAL_STATE"
                )
            self.runtime.store.put("starting_realized_equity", str(realized))
        else:
            try:
                if Decimal(str(starting)) <= 0:
                    raise ValueError
            except Exception:
                raise ProductionServiceFault(
                    "STARTING_REALIZED_EQUITY_STATE_INVALID"
                ) from None
        # Broker equity less broker unrealized PnL is the current realized basis.
        # External funding changes after authorization were rejected above.
        self.runtime.set_realized_equity(realized)
        return realized, portfolio

    def _snapshot(self) -> tuple[dict[str, Any], list[BrokerOrderView], dict[str, int]]:
        details = self.api.session_details()
        if (
            not isinstance(details, dict)
            or details.get("readonly") is not False
            or not isinstance(details.get("account_ids"), list)
            or [str(value) for value in details["account_ids"]].count(
                self.account_id
            ) != 1
        ):
            raise ProductionServiceFault("PRODUCTION_TRADING_SESSION_AUTHORITY_INVALID")
        account = self.api.account(self.account_id)
        if (
            not isinstance(account, dict)
            or account.get("status") not in ACTIVE_ACCOUNT_STATUSES
        ):
            raise ProductionServiceFault("PRODUCTION_ACCOUNT_NOT_ACTIVE")
        try:
            orders = order_views(self.api.orders(self.account_id))
            by_symbol = position_quantities(account)
            require_no_unknown_active_orders(
                orders, self.runtime.store.all_intents()
            )
        except ProductionBrokerStateError as exc:
            raise ProductionServiceFault(str(exc)) from None
        finam_to_instrument = {
            row["finam_symbol"]: instrument
            for instrument, row in self.runtime.registry.items()
        }
        unknown = set(by_symbol) - set(finam_to_instrument)
        if unknown:
            raise ProductionServiceFault("STAGE8_12_4_UNEXPECTED_NON_N4_POSITION")
        positions = {
            instrument: by_symbol.get(row["finam_symbol"], 0)
            for instrument, row in self.runtime.registry.items()
        }
        self.last_api_contact = self.clock().astimezone(timezone.utc)
        return account, orders, positions

    def _build_authorities_and_histories(
        self, now: datetime
    ) -> tuple[dict[str, InstrumentAuthority], dict[str, pd.DataFrame]]:
        assets = self.api.assets_all_active()
        if not isinstance(assets, list):
            raise ProductionServiceFault("PRODUCTION_ACTIVE_ASSET_CATALOG_INVALID")
        authorities: dict[str, InstrumentAuthority] = {}
        histories: dict[str, pd.DataFrame] = {}
        start = (now - timedelta(days=30)).isoformat()
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
            binding = validate_finam_binding(
                instrument, asset, params, schedule,
                self.api.asset(symbol, self.account_id),
            ).to_dict()
            if (
                not str(binding.get("status", "")).startswith("AUTHENTICATED_")
                or binding.get("is_tradable") is not True
                or binding.get("finam_symbol") != frozen["finam_symbol"]
                or binding.get("mic") != frozen["mic"]
                or str(binding.get("security_id")) != frozen["security_id"]
                or str(binding.get("trade_lot_size")) != frozen["quantity_granularity"]
            ):
                raise ProductionServiceFault("PRODUCTION_N4_BINDING_INVALID")
            try:
                authority = InstrumentAuthority(
                    instrument=instrument,
                    finam_symbol=symbol,
                    price_step=Decimal(frozen["price_step"]),
                    tick_value=Decimal(frozen["tick_value"]),
                    trade_lot_size=int(Decimal(frozen["quantity_granularity"])),
                    long_initial_margin=directional_initial_margin(params, "LONG"),
                    short_initial_margin=directional_initial_margin(params, "SHORT"),
                )
                windows = trading_h1_windows(schedule)
                response = self.api.bars(symbol, start, now.isoformat())
                history = update_production_h1(
                    runtime_root=self.root,
                    data_root=self.data_root,
                    instrument=instrument,
                    finam_response=response,
                    observed_at=now,
                    trading_windows=windows,
                )
                expected_open = newest_expected_h1_close(schedule, now)
            except (KeyError, ValueError, ProductionHistoryError) as exc:
                raise ProductionServiceFault(str(exc)) from None
            if expected_open is not None:
                expected_close = (
                    pd.Timestamp(expected_open).tz_convert("Europe/Moscow")
                    + pd.Timedelta("1h")
                )
                if expected_close not in history.index:
                    raise ProductionServiceFault("STALE_COMPLETED_H1_DATA")
                self.runtime.store.put(
                    f"expected_h1:{instrument}",
                    expected_open.astimezone(timezone.utc).isoformat(),
                )
            authorities[instrument] = authority
            histories[instrument] = history
        return authorities, histories

    def _transition_ack(self, key: str, broker_id: str) -> None:
        intent = self.runtime.store.intent(key)
        if intent is None:
            raise ProductionServiceFault("LOCAL_INTENT_NOT_FOUND")
        if intent["status"] == "ACK" and intent.get("broker_order_id") == broker_id:
            return
        self.runtime.store.transition_intent(key, "ACK", broker_id)

    def _submit_intent(
        self,
        intent: dict[str, Any],
        *,
        now: datetime,
        broker_positions_map: dict[str, int],
        allow_entry: bool,
    ) -> None:
        key = intent["idempotency_key"]
        action = _runtime_action(intent["payload"])
        if intent["status"] != "INTENT_PERSISTED":
            return
        if action.kind == "ENTRY" and not allow_entry:
            raise ProductionServiceFault("ORPHANED_ENTRY_INTENT_REQUIRES_OPERATOR")
        self.runtime.store.transition_intent(key, "SUBMITTED")
        try:
            if action.kind == "ENTRY":
                response = self.transport.submit_entry(action, now=now)
            elif action.kind in {"PROTECTIVE_STOP_INSTALL", "PROTECTIVE_STOP_REPLACE"}:
                response = self.transport.submit_protective_stop(
                    action,
                    observed_position_quantity=broker_positions_map[action.instrument],
                )
            elif action.kind == "EMERGENCY_EXIT_REQUIRED":
                response = self.transport.submit_emergency_exit(
                    action,
                    observed_position_quantity=broker_positions_map[action.instrument],
                )
            else:
                raise ProductionServiceFault("LOCAL_INTENT_KIND_INVALID")
        except LiveExecutionError as exc:
            code = str(exc)
            if (
                action.kind == "ENTRY"
                and code.startswith("STAGE8_12_4_ENTRY_GATE_BLOCKED:")
            ):
                self.runtime.store.transition_intent(key, "CANCELLED")
                raise ProductionServiceFault(code, halt=False) from None
            raise ProductionServiceFault(code) from None
        except FinamOrderRejected:
            self.runtime.store.transition_intent(key, "REJECTED")
            if action.kind == "PROTECTIVE_STOP_INSTALL":
                emergency = self.runtime.require_emergency_exit(
                    action.instrument, reason="PROTECTIVE_STOP_INSTALL_REJECTED"
                )
                emergency_intent = self.runtime.store.intent(emergency.idempotency_key)
                if emergency_intent is None:
                    raise ProductionServiceFault("EMERGENCY_EXIT_INTENT_NOT_FOUND")
                self._submit_intent(
                    {"idempotency_key": emergency.idempotency_key, **emergency_intent},
                    now=now,
                    broker_positions_map=broker_positions_map,
                    allow_entry=False,
                )
                raise ProductionServiceFault(
                    "PROTECTIVE_STOP_INSTALL_REJECTED_EMERGENCY_EXIT_SUBMITTED"
                )
            if action.kind == "PROTECTIVE_STOP_REPLACE":
                raise ProductionServiceFault("PROTECTIVE_STOP_REPLACEMENT_REJECTED")
            if action.kind == "EMERGENCY_EXIT_REQUIRED":
                raise ProductionServiceFault("EMERGENCY_EXIT_REJECTED")
            if action.kind == "ENTRY":
                raise ProductionServiceFault("ENTRY_ORDER_REJECTED")
            raise ProductionServiceFault("ORDER_REJECTED_KIND_INVALID")
        except FinamUncertainSubmission:
            self.runtime.store.transition_intent(key, "UNCERTAIN")
            raise ProductionServiceFault("ORDER_SUBMISSION_UNCERTAIN") from None
        broker_id = _order_id_from_response(response)
        self._transition_ack(key, broker_id)

    def _handle_unresolved_intent(
        self,
        intent: dict[str, Any],
        *,
        now: datetime,
        orders: list[BrokerOrderView],
        broker_positions_map: dict[str, int],
    ) -> bool:
        key = intent["idempotency_key"]
        payload = intent["payload"]
        action = _runtime_action(payload)
        status = intent["status"]
        order = order_for_intent(orders, idempotency_key=key)

        if status == "INTENT_PERSISTED":
            self._submit_intent(
                intent,
                now=now,
                broker_positions_map=broker_positions_map,
                allow_entry=False,
            )
            return True

        if order is None:
            if status == "UNCERTAIN":
                raise ProductionServiceFault("UNCERTAIN_ORDER_NOT_FOUND")
            if status in {"SUBMITTED", "ACK"}:
                raise ProductionServiceFault(
                    "SUBMITTED_ORDER_NOT_FOUND",
                    halt=False,
                    pending=True,
                )
            raise ProductionServiceFault("LOCAL_INTENT_BROKER_ORDER_MISSING")

        if order.status in REJECTED_ORDER_STATUSES:
            self.runtime.store.transition_intent(key, "REJECTED", order.order_id)
            if action.kind == "PROTECTIVE_STOP_INSTALL":
                emergency = self.runtime.require_emergency_exit(
                    action.instrument, reason="PROTECTIVE_STOP_INSTALL_REJECTED"
                )
                emergency_intent = self.runtime.store.intent(emergency.idempotency_key)
                if emergency_intent is None:
                    raise ProductionServiceFault("EMERGENCY_EXIT_INTENT_NOT_FOUND")
                self._submit_intent(
                    {"idempotency_key": emergency.idempotency_key, **emergency_intent},
                    now=now,
                    broker_positions_map=broker_positions_map,
                    allow_entry=False,
                )
                raise ProductionServiceFault(
                    "PROTECTIVE_STOP_INSTALL_REJECTED_EMERGENCY_EXIT_SUBMITTED"
                )
            if action.kind == "PROTECTIVE_STOP_REPLACE":
                raise ProductionServiceFault("PROTECTIVE_STOP_REPLACEMENT_REJECTED")
            if action.kind == "EMERGENCY_EXIT_REQUIRED":
                raise ProductionServiceFault("EMERGENCY_EXIT_REJECTED")
            return True

        if action.kind == "ENTRY":
            if order.status in FILLED_ORDER_STATUSES:
                observed = broker_positions_map[action.instrument]
                if observed != action.expected_position_quantity:
                    raise ProductionServiceFault(
                        "FILLED_ENTRY_POSITION_NOT_EXACT",
                        halt=False,
                        pending=True,
                    )
                self._transition_ack(key, order.order_id)
                stop = self.runtime.confirm_entry_position(key, observed)
                return stop is not None or True
            if order.active:
                self._transition_ack(key, order.order_id)
                raise ProductionServiceFault(
                    "ENTRY_ORDER_PENDING", halt=False, pending=True
                )
            raise ProductionServiceFault("ENTRY_ORDER_TERMINAL_WITHOUT_FILL")

        if action.kind in {"PROTECTIVE_STOP_INSTALL", "PROTECTIVE_STOP_REPLACE"}:
            observed = broker_positions_map[action.instrument]
            if order.active:
                self.runtime.confirm_protective_stop(key, order.order_id)
                return True
            if order.status in {"SL_EXECUTED", "EXECUTED"} and observed == 0:
                self._transition_ack(key, order.order_id)
                self.runtime.store.transition_intent(key, "RECONCILED", order.order_id)
                return True
            if order.status in TERMINAL_ORDER_STATUSES:
                if action.kind == "PROTECTIVE_STOP_INSTALL":
                    emergency = self.runtime.require_emergency_exit(
                        action.instrument, reason="PROTECTIVE_STOP_TERMINAL_WITH_POSITION"
                    )
                    emergency_intent = self.runtime.store.intent(emergency.idempotency_key)
                    if emergency_intent is None:
                        raise ProductionServiceFault("EMERGENCY_EXIT_INTENT_NOT_FOUND")
                    self._submit_intent(
                        {"idempotency_key": emergency.idempotency_key, **emergency_intent},
                        now=now,
                        broker_positions_map=broker_positions_map,
                        allow_entry=False,
                    )
                    raise ProductionServiceFault(
                        "PROTECTIVE_STOP_TERMINAL_EMERGENCY_EXIT_SUBMITTED"
                    )
                raise ProductionServiceFault("PROTECTIVE_STOP_REPLACEMENT_TERMINAL")
            raise ProductionServiceFault(
                "PROTECTIVE_STOP_NOT_ACTIVE", halt=False, pending=True
            )

        if action.kind == "EMERGENCY_EXIT_REQUIRED":
            observed = broker_positions_map[action.instrument]
            if observed == 0:
                self._transition_ack(key, order.order_id)
                self.runtime.store.transition_intent(key, "FILL", order.order_id)
                self.runtime.store.transition_intent(key, "RECONCILED", order.order_id)
                return True
            if order.active:
                self._transition_ack(key, order.order_id)
                raise ProductionServiceFault(
                    "EMERGENCY_EXIT_PENDING", halt=False, pending=True
                )
            if order.status in FILLED_ORDER_STATUSES:
                raise ProductionServiceFault(
                    "EMERGENCY_EXIT_FILLED_POSITION_STILL_OPEN"
                )
            raise ProductionServiceFault("EMERGENCY_EXIT_STATE_INVALID")
        raise ProductionServiceFault("LOCAL_INTENT_KIND_INVALID")

    def _settle_unresolved(self, now: datetime) -> None:
        for attempt in range(SUBMISSION_RECONCILIATION_POLLS):
            unresolved = self.runtime.store.unresolved_intents()
            if not unresolved:
                return
            if len(unresolved) != 1:
                raise ProductionServiceFault("MULTIPLE_UNRESOLVED_PRODUCTION_INTENTS")
            account, orders, positions = self._snapshot()
            changed = self._handle_unresolved_intent(
                unresolved[0], now=now, orders=orders,
                broker_positions_map=positions,
            )
            if changed:
                continue
            if attempt + 1 < SUBMISSION_RECONCILIATION_POLLS:
                self.sleeper(SUBMISSION_RECONCILIATION_SLEEP_SECONDS)
        if self.runtime.store.unresolved_intent_count():
            raise ProductionServiceFault(
                "PRODUCTION_INTENT_RECONCILIATION_PENDING",
                halt=False,
                pending=True,
            )

    def _stop_intents_for_trade(self, trade_id: str) -> list[dict[str, Any]]:
        return [
            row for row in self.runtime.store.all_intents()
            if row["payload"].get("trade_id") == trade_id
            and row["payload"].get("kind") in {
                "PROTECTIVE_STOP_INSTALL", "PROTECTIVE_STOP_REPLACE"
            }
        ]

    def _prove_stops_terminal_after_flat(
        self, position: dict[str, Any]
    ) -> None:
        trade_id = position.get("trade_id")
        if not isinstance(trade_id, str) or not trade_id:
            raise ProductionServiceFault("LOCAL_POSITION_STATE_INVALID")
        intents = self._stop_intents_for_trade(trade_id)
        if not intents:
            raise ProductionServiceFault("PROTECTIVE_STOP_HISTORY_MISSING")
        for intent in intents:
            broker_id = intent.get("broker_order_id")
            if not broker_id:
                if intent.get("status") in {"REJECTED", "CANCELLED"}:
                    continue
                raise ProductionServiceFault("PROTECTIVE_STOP_TERMINAL_PROOF_MISSING")
            order = order_views([self.api.order(self.account_id, broker_id)])[0]
            if order.active:
                try:
                    self.transport.cancel_protective_stop_after_flat(
                        broker_id,
                        observed_position_quantity=0,
                        finam_symbol=position["finam_symbol"],
                    )
                except Exception:
                    # Never retry a cancel blindly after an ambiguous response.
                    order = order_views([self.api.order(self.account_id, broker_id)])[0]
                    if order.active:
                        raise ProductionServiceFault(
                            "PROTECTIVE_STOP_CANCEL_AFTER_FLAT_PENDING",
                            halt=False,
                            pending=True,
                        ) from None
                else:
                    order = order_views([self.api.order(self.account_id, broker_id)])[0]
            if order.status not in TERMINAL_ORDER_STATUSES:
                raise ProductionServiceFault(
                    "PROTECTIVE_STOP_TERMINAL_PENDING",
                    halt=False,
                    pending=True,
                )

    def _finalize_flat_local_positions(
        self,
        broker_positions_map: dict[str, int],
        realized_equity: Decimal,
    ) -> None:
        for instrument, position in list(self.runtime.open_positions().items()):
            if broker_positions_map[instrument] != 0:
                continue
            for intent in self.runtime.store.unresolved_intents():
                if (
                    intent["payload"].get("instrument") == instrument
                    and intent["payload"].get("kind") == "EMERGENCY_EXIT_REQUIRED"
                ):
                    key = intent["idempotency_key"]
                    broker_id = intent.get("broker_order_id")
                    if broker_id:
                        self._transition_ack(key, broker_id)
                    self.runtime.store.transition_intent(key, "FILL", broker_id)
                    self.runtime.store.transition_intent(key, "RECONCILED", broker_id)
            self._prove_stops_terminal_after_flat(position)
            self.runtime.broker_exit_observed(
                instrument,
                realized_equity_after_exit=realized_equity,
                protective_stop_terminal=True,
            )

    def _protection_rows(
        self,
        orders: list[BrokerOrderView],
        broker_positions_map: dict[str, int],
    ) -> list[dict[str, Any]]:
        local = self.runtime.open_positions()
        broker_open = {
            instrument: quantity
            for instrument, quantity in broker_positions_map.items()
            if quantity != 0
        }
        if set(broker_open) != set(local):
            raise ProductionServiceFault("BROKER_LOCAL_POSITION_SET_MISMATCH")
        rows: list[dict[str, Any]] = []
        for instrument in INSTRUMENTS:
            position = local.get(instrument)
            if position is None:
                continue
            expected = _expected_quantity(position)
            if broker_positions_map[instrument] != expected:
                raise ProductionServiceFault("BROKER_LOCAL_POSITION_QUANTITY_MISMATCH")
            if position.get("protective_stop_state") != "ACTIVE":
                raise ProductionServiceFault("LOCAL_PROTECTIVE_STOP_NOT_ACTIVE")
            try:
                stops = protected_stop_ids_for_position(orders, position=position)
            except ProductionBrokerStateError as exc:
                raise ProductionServiceFault(str(exc)) from None
            rows.append({
                "instrument": instrument,
                "trade_id": position["trade_id"],
                "expected_position_quantity": expected,
                "covered_quantity": abs(expected),
                "active_stop_order_ids": stops,
            })
        return rows

    def _heartbeat(
        self,
        *,
        now: datetime,
        healthy: bool,
        code: str | None,
        protection: list[dict[str, Any]],
        broker_open_count: int,
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
            broker_open_position_count=broker_open_count,
            failure_code=code,
            now=now,
        )
        self.last_protection = list(protection)
        self.last_broker_open_count = broker_open_count

    def _entry_gate_open(self, now: datetime) -> bool:
        gate = evaluate_production_entry_gate(
            runtime_root=self.root,
            now=now,
            expected_commit=self.accepted_commit,
            expected_account_hash=self.account_hash,
            execution_authorized=True,
        )
        if gate.get("entry_gate_open") is True:
            return True
        reasons = set(gate.get("reason_codes") or [])
        if reasons == {"KILL_SWITCH_NOT_ARMED"}:
            return False
        raise ProductionServiceFault(
            "PRODUCTION_ENTRY_GATE_INVALID:" + ",".join(sorted(reasons))
        )

    def _completed_bars_after_position(
        self,
        instrument: str,
        history: pd.DataFrame,
        now: datetime,
    ) -> list[CompletedBar]:
        position = self.runtime.open_positions()[instrument]
        signal_text = position.get("signal_timestamp")
        if not isinstance(signal_text, str):
            raise ProductionServiceFault("POSITION_SIGNAL_TIMESTAMP_MISSING")
        try:
            start = pd.Timestamp(datetime.fromisoformat(signal_text))
        except ValueError:
            raise ProductionServiceFault("POSITION_SIGNAL_TIMESTAMP_INVALID") from None
        last_managed = self.runtime.store.get(f"last_managed_h1:{instrument}")
        if last_managed is not None:
            try:
                start = max(start, pd.Timestamp(datetime.fromisoformat(last_managed)))
            except ValueError:
                raise ProductionServiceFault("POSITION_MANAGEMENT_WATERMARK_INVALID") from None
        execution, _ = self.runtime.context_builder.build(history, now)
        result: list[CompletedBar] = []
        for stamp, row in execution.loc[execution.index > start].iterrows():
            if pd.isna(row.ATR):
                raise ProductionServiceFault("POSITION_ATR_UNAVAILABLE")
            result.append(CompletedBar(
                stamp.to_pydatetime(),
                float(row.Open), float(row.High), float(row.Low), float(row.Close),
                float(row.ATR),
                None if pd.isna(row.PriorHigh) else float(row.PriorHigh),
                None if pd.isna(row.PriorLow) else float(row.PriorLow),
                completed=True,
            ))
        return result

    def _submit_new_entry(
        self,
        action: RuntimeAction,
        *,
        now: datetime,
        broker_positions_map: dict[str, int],
    ) -> None:
        intent = self.runtime.store.intent(action.idempotency_key)
        if intent is None:
            raise ProductionServiceFault("ENTRY_INTENT_NOT_FOUND")
        self._submit_intent(
            {"idempotency_key": action.idempotency_key, **intent},
            now=now,
            broker_positions_map=broker_positions_map,
            allow_entry=True,
        )
        # Entry fill + initial SL are reconciled immediately when possible.
        self._settle_unresolved(now)

    def _manage_open_positions(
        self,
        *,
        now: datetime,
        histories: dict[str, pd.DataFrame],
        broker_positions_map: dict[str, int],
    ) -> None:
        for instrument in INSTRUMENTS:
            if instrument not in self.runtime.open_positions():
                continue
            for bar in self._completed_bars_after_position(
                instrument, histories[instrument], now
            ):
                action = self.runtime.manage_completed_bar(
                    instrument,
                    bar,
                    observed_position_quantity=broker_positions_map[instrument],
                )
                if action is None:
                    continue
                intent = self.runtime.store.intent(action.idempotency_key)
                if intent is None:
                    raise ProductionServiceFault("MANAGEMENT_INTENT_NOT_FOUND")
                self._submit_intent(
                    {"idempotency_key": action.idempotency_key, **intent},
                    now=now,
                    broker_positions_map=broker_positions_map,
                    allow_entry=False,
                )
                self._settle_unresolved(now)
                # Re-read broker authority before processing the next H1 bar.
                _, _, broker_positions_map = self._snapshot()
                if broker_positions_map[instrument] == 0:
                    return

    def cycle(self) -> None:
        now = self.clock().astimezone(timezone.utc)
        # Resolve prior durable intent before evaluating any new strategy state.
        self._settle_unresolved(now)

        account, orders, broker_map = self._snapshot()
        local_before_financial = self.runtime.open_positions()
        if any(
            quantity != 0 and instrument not in local_before_financial
            for instrument, quantity in broker_map.items()
        ):
            raise ProductionServiceFault("UNEXPECTED_BROKER_POSITION")
        realized, portfolio = self._financial_authority(account, now)
        self._finalize_flat_local_positions(broker_map, realized)

        # Flat finalization can change local position state and broker stop state.
        account, orders, broker_map = self._snapshot()
        local = self.runtime.open_positions()
        for instrument, quantity in broker_map.items():
            if quantity != 0 and instrument not in local:
                raise ProductionServiceFault("UNEXPECTED_BROKER_POSITION")
        protection = self._protection_rows(orders, broker_map)

        authorities, histories = self._build_authorities_and_histories(now)
        self._manage_open_positions(
            now=now, histories=histories, broker_positions_map=broker_map
        )

        # Management may replace protection or exit a position.
        account, orders, broker_map = self._snapshot()
        realized, portfolio = self._financial_authority(account, now)
        self._finalize_flat_local_positions(broker_map, realized)
        account, orders, broker_map = self._snapshot()
        protection = self._protection_rows(orders, broker_map)

        self.cycle_count += 1
        self.runtime.store.put("production_cycle_count", self.cycle_count)
        self._heartbeat(
            now=now,
            healthy=True,
            code=None,
            protection=protection,
            broker_open_count=sum(1 for value in broker_map.values() if value != 0),
        )

        if not self._entry_gate_open(now):
            return

        budget = self.runtime.begin_batch(
            realized_equity=realized,
            available_cash=portfolio.available_cash,
        )
        for instrument in INSTRUMENTS:
            if instrument in self.runtime.open_positions():
                continue
            signal = self.runtime.build_latest_signal(
                instrument, histories[instrument], now
            )
            if signal is None:
                continue
            action = self.runtime.plan_entry(
                signal,
                authorities[instrument],
                realized_equity=realized,
                budget=budget,
            )
            if action.kind != "ENTRY":
                continue
            self._submit_new_entry(
                action, now=now, broker_positions_map=broker_map
            )
            account, orders, broker_map = self._snapshot()
            protection = self._protection_rows(orders, broker_map)
            self._heartbeat(
                now=now,
                healthy=True,
                code=None,
                protection=protection,
                broker_open_count=sum(
                    1 for value in broker_map.values() if value != 0
                ),
            )

    def run(self, *, once: bool = False) -> int:
        while True:
            try:
                self.cycle()
            except ProductionServiceFault as exc:
                now = self.clock().astimezone(timezone.utc)
                if exc.halt:
                    try:
                        write_kill_switch(self.root, "HALTED", now=now)
                    except Exception:
                        pass
                try:
                    self._heartbeat(
                        now=now,
                        healthy=False,
                        code=str(exc),
                        protection=self.last_protection,
                        broker_open_count=self.last_broker_open_count,
                    )
                except Exception:
                    pass
                self.logger.error(
                    "PRODUCTION_CYCLE_BLOCKED code=%s halt=%s pending=%s",
                    str(exc), exc.halt, exc.pending,
                )
                if once:
                    return 1
                self.sleeper(
                    PENDING_POLL_SECONDS if exc.pending else DEFAULT_BACKOFF_SECONDS
                )
                continue
            except Exception:
                now = self.clock().astimezone(timezone.utc)
                try:
                    write_kill_switch(self.root, "HALTED", now=now)
                except Exception:
                    pass
                try:
                    self._heartbeat(
                        now=now,
                        healthy=False,
                        code="PRODUCTION_OPERATIONAL_CYCLE_FAILED",
                        protection=self.last_protection,
                        broker_open_count=self.last_broker_open_count,
                    )
                except Exception:
                    pass
                self.logger.exception(
                    "PRODUCTION_OPERATIONAL_CYCLE_FAILED"
                )
                if once:
                    return 1
                self.sleeper(DEFAULT_BACKOFF_SECONDS)
                continue
            self.logger.info(
                "PRODUCTION_CYCLE_PASS cycle=%d open_positions=%d",
                self.cycle_count, len(self.runtime.open_positions())
            )
            if once:
                return 0
            self.sleeper(self.poll_seconds)


def run_from_environment(
    runtime_root: Path,
    data_root: Path,
    *,
    accepted_commit: str,
    once: bool = False,
    poll_seconds: int = DEFAULT_POLL_SECONDS,
    api_factory=FinamAPI,
    environment: dict[str, str] | None = None,
    clock: Callable[[], datetime] | None = None,
) -> int:
    environment = dict(os.environ if environment is None else environment)
    if environment.get("FINAM_MODE") != MODE:
        raise ProductionServiceFault("PRODUCTION_MODE_REQUIRED")
    if environment.get("PRODUCTION_SPECIFICATION_ID") != PRODUCTION_SPECIFICATION_ID:
        raise ProductionServiceFault("PRODUCTION_ID_REQUIRED")
    if environment.get("PRODUCTION_IDENTITY") != ACTIVE_IDENTITY:
        raise ProductionServiceFault("PRODUCTION_IDENTITY_REQUIRED")
    secret = environment.get("FINAM_API_SECRET", "")
    account = environment.get("FINAM_REAL_ACCOUNT_ID", "")
    if not secret:
        raise ProductionServiceFault("FINAM_API_SECRET_MISSING")
    if not account:
        raise ProductionServiceFault("FINAM_REAL_ACCOUNT_ID_MISSING")

    lock = InstanceLock(Path(runtime_root) / "state" / "stage8-production.lock")
    lock.acquire()
    service = None
    try:
        service = ProductionService(
            runtime_root=runtime_root,
            data_root=data_root,
            api=api_factory(secret),
            account_id=account,
            accepted_commit=accepted_commit,
            poll_seconds=poll_seconds,
            clock=clock,
        )
        service.connect()
        return service.run(once=once)
    finally:
        if service is not None:
            service.close()
        lock.release()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Stage 8.12.4 authorized FULL/R15 production service"
    )
    parser.add_argument("--runtime-root", type=Path, required=True)
    parser.add_argument("--data-root", type=Path, required=True)
    parser.add_argument("--accepted-commit", required=True)
    parser.add_argument("--poll-seconds", type=int, default=DEFAULT_POLL_SECONDS)
    parser.add_argument("--once", action="store_true")
    args = parser.parse_args(argv)
    try:
        return run_from_environment(
            args.runtime_root,
            args.data_root,
            accepted_commit=args.accepted_commit,
            once=args.once,
            poll_seconds=args.poll_seconds,
        )
    except (
        ProductionServiceFault,
        ProductionRuntimeError,
        ProductionBrokerStateError,
        ProductionHistoryError,
        RuntimeError,
        ValueError,
    ) as exc:
        print(str(exc))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
