"""Immutable display contracts, schema v1. None means UNKNOWN, never zero."""
from dataclasses import dataclass, fields
from datetime import datetime
from enum import StrEnum
from math import isfinite
from types import UnionType
from typing import get_args, get_origin, get_type_hints


class RobotId(StrEnum):
    H1 = "H1"
    M15 = "M15"


class State(StrEnum):
    HALTED = "HALTED"
    NOT_DEPLOYED = "NOT_DEPLOYED"
    HEALTHY = "HEALTHY"
    STALE = "STALE"
    UNKNOWN = "UNKNOWN"
    DATA_GAP = "DATA_GAP"
    API_ERROR = "API_ERROR"
    UNRESOLVED = "UNRESOLVED"
    UNHEALTHY = "UNHEALTHY"


class SourceKind(StrEnum):
    SYNTHETIC = "SYNTHETIC"
    OFFLINE_FIXTURE = "OFFLINE_FIXTURE"
    READONLY_EXPORT = "READONLY_EXPORT"
    VERIFIED_LIVE_READONLY = "VERIFIED_LIVE_READONLY"  # reserved; CC-03 required


class ExecutionState(StrEnum):
    INTENT = "INTENT"
    REQUESTED = "REQUESTED"
    ACK = "ACK"
    POSITION_OBSERVED = "POSITION_OBSERVED"
    FILL_CONFIRMED = "FILL_CONFIRMED"
    UNRESOLVED = "UNRESOLVED"


def aware(value: datetime | None) -> None:
    if value is not None and (not isinstance(value, datetime) or value.tzinfo is None
                              or value.utcoffset() is None):
        raise ValueError("TIMEZONE_REQUIRED")


def number(value: float | int | None, *, positive: bool = False) -> None:
    if value is not None and (type(value) not in (float, int) or not isfinite(value)
                              or (positive and value <= 0)):
        raise ValueError("INVALID_NUMBER")


def typed(value, annotation) -> bool:
    if get_origin(annotation) is UnionType:
        return any(typed(value, option) for option in get_args(annotation))
    if get_origin(annotation) is tuple:
        return isinstance(value, tuple) and all(typed(item, get_args(annotation)[0]) for item in value)
    if annotation is float:
        return type(value) in (float, int) and isfinite(value)
    if annotation in (int, bool, str):
        return type(value) is annotation
    return isinstance(value, annotation)


def validate_types(record):
    for name, annotation in get_type_hints(type(record)).items():
        if not typed(getattr(record, name), annotation):
            raise ValueError(f"INVALID_FIELD_TYPE:{name}")


@dataclass(frozen=True)
class DataProvenance:
    robot_id: RobotId
    account_scope: str
    source: str
    observed_at: datetime | None
    received_at: datetime
    synthetic: bool = True
    schema_version: int = 1
    source_kind: SourceKind = SourceKind.SYNTHETIC
    snapshot_ttl_seconds: int | None = None
    heartbeat_ttl_seconds: int | None = None

    def __post_init__(self):
        validate_types(self)
        if self.source_kind == SourceKind.SYNTHETIC:
            if self.account_scope != f"DEMO-{self.robot_id}":
                raise ValueError("ACCOUNT_SCOPE_MISMATCH")
            if not self.source.startswith("SYNTHETIC/") or self.synthetic is not True:
                raise ValueError("CC01_SYNTHETIC_ONLY")
            if self.snapshot_ttl_seconds is not None or self.heartbeat_ttl_seconds is not None:
                raise ValueError("SYNTHETIC_TTL_FIXED")
        elif self.source_kind == SourceKind.OFFLINE_FIXTURE:
            if (self.robot_id != RobotId.H1 or self.account_scope != "FIXTURE-H1"
                    or self.source != "OFFLINE_FIXTURE/H1" or self.synthetic is not True
                    or self.snapshot_ttl_seconds != 180 or self.heartbeat_ttl_seconds != 90):
                raise ValueError("OFFLINE_BINDING_REQUIRED")
        elif self.source_kind == SourceKind.READONLY_EXPORT:
            if (self.robot_id != RobotId.H1 or self.source != "READONLY_EXPORT/H1"
                    or self.synthetic is not False or self.account_scope in ("FIXTURE-H1", "DEMO-H1")
                    or not self.account_scope.startswith(("H1-", "UNBOUND-H1"))):
                raise ValueError("EXPORT_BINDING_REQUIRED")
        else:
            raise ValueError("CC03_PHYSICAL_ACCEPTANCE_REQUIRED")
        if self.schema_version != 1:
            raise ValueError("SCHEMA_VERSION_UNSUPPORTED")
        aware(self.observed_at)
        aware(self.received_at)
        if self.received_at is None:
            raise ValueError("RECEIVED_AT_REQUIRED")


