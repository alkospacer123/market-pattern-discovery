"""Pure synthetic N4 MOEX tick-price and FINAM GO matching tests; no token/network."""
import unittest
from dataclasses import replace
from decimal import Decimal

from IntradayLab.m15_robot.broker_risk_readonly import (
    M15InstrumentParams, M15RiskAuthorityError,
)
from IntradayLab.m15_robot.exchange_contract import (
    MOEX_N4_2026_10_18, contract_from_moex_and_finam,
)


def broker_proof(symbol):
    reference = MOEX_N4_2026_10_18[symbol]
    return M15InstrumentParams(
        symbol=symbol, price_step=reference.price_step, trade_lot_size=1,
        long_initial_margin_rub=Decimal("1000.25"),
        short_initial_margin_rub=Decimal("2000.50"),
    )


class ExactExchangeTickRub(unittest.TestCase):
    def test_four_official_contract_tick_values_and_steps(self):
        self.assertEqual(tuple(MOEX_N4_2026_10_18), (
            "USDRUBF@RTSX", "CNYRUBF@RTSX", "GLDRUBF@RTSX", "IMOEXF@RTSX"))
        expected = {
            "USDRUBF@RTSX": ("0.01", "10"),
            "CNYRUBF@RTSX": ("0.001", "1"),
            "GLDRUBF@RTSX": ("0.1", "0.1"),
            "IMOEXF@RTSX": ("0.5", "5"),
        }
        for symbol, (step, value) in expected.items():
            spec = MOEX_N4_2026_10_18[symbol]
            self.assertEqual(spec.price_step, Decimal(step))
            self.assertEqual(spec.tick_rub, Decimal(value))
            self.assertEqual(spec.reference_url.rsplit("/", 1)[-1], symbol.split("@")[0])

    def test_four_n4_official_tick_and_broker_step_match(self):
        for symbol in MOEX_N4_2026_10_18:
            with self.subTest(symbol=symbol):
                approved = contract_from_moex_and_finam(broker_proof(symbol))
                self.assertEqual(approved.tick_value, MOEX_N4_2026_10_18[symbol].tick_rub)
                self.assertEqual(approved.long_initial_margin, Decimal("1000.25"))
                self.assertEqual(approved.short_initial_margin, Decimal("2000.50"))
                self.assertEqual(approved.trade_lot_size, 1)

    def test_broker_step_mismatch_is_fail_closed(self):
        p = replace(broker_proof("IMOEXF@RTSX"), price_step=Decimal("0.1"))
        with self.assertRaisesRegex(M15RiskAuthorityError, "PRICE_STEP_MISMATCH"):
            contract_from_moex_and_finam(p)

    def test_wrong_symbol_is_fail_closed(self):
        p = replace(broker_proof("GLDRUBF@RTSX"), symbol="RI@RTSX")
        with self.assertRaisesRegex(M15RiskAuthorityError, "SYMBOL_NOT_N4"):
            contract_from_moex_and_finam(p)

    def test_broker_proof_required_not_just_ticker(self):
        with self.assertRaisesRegex(M15RiskAuthorityError, "BROKER_PROOF_REQUIRED"):
            contract_from_moex_and_finam("USDRUBF@RTSX")

    def test_missing_broker_go_is_fail_closed(self):
        p = replace(broker_proof("CNYRUBF@RTSX"), short_initial_margin_rub=Decimal("0"))
        with self.assertRaisesRegex(M15RiskAuthorityError, "CONTRACT_INVALID"):
            contract_from_moex_and_finam(p)

    def test_broker_lot_granularity_is_not_exchange_underlying_size(self):
        p = replace(broker_proof("USDRUBF@RTSX"), trade_lot_size=2)
        approved = contract_from_moex_and_finam(p)
        self.assertEqual(approved.trade_lot_size, 2)
        self.assertEqual(approved.tick_value, Decimal("10"))

    def test_not_authority_for_realized_equity_or_costs(self):
        approved = contract_from_moex_and_finam(broker_proof("GLDRUBF@RTSX"))
        self.assertFalse(hasattr(approved, "realized_equity"))
        self.assertFalse(hasattr(approved, "commission"))


if __name__ == "__main__":
    unittest.main()
