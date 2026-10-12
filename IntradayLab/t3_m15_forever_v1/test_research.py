"""Standalone correctness, causal availability and reference regression tests."""
import io
import json
from pathlib import Path
import tempfile
import unittest

import numpy as np
import pandas as pd

from engine import (CONFIGS, TZ, Parameters, close_index, context, execute,
                    indicators, read_prefix)
from research import compare, metrics

HERE = Path(__file__).resolve().parent


def candles(n=1000):
    at = pd.date_range("2023-01-03 09:15", periods=n, freq="15min", tz=TZ)
    price = 100 + np.arange(n)*.01 + np.sin(np.arange(n)/7)
    return pd.DataFrame({"Open": price, "High": price+.2, "Low": price-.2,
                         "Close": price+.05, "Volume": 10.}, index=at)


def execution_bars(rows):
    """Open, High, Low, Close, ATR, Signal; features intentionally controlled."""
    return pd.DataFrame(rows, columns=["Open", "High", "Low", "Close", "ATR", "Signal"],
                        index=pd.date_range("2023-01-03 10:00", periods=len(rows), freq="15min", tz=TZ))


class Correctness(unittest.TestCase):
    def test_future_ohlc_not_read_or_parsed(self):
        # A completely malformed future OHLC suffix must be unreachable.
        with tempfile.TemporaryDirectory() as folder:
            p = Path(folder)/"source.csv"
            p.write_text("Ticker;Datetime;Open;High;Low;Close;Volume\nX;2024-12-30 23:45:00;1;2;1;2;10\nX;2025-01-01 00:00:00;MUST_NOT_PARSE;bad;bad;bad;bad\n")
            frame, _ = read_prefix(p)
            self.assertEqual(len(frame), 1)
            self.assertEqual(close_index(frame).index[0], pd.Timestamp("2024-12-31 00:00", tz=TZ))

    def test_close_availability_and_daily_blocks(self):
        f = candles(9)
        h = context(f)
        self.assertEqual(list(h.index), [f.index[3], f.index[7]])
        self.assertEqual(h.Close.iloc[0], f.Close.iloc[3])
        second = f.iloc[:3].copy()
        second.index += pd.Timedelta(days=1)
        h2 = context(pd.concat([f.iloc[:3], second]))
        self.assertEqual(len(h2), 0)  # Never join daily leftovers.

    def test_gapped_block_not_repacked(self):
        f = candles(9).drop(candles(9).index[1])
        h = context(f)
        self.assertEqual(list(h.index), [f.index[7]])

    def test_indicators_prefix_and_future_mutation(self):
        full = candles(1000)
        prefix = full.iloc[:700]
        a, ah = indicators(prefix, Parameters())
        b, bh = indicators(full, Parameters())
        pd.testing.assert_frame_equal(a, b.loc[a.index])
        pd.testing.assert_frame_equal(ah, bh.loc[ah.index])
        mutated = full.copy()
        mutated.loc[mutated.index[700:], ["Open", "High", "Low", "Close"]] *= 8
        c, _ = indicators(mutated, Parameters())
        pd.testing.assert_frame_equal(a, c.loc[a.index])

    def test_no_current_bar_in_donchian(self):
        f = candles(100)
        f.iloc[30, f.columns.get_loc("High")] = 9999
        low, _ = indicators(f, Parameters())
        self.assertEqual(low.PriorHigh.iloc[30], f.High.iloc[10:30].max())
        self.assertEqual(low.PriorHigh.iloc[31], 9999)

    def test_h1_regime_unavailable_before_fourth_close(self):
        low, high = indicators(candles(500), Parameters())
        first_ready = high.index[79]  # 75 EMA bars + 5-bar slope.
        self.assertTrue(high.Slope.iloc[:79].isna().all())
        self.assertTrue((low.loc[low.index < first_ready, "Signal"] == 0).all())

    def test_stop_precedes_trailing_and_stop_bar_mfe(self):
        low = execution_bars([[100,100,100,100,1,1], [100,110,97,100,1,0]])
        f, opened = execute(low, "USDRUBF", "BASELINE", Parameters(), .001)
        self.assertIsNone(opened)
        self.assertEqual(f.exit_price.iloc[0], 98)
        self.assertEqual(f.MFE_R.iloc[0], 0)
        self.assertEqual(f.MAE_R.iloc[0], 1)
        self.assertEqual(f.exit_type.iloc[0], "INITIAL_STOP")

    def test_ratchet_used_only_next_bar(self):
        low = execution_bars([[100,100,100,100,1,1], [100,110,99,109,1,0], [108,108,106,107,1,0]])
        f, _ = execute(low, "USDRUBF", "BASELINE", Parameters(), .001)
        self.assertEqual(f.exit_price.iloc[0], 107)
        self.assertEqual(f.MFE_R.iloc[0], 5)
        self.assertEqual(f.bars_held.iloc[0], 2)
        self.assertEqual(f.exit_type.iloc[0], "RATCHETED_STOP")

    def test_gap_and_same_bar_reentry(self):
        low = execution_bars([[100,100,100,100,1,1], [97,99,96,99,1,-1], [103,104,102,103,1,0]])
        f, _ = execute(low, "USDRUBF", "BASELINE", Parameters(), .001)
        self.assertEqual(list(f.exit_price), [97,103])
        self.assertEqual(list(f.gross_R), [-1.5,-2])
        self.assertEqual(f.entry_time.iloc[1], f.exit_time.iloc[0])
        self.assertTrue(f.gap_exit.all())

    def test_c1_r_and_price_scaling(self):
        a = execution_bars([[100,100,100,100,1,1], [100,100,98,98,1,0]])
        f, _ = execute(a, "GLDRUBF", "BASELINE", Parameters(), .1)
        self.assertAlmostEqual(f.C1_R.iloc[0], .1)
        self.assertAlmostEqual(f.net_R.iloc[0], -1.1)
        b = a.copy()
        b[["Open","High","Low","Close","ATR"]] *= 10
        g, _ = execute(b, "IMOEXF", "BASELINE", Parameters(), 1)
        np.testing.assert_allclose(f[["gross_R","net_R","MAE_R","MFE_R"]], g[["gross_R","net_R","MAE_R","MFE_R"]], rtol=0, atol=1e-12)

    def test_open_terminal_position_not_fabricated(self):
        a = execution_bars([[100,100,100,100,1,1]])
        f, opened = execute(a, "USDRUBF", "BASELINE", Parameters(), .001)
        self.assertEqual(len(f), 0)
        self.assertIn("OPEN_NOT_LIQUIDATED", opened["status"])

    def test_drawdown_streak_and_concentration(self):
        # Mutate known closed records, then assert independently hand-calculated statistics.
        a = execution_bars([[100,100,100,100,1,1], [100,100,98,98,1,0]])
        row, _ = execute(a, "GLDRUBF", "BASELINE", Parameters(), .1)
        f = pd.concat([row]*8, ignore_index=True)
        f["trade_id"] = [str(i) for i in range(8)]
        f["exit_time"] = pd.date_range("2023-02-01", periods=8, tz=TZ)
        f["net_R"] = [3,-2,-2,1,4,-1,-1,2]
        m = metrics(f)
        self.assertEqual(m["max_drawdown_R"], 4)
        self.assertEqual(m["max_losing_streak"], 2)
        self.assertEqual(m["net_R"], 4)
        self.assertEqual(m["net_R_without_top5"], -5)

    def test_comparator_detects_numeric_and_order_errors(self):
        a = execution_bars([[100,100,100,100,1,1], [100,100,98,98,1,0]])
        f, _ = execute(a, "GLDRUBF", "BASELINE", Parameters(), .1)
        d, _ = compare("BASELINE", f, f)
        self.assertEqual(d, [])
        changed = f.copy()
        changed.loc[0,"initial_stop"] += 1e-6
        changed.loc[0,"direction"] = "SHORT"
        d, _ = compare("BASELINE", changed, f)
        self.assertEqual({r["field"] for r in d}, {"initial_stop","direction"})

    def test_published_gate_regression(self):
        detail = json.loads((HERE/"REPRODUCTION_DETAIL.json").read_text())
        self.assertEqual(detail["gate_a"], "PASS")
        self.assertEqual([r["actual_trades"] for r in detail["replays"]], [425,401])
        self.assertEqual(detail["total_differences"], 0)
        self.assertEqual(sum(r["candles"] for r in detail["source_equality"]), 59523)


if __name__ == "__main__":
    unittest.main()
