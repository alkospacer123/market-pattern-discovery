"""Pure Stage 8.12 N4 simultaneous positive-capacity calculator.

The calculator does not read FINAM or authorize trading.  Real Stage 8.12.3
evidence must supply current directional initial margins and strategy-consistent
loss-per-contract values.  Reserve is an explicit scenario input, not part of
the frozen R15 risk model.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from decimal import Decimal
from typing import Mapping

from .specification import INSTRUMENTS

RISK_FRACTION = Decimal("0.015")


@dataclass(frozen=True)
class N4CapacityInput:
    loss_per_contract: Decimal
    trade_lot_size: int
    long_initial_margin: Decimal
    short_initial_margin: Decimal


@dataclass(frozen=True)
class N4CapacityPlan:
    r15_equity_floor: Decimal
    long_margin_floor: Decimal
    short_margin_floor: Decimal
    worst_direction_margin_floor: Decimal
    base_required_capital: Decimal
    reserve_fraction: Decimal
    reserve_cash: Decimal
    required_capital_with_reserve: Decimal

    def evidence(self) -> dict:
        return {
            key: str(value) if isinstance(value, Decimal) else value
            for key, value in asdict(self).items()
        }


def simultaneous_positive_capacity(
    inputs: Mapping[str, N4CapacityInput], *, reserve_fraction: Decimal
) -> N4CapacityPlan:
    if set(inputs) != set(INSTRUMENTS):
        raise ValueError("N4_CAPACITY_INPUTS_MUST_MATCH_FROZEN_BASKET")
    if reserve_fraction < 0:
        raise ValueError("CAPITAL_RESERVE_FRACTION_INVALID")

    risk_floors = []
    long_margin = Decimal("0")
    short_margin = Decimal("0")
    worst_margin = Decimal("0")
    for instrument in INSTRUMENTS:
        item = inputs[instrument]
        if (
            item.loss_per_contract <= 0
            or type(item.trade_lot_size) is not int
            or item.trade_lot_size <= 0
            or item.long_initial_margin <= 0
            or item.short_initial_margin <= 0
        ):
            raise ValueError("N4_CAPACITY_INPUT_INVALID")
        one_trade_lot_loss = item.loss_per_contract * item.trade_lot_size
        risk_floors.append(one_trade_lot_loss / RISK_FRACTION)
        long_margin += item.long_initial_margin * item.trade_lot_size
        short_margin += item.short_initial_margin * item.trade_lot_size
        worst_margin += max(item.long_initial_margin, item.short_initial_margin) * item.trade_lot_size

    r15_floor = max(risk_floors)
    base = max(r15_floor, worst_margin)
    reserve_cash = base * reserve_fraction
    return N4CapacityPlan(
        r15_equity_floor=r15_floor,
        long_margin_floor=long_margin,
        short_margin_floor=short_margin,
        worst_direction_margin_floor=worst_margin,
        base_required_capital=base,
        reserve_fraction=reserve_fraction,
        reserve_cash=reserve_cash,
        required_capital_with_reserve=base + reserve_cash,
    )
