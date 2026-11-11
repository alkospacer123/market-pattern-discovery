"""N4 intracycle R15/GO reservation; H1 MarginBatchBudget pattern, M15 only.

Pure offline capacity tracking. Inputs MUST be read from separately authenticated
M15 broker account/symbol authority. Does not authorize a trade or mutate state.
Never subtract existing margin twice: incoming FINAM available_cash is already
net capacity, and only NEW reservations in this cycle are subtracted.
"""
from __future__ import annotations

from decimal import Decimal

from .grid_risk import ContractAuthority, SizedOrder, size_r15
from .spec import INSTRUMENTS, MAX_NOMINAL_INITIAL_RISK


class M15BatchRiskError(RuntimeError):
    pass


class M15BatchRiskBudget:
    """A single broker-snapshot's shared margin and aggregate initial risk."""

    def __init__(
        self, *, realized_equity: Decimal, available_margin_cash: Decimal,
        committed_initial_risk: Decimal = Decimal("0"),
        occupied_instruments: tuple[str, ...] = (),
    ):
        for value in (realized_equity, available_margin_cash, committed_initial_risk):
            if not isinstance(value, Decimal) or not value.is_finite():
                raise M15BatchRiskError("M15_BATCH_FINANCIAL_INVALID")
        if realized_equity <= 0 or available_margin_cash < 0 or committed_initial_risk < 0:
            raise M15BatchRiskError("M15_BATCH_FINANCIAL_INVALID")
        if any(symbol not in INSTRUMENTS for symbol in occupied_instruments):
            raise M15BatchRiskError("M15_BATCH_UNKNOWN_INSTRUMENT")
        if len(set(occupied_instruments)) != len(occupied_instruments):
            raise M15BatchRiskError("M15_BATCH_DUPLICATE_OCCUPIED_INSTRUMENT")
        self.realized_equity = realized_equity
        self.remaining_margin_cash = available_margin_cash
        self.committed_initial_risk = committed_initial_risk
        self.occupied_instruments = set(occupied_instruments)

    def size_and_reserve(
        self, *, instrument: str, direction: str, entry: Decimal,
        stop: Decimal, contract: ContractAuthority,
    ) -> SizedOrder:
        if instrument not in INSTRUMENTS:
            raise M15BatchRiskError("M15_BATCH_UNKNOWN_INSTRUMENT")
        if instrument in self.occupied_instruments:
            raise M15BatchRiskError("M15_BATCH_INSTRUMENT_OCCUPIED")
        result = size_r15(
            realized_equity=self.realized_equity,
            entry=entry, stop=stop, contract=contract, direction=direction,
            available_margin_cash=self.remaining_margin_cash,
            already_committed_initial_risk=self.committed_initial_risk,
        )
        if result.final_quantity == 0:
            return result
        margin = (
            contract.long_initial_margin if direction == "LONG"
            else contract.short_initial_margin
        ) * result.final_quantity
        next_margin = self.remaining_margin_cash - margin
        next_risk = self.committed_initial_risk + result.initial_nominal_risk
        if (next_margin < 0 or next_risk >
                self.realized_equity * MAX_NOMINAL_INITIAL_RISK):
            raise M15BatchRiskError("M15_BATCH_OVERALLOCATION")
        self.remaining_margin_cash = next_margin
        self.committed_initial_risk = next_risk
        self.occupied_instruments.add(instrument)
        return result

    @property
    def execution_authorized(self) -> bool:
        return False
