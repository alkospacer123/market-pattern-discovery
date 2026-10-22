"""Focused offline synthetic regression for pooled V20 instrument monitoring."""
import unittest
from datetime import datetime, timedelta
from V20_TradingSystem_M15.v20_runtime.instrument_regime import (
    unique_events, instrument_regime_card, format_card,
)


def paths(n, *, instrument="USDRUBF", values=None, gap=1):
    base = datetime(2024, 1, 1, 10)
    out = []
    for i in range(n):
        stamp = base + timedelta(days=i * gap)
        out.append(dict(instrument=instrument, strategy="SHALLOW_PULLBACK",
                        contract=instrument, signal=stamp,
                        available=stamp + timedelta(days=2),
                        raw_R=float(values[i] if values is not None else i), stop_touch=i % 2 == 0))
    return out


class RegimeTests(unittest.TestCase):
    def test_pooled_exact_duplicates_and_distinct_instruments(self):
        a = paths(40)
        b = [dict(x, strategy="OBV_PRESSURE") for x in a]
        c = [dict(x, instrument="CNYRUBF", contract="CNYRUBF") for x in a]
        card = instrument_regime_card(a + b + c, "USDRUBF", a[-1]["available"])
        self.assertEqual((card["observed_raw_paths"], card["unique_completed_events"],
                          card["duplicate_paths_removed"]), (80, 40, 40))
        self.assertEqual(card["current"]["raw_R"], 29.5)
        self.assertEqual(card["previous"]["raw_R"], 9.5)

    def test_duplicate_conflict_fail_closed(self):
        a = paths(1)[0]
        with self.assertRaisesRegex(ValueError, "CONFLICTING_DUPLICATE"):
            unique_events([a, dict(a, raw_R=999)], instrument="USDRUBF", as_of=a["available"])

    def test_future_sentinel_not_read(self):
        a = paths(40)
        t = a[-1]["available"]
        future = dict(paths(1)[0], signal=t + timedelta(days=1),
                      available=t + timedelta(days=4), raw_R=object())
        self.assertEqual(instrument_regime_card(a + [future], "USDRUBF", t),
                         instrument_regime_card(a, "USDRUBF", t))

    def test_equality_available_atomic(self):
        a = paths(40)
        for x in a:
            x["available"] = datetime(2025, 1, 1, 10)
        before = instrument_regime_card(a, "USDRUBF", datetime(2025, 1, 1, 9, 59))
        at = instrument_regime_card(a, "USDRUBF", datetime(2025, 1, 1, 10))
        self.assertEqual(before["unique_completed_events"], 0)
        self.assertEqual(at["unique_completed_events"], 40)

    def test_persistent_observation_not_prediction(self):
        a = paths(50, values=[5] * 20 + [1] * 30)
        card = instrument_regime_card(a, "USDRUBF", a[-1]["available"])
        self.assertFalse(card["prediction_validated"])
        self.assertFalse(card["affects_orders_or_risk"])
        self.assertEqual(card["status"], "УСТОЙЧИВОЕ НАБЛЮДАЕМОЕ СНИЖЕНИЕ")

    def test_sparse_and_stale(self):
        a = paths(40, gap=30)
        card = instrument_regime_card(a, "USDRUBF", a[-1]["available"])
        self.assertEqual(card["status"], "НЕДОСТАТОЧНО ДАННЫХ")
        b = paths(40)
        card = instrument_regime_card(b, "USDRUBF", b[-1]["available"] + timedelta(days=91))
        self.assertIn("RAW_OUTCOME_STALE", card["reasons"])

    def test_stop_aware_metric_not_pnl(self):
        a = paths(40, values=[2] * 40)
        card = instrument_regime_card(a, "USDRUBF", a[-1]["available"])
        self.assertEqual(card["current"]["raw_R"], 2)
        self.assertEqual(card["current"]["stop_aware_reference_R"], 0.5)
        self.assertIn("НЕ PnL", format_card(card))


if __name__ == "__main__":
    unittest.main()
