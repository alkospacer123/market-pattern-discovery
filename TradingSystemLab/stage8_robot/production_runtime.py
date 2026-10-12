"""Broker-neutral Stage 8.12 production runtime assembly.

This module deliberately has no FINAM transport or Broker dependency.  It wires
the frozen Stage 7 decision/risk/state components into durable production
actions while real-order transmission remains structurally unavailable.

A later, separately authorized adapter may consume these actions only after
Stage 8.12.2/8.12.3 have passed and Stage 8.12.4 is explicitly authorized.
"""
from __future__ import annotations

import csv
from dataclasses import asdict, dataclass
from decimal import Decimal
from functools import wraps
import json
import sqlite3
from pathlib import Path
from typing import Any, Literal

import pandas as pd

from .context_builder import T3ContextBuilder
from .margin import MarginBatchBudget, cap_r15_by_margin
from .risk import ContractEconomics, size_position
from .specification import ACTIVE_IDENTITY, INSTRUMENTS, PRODUCTION_SPECIFICATION_ID, load_frozen_specification
from .state import StateStore, _validate_acceptance_schema
from .strategy_core import CompletedBar, DecisionCore, PositionState, SignalIntent, T3Context
from .trail1_state import Trail1State
from .execution_grid import (EXECUTION_REVISION, authority_fingerprint, decimal_price,
                             initial_projection, manage_executable, require_on_grid)

RUNTIME_SCHEMA = "stage8_12_production_runtime.v1"
AMENDED_RUNTIME_SCHEMA = "stage8_12_production_runtime.stop_tick_grid.v1"
MODE = "STAGE8_12_CODE_ONLY"
PRODUCTION_REGISTRY = Path(__file__).with_name("production_instrument_registry.csv")
ActionKind = Literal[
    "ENTRY",
    "PROTECTIVE_STOP_INSTALL",
    "PROTECTIVE_STOP_REPLACE",
    "EMERGENCY_EXIT_REQUIRED",
    "BROKER_EXIT_OBSERVED",
    "SKIP_ZERO_CAPACITY",
    "SKIP_RISK_LIMIT",
    "SKIP_STOP_NOT_ON_TICK_GRID",
]


class ProductionRuntimeError(RuntimeError):
    pass


def _atomic(method):
    @wraps(method)
    def invoke(self, *args, **kwargs):
        with self.store.transaction():
            return method(self, *args, **kwargs)
    return invoke


@dataclass(frozen=True)
class InstrumentAuthority:
    instrument: str
    finam_symbol: str
    price_step: Decimal
    tick_value: Decimal
    trade_lot_size: int
    long_initial_margin: Decimal
    short_initial_margin: Decimal

    def initial_margin(self, direction: str) -> Decimal:
        if direction == "LONG":
            return self.long_initial_margin
        if direction == "SHORT":
            return self.short_initial_margin
        raise ProductionRuntimeError("DIRECTION_INVALID")


@dataclass(frozen=True)
class RuntimeAction:
    kind: ActionKind
    idempotency_key: str | None
    instrument: str
    finam_symbol: str
    direction: str | None
    quantity: int
    trade_id: str | None
    signal_id: str | None
    reference_price: Decimal | None
    stop_price: Decimal | None
    expected_position_quantity: int | None
    reason: str | None = None
    execution_revision: str | None = None
    price_step: Decimal | None = None

    def payload(self) -> dict[str, Any]:
        result = asdict(self)
        for key, value in tuple(result.items()):
            if isinstance(value, Decimal):
                result[key] = str(value)
        result["production_specification_id"] = PRODUCTION_SPECIFICATION_ID
        result["active_identity"] = ACTIVE_IDENTITY
        result["runtime_schema"] = AMENDED_RUNTIME_SCHEMA if self.execution_revision else RUNTIME_SCHEMA
        if self.execution_revision is None:
            result.pop("execution_revision")
            result.pop("price_step")
        return result


def _load_registry(path: Path = PRODUCTION_REGISTRY) -> dict[str, dict[str, str]]:
    try:
        with path.open(newline="", encoding="utf-8") as stream:
            rows = list(csv.DictReader(stream))
    except (OSError, csv.Error) as exc:
        raise ProductionRuntimeError("PRODUCTION_REGISTRY_UNREADABLE") from exc
    if len(rows) != len(INSTRUMENTS):
        raise ProductionRuntimeError("PRODUCTION_REGISTRY_NOT_N4")
    mapped = {row.get("research_symbol"): row for row in rows}
    if set(mapped) != set(INSTRUMENTS):
        raise ProductionRuntimeError("PRODUCTION_REGISTRY_NOT_N4")
    for instrument in INSTRUMENTS:
        row = mapped[instrument]
        if (
            row.get("binding_status") != "AUTHENTICATED_REAL_READONLY"
            or row.get("trading_status") != "TRADABLE"
            or row.get("mic") != "RTSX"
            or not row.get("finam_symbol")
            or not row.get("security_id")
        ):
            raise ProductionRuntimeError("PRODUCTION_REGISTRY_AUTHORITY_INVALID")
    return mapped


def _trail_to_dict(state: Trail1State) -> dict[str, Any]:
    result = {
        "direction": state.direction,
        "entry_price": state.entry_price,
        "initial_stop_price": state.initial_stop_price,
        "enabled": state.enabled,
        "triggered": state.triggered,
        "activated": state.activated,
        "trigger_bar_time": state.trigger_bar_time,
        "activation_time": state.activation_time,
        "stored_candidate": state.stored_candidate,
        "candidate_already_looser": state.candidate_already_looser,
        "gap_through_activated_trail": state.gap_through_activated_trail,
    }
    return {k: str(v) if isinstance(v, Decimal) else v for k, v in result.items()}


