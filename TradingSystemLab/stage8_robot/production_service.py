"""Authorized Stage 8.12.4 continuous FINAM production service.

This service only orchestrates frozen authorities already established by Stage
7 and Stages 8.12.1-8.12.4.  It never selects parameters, rounds frozen stops,
accepts partial entries as a new size, or retries an uncertain POST.

Existing broker risk is reconciled and protected before any new signal may be
transmitted.  A HALTED kill switch blocks new entries but does not stop
reconciliation, protective-stop maintenance, or emergency exits.
"""
from __future__ import annotations

import argparse
import hashlib
import os
import time
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any, Callable

import pandas as pd

from .account_cleanliness import TERMINAL_ORDER_STATUSES
from .broker import compact_client_order_id
from .finam_api import FinamAPI, FinamOrderRejected, FinamUncertainSubmission
from .funding_margin_diagnostic import ACTIVE_ACCOUNT_STATUSES, load_production_registry
from .instrument_resolver import (
    MOEX_REFERENCE,
    N4,
    discover_finam_asset,
    parse_rest_value_object,
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
from .production_history import (
    ProductionHistoryError,
    finam_completed_open_h1,
)
from .production_history_store import (
    ProductionHistoryStore,
    ProductionHistoryStoreError,
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
from .specification import INSTRUMENTS
from .strategy_core import CompletedBar

MODE = "STAGE8_12_4_REAL_PRODUCTION"
PRODUCTION_STATE_FILENAME = "stage8-12-production.sqlite3"
LOCK_FILENAME = "stage8-12-4-production.lock"
DEFAULT_POLL_SECONDS = 300
POLL_MIN_SECONDS = 30
POLL_MAX_SECONDS = 3600
DEFAULT_SETTLEMENT_SECONDS = 30
SETTLEMENT_POLL_SECONDS = 1
H1_LOOKBACK_DAYS = 30

MARKET_FILLED = frozenset({"FILLED", "EXECUTED"})
BROKER_REJECTED = frozenset({
    "CANCELLED", "REJECTED", "EXPIRED", "FAILED",
    "DENIED_BY_BROKER", "REJECTED_BY_EXCHANGE", "DISABLED",
})


class ProductionServiceFault(RuntimeError):
    pass


def _fail(code: str) -> None:
    raise ProductionServiceFault(code)


def _required_environment(environment: dict[str, str]) -> tuple[str, str]:
    if environment.get("FINAM_MODE") != MODE:
        _fail("STAGE8_12_4_REAL_PRODUCTION_MODE_REQUIRED")
    secret = environment.get("FINAM_API_SECRET", "")
    account = environment.get("FINAM_REAL_ACCOUNT_ID", "")
    if not secret:
        _fail("STAGE8_12_4_FINAM_API_SECRET_MISSING")
    if not account:
        _fail("STAGE8_12_4_FINAM_REAL_ACCOUNT_ID_MISSING")
    return secret, account


def _order_map(orders: list[BrokerOrderView]) -> dict[str, BrokerOrderView]:
    result: dict[str, BrokerOrderView] = {}
    for order in orders:
        if order.order_id in result:
            _fail("STAGE8_12_4_DUPLICATE_BROKER_ORDER_ID")
        result[order.order_id] = order
    return result


class ProductionService:
    def __init__(
        self,
        runtime_root: Path | str,
        api: Any,
        account_id: str,
        accepted_commit: str,
        *,
        poll_seconds: int = DEFAULT_POLL_SECONDS,
        settlement_seconds: int = DEFAULT_SETTLEMENT_SECONDS,
        clock: Callable[[], datetime] | None = None,
        sleeper: Callable[[float], None] = time.sleep,
        transport_factory=AuthorizedFinamProductionTransport,
    ):
        if not POLL_MIN_SECONDS <= poll_seconds <= POLL_MAX_SECONDS:
            raise ValueError("POLL_SECONDS_OUT_OF_RANGE")
        if not 1 <= settlement_seconds <= 120:
            raise ValueError("SETTLEMENT_SECONDS_OUT_OF_RANGE")
        self.root = Path(runtime_root)
        for name in ("state", "audit", "logs", "diagnostics", "backups", "locks"):
            (self.root / name).mkdir(parents=True, exist_ok=True)
        self.api = api
        self.account_id = str(account_id)
        self.account_hash = hashlib.sha256(self.account_id.encode("utf-8")).hexdigest()
        self.accepted_commit = str(accepted_commit).strip().lower()
        self.poll_seconds = poll_seconds
        self.settlement_seconds = settlement_seconds
        self.clock = clock or (lambda: datetime.now(timezone.utc))
        self.sleeper = sleeper
        self.runtime = ProductionRuntime(self.root / "state" / PRODUCTION_STATE_FILENAME)
        self.history = ProductionHistoryStore(self.root)
        self.transport = transport_factory(
            api=self.api,
            account_id=self.account_id,
            runtime_root=self.root,
            accepted_commit=self.accepted_commit,
        )
        self.logger = configure_operational_log(
            self.root / "logs" / "stage8-12-4-production.log"
        )
        self.authorities: dict[str, InstrumentAuthority] = {}
        self.symbols: dict[str, str] = {}
        self.cycle_count = 0
        self.consecutive_failures = 0
        self.last_api_contact: datetime | None = None
        self.last_protection: list[dict[str, Any]] = []

    def close(self) -> None:
        self.history.close()
        self.runtime.close()
        for handler in self.logger.handlers:
            handler.flush()
            handler.close()
        self.logger.handlers.clear()

    def authenticate_and_bind(self) -> None:
        self.transport.connect()
        details = self.api.session_details()
        if (
            not isinstance(details, dict)
            or details.get("readonly") is not False
            or not isinstance(details.get("account_ids"), list)
            or [str(value) for value in details["account_ids"]].count(self.account_id) != 1
        ):
            _fail("STAGE8_12_4_TRADING_SESSION_AUTHORITY_INVALID")

        frozen_registry = load_production_registry()
        if set(frozen_registry) != set(N4):
            _fail("STAGE8_12_4_FROZEN_REGISTRY_INVALID")
        assets = self.api.assets_all_active()
        if not isinstance(assets, list):
            _fail("STAGE8_12_4_ACTIVE_ASSET_CATALOG_INVALID")

        for instrument in N4:
            frozen = frozen_registry[instrument]
            asset, reason = discover_finam_asset(instrument, assets)
            if reason or not isinstance(asset, dict):
                _fail("STAGE8_12_4_N4_BINDING_INVALID")
            symbol = asset.get("symbol")
            if not isinstance(symbol, str):
                _fail("STAGE8_12_4_N4_BINDING_INVALID")
            params = self.api.asset_params(symbol, self.account_id)
            schedule = self.api.schedule(symbol)
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
                or binding.get("finam_symbol") != frozen.get("finam_symbol")
                or binding.get("mic") != frozen.get("mic")
                or str(binding.get("security_id")) != frozen.get("security_id")
                or str(binding.get("trade_lot_size")) != frozen.get("quantity_granularity")
            ):
                _fail("STAGE8_12_4_N4_BINDING_INVALID")
            step, tick, _ = MOEX_REFERENCE[instrument]
            try:
                lot = int(Decimal(str(binding["trade_lot_size"])))
                long_margin = directional_initial_margin(params, "LONG")
                short_margin = directional_initial_margin(params, "SHORT")
            except (KeyError, ValueError):
                _fail("STAGE8_12_4_N4_MARGIN_AUTHORITY_INVALID")
            authority = InstrumentAuthority(
                instrument, symbol, step, tick, lot, long_margin, short_margin
            )
            self.runtime._validate_instrument_authority(authority)
            self.authorities[instrument] = authority
            self.symbols[instrument] = symbol

    def _snapshot(
        self,
    ) -> tuple[dict[str, Any], dict[str, int], list[BrokerOrderView]]:
        account = self.api.account(self.account_id)
        self.last_api_contact = self.clock().astimezone(timezone.utc)
        if (
            not isinstance(account, dict)
            or account.get("status") not in ACTIVE_ACCOUNT_STATUSES
        ):
            _fail("STAGE8_12_4_ACCOUNT_NOT_ACTIVE")
        try:
            positions = position_quantities(account)
            orders = order_views(self.api.orders(self.account_id))
        except ProductionBrokerStateError as exc:
            raise ProductionServiceFault(str(exc)) from None
        allowed_symbols = set(self.symbols.values())
        if any(symbol not in allowed_symbols for symbol in positions):
            _fail("STAGE8_12_4_UNEXPECTED_NON_N4_POSITION")
        return account, positions, orders

    def _realized_basis(self, account: dict[str, Any]) -> tuple[Decimal, Decimal]:
        try:
            financial = portfolio_authority(account)
            equity = parse_rest_decimal_value_object(account.get("equity"), positive=True)
            unrealized = parse_rest_decimal_value_object(account.get("unrealized_profit"))
        except ValueError:
            _fail("STAGE8_12_4_FINANCIAL_AUTHORITY_INVALID")
        external = Decimal(
            str(self.runtime.store.get("explained_external_cash_flows", "0"))
        )
        basis = equity - unrealized - external
        if not basis.is_finite() or basis <= 0 or financial.available_cash < 0:
            _fail("STAGE8_12_4_FINANCIAL_AUTHORITY_INVALID")
        return basis, financial.available_cash

    def _find_order(
        self, intent: dict[str, Any], orders: list[BrokerOrderView]
    ) -> BrokerOrderView | None:
        broker_id = intent.get("broker_order_id")
        if isinstance(broker_id, str) and broker_id:
            return next((row for row in orders if row.order_id == broker_id), None)
        key = intent.get("idempotency_key")
        if not isinstance(key, str) or not key:
            _fail("STAGE8_12_4_INTENT_IDEMPOTENCY_INVALID")
        try:
            return unique_order_by_client_id(orders, compact_client_order_id(key))
        except ProductionBrokerStateError as exc:
            raise ProductionServiceFault(str(exc)) from None

    def _require_no_unknown_active_orders(
        self, orders: list[BrokerOrderView]
    ) -> None:
        intents = self.runtime.store.all_intents()
        known_ids = {
            intent["broker_order_id"] for intent in intents
            if isinstance(intent.get("broker_order_id"), str)
            and intent["broker_order_id"]
        }
        known_clients = {
            compact_client_order_id(intent["idempotency_key"])
            for intent in intents
            if isinstance(intent.get("idempotency_key"), str)
            and intent["idempotency_key"]
        }
        known_comments = {
            intent["idempotency_key"] for intent in intents
            if isinstance(intent.get("idempotency_key"), str)
            and intent["idempotency_key"]
        }
        for order in orders:
            if not order.active:
                continue
            if (
                order.order_id in known_ids
                or order.client_order_id in known_clients
                or order.comment in known_comments
            ):
                continue
            _fail("STAGE8_12_4_UNEXPECTED_ACTIVE_BROKER_ORDER")

    @staticmethod
    def _runtime_action(payload: dict[str, Any]) -> RuntimeAction:
        return RuntimeAction(
            payload["kind"],
            payload["idempotency_key"],
            payload["instrument"],
            payload["finam_symbol"],
            payload["direction"],
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

    def _latest_stop_matches_state(
        self,
        value: dict[str, Any],
        active: list[BrokerOrderView],
    ) -> None:
        broker_id = value.get("protective_stop_broker_order_id")
        if not isinstance(broker_id, str) or not broker_id:
            _fail("STAGE8_12_4_POSITION_PROTECTIVE_STOP_ID_MISSING")
        current = next((row for row in active if row.order_id == broker_id), None)
        if current is None:
            _fail("STAGE8_12_4_LATEST_PROTECTIVE_STOP_NOT_ACTIVE")
        request = current.request
        expected_side = "SIDE_SELL" if value.get("direction") == "LONG" else "SIDE_BUY"
        try:
            broker_price = parse_rest_value_object(
                request.get("sl_price"), positive=True
            )
            local_price = Decimal(str(value.get("current_stop")))
        except (TypeError, ValueError):
            _fail("STAGE8_12_4_PROTECTIVE_STOP_PRICE_INVALID")
        if current.side != expected_side or broker_price != local_price:
            _fail("STAGE8_12_4_LATEST_PROTECTIVE_STOP_MISMATCH")

    def _position_protection(
        self,
        positions: dict[str, int],
        orders: list[BrokerOrderView],
    ) -> list[dict[str, Any]]:
        protection = []
        local_positions = self.runtime.open_positions()
        local_symbols = {value["finam_symbol"] for value in local_positions.values()}
        unexpected = {
            symbol for symbol, quantity in positions.items()
            if quantity != 0 and symbol not in local_symbols
        }
        if unexpected:
            _fail("STAGE8_12_4_UNEXPECTED_N4_BROKER_POSITION")
        for instrument, value in sorted(local_positions.items()):
            symbol = value["finam_symbol"]
            expected = (
                int(value["quantity"])
                if value["direction"] == "LONG"
                else -int(value["quantity"])
            )
            if positions.get(symbol, 0) != expected:
                _fail("STAGE8_12_4_POSITION_AUTHORITY_MISMATCH")
            try:
                active = active_sltp_for_trade(
                    orders, trade_id=value["trade_id"], symbol=symbol
                )
            except ProductionBrokerStateError as exc:
                raise ProductionServiceFault(str(exc)) from None
            self._latest_stop_matches_state(value, active)
            protection.append({
                "instrument": instrument,
                "trade_id": value["trade_id"],
                "expected_position_quantity": expected,
                "covered_quantity": abs(expected),
                "active_stop_order_ids": sorted(row.order_id for row in active),
            })
        self.last_protection = protection
        return protection

    def _write_heartbeat(
        self,
        *,
        healthy: bool,
        unresolved: int,
        protection: list[dict[str, Any]] | None = None,
    ) -> None:
        write_production_heartbeat(
            self.root,
            accepted_commit=self.accepted_commit,
            account_hash=self.account_hash,
            reconciliation_status="PASS" if healthy else "FAULT",
            unresolved_intent_count=unresolved,
            health_status="HEALTHY" if healthy else "UNHEALTHY",
            cycle_count=self.cycle_count,
            last_api_contact=(
                self.last_api_contact
                or self.clock().astimezone(timezone.utc)
            ),
            position_protection=(
                list(self.last_protection)
                if protection is None else protection
            ),
            now=self.clock().astimezone(timezone.utc),
        )

    def _submit_risk_reducing(
        self, action: RuntimeAction, observed_quantity: int
    ) -> None:
        try:
            if action.kind in {
                "PROTECTIVE_STOP_INSTALL", "PROTECTIVE_STOP_REPLACE"
            }:
                self.transport.submit_protective_stop(
                    action,
                    observed_position_quantity=observed_quantity,
                    state_store=self.runtime.store,
                )
            elif action.kind == "EMERGENCY_EXIT_REQUIRED":
                self.transport.submit_emergency_exit(
                    action,
                    observed_position_quantity=observed_quantity,
                    state_store=self.runtime.store,
                )
            else:
                _fail("STAGE8_12_4_RISK_REDUCING_ACTION_INVALID")
        except FinamOrderRejected:
            if action.kind in {
                "PROTECTIVE_STOP_INSTALL", "PROTECTIVE_STOP_REPLACE"
            }:
                emergency = self.runtime.emergency_exit_for_unprotected_position(
                    action.instrument, reason="PROTECTIVE_STOP_REJECTED"
                )
                self.transport.submit_emergency_exit(
                    emergency,
                    observed_position_quantity=observed_quantity,
                    state_store=self.runtime.store,
                )
            _fail("STAGE8_12_4_RISK_REDUCING_ORDER_REJECTED")
        except FinamUncertainSubmission:
            if action.kind in {
                "PROTECTIVE_STOP_INSTALL", "PROTECTIVE_STOP_REPLACE"
            }:
                emergency = self.runtime.emergency_exit_for_unprotected_position(
                    action.instrument,
                    reason="PROTECTIVE_STOP_SUBMISSION_UNCERTAIN",
                )
                try:
                    self.transport.submit_emergency_exit(
                        emergency,
                        observed_position_quantity=observed_quantity,
                        state_store=self.runtime.store,
                    )
                except (FinamOrderRejected, FinamUncertainSubmission):
                    pass
            _fail("STAGE8_12_4_RISK_REDUCING_SUBMISSION_UNCERTAIN")

    def _reconcile_unresolved(
        self,
        positions: dict[str, int],
        orders: list[BrokerOrderView],
        *,
        allow_missing: bool,
    ) -> bool:
        progress = False
        unresolved = self.runtime.store.unresolved_intents()
        priority = {
            "EMERGENCY_EXIT_REQUIRED": 0,
            "PROTECTIVE_STOP_INSTALL": 1,
            "PROTECTIVE_STOP_REPLACE": 1,
            "ENTRY": 2,
        }
        unresolved.sort(
            key=lambda intent: (
                priority.get(intent.get("payload", {}).get("kind"), 9),
                intent.get("updated_at", ""),
                intent.get("idempotency_key", ""),
            )
        )
        for intent in unresolved:
            payload = intent["payload"]
            kind = payload.get("kind")
            key = intent["idempotency_key"]
            status = intent["status"]
            symbol = payload.get("finam_symbol")
            observed = positions.get(symbol, 0) if isinstance(symbol, str) else 0

            if status == "INTENT_PERSISTED":
                if kind == "ENTRY":
                    _fail(
                        "STAGE8_12_4_PERSISTED_ENTRY_REQUIRES_OPERATOR_RECONCILIATION"
                    )
                action = self._runtime_action(payload)
                self._submit_risk_reducing(action, observed)
                progress = True
                continue

            order = self._find_order(intent, orders)
            if order is None:
                if allow_missing:
                    continue
                _fail("STAGE8_12_4_UNRESOLVED_INTENT_BROKER_ORDER_NOT_FOUND")
            if not intent.get("broker_order_id"):
                self.runtime.store.transition_intent(
                    key, "ACK", order.order_id
                )
                progress = True

            if order.status in BROKER_REJECTED:
                terminal = (
                    "CANCELLED" if order.status == "CANCELLED" else "REJECTED"
                )
                self.runtime.store.transition_intent(
                    key, terminal, order.order_id
                )
                if (
                    kind in {
                        "PROTECTIVE_STOP_INSTALL",
                        "PROTECTIVE_STOP_REPLACE",
                    }
                    and observed
                ):
                    emergency = self.runtime.emergency_exit_for_unprotected_position(
                        payload["instrument"],
                        reason="PROTECTIVE_STOP_TERMINAL_WITH_OPEN_POSITION",
                    )
                    self._submit_risk_reducing(emergency, observed)
                progress = True
                continue

            if kind == "ENTRY":
                expected = int(payload["expected_position_quantity"])
                if order.status in MARKET_FILLED:
                    if observed == expected:
                        stop = self.runtime.confirm_entry_position(key, observed)
                        if stop is not None:
                            self._submit_risk_reducing(stop, observed)
                        progress = True
                    elif observed != 0 and (observed > 0) == (expected > 0):
                        emergency = self.runtime.emergency_exit_for_entry_mismatch(
                            key,
                            observed,
                            reason="PARTIAL_OR_UNEXPECTED_ENTRY_FILL",
                        )
                        self._submit_risk_reducing(emergency, observed)
                        progress = True
                    elif not allow_missing:
                        _fail("STAGE8_12_4_FILLED_ENTRY_POSITION_MISMATCH")
                elif observed != 0:
                    emergency = self.runtime.emergency_exit_for_entry_mismatch(
                        key, observed, reason="PARTIAL_ENTRY_POSITION_OBSERVED"
                    )
                    self._submit_risk_reducing(emergency, observed)
                    progress = True
                continue

            if kind in {
                "PROTECTIVE_STOP_INSTALL", "PROTECTIVE_STOP_REPLACE"
            }:
                try:
                    active = active_sltp_for_trade(
                        orders,
                        trade_id=payload["trade_id"],
                        symbol=payload["finam_symbol"],
                    )
                except ProductionBrokerStateError as exc:
                    raise ProductionServiceFault(str(exc)) from None
                matching = next(
                    (row for row in active if row.order_id == order.order_id),
                    None,
                )
                if matching is not None:
                    self.runtime.confirm_protective_stop(key, order.order_id)
                    progress = True
                elif order.status in TERMINAL_ORDER_STATUSES and observed:
                    emergency = self.runtime.emergency_exit_for_unprotected_position(
                        payload["instrument"],
                        reason="PROTECTIVE_STOP_NOT_ACTIVE",
                    )
                    self._submit_risk_reducing(emergency, observed)
                    progress = True
                continue

            if kind == "EMERGENCY_EXIT_REQUIRED":
                if order.status in MARKET_FILLED and observed == 0:
                    self.runtime.store.transition_intent(
                        key, "RECONCILED", order.order_id
                    )
                    trade_id = payload.get("trade_id")
                    local = self.runtime.open_positions().get(payload.get("instrument"))
                    if local is None and isinstance(trade_id, str):
                        for candidate in self.runtime.store.unresolved_intents():
                            cp = candidate.get("payload", {})
                            if (
                                cp.get("kind") == "ENTRY"
                                and cp.get("trade_id") == trade_id
                            ):
                                self.runtime.store.transition_intent(
                                    candidate["idempotency_key"],
                                    "CLOSED",
                                    candidate.get("broker_order_id"),
                                )
                    progress = True
                elif order.status in MARKET_FILLED and observed != 0:
                    _fail("STAGE8_12_4_EMERGENCY_EXIT_POSITION_STILL_OPEN")
                continue

            _fail("STAGE8_12_4_UNRESOLVED_INTENT_KIND_INVALID")
        return progress

    def _close_broker_flat_positions(
        self,
        positions: dict[str, int],
        orders: list[BrokerOrderView],
        realized_basis: Decimal,
    ) -> bool:
        progress = False
        by_id = _order_map(orders)
        all_intents = self.runtime.store.all_intents()
        for instrument, value in list(self.runtime.open_positions().items()):
            if positions.get(value["finam_symbol"], 0) != 0:
                continue
            related = [
                intent for intent in all_intents
                if intent.get("payload", {}).get("trade_id") == value.get("trade_id")
                and intent.get("payload", {}).get("kind")
                in {"PROTECTIVE_STOP_INSTALL", "PROTECTIVE_STOP_REPLACE"}
                and intent.get("broker_order_id")
            ]
            if not related:
                _fail("STAGE8_12_4_FLAT_POSITION_WITHOUT_STOP_HISTORY")
            all_terminal = True
            for intent in related:
                row = by_id.get(str(intent["broker_order_id"]))
                if row is None:
                    _fail("STAGE8_12_4_PROTECTIVE_STOP_TERMINAL_PROOF_MISSING")
                if row.active:
                    self.transport.cancel_protective_stop_after_flat(
                        row.order_id, observed_position_quantity=0
                    )
                    all_terminal = False
                elif row.status not in TERMINAL_ORDER_STATUSES:
                    all_terminal = False
            if not all_terminal:
                continue
            self.runtime.broker_exit_observed(
                instrument,
                realized_equity_after_exit=realized_basis,
                protective_stop_terminal=True,
            )
            progress = True
        return progress

    def _refresh_history(self, now: datetime) -> dict[str, pd.DataFrame]:
        frames: dict[str, pd.DataFrame] = {}
        start = (
            now.astimezone(timezone.utc) - timedelta(days=H1_LOOKBACK_DAYS)
        ).isoformat()
        for instrument in INSTRUMENTS:
            symbol = self.symbols[instrument]
            schedule = self.api.schedule(symbol)
            try:
                windows = trading_h1_windows(schedule)
            except RuntimeError as exc:
                raise ProductionServiceFault(str(exc)) from None
            response = self.api.bars(
                symbol, start, now.astimezone(timezone.utc).isoformat()
            )
            try:
                live = finam_completed_open_h1(response, now, windows)
                expected = newest_expected_h1_close(schedule, now)
                if expected is not None:
                    expected_moscow = pd.Timestamp(expected).tz_convert(
                        "Europe/Moscow"
                    )
                    if expected_moscow not in live.index:
                        _fail("STAGE8_12_4_H1_DATA_STALE")
                self.history.merge_live(instrument, live)
                frames[instrument] = self.history.close_frame(instrument)
            except (ProductionHistoryError, ProductionHistoryStoreError) as exc:
                raise ProductionServiceFault(str(exc)) from None
        self.last_api_contact = now.astimezone(timezone.utc)
        return frames

    def _manage_existing_positions(
        self,
        frames: dict[str, pd.DataFrame],
        broker_positions: dict[str, int],
        now: datetime,
    ) -> bool:
        for instrument, value in list(self.runtime.open_positions().items()):
            observed = broker_positions.get(value["finam_symbol"], 0)
            execution, _ = self.runtime.context_builder.build(
                frames[instrument], now
            )
            cutoff = (
                self.runtime.store.get(f"last_managed_h1:{instrument}")
                or self.runtime.store.get(f"last_evaluated_h1:{instrument}")
            )
            for stamp, row in execution.iterrows():
                if cutoff is not None and stamp.isoformat() <= cutoff:
                    continue
                if pd.isna(row.ATR):
                    continue
                bar = CompletedBar(
                    stamp.to_pydatetime(),
                    float(row.Open),
                    float(row.High),
                    float(row.Low),
                    float(row.Close),
                    float(row.ATR),
                    None if pd.isna(row.PriorHigh) else float(row.PriorHigh),
                    None if pd.isna(row.PriorLow) else float(row.PriorLow),
                )
                action = self.runtime.manage_completed_bar(
                    instrument, bar, observed_position_quantity=observed
                )
                if action is not None:
                    if action.kind == "BROKER_EXIT_OBSERVED":
                        return True
                    self._submit_risk_reducing(action, observed)
                    return True
        return False

    def _settle_after_entry(self, deadline: datetime) -> bool:
        while self.clock().astimezone(timezone.utc) <= deadline:
            _, positions, orders = self._snapshot()
            self._require_no_unknown_active_orders(orders)
            progress = self._reconcile_unresolved(
                positions, orders, allow_missing=True
            )
            if self.runtime.store.unresolved_intent_count() == 0:
                protection = self._position_protection(positions, orders)
                self._write_heartbeat(
                    healthy=True, unresolved=0, protection=protection
                )
                return True
            if not progress:
                self.sleeper(SETTLEMENT_POLL_SECONDS)
        return False

    def _plan_new_entries(
        self,
        frames: dict[str, pd.DataFrame],
        realized_basis: Decimal,
        available_cash: Decimal,
        now: datetime,
    ) -> None:
        budget = self.runtime.begin_batch(
            realized_equity=realized_basis,
            available_cash=available_cash,
        )
        for instrument in INSTRUMENTS:
            if instrument in self.runtime.open_positions():
                continue
            signal = self.runtime.build_latest_signal(
                instrument, frames[instrument], now
            )
            if signal is None:
                continue
            action = self.runtime.plan_entry(
                signal,
                self.authorities[instrument],
                realized_equity=realized_basis,
                budget=budget,
            )
            if action.kind != "ENTRY":
                continue
            try:
                self.transport.submit_entry(
                    action, now=now, state_store=self.runtime.store
                )
            except FinamOrderRejected:
                _fail("STAGE8_12_4_ENTRY_ORDER_REJECTED")
            except FinamUncertainSubmission:
                _fail("STAGE8_12_4_ENTRY_SUBMISSION_UNCERTAIN")
            self._write_heartbeat(
                healthy=False,
                unresolved=self.runtime.store.unresolved_intent_count(),
            )
            deadline = self.clock().astimezone(timezone.utc) + timedelta(
                seconds=self.settlement_seconds
            )
            if not self._settle_after_entry(deadline):
                _fail("STAGE8_12_4_ENTRY_PROTECTION_SETTLEMENT_TIMEOUT")

    def cycle(self) -> None:
        now = self.clock().astimezone(timezone.utc)
        account, positions, orders = self._snapshot()
        self._require_no_unknown_active_orders(orders)
        realized_basis, available_cash = self._realized_basis(account)

        local_positions = self.runtime.open_positions()
        persisted = self.runtime.current_realized_equity()
        broker_flat_local = any(
            positions.get(value["finam_symbol"], 0) == 0
            for value in local_positions.values()
        )
        if persisted is None:
            if (
                local_positions
                or self.runtime.store.unresolved_intent_count()
                or positions
            ):
                _fail("STAGE8_12_4_REALIZED_EQUITY_INITIALIZATION_NOT_CLEAN")
            self.runtime.set_realized_equity(realized_basis)
            persisted = realized_basis
        elif realized_basis != persisted and not broker_flat_local:
            _fail("STAGE8_12_4_UNEXPLAINED_REALIZED_EQUITY_DISCREPANCY")

        for _ in range(8):
            progress = self._reconcile_unresolved(
                positions, orders, allow_missing=False
            )
            if not progress:
                break
            account, positions, orders = self._snapshot()
            self._require_no_unknown_active_orders(orders)
        if self.runtime.store.unresolved_intent_count():
            _fail("STAGE8_12_4_UNRESOLVED_INTENT_REMAINS")

        if self._close_broker_flat_positions(
            positions, orders, realized_basis
        ):
            account, positions, orders = self._snapshot()
            realized_basis, available_cash = self._realized_basis(account)
            if self.runtime.current_realized_equity() != realized_basis:
                _fail("STAGE8_12_4_REALIZED_EQUITY_POST_EXIT_MISMATCH")

        protection = self._position_protection(positions, orders)
        frames = self._refresh_history(now)

        if self._manage_existing_positions(frames, positions, now):
            self._write_heartbeat(
                healthy=False,
                unresolved=self.runtime.store.unresolved_intent_count(),
                protection=protection,
            )
            return
        if self.runtime.store.unresolved_intent_count():
            _fail("STAGE8_12_4_UNRESOLVED_INTENT_AFTER_BAR_MANAGEMENT")

        account, positions, orders = self._snapshot()
        self._require_no_unknown_active_orders(orders)
        realized_basis, available_cash = self._realized_basis(account)
        if self.runtime.current_realized_equity() != realized_basis:
            _fail("STAGE8_12_4_REALIZED_EQUITY_PRE_ENTRY_MISMATCH")
        protection = self._position_protection(positions, orders)

        self.cycle_count += 1
        self.consecutive_failures = 0
        self._write_heartbeat(healthy=True, unresolved=0, protection=protection)
        gate = evaluate_production_entry_gate(
            runtime_root=self.root,
            now=now,
            expected_commit=self.accepted_commit,
            expected_account_hash=self.account_hash,
            execution_authorized=True,
        )
        if gate.get("entry_gate_open") is True:
            self._plan_new_entries(
                frames, realized_basis, available_cash, now
            )
        else:
            reasons = set(gate.get("reason_codes") or [])
            if reasons != {"KILL_SWITCH_NOT_ARMED"}:
                _fail("STAGE8_12_4_PRODUCTION_ENTRY_GATE_INVALID")
            self.logger.info("PRODUCTION_NEW_ENTRIES_HALTED")
        self.logger.info(
            "PRODUCTION_CYCLE_PASS cycle=%d open_positions=%d",
            self.cycle_count,
            len(self.runtime.open_positions()),
        )

    def run(self, *, once: bool = False) -> int:
        while True:
            try:
                self.cycle()
            except ProductionServiceFault as exc:
                self.consecutive_failures += 1
                try:
                    self._write_heartbeat(
                        healthy=False,
                        unresolved=self.runtime.store.unresolved_intent_count(),
                    )
                except Exception:
                    pass
                self.logger.error("PRODUCTION_SAFETY_FAULT code=%s", str(exc))
                return 1
            except Exception:
                self.consecutive_failures += 1
                try:
                    self._write_heartbeat(
                        healthy=False,
                        unresolved=self.runtime.store.unresolved_intent_count(),
                    )
                except Exception:
                    pass
                self.logger.exception("PRODUCTION_OPERATIONAL_FAILURE")
                return 1
            if once:
                return 0
            self.sleeper(self.poll_seconds)


def run_from_environment(
    runtime_root: Path,
    accepted_commit: str,
    *,
    once: bool = False,
    poll_seconds: int = DEFAULT_POLL_SECONDS,
    api_factory=FinamAPI,
    environment: dict[str, str] | None = None,
    clock: Callable[[], datetime] | None = None,
) -> int:
    environment = dict(os.environ if environment is None else environment)
    secret, account = _required_environment(environment)
    lock = InstanceLock(Path(runtime_root) / "locks" / LOCK_FILENAME)
    lock.acquire()
    service = None
    try:
        service = ProductionService(
            runtime_root,
            api_factory(secret),
            account,
            accepted_commit,
            poll_seconds=poll_seconds,
            clock=clock,
        )
        service.authenticate_and_bind()
        return service.run(once=once)
    finally:
        if service is not None:
            service.close()
        lock.release()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Stage 8.12.4 authorized FINAM production service"
    )
    parser.add_argument("--runtime-root", type=Path, required=True)
    parser.add_argument("--accepted-commit", required=True)
    parser.add_argument("--once", action="store_true")
    parser.add_argument(
        "--poll-seconds", type=int, default=DEFAULT_POLL_SECONDS
    )
    args = parser.parse_args(argv)
    try:
        return run_from_environment(
            args.runtime_root,
            args.accepted_commit,
            once=args.once,
            poll_seconds=args.poll_seconds,
        )
    except (
        ProductionServiceFault,
        ProductionRuntimeError,
        ProductionHistoryError,
        ProductionHistoryStoreError,
        RuntimeError,
        ValueError,
    ) as exc:
        print(str(exc))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
