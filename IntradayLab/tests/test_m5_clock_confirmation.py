"""Synthetic clock controls, not real-data strategy/fill tests."""
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from check_m5_clock_confirmation import control_labels, start_label_cny_grid
from session_mtf import Bar


def bar(t, price="12.001"):
    p = Decimal(price)
    return Bar(t, p, p, p, p, Decimal(100), symbol="CNYRUBF")


class M5ClockControlTests(unittest.TestCase):
    def test_start_label_switch_uses_new_tick_at_exact_effective_time(self):
        stats = start_label_cny_grid([
            bar(datetime(2023, 9, 27, 18, 55)), bar(datetime(2023, 9, 27, 19)),
        ])
        self.assertEqual(stats, {"old_grid_bars": 1, "new_grid_bars": 1,
                                 "crosses_tick_switch": 0, "off_grid_price_fields": 4})

    def test_no_control_row_is_invented_for_absent_date(self):
        out = control_labels([bar(datetime(2023, 8, 30, 10))], date(2023, 8, 31))
        self.assertEqual(out["rows"], 0)
        self.assertIsNone(out["first"])
        self.assertIsNone(out["last"])

    def test_halt_control_keeps_crossing_bar_and_actual_restart_label(self):
        out = control_labels([bar(datetime(2024, 11, 19, 16, m)) for m in (15, 50)], date(2024, 11, 19))
        self.assertEqual(out["labels_1610_1700"], ["16:15:00", "16:50:00"])
        self.assertEqual(out["rows"], 2)


if __name__ == "__main__":
    unittest.main()
