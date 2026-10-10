"""Independent oracle regressions for economically material edge cases."""
import importlib.util
from pathlib import Path
import unittest
from datetime import datetime as DT, timedelta as TD
from decimal import Decimal as D, localcontext

spec = importlib.util.spec_from_file_location('independent_m15_oracle', Path(__file__).resolve().parents[1] / 'tools/audit_squeeze_m15.py')
oracle = importlib.util.module_from_spec(spec)
spec.loader.exec_module(oracle)


class IndependentM15OracleTest(unittest.TestCase):
    def source(self):
        start = DT(2023, 1, 3, 10)
        return {start + i * TD(minutes=5): (D('100'), D('100.05'), D('99.95'), D('100'), D(1)) for i in range(48)}

    def replace_parent(self, raw, at, o, h, l, c):
        for i in range(3):
            raw[at + i * TD(minutes=5)] = tuple(map(D, (o, h, l, c))) + (D(1),)

    def opportunity(self, raw, direction=1):
        t = DT(2023, 1, 3, 10, 45)
        if direction > 0:
            self.replace_parent(raw, t, '100', '100.06', '99.95', '100.06')
        else:
            self.replace_parent(raw, t, '100', '100.05', '99.94', '99.94')
        frames = {DT(2023, 1, 3, 10, minute): dict(at=DT(2023, 1, 3, 10, minute), atr7=D('.2'), squeeze=squeeze)
                  for minute, squeeze in ((15, True), (30, True), (45, False))}
        return frames

    def replay(self, raw, frames, scenario=10):
        parents, h1 = oracle.compose(raw, 15), oracle.compose(raw, 60)
        return oracle.reconstruct(raw, 'USDRUBF', 'SQUEEZE_M15', scenario, parents, h1, frames)

    def test_missing_child_is_not_a_parent_or_zero_fill(self):
        raw = self.source()
        frames = self.opportunity(raw)
        del raw[DT(2023, 1, 3, 11, 20)]
        result = self.replay(raw, frames)
        signal, trade = result['signals'][0], result['trade_ledger'][0]
        self.assertEqual(signal['status'], 'UNKNOWN_POSSIBLE_ENTRY_FILL')
        self.assertEqual(trade['unknown_reason'], 'UNKNOWN_POSSIBLE_ENTRY_FILL')
        self.assertIsNone(trade['entry'])
        self.assertIsNone(trade['initial_risk'])
        self.assertIsNone(trade['net'])
        self.assertEqual(trade['model_flat_slot'], DT(2023, 1, 3, 11, 45))
        self.assertEqual(oracle.aggregate([trade])['entries'], 0)
        self.assertEqual(oracle.aggregate([trade])['unknown_entry_orders'], 1)

    def test_same_causal_m15_target_both_delays_and_range_excludes_signal(self):
        raw = self.source()
        frames = self.opportunity(raw)
        for scenario, availability in ((10, 5), (15, 10)):
            result = self.replay(raw, frames, scenario)
            signal = result['signals'][0]
            self.assertEqual(signal['available_at'], DT(2023, 1, 3, 11, availability))
            self.assertEqual(signal['planned_execution_at'], DT(2023, 1, 3, 11, 15))
            self.assertEqual(signal['range_high'], D('100.05'))
            self.assertEqual(signal['squeeze_bars'], 2)

    def test_stop_first_dual_touch_for_long_and_short(self):
        for direction in (1, -1):
            raw = self.source()
            frames = self.opportunity(raw, direction)
            self.replace_parent(raw, DT(2023, 1, 3, 11, 15),
                                '100.10' if direction > 0 else '99.90', '100.6', '99.4',
                                '100.1' if direction > 0 else '99.9')
            trade = self.replay(raw, frames)['trade_ledger'][0]
            self.assertEqual(trade['exit_reason'], 'STOP')
            self.assertIn('STOP_FIRST_BOTH_LEVELS', trade['flags'])
            self.assertIn('ENTRY_BAR_STOP', trade['flags'])
            self.assertLess(trade['net'], 0)
            self.assertEqual(trade['mfe_R'], 0)

    def test_entry_bar_take_forbidden_later_tick_penetration_required(self):
        raw = self.source()
        frames = self.opportunity(raw)
        self.replace_parent(raw, DT(2023, 1, 3, 11, 15), '100.1', '100.6', '100.08', '100.2')
        self.replace_parent(raw, DT(2023, 1, 3, 11, 30), '100.2', '100.42', '100.08', '100.2')
        self.replace_parent(raw, DT(2023, 1, 3, 11, 45), '100.2', '100.43', '100.08', '100.2')
        result = self.replay(raw, frames)
        trade = result['trade_ledger'][0]
        self.assertEqual(trade['exit_at'], DT(2023, 1, 3, 11, 45))
        self.assertEqual(trade['exit_reason'], 'TAKE')
        self.assertEqual(trade['net_R'], 3)
        self.assertEqual([r['reason'] for r in result['execution_events'] if r['kind'] == 'TP_NONFILL'],
                         ['ENTRY_BAR_TP_FORBIDDEN', 'TOUCH_WITHOUT_TICK_PENETRATION'])

    def test_gap_resets_seed_and_no_clearing_bridging(self):
        raw = self.source()
        parents = oracle.compose(raw, 15)
        with localcontext() as ctx:
            ctx.prec = 50
            features = oracle.batch_indicators(parents)
            self.assertNotIn(DT(2023, 1, 3, 11, 15), features)
            self.assertEqual(features[DT(2023, 1, 3, 11, 30)]['warmup'], 7)
            del raw[DT(2023, 1, 3, 11, 40)]
            features = oracle.batch_indicators(oracle.compose(raw, 15))
            self.assertNotIn(DT(2023, 1, 3, 12), features)
            self.assertEqual(features[DT(2023, 1, 3, 13, 15)]['warmup'], 7)
        self.assertIsNone(oracle.window(DT(2023, 1, 3, 14)))
        self.assertIsNone(oracle.window(DT(2023, 1, 3, 18, 45)))

    def test_h1_expected_pair_availability_and_continuity_no_fallback(self):
        raw = self.source()
        h1 = oracle.compose(raw, 60)
        w = oracle.window(DT(2023, 1, 3, 12))
        not_ready = oracle.h1_context(raw, h1, DT(2023, 1, 3, 12), w, 10, 1)
        ready = oracle.h1_context(raw, h1, DT(2023, 1, 3, 12, 5), w, 10, 1)
        self.assertEqual(not_ready['mtf_reason'], 'MTF_TWO_PARENTS_NOT_READY')
        self.assertIsNone(ready['mtf_reason'])
        self.assertEqual(ready['mtf_available_at'], DT(2023, 1, 3, 12, 5))
        del raw[DT(2023, 1, 3, 12, 5)]
        stale = oracle.h1_context(raw, h1, DT(2023, 1, 3, 12, 20), w, 10, 1)
        self.assertEqual(stale['mtf_reason'], 'MTF_CONTINUITY_GAP')

    def test_cost_replacement_identical_executions_and_coverage_labels(self):
        raw = self.source()
        frames = self.opportunity(raw)
        self.replace_parent(raw, DT(2023, 1, 3, 11, 15), '100.1', '100.12', '99.99', '100.1')
        trade = self.replay(raw, frames)['trade_ledger'][0]
        c1, c2 = oracle.aggregate([trade], 1), oracle.aggregate([trade], 2)
        self.assertEqual(c1['entries'], c2['entries'])
        self.assertEqual(c2['closed_net'], c1['closed_net'] - trade['c1'])
        coverage, _ = oracle.calendar(raw, oracle.compose(raw, 15))
        self.assertEqual(coverage['2023-01']['coverage_status'], 'PARTIAL_DATA')
        shifted = {t.replace(month=7, day=11): b for t, b in raw.items()}
        coverage, _ = oracle.calendar(shifted, oracle.compose(shifted, 15))
        self.assertEqual(coverage['2023-06']['coverage_status'], 'NO_COVERAGE')
        self.assertEqual(coverage['2023-07']['coverage_status'], 'PARTIAL_LAUNCH')

    def test_missing_exposure_retains_known_entry_and_unknown_payoff(self):
        raw = self.source()
        frames = self.opportunity(raw)
        self.replace_parent(raw, DT(2023, 1, 3, 11, 15), '100.1', '100.2', '100.08', '100.2')
        del raw[DT(2023, 1, 3, 11, 35)]
        trade = self.replay(raw, frames)['trade_ledger'][0]
        self.assertEqual(trade['entry'], D('100.1'))
        self.assertEqual(trade['unknown_reason'], 'MISSING_EXPOSED_M15_PATH')
        self.assertEqual(trade['model_flat_slot'], DT(2023, 1, 3, 12))
        self.assertIsNone(trade['net'])
        self.assertIsNone(trade['c1'])
        self.assertEqual(oracle.aggregate([trade])['known_entry_cost_unknown'], D('.01'))

    def test_market_open_exit_precedes_exit_bar_protection(self):
        raw = self.source()
        frames = self.opportunity(raw)
        self.replace_parent(raw, DT(2023, 1, 3, 11, 15), '100.1', '100.2', '100.01', '100.03')
        self.replace_parent(raw, DT(2023, 1, 3, 11, 30), '100.15', '100.19', '100.08', '100.16')
        self.replace_parent(raw, DT(2023, 1, 3, 11, 45), '100.09', '101', '99', '100.1')
        trade = self.replay(raw, frames)['trade_ledger'][0]
        self.assertEqual(trade['exit_at'], DT(2023, 1, 3, 11, 45))
        self.assertEqual(trade['exit_reason'], 'FAILED_BREAKOUT')
        self.assertEqual(trade['exit'], D('100.09'))
        self.assertEqual(trade['mfe_R'], D('.9'))

    def test_episode_session_reset_clock_annotation(self):
        raw = self.source()
        parents = oracle.compose(raw, 15)
        frames = {DT(2023, 1, 3, 13, minute): dict(at=DT(2023, 1, 3, 13, minute), atr7=D('.2'), squeeze=True) for minute in (15, 30, 45)}
        for scenario, minute in ((10, 20), (15, 25)):
            cycles, signals = oracle.cycles_and_signals(parents, 'USDRUBF', frames, scenario)
            self.assertEqual(len(cycles), 1)
            self.assertEqual(cycles[0]['terminal_at'], DT(2023, 1, 3, 14, minute))
            self.assertEqual(cycles[0]['terminal_reason'], 'NO_EXPANSION_SESSION')
            self.assertEqual(signals, {})

    def test_h1_does_not_consult_not_yet_delivered_child(self):
        raw = self.source()
        h1 = oracle.compose(raw, 60)
        del raw[DT(2023, 1, 3, 12, 15)]
        context = oracle.h1_context(raw, h1, DT(2023, 1, 3, 12, 20), oracle.window(DT(2023, 1, 3, 12)), 10, 1)
        self.assertIsNone(context['mtf_reason'])


if __name__ == '__main__':
    unittest.main()
