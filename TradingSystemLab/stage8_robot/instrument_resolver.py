"""Direct perpetual-future model and cross-source binding validation."""
from __future__ import annotations
from dataclasses import dataclass
from decimal import Decimal
import csv
from pathlib import Path
from typing import Any

PERPETUAL_FUTURE = "PERPETUAL_FUTURE"
OPERATOR_ACTION_ONLY = "OPERATOR_ACTION_ONLY"
AUTHENTICATED = "AUTHENTICATED_DEMO_TRADABLE"

@dataclass(frozen=True)
class Instrument:
    research_symbol: str
    finam_symbol: str | None
    moex_short_code: str
    mic: str
    security_id: str | None
    instrument_type: str
    perpetual: bool
    automatic_prolongation: bool
    price_step: Decimal
    tick_value: Decimal
    contract_size: Decimal
    quantity_granularity: Decimal
    currency: str
    trading_status: str
    trading_schedule: dict[str, Any] | None
    quarterly_exercise: str = OPERATOR_ACTION_ONLY
    expiry: None = None
    binding_status: str = "BLOCKED_UNAUTHENTICATED"

    def __post_init__(self) -> None:
        if self.instrument_type != PERPETUAL_FUTURE or not self.perpetual or self.expiry is not None:
            raise ValueError("PRODUCTION_INSTRUMENT_MUST_BE_NONEXPIRING_PERPETUAL")

class ContractResolver:
    """Resolve N4 directly; never maps a perpetual to an expiring contract."""
    def __init__(self, instruments: list[Instrument]): self.instruments = instruments
    def resolve(self, symbol: str, on_date=None) -> Instrument:
        found = [x for x in self.instruments if x.research_symbol == symbol and x.binding_status == AUTHENTICATED]
        if len(found) != 1: raise RuntimeError(f"PERPETUAL_BINDING_UNAVAILABLE:{symbol}")
        return found[0]
    @staticmethod
    def open_position_roll(*_): raise RuntimeError("OPERATOR_ACTION_ONLY_NO_AUTOMATIC_ROLL")

MOEX_REFERENCE = {
    "USDRUBF": (Decimal("0.01"), Decimal("10"), Decimal("1000")),
    "CNYRUBF": (Decimal("0.001"), Decimal("1"), Decimal("1000")),
    "GLDRUBF": (Decimal("0.1"), Decimal("0.1"), Decimal("1")),
    "IMOEXF": (Decimal("0.5"), Decimal("5"), Decimal("10")),
}

def validate_finam_binding(symbol: str, asset: dict, params: dict, schedule: dict | None) -> str:
    """Require authenticated FINAM economics to agree with recorded MOEX evidence."""
    if not asset: return "BLOCKED_NOT_FOUND"
    def value(*names):
        for source in (params, asset):
            for name in names:
                if source.get(name) is not None: return Decimal(str(source[name]))
        return None
    step, _tick, size = MOEX_REFERENCE[symbol]
    if value("priceIncrement", "price_step", "minPriceStep") != step or value("lotSize", "contractSize", "contract_size") != size:
        return "BLOCKED_PARAM_MISMATCH"
    granularity = value("quantityStep", "quantity_granularity", "lotStep")
    if granularity is None or granularity <= 0: return "BLOCKED_PARAM_MISMATCH"
    tradable = asset.get("tradable", asset.get("tradingAvailable", asset.get("trading_status") == "ACTIVE"))
    return AUTHENTICATED if tradable is True else "BLOCKED_NOT_TRADABLE"

def load_registry(path: Path) -> list[Instrument]:
    rows=[]
    with path.open(newline="",encoding="utf-8") as f:
        for r in csv.DictReader(f):
            rows.append(Instrument(r["research_symbol"],r["finam_symbol"] or None,r["moex_short_code"],r["mic"],r["security_id"] or None,
                r["instrument_type"],r["perpetual"].lower()=="true",r["automatic_prolongation"].lower()=="true",Decimal(r["price_step"]),
                Decimal(r["tick_value"]),Decimal(r["contract_size"]),Decimal(r["quantity_granularity"]),r["currency"],r["trading_status"],None,
                r["quarterly_exercise"],None,r["binding_status"]))
    return rows
