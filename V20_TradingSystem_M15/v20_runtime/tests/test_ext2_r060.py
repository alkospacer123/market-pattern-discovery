"""OFFLINE-only contract tests for TRL-R060 EXT2. No FINAM or LIVE writes."""
from __future__ import annotations

from datetime import datetime, timedelta
import unittest
import pandas as pd

from V20_TradingSystem_M15.v20_runtime.ext2_r060 import ext2_signal_gate, r060_features


def history(side: int, contra: bool = False):
    rows = []
    first = datetime(2026, 9, 1, 10, 0)
    for day in range(18):
        for bar in range(32):
            at = first + timedelta(days=day, minutes=15 * bar)
            if day < 17:
                low, high, op, close = 10.0, 11.0, 10.5, 10.5
            elif side == 1:
                low, high, op, close = 12.6, 13.5, 13.0, 13.4
                if contra and bar == 30:
                    op, close = 13.3, 13.0
            else:
                low, high, op, close = 7.7, 8.7, 8.3, 7.9
                if contra and bar == 30:
                    op, close = 7.9, 8.3
            rows.append({"Datetime": at, "Open": op, "High": high,
                         "Low": low, "Close": close, "Volume": 100.0})
    return pd.DataFrame(rows)


class EXT2R060Acceptance(unittest.TestCase):
    def test_shallow_obv_long_short_exact_threshold_noopposing(self):
        for side in (1, -1):
            raw = history(side)
            stamp = raw.Datetime.iloc[-1]
            for robot in ("v20-shallow", "v20-obv"):
                decision = ext2_signal_gate(
                    robot=robot, symbol="GLDRUBF", side=side,
                    signal_open_msk=stamp, completed_bars=raw)
                self.assertTrue(decision.applicable)
                self.assertFalse(decision.permit)
                self.assertEqual(decision.reason, "EXT2_LATE_NO_OPPOSING_M15")
                self.assertEqual(decision.opposing_m15, 0)

    def test_contra_candle_in_previous_three_allows_same_extreme(self):
        for side in (1, -1):
            raw = history(side, contra=True)
            decision = ext2_signal_gate(robot="v20-obv", symbol="CNYRUBF",
                                        side=side, signal_open_msk=raw.Datetime.iloc[-1],
                                        completed_bars=raw)
            self.assertTrue(decision.permit)
            self.assertEqual(decision.reason, "EXT2_PASS")
            self.assertEqual(decision.opposing_m15, 1)

    def test_inside_and_imoex_are_unmodified(self):
        raw = history(1)
        for robot, symbol in (("v20-inside", "GLDRUBF"),
                              ("v20-shallow", "IMOEXF"), ("v20-obv", "IMOEXF")):
            result = ext2_signal_gate(robot=robot, symbol=symbol, side=1,
                                      signal_open_msk=raw.Datetime.iloc[-1],
                                      completed_bars=raw)
            self.assertTrue(result.permit)
            self.assertFalse(result.applicable)

    def test_unavailable_truncated_or_future_history_blocks_entry(self):
        raw = history(1)
        stamp = raw.Datetime.iloc[-1]
        for frame in (None, raw.iloc[:3]):
            result = ext2_signal_gate(robot="v20-shallow", symbol="USDRUBF",
                                      side=1, signal_open_msk=stamp,
                                      completed_bars=frame)
            self.assertFalse(result.permit)
        extra = raw.tail(1).assign(Datetime=stamp + timedelta(minutes=15))
        result = ext2_signal_gate(robot="v20-shallow", symbol="USDRUBF",
                                  side=1, signal_open_msk=stamp,
                                  completed_bars=pd.concat([raw, extra], ignore_index=True))
        self.assertFalse(result.permit)
        self.assertEqual(result.reason, "EXT2_FUTURE_OR_INCOMPLETE_M15")

    def test_daily_aggregation_uses_previous_day_only(self):
        features = r060_features(history(1))
        self.assertAlmostEqual(float(features.prior_low.iloc[-1]), 10.0)
        self.assertAlmostEqual(float(features.prior_high.iloc[-1]), 11.0)
        self.assertAlmostEqual(float(features.prior_datr14.iloc[-1]), 1.0)


if __name__ == "__main__":
    unittest.main()
