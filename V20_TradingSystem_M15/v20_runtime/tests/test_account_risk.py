"""04.4 isolated tests with explicit account evidence; no FINAM connection."""
from dataclasses import replace
from decimal import Decimal
import unittest

from V20_TradingSystem_M15.v20_runtime.account_risk import (
    AccountAuthority, RiskBlocked, RiskReservation, reserve_entry, revalue_fill,
)


def authority(account="fake-shallow", *, cash="200000", equity="500000", cost="50", margin="10000"):
    return AccountAuthority(account, Decimal(equity), Decimal(cash), Decimal("0.001"),
                            Decimal("10"), Decimal(margin), 1, Decimal(cost))


def take(a, key="a", *, entry="10.000", atr="0.013", planned_max_quantity=20, existing=()):
    return reserve_entry(authority=a, entry_key=key, symbol="CNYRUBF", direction="LONG",
                         entry=entry, atr14=atr, planned_max_quantity=planned_max_quantity,
                         current_reservations=existing)


class MoneyRiskTests(unittest.TestCase):
    def test_existing_h1_sizing_caps_r15_and_margin(self):
        x = take(authority(), planned_max_quantity=20)
        self.assertEqual(x.initial_stop, Decimal("9.974"))
        self.assertEqual(x.quantity, 20)  # GO 200k/10k; 1.5% allows >20
        self.assertEqual(x.reserved_margin, Decimal("200000"))
        self.assertLessEqual(x.reserved_risk, Decimal("7500"))

    def test_local_pending_reservations_prevent_double_spend(self):
        a = authority()
        first = take(a, planned_max_quantity=15)
        self.assertEqual(first.reserved_margin, Decimal("150000"))
        second = take(a, "b", planned_max_quantity=15, existing=[first])
        self.assertEqual(second.quantity, 5)
        with self.assertRaisesRegex(RiskBlocked, "NO_ACCOUNT_RISK_OR_MARGIN_CAPACITY"):
            take(a, "c", planned_max_quantity=15, existing=[first, second])

    def test_one_lot_cannot_fit_risk_or_go(self):
        with self.assertRaisesRegex(RiskBlocked, "INSUFFICIENT_RISK_OR_MARGIN"):
            take(authority(cash="9999"))
        with self.assertRaisesRegex(RiskBlocked, "INSUFFICIENT_RISK_OR_MARGIN"):
            take(authority(equity="100"))

    def test_missing_evidence_is_fail_closed(self):
        with self.assertRaises(RiskBlocked):
            authority(cash="NaN")
        with self.assertRaises(RiskBlocked):
            authority(equity="0")
        with self.assertRaises(RiskBlocked):
            authority(margin="-1")
        with self.assertRaises(RiskBlocked):
            AccountAuthority("", Decimal("1"), Decimal("10"), Decimal("0.001"), Decimal("1"), Decimal("1"), 1, Decimal("0"))

    def test_six_percent_account_risk_cap_reservations(self):
        a = authority(cash="1000000", margin="1", cost="0")
        taken = [take(a, str(i), planned_max_quantity=20, existing=[]) for i in range(4)]
        # Aggregate exactly 4x original <6%, but a fifth enormous trusted commitment is rejected.
        large = replace(taken[0], entry_key="prior", reserved_risk=Decimal("29999"))
        with self.assertRaisesRegex(RiskBlocked, "INSUFFICIENT_RISK_OR_MARGIN_FOR_ONE_LOT"):
            take(a, "after", existing=[large])

    def test_account_isolation_and_duplicate_reservation(self):
        a = authority()
        x = take(a)
        with self.assertRaisesRegex(RiskBlocked, "ENTRY_KEY_ALREADY_RESERVED"):
            take(a, "a", existing=[x])
        with self.assertRaisesRegex(RiskBlocked, "CROSS_ACCOUNT_RESERVATION"):
            take(authority("fake-obv"), existing=[x])

    def test_vwap_slippage_and_fee_revaluation(self):
        x = take(authority(), planned_max_quantity=15)
        actual = revalue_fill(x, [(2, "10.001", "3"), (3, "10.002", "4")])
        self.assertEqual(actual["filled_quantity"], 5)
        self.assertEqual(actual["status"], "PASS")
        self.assertEqual(actual["known_fees"], "7")
        self.assertEqual(actual["reserved_margin"], "50000")
        self.assertEqual(actual["projected_stop"], "9.975")

    def test_actual_fee_or_aggregate_excess_blocks_new_entries(self):
        x = take(authority(cash="500000", margin="10000", cost="0"), planned_max_quantity=15)
        expensive = revalue_fill(x, [(15, "10.000", "20000")])
        self.assertEqual(expensive["reason"], "ACTUAL_FILL_EXCEEDS_R15")
        aggregated = revalue_fill(x, [(15, "10.000", "0")], other_reserved_risk="29990")
        self.assertEqual(aggregated["reason"], "ACCOUNT_INITIAL_RISK_EXCEEDS_R6")

    def test_partial_fills_and_restart_serialization(self):
        x = take(authority(), planned_max_quantity=10)
        recovered = RiskReservation.restore(x.record())
        self.assertEqual(recovered, x)
        first = revalue_fill(recovered, [(2, "10.000", "0")])
        second = revalue_fill(recovered, [(2, "10.000", "0"), (3, "10.001", "2")])
        self.assertEqual(first["filled_quantity"], 2)
        self.assertEqual(second["filled_quantity"], 5)
        with self.assertRaisesRegex(RiskBlocked, "FILL_OVER_QUANTITY"):
            revalue_fill(recovered, [(11, "10", "0")])


if __name__ == "__main__":
    unittest.main()
