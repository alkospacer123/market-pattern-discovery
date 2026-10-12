"""Continuous Stage 8.12.4 FINAM production service.

Before durable authorization this service is deliberately order-incapable: it
uses the exact production trading credential for GET/reconciliation, but does
not construct AuthorizedFinamProductionTransport and does not evaluate/consume
new entry signals. After later explicit authorization the same service path can
submit only through the already-audited transport and production entry gate.
"""
from __future__ import annotations

import argparse
import hashlib
import os
import time
from dataclasses import dataclass, replace
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any, Callable

import pandas as pd

from .account_cleanliness import TERMINAL_ORDER_STATUSES
from .broker import compact_client_order_id
from .finam_api import FinamAPI, FinamOrderRejected, FinamUncertainSubmission
from .live_execution import AuthorizedFinamProductionTransport, EntryPrePostRefused, LiveExecutionError
from .margin import directional_initial_margin, parse_rest_decimal_value_object, portfolio_authority
from .operations import InstanceLock, configure_operational_log
from .production_authorization import authorization_path, load_authorization
from .production_broker_state import (
    BrokerOrderView,
    active_sltp_for_trade,
    order_views,
    position_quantities,
    unique_order_by_client_id,
)
from .production_history import (
    STAGE5_DATA_COMMIT,
    close_index_for_frozen_t3,
    extend_rolling_open_h1,
    finam_completed_open_h1,
    load_stage5_seed_open_h1,
)
from .production_runtime import InstrumentAuthority, ProductionRuntime, RuntimeAction
from .production_safety_gate import evaluate_production_entry_gate, write_production_heartbeat
from .readonly_supervisor import newest_expected_h1_close, trading_h1_windows
from .specification import ACTIVE_IDENTITY, INSTRUMENTS, PRODUCTION_SPECIFICATION_ID, load_frozen_specification
from .strategy_core import CompletedBar
from .execution_grid import EXECUTION_REVISION, FINAM_FILL_AUTHORITY_VERIFIED

MODE = "STAGE8_12_PRODUCTION"
STATE_DATABASE = "stage8-12-production.sqlite3"
INSTANCE_LOCK = "stage8-12-production.lock"
LOG_FILE = "stage8-12-production.log"
H1_LOOKBACK_DAYS = 30
DEFAULT_POLL_SECONDS = 30
FAST_RECONCILIATION_SECONDS = 3
ENTRY_MINIMUM_REMAINING_SESSION = timedelta(minutes=5)
ACTIVE_ACCOUNT_STATUSES = frozenset({"ACCOUNT_ACTIVE", "ACCOUNT_STATUS_ACTIVE"})


class ProductionServiceError(RuntimeError):
    pass


@dataclass(frozen=True)
class Snapshot:
    account: dict[str, Any]
    positions: dict[str, int]
    orders: list[BrokerOrderView]
    realized_equity: Decimal
    available_cash: Decimal
    observed_at: datetime


def _order_id(response: Any) -> str:
    value = response.get("order_id") if isinstance(response, dict) else None
    if not isinstance(value, str) or not value:
        raise ProductionServiceError("STAGE8_12_4_ORDER_ACK_INVALID")
    return value


