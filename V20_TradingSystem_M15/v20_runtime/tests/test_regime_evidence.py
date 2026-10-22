"""Focused causal/offline checks for statistical evidence card."""
import unittest
from datetime import datetime, timedelta
from V20_TradingSystem_M15.v20_runtime.regime_evidence import (
    exact_lower_tail, observed_independent_events, evidence_card,
)


class RegimeEvidenceTests(unittest.TestCase):
    @staticmethod
    def sample(n, rate=0.5):
        t0 = datetime(2024, 1, 1)
        return [dict(instrument="USDRUBF", contract="USDRUBF",
                     signal=t0+timedelta(days=3*i),
                     available=t0+timedelta(days=3*i+2),
                     fp2=int(i % 2 == 0 if rate == 0.5 else i < int(n*rate)))
                for i in range(n)]

    def test_fisher_exact(self):
        self.assertAlmostEqual(exact_lower_tail(80, 32, 80, 20),
                               0.03141698514025504)
        self.assertAlmostEqual(exact_lower_tail(80, 45, 80, 20),
                               0.0000487472494948279)
        with self.assertRaises(ValueError):
            exact_lower_tail(20, 21, 20, 1)

    def test_no_lookahead_even_poison_value(self):
        rows = self.sample(160)
        at = rows[99]["available"]
        poison = dict(rows[-1], signal=at+timedelta(days=1),
                      available=at+timedelta(days=6), fp2=object())
        self.assertEqual(evidence_card(rows+[poison], "USDRUBF", at),
                         evidence_card(rows, "USDRUBF", at))

    def test_atomic_completion(self):
        rows = self.sample(160)
        t = rows[-1]["available"]
        self.assertEqual(len(evidence_card(rows, "USDRUBF", t)["checks"]), 1)
        self.assertEqual(len(evidence_card(rows, "USDRUBF",
                          t-timedelta(seconds=1))["checks"]), 0)

    def test_no_overlap(self):
        rows = self.sample(10)
        rows[1]["signal"] = rows[0]["signal"] + timedelta(days=1)
        selected = observed_independent_events(rows, "USDRUBF", rows[-1]["available"])
        self.assertEqual(len(selected), 9)

    def test_duplicate_fails_closed(self):
        rows = self.sample(3)
        with self.assertRaisesRegex(ValueError, "DUPLICATE_PUBLISHED"):
            observed_independent_events(rows+[dict(rows[1])], "USDRUBF",
                                        rows[-1]["available"])

    def test_few_data_is_not_good_market(self):
        card = evidence_card(self.sample(80), "USDRUBF",
                             datetime(2024, 12, 31))
        self.assertEqual(card["last_status"], "INSUFFICIENT_EVIDENCE")
        self.assertFalse(card["predictive_reliability_validated"])
        self.assertFalse(card["affects_orders_or_risk"])

    def test_significant_change_only_on_observed_data(self):
        rows = self.sample(160)
        for i in range(80):
            rows[i]["fp2"] = 1
        for i in range(80, 160):
            rows[i]["fp2"] = 0
        card = evidence_card(rows, "USDRUBF", rows[-1]["available"])
        self.assertEqual(card["last_status"], "FP2_DROP_EVIDENCE")
        self.assertLess(card["checks"][-1]["p_down"], card["checks"][-1]["alpha"])

    def test_repeated_look_budget(self):
        total = sum(0.025/(k*(k+1)) for k in range(1, 10000))
        self.assertLess(total, 0.025)
        self.assertGreater(total, 0.02499)

    def test_significant_recovery_uses_upper_tail_in_chronological_order(self):
        rows=self.sample(160)
        for i,row in enumerate(rows):
            row['fp2']=int(i>=80)
        card=evidence_card(rows,'USDRUBF',rows[-1]['available'])
        self.assertEqual(card['last_status'],'FP2_RECOVERY_EVIDENCE')
        check=card['checks'][-1]
        self.assertLess(check['p_up'],check['alpha'])
        self.assertGreater(check['p_down'],.99)


if __name__ == "__main__":
    unittest.main()
