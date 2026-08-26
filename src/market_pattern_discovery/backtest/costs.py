from dataclasses import dataclass
from math import isfinite

@dataclass(frozen=True)
class CostModel:
    """Required future evaluation costs, expressed in price units per trade."""
    transaction_cost: float
    slippage: float
    def __post_init__(self) -> None:
        if not isfinite(self.transaction_cost) or not isfinite(self.slippage):
            raise ValueError("transaction costs and slippage must be finite")
        if self.transaction_cost < 0 or self.slippage < 0:
            raise ValueError("transaction costs and slippage cannot be negative")
