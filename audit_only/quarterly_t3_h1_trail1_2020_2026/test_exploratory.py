"""Nontrivial edge cases; full historical audits run inside run_exploratory.py."""
import unittest
import sys
from pathlib import Path
import numpy as np
import pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from exploratory_core import metrics, metric_audit
from roll_diagnostics import windows, near


class ExploratoryTests(unittest.TestCase):
    def frame(self):
        return pd.DataFrame({"exit_time": pd.to_datetime(["2021-12-31T23:00:00Z", "2022-01-02T07:00:00Z", "2022-01-03T07:00:00Z"], utc=True).tz_convert("Europe/Moscow"),
            "instrument": ["Si"]*3, "trade_id": ["1", "2", "3"], "gross_R": [2., -3., 1.], "cost_R": [.1]*3, "net_R_C1": [1.9, -3.1, .9]})

    def test_drawdown_includes_zero_and_is_invariant_to_input_permutation(self):
        f = self.frame()
        self.assertAlmostEqual(metrics(f)["max_closed_R_drawdown"], -3.1)
        self.assertEqual(metrics(f), metrics(f.iloc[::-1]))
        self.assertTrue(metric_audit(f))

    def test_moscow_exit_year_differs_from_utc_year(self):
        f = self.frame()
        self.assertEqual(f.exit_time.iloc[0].year, 2022)
        self.assertEqual(f.exit_time.iloc[0].tz_convert("UTC").year, 2021)

    def test_no_losses_does_not_become_zero_pf(self):
        f = self.frame().iloc[[0]]
        self.assertIsNone(metrics(f)["net_pf"])
        self.assertTrue(metric_audit(f))
        self.assertEqual(metrics(f.iloc[:0])["trades"], 0)

    def test_calendar_proxy_is_labelled_unconfirmed_and_has_inclusive_end_day(self):
        w = [x for x in windows() if x["definition"] == "quarter_3d" and x["anchor"].year == 2026 and x["anchor"].month == 3]
        self.assertEqual(w[0]["anchor"].day, 19)
        self.assertFalse(w[0]["actual_roll_date_confirmed"])
        self.assertTrue(near(pd.Timestamp("2026-03-22 23:00", tz="Europe/Moscow"), w))
        self.assertFalse(near(pd.Timestamp("2026-03-23", tz="Europe/Moscow"), w))


if __name__ == "__main__": unittest.main(verbosity=2)