def _trail_from_dict(value: dict[str, Any]) -> Trail1State:
    state = Trail1State(
        value["direction"],
        float(value["entry_price"]),
        float(value["initial_stop_price"]),
        enabled=bool(value.get("enabled", True)),
    )
    state.triggered = bool(value.get("triggered", False))
    state.activated = bool(value.get("activated", False))
    state.trigger_bar_time = value.get("trigger_bar_time")
    state.activation_time = value.get("activation_time")
    state.stored_candidate = value.get("stored_candidate")
    state.candidate_already_looser = bool(value.get("candidate_already_looser", False))
    state.gap_through_activated_trail = bool(value.get("gap_through_activated_trail", False))
    return state


def _position_to_dict(position: PositionState, meta: dict[str, Any]) -> dict[str, Any]:
    return {
        **meta,
        "instrument": position.instrument,
        "direction": position.direction,
        "entry": str(position.entry) if isinstance(position.entry, Decimal) else position.entry,
        "initial_stop": str(position.initial_stop) if isinstance(position.initial_stop, Decimal) else position.initial_stop,
        "current_stop": str(position.current_stop) if isinstance(position.current_stop, Decimal) else position.current_stop,
        "favorable_extreme": str(position.favorable_extreme) if isinstance(position.favorable_extreme, Decimal) else position.favorable_extreme,
        "trail1": _trail_to_dict(position.trail1),
    }


def _position_from_dict(value: dict[str, Any]) -> PositionState:
    number = (lambda value: Decimal(str(value))) if value.get("execution_revision") else float
    return PositionState(
        instrument=value["instrument"],
        direction=value["direction"],
        entry=number(value["entry"]),
        initial_stop=number(value["initial_stop"]),
        current_stop=number(value["current_stop"]),
        favorable_extreme=number(value["favorable_extreme"]),
        trail1=_trail_from_dict(value["trail1"]),
    )


def _signal_to_dict(signal: SignalIntent) -> dict[str, Any]:
    return {
        "signal_id": signal.signal_id,
        "trade_id": signal.trade_id,
        "instrument": signal.instrument,
        "direction": signal.direction,
        "timestamp": signal.timestamp.isoformat(),
        "entry": signal.entry,
        "initial_stop": signal.initial_stop,
        "initial_r": signal.initial_r,
        "canonical_stop": signal.canonical_stop,
    }


def _signal_from_dict(value: dict[str, Any]) -> SignalIntent:
    from datetime import datetime
    return SignalIntent(
        signal_id=value["signal_id"],
        trade_id=value["trade_id"],
        instrument=value["instrument"],
        direction=value["direction"],
        timestamp=datetime.fromisoformat(value["timestamp"]),
        entry=float(value["entry"]),
        initial_stop=float(value["initial_stop"]),
        initial_r=float(value["initial_r"]),
        canonical_stop=float(value["canonical_stop"]),
    )