class Record:
    """Runtime checks shared by immutable typed records."""
    def __post_init__(self):
        validate_types(self)
        if not isinstance(self.provenance, DataProvenance):
            raise ValueError("PROVENANCE_REQUIRED")
        for field in fields(self):
            value = getattr(self, field.name)
            if field.name.endswith('_at'):
                aware(value)
            if type(value) in (float, int):
                number(value)
        for name in ("quantity", "filled_quantity", "open_positions", "error_count"):
            value = getattr(self, name, None)
            if value is not None and (type(value) is not int or value < 0):
                raise ValueError("INVALID_QUANTITY")


@dataclass(frozen=True)
class RobotStatus(Record):
    provenance: DataProvenance
    state: State
    project: str
    strategy: str
    production_identity: str | None
    heartbeat_at: datetime | None
    last_bar_at: datetime | None
    open_positions: int | None
    trading_allowed: bool | None
    error_count: int | None
    task_state: str | None
    session: str | None

    def __post_init__(self):
        super().__post_init__()
        if not isinstance(self.state, State) or self.trading_allowed not in (False, None):
            raise ValueError("MVP_TRADING_FORBIDDEN")
        if self.provenance.robot_id == RobotId.M15 and (
            self.state != State.NOT_DEPLOYED or self.production_identity is not None
            or self.heartbeat_at is not None or self.open_positions is not None
        ):
            raise ValueError("NO_RUNTIME_AUTHORITY")


@dataclass(frozen=True)
class Candle(Record):
    provenance: DataProvenance
    instrument: str
    close_at: datetime
    open: float
    high: float
    low: float
    close: float
    demo_indicator: float | None = None

    def __post_init__(self):
        super().__post_init__()
        for value in (self.open, self.high, self.low, self.close):
            number(value, positive=True)
        if self.close_at is None or not self.low <= min(self.open, self.close) <= max(self.open, self.close) <= self.high:
            raise ValueError("INVALID_CANDLE")


@dataclass(frozen=True)
class InstrumentStatus(Record):
    provenance: DataProvenance
    instrument: str
    state: State
    last_bar_at: datetime | None
    condition: str | None
    stop_price: float | None
    stop_evidence: str | None

    def __post_init__(self):
        super().__post_init__()
        if self.stop_price is not None:
            number(self.stop_price, positive=True)
            if not self.stop_evidence:
                raise ValueError("STOP_EVIDENCE_REQUIRED")


@dataclass(frozen=True)
class SignalEvent(Record):
    provenance: DataProvenance
    instrument: str
    occurred_at: datetime
    direction: str
    reason: str | None
    price: float | None


@dataclass(frozen=True)
class OrderEvent(Record):
    provenance: DataProvenance
    instrument: str
    occurred_at: datetime
    order_id: str
    state: ExecutionState
    quantity: int | None
    filled_quantity: int | None = None
    fill_price: float | None = None
    fill_evidence: str | None = None

    def __post_init__(self):
        super().__post_init__()
        if not isinstance(self.state, ExecutionState):
            raise ValueError("INVALID_EXECUTION_STATE")
        if self.state == ExecutionState.FILL_CONFIRMED:
            if not self.fill_evidence or not self.filled_quantity or self.fill_price is None:
                raise ValueError("FILL_EVIDENCE_REQUIRED")
            number(self.fill_price, positive=True)
            if self.quantity is not None and self.filled_quantity > self.quantity:
                raise ValueError("FILL_EXCEEDS_REQUEST")
        elif any(x is not None for x in (self.filled_quantity, self.fill_price, self.fill_evidence)):
            raise ValueError("ACK_IS_NOT_FILL")


@dataclass(frozen=True)
class PositionSnapshot(Record):
    provenance: DataProvenance
    instrument: str
    quantity: int
    entry_price: float | None
    unrealized_pnl: float | None
    stop_price: float | None
    stop_evidence: str | None
    side: str | None = None

    def __post_init__(self):
        super().__post_init__()
        if self.quantity == 0:
            raise ValueError("OPEN_POSITION_REQUIRES_QUANTITY")
        if self.stop_price is not None and not self.stop_evidence:
            raise ValueError("STOP_EVIDENCE_REQUIRED")


@dataclass(frozen=True)
class RiskSnapshot(Record):
    provenance: DataProvenance
    per_position_pct: float | None
    maximum_total_pct: float | None
    used_pct: float | None
    contracts: int | None
    reason: str | None

    def __post_init__(self):
        super().__post_init__()
        for value in (self.per_position_pct, self.maximum_total_pct, self.used_pct):
            if value is not None and not 0 <= value <= 100:
                raise ValueError("INVALID_RISK_PERCENT")
        if self.contracts is not None and (type(self.contracts) is not int or self.contracts < 0):
            raise ValueError("INVALID_CONTRACTS")


