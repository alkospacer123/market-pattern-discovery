"""Synthetic immutable M15 seed-to-FINAM seam, no archive or broker access."""
import unittest
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import pandas as pd

from IntradayLab.m15_robot.continuation import (
    M15HistoryContinuityError, immutable_prefix_splice,
)

MSK = ZoneInfo("Europe/Moscow")
T = datetime(2026, 10, 16, 10, 0, tzinfo=MSK)
FIELDS = ("Open", "High", "Low", "Close", "Volume")


def series(offsets, value=100.0):
    return pd.DataFrame(
        [
            (value + i, value + i + 2, value + i - 1, value + i + 1, i + 1)
            for i in offsets
        ],
        index=pd.DatetimeIndex([T + timedelta(minutes=15*i) for i in offsets]),
        columns=FIELDS,
    )


class ImmutableHistory(unittest.TestCase):
    def test_overlap_and_append_exact_following_two(self):
        seed = series([0, 1, 2])
        broker = series([1, 2, 3, 4])
        merged = immutable_prefix_splice(seed, broker)
        self.assertEqual(len(merged), 5)
        pd.testing.assert_frame_equal(merged.iloc[:3], seed)
        pd.testing.assert_frame_equal(merged.iloc[3:], broker.iloc[2:])

    def test_readonly_overlap_without_new_bar(self):
        seed = series([0, 1, 2])
        same = immutable_prefix_splice(seed, series([1, 2]))
        pd.testing.assert_frame_equal(same, seed)

    def test_seam_not_in_30_day_feed_blocks(self):
        with self.assertRaisesRegex(M15HistoryContinuityError, "SEAM_MISSING"):
            immutable_prefix_splice(series([0, 1, 2]), series([3, 4, 5]))

    def test_existing_bar_rewritten_blocks(self):
        seed = series([0, 1, 2])
        broker = series([1, 2, 3])
        broker.iloc[0, 3] = 999.0
        with self.assertRaisesRegex(M15HistoryContinuityError, "HISTORY_CHANGED"):
            immutable_prefix_splice(seed, broker)

    def test_terminal_seam_rewritten_blocks(self):
        seed = series([0, 1, 2])
        broker = series([1, 2, 3])
        broker.iloc[1, 1] = 999.0
        with self.assertRaisesRegex(M15HistoryContinuityError, "HISTORY_CHANGED"):
            immutable_prefix_splice(seed, broker)

    def test_broker_duplicate_index_rejected(self):
        data = series([1, 2, 2, 3])
        with self.assertRaisesRegex(M15HistoryContinuityError, "DUPLICATE"):
            immutable_prefix_splice(series([0, 1, 2]), data)

    def test_old_history_does_not_get_reset_to_30_days(self):
        original = series(list(range(200)))
        observed = series(list(range(195, 206)))
        merged = immutable_prefix_splice(original, observed)
        self.assertEqual(len(merged), 206)
        self.assertEqual(merged.index[0], original.index[0])

    def test_out_of_order_broker_rejected(self):
        broker = series([2, 1, 3])
        with self.assertRaisesRegex(M15HistoryContinuityError, "NONMONOTONIC"):
            immutable_prefix_splice(series([0, 1, 2]), broker)

    def test_broker_missing_msk_timezone_rejected(self):
        broker = series([1, 2, 3]).tz_convert("UTC")
        with self.assertRaisesRegex(M15HistoryContinuityError, "MSK"):
            immutable_prefix_splice(series([0, 1, 2]), broker)

    def test_seed_not_mutated(self):
        seed = series([0, 1, 2])
        frozen_copy = seed.copy(deep=True)
        immutable_prefix_splice(seed, series([1, 2, 3]))
        pd.testing.assert_frame_equal(seed, frozen_copy)

    def test_offgrid_close_index_rejected(self):
        broker = series([1, 2, 3])
        broker.index = broker.index + timedelta(minutes=1)
        with self.assertRaisesRegex(M15HistoryContinuityError, "CLOSE_GRID"):
            immutable_prefix_splice(series([0, 1, 2]), broker)


if __name__ == "__main__":
    unittest.main()
