"""Authorized Stage 8.12.4 continuous production service.

The service composes already-frozen Stage-7/Stage-8 authorities.  It does not
select strategy parameters, change sizing, round stops, or infer broker state.

Ordering per cycle:
1. exact account/order/position reconciliation;
2. settle any risk-reducing persisted work;
3. close broker-flat local positions only after protective-stop terminal proof;
4. refresh causal H1 history and manage existing positions;
5. publish a healthy production heartbeat;
6. evaluate new signals and, one at a time, require FILLED position + ACTIVE
   protective stop before another N4 entry may be transmitted.
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
    ProductionBrokerStateError,
    by_broker_id,
    by_client_id,
    client_order_id,
    is_active,
    is_filled,
    is_rejected,
    is_terminal,
    normalized_status,
    order_comment,
    order_id,
    order_rows,
    position_quantity_map,
)
from .production_history import ProductionHistoryCache, ProductionHistoryError
from .production_runtime import (
    InstrumentAuthority,
    ProductionRuntime,
    ProductionRuntimeError,
    RuntimeAction,
)
from .production_safety_gate import write_production_heartbeat
from .specification import ACTIVE_IDENTITY, INSTRUMENTS, PRODUCTION_SPECIFICATION_ID

MODE = "STAGE8_12_4_REAL_PRODUCTION"
PRODUCTION_STATE_FILENAME = "stage8-12-production.sqlite3"
LOCK_FILENAME = "stage8-12-4-production.lock"
DEFAULT_POLL_SECONDS = 300
POLL_MIN_SECONDS = 30
POLL_MAX_SECONDS = 3600
DEFAULT_SETTLEMENT_SECONDS = 30
SETTLEMENT_POLL_SECONDS = 1
H1_LOOKBACK_DAYS = 30


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


def _broker_order_id(result: Any) -> str:
    if not isinstance(result, dict):
        _fail("STAGE8_12_4_BROKER_ACK_INVALID")
    value = result.get("order_id") or result.get("orderId")
    if not isinstance(value, str) or not value:
        _fail("STAGE8_12_4_BROKER_ACK_ORDER_ID_MISSING")
    return value


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
    ):
        if not POLL_MIN_SECONDS <= poll_seconds <= POLL_MAX_SECONDS:
            raise ValueError("POLL_SECONDS_OUT_OF_RANGE")
        if settlement_seconds < 1 or settlement_seconds > 120:
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
        self.runtime = ProductionRuntime(
            self.root / "state" / PRODUCTION_STATE_FILENAME
        )
        self.history = ProductionHistoryCache(self.root)
        self.transport = AuthorizedFinamProductionTransport(
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
        self._last_position_protection: list[dict[str, Any]] = []

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

        production_registry = load_production_registry()
        if set(production_registry) != set(N4):
            _fail("STAGE8_12_4_FROZEN_REGISTRY_INVALID")
        assets = self.api.assets_all_active()
        if not isinstance(assets, list):
            _fail("STAGE8_12_4_ACTIVE_ASSET_CATALOG_INVALID")

        for instrument in N4:
            frozen = production_registry[instrument]
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
                instrument=instrument,
                finam_symbol=symbol,
                price_step=step,
                tick_value=tick,
                trade_lot_size=lot,
                long_initial_margin=long_margin,
                short_initial_margin=short_margin,
            )
            self.runtime._validate_instrument_authority(authority)
            self.authorities[instrument] = authority
            self.symbols[instrument] = symbol

    def _snapshot(self) -> tuple[dict[str, Any], dict[str, int], list[dict[str, Any]]]:
        account = self.api.account(self.account_id)
        self.last_api_contact = self.clock().astimezone(timezone.utc)
        if not isinstance(account, dict) or account.get("status") not in ACTIVE_ACCOUNT_STATUSES:
            _fail("STAGE8_12_4_ACCOUNT_NOT_ACTIVE")
        try:
            positions = position_quantity_map(account)
            orders = order_rows(self.api.orders(self.account_id))
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
        external = Decimal(str(self.runtime.store.get("explained_external_cash_flows", "0")))
        basis = equity - unrealized - external
        if not basis.is_finite() or basis <= 0 or financial.available_cash < 0:
            _fail("STAGE8_12_4_FINANCIAL_AUTHORITY_INVALID")
        return basis, financial.available_cash

    def _find_broker_order(
        self,
        intent: dict[str, Any],
        rows_by_broker: dict[str, dict[str, Any]],
        rows_by_client: dict[str, dict[str, Any]],
    ) -> dict[str, Any] | None:
        broker_id = intent.get("broker_order_id")
        if isinstance(broker_id, str) and broker_id:
            return rows_by_broker.get(broker_id)
        key = intent["idempotency_key"]
        return rows_by_client.get(compact_client_order_id(key))

    def _known_active_order_ids(self, rows: list[dict[str, Any]]) -> set[str]:
        intents = self.runtime.store.intents()
        known_broker_ids = {
            str(intent["broker_order_id"])
            for intent in intents
            if isinstance(intent.get("broker_order_id"), str)
            and intent["broker_order_id"]
        }
        known_client_ids = {
            compact_client_order_id(intent["idempotency_key"])
            for intent in intents
            if isinstance(intent.get("idempotency_key"), str)
            and intent["idempotency_key"]
        }
        known_comments = {
            intent["idempotency_key"]
            for intent in intents
            if isinstance(intent.get("idempotency_key"), str)
            and intent["idempotency_key"]
        }
        unexpected = set()
        for row in rows:
            if not is_active(row):
                continue
            if (
                order_id(row) in known_broker_ids
                or client_order_id(row) in known_client_ids
                or order_comment(row) in known_comments
            ):
                continue
            unexpected.add(order_id(row))
        if unexpected:
            _fail("STAGE8_12_4_UNEXPECTED_ACTIVE_BROKER_ORDER")
        return known_broker_ids

    def _verify_stop_row(self, row: dict[str, Any], intent: dict[str, Any]) -> None:
        payload = row.get("sltp_order")
        local = intent.get("payload")
        if not isinstance(payload, dict) or not isinstance(local, dict):
            _fail("STAGE8_12_4_PROTECTIVE_STOP_BROKER_SCHEMA_INVALID")
        expected_side = "SIDE_SELL" if local.get("direction") == "LONG" else "SIDE_BUY"
        measure = payload.get("sl_qty_measure")
        try:
            quantity = parse_rest_value_object(payload.get("quantity_sl"), positive=True)
            price = parse_rest_value_object(payload.get("sl_price"), positive=True)
            expected_price = Decimal(str(local.get("stop_price")))
        except (TypeError, ValueError):
            _fail("STAGE8_12_4_PROTECTIVE_STOP_BROKER_SCHEMA_INVALID")
        if (
            payload.get("symbol") != local.get("finam_symbol")
            or payload.get("side") != expected_side
            or quantity != Decimal("100")
            or measure != "SLTP_QTY_MEASURE_PERCENT"
            or price != expected_price
            or order_comment(row) != intent["idempotency_key"]
        ):
            _fail("STAGE8_12_4_PROTECTIVE_STOP_BROKER_MISMATCH")

    def _position_protection(
        self,
        positions: dict[str, int],
        orders: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        by_id = by_broker_id(orders)
        protection = []
        local_positions = self.runtime.open_positions()
        all_intents = self.runtime.store.intents()
        for instrument, value in sorted(local_positions.items()):
            symbol = value["finam_symbol"]
            expected = int(value["quantity"]) if value["direction"] == "LONG" else -int(value["quantity"])
            if positions.get(symbol, 0) != expected:
                _fail("STAGE8_12_4_POSITION_AUTHORITY_MISMATCH")
            active_stop_ids = []
            for intent in all_intents:
                payload = intent.get("payload", {})
                if (
                    payload.get("trade_id") != value.get("trade_id")
                    or payload.get("kind") not in {"PROTECTIVE_STOP_INSTALL", "PROTECTIVE_STOP_REPLACE"}
                    or not intent.get("broker_order_id")
                ):
                    continue
                row = by_id.get(str(intent["broker_order_id"]))
                if row is None:
                    continue
                self._verify_stop_row(row, intent)
                if is_active(row):
                    active_stop_ids.append(order_id(row))
            if not active_stop_ids:
                _fail("STAGE8_12_4_POSITION_UNPROTECTED")
            protection.append({
                "instrument": instrument,
                "trade_id": value["trade_id"],
                "expected_position_quantity": expected,
                "covered_quantity": abs(expected),
                "active_stop_order_ids": sorted(active_stop_ids),
            })
        self._last_position_protection = protection
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
            last_api_contact=self.last_api_contact or self.clock().astimezone(timezone.utc),
            position_protection=(
                list(self._last_position_protection)
                if protection is None
                else protection
            ),
            now=self.clock().astimezone(timezone.utc),
        )

    def _transition_rejected(self, intent: dict[str, Any], row: dict[str, Any]) -> None:
        status = normalized_status(row)
        terminal = "CANCELLED" if status == "CANCELLED" else "REJECTED"
        self.runtime.store.transition_intent(
            intent["idempotency_key"], terminal, order_id(row)
        )

    def _submit_risk_reducing(
        self,
        action: RuntimeAction,
        observed_quantity: int,
    ) -> None:
        try:
            if action.kind in {"PROTECTIVE_STOP_INSTALL", "PROTECTIVE_STOP_REPLACE"}:
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
            if action.kind in {"PROTECTIVE_STOP_INSTALL", "PROTECTIVE_STOP_REPLACE"}:
                emergency = self.runtime.emergency_exit_for_unprotected_position(
                    action.instrument,
                    reason="PROTECTIVE_STOP_REJECTED",
                )
                self.transport.submit_emergency_exit(
                    emergency,
                    observed_position_quantity=observed_quantity,
                    state_store=self.runtime.store,
                )
            raise ProductionServiceFault("STAGE8_12_4_RISK_REDUCING_ORDER_REJECTED") from None
        except FinamUncertainSubmission:
            if action.kind in {"PROTECTIVE_STOP_INSTALL", "PROTECTIVE_STOP_REPLACE"}:
                emergency = self.runtime.emergency_exit_for_unprotected_position(
                    action.instrument,
                    reason="PROTECTIVE_STOP_SUBMISSION_UNCERTAIN",
                )
                self.transport.submit_emergency_exit(
                    emergency,
                    observed_position_quantity=observed_quantity,
                    state_store=self.runtime.store,
                )
            raise ProductionServiceFault("STAGE8_12_4_RISK_REDUCING_SUBMISSION_UNCERTAIN") from None

    def _reconcile_unresolved(
        self,
        positions: dict[str, int],
        orders: list[dict[str, Any]],
    ) -> bool:
        by_id = by_broker_id(orders)
        by_client = by_client_id(orders)
        progress = False
        for intent in self.runtime.store.intents(unresolved_only=True):
            payload = intent["payload"]
            kind = payload.get("kind")
            key = intent["idempotency_key"]
            status = intent["status"]
            symbol = payload.get("finam_symbol")
            observed = positions.get(symbol, 0) if isinstance(symbol, str) else 0

            if status == "INTENT_PERSISTED":
                if kind == "ENTRY":
                    _fail("STAGE8_12_4_PERSISTED_ENTRY_REQUIRES_OPERATOR_RECONCILIATION")
                action = self.runtime._protective_stop_action_from_payload(payload)
                if kind == "EMERGENCY_EXIT_REQUIRED":
                    action = RuntimeAction(
                        "EMERGENCY_EXIT_REQUIRED", key, payload["instrument"],
                        payload["finam_symbol"], payload["direction"],
                        int(payload["quantity"]), payload.get("trade_id"),
                        payload.get("signal_id"),
                        Decimal(str(payload["reference_price"])),
                        Decimal(str(payload["stop_price"])), 0,
                        payload.get("reason"),
                    )
                self._submit_risk_reducing(action, observed)
                progress = True
                continue

            row = self._find_broker_order(intent, by_id, by_client)
            if row is None:
                _fail("STAGE8_12_4_UNRESOLVED_INTENT_BROKER_ORDER_NOT_FOUND")
            broker_id = order_id(row)
            if intent.get("broker_order_id") in (None, ""):
                self.runtime.store.transition_intent(key, "ACK", broker_id)
                intent = self.runtime.store.intent(key) | {"idempotency_key": key}
                progress = True

            if is_rejected(row) or normalized_status(row) == "CANCELLED":
                self._transition_rejected(intent, row)
                if kind in {"PROTECTIVE_STOP_INSTALL", "PROTECTIVE_STOP_REPLACE"} and observed:
                    emergency = self.runtime.emergency_exit_for_unprotected_position(
                        payload["instrument"], reason="PROTECTIVE_STOP_TERMINAL_WITH_OPEN_POSITION"
                    )
                    self._submit_risk_reducing(emergency, observed)
                progress = True
                continue

            if kind == "ENTRY":
                expected = int(payload["expected_position_quantity"])
                if is_filled(row):
                    if observed == expected:
                        stop = self.runtime.confirm_entry_position(key, observed)
                        if stop is not None:
                            self._submit_risk_reducing(stop, observed)
                        progress = True
                    elif observed != 0 and (observed > 0) == (expected > 0):
                        emergency = self.runtime.emergency_exit_for_entry_mismatch(
                            key, observed, reason="PARTIAL_OR_UNEXPECTED_ENTRY_FILL"
                        )
                        self._submit_risk_reducing(emergency, observed)
                        progress = True
                    else:
                        _fail("STAGE8_12_4_FILLED_ENTRY_POSITION_MISMATCH")
                elif observed != 0:
                    emergency = self.runtime.emergency_exit_for_entry_mismatch(
                        key, observed, reason="PARTIAL_ENTRY_POSITION_OBSERVED"
                    )
                    self._submit_risk_reducing(emergency, observed)
                    progress = True
                continue

            if kind in {"PROTECTIVE_STOP_INSTALL", "PROTECTIVE_STOP_REPLACE"}:
                self._verify_stop_row(row, intent)
                if is_active(row):
                    self.runtime.confirm_protective_stop(key, broker_id)
                    progress = True
                elif is_terminal(row) and observed:
                    emergency = self.runtime.emergency_exit_for_unprotected_position(
                        payload["instrument"], reason="PROTECTIVE_STOP_NOT_ACTIVE"
                    )
                    self._submit_risk_reducing(emergency, observed)
                    progress = True
                continue

            if kind == "EMERGENCY_EXIT_REQUIRED":
                if is_filled(row) and observed == 0:
                    self.runtime.store.transition_intent(key, "RECONCILED", broker_id)
                    progress = True
                elif is_filled(row) and observed != 0:
                    _fail("STAGE8_12_4_EMERGENCY_EXIT_POSITION_STILL_OPEN")
                continue

            _fail("STAGE8_12_4_UNRESOLVED_INTENT_KIND_INVALID")
        return progress

    def _terminalize_flat_positions(
        self,
        account: dict[str, Any],
        positions: dict[str, int],
        orders: list[dict[str, Any]],
        realized_basis: Decimal,
    ) -> bool:
        progress = False
        by_id = by_broker_id(orders)
        intents = self.runtime.store.intents()
        for instrument, value in list(self.runtime.open_positions().items()):
            symbol = value["finam_symbol"]
            if positions.get(symbol, 0) != 0:
                continue
            related = [
                intent for intent in intents
                if intent.get("payload", {}).get("trade_id") == value.get("trade_id")
                and intent.get("payload", {}).get("kind") in {
                    "PROTECTIVE_STOP_INSTALL", "PROTECTIVE_STOP_REPLACE"
                }
                and intent.get("broker_order_id")
            ]
            if not related:
                _fail("STAGE8_12_4_FLAT_POSITION_WITHOUT_PROTECTIVE_STOP_HISTORY")
            all_terminal = True
            for intent in related:
                row = by_id.get(str(intent["broker_order_id"]))
                if row is None:
                    _fail("STAGE8_12_4_PROTECTIVE_STOP_TERMINAL_PROOF_MISSING")
                self._verify_stop_row(row, intent)
                if is_active(row):
                    self.transport.cancel_protective_stop_after_flat(
                        order_id(row), observed_position_quantity=0
                    )
                    all_terminal = False
                elif not is_terminal(row):
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
        frames = {}
        start = (now.astimezone(timezone.utc) - timedelta(days=H1_LOOKBACK_DAYS)).isoformat()
        for instrument in INSTRUMENTS:
            symbol = self.symbols[instrument]
            schedule = self.api.schedule(symbol)
            response = self.api.bars(symbol, start, now.astimezone(timezone.utc).isoformat())
            try:
                self.history.merge_finam_tail(
                    instrument=instrument,
                    response=response,
                    schedule=schedule,
                    now=now,
                )
                frames[instrument] = self.history.frame(instrument)
            except ProductionHistoryError as exc:
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
            symbol = value["finam_symbol"]
            observed = broker_positions.get(symbol, 0)
            execution, _ = self.runtime.context_builder.build(frames[instrument], now)
            cutoff = (
                self.runtime.store.get(f"last_managed_h1:{instrument}")
                or self.runtime.store.get(f"last_evaluated_h1:{instrument}")
            )
            for stamp, row in execution.iterrows():
                if cutoff is not None and stamp.isoformat() <= cutoff:
                    continue
                from .strategy_core import CompletedBar
                bar = CompletedBar(
                    stamp.to_pydatetime(),
                    float(row.Open), float(row.High), float(row.Low), float(row.Close),
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
            account, positions, orders = self._snapshot()
            self._known_active_order_ids(orders)
            progress = self._reconcile_unresolved(positions, orders)
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
            signal = self.runtime.build_latest_signal(instrument, frames[instrument], now)
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
                continue
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
        self._known_active_order_ids(orders)
        realized_basis, available_cash = self._realized_basis(account)
        local_positions = self.runtime.open_positions()
        persisted = self.runtime.current_realized_equity()
        broker_flat_local = any(
            positions.get(value["finam_symbol"], 0) == 0
            for value in local_positions.values()
        )
        if persisted is None:
            if local_positions or self.runtime.store.unresolved_intent_count() or positions:
                _fail("STAGE8_12_4_REALIZED_EQUITY_INITIALIZATION_NOT_CLEAN")
            self.runtime.set_realized_equity(realized_basis)
            persisted = realized_basis
        elif realized_basis != persisted and not broker_flat_local:
            _fail("STAGE8_12_4_UNEXPLAINED_REALIZED_EQUITY_DISCREPANCY")

        # Resolve/reduce existing broker risk before strategy progression.
        for _ in range(8):
            progress = self._reconcile_unresolved(positions, orders)
            if not progress:
                break
            account, positions, orders = self._snapshot()
            self._known_active_order_ids(orders)
        if self.runtime.store.unresolved_intent_count():
            _fail("STAGE8_12_4_UNRESOLVED_INTENT_REMAINS")

        if self._terminalize_flat_positions(
            account, positions, orders, realized_basis
        ):
            account, positions, orders = self._snapshot()
            realized_basis, available_cash = self._realized_basis(account)
            if self.runtime.current_realized_equity() != realized_basis:
                _fail("STAGE8_12_4_REALIZED_EQUITY_POST_EXIT_MISMATCH")

        protection = self._position_protection(positions, orders)
        frames = self._refresh_history(now)

        # Existing positions always consume completed bars before new entries.
        if self._manage_existing_positions(frames, positions, now):
            self._write_heartbeat(
                healthy=False,
                unresolved=self.runtime.store.unresolved_intent_count(),
                protection=protection,
            )
            return
        if self.runtime.store.unresolved_intent_count():
            _fail("STAGE8_12_4_UNRESOLVED_INTENT_AFTER_BAR_MANAGEMENT")

        # Re-snapshot before opening the entry gate.
        account, positions, orders = self._snapshot()
        realized_basis, available_cash = self._realized_basis(account)
        if self.runtime.current_realized_equity() != realized_basis:
            _fail("STAGE8_12_4_REALIZED_EQUITY_PRE_ENTRY_MISMATCH")
        protection = self._position_protection(positions, orders)
        self.cycle_count += 1
        self.consecutive_failures = 0
        self._write_heartbeat(healthy=True, unresolved=0, protection=protection)
        self._plan_new_entries(
            frames, realized_basis, available_cash, now
        )
        self.logger.info(
            "PRODUCTION_CYCLE_PASS cycle=%d open_positions=%d",
            self.cycle_count, len(self.runtime.open_positions())
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
    parser = argparse.ArgumentParser(description="Stage 8.12.4 authorized FINAM production service")
    parser.add_argument("--runtime-root", type=Path, required=True)
    parser.add_argument("--accepted-commit", required=True)
    parser.add_argument("--once", action="store_true")
    parser.add_argument("--poll-seconds", type=int, default=DEFAULT_POLL_SECONDS)
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
        RuntimeError,
        ValueError,
    ) as exc:
        print(str(exc))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
