"""H1-derived tick-grid and R15+margin sizing, isolated from the live H1 robot.

Port of the audited stage8_robot/execution_grid.py (conservative outward stop
projection), risk.py (1.5% of realized equity), margin.py (min(R15, margin)).
This module has no trading or broker API and cannot submit an order.
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation, ROUND_FLOOR
from fractions import Fraction

from .spec import INITIAL_STOP_ATR, MAX_NOMINAL_INITIAL_RISK, RISK_FRACTION


def decimal_price(value) -> Decimal:
    try:
        result = Decimal(str(value))
    except (InvalidOperation, ValueError):
        raise ValueError("M15_PRICE_INVALID") from None
    if not result.is_finite() or result <= 0:
        raise ValueError("M15_PRICE_INVALID")
    return result


def _tick_ratio(value, step) -> tuple[int, int]:
    price = value if isinstance(value, Fraction) else decimal_price(value)
    increment = decimal_price(step)
    pn, pd = price.as_integer_ratio()
    sn, sd = increment.as_integer_ratio()
    return pn * sd, pd * sn


def project_stop(direction: str, value, price_step) -> Decimal:
    """LONG down, SHORT up. Same outward-projection contract as H1."""
    if direction not in ("LONG", "SHORT"):
        raise ValueError("M15_DIRECTION_INVALID")
    numerator, denominator = _tick_ratio(value, price_step)
    ticks, rem = divmod(numerator, denominator)
    if direction == "SHORT" and rem:
        ticks += 1
    t = decimal_price(price_step).as_tuple()
    coefficient = int("".join(map(str, t.digits))) * ticks
    result = Decimal((0, tuple(map(int, str(coefficient))), t.exponent))
    return decimal_price(result)


def require_on_grid(price, price_step) -> Decimal:
    n, d = _tick_ratio(price, price_step)
    if n % d:
        raise ValueError("M15_ENTRY_NOT_ON_TICK_GRID")
    return decimal_price(price)


def initial_stop(direction: str, actual_entry, signal_atr, price_step) -> Decimal:
    """Compute stop from broker-observed entry, not historical signal Close."""
    entry = require_on_grid(actual_entry, price_step)
    atr = decimal_price(signal_atr)
    raw = entry - INITIAL_STOP_ATR * atr if direction == "LONG" else entry + INITIAL_STOP_ATR * atr
    if raw <= 0 or (direction == "LONG" and raw >= entry) or (direction == "SHORT" and raw <= entry):
        raise ValueError("M15_STOP_WRONG_SIDE")
    return project_stop(direction, raw, price_step)


@dataclass(frozen=True)
class ContractAuthority:
    price_step: Decimal
    tick_value: Decimal
    trade_lot_size: int
    long_initial_margin: Decimal
    short_initial_margin: Decimal

    def validate(self) -> None:
        for value in (self.price_step, self.tick_value, self.long_initial_margin, self.short_initial_margin):
            if not isinstance(value, Decimal) or not value.is_finite() or value <= 0:
                raise ValueError("M15_CONTRACT_AUTHORITY_INVALID")
        if type(self.trade_lot_size) is not int or self.trade_lot_size <= 0:
            raise ValueError("M15_LOT_INVALID")


@dataclass(frozen=True)
class SizedOrder:
    risk_budget: Decimal
    per_contract_loss: Decimal
    by_risk: int
    by_margin: int
    final_quantity: int
    initial_nominal_risk: Decimal
    reason: str


def size_r15(
    *, realized_equity: Decimal, entry: Decimal, stop: Decimal,
    contract: ContractAuthority, direction: str, available_margin_cash: Decimal,
    already_committed_initial_risk: Decimal = Decimal("0"),
) -> SizedOrder:
    """R15 with 6% aggregate nominal cap and H1-style downward lot rounding.

    Inputs must have been independently authenticated against the *M15 account*.
    Do not feed H1's account, margin or registry to this function.
    """
    contract.validate()
    if direction not in ("LONG", "SHORT"):
        raise ValueError("M15_DIRECTION_INVALID")
    for value in (realized_equity, available_margin_cash, already_committed_initial_risk):
        if not isinstance(value, Decimal) or not value.is_finite():
            raise ValueError("M15_ACCOUNT_FINANCIAL_INVALID")
    if realized_equity <= 0 or available_margin_cash < 0 or already_committed_initial_risk < 0:
        raise ValueError("M15_ACCOUNT_FINANCIAL_INVALID")
    e = require_on_grid(entry, contract.price_step)
    s = require_on_grid(stop, contract.price_step)
    if (direction == "LONG" and s >= e) or (direction == "SHORT" and s <= e):
        raise ValueError("M15_STOP_WRONG_SIDE")
    ticks = abs(e - s) / contract.price_step
    if ticks != ticks.to_integral_value():
        raise ValueError("M15_STOP_DISTANCE_OFF_GRID")
    per_contract_loss = ticks * contract.tick_value
    if per_contract_loss <= 0:
        raise ValueError("M15_LOSS_PER_CONTRACT_INVALID")
    risk_cap = max(Decimal("0"), realized_equity * MAX_NOMINAL_INITIAL_RISK - already_committed_initial_risk)
    risk_budget = min(realized_equity * RISK_FRACTION, risk_cap)
    margin_per_contract = (
        contract.long_initial_margin if direction == "LONG" else contract.short_initial_margin
    )
    granularity = contract.trade_lot_size
    lots_risk = int((risk_budget / (per_contract_loss * granularity)).to_integral_value(rounding=ROUND_FLOOR))
    lots_margin = int((available_margin_cash / (margin_per_contract * granularity)).to_integral_value(rounding=ROUND_FLOOR))
    by_risk = lots_risk * granularity
    by_margin = lots_margin * granularity
    quantity = min(by_risk, by_margin)
    nominal = quantity * per_contract_loss
    if nominal > risk_budget or quantity * margin_per_contract > available_margin_cash:
        raise AssertionError("M15_CAPACITY_OVERALLOCATION")
    return SizedOrder(risk_budget, per_contract_loss, by_risk, by_margin, quantity, nominal,
                      "OK" if quantity else "ZERO_RISK_OR_MARGIN_CAPACITY")


@dataclass(frozen=True)
class TrailingState:
    """Position state should originate from a reconciled broker fill."""
    instrument: str
    direction: str
    entry: Decimal
    active_stop: Decimal
    extreme: Decimal
    last_survived_m15_close: str | None = None


def ratchet_after_survived_completed_bar(
    state: TrailingState, *, completed_at, high, low, atr, price_step
) -> TrailingState:
    """Project tighter stop after survived bar; broker owns the actual stop fill.

    The caller MUST first reconcile broker position/protection and MUST NOT
    infer a FINAM fill from intrabar OHLC touch. New stop applies only after
    the survived-bar event and an acknowledged broker protection update.
    """
    if state.direction not in ("LONG", "SHORT"):
        raise ValueError("M15_DIRECTION_INVALID")
    import dataclasses
    newtime = completed_at.isoformat()
    if state.last_survived_m15_close is not None and newtime <= state.last_survived_m15_close:
        raise ValueError("M15_TRAIL_BAR_REPLAY_OR_OUT_OF_ORDER")
    h, l, a = decimal_price(high), decimal_price(low), decimal_price(atr)
    if h < l:
        raise ValueError("M15_BAR_RANGE_INVALID")
    previous = require_on_grid(state.active_stop, price_step)
    if state.direction == "LONG":
        extreme = max(state.extreme, h)
        candidate = project_stop("LONG", extreme - Decimal("3.5") * a, price_step) if extreme > Decimal("3.5") * a else previous
        tightened = max(previous, candidate)
    else:
        extreme = min(state.extreme, l)
        candidate = project_stop("SHORT", extreme + Decimal("3.5") * a, price_step)
        tightened = min(previous, candidate)
    return dataclasses.replace(state, active_stop=tightened, extreme=extreme, last_survived_m15_close=newtime)
