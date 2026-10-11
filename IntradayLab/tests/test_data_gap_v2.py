"""Prospective policy: explicit scalar prices, causal gaps and old-mode parity."""
from copy import deepcopy
from dataclasses import replace
from datetime import date, timedelta
from decimal import Decimal as D
import json
from pathlib import Path
import tempfile
import unittest

from IntradayLab.core.backtester import Backtester
from IntradayLab.core.data_quality import DATA_GAP_SKIP_V2, LEGACY_UNKNOWN
from IntradayLab.core.execution import ENTRY_NEXT_OPEN, ENTRY_WAIT_ONE_BAR, cost
from IntradayLab.core.reports import write_data_quality_reports
from IntradayLab.strategies.orb_false_break_fade import ORBFalseBreakFade
from IntradayLab.tools.data_gap_v2_examples import LAB, FIVE, SyntheticSignals, fixture, generate


class DataGapTests(unittest.TestCase):
    def setUp(self):
        self.cfg, self.rules, self.rows, self.requests = fixture()
        self.day = date(2023, 1, 4)
        # Each test starts with complete observations.
        for clock in ('10:20','10:50'):
            at = self.at(clock)
            self.rows[at] = replace(self.rows[self.at('10:00')], start=at)
        self.rows = dict(sorted(self.rows.items()))

    def at(self, clock, day=None):
        return self.rules.at(day or self.day, clock)

    def run_engine(self, requests=None, mode=ENTRY_NEXT_OPEN, policy=DATA_GAP_SKIP_V2, strategy=None):
        return Backtester(self.rules, entry_mode=mode, data_gap_policy=policy).run(
            strategy or SyntheticSignals(requests or [self.at('10:20')]),
            'USDRUBF', self.rows, start=self.day, end_exclusive=date(2023, 1, 6))

    def test_missing_entry_skip_never_rolls_forward(self):
        del self.rows[self.at('10:20')]
        r = self.run_engine()
        self.assertEqual(r.trades, [])
        self.assertEqual(r.data_quality_exclusions, [])
        self.assertEqual(r.data_gap_skips[0]['reason'], 'MISSING_EXECUTION_BAR')
        self.assertEqual(r.data_gap_skips[0]['signal_at'], self.at('10:20'))
        self.assertFalse(r.signals[0]['model_filled'])
        self.assertEqual(r.days[0]['accepted_entries'], 0)
        self.assertFalse(r.days[0]['remainder_of_day_blocked'])

    def test_invalid_open_skip(self):
        for value in ('NaN','Infinity','0','-1','100.901'):
            with self.subTest(open=value):
                self.rows[self.at('10:20')] = replace(self.rows[self.at('10:20')], open=D(value))
                r = self.run_engine()
                self.assertEqual(r.data_gap_skips[0]['reason'], 'INVALID_EXECUTION_OPEN')
                self.assertEqual(r.trades, [])

    def test_next_correct_opportunity_executes_after_skip(self):
        del self.rows[self.at('10:20')]
        r = self.run_engine([self.at('10:20'), self.at('10:40')])
        self.assertEqual(len(r.trades), 1)
        self.assertEqual(r.trades[0]['entry_at'], self.at('10:40'))
        self.assertFalse(r.trades[0]['prior_exclusion_requires_flat_assumption'])

    def test_missing_exposure_separate_no_economics(self):
        del self.rows[self.at('10:25')]
        r = self.run_engine()
        self.assertEqual(r.trades, [])
        q = r.data_quality_exclusions[0]
        self.assertEqual(q['entry_at'], self.at('10:20'))
        self.assertEqual((q['entry_price'], q['stop'], q['take']), (D('100.90'),D('101.02'),D('100.72')))
        self.assertEqual(q['gap_detected_at'], self.at('10:25'))
        self.assertEqual(q['gap_interval_start'], self.at('10:25'))
        self.assertIsNone(q['exit_price'])
        self.assertIsNone(q['resolved_at'])
        self.assertNotIn('net_c1', q)
        self.assertNotIn('cost_c1', q)
        self.assertEqual(q['cost_entry_c1'], D('.01'))

    def test_same_day_block_next_independent_day_conditional_flat(self):
        del self.rows[self.at('10:25')]
        r = self.run_engine([self.at('10:20'),self.at('11:10'),self.at('10:20',date(2023,1,5))])
        self.assertEqual(r.signals[1]['reason'], 'DATA_QUALITY_POSITION_BLOCK')
        self.assertFalse(r.signals[1]['model_filled'])
        self.assertEqual(len(r.data_quality_exclusions), 1)
        self.assertEqual(len(r.trades), 1)
        self.assertTrue(r.trades[0]['prior_exclusion_requires_flat_assumption'])
        self.assertTrue(r.days[1]['initial_flat_assumed'])
        self.assertFalse(r.days[1]['initial_flat_proven'])

    def test_current_hlc_not_used_for_entry_later_invalid_exposure(self):
        at = self.at('10:20')
        self.rows[at] = replace(self.rows[at], high=D('99'), problem='OHLC_GEOMETRY_OR_VOLUME')
        r = self.run_engine()
        self.assertTrue(r.signals[0]['model_filled'])
        q = r.data_quality_exclusions[0]
        self.assertEqual(q['exclusion_reason'], 'INVALID_EXPOSED_BAR')
        self.assertEqual(q['gap_detected_at'], self.at('10:25'))
        self.assertEqual(q['gap_interval_start'], at)

    def test_closed_before_missing_slot_stays_closed_stop_first(self):
        at = self.at('10:20')
        self.rows[at] = replace(self.rows[at], high=D('101.10'),low=D('100.50'))
        del self.rows[self.at('10:25')]
        r = self.run_engine()
        self.assertEqual(len(r.data_quality_exclusions), 0)
        q = r.trades[0]
        self.assertEqual((q['exit_reason'],q['exit_price'],q['net_c1']), ('STOP',D('101.02'),D('-.14')))
        self.assertTrue(q['stop_take_conflict'])

    def test_stop_gap_real_open_and_c1(self):
        at = self.at('10:25')
        self.rows[at] = replace(self.rows[at],open=D('101.10'),high=D('101.20'),low=D('101.05'),close=D('101.10'))
        q = self.run_engine().trades[0]
        self.assertEqual((q['exit_price'],q['exit_at'],q['net_c1']), (D('101.10'),at,D('-.22')))
        self.assertEqual(q['cost_c1'],D('.02'))
        self.assertEqual(cost(D('.01'),D('.001'),1),D('.011'))
        self.assertEqual(self.rules.tick('CNYRUBF',self.at('18:55',date(2023,9,27))),D('.01'))
        self.assertEqual(self.rules.tick('CNYRUBF',self.at('19:00',date(2023,9,27))),D('.001'))

    def test_entry_take_prohibited_and_session_flat_uses_exact_open(self):
        at = self.at('10:20')
        self.rows[at] = replace(self.rows[at],low=D('100.50'))
        q = self.run_engine().trades[0]
        self.assertEqual(q['exit_reason'],'TIME')
        r = self.run_engine([self.at('13:45'), self.at('13:55')])
        self.assertEqual(r.trades[0]['exit_at'],self.at('13:55'))
        self.assertEqual(r.trades[0]['exit_reason'],'SESSION_FLAT')
        self.assertEqual(r.signals[1]['reason'],'SESSION_LIMIT')

    def test_missing_flat_open_excluded_never_uses_next_price(self):
        del self.rows[self.at('13:55')]
        r = self.run_engine([self.at('13:45')])
        self.assertEqual(r.trades, [])
        self.assertEqual(r.data_quality_exclusions[0]['gap_interval_start'], self.at('13:55'))
        self.assertIsNone(r.data_quality_exclusions[0]['exit_price'])

    def test_waiting_clock_kept_and_missing_waiting_bar_resets(self):
        r = self.run_engine(mode=ENTRY_WAIT_ONE_BAR)
        self.assertEqual(r.trades[0]['entry_at'],self.at('10:25'))
        del self.rows[self.at('10:20')]
        r = self.run_engine(mode=ENTRY_WAIT_ONE_BAR)
        self.assertEqual(r.signals[0]['reason'],'NO_WAITING_BAR')
        self.assertEqual(r.data_gap_skips, [])

    def test_orb_missing_construction_keeps_previous_reset_no_synthetics(self):
        cfg = json.loads((LAB/'config/orb_a_base_2023_canonical_v1.json').read_text())
        del self.rows[self.at('10:05')]
        original = dict(self.rows)
        r = self.run_engine(strategy=ORBFalseBreakFade(cfg['parameters']))
        self.assertEqual([t for t in r.trades if t['signal_at'].date()==self.day], [])
        self.assertEqual(self.rows, original)
        self.assertTrue(any(s['reason']=='NO_OR' for s in r.signals))

    def test_legacy_default_is_exact_with_unknown_and_wait(self):
        del self.rows[self.at('10:25')]
        implicit = Backtester(self.rules).run(SyntheticSignals([self.at('10:20')]),'USDRUBF',self.rows,
            start=self.day,end_exclusive=date(2023,1,6))
        self.assertEqual(implicit,self.run_engine(mode=ENTRY_WAIT_ONE_BAR,policy=LEGACY_UNKNOWN))
        self.assertEqual(implicit[1][0]['status'],'UNKNOWN')

    def test_duplicate_signals_fail_before_reports(self):
        r = self.run_engine()
        r.signals.append(dict(r.signals[0]))
        with self.assertRaisesRegex(ValueError,'DUPLICATE'):
            r.validate()

    def test_counts_and_report_statuses_empty_schemas_no_overwrite(self):
        with tempfile.TemporaryDirectory(dir=LAB/'work') as tmp:
            out = Path(tmp)/'example'
            r = generate(out)
            m = json.loads((out/'metrics.json').read_text())
            self.assertEqual(m['totals_counts_only'],dict(accepted_entries=3,closed=2,
                data_gap_skips=1,data_quality_excluded=1,exclusion_fraction=str(D(1)/3)))
            self.assertIsNone(m['annual_economics'])
            for name in ('trades','signals','data_gap_skips','data_quality_exclusions','coverage_report'):
                self.assertNotIn('UNKNOWN',(out/(name+'.csv')).read_text())
            with self.assertRaisesRegex(ValueError,'IMMUTABLE'):
                write_data_quality_reports(out,r,{'USDRUBF':self.rows},self.cfg,self.rules)
            empty = self.run_engine([self.at('09:00')])
            write_data_quality_reports(Path(tmp)/'empty',empty,{'USDRUBF':self.rows},self.cfg,self.rules)
            self.assertIn('signal_id',(Path(tmp)/'empty/trades.csv').read_text())

    def test_future_guard_and_invalid_policy(self):
        for kwargs in (dict(data_gap_policy='AUTO'),dict(data_gap_policy=DATA_GAP_SKIP_V2,timeframe_minutes=15),
                       dict(data_gap_policy=DATA_GAP_SKIP_V2,allow_entry_bar_take=True)):
            with self.assertRaises(ValueError):Backtester(self.rules,**kwargs)
        with self.assertRaises(ValueError):
            Backtester(self.rules,data_gap_policy=DATA_GAP_SKIP_V2).run(SyntheticSignals([]),
                'USDRUBF',self.rows,start=self.day,end_exclusive=date(2024,1,2))

    def test_independent_audit_detects_corrupt_arithmetic_and_missing_records(self):
        from IntradayLab.tools.audit_data_gap_v2 import audit
        with tempfile.TemporaryDirectory(dir=LAB/'work') as tmp:
            out = Path(tmp)/'example'
            generate(out)
            self.assertEqual(audit(out)['status'],'PASS')
            path = out/'metrics.json'
            before = path.read_text()
            value = json.loads(before)
            value['instruments']['USDRUBF']['conditional_closed_only_C1']['PF_C1_R']='999'
            path.write_text(json.dumps(value))
            with self.assertRaisesRegex(AssertionError,'PF'):audit(out)
            path.write_text(before)
            ledger = out/'data_quality_exclusions.csv'
            raw = ledger.read_text()
            ledger.write_text(raw.splitlines()[0]+'\n')
            with self.assertRaisesRegex(AssertionError,'ROW_SET'):audit(out)
            ledger.write_text(raw)
            cov = out/'coverage_report.csv'
            import csv
            with cov.open(newline='') as stream:
                reader = csv.DictReader(stream);columns=reader.fieldnames;records=list(reader)
            records[0]['missing_bars']='0'
            with cov.open('w',newline='') as stream:
                writer=csv.DictWriter(stream,fieldnames=columns);writer.writeheader();writer.writerows(records)
            with self.assertRaisesRegex(AssertionError,'COVERAGE'):audit(out)


if __name__ == '__main__':
    unittest.main()
