"""Synthetic fail-closed completeness acceptance tests; no market-data reads."""
import sys
import unittest
from pathlib import Path
from datetime import datetime, timedelta

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from m5_baseline import next_slot
from stage2_research_completeness_gate import assess, EXPECTED, MONTHS, VERDICT


def sample():
    runs = []
    signals = []
    for name in sorted(EXPECTED):
        runs.append({
            'run': name, 'signals': 2,
            'signal_status_counts': {'MODELLED': 1, 'BLOCKED': 1},
            'summary': {'unknown_entry_orders': 1, 'unresolved': 0,
                        'total_unresolved_cases': 1,
                        'closed_accounted_trades': 1, 'closed_only_gross': '1.5',
                        'closed_only_c1': '0.5', 'closed_only_net_c1': '1.0',
                        'PF': '2.0', 'full_PF': None, 'net_model_c1': None},
            'coverage': {m: {'coverage_status': 'COVERED', 'expected_research_slots': 10,
                             'missing_slots': 0} for m in MONTHS},
        })
        signals.extend([{'run': name, 'signal_at': '2023-01-03 10:00:00', 'status': 'MODELLED'},
                        {'run': name, 'signal_at': '2023-02-03 10:00:00', 'status': 'BLOCKED'}])
    return ({'manifest_sha256': 'abc', 'runs': runs},
            {'manifest_sha256': 'abc', 'matrix_runs': 8, 'signals': 16,
             'blocked_signals': 8, 'unknown_entry_orders': 8,
             'total_unresolved_cases': 8}, signals)


def sample_metrics():
    rows = []
    for run in sorted(EXPECTED):
        rows.append({'run': run, 'group': 'YEAR', 'period': '2023',
                     'closed_accounted_trades': '1', 'full_PF': '', 'net_model_c1': ''})
        for direction in ('LONG', 'SHORT'):
            rows.append({'run': run, 'group': 'DIRECTION', 'period': direction,
                         'closed_accounted_trades': '0', 'full_PF': '', 'net_model_c1': ''})
        for month in MONTHS:
            rows.append({'run': run, 'group': 'MONTH', 'period': month,
                         'coverage_status': 'COVERED',
                         'closed_accounted_trades': '0', 'full_PF': '', 'net_model_c1': ''})
    return rows


class GateTests(unittest.TestCase):
    def test_incomplete_never_passes_on_profitable_closed_only(self):
        result, verify, signals = sample()
        out = assess(result, verify, signals, 'abc')
        self.assertEqual(VERDICT, out['verdict'])
        self.assertEqual('50.00', out['blocked_percent'])
        self.assertEqual(96, len(out['run_months']))
        self.assertEqual('UNRESOLVED_OR_UNPROVEN', out['run_months'][0]['research_PnL_status'])

    def test_falsely_present_full_pf_fails(self):
        result, verify, signals = sample()
        result['runs'][0]['summary']['full_PF'] = '1.5'
        with self.assertRaisesRegex(ValueError, 'UNPROVEN_ANNUAL'):
            assess(result, verify, signals, 'abc')

    def test_signal_mismatch_fails(self):
        result, verify, signals = sample()
        with self.assertRaisesRegex(ValueError, 'SIGNAL_LEDGER'):
            assess(result, verify, signals[:-1], 'abc')

    def test_c1_accounting_fails(self):
        result, verify, signals = sample()
        result['runs'][0]['summary']['closed_only_net_c1'] = '2.0'
        with self.assertRaisesRegex(ValueError, 'C1_ACCOUNTING'):
            assess(result, verify, signals, 'abc')

    def test_manifest_change_fails(self):
        result, verify, signals = sample()
        with self.assertRaisesRegex(ValueError, 'MANIFEST_HASH'):
            assess(result, verify, signals, 'tampered')


    def test_frozen_boundary_timing_is_late(self):
        """At B-20, next M5 open B-15 confirms only B-5, later than B-10."""
        for b in ('2023-02-02 14:00:00', '2023-02-02 18:50:00'):
            B = datetime.fromisoformat(b)
            current_request = B - timedelta(minutes=20)
            exit_start = next_slot(current_request)
            acknowledge = exit_start + timedelta(minutes=10)
            self.assertEqual(exit_start, B - timedelta(minutes=15))
            self.assertEqual(acknowledge, B - timedelta(minutes=5))
            self.assertGreater(acknowledge, B - timedelta(minutes=10))

    def test_proposed_earlier_close_is_only_conditionally_feasible(self):
        """Proposed B-30 lead supports a last permitted B-35 entry ack at B-25."""
        for b in ('2023-02-02 14:00:00', '2023-02-02 18:50:00'):
            B = datetime.fromisoformat(b)
            last_entry_start = B - timedelta(minutes=35)
            last_entry_ack = last_entry_start + timedelta(minutes=10)
            self.assertEqual(last_entry_ack, B - timedelta(minutes=25))
            earliest_late_close_start = next_slot(last_entry_ack)
            self.assertEqual(earliest_late_close_start, B - timedelta(minutes=20))
            self.assertEqual(earliest_late_close_start + timedelta(minutes=10),
                             B - timedelta(minutes=10))
            earlier_close = next_slot(B - timedelta(minutes=30))
            self.assertEqual(earlier_close + timedelta(minutes=10),
                             B - timedelta(minutes=15))

    def test_metrics_120_rows_verify_without_fake_profit(self):
        result, verify, signals = sample()
        out = assess(result, verify, signals, 'abc', sample_metrics())
        self.assertEqual(VERDICT, out['verdict'])

    def test_false_monthly_pf_in_metrics_rejected(self):
        result, verify, signals = sample()
        metrics = sample_metrics()
        month = next(m for m in metrics if m['group'] == 'MONTH')
        month['full_PF'] = '1.7'
        with self.assertRaisesRegex(ValueError, 'UNPROVEN_CSV_MONTHLY'):
            assess(result, verify, signals, 'abc', metrics)

    def test_missing_monthly_metric_rejected(self):
        result, verify, signals = sample()
        metrics = sample_metrics()[:-1]
        with self.assertRaisesRegex(ValueError, 'INVALID_METRIC_GROUP_COUNTS'):
            assess(result, verify, signals, 'abc', metrics)



if __name__ == '__main__':
    unittest.main()
