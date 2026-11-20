"""04.2: N4 extension of previously confirmed USD frozen signal parity.

Only original published RAW_SIGNAL rows and SHA-pinned external N4 quotes;
no invented outcomes, no broker or H1/M15 mutations. If source CSVs are
unavailable in this checkout, report SKIP, never PASS.
"""
from __future__ import annotations

import csv
import hashlib
import os
from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

try:
    import pandas as pd
    from V20_TradingSystem_M15.v20_runtime import frozen_adapter
except ImportError:
    pd = None
    frozen_adapter = None

from V20_TradingSystem_M15.v20_runtime.market_reference_descriptive import SOURCE_SHA256
from V20_TradingSystem_M15.v20_runtime.offline_planner import OfflinePlanner
from V20_TradingSystem_M15.v20_runtime.h1_execution import FakeBroker, OfflineH1Executor
from V20_TradingSystem_M15.v20_runtime.h1_state_journal import ROBOT_STRATEGIES
from TradingSystemLab.stage8_robot.production_runtime import _load_registry

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "V20-03" / "comparison" / "QUOTE_PATH_DIAGNOSTICS.csv"
RAW_SHA = "1f936dca02b9c99ed1df6ca30ef52c4c33128c9d06743175b6f5d6f59dee9c0f"
QUOTE_ROOT = Path(os.environ.get("V20_N4_QUOTES_ROOT",
                                     "/workspace/market-pattern-data/forever"))
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
        cls.evidence = []
        with RAW.open(newline="") as f:
            for row in csv.DictReader(f):
                if (row["record_type"] != "RAW_SIGNAL"
                        or row["instrument"] not in NEW_N4
                        or not row["signal_bar_dt"].startswith("2024-")):
                    continue
                key = (row["instrument"], row["strategy"], int(row["side"]))
                if row["strategy"] in STRATEGIES:
                    cls.cases.setdefault(key, row)
        required_pairs = {(symbol, strategy, side)
                          for symbol in NEW_N4 for strategy in STRATEGIES
                          for side in (-1, 1)}
        if required_pairs - cls.cases.keys():
            raise AssertionError("NO_PUBLISHED_2024_RAW_FOR_PAIRS:"
                                 + repr(sorted(required_pairs - cls.cases.keys())))

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
                next_open = cutoff + timedelta(minutes=15)
                self.assertEqual(datetime.fromisoformat(row["entry_dt"]), next_open)
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
                # At NEXT_OPEN only its Open is available, never its future HLCV.
                with (QUOTE_ROOT / symbol / (symbol + "_M15.csv")).open() as f:
                    entry = next(x for x in csv.DictReader(f, delimiter=";")
                                 if datetime.fromisoformat(x["Datetime"]) == next_open)
                self.assertAlmostEqual(float(entry["Open"]), float(row["entry"]))
                binding = _load_registry()[symbol]
                plan = OfflinePlanner(strategy).reference_next_open(
                    signal, at=next_open, entry_open=entry["Open"],
                    realized_equity="500000", price_step=binding["price_step"],
                    tick_value=binding["tick_value"], initial_margin="10000",
                    available_cash="200000", trade_lot_size=1,
                    cost_buffer_per_contract=2*Decimal(binding["tick_value"]))
                robot = next(k for k, v in ROBOT_STRATEGIES.items() if v == strategy)
                broker = FakeBroker("fixture-"+robot)
                with TemporaryDirectory(prefix="v20_n4_execution_") as tmp:
                    state_root = Path(tmp)/"V20Lab"
                    with OfflineH1Executor(state_root, robot, broker.account_id, broker) as executor:
                        key = executor.submit_entry(signal, plan, price_step=binding["price_step"])
                        broker.fill(broker.orders[0]["order_id"], key, plan.quantity,
                                    entry["Open"], next_open.isoformat())
                        result = executor.recover()
                        self.assertIsNone(result["halt"])
                        self.assertEqual(broker.orders[1]["sltp_order"]["sl_price"],
                                         {"value": str(plan.initial_stop)})
                    with OfflineH1Executor(state_root, robot, broker.account_id, broker) as executor:
                        executor.recover()
                        self.assertEqual(executor.submit_entry(signal, plan,
                                         price_step=binding["price_step"]), key)
                        self.assertEqual(broker.post_count, 2)
                self.evidence.append(dict(symbol=symbol, strategy=strategy, side=side,
                                          signal_bar_open=cutoff.isoformat(),
                                          known_at=next_open.isoformat(),
                                          atr=float(signal.atr14), expected_atr=expected_atr,
                                          next_open=float(entry["Open"]),
                                          prefix_rows=len(source), status="PASS",
                                          execution_restart="PASS_FAKE_ONLY",
                                          reference_quantity=plan.quantity,
                                          initial_stop=str(plan.initial_stop)))
                checked.add((symbol, strategy))
        self.assertEqual(
            checked,
            {(symbol, strategy) for symbol in NEW_N4 for strategy in STRATEGIES})


if __name__ == "__main__":
    unittest.main()