def _action(payload: dict[str, Any]) -> RuntimeAction:
    try:
        return RuntimeAction(
            payload["kind"], payload.get("idempotency_key"), payload["instrument"],
            payload["finam_symbol"], payload.get("direction"), int(payload["quantity"]),
            payload.get("trade_id"), payload.get("signal_id"),
            None if payload.get("reference_price") is None else Decimal(str(payload["reference_price"])),
            None if payload.get("stop_price") is None else Decimal(str(payload["stop_price"])),
            payload.get("expected_position_quantity"), payload.get("reason"),
            payload.get("execution_revision"),
            None if payload.get("price_step") is None else Decimal(payload["price_step"]),
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise ProductionServiceError("STAGE8_12_4_INTENT_PAYLOAD_INVALID") from exc


def _expected_side(action: RuntimeAction, *, exit_order: bool) -> str:
    if action.direction not in {"LONG", "SHORT"}:
        raise ProductionServiceError("STAGE8_12_4_DIRECTION_INVALID")
    buy = action.direction == "LONG"
    if exit_order:
        buy = not buy
    return "SIDE_BUY" if buy else "SIDE_SELL"


class ProductionService:
    def __init__(
        self, runtime_root: Path, stage5_data_root: Path, api: Any, account_id: str,
        accepted_commit: str, *, poll_seconds: int = DEFAULT_POLL_SECONDS,
        clock: Callable[[], datetime] | None = None,
        sleeper: Callable[[float], None] = time.sleep,
        execution_revision: str | None = None,
    ):
        spec = load_frozen_specification()
        if spec.production_id != PRODUCTION_SPECIFICATION_ID or spec.identity != ACTIVE_IDENTITY:
            raise ProductionServiceError("STAGE8_12_4_FROZEN_PRODUCTION_AUTHORITY_INVALID")
        commit = str(accepted_commit).strip().lower()
        if len(commit) != 40 or any(ch not in "0123456789abcdef" for ch in commit):
            raise ProductionServiceError("STAGE8_12_4_COMMIT_INVALID")
        if not account_id or not 5 <= poll_seconds <= 3600:
            raise ProductionServiceError("STAGE8_12_4_SERVICE_CONFIGURATION_INVALID")

        self.root = Path(runtime_root).resolve()
        self.stage5_data_root = Path(stage5_data_root).resolve()
        self.api = api
        self.account_id = str(account_id)
        self.account_hash = hashlib.sha256(self.account_id.encode("utf-8")).hexdigest()
        self.accepted_commit = commit
        self.poll_seconds = poll_seconds
        self.clock = clock or (lambda: datetime.now(timezone.utc))
        self.sleeper = sleeper
        for name in ("state", "audit", "logs", "diagnostics", "backups", "safety"):
            (self.root / name).mkdir(parents=True, exist_ok=True)
        self.runtime = ProductionRuntime(self.root / "state" / STATE_DATABASE,
                                         execution_revision=execution_revision)
        self.logger = configure_operational_log(self.root / "logs" / LOG_FILE)
        self.transport: AuthorizedFinamProductionTransport | None = None
        self.cycle_count = int(self.runtime.store.get("production_service_cycle_count", 0) or 0)
        self.last_api_contact: datetime | None = None
        identity = {
            "production_specification_id": PRODUCTION_SPECIFICATION_ID,
            "active_identity": ACTIVE_IDENTITY,
            "account_hash": self.account_hash,
            "stage5_data_commit": STAGE5_DATA_COMMIT,
        }
        prior = self.runtime.store.get("production_service_identity")
        if prior is not None and prior != identity:
            raise ProductionServiceError("STAGE8_12_4_SERVICE_IDENTITY_MISMATCH")
        self.runtime.store.put("production_service_identity", identity)
        if self.runtime.store.get("explained_external_cash_flows") is None:
            self.runtime.store.put("explained_external_cash_flows", "0")

    def close(self) -> None:
        self.runtime.close()
        for handler in tuple(self.logger.handlers):
            handler.flush()
            handler.close()
        self.logger.handlers.clear()

    def authenticate(self) -> None:
        """Never construct an order-capable adapter while authorization is absent."""
        if authorization_path(self.root).exists():
            load_authorization(
                self.root,
                expected_commit=self.accepted_commit,
                expected_account_hash=self.account_hash,
            )
            self.transport = AuthorizedFinamProductionTransport(
                api=self.api, account_id=self.account_id, runtime_root=self.root,
                accepted_commit=self.accepted_commit,
            )
            self.transport.connect()
            return

        self.api.create_session()
        details = self.api.session_details()
        ids = details.get("account_ids") if isinstance(details, dict) else None
        if not isinstance(ids, list) or [str(value) for value in ids].count(self.account_id) != 1:
            raise ProductionServiceError("STAGE8_12_4_ACCOUNT_NOT_EXACTLY_ENUMERATED")
        if details.get("readonly") is not False:
            raise ProductionServiceError("STAGE8_12_4_TRADING_TOKEN_NOT_WRITE_CAPABLE")
        self.api.account(self.account_id)
        self.transport = None

    def _realized_basis(
        self,
        account: dict[str, Any],
        positions: dict[str, int],
        orders: list[BrokerOrderView],
    ) -> Decimal:
        try:
            equity = parse_rest_decimal_value_object(account.get("equity"))
            unrealized = parse_rest_decimal_value_object(account.get("unrealized_profit"))
            explained = Decimal(str(self.runtime.store.get("explained_external_cash_flows", "0")))
        except Exception as exc:
            raise ProductionServiceError("STAGE8_12_4_REALIZED_EQUITY_AUTHORITY_INVALID") from exc
        if not explained.is_finite():
            raise ProductionServiceError("STAGE8_12_4_REALIZED_EQUITY_AUTHORITY_INVALID")
        realized = equity - unrealized - explained
        if realized <= 0:
            raise ProductionServiceError("STAGE8_12_4_REALIZED_EQUITY_INVALID")

        persisted = self.runtime.current_realized_equity()
        starting = self.runtime.store.get("starting_realized_equity")
        if persisted is None:
            # The production ledger may bootstrap only from a clean real account.
            # A lost/new database must never adopt an already-open broker position
            # or in-flight order as if it were known production state.
            if (
                positions
                or any(order.active for order in orders)
                or self.runtime.store.unresolved_intent_count()
            ):
                raise ProductionServiceError(
                    "STAGE8_12_4_REALIZED_EQUITY_BOOTSTRAP_REQUIRES_CLEAN_ACCOUNT"
                )
            if starting is not None:
                raise ProductionServiceError("STAGE8_12_4_REALIZED_EQUITY_STATE_INVALID")
            self.runtime.store.put("starting_realized_equity", str(realized))
        elif starting is None:
            raise ProductionServiceError("STAGE8_12_4_REALIZED_EQUITY_STATE_INVALID")

        # Broker realized basis is authoritative; raw broker equity never is.
        # Updating this value while a position is open is safe only because
        # unrealized PnL and explained external cash flows are removed first.
        self.runtime.set_realized_equity(realized)
        return realized

    def snapshot(self, now: datetime) -> Snapshot:
        account = self.api.account(self.account_id)
        if not isinstance(account, dict) or account.get("status") not in ACTIVE_ACCOUNT_STATUSES:
            raise ProductionServiceError("STAGE8_12_4_ACCOUNT_NOT_ACTIVE")
        if self.runtime.execution_revision and account.get("account_id") != self.account_id:
            self.runtime.halt("POSITION_ACCOUNT_IDENTITY_UNVERIFIED")
            raise ProductionServiceError("STAGE8_12_4_POSITION_ACCOUNT_IDENTITY_UNVERIFIED")
        try:
            positions = position_quantities(account)
            orders = order_views(self.api.orders(self.account_id))
            available = portfolio_authority(account).available_cash
        except (RuntimeError, ValueError) as exc:
            raise ProductionServiceError("STAGE8_12_4_BROKER_STATE_INVALID") from exc
        self.last_api_contact = now
        return Snapshot(
            account,
            positions,
            orders,
            self._realized_basis(account, positions, orders),
            available,
            now,
        )

    def _symbols(self) -> dict[str, str]:
        return {name: self.runtime.registry[name]["finam_symbol"] for name in INSTRUMENTS}

    def _assert_exact_broker_ownership(self, snap: Snapshot) -> None:
        symbols = self._symbols()
        if set(snap.positions) - set(symbols.values()):
            raise ProductionServiceError("STAGE8_12_4_UNEXPECTED_BROKER_POSITION")
        intents = self.runtime.store.all_intents()
        client_to_intent = {}
        for row in intents:
            key = row["idempotency_key"]
            client = compact_client_order_id(key)
            if client in client_to_intent:
                raise ProductionServiceError("STAGE8_12_4_CLIENT_ORDER_ID_COLLISION")
            client_to_intent[client] = row
        seen = set()
        for order in snap.orders:
            if not order.active:
                continue
            if order.client_order_id in seen:
                raise ProductionServiceError("STAGE8_12_4_DUPLICATE_ACTIVE_CLIENT_ORDER_ID")
            seen.add(order.client_order_id)
            row = client_to_intent.get(order.client_order_id)
            if row is None or row["payload"].get("finam_symbol") != order.symbol:
                raise ProductionServiceError("STAGE8_12_4_UNEXPECTED_ACTIVE_BROKER_ORDER")
        local = self.runtime.open_positions()
        unresolved = self.runtime.store.unresolved_intents()
        for instrument, symbol in symbols.items():
            quantity = snap.positions.get(symbol, 0)
            if quantity and instrument not in local:
                owned = any(
                    row["payload"].get("kind") == "ENTRY"
                    and row["payload"].get("instrument") == instrument
                    and (row["payload"].get("expected_position_quantity") == quantity
                         or self.runtime.execution_revision and quantity*row["payload"].get("expected_position_quantity",0)>0
                         and abs(quantity)<=abs(row["payload"]["expected_position_quantity"]))
                    and row["status"] in {"SUBMITTED", "UNCERTAIN", "ACK", "PARTIAL_FILL", "FILL"}
                    for row in unresolved
                )
                if not owned:
                    raise ProductionServiceError("STAGE8_12_4_UNEXPECTED_BROKER_POSITION")

    def _matching(self, snap: Snapshot, action: RuntimeAction) -> BrokerOrderView | None:
        if not action.idempotency_key:
            raise ProductionServiceError("STAGE8_12_4_IDEMPOTENCY_KEY_REQUIRED")
        return unique_order_by_client_id(
            snap.orders, compact_client_order_id(action.idempotency_key)
        )

    def _validate_regular(self, order: BrokerOrderView, action: RuntimeAction, *, exit_order: bool) -> None:
        if (
            order.kind != "REGULAR" or order.symbol != action.finam_symbol
            or order.side != _expected_side(action, exit_order=exit_order)
        ):
            raise ProductionServiceError("STAGE8_12_4_ORDER_RECONCILIATION_MISMATCH")
        try:
            quantity = int(Decimal(order.request["quantity"]["value"]))
        except Exception as exc:
            raise ProductionServiceError("STAGE8_12_4_ORDER_RECONCILIATION_MISMATCH") from exc
        if quantity != action.quantity:
            raise ProductionServiceError("STAGE8_12_4_ORDER_RECONCILIATION_MISMATCH")


    def _validate_sltp(self, order: BrokerOrderView, action: RuntimeAction) -> None:
        if (
            order.kind != "SLTP"
            or order.symbol != action.finam_symbol
            or order.side != _expected_side(action, exit_order=True)
            or order.comment != action.idempotency_key
            or action.stop_price is None
        ):
            raise ProductionServiceError("STAGE8_12_4_SLTP_RECONCILIATION_MISMATCH")
        try:
            price = Decimal(order.request["sl_price"]["value"])
        except Exception as exc:
            raise ProductionServiceError("STAGE8_12_4_SLTP_RECONCILIATION_MISMATCH") from exc
        if price != action.stop_price:
            raise ProductionServiceError("STAGE8_12_4_SLTP_RECONCILIATION_MISMATCH")

    def _require_entry_submission_session(
        self, finam_symbol: str, now: datetime
    ) -> None:
        windows = trading_h1_windows(self.api.schedule(finam_symbol))
        observed = now.astimezone(timezone.utc)
        active = [(start, end) for start, end in windows if start <= observed < end]
        if not active:
            raise LiveExecutionError("STAGE8_12_4_TRADING_SESSION_NOT_OPEN")
        if max(end for _, end in active) - observed < ENTRY_MINIMUM_REMAINING_SESSION:
            raise LiveExecutionError(
                "STAGE8_12_4_ENTRY_SESSION_SAFETY_MARGIN_NOT_MET"
            )

    def _submit(self, action: RuntimeAction, snap: Snapshot) -> None:
        if self.transport is None:
            return
        key = action.idempotency_key
        intent = self.runtime.store.intent(key) if key else None
        if not key or intent is None or intent["status"] != "INTENT_PERSISTED":
            return
        if (action.execution_revision == EXECUTION_REVISION and action.kind == "PROTECTIVE_STOP_REPLACE"
                and self.runtime.store.get("execution_halt")):
            return  # Keep the existing backstop; no ordinary TRAIL1 POST while halted.
        submit_now = self.clock().astimezone(timezone.utc)
        if action.kind == "ENTRY":
            if action.execution_revision == EXECUTION_REVISION and self.runtime.store.get("execution_halt"):
                raise ProductionServiceError("STAGE8_12_4_HALTED_OPERATOR_INTERVENTION_REQUIRED")
            if action.execution_revision == EXECUTION_REVISION and not FINAM_FILL_AUTHORITY_VERIFIED:
                raise ProductionServiceError("ACTUAL_FILL_AUTHORITY_BLOCKED_NO_ENTRY_SUBMISSION")
            if action.execution_revision == EXECUTION_REVISION:
                refusals = self.runtime.store.get(f"entry_pre_post_refusals:{key}", [])
                if (refusals and self.runtime.store.get(f"entry_submission:{key}") is None
                        and submit_now == datetime.fromisoformat(refusals[-1]["submission"]["submitted_at"])):
                    return  # Repeated reconciliation at the same attempt time is a no-op.
            self._require_entry_submission_session(action.finam_symbol, submit_now)
        if action.execution_revision == EXECUTION_REVISION:
            if action.kind == "ENTRY":
                try:
                    self.runtime.record_entry_submission(key, self.account_id, submit_now.isoformat())
                except Exception:
                    with self.runtime.store.transaction():
                        if self.runtime.store.get(f"entry_submission:{key}") is not None:
                            self.runtime.store.transition_intent(key, "UNCERTAIN")
                        self.runtime.halt("ENTRY_SUBMISSION_AUTHORITY_UNVERIFIED")
                    raise
            elif action.kind in {"PROTECTIVE_STOP_INSTALL", "PROTECTIVE_STOP_REPLACE"}:
                observed = snap.positions.get(action.finam_symbol,0)
                planned = intent["payload"]["planned_quantity"]
                if type(observed) is not int or not observed or (observed>0)!=(action.direction=="LONG") or abs(observed)>planned:
                    self.runtime.halt("PROTECTIVE_SUBMISSION_POSITION_UNVERIFIED")
                    raise ProductionServiceError("STAGE8_12_4_PROTECTIVE_SUBMISSION_POSITION_UNVERIFIED")
                # The endpoint always receives 100%, never a fixed contract count.
                # Persist the fresh pre-POST quantity separately from immutable intent.
                with self.runtime.store.transaction():
                    self.runtime.store.put(f"protective_submission:{key}", {"position_quantity":observed,
                                                                           "submitted_at":submit_now.isoformat()})
                    self.runtime.store.transition_intent(key,"SUBMITTED")
                action = replace(action,quantity=abs(observed),expected_position_quantity=observed)
            else:
                self.runtime.store.transition_intent(key,"SUBMITTED")
        else:
            self.runtime.store.transition_intent(key, "SUBMITTED")
        try:
            if action.kind == "ENTRY":
                response = self.transport.submit_entry(action, now=submit_now)
            elif action.kind in {"PROTECTIVE_STOP_INSTALL", "PROTECTIVE_STOP_REPLACE"}:
                response = self.transport.submit_protective_stop(
                    action, observed_position_quantity=snap.positions.get(action.finam_symbol, 0)
                )
            elif action.kind == "EMERGENCY_EXIT_REQUIRED":
                response = self.transport.submit_emergency_exit(
                    action, observed_position_quantity=snap.positions.get(action.finam_symbol, 0)
                )
            else:
                raise ProductionServiceError("STAGE8_12_4_ORDER_ACTION_INVALID")
            broker_id = _order_id(response)
        except LiveExecutionError as exc:
            if action.execution_revision == EXECUTION_REVISION and action.kind == "ENTRY":
                if isinstance(exc, EntryPrePostRefused):
                    try:
                        self.runtime.restore_entry_pre_post(key, self.account_id, submit_now.isoformat(), str(exc))
                    except Exception:
                        self.runtime.halt("ENTRY_PRE_POST_RECOVERY_UNVERIFIED")
                        raise
                else:
                    with self.runtime.store.transaction():
                        self.runtime.store.transition_intent(key, "UNCERTAIN")
                        self.runtime.halt("ENTRY_SUBMISSION_OUTCOME_UNVERIFIED")
                raise
            # Preserve existing legacy/non-ENTRY guard-refusal behavior.
            # Candidate ENTRY above requires the explicit pre-POST contract.
            self.runtime.store.transition_intent(key, "INTENT_PERSISTED")
            raise
        except FinamUncertainSubmission:
            with self.runtime.store.transaction():
                self.runtime.store.transition_intent(key, "UNCERTAIN")
                if action.execution_revision == EXECUTION_REVISION and action.kind == "ENTRY":
                    self.runtime.halt("ENTRY_SUBMISSION_OUTCOME_UNVERIFIED")
            raise
        except FinamOrderRejected:
            self.runtime.store.transition_intent(key, "REJECTED")
            raise
        except Exception:
            if action.execution_revision == EXECUTION_REVISION and action.kind == "ENTRY":
                with self.runtime.store.transaction():
                    self.runtime.store.transition_intent(key, "UNCERTAIN")
                    self.runtime.halt("ENTRY_SUBMISSION_OUTCOME_UNVERIFIED")
            raise
        self.runtime.store.transition_intent(key, "ACK", broker_id)

    def _reconcile_intents(self, snap: Snapshot) -> None:
        generated: list[RuntimeAction] = []
        faults = []
        rows = self.runtime.store.unresolved_intents()
        if self.runtime.execution_revision:
            # Revalidate price facts for owned open entries after restart, including
            # terminal local entries. A stale/missing history never causes a retry.
            local_trades = {p['trade_id'] for p in self.runtime.open_positions().values()}
            keys = {row['idempotency_key'] for row in rows}
            rows += [row for row in self.runtime.store.all_intents() if row['idempotency_key'] not in keys
                     and row['payload'].get('kind')=='ENTRY' and row['payload'].get('trade_id') in local_trades]
        for row in tuple(rows):
            action = _action(row["payload"])
            order = self._matching(snap, action)
            status = row["status"]

            if action.kind == "ENTRY":
                if self.runtime.execution_revision:
                    try:
                        self._reconcile_candidate_entry(row, action, order, snap)
                    except Exception as exc:
                        self.runtime.halt("FILL_OR_PARTIAL_RECONCILIATION_UNVERIFIED")
                        faults.append(exc)
                    continue
                quantity = snap.positions.get(action.finam_symbol, 0)
                if order is not None:
                    self._validate_regular(order, action, exit_order=False)

                # Exact /account quantity proves exposure, not execution price.
                # Preserve the precommitted initial protection; missing price
                # authority blocks management and new entries in the amendment.
                if quantity:
                    if (
                        order is not None
                        and order.status in TERMINAL_ORDER_STATUSES
                        and order.status not in {"FILLED", "EXECUTED"}
                    ):
                        raise ProductionServiceError(
                            "STAGE8_12_4_REJECTED_ENTRY_HAS_POSITION"
                        )
                    stop = self.runtime.confirm_entry_position(
                        action.idempotency_key, quantity
                    )
                    if stop is not None:
                        generated.append(stop)
                    continue

                if order is not None:
                    if order.status in {"FILLED", "EXECUTED"}:
                        raise ProductionServiceError(
                            "STAGE8_12_4_FILLED_ENTRY_WITHOUT_POSITION"
                        )
                    if order.status in TERMINAL_ORDER_STATUSES:
                        terminal = (
                            "CANCELLED"
                            if order.status in {"CANCELLED", "REPLACED", "EXPIRED", "DISABLED"}
                            else "REJECTED"
                        )
                        self.runtime.store.transition_intent(
                            action.idempotency_key, terminal, order.order_id
                        )
                        continue
                    if status in {"INTENT_PERSISTED", "SUBMITTED", "UNCERTAIN"}:
                        self.runtime.store.transition_intent(
                            action.idempotency_key, "ACK", order.order_id
                        )
                    continue

                if status == "INTENT_PERSISTED":
                    self._submit(action, snap)
                    continue
                if status in {"SUBMITTED", "UNCERTAIN", "ACK", "PARTIAL_FILL", "FILL"}:
                    raise ProductionServiceError(
                        "STAGE8_12_4_UNCERTAIN_ENTRY_REQUIRES_BROKER_PROOF"
                    )

            elif action.kind in {"PROTECTIVE_STOP_INSTALL", "PROTECTIVE_STOP_REPLACE"}:
                if order is None:
                    if status in {"SUBMITTED", "UNCERTAIN", "ACK", "PARTIAL_FILL", "FILL"}:
                        raise ProductionServiceError(
                            "STAGE8_12_4_UNCERTAIN_STOP_REQUIRES_BROKER_PROOF"
                        )
                    if status == "INTENT_PERSISTED":
                        self._submit(action, snap)
                    continue

                active = active_sltp_for_trade(
                    snap.orders, trade_id=action.trade_id, symbol=action.finam_symbol
                )
                self._validate_sltp(order, action)
                if order.active and order in active:
                    self.runtime.confirm_protective_stop(
                        action.idempotency_key, order.order_id
                    )
                elif order.status in TERMINAL_ORDER_STATUSES:
                    raise ProductionServiceError(
                        "STAGE8_12_4_PROTECTIVE_STOP_TERMINAL_BEFORE_RECONCILIATION"
                    )

            elif action.kind == "EMERGENCY_EXIT_REQUIRED":
                quantity = snap.positions.get(action.finam_symbol, 0)
                expected = (
                    action.quantity if action.direction == "LONG" else -action.quantity
                )
                if quantity not in {0, expected}:
                    raise ProductionServiceError(
                        "STAGE8_12_4_POSITION_RECONCILIATION_MISMATCH"
                    )

                # Flat /account position is authoritative even if /orders has
                # not converged yet or the old protective stop won the race.
                if quantity == 0:
                    if order is not None:
                        self._validate_regular(order, action, exit_order=True)
                    self.runtime.store.transition_intent(
                        action.idempotency_key,
                        "CLOSED",
                        order.order_id if order is not None else row.get("broker_order_id"),
                    )
                    continue

                if order is None:
                    if status == "INTENT_PERSISTED":
                        self._submit(action, snap)
                        continue
                    if status in {"SUBMITTED", "UNCERTAIN", "ACK", "PARTIAL_FILL", "FILL"}:
                        raise ProductionServiceError(
                            "STAGE8_12_4_UNCERTAIN_EXIT_REQUIRES_BROKER_PROOF"
                        )
                else:
                    self._validate_regular(order, action, exit_order=True)
                    if order.status in TERMINAL_ORDER_STATUSES:
                        raise ProductionServiceError(
                            "STAGE8_12_4_TERMINAL_EXIT_HAS_OPEN_POSITION"
                        )
                    if status in {"INTENT_PERSISTED", "SUBMITTED", "UNCERTAIN"}:
                        self.runtime.store.transition_intent(
                            action.idempotency_key, "ACK", order.order_id
                        )
            else:
                raise ProductionServiceError(
                    "STAGE8_12_4_UNKNOWN_UNRESOLVED_INTENT"
                )

        for action in generated:
            self._submit(action, snap)
        if faults:
            raise ProductionServiceError("STAGE8_12_4_HALTED_OPERATOR_INTERVENTION_REQUIRED") from faults[0]

    def _reconcile_candidate_entry(self, row, action, order, snap) -> None:
        key = action.idempotency_key
        quantity = snap.positions.get(action.finam_symbol,0)
        if order is not None:
            self._validate_regular(order,action,exit_order=False)
            if row.get("broker_order_id") not in {None,order.order_id}:
                raise ProductionServiceError("STAGE8_12_4_ENTRY_ORDER_ID_CHANGED")
            if row.get("broker_order_id") is None:
                self.runtime.store.transition_intent(key,"ACK",order.order_id)
            if order.status in TERMINAL_ORDER_STATUSES:
                self.runtime.store.put(f"entry_terminal:{key}", {"order_id":order.order_id,"status":order.status})
        if quantity:
            # Protect exposure before requesting price history (which may fail).
            stop = self.runtime.confirm_entry_position(key,quantity)
            if stop is not None:
                self._submit(stop,snap)
            current = self.runtime.store.intent(key)
            submission = self.runtime.store.get(f"entry_submission:{key}")
            if not current["broker_order_id"] or not submission:
                raise ProductionServiceError("STAGE8_12_4_EXACT_FILL_IDENTITY_OR_INTERVAL_MISSING")
            end = snap.observed_at.isoformat()
            response = self.api.trades(self.account_id,start=submission["submitted_at"],end=end,limit=1000)
            self.runtime.handoff_entry_history(key, account_id=self.account_id,broker_order_id=current["broker_order_id"],
                response=response,start=submission["submitted_at"],end=end,limit=1000,observed_at=end)
            return
        if self.runtime.open_positions().get(action.instrument):
            # A stop may have flattened a partial entry while its remainder is
            # still active. Never remove protection or retry/compensate the entry.
            if row["status"] != "RECONCILED":
                self.runtime.halt("FLAT_WITH_OPEN_ENTRY_PRESERVE_BACKSTOP")
                raise ProductionServiceError("STAGE8_12_4_HALTED_OPERATOR_INTERVENTION_REQUIRED")
            return
        if order is not None:
            if order.status in {"FILLED","EXECUTED"}:
                raise ProductionServiceError("STAGE8_12_4_FILLED_ENTRY_WITHOUT_POSITION")
            if order.status in TERMINAL_ORDER_STATUSES:
                terminal = "CANCELLED" if order.status in {"CANCELLED","REPLACED","EXPIRED","DISABLED"} else "REJECTED"
                self.runtime.store.transition_intent(key,terminal,order.order_id)
            elif row["status"] in {"INTENT_PERSISTED","SUBMITTED","UNCERTAIN"}:
                self.runtime.store.transition_intent(key,"ACK",order.order_id)
            return
        if row["status"] == "INTENT_PERSISTED":
            try:
                self._submit(action,snap)
            except EntryPrePostRefused:
                return  # Only this flat ENTRY call supplied the pre-POST proof.
        elif row["status"] in {"SUBMITTED","UNCERTAIN","ACK","PARTIAL_FILL","FILL"}:
            raise ProductionServiceError("STAGE8_12_4_UNCERTAIN_ENTRY_REQUIRES_BROKER_PROOF")

    def _flat_cleanup_and_exit(self, snap: Snapshot) -> Snapshot:
        if self.runtime.execution_revision:
            for row in self.runtime.store.unresolved_intents():
                if row['payload'].get('kind')=='ENTRY' and not snap.positions.get(row['payload']['finam_symbol'],0):
                    value = self.runtime.open_positions().get(row['payload']['instrument'])
                    if value:
                        self.runtime.halt("FLAT_WITH_OPEN_ENTRY_PRESERVE_BACKSTOP")
                        raise ProductionServiceError("STAGE8_12_4_HALTED_OPERATOR_INTERVENTION_REQUIRED")
        changed = False
        for instrument, value in tuple(self.runtime.open_positions().items()):
            symbol = value["finam_symbol"]
            if snap.positions.get(symbol, 0):
                continue
            active = active_sltp_for_trade(
                snap.orders, trade_id=value["trade_id"], symbol=symbol
            )
            if active and self.transport is None:
                raise ProductionServiceError("STAGE8_12_4_FLAT_POSITION_HAS_ACTIVE_PROTECTIVE_STOP")
            for stop in active:
                self.transport.cancel_protective_stop_after_flat(
                    stop.order_id, observed_position_quantity=0
                )
                changed = True
        if changed:
            snap = self.snapshot(snap.observed_at)
        for instrument, value in tuple(self.runtime.open_positions().items()):
            symbol = value["finam_symbol"]
            if snap.positions.get(symbol, 0):
                continue
            if active_sltp_for_trade(snap.orders, trade_id=value["trade_id"], symbol=symbol):
                raise ProductionServiceError("STAGE8_12_4_FLAT_POSITION_HAS_ACTIVE_PROTECTIVE_STOP")
            self.runtime.broker_exit_observed(
                instrument, realized_equity_after_exit=snap.realized_equity,
                protective_stop_terminal=True,
            )
        return snap

    def _protection(self, snap: Snapshot) -> list[dict[str, Any]]:
        result = []
        intent_by_client: dict[str, dict[str, Any]] = {}
        for row in self.runtime.store.all_intents():
            client = compact_client_order_id(row["idempotency_key"])
            if client in intent_by_client:
                raise ProductionServiceError(
                    "STAGE8_12_4_CLIENT_ORDER_ID_COLLISION"
                )
            intent_by_client[client] = row

        for instrument, value in sorted(self.runtime.open_positions().items()):
            expected = (
                int(value["quantity"])
                if value["direction"] == "LONG"
                else -int(value["quantity"])
            )
            observed = snap.positions.get(value["finam_symbol"], 0)
            if observed != expected:
                if self.runtime.execution_revision:
                    self.runtime.halt("POSITION_CHANGED_AFTER_RECONCILIATION")
                raise ProductionServiceError(
                    "STAGE8_12_4_POSITION_RECONCILIATION_MISMATCH"
                )
            stops = active_sltp_for_trade(
                snap.orders, trade_id=value["trade_id"], symbol=value["finam_symbol"]
            )
            if not stops:
                raise ProductionServiceError("STAGE8_12_4_OPEN_POSITION_UNPROTECTED")

            for stop in stops:
                row = intent_by_client.get(stop.client_order_id)
                if row is None:
                    raise ProductionServiceError(
                        "STAGE8_12_4_UNEXPECTED_ACTIVE_PROTECTIVE_STOP"
                    )
                action = _action(row["payload"])
                if (
                    action.kind not in {"PROTECTIVE_STOP_INSTALL", "PROTECTIVE_STOP_REPLACE"}
                    or action.trade_id != value["trade_id"]
                    or action.instrument != instrument
                ):
                    raise ProductionServiceError(
                        "STAGE8_12_4_UNEXPECTED_ACTIVE_PROTECTIVE_STOP"
                    )
                self._validate_sltp(stop, action)

            active_ids = [stop.order_id for stop in stops]
            current_stop_id = value.get("protective_stop_broker_order_id")
            if (
                value.get("protective_stop_state") != "ACTIVE"
                or not isinstance(current_stop_id, str)
                or current_stop_id not in active_ids
                or Decimal(str(value.get("protective_stop_price")))
                != Decimal(str(value["current_stop"]))
            ):
                raise ProductionServiceError(
                    "STAGE8_12_4_CURRENT_PROTECTIVE_STOP_NOT_ACTIVE"
                )
            if self.runtime.execution_revision and value.get("protective_covered_quantity") != abs(observed):
                self.runtime.halt("PROTECTIVE_COVERAGE_UNVERIFIED")
                raise ProductionServiceError("STAGE8_12_4_HALTED_OPERATOR_INTERVENTION_REQUIRED")
            result.append({
                "instrument": instrument,
                "trade_id": value["trade_id"],
                "expected_position_quantity": expected,
                "covered_quantity": abs(expected),
                "active_stop_order_ids": active_ids,
            })
        return result

    def _history(self, instrument: str, now: datetime) -> pd.DataFrame:
        symbol = self.runtime.registry[instrument]["finam_symbol"]
        schedule = self.api.schedule(symbol)
        windows = trading_h1_windows(schedule)
        response = self.api.bars(
            symbol, (now - timedelta(days=H1_LOOKBACK_DAYS)).isoformat(), now.isoformat()
        )
        live = finam_completed_open_h1(response, now, windows)
        expected = newest_expected_h1_close(schedule, now)
        prior_text = self.runtime.store.get(f"production_expected_h1:{instrument}")
        prior = datetime.fromisoformat(prior_text) if prior_text else None
        expected = max(expected, prior) if expected is not None and prior is not None else expected or prior
        if expected is None:
            raise ProductionServiceError("STAGE8_12_4_EXPECTED_H1_UNAVAILABLE")
        live_utc = {stamp.tz_convert("UTC").to_pydatetime() for stamp in live.index}
        if expected.astimezone(timezone.utc) not in live_utc:
            raise ProductionServiceError("STAGE8_12_4_STALE_COMPLETED_H1_DATA")
        seed = load_stage5_seed_open_h1(self.stage5_data_root, instrument)
        continuation_key = f"production_h1_continuation:{instrument}"
        persisted = self.runtime.store.get(continuation_key)
        merged, continuation = extend_rolling_open_h1(
            seed, persisted, live, instrument
        )
        if continuation != persisted:
            self.runtime.store.put(continuation_key, continuation)
        self.runtime.store.put(
            f"production_expected_h1:{instrument}", expected.isoformat()
        )
        return close_index_for_frozen_t3(merged)

    def _manage_positions(
        self, histories: dict[str, pd.DataFrame], snap: Snapshot
    ) -> bool:
        if self.runtime.store.unresolved_intent_count() or self.runtime.execution_revision and self.runtime.store.get("execution_halt"):
            return False
        for instrument in tuple(self.runtime.open_positions()):
            execution, _ = self.runtime.context_builder.build(
                histories[instrument], snap.observed_at
            )
            watermark = self.runtime.store.get(f"last_managed_h1:{instrument}")
            pending = (
                execution
                if watermark is None
                else execution.loc[execution.index > pd.Timestamp(watermark)]
            )
            for stamp, row in pending.iterrows():
                if pd.isna(row.ATR):
                    raise ProductionServiceError(
                        "STAGE8_12_4_COMPLETED_H1_INDICATOR_INVALID"
                    )
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
                    instrument,
                    bar,
                    observed_position_quantity=snap.positions.get(
                        self.runtime.registry[instrument]["finam_symbol"], 0
                    ),
                )
                if action is not None:
                    self._submit(action, snap)
                    return True
        return False

    def _entry_session_ready(
        self, instrument: str, history: pd.DataFrame, now: datetime
    ) -> bool:
        symbol = self.runtime.registry[instrument]["finam_symbol"]
        schedule = self.api.schedule(symbol)
        windows = trading_h1_windows(schedule)
        observed = now.astimezone(timezone.utc)
        active = [(start, end) for start, end in windows if start <= observed < end]
        if not active:
            return False
        if max(end for _, end in active) - observed < ENTRY_MINIMUM_REMAINING_SESSION:
            return False

        derived = newest_expected_h1_close(schedule, now)
        if derived is None:
            return False
        expected_close = (
            pd.Timestamp(derived).tz_convert("Europe/Moscow") + pd.Timedelta("1h")
        )
        if history.empty or history.index[-1] != expected_close:
            raise ProductionServiceError(
                "STAGE8_12_4_ENTRY_H1_NOT_LATEST_CURRENT_SESSION_BAR"
            )
        return True

    def _plan_entry(
        self, histories: dict[str, pd.DataFrame], snap: Snapshot
    ) -> bool:
        if self.transport is None or self.runtime.store.unresolved_intent_count() or self.runtime.execution_revision and self.runtime.store.get("execution_halt"):
            return False
        if self.runtime.execution_revision == EXECUTION_REVISION and not FINAM_FILL_AUTHORITY_VERIFIED:
            return False
        gate = evaluate_production_entry_gate(
            runtime_root=self.root, now=snap.observed_at,
            expected_commit=self.accepted_commit, expected_account_hash=self.account_hash,
            execution_authorized=True,
        )
        if gate.get("entry_gate_open") is not True:
            return False
        budget = self.runtime.begin_batch(
            realized_equity=snap.realized_equity, available_cash=snap.available_cash
        )
        for instrument in INSTRUMENTS:
            if instrument in self.runtime.open_positions():
                continue
            if not self._entry_session_ready(
                instrument, histories[instrument], snap.observed_at
            ):
                continue
            signal = self.runtime.build_latest_signal(
                instrument, histories[instrument], snap.observed_at
            )
            if signal is None:
                continue
            row = self.runtime.registry[instrument]
            params = self.api.asset_params(row["finam_symbol"], self.account_id)
            authority = InstrumentAuthority(
                instrument, row["finam_symbol"], Decimal(row["price_step"]),
                Decimal(row["tick_value"]), int(row["quantity_granularity"]),
                directional_initial_margin(params, "LONG"),
                directional_initial_margin(params, "SHORT"),
            )
            action = self.runtime.plan_entry(
                signal, authority, realized_equity=snap.realized_equity, budget=budget
            )
            if action.kind == "ENTRY":
                self._submit(action, snap)
                return True
        return False

    def _heartbeat(self, snap: Snapshot, protection: list[dict[str, Any]], healthy: bool) -> None:
        write_production_heartbeat(
            self.root, accepted_commit=self.accepted_commit, account_hash=self.account_hash,
            reconciliation_status="PASS" if healthy else "FAULT",
            unresolved_intent_count=self.runtime.store.unresolved_intent_count(),
            health_status="HEALTHY" if healthy else "UNHEALTHY",
            cycle_count=self.cycle_count,
            last_api_contact=self.last_api_contact or snap.observed_at,
            position_protection=protection, now=snap.observed_at,
        )

    def _fault_heartbeat(self, now: datetime | None = None) -> None:
        observed = (now or self.clock()).astimezone(timezone.utc)
        write_production_heartbeat(
            self.root,
            accepted_commit=self.accepted_commit,
            account_hash=self.account_hash,
            reconciliation_status="FAULT",
            unresolved_intent_count=self.runtime.store.unresolved_intent_count(),
            health_status="UNHEALTHY",
            cycle_count=self.cycle_count,
            last_api_contact=self.last_api_contact
            or datetime(1970, 1, 1, tzinfo=timezone.utc),
            position_protection=[],
            now=observed,
        )

    def cycle(self) -> None:
        now = self.clock().astimezone(timezone.utc)
        snap = self.snapshot(now)
        self._assert_exact_broker_ownership(snap)
        self._reconcile_intents(snap)
        snap = self.snapshot(now)
        snap = self._flat_cleanup_and_exit(snap)
        snap = self.snapshot(now)
        self._assert_exact_broker_ownership(snap)
        protection = self._protection(snap)
        if self.runtime.execution_revision and self.runtime.store.get("execution_halt"):
            self._fault_heartbeat(now)
            raise ProductionServiceError("STAGE8_12_4_HALTED_OPERATOR_INTERVENTION_REQUIRED")
        histories = {
            instrument: self._history(instrument, now) for instrument in INSTRUMENTS
        }
        action_started = self._manage_positions(histories, snap)
        if action_started or self.runtime.store.unresolved_intent_count():
            self._fault_heartbeat(now)
            return

        self.cycle_count += 1
        self.runtime.store.put("production_service_cycle_count", self.cycle_count)
        self._heartbeat(snap, protection, True)

        entry_started = self._plan_entry(histories, snap)
        if entry_started or self.runtime.store.unresolved_intent_count():
            self._fault_heartbeat(now)
        self.logger.info(
            "PRODUCTION_CYCLE_PASS cycle=%d authorized=%s positions=%d unresolved=%d",
            self.cycle_count, self.transport is not None,
            len(self.runtime.open_positions()), self.runtime.store.unresolved_intent_count(),
        )

    def run(self, *, once: bool = False) -> int:
        while True:
            try:
                self.cycle()
            except Exception as exc:
                code = str(exc)
                if not code.startswith("STAGE8_12_4_") and not code.startswith("FINAM_"):
                    code = "STAGE8_12_4_PRODUCTION_CYCLE_FAILED"
                try:
                    self._fault_heartbeat()
                except Exception:
                    pass
                self.logger.error("PRODUCTION_CYCLE_FAULT code=%s", code)
                if once:
                    return 1
                self.sleeper(FAST_RECONCILIATION_SECONDS)
                continue
            if once:
                return 0
            self.sleeper(
                FAST_RECONCILIATION_SECONDS
                if self.runtime.store.unresolved_intent_count()
                else self.poll_seconds
            )


