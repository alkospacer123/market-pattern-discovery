"""Reporting safety regressions and physically bounded independent reader."""
import io
from pathlib import Path
import sys
import unittest
from decimal import Decimal as D
from datetime import datetime

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'tools'))
from independent_corrective_review import aggregate, breakout_diagnostic, exact_lines, independent_tick, intervals


def closed(net):
    return {'status': 'MODELLED', 'net_model_c1': str(net),
            'gross_price_pnl': str(D(net)+D('.02')), 'c1_total': '.02', 'exit_reason': 'STOP'}


class RawSentinel(io.RawIOBase):
    def __init__(self, allowed):
        self.data = io.BytesIO(allowed)
        self.limit = len(allowed)
        self.requests = []

    def read(self, count=-1):
        if count < 0 or self.data.tell()+count > self.limit:
            raise AssertionError('Attempt to read a protected future byte')
        self.requests.append(count)
        return self.data.read(count)


class CorrectiveReporting(unittest.TestCase):
    def test_unknown_trade_cannot_publish_known_subset_pf_as_full(self):
        unknown = {'status': 'UNRESOLVED', 'net_model_c1': '', 'exit_reason': 'UNKNOWN_PATH'}
        r = aggregate([closed('.20'), closed('-.10'), unknown], 'COVERED')
        self.assertEqual(r['net_PF_closed_diagnostic'], D(2))
        for field in ('PF', 'full_PF', 'Net', 'net_model_c1', 'Drawdown'):
            self.assertIsNone(r[field], field)
        self.assertEqual(r['PF_null_reason'], 'UNRESOLVED')
        self.assertIsNone(r['net_PF_closed_diagnostic_null_reason'])

    def test_partial_month_cannot_be_published_as_complete(self):
        r = aggregate([closed('.20'), closed('-.10')], 'PARTIAL_COVERAGE')
        self.assertEqual(r['closed_only_net_c1'], D('.10'))
        self.assertEqual(r['metric_status'], 'PARTIAL_COVERAGE')
        self.assertIsNone(r['full_PF'])
        self.assertIsNone(r['Net'])

    def test_complete_month_publishes_exact_net_and_pf(self):
        r = aggregate([closed('.20'), closed('-.10')], 'COVERED')
        self.assertEqual(r['full_PF'], D(2))
        self.assertEqual(r['PF'], r['full_PF'])
        self.assertEqual(r['Net'], D('.10'))
        self.assertIsNone(r['PF_null_reason'])
        self.assertIsNone(r['Drawdown'])
        self.assertEqual(r['Drawdown_null_reason'], 'INTRABAR_PATH_UNOBSERVED')

    def test_no_coverage_is_not_zero_profit(self):
        r = aggregate([], 'NO_COVERAGE')
        self.assertEqual(r['metric_status'], 'NO_COVERAGE')
        self.assertIsNone(r['Net'])
        self.assertIsNone(r['closed_only_net_c1'])
        self.assertEqual(r['full_PF_null_reason'], 'NO_COVERAGE')

    def test_covered_zero_trades_is_zero_net_and_undefined_pf(self):
        r = aggregate([], 'COVERED')
        self.assertEqual(r['metric_status'], 'ZERO_TRADES')
        self.assertEqual(r['Net'], 0)
        self.assertIsNone(r['PF'])
        self.assertEqual(r['PF_null_reason'], 'NO_CLOSED_TRADES')

    def test_no_losses_reason_is_separate_from_unknown_full_pf(self):
        r = aggregate([closed('.20')], 'PARTIAL_COVERAGE')
        self.assertEqual(r['PF_null_reason'], 'PARTIAL_COVERAGE')
        self.assertEqual(r['net_PF_closed_diagnostic_null_reason'], 'NO_LOSSES')

    def test_cross_month_unknown_exposure_blocks_empty_month_full_result(self):
        r = aggregate([], 'COVERED', spanning_unknown=True)
        self.assertEqual(r['metric_status'], 'UNRESOLVED')
        self.assertIsNone(r['Net'])
        self.assertFalse(r['full_period_accounted'])

    def test_zero_net_closed_trade_still_counts_as_accounted(self):
        r = aggregate([closed('0')], 'COVERED')
        self.assertEqual(r['closed_accounted_trades'], 1)
        self.assertEqual(r['net_expectancy_closed_diagnostic'], 0)
        self.assertEqual(r['closed_only_c1'], D('.02'))

    def test_exact_reader_never_probes_future_sentinel(self):
        raw = RawSentinel(b'header\n2023-row\n')
        self.assertEqual(list(exact_lines(raw, 2)), [b'header\n', b'2023-row\n'])
        self.assertEqual(raw.data.tell(), raw.limit)
        self.assertTrue(all(n == 1 for n in raw.requests))

    def test_independent_reader_rejects_buffered_input(self):
        with self.assertRaises(ValueError):
            list(exact_lines(io.BytesIO(b'header\n'), 1))

    def test_each_side_uses_tick_at_exact_historical_switch(self):
        before = independent_tick('CNYRUBF', datetime(2023, 9, 27, 18, 59, 59))
        after = independent_tick('CNYRUBF', datetime(2023, 9, 27, 19))
        self.assertEqual(before+after, D('.011'))

    def test_march_clearing_exception_and_reversion(self):
        self.assertEqual(intervals(datetime(2023, 3, 20).date())[1][0].minute, 15)
        self.assertEqual(intervals(datetime(2023, 3, 21).date())[1][0].minute, 5)
        self.assertEqual(intervals(datetime(2023, 3, 8).date()), [])

    def test_exit_bar_close_cannot_prove_return_before_stop(self):
        row = {'run': 'MOMENTUM_USDRUBF', 'signal_id': 'synthetic', 'status': 'MODELLED',
               'direction': 'LONG', 'entry_interval_start': '2023-01-03 11:00:00',
               'entry': '101', 'exit_interval_start': '2023-01-03 11:05:00', 'exit_reason': 'STOP'}
        signal = {'range_high_shifted': '100', 'range_low_shifted': '99'}
        index = {datetime(2023, 1, 3, 11): (D(101), D(102), D(101), D(101), D(1)),
                 datetime(2023, 1, 3, 11, 5): (D(101), D(101), D(98), D(99), D(1))}
        r = breakout_diagnostic(row, signal, index)
        self.assertFalse(r['close_crossed_breakout_edge_before_exit'])
        self.assertFalse(r['close_return_observable_before_exit_start'])
        self.assertTrue(r['stop_within_10_minutes'])

    def test_price_return_before_exit_is_separate_from_causal_availability(self):
        row = {'run': 'MOMENTUM_USDRUBF', 'signal_id': 'synthetic', 'status': 'MODELLED',
               'direction': 'LONG', 'entry_interval_start': '2023-01-03 11:00:00',
               'entry': '101', 'exit_interval_start': '2023-01-03 11:05:00', 'exit_reason': 'STOP'}
        signal = {'range_high_shifted': '100', 'range_low_shifted': '99'}
        index = {datetime(2023, 1, 3, 11): (D(101), D(102), D(99), D(100), D(1))}
        r = breakout_diagnostic(row, signal, index)
        self.assertTrue(r['close_crossed_breakout_edge_before_exit'])
        self.assertFalse(r['close_return_observable_before_exit_start'])


if __name__ == '__main__':
    unittest.main()
