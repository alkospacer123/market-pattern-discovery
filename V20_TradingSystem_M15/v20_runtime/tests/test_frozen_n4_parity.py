"""04.2: N4 extension of previously confirmed USD frozen signal parity.

Only original published RAW_SIGNAL rows and SHA-pinned external N4 quotes;
no invented outcomes, no broker or H1/M15 mutations. If source CSVs are
unavailable in this checkout, report SKIP, never PASS.
"""
from __future__ import annotations

import csv
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
import unittest

try:
    import pandas as pd
    from V20_TradingSystem_M15.v20_runtime import frozen_adapter
except ImportError:
    pd = None
    frozen_adapter = None

from V20_TradingSystem_M15.v20_runtime.market_reference_descriptive import SOURCE_SHA256

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "V20-03" / "comparison" / "QUOTE_PATH_DIAGNOSTICS.csv"
RAW_SHA = "1f936dca02b9c99ed1df6ca30ef52c4c33128c9d06743175b6f5d6f59dee9c0f"
QUOTE_ROOT = Path("/workspace/market-pattern-data/forever")
# USD parity (three strategies, two sides) is already verified in test_frozen_adapter.py.
NEW_N4 = ("CNYRUBF", "GLDRUBF", "IMOEXF")
STRATEGIES = ("SHALLOW_PULLBACK", "OBV_PRESSURE", "INSIDE_DAY_RELEASE")
REQUIRED = ("Open", "High", "Low", "Close", "Volume")


@unittest.skipIf(pd is None, "Declared frozen pandas/numpy dependencies unavailable")
class AdditionalN4FrozenSignalParity(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        missing = [s for s in NEW_N4
                   if not (QUOTE_ROOT / s / (s + "_M15.csv")).is_file()]
        if missing:
            raise unittest.SkipTest("External N4 source unavailable: " + ",".join(missing))
        if not RAW.is_file():
            raise unittest.SkipTest("Published RAW_SIGNAL ledger unavailable")
        if hashlib.sha256(RAW.read_bytes()).hexdigest() != RAW_SHA:
            raise AssertionError("PUBLISHED_RAW_SIGNAL_SHA_CHANGED")
        for symbol in NEW_N4:
            path = QUOTE_ROOT / symbol / (symbol + "_M15.csv")
            if hashlib.sha256(path.read_bytes()).hexdigest() != SOURCE_SHA256[symbol]:
                raise AssertionError("FROZEN_N4_QUOTES_SHA_CHANGED:" + symbol)

        # First signal per symbol / strategy / direction in 2024, no PnL or
        # eventual success selection. Use only known signal time as cutoff.
        cls.cases = {}
        with RAW.open(newline="") as f:
            for row in csv.DictReader(f):
                if (row["record_type"] != "RAW_SIGNAL"
                        or row["instrument"] not in NEW_N4
                        or not row["signal_bar_dt"].startswith("2024-")):
                    continue
                key = (row["instrument"], row["strategy"], int(row["side"]))
                if row["strategy"] in STRATEGIES:
                    cls.cases.setdefault(key, row)
        required_pairs = {(symbol, strategy)
                          for symbol in NEW_N4 for strategy in STRATEGIES}
        found_pairs = {(symbol, strategy)
                       for symbol, strategy, _side in cls.cases}
        if required_pairs - found_pairs:
            raise AssertionError("NO_PUBLISHED_2024_RAW_FOR_PAIRS:"
                                 + repr(sorted(required_pairs - found_pairs)))

    @staticmethod
    def prefix(symbol, cutoff):
        path = QUOTE_ROOT / symbol / (symbol + "_M15.csv")
        history = []
        with path.open(newline="") as stream:
            for row in csv.DictReader(stream, delimiter=";"):
                stamp = datetime.fromisoformat(row["Datetime"])
                if stamp > cutoff:
                    break  # no future OHLCV converted or read into features
                history.append({"Datetime": stamp,
                                **{field: float(row[field]) for field in REQUIRED}})
        if not history or history[-1]["Datetime"] != cutoff:
            raise AssertionError("NO_EXACT_FINISHED_SIGNAL_M15:" + symbol)
        return pd.DataFrame(history)

    def test_published_first_signal_each_strategy_and_available_side(self):
        checked = set()
        for (symbol, strategy, side), row in sorted(self.cases.items()):
            with self.subTest(symbol=symbol, strategy=strategy, side=side):
                cutoff = datetime.fromisoformat(row["signal_bar_dt"])
                source = self.prefix(symbol, cutoff)
                original = source.copy(deep=True)
                signal = frozen_adapter.completed_signal(
                    symbol, strategy, source,
                    observed_at=cutoff + timedelta(minutes=15))
                self.assertIsNotNone(signal)
                self.assertEqual(
                    (signal.symbol, signal.strategy, signal.side,
                     signal.signal_bar_open),
                    (symbol, strategy, side, cutoff))
                expected_atr = (float(row["ATR14_price_pct"])
                                * float(source.Close.iloc[-1]) / 100.0)
                self.assertAlmostEqual(float(signal.atr14), expected_atr,
                                       delta=max(1e-11, abs(expected_atr) * 1e-9))
                pd.testing.assert_frame_equal(source, original)
                checked.add((symbol, strategy))
        self.assertEqual(
            checked,
            {(symbol, strategy) for symbol in NEW_N4 for strategy in STRATEGIES})


if __name__ == "__main__":
    unittest.main()
