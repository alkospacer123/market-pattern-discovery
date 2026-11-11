"""N4 tick monetary authority: pinned MOEX perpetual-futures specifications.

Reference date 2026-10-18; prices in RUB per ONE MINIMUM PRICE STEP per
contract, NOT the exchange underlying lot_size (1000 USD/CNY, 1 g, 10 index).
Each step must exactly match fresh FINAM account-bound GET metadata.
No estimated tick value from margin, quote levels, position size or price.
No network, token, SQLite, LIVE authorization, order submission, or H1 access.

Exchange reference pages (checked on 2026-10-18):
https://www.moex.com/ru/derivatives/perpetual-futures/USDRUBF
https://www.moex.com/ru/derivatives/perpetual-futures/CNYRUBF
https://www.moex.com/ru/derivatives/perpetual-futures/GLDRUBF
https://www.moex.com/ru/derivatives/perpetual-futures/IMOEXF
A changed exchange specification requires review, not a silent fallback.
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from types import MappingProxyType

from .broker_risk_readonly import M15InstrumentParams, M15RiskAuthorityError
from .grid_risk import ContractAuthority


@dataclass(frozen=True)
class MoexTickSpec:
    price_step: Decimal
    tick_rub: Decimal
    reference_url: str


PREFIX = "https://www.moex.com/ru/derivatives/perpetual-futures/"
MOEX_N4_2026_10_18 = MappingProxyType({
    "USDRUBF@RTSX": MoexTickSpec(Decimal("0.01"), Decimal("10"), PREFIX + "USDRUBF"),
    "CNYRUBF@RTSX": MoexTickSpec(Decimal("0.001"), Decimal("1"), PREFIX + "CNYRUBF"),
    "GLDRUBF@RTSX": MoexTickSpec(Decimal("0.1"), Decimal("0.1"), PREFIX + "GLDRUBF"),
    "IMOEXF@RTSX": MoexTickSpec(Decimal("0.5"), Decimal("5"), PREFIX + "IMOEXF"),
})


def contract_from_moex_and_finam(checked: M15InstrumentParams) -> ContractAuthority:
    """One N4 tradeable contract, only after exact broker GO/step/lot proof.

    Frozen MOEX reference is source of tick RUB, live M15-bound FINAM response
    is source of exact executable tick grid, trade lot and LONG/SHORT margin.
    A valid reference does not itself prove realized equity or LIVE readiness.
    """
    if not isinstance(checked, M15InstrumentParams):
        raise M15RiskAuthorityError("M15_EXCHANGE_BROKER_PROOF_REQUIRED")
    spec = MOEX_N4_2026_10_18.get(checked.symbol)
    if spec is None:
        raise M15RiskAuthorityError("M15_EXCHANGE_SYMBOL_NOT_N4")
    if type(checked.price_step) is not Decimal or checked.price_step != spec.price_step:
        raise M15RiskAuthorityError("M15_EXCHANGE_FINAM_PRICE_STEP_MISMATCH")
    contract = ContractAuthority(
        price_step=spec.price_step,
        tick_value=spec.tick_rub,
        trade_lot_size=checked.trade_lot_size,
        long_initial_margin=checked.long_initial_margin_rub,
        short_initial_margin=checked.short_initial_margin_rub,
    )
    try:
        contract.validate()
    except ValueError:
        raise M15RiskAuthorityError("M15_EXCHANGE_CONTRACT_INVALID") from None
    return contract
