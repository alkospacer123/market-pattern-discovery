"""Synthetic diagnostics; no real CSVs, strategy signals or fills."""
from datetime import date, datetime, timedelta
from decimal import Decimal
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from check_m5_readiness import (assumed_available_at, candidate_entry_timing, dated_cny_grid,
                                daytime_windows, envelope, exclusion, summarize)
from session_mtf import Bar


def bar(label, symbol="SYNTHETIC", price="100", volume="100"):
    p = Decimal(price)
    return Bar(label, p, p, p, Decimal(price), Decimal(volume), symbol=symbol)


class M5ReadinessTests(unittest.TestCase):
    def test_availability_is_after_both_possible_closes(self):
        t = datetime(2024, 4, 26, 10, 15)
        self.assertEqual(envelope(t), (t - timedelta(minutes=5), t + timedelta(minutes=5)))
        self.assertEqual(assumed_available_at(t), t + timedelta(minutes=10))

    def test_boundary_and_auction_bars_are_excluded(self):
        day = datetime(2024, 6, 14)
        for h, m, reason in ((9, 55, "outside_candidate_daytime"),
                             (10, 0, "crosses_candidate_boundary"),
                             (14, 5, "crosses_candidate_boundary")):
            self.assertEqual(exclusion(bar(day.replace(hour=h, minute=m))), reason)
        self.assertIsNone(exclusion(bar(day.replace(hour=10, minute=5))))

    def test_quarantine_uses_interval_overlap_not_just_label(self):
        self.assertEqual(exclusion(bar(datetime(2024, 8, 16, 18, 45), "IMOEXF")), "quarantine")
        self.assertIsNone(exclusion(bar(datetime(2024, 8, 16, 18, 40), "IMOEXF")))

    def test_gaps_are_counted_and_never_reconstructed(self):
        bars = [bar(datetime(2024, 12, 30, 10, m)) for m in (5, 15)]
        out = summarize(bars)
        self.assertEqual(out["raw_bars"], 2)
        self.assertEqual(out["potential_observation_bars"], 2)
        self.assertEqual(out["missing_candidate_slots"], 101)
        self.assertEqual(out["authorized_bars"], 0)
        self.assertEqual(out["authorized_dates"], 0)

    def test_zero_volume_does_not_prove_execution(self):
        self.assertEqual(exclusion(bar(datetime(2024, 4, 26, 10, 5), volume="0")), "zero_volume")

    def test_entry_timing_obeys_flat_reserve_without_future_bar_lookup(self):
        self.assertTrue(candidate_entry_timing(bar(datetime(2024, 4, 26, 13, 5))))
        self.assertFalse(candidate_entry_timing(bar(datetime(2024, 4, 26, 13, 10))))
        self.assertTrue(candidate_entry_timing(bar(datetime(2024, 4, 26, 17, 55))))
        self.assertFalse(candidate_entry_timing(bar(datetime(2024, 4, 26, 18))))

    def test_historical_clearing_and_halt_are_not_bridged(self):
        extended = daytime_windows(date(2023, 3, 13))
        self.assertEqual(extended[1][0], datetime(2023, 3, 13, 14, 15))
        self.assertTrue(all(a.hour >= 10 and z.hour <= 19 for a, z in extended))
        halted = daytime_windows(date(2024, 11, 19))
        self.assertEqual(halted[1][1], datetime(2024, 11, 19, 16, 18))
        self.assertEqual(exclusion(bar(datetime(2024, 11, 19, 16, 15))), "crosses_candidate_boundary")

    def test_cny_uses_old_grid_and_flags_switch_ambiguity(self):
        bars = [bar(datetime(2023, 9, 27, 18, 45), "CNYRUBF", "12.001"),
                bar(datetime(2023, 9, 27, 19), "CNYRUBF", "12.001"),
                bar(datetime(2023, 9, 27, 19, 5), "CNYRUBF", "12.001")]
        self.assertEqual(dated_cny_grid(bars), {"old_grid_bars": 1, "new_grid_bars": 1,
                                              "switch_ambiguous_bars": 1, "off_grid_price_fields": 4})


if __name__ == "__main__":
    unittest.main()
