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
from decimal import Decimal, localcontext
from fractions import Fraction
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
AMENDED_RUNTIME_SCHEMA = "stage8_12_production_runtime.stop_tick_grid.v2"
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
    return {k: str(v) if isinstance(v, (Decimal, Fraction)) else v for k, v in result.items()}


def _trail_from_dict(value: dict[str, Any], number=lambda value: float(Fraction(str(value)))) -> Trail1State:
    state = Trail1State(
        value["direction"],
        number(value["entry_price"]),
        number(value["initial_stop_price"]),
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


def _stop_text(value):
    if isinstance(value,Fraction):
        remainder=value.denominator
        for factor in (2,5):
            while remainder%factor==0:
                remainder//=factor
        if remainder != 1:
            raise ValueError("EXECUTABLE_STOP_DECIMAL_INVALID")
        with localcontext() as context:
            context.prec=len(str(abs(value.numerator)))+len(str(value.denominator))+1
            return str(Decimal(value.numerator)/Decimal(value.denominator))
    return str(value) if isinstance(value,Decimal) else value


def _position_to_dict(position: PositionState, meta: dict[str, Any]) -> dict[str, Any]:
    return {
        **meta,
        "instrument": position.instrument,
        "direction": position.direction,
        "entry": str(position.entry) if isinstance(position.entry, (Decimal, Fraction)) else position.entry,
        "initial_stop": _stop_text(position.initial_stop),
        "current_stop": _stop_text(position.current_stop),
        "favorable_extreme": str(position.favorable_extreme) if isinstance(position.favorable_extreme, (Decimal, Fraction)) else position.favorable_extreme,
        "trail1": _trail_to_dict(position.trail1),
    }


def _position_from_dict(value: dict[str, Any]) -> PositionState:
    number = (lambda value: Fraction(str(value))) if value.get("fill_price_exact") else ((lambda value: Decimal(str(value))) if value.get("execution_revision") else float)
    return PositionState(
        instrument=value["instrument"],
        direction=value["direction"],
        entry=number(value["entry"]),
        initial_stop=number(value["initial_stop"]),
        current_stop=number(value["current_stop"]),
        favorable_extreme=number(value["favorable_extreme"]),
        trail1=_trail_from_dict(value["trail1"], number),
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
                for key in {fill["entry_key"] for fill in self.store.all_fills()}:
                    self._validated_order_fills(key)
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
        result = {k: str(v) if isinstance(v, (Decimal, Fraction)) else v for k, v in asdict(authority).items()}
        result["registry_fingerprint"] = authority_fingerprint(self.registry[authority.instrument])
        return result

    def _validate_execution_evidence(self, value: dict) -> None:
        # Reproduce the persisted sizing context, independent of fill display precision.
        with localcontext() as context:
            context.prec = 28
            self._validate_execution_evidence_decimal(value)

    def _validate_execution_evidence_decimal(self, value: dict) -> None:
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
            if (recomputed.evidence() != sized or value.get("planned_quantity", value["quantity"]) != recomputed.final_quantity
                    or type(value["quantity"]) is not int or not 0 < value["quantity"] <= recomputed.final_quantity
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
                and row.get("currency") == "RUB"
                and "MOEX frozen tick-value reference" in row.get("authority", "")
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
                    if Fraction(str(position["initial_stop"])) != Fraction(position["executable_initial_stop"]):
                        raise ValueError("INITIAL_STOP")
                    verified = position["verified_fill_entry"]
                    entry = position["reference_entry"] if verified is None else verified
                    if Fraction(str(position["entry"])) != Fraction(str(entry)):
                        raise ValueError("ENTRY_AUTHORITY")
                    if verified is None and (position["fill_authority"] != "MISSING" or position["actual_initial_loss_cash"] is not None):
                        raise ValueError("MISSING_FILL_MUST_NOT_CLAIM_RISK")
                    if position["fill_authority"] not in {"MISSING", "OFFLINE_SYNTHETIC_VERIFIED", "FINAM_ACCOUNT_TRADE"}:
                        raise ValueError("FILL_AUTHORITY_UNKNOWN")
                    if position["fill_authority"] == "FINAM_ACCOUNT_TRADE" and not position.get("fill_price_exact"):
                        raise ValueError("DURABLE_FILL_PRICE_MISSING")
                    if position.get("fill_price_exact"):
                        self._validate_durable_fill_position(position)
                    self._validate_protective_position(position)
                    require_on_grid(Fraction(str(position["current_stop"])), step)
                    candidate = position["trail1"]["stored_candidate"]
                    if candidate is not None:
                        require_on_grid(candidate, step)
                except Exception as exc:
                    raise ProductionRuntimeError("EXECUTION_POSITION_STATE_INVALID") from exc
        return value

    def _validate_protective_position(self, position: dict) -> None:
        state=position["protective_stop_state"]
        covered=position["protective_covered_quantity"]
        if type(covered) is not int or covered<0:
            raise ValueError("PROTECTIVE_COVERAGE_SCHEMA_INVALID")
        if state == "PENDING":
            if covered != 0 or position.get("protective_stop_broker_order_id"):
                raise ValueError("PENDING_STOP_MUST_NOT_CLAIM_COVERAGE")
            return
        if state not in {"ACTIVE","PENDING_REPLACE"}:
            raise ValueError("PROTECTIVE_STATE_INVALID")
        broker_id=position["protective_stop_broker_order_id"]
        rows=[r for r in self.store.all_intents() if r["broker_order_id"]==broker_id
              and r["payload"].get("kind") in {"PROTECTIVE_STOP_INSTALL","PROTECTIVE_STOP_REPLACE"}]
        if not broker_id or len(rows)!=1 or rows[0]["status"]!="RECONCILED":
            raise ValueError("DURABLE_STOP_PROOF_MISSING")
        row=rows[0];payload=row["payload"]
        submission=self.store.get(f"protective_submission:{row['idempotency_key']}")
        expected=abs(submission["position_quantity"]) if submission else payload["quantity"]
        if (covered!=expected or covered<=0 or covered>position["planned_quantity"]
                or payload["trade_id"]!=position["trade_id"] or payload["instrument"]!=position["instrument"]
                or Decimal(position["protective_stop_price"])!=Decimal(payload["stop_price"])):
            raise ValueError("DURABLE_STOP_COVERAGE_INVALID")
        if covered!=position["quantity"] and not self.store.get("execution_halt"):
            raise ValueError("UNCERTAIN_PROTECTION_MUST_HALT")

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
        evaluated = self.store.get(evaluated_key)
        if self.execution_revision and evaluated is not None and timestamp < pd.Timestamp(evaluated):
            raise ProductionRuntimeError("STALE_OR_NON_MONOTONIC_SIGNAL_H1")
        if evaluated == timestamp.isoformat():
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
        if self.execution_revision and self.store.get("execution_halt"):
            raise ProductionRuntimeError("HALTED_OPERATOR_INTERVENTION_REQUIRED")
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
                               fill_authority: str | None = None,
                               observed_protective_stop: Any = None) -> RuntimeAction | None:
        if self.execution_revision:
            return self._confirm_candidate_entry(
                entry_key, observed_quantity, verified_fill_entry=verified_fill_entry,
                fill_authority=fill_authority, observed_protective_stop=observed_protective_stop,
            )
        if observed_protective_stop is not None:
            raise ProductionRuntimeError("LEGACY_PROTECTION_OBSERVATION_NOT_SUPPORTED")
        intent = self.store.intent(entry_key)
        if not intent or intent["payload"].get("kind") != "ENTRY":
            raise ProductionRuntimeError("ENTRY_INTENT_NOT_FOUND")
        payload = intent["payload"]
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
            if not self.store.persist_intent(stop_key, stop_payload):
                raise ProductionRuntimeError("DUPLICATE_PROTECTIVE_STOP_INTENT")
            return stop_action
        if stop_intent["payload"].get("kind") != "PROTECTIVE_STOP_INSTALL":
            raise ProductionRuntimeError("PROTECTIVE_STOP_STATE_MISMATCH")
        return self._protective_stop_action_from_payload(stop_intent["payload"])

    def halt(self, reason: str) -> None:
        """Sticky candidate fault; reconciliation/protection may continue, trading may not."""
        if not self.execution_revision:
            raise ProductionRuntimeError("EXECUTION_REVISION_REQUIRED")
        previous = self.store.get("execution_halt", {})
        reasons = sorted(set(previous.get("reasons", [])) | {reason})
        self.store.put("execution_halt", {"status": "HALTED", "operator_intervention_required": True,
                                          "reasons": reasons, "execution_revision": self.execution_revision})

    @_atomic
    def record_entry_submission(self, entry_key: str, account_id: str, submitted_at: str) -> None:
        from .finam_fill_price_readonly import digest
        from .controlled_real_acceptance import _timestamp
        row = self.store.intent(entry_key)
        if not self.execution_revision or not row or row["payload"].get("kind") != "ENTRY":
            raise ProductionRuntimeError("ENTRY_INTENT_NOT_FOUND")
        self._validate_execution_evidence(row["payload"])
        if _timestamp(submitted_at) < _timestamp(row["payload"]["signal_timestamp"]):
            raise ProductionRuntimeError("ENTRY_SUBMISSION_PRECEDES_SIGNAL")
        identity = self.store.get("production_service_identity")
        if not account_id or identity and identity["account_hash"] != digest(account_id):
            raise ProductionRuntimeError("FILL_ACCOUNT_IDENTITY_MISMATCH")
        value = {"account_sha256": digest(account_id), "submitted_at": submitted_at,
                 "execution_revision": self.execution_revision}
        old = self.store.get(f"entry_submission:{entry_key}")
        if old is not None and old != value:
            raise ProductionRuntimeError("ENTRY_SUBMISSION_ALREADY_COMMITTED")
        if old is not None:
            if row["status"] == "INTENT_PERSISTED":
                raise ProductionRuntimeError("ENTRY_SUBMISSION_STATUS_MISMATCH")
            return
        if row["status"] != "INTENT_PERSISTED" or row["broker_order_id"] is not None:
            raise ProductionRuntimeError("ENTRY_SUBMISSION_BOUNDARY_MISSING")
        refusals = self.store.get(f"entry_pre_post_refusals:{entry_key}", [])
        if any(_timestamp(submitted_at) <= _timestamp(item["submission"]["submitted_at"]) for item in refusals):
            raise ProductionRuntimeError("ENTRY_SUBMISSION_TIME_REUSED_OR_REGRESSED")
        self.store.put(f"entry_submission:{entry_key}", value)
        self.store.transition_intent(entry_key, "SUBMITTED")

    @_atomic
    def restore_entry_pre_post(self, entry_key: str, account_id: str, submitted_at: str, reason: str) -> None:
        """Called only for EntryPrePostRefused; retain proof, release active authority."""
        from .finam_fill_price_readonly import digest
        row = self.store.intent(entry_key)
        if not self.execution_revision or not row or row["payload"].get("kind") != "ENTRY":
            raise ProductionRuntimeError("ENTRY_INTENT_NOT_FOUND")
        self._validate_execution_evidence(row["payload"])
        expected = {"account_sha256": digest(account_id), "submitted_at": submitted_at,
                    "execution_revision": self.execution_revision}
        proof = {"submission": expected, "outcome": "ENTRY_POST_NOT_CALLED", "reason": reason}
        active_key = f"entry_submission:{entry_key}"
        history_key = f"entry_pre_post_refusals:{entry_key}"
        active = self.store.get(active_key)
        history = self.store.get(history_key, [])
        if active is None and row["status"] == "INTENT_PERSISTED" and row["broker_order_id"] is None and proof in history:
            return
        if (active != expected or row["status"] != "SUBMITTED" or row["broker_order_id"] is not None
                or self.store.get(f"entry_fill_history:{entry_key}") is not None
                or self.open_positions().get(row["payload"]["instrument"]) is not None
                or any(fill["entry_key"] == entry_key for fill in self.store.all_fills())):
            raise ProductionRuntimeError("ENTRY_PRE_POST_RECOVERY_AUTHORITY_MISMATCH")
        self.store.put(history_key, history + [proof])
        self.store.put(active_key, None)
        self.store.transition_intent(entry_key, "INTENT_PERSISTED")

    def handoff_entry_history(self, entry_key: str, **history) -> dict:
        if not self.execution_revision:
            raise ProductionRuntimeError("EXECUTION_REVISION_REQUIRED")
        try:
            return self._handoff_entry_history(entry_key, **history)
        except Exception:
            # Facts roll back first; the durable halt survives the failed handoff.
            self.halt("FILL_HISTORY_AUTHORITY_UNVERIFIED")
            raise

    @_atomic
    def _handoff_entry_history(self, entry_key: str, *, account_id: str, broker_order_id: str,
                              response: dict, start: str, end: str, limit: int,
                              observed_at: str) -> dict:
        """Validate bounded AccountTrade history and atomically adopt execution facts.

        Account positions must have been reconciled first, so missing or delayed
        price history never postpones creation of the initial protective intent.
        XXX stays a feed label; only authenticated RUB tick economics value risk.
        """
        from .finam_fill_price_readonly import Target, analyze_history, digest
        from .controlled_real_acceptance import _timestamp
        row = self.store.intent(entry_key)
        submission = self.store.get(f"entry_submission:{entry_key}")
        if not self.execution_revision or not row or row["payload"].get("kind") != "ENTRY":
            raise ProductionRuntimeError("ENTRY_INTENT_NOT_FOUND")
        payload = row["payload"]
        self._validate_execution_evidence(payload)
        if (not submission or submission["account_sha256"] != digest(account_id)
                or not broker_order_id or row["broker_order_id"] != broker_order_id):
            raise ProductionRuntimeError("EXACT_DURABLE_FILL_IDENTITY_REQUIRED")
        if (_timestamp(start) > _timestamp(submission["submitted_at"])
                or _timestamp(end) != _timestamp(observed_at)
                or _timestamp(end) <= _timestamp(submission["submitted_at"])):
            raise ProductionRuntimeError("HISTORY_COVERAGE_OR_FRESHNESS_UNPROVEN")
        previous = self.store.get(f"entry_fill_history:{entry_key}")
        if previous and _timestamp(observed_at) < _timestamp(previous["observed_at"]):
            raise ProductionRuntimeError("STALE_FILL_HISTORY")
        target = Target(account_id, entry_key, broker_order_id, payload["finam_symbol"],
                        "SIDE_BUY" if payload["direction"] == "LONG" else "SIDE_SELL",
                        payload["quantity"], Decimal(payload["price_step"]))
        report = analyze_history(response, target, start, end, limit)
        facts = {fact["trade_id_sha256"]: fact for fact in report["matched_unique_fills"]}
        positions = self.open_positions()
        old = self.store.fills_for_order(broker_order_id)
        if any(fill["broker_trade_id_sha256"] not in facts for fill in old):
            raise ProductionRuntimeError("DURABLE_FILLS_MISSING_FROM_HISTORY")
        for source in response["trades"]:
            if source.get("order_id") != broker_order_id:
                continue
            fact = facts[digest(source["trade_id"])]
            if _timestamp(source["timestamp"]) < _timestamp(submission["submitted_at"]):
                raise ProductionRuntimeError("FILL_PRECEDES_ENTRY_SUBMISSION")
            fill = {"fill_id": "finam:"+digest(account_id)+":"+digest(source["trade_id"]),
                    "broker_order_id": broker_order_id, "broker_trade_id": source["trade_id"],
                    "broker_trade_id_sha256": digest(source["trade_id"]),
                    "trade_id": payload["trade_id"], "signal_id": payload["signal_id"],
                    "entry_key": entry_key, "quantity": fact["quantity"], "price": fact["price"],
                    "timestamp": [fact["utc_seconds"], fact["nanoseconds"]],
                    "account_sha256": digest(account_id), "symbol": target.symbol, "side": target.side,
                    "account_trade_currency": fact["account_trade_currency"],
                    "risk_currency": "RUB", "currency_conversion_performed": False,
                    "specification_fingerprint": payload["specification_fingerprint"],
                    "execution_revision": self.execution_revision}
            # SQL timestamp is text; nanoseconds are retained without float conversion.
            fill["timestamp"] = f"{fact['utc_seconds']}:{fact['nanoseconds']:09d}"
            self.store.persist_fill(fill, strict=True)
        self.store.put(f"entry_fill_history:{entry_key}", {
            "start": start, "end_exclusive": end, "observed_at": observed_at,
            "fill_set_sha256": report["fill_set_sha256"], "matched_quantity": report["matched_quantity"],
            "weighted_price_exact": report["weighted_price_exact"],
            "account_trade_currencies": report["account_trade_currencies"], "limit": limit})
        current = positions.get(payload["instrument"])
        if current is None or current["trade_id"] != payload["trade_id"]:
            raise ProductionRuntimeError("FILL_POSITION_HANDOFF_REQUIRED")
        current["filled_quantity"] = report["matched_quantity"]
        current["account_trade_currencies"] = report["account_trade_currencies"]
        current["risk_currency"] = "RUB"
        current["currency_conversion_performed"] = False
        if report["matched_quantity"] != current["quantity"]:
            self.halt("FILL_HISTORY_POSITION_QUANTITY_MISMATCH")
            current.update(verified_fill_entry=None, fill_authority="MISSING", actual_initial_loss_cash=None,
                           actual_initial_r=None)
            for key in ("fill_price_exact", "actual_initial_r_exact", "actual_initial_loss_cash_exact"):
                current.pop(key, None)
            current["entry"] = current["reference_entry"]
        else:
            mean = Fraction(int(report["weighted_price_exact"]["numerator"]),
                            int(report["weighted_price_exact"]["denominator"]))
            stop = Fraction(current["executable_initial_stop"])
            r = abs(mean-stop)
            cash = r / Fraction(payload["price_step"]) * Fraction(payload["instrument_authority"]["tick_value"]) * current["quantity"]
            exact = lambda v: {"numerator": str(v.numerator), "denominator": str(v.denominator)}
            current.update(entry=str(mean), verified_fill_entry=str(mean), fill_price_exact=exact(mean),
                           fill_authority="FINAM_ACCOUNT_TRADE", actual_initial_r=str(r),
                           actual_initial_r_exact=exact(r), actual_initial_loss_cash=str(cash),
                           actual_initial_loss_cash_exact=exact(cash),
                           actual_r15_within_reference_budget=cash <= Fraction(payload["risk_cash"]))
            wrong_side = mean <= stop if payload["direction"] == "LONG" else mean >= stop
            if wrong_side:
                self.halt("FILL_BEYOND_PRECOMMITTED_STOP")
            elif current["trail1"]["triggered"]:
                if Fraction(str(current["trail1"]["entry_price"])) != mean:
                    raise ProductionRuntimeError("FILL_CHANGE_AFTER_TRAIL1_STARTED")
            else:
                current["trail1"] = _trail_to_dict(Trail1State(payload["direction"], mean, stop))
                current["favorable_extreme"] = str(mean)
            if cash > Fraction(payload["risk_cash"]):
                self.halt("ACTUAL_R15_REFERENCE_BUDGET_EXCEEDED")
            terminal = self.store.get(f"entry_terminal:{entry_key}")
            if current["quantity"] == payload["quantity"] or terminal and terminal["order_id"] == broker_order_id:
                self.store.transition_intent(entry_key, "RECONCILED", broker_order_id)
        positions[payload["instrument"]] = current
        self._save_positions(positions)
        return report

    def _validated_order_fills(self, entry_key: str) -> list[dict]:
        from .controlled_real_acceptance import _timestamp
        from .finam_fill_price_readonly import digest
        row = self.store.intent(entry_key)
        submission = self.store.get(f"entry_submission:{entry_key}")
        if not row or not submission or not row["broker_order_id"]:
            raise ValueError("DURABLE_FILL_IDENTITY_MISSING")
        payload = row["payload"]
        if payload.get("kind") != "ENTRY":
            raise ValueError("DURABLE_FILL_ENTRY_REQUIRED")
        self._validate_execution_evidence(payload)
        service = self.store.get("production_service_identity")
        if service and service["account_hash"] != submission["account_sha256"]:
            raise ValueError("DURABLE_FILL_ACCOUNT_MISMATCH")
        fills = self.store.fills_for_order(row["broker_order_id"])
        for fill in fills:
            if (fill["broker_order_id"] != row["broker_order_id"] or fill["entry_key"] != entry_key or fill["trade_id"] != payload["trade_id"]
                    or fill["signal_id"] != payload["signal_id"]
                    or digest(fill["broker_trade_id"]) != fill["broker_trade_id_sha256"]
                    or fill["account_sha256"] != submission["account_sha256"]
                    or fill["symbol"] != payload["finam_symbol"]
                    or fill["side"] != ("SIDE_BUY" if payload["direction"] == "LONG" else "SIDE_SELL")
                    or fill["account_trade_currency"] not in {"RUB", "XXX"}
                    or fill["risk_currency"] != "RUB" or fill["currency_conversion_performed"] is not False
                    or fill["specification_fingerprint"] != payload["specification_fingerprint"]
                    or fill["execution_revision"] != self.execution_revision
                    or fill["fill_id"] != "finam:"+submission["account_sha256"]+":"+fill["broker_trade_id_sha256"]
                    or type(fill["quantity"]) is not int or fill["quantity"] <= 0):
                raise ValueError("DURABLE_FILL_IDENTITY_INVALID")
            require_on_grid(fill["price"], payload["price_step"])
            seconds,nanos = map(int,fill["timestamp"].split(":"))
            if not 0 <= nanos < 10**9 or (seconds,nanos) < _timestamp(submission["submitted_at"]):
                raise ValueError("DURABLE_FILL_TIME_INVALID")
        quantity=sum(fill["quantity"] for fill in fills)
        if quantity > payload["quantity"]:
            raise ValueError("DURABLE_FILLS_EXCEED_REQUEST")
        history=self.store.get(f"entry_fill_history:{entry_key}")
        if not history or history["matched_quantity"] != quantity:
            raise ValueError("DURABLE_FILL_HISTORY_MISSING")
        canonical=[]
        for fill in fills:
            seconds,nanos=map(int,fill["timestamp"].split(":"))
            if not _timestamp(history["start"]) <= (seconds,nanos) < _timestamp(history["end_exclusive"]):
                raise ValueError("DURABLE_FILL_HISTORY_TIME_INVALID")
            canonical.append({"trade_id_sha256":fill["broker_trade_id_sha256"],"quantity":fill["quantity"],
                              "price":fill["price"],"utc_seconds":seconds,"nanoseconds":nanos,
                              "account_trade_currency":fill["account_trade_currency"]})
        canonical.sort(key=lambda fact:fact["trade_id_sha256"])
        if digest(json.dumps(canonical,sort_keys=True,separators=(",",":"))) != history["fill_set_sha256"]:
            raise ValueError("DURABLE_FILL_HISTORY_FINGERPRINT_INVALID")
        return fills

    def _validate_durable_fill_position(self, position: dict) -> None:
        """Recompute authoritative price/risk from durable fills after every restart."""
        row = self.store.intent(position["entry_key"])
        fills = self._validated_order_fills(position["entry_key"])
        payload = row["payload"]
        quantity = sum(fill["quantity"] for fill in fills)
        if quantity != position["quantity"] or quantity != position["filled_quantity"]:
            raise ValueError("DURABLE_FILL_QUANTITY_INVALID")
        mean = sum((Fraction(fill["price"])*fill["quantity"] for fill in fills), Fraction(0))/quantity
        r = abs(mean-Fraction(position["executable_initial_stop"]))
        cash = r/Fraction(payload["price_step"])*Fraction(payload["instrument_authority"]["tick_value"])*quantity
        for key, value in (("fill_price_exact",mean),("actual_initial_r_exact",r),("actual_initial_loss_cash_exact",cash)):
            pair = position[key]
            if Fraction(int(pair["numerator"]),int(pair["denominator"])) != value:
                raise ValueError("DURABLE_FILL_PRICE_OR_RISK_INVALID")
        if (position["fill_authority"] != "FINAM_ACCOUNT_TRADE" or Fraction(position["verified_fill_entry"]) != mean
                or Fraction(position["actual_initial_r"]) != r or Fraction(position["actual_initial_loss_cash"]) != cash
                or sorted({f["account_trade_currency"] for f in fills}) != position["account_trade_currencies"]):
            raise ValueError("DURABLE_FILL_PRICE_OR_RISK_INVALID")

    def _confirm_candidate_entry(self, entry_key: str, observed_quantity: int, *,
                                 verified_fill_entry: Decimal | None, fill_authority: str | None,
                                 observed_protective_stop: Any = None) -> RuntimeAction | None:
        intent = self.store.intent(entry_key)
        if not intent or intent["payload"].get("kind") != "ENTRY":
            raise ProductionRuntimeError("ENTRY_INTENT_NOT_FOUND")
        payload = intent["payload"]
        self._validate_execution_evidence(payload)
        expected = payload["expected_position_quantity"]
        if type(observed_quantity) is not int or type(expected) is not int:
            raise ProductionRuntimeError("POSITION_AUTHORITY_SCHEMA_INVALID")
        positions = self.open_positions()
        current = positions.get(payload["instrument"])
        if observed_quantity == 0:
            if current is not None:
                self.halt("POSITION_FLAT_WHILE_ENTRY_UNRESOLVED")
            return None
        if observed_quantity*expected <= 0 or abs(observed_quantity) > abs(expected):
            raise ProductionRuntimeError("POSITION_AUTHORITY_UNEXPECTED_QUANTITY")
        if intent["status"] in {"CANCELLED","REJECTED","CLOSED"}:
            raise ProductionRuntimeError("TERMINAL_ENTRY_INTENT_HAS_BROKER_POSITION")
        if current is None and intent["status"] == "RECONCILED":
            raise ProductionRuntimeError("ENTRY_RECONCILED_POSITION_MISSING_REQUIRES_REVIEW")
        if verified_fill_entry is not None and fill_authority != "OFFLINE_SYNTHETIC_VERIFIED":
            raise ProductionRuntimeError("ACTUAL_FILL_AUTHORITY_UNVERIFIED")
        if current is None:
            current = dict(payload)
            current.pop("kind", None)
            current.update(entry_key=entry_key, planned_quantity=payload["quantity"], quantity=abs(observed_quantity),
                           entry=payload["reference_entry"], initial_stop=payload["executable_initial_stop"],
                           current_stop=payload["executable_initial_stop"], favorable_extreme=payload["reference_entry"],
                           protective_stop_state="PENDING", protective_stop_revision=0, protective_covered_quantity=0,
                           trail1=_trail_to_dict(Trail1State(payload["direction"],Decimal(payload["reference_entry"]),Decimal(payload["executable_initial_stop"]))),
                           filled_quantity=0, actual_initial_r=None)
            watermark = self.store.get(f"last_managed_h1:{payload['instrument']}")
            if watermark and watermark > payload["signal_timestamp"]:
                raise ProductionRuntimeError("ENTRY_SIGNAL_WATERMARK_MISMATCH")
            self.store.put(f"last_managed_h1:{payload['instrument']}",payload["signal_timestamp"])
        elif current["trade_id"] != payload["trade_id"]:
            raise ProductionRuntimeError("ENTRY_POSITION_ALREADY_EXISTS")
        elif current["quantity"] != abs(observed_quantity):
            if self.store.get(f"entry_growth_hold:{entry_key}") is not None:
                self.halt("POSITION_GROWTH_REQUIRES_OPERATOR_RECOVERY")
                return None
            if abs(observed_quantity) < current["quantity"]:
                self.halt("POSITION_CHANGED_WHILE_ENTRY_UNRESOLVED")
                self.store.put(f"entry_growth_hold:{entry_key}", {
                    "observed_quantity": abs(observed_quantity), "prior_quantity": current["quantity"],
                    "reason": "POSITION_DECREASED_OR_REVERSED",
                })
                return None
            if current["protective_stop_state"] == "ACTIVE":
                # An ACTIVE local flag or an SLTP ACK is not proof that FINAM
                # protects newly filled contracts. Require the *same* broker
                # stop ID, exact persisted intent, and fresh active 100% order
                # in the current account/orders observation before growth.
                from .broker import compact_client_order_id
                from .account_cleanliness import ACTIVE_ORDER_STATUSES
                from .production_broker_state import BrokerOrderView, active_sltp_for_trade
                broker_id = current.get("protective_stop_broker_order_id")
                related = [
                    row for row in self.store.all_intents()
                    if row["payload"].get("kind") in {"PROTECTIVE_STOP_INSTALL", "PROTECTIVE_STOP_REPLACE"}
                    and row["payload"].get("trade_id") == current["trade_id"]
                    and row.get("broker_order_id") == broker_id
                    and row["status"] == "RECONCILED"
                ]
                matched = False
                if (type(current.get("protective_covered_quantity")) is int
                        and current["protective_covered_quantity"] == current["quantity"]
                        and current.get("protective_stop_state") == "ACTIVE"
                        and isinstance(broker_id, str) and broker_id and len(related) == 1
                        and isinstance(observed_protective_stop, BrokerOrderView)):
                    stop = observed_protective_stop
                    row = related[0]
                    try:
                        expected_price = Decimal(str(current["current_stop"]))
                        observed_price = Decimal(stop.request["sl_price"]["value"])
                        matched = (
                            stop.order_id == broker_id and stop.active
                            and stop.status in ACTIVE_ORDER_STATUSES
                            and stop.kind == "SLTP"
                            and stop.request.get("symbol") == stop.symbol
                            and stop.request.get("side") == stop.side
                            and stop.request.get("client_order_id") == stop.client_order_id
                            and stop.request.get("comment") == stop.comment
                            and stop.symbol == payload["finam_symbol"]
                            and stop.side == ("SIDE_SELL" if payload["direction"] == "LONG" else "SIDE_BUY")
                            and stop.comment == row["idempotency_key"]
                            and stop.client_order_id == compact_client_order_id(row["idempotency_key"])
                            and observed_price == expected_price
                            and observed_price == Decimal(str(current["protective_stop_price"]))
                            and active_sltp_for_trade(
                                [stop], trade_id=current["trade_id"],
                                symbol=payload["finam_symbol"],
                            ) == [stop]
                        )
                    except (KeyError, TypeError, ValueError, ArithmeticError, RuntimeError):
                        matched = False
                if not matched:
                    self.halt("POSITION_GROWTH_ACTIVE_STOP_NOT_REVERIFIED")
                    self.store.put(f"entry_growth_hold:{entry_key}", {
                        "observed_quantity": abs(observed_quantity), "prior_quantity": current["quantity"],
                        "reason": "ACTIVE_PERCENT_STOP_BROKER_PROOF_MISSING",
                    })
                    return None
                current["protective_covered_quantity"] = abs(observed_quantity)
                self.store.put(f"entry_growth_stop_observed:{entry_key}", {
                    "from_quantity": current["quantity"], "to_quantity": abs(observed_quantity),
                    "broker_stop_id": broker_id, "client_order_id": stop.client_order_id,
                    "stop_price": str(expected_price), "quantity_measure": "SLTP_QTY_MEASURE_PERCENT",
                    "quantity_percent": "100", "evidence": "CURRENT_ACCOUNT_ORDERS_SNAPSHOT",
                    "real_finam_dynamic_coverage_proven": False,
                })
            current["quantity"] = abs(observed_quantity)
            current.update(entry=current["reference_entry"], verified_fill_entry=None,fill_authority="MISSING",
                           actual_initial_r=None, actual_initial_loss_cash=None)
            for field in ("fill_price_exact","actual_initial_r_exact","actual_initial_loss_cash_exact"):
                current.pop(field,None)
        if verified_fill_entry is not None:
            price = decimal_price(verified_fill_entry)
            stop = Decimal(payload["executable_initial_stop"])
            if (price <= stop if payload["direction"] == "LONG" else price >= stop):
                raise ProductionRuntimeError("FILL_BEYOND_INITIAL_STOP_REQUIRES_REVIEW")
            if current["verified_fill_entry"] not in (None,str(price)):
                raise ProductionRuntimeError("FILL_AUTHORITY_CHANGED_REQUIRES_REVIEW")
            r = abs(price-stop)
            current.update(entry=str(price),verified_fill_entry=str(price),fill_authority=fill_authority,
                           favorable_extreme=str(price),actual_initial_r=str(r),
                           actual_initial_loss_cash=str(r/Decimal(payload["price_step"])*Decimal(payload["instrument_authority"]["tick_value"])*current["quantity"]),
                           trail1=_trail_to_dict(Trail1State(payload["direction"],price,stop)))
        positions[payload["instrument"]] = current
        self._save_positions(positions)
        # Quantity alone proves exposure. It never proves entry price/completion.
        if verified_fill_entry is not None and abs(observed_quantity) == abs(expected):
            self.store.transition_intent(entry_key,"RECONCILED",intent["broker_order_id"])
        elif intent["status"] != "RECONCILED":
            self.store.transition_intent(entry_key,"PARTIAL_FILL" if abs(observed_quantity)<abs(expected) else "FILL",intent["broker_order_id"])
        stop_key = f"stage8.12:{payload['trade_id']}:stop:0000"
        stop_intent = self.store.intent(stop_key)
        if current["protective_stop_state"] == "PENDING_REPLACE" and intent["status"] == "RECONCILED":
            return None
        if current["protective_stop_state"] == "ACTIVE":
            if current["protective_covered_quantity"] != current["quantity"]:
                self.halt("PROTECTIVE_COVERAGE_UNVERIFIED")
            return None
        if current["protective_stop_state"] != "PENDING":
            raise ProductionRuntimeError("PROTECTIVE_STOP_STATE_MISMATCH")
        if stop_intent is not None:
            if stop_intent["payload"].get("kind") != "PROTECTIVE_STOP_INSTALL":
                raise ProductionRuntimeError("PROTECTIVE_STOP_STATE_MISMATCH")
            return self._protective_stop_action_from_payload(stop_intent["payload"])
        action = self._action("PROTECTIVE_STOP_INSTALL",stop_key,payload["instrument"],payload["finam_symbol"],
                              payload["direction"],abs(observed_quantity),payload["trade_id"],payload["signal_id"],
                              Decimal(payload["reference_entry"]),Decimal(payload["executable_initial_stop"]),observed_quantity)
        self.store.persist_intent(stop_key,action.payload() | self._stop_evidence(current))
        return action

    def _stop_evidence(self, position: dict) -> dict:
        return {k: position[k] for k in (
            "specification_fingerprint", "instrument_authority", "raw_initial_stop", "raw_initial_r",
            "reference_entry", "verified_fill_entry", "fill_authority", "executable_initial_stop",
            "executable_initial_r", "last_processed_h1", "sizing", "risk_cash",
            "reference_initial_loss_cash", "margin_reservation")} | ({"planned_quantity": position.get("planned_quantity", position["quantity"])} if self.execution_revision else {})


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
        if self.execution_revision:
            submission = self.store.get(f"protective_submission:{stop_key}")
            covered = abs(submission["position_quantity"]) if submission else payload["quantity"]
            current["protective_covered_quantity"] = covered
            if covered != current["quantity"]:
                self.halt("PROTECTIVE_COVERAGE_UNVERIFIED")
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
            Decimal(str(current.get("reference_entry", current["entry"]))), Decimal(str(current["current_stop"])), 0,
            "POSITION_AUTHORITY_FLAT",
        )
        positions.pop(instrument)
        self._save_positions(positions)
        self.set_realized_equity(realized_equity_after_exit)
        return action

    @_atomic
    def manage_completed_bar(self, instrument: str, bar: CompletedBar,
                             *, observed_position_quantity: int) -> RuntimeAction | None:
        if self.execution_revision and self.store.get("execution_halt"):
            raise ProductionRuntimeError("HALTED_OPERATOR_INTERVENTION_REQUIRED")
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
                require_on_grid(outcome["fill"], value["instrument_authority"]["price_step"]) if self.execution_revision else Decimal(str(outcome["fill"])), require_on_grid(position.current_stop, value["instrument_authority"]["price_step"]) if self.execution_revision else Decimal(str(position.current_stop)), 0,
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
                Decimal(str(value.get("reference_entry", position.entry))), require_on_grid(position.current_stop, value["instrument_authority"]["price_step"]) if self.execution_revision else Decimal(str(position.current_stop)), expected,
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