def run_from_environment(
    runtime_root: Path, stage5_data_root: Path, *, accepted_commit: str,
    once: bool = False, poll_seconds: int = DEFAULT_POLL_SECONDS,
    api_factory=FinamAPI, environment: dict[str, str] | None = None,
    clock: Callable[[], datetime] | None = None,
) -> int:
    environment = dict(os.environ if environment is None else environment)
    if environment.get("FINAM_MODE") != MODE:
        raise ProductionServiceError("STAGE8_12_4_PRODUCTION_MODE_REQUIRED")
    secret = environment.get("FINAM_API_SECRET", "")
    account = environment.get("FINAM_REAL_ACCOUNT_ID", "")
    if not secret or not account:
        raise ProductionServiceError("STAGE8_12_4_PRODUCTION_CREDENTIAL_MISSING")
    lock = InstanceLock(Path(runtime_root) / "state" / INSTANCE_LOCK)
    lock.acquire()
    service = None
    try:
        service = ProductionService(
            runtime_root, stage5_data_root, api_factory(secret), account, accepted_commit,
            poll_seconds=poll_seconds, clock=clock,
        )
        try:
            service.authenticate()
        except Exception:
            try:
                service._fault_heartbeat()
            except Exception:
                pass
            raise
        return service.run(once=once)
    finally:
        if service is not None:
            service.close()
        lock.release()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Stage 8.12.4 FINAM production service")
    parser.add_argument("--runtime-root", type=Path, required=True)
    parser.add_argument("--stage5-data-root", type=Path, required=True)
    parser.add_argument("--accepted-commit", required=True)
    parser.add_argument("--poll-seconds", type=int, default=DEFAULT_POLL_SECONDS)
    parser.add_argument("--once", action="store_true")
    args = parser.parse_args(argv)
    try:
        return run_from_environment(
            args.runtime_root, args.stage5_data_root,
            accepted_commit=args.accepted_commit, once=args.once,
            poll_seconds=args.poll_seconds,
        )
    except (ProductionServiceError, RuntimeError, ValueError) as exc:
        code = str(exc)
        print(code if code.startswith("STAGE8_12_4_") else "STAGE8_12_4_PRODUCTION_STARTUP_FAILED")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
