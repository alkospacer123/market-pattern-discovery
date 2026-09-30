"""Frozen FULL/R15 sizing using authenticated contract economics only."""
from dataclasses import dataclass
from decimal import Decimal, ROUND_FLOOR

@dataclass(frozen=True)
class ContractEconomics:
    price_step: Decimal; tick_value: Decimal; quantity_granularity: int; valid: bool
@dataclass(frozen=True)
class SizeResult:
    risk_cash: Decimal; stop_ticks: Decimal; loss_per_contract: Decimal; quantity: int
def size_position(realized_equity:Decimal,entry:Decimal,stop:Decimal,contract:ContractEconomics)->SizeResult:
    if not contract.valid: raise ValueError("CONTRACT_INVALID")
    if min(realized_equity,contract.price_step,contract.tick_value)>0 and entry>0 and stop>0: pass
    else: raise ValueError("SIZING_INPUT_INVALID")
    distance=abs(entry-stop); ticks=distance/contract.price_step
    if ticks != ticks.to_integral_value(): raise ValueError("STOP_NOT_ON_TICK_GRID")
    loss=ticks*contract.tick_value
    if loss<=0 or contract.quantity_granularity<=0: raise ValueError("LOSS_OR_GRANULARITY_INVALID")
    risk=realized_equity*Decimal("0.015")
    lots=(risk/loss/contract.quantity_granularity).to_integral_value(rounding=ROUND_FLOOR)
    qty=int(lots)*contract.quantity_granularity
    if qty<=0: raise ValueError("QUANTITY_ZERO")
    return SizeResult(risk,ticks,loss,qty)