@dataclass(frozen=True)
class PortfolioSnapshot(Record):
    provenance: DataProvenance
    equity: float | None
    realized_pnl: float | None
    unrealized_pnl: float | None
    commissions: float | None
    profit_factor: float | None
    maximum_drawdown_pct: float | None


@dataclass(frozen=True)
class Trade(Record):
    provenance: DataProvenance
    instrument: str
    entry_at: datetime
    exit_at: datetime
    entry_price: float
    exit_price: float
    net_pnl: float
    commission: float


@dataclass(frozen=True)
class SystemAlert(Record):
    provenance: DataProvenance
    instrument: str | None
    occurred_at: datetime
    kind: str
    severity: str
    message: str


@dataclass(frozen=True)
class FieldObservation:
    name: str
    observed_at: datetime | None
    state: State

    def __post_init__(self):
        validate_types(self)
        aware(self.observed_at)


@dataclass(frozen=True)
class BarObservation(Record):
    provenance: DataProvenance
    instrument: str
    close_at: datetime | None
    time_source: str
    gaps: bool | None
    quality: str
    freshness: State


@dataclass(frozen=True)
class StopObservation(Record):
    provenance: DataProvenance
    instrument: str
    side: str
    quantity: int
    expected_quantity: int
    observed_quantity: int | None
    broker_status: str
    checked_at: datetime | None
    evidence: str | None
    protected: bool


@dataclass(frozen=True)
class H1ReadonlyDetails(Record):
    provenance: DataProvenance
    production_specification_id: str
    accepted_code_commit: str
    account_alias: str
    generated_at: datetime
    last_successful_cycle_at: datetime | None
    reconciliation: str
    unresolved_intents: int | None
    source_status: str
    orders_complete: bool
    positions_complete: bool
    observations: tuple[FieldObservation, ...]
    bars: tuple[BarObservation, ...]
    stops: tuple[StopObservation, ...]
    deposits: float | None
    withdrawals: float | None
    available_margin: float | None


@dataclass(frozen=True)
class WindowsObservation:
    name: str
    source: str
    state: str
    observed_at: datetime
    freshness: str
    authority: str
    reason: str
    value: str | None

    def __post_init__(self):
        validate_types(self)
        aware(self.observed_at)


@dataclass(frozen=True)
class RobotSnapshot:
    status: RobotStatus
    instruments: tuple[InstrumentStatus, ...]
    candles: tuple[Candle, ...]
    signals: tuple[SignalEvent, ...]
    orders: tuple[OrderEvent, ...]
    positions: tuple[PositionSnapshot, ...] | None
    risk: RiskSnapshot
    portfolio: PortfolioSnapshot
    trades: tuple[Trade, ...] | None
    events: tuple[SystemAlert, ...]
    h1_readonly: H1ReadonlyDetails | None = None
    readonly_observations: tuple[FieldObservation, ...] = ()
    readonly_identity: str | None = None
    windows_observations: tuple[WindowsObservation, ...] = ()
    readonly_expires_at: datetime | None = None

    def __post_init__(self):
        validate_types(self)
        aware(self.readonly_expires_at)
        records = (*self.instruments, *self.candles, *self.signals, *self.orders,
                   *(self.positions or ()), self.risk, self.portfolio,
                   *(self.trades or ()), *self.events)
        expected = self.status.provenance
        if self.h1_readonly is not None:
            if expected.source_kind != SourceKind.OFFLINE_FIXTURE:
                raise ValueError("READONLY_SOURCE_REQUIRED")
            records += (self.h1_readonly, *self.h1_readonly.bars, *self.h1_readonly.stops)
        for record in records:
            if not isinstance(record, Record) or (record.provenance.robot_id, record.provenance.account_scope) != (expected.robot_id, expected.account_scope):
                raise ValueError("CROSS_ACCOUNT_CONTAMINATION")
            if record.provenance != expected:
                raise ValueError("NON_ATOMIC_PROVENANCE")
        if self.positions is not None and self.status.open_positions != len(self.positions):
            raise ValueError("POSITION_COUNT_MISMATCH")
        if expected.robot_id == RobotId.M15 and (
            self.positions is not None or self.trades is not None
            or any(getattr(self.portfolio, f.name) is not None for f in fields(self.portfolio) if f.name != 'provenance')
            or any(getattr(self.risk, name) is not None for name in ('per_position_pct', 'maximum_total_pct', 'used_pct', 'contracts'))
        ):
            raise ValueError("NO_M15_FINANCIAL_AUTHORITY")
