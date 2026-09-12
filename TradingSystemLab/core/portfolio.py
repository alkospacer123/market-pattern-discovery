"""Fixed-risk sizing without implicit leverage or rounding assumptions."""
from dataclasses import dataclass


@dataclass(frozen=True)
class FixedRiskPortfolio:
    initial_capital: float = 100_000.0
    risk_fraction: float = 0.01
    point_value: float = 1.0

    def size(self, equity: float, entry: float, stop: float) -> float:
        risk_per_unit = abs(entry - stop) * self.point_value
        if risk_per_unit <= 0:
            raise ValueError("stop must differ from entry")
        return equity * self.risk_fraction / risk_per_unit
