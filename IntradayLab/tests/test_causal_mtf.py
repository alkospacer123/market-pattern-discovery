"""Missing-child, delivery, future-mutation and M5 execution regressions."""
from dataclasses import replace
from datetime import datetime, timedelta
from decimal import Decimal as D
import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from causal_mtf import DerivedContext
from audit_causal_mtf import independent_pair
from session_mtf import Bar
from m5_conditional_v2 import Replay, window_at
from run_causal_mtf import MTFFrozen

LAB = Path(__file__).resolve().parents[1]
PARAMS = json.loads((LAB / 'config/stage2_complete_architectures_v1.json').read_text())['parameters']
T = datetime(2023, 1, 3, 10)


def bars(n=48, start=T):
    return [Bar(start + timedelta(minutes=i * 5), D(100 + i), D(102 + i),
                D(99 + i), D(101 + i), D(i + 1), symbol='USDRUBF') for i in range(n)]


class CausalMTFTests(unittest.TestCase):
    def test_exact_ohlcv_and_last_child_delay(self):
        c = DerivedContext(bars(), 30, PARAMS)
        self.assertEqual(c.cells[T].ohlcv, (D(100), D(107), D(99), D(106), D(21)))
        self.assertEqual(c.cells[T].available_at, T + timedelta(minutes=35))

    def test_no_unfinished_or_early_pair(self):
        c = DerivedContext(bars(), 30, PARAMS)
        self.assertIsNone(c.pair(T + timedelta(minutes=64), window_at(T))[0])
        self.assertIsNotNone(c.pair(T + timedelta(minutes=65), window_at(T))[0])

    def test_each_missing_child_rejects_parent(self):
        source = bars()
        for i in range(6):
            c = DerivedContext(source[:i] + source[i + 1:], 30, PARAMS)
            self.assertIsNone(c.cells[T])
            self.assertIsNone(c.pair(T + timedelta(minutes=65), window_at(T))[0])

    def test_gap_invalidates_latest_no_stale_fallback(self):
        source = bars()
        c = DerivedContext(source[:13] + source[14:], 30, PARAMS)
        self.assertIsNotNone(c.pair(T + timedelta(minutes=65), window_at(T))[0])
        self.assertIsNone(c.pair(T + timedelta(minutes=95), window_at(T))[0])
        self.assertIsNone(c.pair(T + timedelta(minutes=125), window_at(T))[0])
        self.assertIsNotNone(c.pair(T + timedelta(minutes=155), window_at(T))[0])

    def test_actual_delayed_earlier_child_controls_release(self):
        source = bars()
        source[2] = replace(source[2], available_at=T + timedelta(minutes=70, seconds=1))
        c = DerivedContext(source, 30, PARAMS)
        self.assertEqual(c.cells[T].available_at, T + timedelta(minutes=75))
        self.assertIsNone(c.pair(T + timedelta(minutes=70), window_at(T))[0])
        self.assertIsNotNone(c.pair(T + timedelta(minutes=75), window_at(T))[0])

    def test_t15_stress_moves_all_contexts(self):
        for minutes in (15, 30, 60):
            c = DerivedContext(bars(), minutes, PARAMS | {'availability_minutes': 15})
            earliest = T + timedelta(minutes=2 * minutes + 10)
            self.assertIsNone(c.pair(earliest - timedelta(minutes=5), window_at(T))[0])
            self.assertIsNotNone(c.pair(earliest, window_at(T))[0])

    def test_h1_and_m15_earliest_delivery(self):
        for minutes in (15, 60):
            c = DerivedContext(bars(), minutes, PARAMS)
            self.assertEqual(c.cells[T].available_at, T + timedelta(minutes=minutes + 5))

    def test_lunch_day_and_clock_alignment(self):
        source = bars(48) + bars(57, datetime(2023, 1, 3, 14, 5)) + bars(48, datetime(2023, 1, 4, 10))
        c = DerivedContext(source, 30, PARAMS)
        self.assertNotIn(datetime(2023, 1, 3, 14), c.cells)
        self.assertNotIn(datetime(2023, 1, 3, 14, 5), c.cells)
        pm = datetime(2023, 1, 3, 14, 30)
        self.assertIsNone(c.pair(pm + timedelta(minutes=35), window_at(pm))[0])
        self.assertIsNone(c.pair(datetime(2023, 1, 4, 10, 35), window_at(datetime(2023, 1, 4, 10)))[0])

    def test_extended_march_break_not_bridged(self):
        source = bars(48, datetime(2023, 3, 14, 10)) + bars(55, datetime(2023, 3, 14, 14, 15))
        c = DerivedContext(source, 15, PARAMS)
        self.assertNotIn(datetime(2023, 3, 14, 14), c.cells)
        at = datetime(2023, 3, 14, 14, 35)
        self.assertIsNone(c.pair(at, window_at(at))[0])

    def test_future_mutations_cannot_change_current_context(self):
        source = bars()
        now = T + timedelta(minutes=65)
        first = DerivedContext(source, 30, PARAMS).describe(now, window_at(T), 1, 'MOMENTUM')
        changed = [replace(b, open=D(1), high=D(99999), low=D(0), close=D(1), volume=D(99999)) if b.timestamp + timedelta(minutes=10) > now else b for b in source]
        other = DerivedContext(changed, 30, PARAMS).describe(now, window_at(T), 1, 'MOMENTUM')
        self.assertEqual(first, other)

    def test_independent_selector_all_synthetic_clocks(self):
        source = bars()
        index = {b.timestamp: b for b in source}
        for minutes in (15, 30, 60):
            for delay in (10, 15):
                c = DerivedContext(source, minutes, PARAMS | {'availability_minutes': delay})
                for i in range(48):
                    now = T + timedelta(minutes=5 * i)
                    self.assertEqual(c.pair(now, window_at(T))[0] is None,
                                     independent_pair(index, minutes, now, window_at(T), delay) is None)

    def test_direction_has_symmetric_economic_meaning(self):
        c = DerivedContext(bars(), 30, PARAMS)
        now = T + timedelta(minutes=65)
        self.assertTrue(c.describe(now, window_at(T), 1, 'MOMENTUM')['mtf_gate_eligible'])
        self.assertFalse(c.describe(now, window_at(T), -1, 'MOMENTUM')['mtf_gate_eligible'])
        self.assertFalse(c.describe(now, window_at(T), -1, 'VWAP_MR')['mtf_gate_eligible'])
        self.assertTrue(c.describe(now, window_at(T), 1, 'VWAP_MR')['mtf_gate_eligible'])

    def test_zero_volume_is_observed_not_missing_or_filled(self):
        c = DerivedContext([replace(b, volume=D(0)) for b in bars()], 30, PARAMS)
        self.assertEqual(c.cells[T].ohlcv[-1], D(0))

    def test_future_year_rejected_before_prices(self):
        class Sentinel:
            timestamp = datetime(2024, 1, 1)
            def __getattr__(self, field):
                raise AssertionError('Future price accessed')
        with self.assertRaises(ValueError):
            DerivedContext([Sentinel()], 30, PARAMS)

    def test_duplicate_and_undeclared_tf_rejected(self):
        with self.assertRaises(ValueError):
            DerivedContext(bars() + bars(1), 30, PARAMS)
        with self.assertRaises(ValueError):
            DerivedContext(bars(), 20, PARAMS)

    def test_mtf_gate_keeps_next_strict_m5_open_and_stop(self):
        source = bars()
        r = MTFFrozen('USDRUBF', 'MOMENTUM', PARAMS)
        r.mtf_context = DerivedContext(source, 30, PARAMS)
        b, now = source[11], T + timedelta(minutes=65)
        f = {'atr': D(2), 'vwap': D(108), 'range_high': D(110), 'range_low': D(90), 'MOMENTUM': 1}
        r.decision(b, now, f)
        ref = Replay('USDRUBF', 'MOMENTUM', PARAMS)
        ref.decision(b, now, f)
        self.assertEqual(r.entry_order['target'], T + timedelta(minutes=70))
        for field in ('stop', 'take', 'cap', 'planned_execution_at'):
            self.assertEqual(r.signals[-1][field], ref.signals[-1][field])
        r.execute(source[14], T + timedelta(minutes=80))
        ref.execute(source[14], T + timedelta(minutes=80))
        self.assertEqual(r.ledger, ref.ledger)

    def test_rejected_context_does_not_create_exposure(self):
        source = bars()
        r = MTFFrozen('USDRUBF', 'MOMENTUM', PARAMS)
        r.mtf_context = DerivedContext(source, 30, PARAMS)
        f = {'atr': D(2), 'vwap': D(108), 'range_high': D(120), 'range_low': D(110), 'MOMENTUM': -1}
        r.decision(source[11], T + timedelta(minutes=65), f)
        self.assertEqual(r.signals[-1]['status'], 'FILTERED')
        self.assertIsNone(r.entry_order)
        self.assertFalse(r.ledger)


if __name__ == '__main__':
    unittest.main()
