"""MOEX instrument semantics for future execution-aware code.

Legacy runners may retain their historical execution assumptions.  New and
explicitly revised execution code must use ``tick_size`` and data/indicator
code must use ``price_precision`` (exposed as ``price_step``) explicitly.
"""

from dataclasses import dataclass
from types import MappingProxyType


@dataclass(frozen=True, slots=True)
class InstrumentSpec:
    """Unambiguous exchange, source-data, and strategy price units."""

    symbol: str
    exchange_name: str
    tick_size: float
    lot_size: int
    price_precision: float
    round_level_step: float
    tick_value_rub: float = 1.0
    currency: str = "RUB"

    @property
    def price_step(self) -> float:
        """Strategy/source price step used by the frozen lab execution model."""
        return self.price_precision


_SPECS = {
    "USDRUBF": InstrumentSpec("USDRUBF", "MOEX", 0.01, 1000, 0.001, 0.10),
    "CNYRUBF": InstrumentSpec("CNYRUBF", "MOEX", 0.01, 1000, 0.001, 0.05),
    "EURRUBF": InstrumentSpec("EURRUBF", "MOEX", 0.01, 1000, 0.001, 0.10),
    "HKDRUBF": InstrumentSpec("HKDRUBF", "MOEX", 0.01, 1000, 0.001, 0.10),
    "GOLD": InstrumentSpec("GOLD", "MOEX", 0.1, 1, 0.1, 10.0),
    "BR": InstrumentSpec("BR", "MOEX", 0.01, 10, 0.01, 1.0),
    "MIX": InstrumentSpec("MIX", "MOEX", 25.0, 1, 25.0, 1000.0),
    "NG": InstrumentSpec("NG", "MOEX", 0.01, 100, 0.01, 1.0),
}
INSTRUMENT_SPECS = MappingProxyType(_SPECS)
ALIASES = MappingProxyType({"Si": "USDRUBF", "USDRUBF": "USDRUBF",
                            "CNY": "CNYRUBF", "CNYRUBF": "CNYRUBF",
                            "EUR": "EURRUBF", "EURRUBF": "EURRUBF",
                            "HKD": "HKDRUBF", "HKDRUBF": "HKDRUBF",
                            "GD": "GOLD", "GOLD": "GOLD", "BR": "BR",
                            "MIX": "MIX", "NG": "NG"})


def get_instrument_spec(symbol: str) -> InstrumentSpec:
    """Return the canonical specification, accepting frozen runner aliases."""
    try:
        return INSTRUMENT_SPECS[ALIASES[symbol]]
    except KeyError as exc:
        raise KeyError(f"unsupported instrument: {symbol!r}") from exc
