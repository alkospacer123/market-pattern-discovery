"""N4 shared capacity and 6% cap; all offline, synthetic exact Decimal."""
import unittest
from decimal import Decimal as d

from IntradayLab.m15_robot.grid_risk import ContractAuthority
from IntradayLab.m15_robot.risk_batch import M15BatchRiskBudget, M15BatchRiskError

N4 = ("USDRUBF", "CNYRUBF", "GLDRUBF", "IMOEXF")


def authority(*, lot=1, long_go="2000", short_go="3000"):
    return ContractAuthority(d("1"), d("10"), lot, d(long_go), d(short_go))


def budget(**kwargs):
    return M15BatchRiskBudget(realized_equity=kwargs.pop("realized_equity", d("100000")),
                              available_margin_cash=kwargs.pop("available_margin_cash", d("200000")),
                              **kwargs)


def add(b, symbol="USDRUBF", direction="LONG", price="100", stop="90", contract=None):
    return b.size_and_reserve(instrument=symbol, direction=direction, entry=d(price),
                              stop=d(stop), contract=contract or authority())


class M15N4Capacity(unittest.TestCase):
    def test_all_four_respect_aggregate_six_percent(self):
        b = budget()
        results = [add(b, x) for x in N4]
        self.assertEqual([r.final_quantity for r in results], [15, 15, 15, 15])
        self.assertEqual(b.committed_initial_risk, d("6000"))
        self.assertEqual(b.remaining_margin_cash, d("80000"))
        self.assertFalse(b.execution_authorized)

    def test_margin_not_spent_twice_on_four_signals(self):
        b = budget(available_margin_cash=d("45000"))
        quantities = [add(b, x).final_quantity for x in N4]
        self.assertEqual(quantities, [15, 7, 0, 0])
        self.assertEqual(b.remaining_margin_cash, d("1000"))
        self.assertEqual(b.committed_initial_risk, d("2200"))

    def test_existing_nominal_initial_risk_depletes_capacity(self):
        b = budget(committed_initial_risk=d("5900"))
        self.assertEqual(add(b, "USDRUBF").final_quantity, 1)
        self.assertEqual(add(b, "CNYRUBF").final_quantity, 0)
        self.assertEqual(b.committed_initial_risk, d("6000"))

    def test_zero_cash_keeps_position_count_zero(self):
        b = budget(available_margin_cash=d("0"))
        self.assertEqual(add(b).final_quantity, 0)
        self.assertEqual(b.occupied_instruments, set())

    def test_zero_capacity_does_not_reserve_or_occupy(self):
        b = budget(committed_initial_risk=d("6000"))
        self.assertEqual(add(b).reason, "ZERO_RISK_OR_MARGIN_CAPACITY")
        self.assertEqual(b.remaining_margin_cash, d("200000"))
        self.assertEqual(b.occupied_instruments, set())

    def test_duplicate_signal_same_instrument_denied(self):
        b = budget()
        add(b)
        with self.assertRaisesRegex(M15BatchRiskError, "OCCUPIED"):
            add(b)
        self.assertEqual(b.committed_initial_risk, d("1500"))

    def test_existing_broker_position_is_occupied(self):
        b = budget(occupied_instruments=("CNYRUBF",))
        with self.assertRaisesRegex(M15BatchRiskError, "OCCUPIED"):
            add(b, "CNYRUBF")

    def test_unknown_instrument_fails(self):
        b = budget()
        with self.assertRaisesRegex(M15BatchRiskError, "UNKNOWN_INSTRUMENT"):
            add(b, "BR")
        self.assertEqual(b.occupied_instruments, set())

    def test_wrong_account_financial_inputs_denied(self):
        for value in (d("-1"), d("nan"), "100000", d("infinity")):
            with self.subTest(value=str(value)):
                with self.assertRaisesRegex(M15BatchRiskError, "FINANCIAL_INVALID"):
                    budget(realized_equity=value)

    def test_duplicate_occupied_list_denied(self):
        with self.assertRaisesRegex(M15BatchRiskError, "DUPLICATE"):
            budget(occupied_instruments=("USDRUBF", "USDRUBF"))

    def test_short_uses_its_own_higher_margin(self):
        b = budget(available_margin_cash=d("10000"))
        r = add(b, direction="SHORT", stop="110")
        self.assertEqual(r.final_quantity, 3)
        self.assertEqual(b.remaining_margin_cash, d("1000"))

    def test_granularity_down_rounds(self):
        b = budget()
        r = add(b, contract=authority(lot=4))
        self.assertEqual(r.final_quantity, 12)
        self.assertEqual(b.committed_initial_risk, d("1200"))

    def test_invalid_stop_does_not_consume_capacity(self):
        b = budget()
        with self.assertRaisesRegex(ValueError, "GRID"):
            add(b, stop="90.5")
        self.assertEqual(b.remaining_margin_cash, d("200000"))
        self.assertEqual(b.committed_initial_risk, d("0"))
        self.assertEqual(b.occupied_instruments, set())

    def test_invalid_direction_does_not_consume_capacity(self):
        b = budget()
        with self.assertRaisesRegex(ValueError, "DIRECTION"):
            add(b, direction="FLAT")
        self.assertEqual(b.remaining_margin_cash, d("200000"))
        self.assertEqual(b.occupied_instruments, set())

    def test_malformed_instrument_contract_does_not_consume_capacity(self):
        b = budget()
        with self.assertRaisesRegex(ValueError, "CONTRACT"):
            add(b, contract=authority(long_go="0"))
        self.assertEqual(b.occupied_instruments, set())

    def test_commissions_and_fees_are_not_estimated(self):
        b = budget()
        add(b)
        self.assertFalse(hasattr(b, "commission"))
        self.assertFalse(hasattr(b, "fees"))


if __name__ == "__main__":
    unittest.main()
