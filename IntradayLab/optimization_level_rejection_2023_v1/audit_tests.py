"""Synthetic-only regression and corruption guards for the independent oracle."""
from copy import deepcopy
from decimal import Decimal as D
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from . import auditor as a


class IndependentAuditTests(unittest.TestCase):
    def setUp(self):
        self.policy=json.loads((a.STUDY/'OPTIMIZATION_LEVEL_REJECTION_POLICY.json').read_text())
        self.p=dict(self.policy['parameters'])
        self.day='2023-12-29'
        self.raw={a.stamp(self.day,f'10:{minute:02d}'):tuple(map(D,values)) for minute,values in [
            (0,('100.02','100.06','100.00','100.02','10')),
            (5,('100.02','100.06','100.00','100.02','10')),
            (10,('100.02','100.06','100.00','100.02','10')),
            (15,('100.02','100.06','100.00','100.02','10')),
            (20,('100.02','100.06','100.00','100.02','10')),
            (25,('100.02','100.06','100.00','100.02','10')),
            (30,('100.02','100.05','99.99','100.02','10')),
            (35,('100.02','100.05','100.01','100.03','10')),
            (40,('100.03','100.30','100.02','100.03','10')),
            (45,('100.03','100.30','100.02','100.03','10')),
            (50,('100.03','100.05','100.02','100.03','10'))]}

    def replay(self,raw=None,p=None):
        raw=self.raw if raw is None else raw
        return a.replay('USDRUBF',raw,a.episodes('USDRUBF',raw,self.p if p is None else p))

    def test_full_net_and_entry_take_suppression(self):
        ss,tt,sk,xx=self.replay()
        trade=tt[0]
        self.assertEqual(trade['entry_at'],a.stamp(self.day,'10:40'))
        self.assertEqual(trade['stop'],D('99.98'))
        self.assertEqual(trade['risk'],D('.05'))
        self.assertEqual(trade['take'],D('100.26'))
        self.assertEqual(trade['exit_interval_start'],a.stamp(self.day,'10:45'))
        self.assertEqual(trade['net_R_c1'],D('4.2'))
        self.assertEqual(trade['realized_net_to_net_R'],D(3))
        self.assertEqual(trade['cost_c1'],D('.02'))
        self.assertEqual(sk+xx,[])

    def test_stop_first_and_net_stop_denominator(self):
        raw=deepcopy(self.raw)
        raw[a.stamp(self.day,'10:45')]=tuple(map(D,('100.03','100.30','99.98','100.03','10')))
        trade=self.replay(raw)[1][0]
        self.assertEqual(trade['exit_reason'],'STOP')
        self.assertTrue(trade['stop_take_conflict'])
        self.assertEqual(trade['net_R_c1'],D('-1.4'))
        self.assertEqual(trade['realized_net_to_net_R'],D(-1))

    def test_open_gap_stop(self):
        raw=deepcopy(self.raw)
        raw[a.stamp(self.day,'10:45')]=tuple(map(D,('99.97','100.30','99.97','100.03','10')))
        trade=self.replay(raw)[1][0]
        self.assertEqual(trade['exit_at'],a.stamp(self.day,'10:45'))
        self.assertEqual(trade['exit_price'],D('99.97'))
        self.assertLess(trade['realized_net_to_net_R'],D(-1))

    def test_skip_without_exposure_economics(self):
        raw=deepcopy(self.raw);del raw[a.stamp(self.day,'10:40')]
        ss,tt,sk,xx=self.replay(raw)
        self.assertEqual(len(sk),1)
        self.assertEqual(sk[0]['status'],'DATA_GAP_SKIP')
        self.assertFalse(sk[0]['order_admitted'])
        self.assertEqual(tt+xx,[])

    def test_exclusion_without_fake_closure_or_pnl(self):
        raw=deepcopy(self.raw);del raw[a.stamp(self.day,'10:45')]
        ss,tt,sk,xx=self.replay(raw)
        self.assertEqual(tt+sk,[])
        self.assertEqual(len(xx),1)
        self.assertTrue(xx[0]['model_filled'])
        self.assertEqual(xx[0]['gap_detected_at'],a.stamp(self.day,'10:45'))
        self.assertEqual(xx[0]['status'],'DATA_QUALITY_EXCLUDED')
        self.assertTrue(all(xx[0].get(k) is None for k in ('exit_price','resolved_at','gross','net_c1','net_R_c1')))

    def test_invalid_exposed_bar_observation_time(self):
        raw=deepcopy(self.raw)
        raw[a.stamp(self.day,'10:40')]=tuple(map(D,('100.03','100.30','100.02','100.03','0')))
        xx=self.replay(raw)[3]
        self.assertEqual(xx[0]['gap_interval_start'],a.stamp(self.day,'10:40'))
        self.assertEqual(xx[0]['gap_detected_at'],a.stamp(self.day,'10:45'))
        self.assertEqual(xx[0]['exclusion_reason'],'INVALID_EXPOSED_BAR')

    def test_original_baseline_legacy_known_closure_is_preserved(self):
        events=a.episodes('USDRUBF',self.raw,self.p)
        ss,tt,sk,xx=a.replay('USDRUBF',self.raw,events,legacy=True)
        self.assertEqual(tt[0]['status'],'CLOSED')
        self.assertEqual(tt[0]['net_R_c1'],D('4.2'))
        self.assertIn('prior_unknown_requires_flat_assumption',tt[0])
        self.assertNotIn('prior_exclusion_requires_flat_assumption',tt[0])
        raw=deepcopy(self.raw);del raw[a.stamp(self.day,'10:40')]
        ss,tt,sk,xx=a.replay('USDRUBF',raw,a.episodes('USDRUBF',raw,self.p),legacy=True)
        self.assertEqual(tt[0]['status'],'UNKNOWN')
        self.assertFalse(tt[0]['model_filled'])
        self.assertIsNone(tt[0]['exit_price'])
        self.assertEqual(sk+xx,[])

    def test_close_and_open_parameter_coupling(self):
        raw=deepcopy(self.raw)
        raw[a.stamp(self.day,'10:30')]=tuple(map(D,('100.02','100.05','99.99','100.01','10')))
        baseline=a.episodes('USDRUBF',raw,self.p)
        strict=a.episodes('USDRUBF',raw,dict(self.p,min_close_reentry_ticks=2))
        ident='USDRUBF_2023-12-29_1030_1'
        self.assertTrue(any(s['signal_id']==ident and s['base_reason']=='SIGNAL' for s in baseline))
        self.assertFalse(any(s['signal_id']==ident for s in strict))
        raw=deepcopy(self.raw)
        raw[a.stamp(self.day,'10:40')]=tuple(map(D,('100.01','100.30','100.01','100.03','10')))
        ss,tt,sk,xx=self.replay(raw,dict(self.p,min_close_reentry_ticks=2))
        target=next(s for s in ss if s['signal_id']==ident)
        self.assertEqual(target['reason'],'OPEN_RECLAIM_NOT_PERSISTENT')
        self.assertEqual(target['status'],'NONFILL')

    def test_structural_buffer_changes_extreme_only(self):
        ss,tt,sk,xx=self.replay(p=dict(self.p,stop_beyond_extreme_ticks=2))
        self.assertEqual(tt[0]['stop'],D('99.97'))
        self.assertEqual(tt[0]['take'],D('100.29'))

    def test_ledger_corruptions_are_rejected(self):
        expected=self.replay()[1]
        actual=[{k:json.dumps(v,default=a.encode,sort_keys=True) if isinstance(v,(dict,list)) else '' if v is None else str(v) for k,v in row.items()} for row in expected]
        a.compare_ledger(actual,expected,'GOOD')
        for field,value in [('stop','99.97'),('entry_at','2023-12-29 10:35:00+03:00'),('take','100.25'),
                            ('net_R_c1','999'),('cost_c1','0'),('status','UNKNOWN')]:
            corrupt=deepcopy(actual);corrupt[0][field]=value
            with self.assertRaises(AssertionError):a.compare_ledger(corrupt,expected,'CORRUPTION')
        with self.assertRaises(AssertionError):a.compare_ledger(actual+actual,expected,'DUPLICATE')
        with self.assertRaises(AssertionError):a.compare_ledger([],expected,'OMITTED')

    def test_independent_metrics_precision_and_gates(self):
        first=self.replay()[1][0];loser=dict(first,signal_id='loser',net_R_c1=D('-1.4'),net_c1=D('-.07'))
        m=a.independent_statistics([first,loser])
        self.assertEqual(m['PF_R'],D(3));self.assertEqual(m['PF_price'],D(3))
        self.assertEqual(m['Net_R'],D('2.8'))
        self.assertFalse(a.independent_checks(m)['pass_sample'])
        self.assertFalse(a.independent_checks(m)['pass_months'])
        self.assertFalse(a.independent_checks(m)['pass_trade_concentration'])

    def test_bounded_source_read_with_future_suffix(self):
        prefix=b'Ticker;Datetime;Open;High;Low;Close;Volume\nUSDRUBF;2023-12-29 10:00:00;100.02;100.06;100.00;100.02;10\n'
        with tempfile.TemporaryDirectory(dir=a.ROOT/'IntradayLab/work') as tmp:
            path=Path(tmp)/'source.csv';path.write_bytes(prefix+b'USDRUBF;2024-01-01 10:00:00;1;1;1;1;1\n')
            p=dict(instruments=['USDRUBF'],inputs={'USDRUBF':dict(path='source.csv',rows_2023=1,prefix_bytes=len(prefix),prefix_sha256=hashlib.sha256(prefix).hexdigest(),blob='synthetic')})
            raw,receipts=a.read_source(Path(tmp),p)
            self.assertEqual(len(raw['USDRUBF']),1)
            self.assertEqual(receipts['USDRUBF']['bytes_read'],len(prefix))
            self.assertEqual(receipts['USDRUBF']['bytes_2024_plus_read'],0)

    def test_tick_change_and_calendar_are_historical(self):
        self.assertEqual(a.tick('CNYRUBF',a.stamp('2023-09-27','18:55')),D('.01'))
        self.assertEqual(a.tick('CNYRUBF',a.stamp('2023-09-27','19:00')),D('.001'))
        self.assertEqual(a.windows(a.date(2023,3,13))[1][0].strftime('%H:%M'),'14:15')
        self.assertEqual(a.windows(a.date(2023,5,9)),[])


if __name__=='__main__':
    unittest.main(verbosity=2)
