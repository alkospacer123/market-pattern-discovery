"""Day-isolated research diagnostics: keep genuine UNKNOWN, never infer flat."""
import sys
from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import orb_false_break_fade_replay as engine
import run_orb_false_break_fade_daywise as daywise

FIVE = timedelta(minutes=5)


def row(o="100", h="101", l="99", c="100"):
    return tuple(map(Decimal, (o, h, l, c, "1")))


def two_day_fixture():
    prices = {}
    for day in (datetime(2023, 1, 3), datetime(2023, 1, 4)):
        for at, _ in engine.slots(day.date()):
            prices[at] = row()
        signal_bar = day.replace(hour=10, minute=15)
        prices[signal_bar] = row("100.95", "101.05", "100.90", "100.95")
    # The first entry is at 10:25; loss of exposed 10:30 bar -> UNKNOWN.
    del prices[datetime(2023, 1, 3, 10, 30)]
    return prices


class DailyResearchMode(unittest.TestCase):
    def test_original_strict_block_kept_and_daywise_restarts_conditional(self):
        prices = two_day_fixture()
        events, _, _ = engine.base_signals("USDRUBF", prices)
        arch = {"atr": False, "mtf": False}
        _, strict = engine.replay("USDRUBF", prices, events, "A_BASE", arch)
        self.assertEqual(len(strict), 1)
        self.assertEqual(strict[0]["status"], "UNKNOWN")
        _, isolated, daily, checked = daywise.evaluate_symbol(
            "USDRUBF", prices, events, "A_BASE", arch
        )
        self.assertGreater(checked, 0)
        self.assertEqual(len(isolated), 2)
        self.assertEqual(isolated[0]["status"], "UNKNOWN")
        self.assertFalse(isolated[0]["prior_unknown_requires_flat_assumption"])
        self.assertEqual(isolated[1]["status"], "CLOSED")
        self.assertTrue(isolated[1]["prior_unknown_requires_flat_assumption"])
        self.assertTrue(daily[1]["prior_unknown_requires_flat_assumption"])
        self.assertEqual(daywise.compact_metrics(isolated)["annual_pf"], None)

    def test_no_claim_of_unknown_resolution_or_annual_pf(self):
        prices = two_day_fixture()
        events, _, _ = engine.base_signals("USDRUBF", prices)
        _, isolated, _, _ = daywise.evaluate_symbol(
            "USDRUBF", prices, events, "A_BASE",
            {"atr": False, "mtf": False}
        )
        self.assertIsNone(isolated[0]["resolved_at"])
        self.assertIsNone(isolated[0]["net_c1"])
        metrics = daywise.compact_metrics(isolated)
        self.assertIsNone(metrics["annual_net"])
        self.assertIsNone(metrics["annual_drawdown"])
        self.assertGreater(metrics["post_unknown_assumption_closed"], 0)

    def test_isolated_second_day_unchanged_if_first_day_price_changes(self):
        prices = two_day_fixture()
        events, _, _ = engine.base_signals("USDRUBF", prices)
        _, first, _, _ = daywise.evaluate_symbol(
            "USDRUBF", prices, events, "A_BASE",
            {"atr": False, "mtf": False}
        )
        prices[datetime(2023, 1, 3, 10, 25)] = row(
            "100.95", "101", "100.9", "100.95"
        )
        events, _, _ = engine.base_signals("USDRUBF", prices)
        _, second, _, _ = daywise.evaluate_symbol(
            "USDRUBF", prices, events, "A_BASE",
            {"atr": False, "mtf": False}
        )
        self.assertEqual(first[-1]["entry_at"], second[-1]["entry_at"])
        self.assertEqual(first[-1]["net_R_c1"], second[-1]["net_R_c1"])


if __name__ == "__main__":
    unittest.main()
