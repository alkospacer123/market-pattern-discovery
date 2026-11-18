"""R088 one-fix regression: R060 can contain an M15 absent from FINAM.

No real source ZIP, broker API, journals, or LIVE mutations involved.
"""
from __future__ import annotations

from datetime import datetime
from importlib.util import spec_from_file_location, module_from_spec
from pathlib import Path
from unittest import TestCase, main
import pandas as pd

from V20_TradingSystem_M15.v20_runtime.ext2_history_bridge import EXT2HistoryBlocked

BUILDER = (Path(__file__).resolve().parents[2] / "V20-08" /
           "r088-build-usd-gld-offline-checkpoints.py")
spec = spec_from_file_location("r088_gld_source_stitch", BUILDER)
module = module_from_spec(spec)
assert spec is not None and spec.loader is not None
spec.loader.exec_module(module)


def frame(stamps):
    return pd.DataFrame({
        "Datetime": pd.to_datetime(stamps),
        "Open": [100.] * len(stamps), "High": [101.] * len(stamps),
        "Low": [99.] * len(stamps), "Close": [100.] * len(stamps),
        "Volume": [12.] * len(stamps),
    }).set_index("Datetime")


class ExactFinamPriorityStitchTests(TestCase):
    def setUp(self):
        self.seed = frame([
            "2026-09-26T17:45:00",
            "2026-09-27T09:45:00",
            "2026-09-27T10:00:00",
            "2026-09-27T10:15:00",
            "2026-09-27T10:30:00",
            "2026-09-27T10:45:00",
            "2026-09-27T11:00:00",
        ])
        self.finam = self.seed.loc[
            ~self.seed.index.isin(pd.to_datetime([
                "2026-09-27T10:00:00", "2026-09-27T10:30:00",
            ])) & (self.seed.index >= pd.Timestamp("2026-09-27T09:45:00"))
        ].copy()

    def test_known_gld_absences_are_not_restored_from_r060(self):
        result, overlap, skipped = module._stitch_pinned_finam_priority(
            self.seed, self.finam, "GLDRUBF")
        self.assertEqual(len(skipped), 2)
        self.assertEqual(tuple(str(x) for x in skipped), (
            "2026-09-27 10:00:00", "2026-09-27 10:30:00"))
        self.assertEqual(len(result), 1 + len(self.finam))
        self.assertEqual(len(overlap), 3)
        self.assertEqual(len(result), 5)
        self.assertFalse(result.Datetime.isin(skipped).any())

    def test_unknown_loss_and_different_symbol_fail_closed(self):
        with self.assertRaisesRegex(
                EXT2HistoryBlocked,
                "R088_SEED_FINAM_UNAPPROVED_DISAPPEARING_M15"):
            module._stitch_pinned_finam_priority(
                self.seed, self.finam, "USDRUBF")
        missing_more = self.finam.drop(pd.Timestamp("2026-09-27T11:00:00"))
        with self.assertRaisesRegex(
                EXT2HistoryBlocked,
                "R088_SEED_FINAM_UNAPPROVED_DISAPPEARING_M15"):
            module._stitch_pinned_finam_priority(
                self.seed, missing_more, "GLDRUBF")

    def test_same_open_disagreeing_ohlcv_still_blocks(self):
        modified = self.finam.copy()
        modified.loc[pd.Timestamp("2026-09-27T10:45:00"), "High"] += 1
        with self.assertRaisesRegex(
                EXT2HistoryBlocked, "R088_SEED_FINAM_OVERLAP_DISAGREEMENT"):
            module._stitch_pinned_finam_priority(
                self.seed, modified, "GLDRUBF")


if __name__ == "__main__":
    main()
