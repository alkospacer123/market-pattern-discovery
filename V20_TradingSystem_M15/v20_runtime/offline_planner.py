"""OFFLINE V20 reference-entry planner; never sends orders or reads credentials.

It uses the unchanged H1 stop-grid and sizing/margin functions from main.
The returned quantity is a research feasibility estimate, *not* a real-order
instruction. LIVE must recompute from the actual FINAM fill, risk and GO.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal, ROUND_FLOOR

from TradingSystemLab.stage8_robot.execution_grid import initial_projection
from TradingSystemLab.stage8_robot.risk import ContractEconomics, size_position
from TradingSystemLab.stage8_robot.margin import cap_r15_by_margin

N4 = frozenset({"USDRUBF", "CNYRUBF", "GLDRUBF", "IMOEXF"})
STRATEGIES = frozenset({"SHALLOW_PULLBACK", "OBV_PRESSURE", "INSIDE_DAY_RELEASE"})
STEP = timedelta(minutes=15)
LIVE_ENABLED = False


@dataclass(frozen=True)
class FrozenSignal:
    strategy: str
    symbol: str
    side: int
    signal_bar_open: datetime  # M15 Open label in Moscow wall time
    atr14: Decimal


@dataclass(frozen=True)
class ProposedEntry:
    strategy: str
    symbol: str
    direction: str
    entry_bar_open: datetime
    reference_entry: Decimal
    initial_stop: Decimal
    reference_stop_risk: Decimal
    quantity: int
    cash_risk_cap: Decimal
    margin_required: Decimal
    reason: str
    mode: str = "OFFLINE_REFERENCE_NOT_ORDER"


class OfflinePlanner:
    """One instance per independent robot/account. No shared trade state."""

    def __init__(self, strategy: str):
        if strategy not in STRATEGIES:
            raise ValueError("UNKNOWN_FROZEN_STRATEGY")
        self.strategy = strategy
        self.used_in_session: set[tuple[object, str]] = set()
        self.open_symbols: set[str] = set()
        self._session = None
        self._entries_today = 0

    @staticmethod
    def _session_key(at: datetime):
        if not isinstance(at, datetime) or at.tzinfo is not None:
            raise ValueError("EXPECTED_MOSCOW_NAIVE_BAR_TIME")
        if at.second or at.microsecond or at.minute % 15:
            raise ValueError("M15_GRID_INVALID")
        # Exact frozen V20 research session boundary (09:00 MSK).
        return (at - timedelta(hours=9)).date()

    def mark_flat(self, symbol: str):
        """Offline-only acknowledgement of externally verified closing."""
        self.open_symbols.discard(symbol)

    def reference_next_open(
        self, signal: FrozenSignal, *, at: datetime, entry_open,
        realized_equity, price_step, tick_value, initial_margin,
        available_cash, trade_lot_size: int, cost_buffer_per_contract
    ) -> ProposedEntry:
        if signal.strategy != self.strategy or signal.symbol not in N4:
            raise ValueError("ACCOUNT_STRATEGY_OR_SYMBOL_MISMATCH")
        if signal.side not in (-1, 1):
            raise ValueError("SIGNAL_SIDE_INVALID")
        if at != signal.signal_bar_open + STEP:
            raise ValueError("NOT_IMMEDIATE_NEXT_OPEN")
        entry_session = self._session_key(at)
        self._session_key(signal.signal_bar_open)
        if signal.symbol in self.open_symbols:
            raise ValueError("ONE_OPEN_POSITION_PER_INSTRUMENT")
        if (entry_session, signal.symbol) in self.used_in_session:
            raise ValueError("ONE_NEW_ENTRY_PER_INSTRUMENT_SESSION")
        entries_today = self._entries_today if entry_session == self._session else 0
        if entries_today >= 2:
            raise ValueError("TWO_NEW_ENTRIES_PER_SESSION")
        atr = Decimal(str(signal.atr14))
        if not atr.is_finite() or atr <= 0:
            raise ValueError("ATR_INVALID")
        fee_slip = Decimal(str(cost_buffer_per_contract))
        if not fee_slip.is_finite() or fee_slip < 0:
            raise ValueError("COST_BUFFER_INVALID")
        direction = "LONG" if signal.side == 1 else "SHORT"
        entry = Decimal(str(entry_open))
        step = Decimal(str(price_step))
        raw_stop = entry - Decimal(signal.side) * Decimal(2) * atr
        stop, distance = initial_projection(direction, entry, raw_stop, step)
        contract = ContractEconomics(step, Decimal(str(tick_value)), trade_lot_size, True)
        base = size_position(Decimal(str(realized_equity)), entry, stop, contract)
        combined = base.loss_per_contract + fee_slip
        if combined <= 0:
            raise ValueError("RISK_BUFFER_INVALID")
        max_qty_with_cost = int((base.risk_cash / combined / trade_lot_size)
                                .to_integral_value(rounding=ROUND_FLOOR)) * trade_lot_size
        risk_qty = min(base.quantity, max_qty_with_cost)
        margin = cap_r15_by_margin(
            realized_equity=Decimal(str(realized_equity)), entry=entry,
            stop=stop, price_step=step, tick_value=contract.tick_value,
            r15_quantity=risk_qty, available_cash=Decimal(str(available_cash)),
            direction=direction, initial_margin=Decimal(str(initial_margin)),
            trade_lot_size=trade_lot_size,
        )
        if margin.final_quantity <= 0:
            raise ValueError("INSUFFICIENT_RISK_OR_MARGIN_CAPACITY")
        # Frozen replay assumes immediate NEXT_OPEN fill. This models only that
        # reference event. Real entries require broker fill/reconcile and repricing.
        self._session = entry_session
        self._entries_today = entries_today + 1
        self.used_in_session.add((entry_session, signal.symbol))
        self.open_symbols.add(signal.symbol)
        return ProposedEntry(
            strategy=signal.strategy, symbol=signal.symbol, direction=direction,
            entry_bar_open=at, reference_entry=entry, initial_stop=stop,
            reference_stop_risk=distance, quantity=margin.final_quantity,
            cash_risk_cap=base.risk_cash,
            margin_required=Decimal(margin.final_quantity) * Decimal(str(initial_margin)),
            reason="OFFLINE_REFERENCE_ONLY",
        )
