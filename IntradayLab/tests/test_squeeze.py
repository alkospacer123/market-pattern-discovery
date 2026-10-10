"""Hand-calculated rules and execution adversaries, independent of 2023 P&L."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'tools'))
from datetime import datetime as DT, timedelta as TD
from decimal import Decimal as D, localcontext
import unittest
from dataclasses import replace
from unittest.mock import patch

from session_mtf import Bar
from squeeze_replay import Indicators, Cycles, Replay, geometry, FIVE, tick
from causal_mtf import DerivedContext
from audit_squeeze import batch_indicators, reconstruct, m30, compare, aggregate


def bar(t, o='100', h='100.02', l='99.98', c='100', volume='1'):
    return Bar(t, D(o), D(h), D(l), D(c), D(volume), symbol='USDRUBF')


def signal(t=DT(2023, 1, 3, 11)):
    return dict(signal_id='test', direction='LONG', direction_sign=1, signal_at=t,
                available_at=t+TD(minutes=10), planned_execution_at=t+TD(minutes=15),
                range_high=D('100'), range_low=D('99.90'), edge=D('100'), atr20=D('.2'),
                stop=D('99.97'), cap=D('100.1'))


def prepared():
    r = Replay('USDRUBF', 'SQUEEZE_M5')
    r.order = signal()
    b = bar(DT(2023, 1, 3, 11, 15), '100.05', '100.10', '100.04', '100.08')
    r.entry(b, b.timestamp+TD(minutes=10))
    return r


class SqueezeTests(unittest.TestCase):
    def fixture_run(self, delay=10, squeeze_start=20, failed=False, missing=None):
        """Control signal observation only; test actual clock/execution loop."""
        class FixedIndicator:
            def __init__(self):
                self.reset()
            def reset(self):
                self.n = 0
            def observe(self, b):
                self.n += 1
                return dict(at=b.timestamp, atr20=D('.20'), squeeze=squeeze_start <= self.n < squeeze_start+3)
        start = DT(2023, 1, 3, 14, 5)
        breakout = start+(squeeze_start+2)*FIVE
        bars = []
        for i in range(57):
            t = start+i*FIVE
            b = bar(t, '100', '100.10', '99.90', '100') if t < breakout else bar(t, '100.11', '100.20', '100.06', '100.15')
            if failed and t == breakout+TD(minutes=25):
                b = replace(b, close=D('100.08'))
            if t != missing:
                bars.append(b)
        with patch('squeeze_replay.Indicators', FixedIndicator):
            return Replay('USDRUBF', 'SQUEEZE_M5', delay).run(bars)

    def test_max_hold_120_and_future_failed_breakout_exit(self):
        r = self.fixture_run()
        p = r.ledger[0]
        self.assertEqual(p['entry_at'], DT(2023, 1, 3, 16, 10))
        self.assertEqual(p['exit_at'], DT(2023, 1, 3, 18, 10))
        self.assertEqual(p['hold_minutes'], 120)
        self.assertEqual(p['exit_reason'], 'MAX_HOLD')
        r = self.fixture_run(failed=True)
        p = r.ledger[0]
        self.assertEqual(p['exit_reason'], 'FAILED_BREAKOUT')
        self.assertEqual(p['exit_at'], DT(2023, 1, 3, 16, 35))
        self.assertEqual(p['exit'], D('100.11'))

    def test_session_reserve_t10_t15_and_missing_exact_entry(self):
        for delay, expected in ((10, DT(2023, 1, 3, 18, 30)), (15, DT(2023, 1, 3, 18, 25))):
            r = self.fixture_run(delay=delay, squeeze_start=30)
            p = r.ledger[0]
            self.assertEqual(p['exit_reason'], 'SESSION_FLAT')
            self.assertEqual(p['exit_at'], expected)
            self.assertEqual(p['exit_ack'], DT(2023, 1, 3, 18, 40))
            self.assertFalse(p['flat_target_breach'])
        r = self.fixture_run(missing=DT(2023, 1, 3, 16, 10))
        self.assertEqual(r.signals[0]['status'], 'NO_BAR_NO_MODEL_FILL')
        self.assertFalse(any(p['signal_id'] == r.signals[0]['signal_id'] for p in r.ledger))

    def test_population_variance_ema_atr_seed(self):
        indicator = Indicators()
        with localcontext() as ctx:
            ctx.prec = 34
            for i in range(20):
                b = bar(DT(2023, 1, 3, 10)+i*FIVE, str(100+i), str(101+i), str(99+i), str(100+i))
                f = indicator.observe(b)
                if i < 19:
                    self.assertIsNone(f)
            self.assertEqual(f['sma20'], D('109.5'))
            self.assertEqual(f['variance20'], D('33.25'))
            self.assertEqual(f['ema20'], D('109.5'))
            self.assertEqual(f['atr20'], D(2))
            b = bar(DT(2023, 1, 3, 11, 40), '125', '126', '124', '125')
            f = indicator.observe(b)
            self.assertEqual(f['tr'], D(7))
            self.assertEqual(f['atr20'], D('2.25'))
            self.assertEqual(f['ema20'], D('109.5')+D(2)/21*D('15.5'))

    def test_cycle_excludes_breakout_and_is_consumed_once(self):
        c = Cycles('USDRUBF')
        t = DT(2023, 1, 3, 11)
        for i in range(3):
            self.assertIsNone(c.observe(bar(t+i*FIVE), {'squeeze': True}, t+i*FIVE+TD(minutes=10)))
        b = bar(t+3*FIVE, '100.04', '120', '90', '101')
        s = c.observe(b, {'squeeze': False}, b.timestamp+TD(minutes=10))
        self.assertEqual(s['range_high'], D('100.02'))
        self.assertEqual(s['range_low'], D('99.98'))
        self.assertEqual(s['direction'], 'LONG')
        self.assertIsNone(c.observe(b, {'squeeze': False}, b.timestamp+TD(minutes=15)))
        c.observe(bar(t+4*FIVE), {'squeeze': True}, t+TD(minutes=30))
        self.assertEqual(len(c.rows), 2)

    def test_short_no_signal_equality_and_no_expansion(self):
        c = Cycles('USDRUBF')
        t = DT(2023, 1, 3, 11)
        for i in range(3):
            c.observe(bar(t+i*FIVE), {'squeeze': True}, t+i*FIVE+TD(minutes=10))
        self.assertIsNone(c.observe(bar(t+3*FIVE, c='100.02'), {'squeeze': False}, t+TD(minutes=25)))
        s = c.observe(bar(t+4*FIVE, '99.95', '100', '99.90', '99.94'), {'squeeze': False}, t+TD(minutes=30))
        self.assertEqual(s['direction'], 'SHORT')
        c = Cycles('USDRUBF')
        for i in range(3):
            c.observe(bar(t+i*FIVE), {'squeeze': True}, t+i*FIVE+TD(minutes=10))
        c.observe(bar(t+3*FIVE), {'squeeze': False}, t+TD(minutes=25))
        c.reset(t+TD(minutes=30), 'NO_EXPANSION_GAP')
        self.assertEqual(c.rows[0]['terminal_reason'], 'NO_EXPANSION_GAP')

    def test_cost_adjusted_three_R_and_fixed_stop(self):
        s = signal()
        g, why = geometry('USDRUBF', s, D('100.05'), s['planned_execution_at'])
        self.assertIsNone(why)
        self.assertEqual(s['stop'], D('99.97'))
        self.assertEqual(g['initial_risk'], D('.08'))
        self.assertEqual(g['take'], D('100.31'))
        self.assertEqual(g['planned_net_RR'], D(3))
        self.assertEqual(geometry('USDRUBF', s, D('100'), s['planned_execution_at'])[1], 'BREAKOUT_NOT_PERSISTENT')
        self.assertEqual(geometry('USDRUBF', s, D('100.11'), s['planned_execution_at'])[1], 'EXTENSION_OVER_0_5_ATR')
        self.assertEqual(geometry('USDRUBF', s, D('100.01'), s['planned_execution_at'])[1], None)
        s['stop'] = D('100')
        self.assertEqual(geometry('USDRUBF', s, D('100.01'), s['planned_execution_at'])[1], 'RISK_BELOW_FOUR_TICKS')

    def test_stop_first_and_adverse_gap(self):
        r = prepared()
        b = bar(DT(2023, 1, 3, 11, 20), '99.95', '100.40', '99.90', '100')
        r.resident(b, b.timestamp+TD(minutes=10))
        p = r.ledger[0]
        self.assertEqual(p['exit_reason'], 'STOP')
        self.assertEqual(p['exit'], D('99.95'))
        self.assertEqual(p['net'], D('-.12'))
        self.assertIn('STOP_FIRST_BOTH_LEVELS', p['flags'])
        self.assertEqual(p['mfe_R'], D(0))

    def test_tp_touch_and_entry_bar_prohibition(self):
        r = prepared()
        t = DT(2023, 1, 3, 11, 20)
        r.resident(bar(t, '100.10', '100.31', '100', '100.20'), t+TD(minutes=10))
        self.assertIsNotNone(r.position)
        self.assertEqual(r.events[-1]['reason'], 'TOUCH_WITHOUT_TICK_PENETRATION')
        r.resident(bar(t+FIVE, '100.20', '100.32', '100.05', '100.25'), t+TD(minutes=15))
        self.assertEqual(r.ledger[0]['exit_reason'], 'TAKE')
        self.assertEqual(r.ledger[0]['net_R'], D(3))
        r = Replay('USDRUBF', 'SQUEEZE_M5')
        r.order = signal()
        r.entry(bar(DT(2023, 1, 3, 11, 15), '100.05', '100.40', '100.04', '100.30'), DT(2023, 1, 3, 11, 25))
        self.assertIsNotNone(r.position)
        self.assertEqual(r.events[-1]['reason'], 'ENTRY_BAR_TP_FORBIDDEN')

    def test_unknown_never_reconciles_payoff(self):
        r = prepared()
        r.unknown(DT(2023, 1, 3, 11, 30), 'MISSING_EXPOSED_M5_PATH')
        self.assertEqual(r.close_order['target'], DT(2023, 1, 3, 11, 35))
        r.finish(DT(2023, 1, 3, 11, 35), DT(2023, 1, 3, 11, 45), D('200'), 'DATA_GAP_EMERGENCY')
        p = r.ledger[0]
        self.assertEqual(p['status'], 'UNKNOWN')
        self.assertIsNone(p['exit'])
        self.assertIsNone(p['net'])
        self.assertIsNone(p['c1'])

    def test_each_m30_child_missing_and_no_stale_fallback(self):
        start = DT(2023, 1, 3, 10)
        bars = [bar(start+i*FIVE, str(100+i), str(101+i), str(99+i), str(100.5+i)) for i in range(18)]
        now, w = DT(2023, 1, 3, 11, 35), (start, DT(2023, 1, 3, 14))
        for removed in range(12, 18):
            selected = [b for i, b in enumerate(bars) if i != removed]
            ctx = DerivedContext(selected, 30, {'availability_minutes': 10})
            pair, why = ctx.pair(now, w)
            self.assertIsNone(pair)
            self.assertEqual(why, 'MTF_INCOMPLETE_CHILD_BUCKET')
            idx = {b.timestamp: (b.open, b.high, b.low, b.close, b.volume) for b in selected}
            self.assertEqual(m30(idx, now, w, 10, 1)['mtf_reason'], why)
        bars[-1] = replace(bars[-1], available_at=now+FIVE)
        self.assertEqual(DerivedContext(bars, 30, {'availability_minutes': 10}).pair(now, w)[1], 'MTF_CHILD_DELIVERY_NOT_READY')

    def test_future_mutation_does_not_change_past_features_or_decisions(self):
        start = DT(2023, 1, 3, 10)
        bars = []
        for i in range(90):
            p = D(100)+D(i % 7)/100
            bars.append(bar(start+i*FIVE, str(p), str(p+D('.03')), str(p-D('.03')), str(p)))
        cut = DT(2023, 1, 3, 12)
        changed = [b if b.timestamp < cut else replace(b, open=b.open+10, high=b.high+10, low=b.low+10, close=b.close+10) for b in bars]
        a, b = (Replay('USDRUBF', 'SQUEEZE_M5').run(x) for x in (bars, changed))
        self.assertEqual([f for f in a.features if f['at'] < cut], [f for f in b.features if f['at'] < cut])
        self.assertEqual([s for s in a.signals if s['signal_at'] < cut], [s for s in b.signals if s['signal_at'] < cut])

    def test_independent_oracle_on_full_synthetic_path(self):
        start = DT(2023, 1, 3, 10)
        bars = []
        for i in range(70):
            p = D('100') if i < 24 else D('100.15')+D(i % 10)/100 if i < 38 else D('99.90')+D(i % 6)/100
            bars.append(bar(start+i*FIVE, str(p), str(p+D('.03')), str(p-D('.03')), str(p)))
        idx = {b.timestamp: (b.open, b.high, b.low, b.close, b.volume) for b in bars}
        for architecture in ('SQUEEZE_M5', 'SQUEEZE_M30_M5'):
            for delay in (10, 15):
                actual = Replay('USDRUBF', architecture, delay).run(bars)
                with localcontext() as ctx:
                    ctx.prec = 50
                    expected = reconstruct(idx, 'USDRUBF', architecture, delay, batch_indicators(idx))
                for name, rows in expected.items():
                    target = actual.cycles.rows if name == 'squeeze_cycles' else actual.ledger if name == 'trade_ledger' else actual.events if name == 'execution_events' else actual.signals
                    serialized = [{k: '' if v is None else str(v) for k, v in row.items()} for row in target]
                    compare(rows, serialized, name)

    def test_c2_is_substitution_and_tick_switch(self):
        r = prepared()
        r.finish(DT(2023, 1, 3, 11, 30), DT(2023, 1, 3, 11, 40), D('100.31'), 'TAKE')
        a, b = aggregate(r.ledger, 1), aggregate(r.ledger, 2)
        self.assertEqual(a['entries'], b['entries'])
        self.assertEqual(a['closed_net']-b['closed_net'], D('.02'))
        self.assertEqual(tick('CNYRUBF', DT(2023, 9, 27, 18, 50)), D('.01'))
        self.assertEqual(tick('CNYRUBF', DT(2023, 9, 27, 19)), D('.001'))


if __name__ == '__main__':
    unittest.main()