class ProductionRuntime:
    """Durable production planner with no order-transmission capability."""

    def __init__(self, state_path: Path, *, registry_path: Path = PRODUCTION_REGISTRY,
                 execution_authorized: bool = False, execution_revision: str | None = None):
        if execution_authorized:
            raise ProductionRuntimeError("STAGE8_12_REAL_ORDER_TRANSMISSION_NOT_AUTHORIZED")
        spec = load_frozen_specification()
        if spec.production_id != PRODUCTION_SPECIFICATION_ID or spec.identity != ACTIVE_IDENTITY:
            raise ProductionRuntimeError("FROZEN_PRODUCTION_AUTHORITY_INVALID")
        self.spec = spec
        self.registry = _load_registry(registry_path)
        if execution_revision not in {None, EXECUTION_REVISION}:
            raise ProductionRuntimeError("EXECUTION_REVISION_INVALID")
        self.execution_revision = execution_revision
        state_path.parent.mkdir(parents=True, exist_ok=True)
        identity = {
            "schema_id": AMENDED_RUNTIME_SCHEMA if execution_revision else RUNTIME_SCHEMA,
            "production_specification_id": PRODUCTION_SPECIFICATION_ID,
            "active_identity": ACTIVE_IDENTITY,
            "mode": MODE,
        }
        if execution_revision:
            identity["execution_revision"] = execution_revision
            # Validate before StateStore opens WAL or writes identity. Legacy,
            # unidentified and mixed states are never silently migrated.
            if state_path.exists():
                db = sqlite3.connect(state_path.resolve().as_uri() + "?mode=ro", uri=True)
                try:
                    _validate_acceptance_schema(db)
                    if db.execute("PRAGMA integrity_check").fetchone() != ("ok",):
                        raise sqlite3.DatabaseError("EXECUTION_STATE_INTEGRITY_INVALID")
                    row = db.execute("SELECT value FROM state WHERE key='database_identity'").fetchone()
                    if row is None or json.loads(row[0]) != identity:
                        raise ProductionRuntimeError("EXECUTION_STATE_REVISION_MISMATCH")
                except sqlite3.DatabaseError as exc:
                    raise ProductionRuntimeError("EXECUTION_STATE_REVISION_MISMATCH") from exc
                finally:
                    db.close()
        self.store = StateStore(state_path, identity)
        self.core = DecisionCore()
        self.context_builder = T3ContextBuilder()
        if execution_revision:
            try:
                self.open_positions()
                for row in self.store.all_intents():
                    if row["payload"].get("execution_revision") != execution_revision:
                        raise ProductionRuntimeError("EXECUTION_STATE_REVISION_MISMATCH")
                    self._validate_execution_evidence(row["payload"])
                    if row["payload"]["kind"] in {"PROTECTIVE_STOP_INSTALL", "PROTECTIVE_STOP_REPLACE"}:
                        require_on_grid(row["payload"]["stop_price"], row["payload"]["price_step"])
            except Exception:
                self.store.close()
                raise

    def _action(self, *args, **kwargs) -> RuntimeAction:
        if self.execution_revision:
            kwargs.update(execution_revision=self.execution_revision,
                          price_step=Decimal(self.registry[args[2]]["price_step"]))
        return RuntimeAction(*args, **kwargs)

    def _authority_evidence(self, authority: InstrumentAuthority) -> dict:
        result = {k: str(v) if isinstance(v, Decimal) else v for k, v in asdict(authority).items()}
        result["registry_fingerprint"] = authority_fingerprint(self.registry[authority.instrument])
        return result

    def _validate_execution_evidence(self, value: dict) -> None:
        try:
            evidence = value["instrument_authority"]
            authority = InstrumentAuthority(**{k: Decimal(v) if k in {
                "price_step", "tick_value", "long_initial_margin", "short_initial_margin"} else v
                for k, v in evidence.items() if k != "registry_fingerprint"})
            self._validate_instrument_authority(authority)
            if (value["execution_revision"] != self.execution_revision
                    or value["instrument"] != authority.instrument
                    or value["finam_symbol"] != authority.finam_symbol
                    or evidence != self._authority_evidence(authority)
                    or value["specification_fingerprint"] != authority_fingerprint(evidence)):
                raise ValueError("REVISION_OR_FINGERPRINT")
            stop, risk = initial_projection(value["direction"], value["reference_entry"],
                                            value["raw_initial_stop"], authority.price_step)
            if stop != Decimal(value["executable_initial_stop"]) or risk != Decimal(value["executable_initial_r"]):
                raise ValueError("PROJECTION")
            if value.get("kind") == "ENTRY" and (
                    Decimal(value["stop_price"]) != stop
                    or Decimal(value["reference_price"]) != Decimal(value["reference_entry"])
                    or value["expected_position_quantity"] != (value["quantity"] if value["direction"] == "LONG" else -value["quantity"])):
                raise ValueError("ENTRY_ACTION")
            sized = value["sizing"]
            base = size_position(Decimal(sized["current_realized_equity"]), Decimal(value["reference_entry"]), stop,
                                 ContractEconomics(authority.price_step, authority.tick_value, authority.trade_lot_size, True))
            recomputed = cap_r15_by_margin(
                realized_equity=Decimal(sized["current_realized_equity"]), entry=Decimal(value["reference_entry"]),
                stop=stop, price_step=authority.price_step, tick_value=authority.tick_value, r15_quantity=base.quantity,
                available_cash=Decimal(sized["available_cash"]), direction=value["direction"],
                initial_margin=authority.initial_margin(value["direction"]), trade_lot_size=authority.trade_lot_size)
            if (recomputed.evidence() != sized or value["quantity"] != recomputed.final_quantity
                    or Decimal(value["risk_cash"]) != recomputed.risk_cash
                    or Decimal(value["margin_reservation"]) != recomputed.final_quantity * recomputed.initial_margin
                    or Decimal(value["reference_initial_loss_cash"]) != recomputed.final_quantity * recomputed.loss_per_contract):
                raise ValueError("SIZING")
        except Exception as exc:
            raise ProductionRuntimeError("EXECUTION_DURABLE_EVIDENCE_INVALID") from exc

    def close(self) -> None:
        self.store.close()

    def _validate_instrument_authority(self, authority: InstrumentAuthority) -> None:
        row = self.registry.get(authority.instrument)
        if row is None:
            raise ProductionRuntimeError("ENTRY_AUTHORITY_INSTRUMENT_MISMATCH")
        try:
            valid = (
                authority.finam_symbol == row["finam_symbol"]
                and authority.price_step == Decimal(row["price_step"])
                and authority.tick_value == Decimal(row["tick_value"])
                and authority.trade_lot_size == int(row["quantity_granularity"])
                and type(authority.trade_lot_size) is int
                and all(v.is_finite() and v > 0 for v in (
                    authority.price_step, authority.tick_value,
                    authority.long_initial_margin, authority.short_initial_margin))
                and authority.long_initial_margin > 0
                and authority.short_initial_margin > 0
            )
        except (KeyError, ValueError, ArithmeticError):
            valid = False
        if not valid:
            raise ProductionRuntimeError("INSTRUMENT_AUTHORITY_NOT_FROZEN")

    def open_positions(self) -> dict[str, dict[str, Any]]:
        value = self.store.get("production_positions", {})
        if not isinstance(value, dict):
            raise ProductionRuntimeError("PRODUCTION_POSITION_STATE_INVALID")
        if self.execution_revision:
            for instrument, position in value.items():
                self._validate_execution_evidence(position)
                try:
                    step = position["instrument_authority"]["price_step"]
                    if self.store.get(f"last_managed_h1:{instrument}") != position["last_processed_h1"]:
                        raise ValueError("POSITION_WATERMARK")
                    if position["instrument"] != instrument or position["trail1"]["direction"] != position["direction"]:
                        raise ValueError("POSITION_IDENTITY")
                    if Decimal(str(position["initial_stop"])) != Decimal(position["executable_initial_stop"]):
                        raise ValueError("INITIAL_STOP")
                    verified = position["verified_fill_entry"]
                    entry = position["reference_entry"] if verified is None else verified
                    if Decimal(str(position["entry"])) != decimal_price(entry):
                        raise ValueError("ENTRY_AUTHORITY")
                    if verified is None and (position["fill_authority"] != "MISSING" or position["actual_initial_loss_cash"] is not None):
                        raise ValueError("MISSING_FILL_MUST_NOT_CLAIM_RISK")
                    require_on_grid(position["current_stop"], step)
                    candidate = position["trail1"]["stored_candidate"]
                    if candidate is not None:
                        require_on_grid(candidate, step)
                except Exception as exc:
                    raise ProductionRuntimeError("EXECUTION_POSITION_STATE_INVALID") from exc
        return value

    def _save_positions(self, positions: dict[str, dict[str, Any]]) -> None:
        self.store.put("production_positions", positions)

    def current_realized_equity(self) -> Decimal | None:
        value = self.store.get("realized_equity")
        return None if value is None else Decimal(str(value))

    def set_realized_equity(self, value: Decimal) -> None:
        if value <= 0:
            raise ProductionRuntimeError("REALIZED_EQUITY_INVALID")
        self.store.put("realized_equity", str(value))

    @_atomic
    def build_latest_signal(self, instrument: str, h1: pd.DataFrame, now) -> SignalIntent | None:
        if instrument not in INSTRUMENTS:
            raise ProductionRuntimeError("INSTRUMENT_NOT_N4")
        if self.store.unresolved_intent_count() != 0:
            raise ProductionRuntimeError("UNRESOLVED_INTENT_BLOCKS_SIGNAL_EVALUATION")
        if self.open_positions().get(instrument) is not None:
            return None
        pending_key = f"pending_signal:{instrument}"
        pending = self.store.get(pending_key)
        if pending is not None:
            if not isinstance(pending, dict):
                raise ProductionRuntimeError("PENDING_SIGNAL_STATE_INVALID")
            if self.execution_revision:
                execution, _ = self.context_builder.build(h1, now)
                if execution.empty or pending["timestamp"] != execution.index[-1].isoformat():
                    raise ProductionRuntimeError("STALE_PENDING_SIGNAL_REQUIRES_REVIEW")
            return _signal_from_dict(pending)
        execution, context = self.context_builder.build(h1, now)
        if execution.empty:
            return None
        timestamp = execution.index[-1]
        evaluated_key = f"last_evaluated_h1:{instrument}"
        if self.store.get(evaluated_key) == timestamp.isoformat():
            return None
        eligible = context.loc[context.index <= timestamp]
        if eligible.empty:
            return None
        row = execution.iloc[-1]
        higher = eligible.iloc[-1]
        if pd.isna(row.ATR):
            return None
        bar = CompletedBar(
            timestamp.to_pydatetime(),
            float(row.Open), float(row.High), float(row.Low), float(row.Close), float(row.ATR),
            None if pd.isna(row.PriorHigh) else float(row.PriorHigh),
            None if pd.isna(row.PriorLow) else float(row.PriorLow),
        )
        ctx = T3Context(
            float(higher.Close), float(higher.EMA100), float(higher.EMA100Slope),
            float(higher.ADX), float(higher.ATR), float(higher.ATRMean20),
            None if pd.isna(higher.EMA50) else float(higher.EMA50),
            None if pd.isna(higher.EMA200) else float(higher.EMA200),
        )
        sequence_key = f"signal_sequence:{instrument}"
        sequence = int(self.store.get(sequence_key, 0)) + 1
        signal = self.core.signal(instrument, bar, ctx, sequence)
        if signal is not None:
            self.store.put(sequence_key, sequence)
            self.store.put(pending_key, _signal_to_dict(signal))
        else:
            self.store.put(evaluated_key, timestamp.isoformat())
        return signal

    def begin_batch(self, *, realized_equity: Decimal, available_cash: Decimal) -> MarginBatchBudget:
        if realized_equity <= 0 or available_cash < 0:
            raise ProductionRuntimeError("BATCH_FINANCIAL_AUTHORITY_INVALID")
        persisted = self.current_realized_equity()
        if persisted is None:
            self.set_realized_equity(realized_equity)
        elif persisted != realized_equity:
            raise ProductionRuntimeError("UNEXPLAINED_REALIZED_EQUITY_DISCREPANCY")
        return MarginBatchBudget(available_cash)

    def _aggregate_open_initial_risk(self) -> Decimal:
        total = Decimal("0")
        for value in self.open_positions().values():
            try:
                total += Decimal(str(value["risk_cash"]))
            except Exception as exc:
                raise ProductionRuntimeError("PRODUCTION_POSITION_STATE_INVALID") from exc
        return total

    def _consume_pending_signal(self, signal: SignalIntent) -> None:
        key = f"pending_signal:{signal.instrument}"
        pending = self.store.get(key)
        if pending is None:
            if self.execution_revision:
                self.store.put(f"last_evaluated_h1:{signal.instrument}", signal.timestamp.isoformat())
            return
        if not isinstance(pending, dict) or pending.get("signal_id") != signal.signal_id:
            raise ProductionRuntimeError("PENDING_SIGNAL_IDENTITY_MISMATCH")
        self.store.put(f"last_evaluated_h1:{signal.instrument}", signal.timestamp.isoformat())
        self.store.put(key, None)

    @_atomic
    def plan_entry(self, signal: SignalIntent, authority: InstrumentAuthority,
                   *, realized_equity: Decimal, budget: MarginBatchBudget) -> RuntimeAction:
        if signal.instrument != authority.instrument or signal.instrument not in INSTRUMENTS:
            raise ProductionRuntimeError("ENTRY_AUTHORITY_INSTRUMENT_MISMATCH")
        self._validate_instrument_authority(authority)
        if self.open_positions().get(signal.instrument) is not None:
            raise ProductionRuntimeError("PYRAMIDING_NOT_AUTHORIZED")
        if self.execution_revision and any(p.get("verified_fill_entry") is None for p in self.open_positions().values()):
            raise ProductionRuntimeError("ACTUAL_FILL_AUTHORITY_BLOCKS_NEW_ENTRY")
        if self.store.unresolved_intent_count() != 0:
            raise ProductionRuntimeError("UNRESOLVED_INTENT_BLOCKS_NEW_ENTRY")
        contract = ContractEconomics(
            authority.price_step, authority.tick_value, authority.trade_lot_size, True)
        entry = Decimal(str(signal.entry))
        stop = Decimal(str(signal.initial_stop))
        if self.execution_revision:
            try:
                decimal_price(realized_equity)
                stop, executable_r = initial_projection(signal.direction, entry, stop, authority.price_step)
                decimal_price(signal.initial_r)
            except ValueError as exc:
                raise ProductionRuntimeError(str(exc)) from exc
        try:
            base = size_position(
                realized_equity, entry, stop, contract)
        except ValueError as exc:
            if str(exc) != "STOP_NOT_ON_TICK_GRID":
                raise
            self._consume_pending_signal(signal)
            return self._action(
                "SKIP_STOP_NOT_ON_TICK_GRID", None, signal.instrument, authority.finam_symbol,
                signal.direction, 0, signal.trade_id, signal.signal_id,
                Decimal(str(signal.entry)), Decimal(str(signal.initial_stop)), 0,
                "STOP_NOT_ON_TICK_GRID",
            )
        sized = cap_r15_by_margin(
            realized_equity=realized_equity,
            entry=Decimal(str(signal.entry)),
            stop=stop,
            price_step=authority.price_step,
            tick_value=authority.tick_value,
            r15_quantity=base.quantity,
            available_cash=budget.remaining,
            direction=signal.direction,
            initial_margin=authority.initial_margin(signal.direction),
            trade_lot_size=authority.trade_lot_size,
        )
        if sized.final_quantity == 0:
            self._consume_pending_signal(signal)
            return self._action(
                "SKIP_ZERO_CAPACITY", None, signal.instrument, authority.finam_symbol,
                signal.direction, 0, signal.trade_id, signal.signal_id,
                entry, stop, 0,
                "INSUFFICIENT_R15_OR_MARGIN_CAPACITY",
            )

        actual_risk = sized.loss_per_contract * sized.final_quantity
        frozen_risk_cash = sized.risk_cash
        limit = realized_equity * Decimal(str(self.spec.maximum_nominal_risk))
        if self._aggregate_open_initial_risk() + frozen_risk_cash > limit:
            self._consume_pending_signal(signal)
            return self._action(
                "SKIP_RISK_LIMIT", None, signal.instrument, authority.finam_symbol,
                signal.direction, 0, signal.trade_id, signal.signal_id,
                entry, stop, 0,
                "MAXIMUM_NOMINAL_INITIAL_RISK_EXCEEDED",
            )
        reservation = sized.initial_margin * sized.final_quantity
        if actual_risk > realized_equity * Decimal("0.015"):
            raise ProductionRuntimeError("REFERENCE_R15_RISK_EXCEEDED")
        if reservation > budget.remaining:
            raise ProductionRuntimeError("LOCAL_MARGIN_OVERALLOCATION")

        key = f"stage8.12:{signal.trade_id}:entry"
        expected = sized.final_quantity if signal.direction == "LONG" else -sized.final_quantity
        payload = self._action(
            "ENTRY", key, signal.instrument, authority.finam_symbol, signal.direction,
            sized.final_quantity, signal.trade_id, signal.signal_id,
            entry, stop, expected,
        ).payload()
        payload.update({
            "risk_cash": str(frozen_risk_cash),
            "actual_initial_loss_cash": str(actual_risk),
            "loss_per_contract": str(sized.loss_per_contract),
            "initial_margin": str(sized.initial_margin),
            "r15_quantity": sized.r15_quantity,
            "margin_quantity": sized.margin_quantity,
            # Persist the exact completed H1 signal close. Production position
            # management must never process the entry candle as a later bar.
            "signal_timestamp": signal.timestamp.isoformat(),
        })
        if self.execution_revision:
            evidence = self._authority_evidence(authority)
            payload.update({
                "reference_entry": str(entry), "verified_fill_entry": None,
                "fill_authority": "MISSING", "raw_initial_stop": str(signal.initial_stop),
                "raw_initial_r": str(signal.initial_r),
                "executable_initial_stop": str(stop), "executable_initial_r": str(executable_r),
                "reference_initial_loss_cash": str(actual_risk),
                "actual_initial_loss_cash": None,
                "instrument_authority": evidence,
                "specification_fingerprint": authority_fingerprint(evidence),
                "sizing": sized.evidence(), "margin_reservation": str(reservation),
                "last_processed_h1": signal.timestamp.isoformat(),
            })
        if not self.store.persist_intent(key, payload):
            existing = self.store.intent(key)
            if existing is None or existing["payload"] != payload:
                raise ProductionRuntimeError("IDEMPOTENCY_PAYLOAD_MISMATCH")
            raise ProductionRuntimeError("DUPLICATE_ENTRY_INTENT")
        self._consume_pending_signal(signal)
        budget.remaining -= reservation
        return self._action(
            "ENTRY", key, signal.instrument, authority.finam_symbol, signal.direction,
            sized.final_quantity, signal.trade_id, signal.signal_id,
            entry, stop, expected,
        )

    def _protective_stop_action_from_payload(self, payload: dict[str, Any]) -> RuntimeAction:
        return self._action(
            payload["kind"], payload["idempotency_key"], payload["instrument"],
            payload["finam_symbol"], payload["direction"], int(payload["quantity"]),
            payload.get("trade_id"), payload.get("signal_id"),
            Decimal(payload["reference_price"]) if payload.get("reference_price") is not None else None,
            Decimal(payload["stop_price"]) if payload.get("stop_price") is not None else None,
            payload.get("expected_position_quantity"), payload.get("reason"),
        )

    @_atomic
    def confirm_entry_position(self, entry_key: str, observed_quantity: int, *,
                               verified_fill_entry: Decimal | None = None,
                               fill_authority: str | None = None) -> RuntimeAction | None:
        intent = self.store.intent(entry_key)
        if not intent or intent["payload"].get("kind") != "ENTRY":
            raise ProductionRuntimeError("ENTRY_INTENT_NOT_FOUND")
        payload = intent["payload"]
        if self.execution_revision:
            self._validate_execution_evidence(payload)
            # This explicit handoff is for order-incapable offline verification.
            # No current FINAM caller can manufacture a verified fill.
            if verified_fill_entry is not None:
                if fill_authority != "OFFLINE_SYNTHETIC_VERIFIED":
                    raise ProductionRuntimeError("ACTUAL_FILL_AUTHORITY_UNVERIFIED")
                verified_fill_entry = decimal_price(verified_fill_entry)
                if (payload["direction"] == "LONG" and verified_fill_entry <= Decimal(payload["stop_price"])
                        or payload["direction"] == "SHORT" and verified_fill_entry >= Decimal(payload["stop_price"])):
                    raise ProductionRuntimeError("FILL_BEYOND_INITIAL_STOP_REQUIRES_REVIEW")
        expected = payload.get("expected_position_quantity")
        if type(expected) is not int or type(observed_quantity) is not int:
            raise ProductionRuntimeError("POSITION_AUTHORITY_SCHEMA_INVALID")

        positions = self.open_positions()
        current = positions.get(payload["instrument"])
        if observed_quantity == 0:
            if intent["status"] == "RECONCILED" or current is not None:
                raise ProductionRuntimeError("ENTRY_POSITION_STATE_BROKER_MISMATCH")
            return None
        if observed_quantity != expected:
            raise ProductionRuntimeError("POSITION_AUTHORITY_UNEXPECTED_QUANTITY")
        if intent["status"] in {"CANCELLED", "REJECTED", "CLOSED"}:
            raise ProductionRuntimeError("TERMINAL_ENTRY_INTENT_HAS_BROKER_POSITION")
        if self.execution_revision and current is None and intent["status"] == "RECONCILED":
            raise ProductionRuntimeError("ENTRY_RECONCILED_POSITION_MISSING_REQUIRES_REVIEW")

        if current is None:
            direction = payload["direction"]
            entry = float(payload["reference_price"])
            stop = float(payload["stop_price"])
            trail = Trail1State(direction, entry, stop)
            position = PositionState(
                payload["instrument"], direction, entry, stop, stop, entry, trail)
            meta = {
                "finam_symbol": payload["finam_symbol"],
                "quantity": payload["quantity"],
                "risk_cash": payload["risk_cash"],
                "actual_initial_loss_cash": payload["actual_initial_loss_cash"],
                "loss_per_contract": payload["loss_per_contract"],
                "trade_id": payload["trade_id"],
                "signal_id": payload["signal_id"],
                "signal_timestamp": payload["signal_timestamp"],
                "protective_stop_state": "PENDING",
                "protective_stop_revision": 0,
            }
            if self.execution_revision:
                position.entry = Decimal(payload["reference_price"])
                position.initial_stop = Decimal(payload["stop_price"])
                position.current_stop = Decimal(payload["stop_price"])
                position.favorable_extreme = position.entry
                meta.update({k: payload[k] for k in (
                    "execution_revision", "reference_entry", "raw_initial_stop", "raw_initial_r",
                    "executable_initial_stop", "executable_initial_r", "instrument_authority",
                    "specification_fingerprint", "sizing", "margin_reservation",
                    "reference_initial_loss_cash", "last_processed_h1")})
                meta["verified_fill_entry"] = None if verified_fill_entry is None else str(verified_fill_entry)
                meta["fill_authority"] = "MISSING" if verified_fill_entry is None else fill_authority
                meta["actual_initial_r"] = None
                if verified_fill_entry is not None:
                    # Actual price may be a weighted average off-grid. Never
                    # round it or reuse size_position's integral-tick rule.
                    actual_r = abs(verified_fill_entry - Decimal(payload["stop_price"]))
                    actual_cash = actual_r / Decimal(payload["price_step"]) * Decimal(payload["instrument_authority"]["tick_value"]) * payload["quantity"]
                    meta.update(actual_initial_r=str(actual_r), actual_initial_loss_cash=str(actual_cash))
                    position.entry = verified_fill_entry
                    position.favorable_extreme = verified_fill_entry
                    position.trail1 = Trail1State(direction, float(verified_fill_entry), stop)
            positions[payload["instrument"]] = _position_to_dict(position, meta)
            self._save_positions(positions)
            # Entry candle exclusion is part of the frozen causal lifecycle.
            watermark_key = f"last_managed_h1:{payload['instrument']}"
            existing_watermark = self.store.get(watermark_key)
            if existing_watermark is None:
                self.store.put(watermark_key, payload["signal_timestamp"])
            elif self.execution_revision and existing_watermark <= payload["signal_timestamp"]:
                self.store.put(watermark_key, payload["signal_timestamp"])
            elif existing_watermark != payload["signal_timestamp"]:
                raise ProductionRuntimeError("ENTRY_SIGNAL_WATERMARK_MISMATCH")
            current = positions[payload["instrument"]]
        elif current.get("trade_id") != payload.get("trade_id"):
            raise ProductionRuntimeError("ENTRY_POSITION_ALREADY_EXISTS")
        elif self.execution_revision and verified_fill_entry is not None and current.get("verified_fill_entry") != str(verified_fill_entry):
            raise ProductionRuntimeError("FILL_AUTHORITY_CHANGED_REQUIRES_REVIEW")

        if intent["status"] != "RECONCILED":
            broker_id = intent.get("broker_order_id")
            self.store.transition_intent(entry_key, "FILL", broker_id)
            self.store.transition_intent(entry_key, "RECONCILED", broker_id)

        stop_key = f"stage8.12:{payload['trade_id']}:stop:0000"
        stop_intent = self.store.intent(stop_key)
        if current.get("protective_stop_state") == "ACTIVE":
            if not stop_intent or stop_intent["status"] != "RECONCILED":
                raise ProductionRuntimeError("PROTECTIVE_STOP_STATE_MISMATCH")
            return None
        if current.get("protective_stop_state") != "PENDING":
            raise ProductionRuntimeError("PROTECTIVE_STOP_STATE_MISMATCH")

        if stop_intent is None:
            stop_action = self._action(
                "PROTECTIVE_STOP_INSTALL", stop_key, payload["instrument"], payload["finam_symbol"],
                payload["direction"], payload["quantity"], payload["trade_id"], payload["signal_id"],
                Decimal(payload["reference_price"]), Decimal(payload["stop_price"]), expected,
            )
            stop_payload = stop_action.payload()
            if self.execution_revision:
                stop_payload.update(self._stop_evidence(current))
            if not self.store.persist_intent(stop_key, stop_payload):
                raise ProductionRuntimeError("DUPLICATE_PROTECTIVE_STOP_INTENT")
            return stop_action
        if stop_intent["payload"].get("kind") != "PROTECTIVE_STOP_INSTALL":
            raise ProductionRuntimeError("PROTECTIVE_STOP_STATE_MISMATCH")
        return self._protective_stop_action_from_payload(stop_intent["payload"])

    def _stop_evidence(self, position: dict) -> dict:
        return {k: position[k] for k in (
            "specification_fingerprint", "instrument_authority", "raw_initial_stop", "raw_initial_r",
            "reference_entry", "verified_fill_entry", "fill_authority", "executable_initial_stop",
            "executable_initial_r", "last_processed_h1", "sizing", "risk_cash",
            "reference_initial_loss_cash", "margin_reservation")}


    @_atomic
    def confirm_protective_stop(self, stop_key: str, broker_order_id: str) -> None:
        if not broker_order_id:
            raise ProductionRuntimeError("PROTECTIVE_STOP_BROKER_ID_REQUIRED")
        intent = self.store.intent(stop_key)
        if not intent or intent["payload"].get("kind") not in {
            "PROTECTIVE_STOP_INSTALL", "PROTECTIVE_STOP_REPLACE"
        }:
            raise ProductionRuntimeError("PROTECTIVE_STOP_INTENT_NOT_FOUND")
        payload = intent["payload"]
        if self.execution_revision:
            self._validate_execution_evidence(payload)
            require_on_grid(payload["stop_price"], payload["price_step"])
        positions = self.open_positions()
        current = positions.get(payload["instrument"])
        if current is None or current.get("trade_id") != payload.get("trade_id"):
            raise ProductionRuntimeError("PROTECTIVE_STOP_POSITION_MISMATCH")

        recorded_broker_id = intent.get("broker_order_id")
        if intent["status"] == "RECONCILED":
            if recorded_broker_id != broker_order_id:
                raise ProductionRuntimeError("PROTECTIVE_STOP_BROKER_ID_MISMATCH")
            if (
                current.get("protective_stop_state") == "ACTIVE"
                and current.get("protective_stop_broker_order_id") == broker_order_id
                and str(current.get("protective_stop_price")) == str(payload["stop_price"])
            ):
                return
        else:
            self.store.transition_intent(stop_key, "ACK", broker_order_id)
            self.store.transition_intent(stop_key, "RECONCILED", broker_order_id)

        current["protective_stop_state"] = "ACTIVE"
        current["protective_stop_broker_order_id"] = broker_order_id
        current["protective_stop_price"] = payload["stop_price"]
        positions[payload["instrument"]] = current
        self._save_positions(positions)


    @_atomic
    def broker_exit_observed(self, instrument: str, *, realized_equity_after_exit: Decimal,
                             protective_stop_terminal: bool) -> RuntimeAction:
        positions = self.open_positions()
        current = positions.get(instrument)
        if current is None:
            raise ProductionRuntimeError("BROKER_EXIT_WITHOUT_LOCAL_POSITION")
        if protective_stop_terminal is not True:
            raise ProductionRuntimeError("PROTECTIVE_STOP_TERMINAL_PROOF_REQUIRED")
        if realized_equity_after_exit <= 0:
            raise ProductionRuntimeError("REALIZED_EQUITY_INVALID")
        action = self._action(
            "BROKER_EXIT_OBSERVED", None, instrument, current["finam_symbol"],
            current["direction"], current["quantity"], current["trade_id"], current["signal_id"],
            Decimal(str(current["entry"])), Decimal(str(current["current_stop"])), 0,
            "POSITION_AUTHORITY_FLAT",
        )
        positions.pop(instrument)
        self._save_positions(positions)
        self.set_realized_equity(realized_equity_after_exit)
        return action

    @_atomic
    def manage_completed_bar(self, instrument: str, bar: CompletedBar,
                             *, observed_position_quantity: int) -> RuntimeAction | None:
        if self.store.unresolved_intent_count() != 0:
            raise ProductionRuntimeError("UNRESOLVED_INTENT_BLOCKS_BAR_PROCESSING")
        watermark_key = f"last_managed_h1:{instrument}"
        prior_watermark = self.store.get(watermark_key)
        if prior_watermark is not None and bar.timestamp.isoformat() <= prior_watermark:
            raise ProductionRuntimeError("DUPLICATE_OR_NON_MONOTONIC_BAR")
        positions = self.open_positions()
        value = positions.get(instrument)
        if value is None:
            if observed_position_quantity != 0:
                raise ProductionRuntimeError("UNEXPECTED_BROKER_POSITION")
            return None
        expected = int(value["quantity"]) if value["direction"] == "LONG" else -int(value["quantity"])
        if observed_position_quantity == 0:
            return self._action(
                "BROKER_EXIT_OBSERVED", None, instrument, value["finam_symbol"],
                value["direction"], value["quantity"], value["trade_id"], value["signal_id"],
                Decimal(str(value["entry"])), Decimal(str(value["current_stop"])), 0,
                "POSITION_AUTHORITY_FLAT",
            )
        if observed_position_quantity != expected:
            raise ProductionRuntimeError("POSITION_AUTHORITY_UNEXPECTED_QUANTITY")
        if value.get("protective_stop_state") != "ACTIVE":
            raise ProductionRuntimeError("PROTECTIVE_STOP_NOT_ACTIVE")
        if self.execution_revision and value.get("verified_fill_entry") is None:
            raise ProductionRuntimeError("ACTUAL_FILL_AUTHORITY_BLOCKS_BAR_PROCESSING")

        position = _position_from_dict(value)
        previous_stop = position.current_stop
        outcome = (manage_executable(self.core, position, bar, value["instrument_authority"]["price_step"])
                   if self.execution_revision else self.core.manage(position, bar))
        if self.execution_revision:
            value["last_processed_h1"] = bar.timestamp.isoformat()
            if "raw_candidate" in outcome:
                value["raw_trail1_candidate"] = outcome["raw_candidate"]
        value.update(_position_to_dict(position, {
            k: value[k] for k in (
                "finam_symbol", "quantity", "risk_cash", "actual_initial_loss_cash",
                "loss_per_contract", "trade_id", "signal_id", "signal_timestamp",
                "protective_stop_state", "protective_stop_revision"
            )
        }))
        if "protective_stop_broker_order_id" in positions[instrument]:
            value["protective_stop_broker_order_id"] = positions[instrument]["protective_stop_broker_order_id"]
        if "protective_stop_price" in positions[instrument]:
            value["protective_stop_price"] = positions[instrument]["protective_stop_price"]
        positions[instrument] = value
        self._save_positions(positions)
        self.store.put(watermark_key, bar.timestamp.isoformat())

        if outcome["event"] == "EXIT":
            key = f"stage8.12:{value['trade_id']}:emergency-exit:{bar.timestamp.isoformat()}"
            action = self._action(
                "EMERGENCY_EXIT_REQUIRED", key, instrument, value["finam_symbol"],
                value["direction"], value["quantity"], value["trade_id"], value["signal_id"],
                Decimal(str(outcome["fill"])), Decimal(str(position.current_stop)), 0,
                "PROTECTIVE_STOP_DIVERGENCE_POSITION_STILL_OPEN",
            )
            action_payload = action.payload()
            if self.execution_revision:
                action_payload.update(self._stop_evidence(value))
            if not self.store.persist_intent(key, action_payload):
                raise ProductionRuntimeError("DUPLICATE_EMERGENCY_EXIT_INTENT")
            return action

        if position.current_stop != previous_stop:
            revision = int(value["protective_stop_revision"]) + 1
            key = f"stage8.12:{value['trade_id']}:stop:{revision:04d}"
            action = self._action(
                "PROTECTIVE_STOP_REPLACE", key, instrument, value["finam_symbol"],
                value["direction"], value["quantity"], value["trade_id"], value["signal_id"],
                Decimal(str(position.entry)), Decimal(str(position.current_stop)), expected,
                "TIGHTER_PERCENT_POSITION_STOP_REQUIRED",
            )
            action_payload = action.payload()
            if self.execution_revision:
                action_payload.update(self._stop_evidence(value))
            if not self.store.persist_intent(key, action_payload):
                raise ProductionRuntimeError("DUPLICATE_PROTECTIVE_STOP_INTENT")
            positions = self.open_positions()
            positions[instrument]["protective_stop_state"] = "PENDING_REPLACE"
            positions[instrument]["protective_stop_revision"] = revision
            self._save_positions(positions)
            return action
        return None
