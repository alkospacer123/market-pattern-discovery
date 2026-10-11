"""Synthetic, no historical candles: parameter grammar, execution and auditor."""
from copy import deepcopy
from datetime import date,timedelta
from decimal import Decimal as D
import json
from pathlib import Path
import tempfile
import unittest
import subprocess
import sys

from IntradayLab.core.backtester import Backtester
from IntradayLab.core.calendar import MarketRules
from IntradayLab.core.data_loader import validate_bar
from IntradayLab.core.models import Context
from IntradayLab.core.execution import entry_geometry
from IntradayLab.core.reports import csv_write
from IntradayLab.strategies.equal_high_low_m5_optimization_a_v1 import EqualHighLowM5OptimizationA
from .contract import POLICY,grid,bounded_reads
from .aggregation import economics,criteria,select
from . import auditor

FIVE=timedelta(minutes=5)


class OptimizationTests(unittest.TestCase):
    def setUp(self):
        self.policy=json.loads(POLICY.read_text());self.rules=MarketRules(self.policy)
        self.day=date(2023,1,4);self.symbol='USDRUBF'

    def at(self,clock):return self.rules.at(self.day,clock)

    def params(self,t=3,sb=1,tp=3):
        return dict(self.policy['parameters'],touches=t,stop_buffer_ticks=sb,target_net_R=str(tp))

    def rows(self,side=-1,t=3,level=D(101),tick=None):
        tick=tick or self.rules.tick(self.symbol,self.at('10:00'))
        rows={};a=self.at('10:00')
        for i in range(107):
            at=a+i*FIVE
            if not any(x<=at<z for x,z in self.rules.windows(self.day)):continue
            # Unequal highs/lows outside the one intended cluster prevent spurious runs.
            mid=level+side*3*tick
            hi=mid+(10+i)*tick;lo=mid-(10+i)*tick
            if i<t:
                hi=level if side==-1 else level+(10+i)*tick
                lo=level if side==1 else level-(10+i)*tick
            elif i==t:
                hi=mid+tick;lo=mid-tick
            else:
                hi=mid+tick;lo=mid-tick
                if i%2:hi+=tick;lo-=tick
            rows[at]=validate_bar(at,(mid,hi,lo,mid,D(10)),FIVE,tick)
        return dict(sorted(rows.items()))

    def engine(self,p,rows,end=None):
        return Backtester(self.rules,entry_mode='ENTRY_NEXT_OPEN',data_gap_policy='DATA_GAP_SKIP_V2').run(
            EqualHighLowM5OptimizationA(p),self.symbol,rows,start=self.day,end_exclusive=end or self.day+timedelta(days=1))

    def independent_match(self,p,rows,result,end=None):
        raw={at:(b.open,b.high,b.low,b.close,b.volume) for at,b in rows.items()}
        events=auditor.episodes(self.symbol,raw,p,start=self.day,end=end or self.day+timedelta(days=1))
        ss,tt,skips,ex=auditor.replay(self.symbol,raw,events,p)
        for actual,wanted in ((result.signals,ss),(result.trades,tt),(result.data_gap_skips,skips),(result.data_quality_exclusions,ex)):
            keys={k for r in wanted for k in r if k!='unknown_effective_at'}
            auditor.check_rows(actual,wanted,keys,'SYNTHETIC')
        return ss,tt,skips,ex

    def test_full_grid_all_targets_both_sides_buffers_and_touch_counts(self):
        self.assertEqual(len(grid(self.policy)),72)
        for spec in grid(self.policy):
            p={k:v for k,v in spec.items() if k!='configuration_id'}
            for side in (1,-1):
                with self.subTest(config=spec['configuration_id'],side=side):
                    rows=self.rows(side,p['touches']);r=self.engine(p,rows);self.independent_match(p,rows,r)
                    q=(r.trades+r.data_quality_exclusions)[0]
                    self.assertEqual(q['entry_at'],self.at('10:00')+p['touches']*FIVE)
                    self.assertEqual(q['stop'],D(101)-side*p['stop_buffer_ticks']*D('.01'))
                    self.assertEqual(q['risk'],(3+p['stop_buffer_ticks'])*D('.01'))
                    self.assertEqual(q['planned_net_to_net_R'],D(p['target_net_R']))
                    self.assertEqual(q['take']%D('.01'),0)

    def test_maximal_run_one_signal_and_ambiguous_consumption(self):
        for t in range(2,6):
            p=self.params(t);s=EqualHighLowM5OptimizationA(p);s.begin_day(self.symbol,self.day);events=[]
            for i in range(9):
                at=self.at('10:00')+i*FIVE
                b=validate_bar(at,tuple(map(D,('100.5','101','100','100.5','10'))),FIVE,D('.01'))
                events+=s.on_bar(b,Context(self.symbol,at,at+FIVE,(self.at('10:00'),self.at('14:00')),D('.01'),{}))
            self.assertEqual(len(events),2);self.assertTrue(all(e['base_reason']=='AMBIGUOUS_BOTH_SIDES' for e in events))

    def test_close_at_extreme_delays_until_first_qualifying_completed_bar(self):
        p=self.params(4);s=EqualHighLowM5OptimizationA(p);s.begin_day(self.symbol,self.day);events=[]
        for i in range(6):
            at=self.at('10:00')+i*FIVE;c=D(101) if i<4 else D('100.97')
            b=validate_bar(at,(c,D(101),D(100)-i*D('.01'),c,D(10)),FIVE,D('.01'))
            events+=s.on_bar(b,Context(self.symbol,at,at+FIVE,(self.at('10:00'),self.at('14:00')),D('.01'),{}))
        self.assertEqual(len(events),1);self.assertEqual(events[0]['cluster_run_bars'],5)
        self.assertEqual(events[0]['touch_1_start'],self.at('10:05'))

    def test_no_signal_before_complete_or_with_insufficient_touches(self):
        p=self.params(5);s=EqualHighLowM5OptimizationA(p);s.begin_day(self.symbol,self.day)
        for at,b in list(self.rows(t=5).items())[:4]:
            self.assertEqual(s.on_bar(b,Context(self.symbol,at,at+FIVE,(self.at('10:00'),self.at('14:00')),D('.01'),{})),[])
        at=self.at('10:20');b=self.rows(t=5)[at]
        with self.assertRaisesRegex(ValueError,'UNCOMPLETED'):
            s.on_bar(b,Context(self.symbol,at,at+timedelta(minutes=4),(self.at('10:00'),self.at('14:00')),D('.01'),{}))

    def test_entry_future_hlc_cannot_change_signal_or_admission(self):
        p=self.params();rows=self.rows();original=self.engine(p,rows)
        at=self.at('10:15');rows[at]=validate_bar(at,(rows[at].open,D(150),D(90),D(95),D(10)),FIVE,D('.01'))
        altered=self.engine(p,rows)
        for k in ('signal_id','signal_at','stop','entry_open','risk','take'):
            self.assertEqual(original.signals[0][k],altered.signals[0][k])
        self.independent_match(p,rows,altered)

    def test_missing_entry_skip_and_missing_exposure_exclusion(self):
        for delete_at,expected in [('10:15','SKIP'),('10:20','EXCLUDED')]:
            p=self.params();rows=self.rows();del rows[self.at(delete_at)];r=self.engine(p,rows)
            self.independent_match(p,rows,r)
            self.assertEqual(len(r.data_gap_skips),int(expected=='SKIP'))
            self.assertEqual(len(r.data_quality_exclusions),int(expected=='EXCLUDED'))
            if expected=='SKIP':self.assertFalse(r.trades)
            else:
                self.assertTrue(r.data_quality_exclusions[0]['model_filled'])
                self.assertIsNone(r.data_quality_exclusions[0]['exit_price'])
                self.assertNotIn('net_R_c1',r.data_quality_exclusions[0])

    def test_invalid_entry_open_and_invalid_exposure_are_distinct(self):
        for clock in ('10:15','10:20'):
            p=self.params();rows=self.rows();at=self.at(clock);b=rows[at]
            rows[at]=validate_bar(at,(D('100.971'),b.high,b.low,b.close,b.volume),FIVE,D('.01'))
            r=self.engine(p,rows);self.independent_match(p,rows,r)
            self.assertEqual(len(r.data_gap_skips),int(clock=='10:15'))
            self.assertEqual(len(r.data_quality_exclusions),int(clock=='10:20'))

    def test_entry_bar_take_disabled_stop_first_and_gap(self):
        for kind in ('TAKE_ONLY','BOTH','GAP'):
            p=self.params();rows=self.rows();at=self.at('10:15');b=rows[at]
            hi=D('101.10') if kind=='BOTH' else D('100.99');lo=D('100.50')
            rows[at]=validate_bar(at,(b.open,hi,lo,b.close,b.volume),FIVE,D('.01'))
            if kind=='GAP':
                at=self.at('10:20');rows[at]=validate_bar(at,tuple(map(D,('101.10','101.11','101.09','101.10','10'))),FIVE,D('.01'))
            r=self.engine(p,rows);self.independent_match(p,rows,r);q=r.trades[0]
            if kind=='BOTH':self.assertEqual(q['exit_interval_start'],self.at('10:15'));self.assertTrue(q['stop_take_conflict'])
            elif kind=='GAP':self.assertEqual(q['exit_price'],D('101.10'))
            else:self.assertNotEqual(q['exit_interval_start'],self.at('10:15'))

    def test_session_flat_open_and_missing_flat_exclusion(self):
        p=self.params();rows=self.rows()
        shifted={at+timedelta(hours=3,minutes=30):b for at,b in rows.items() if at<self.at('10:25')}
        for at in shifted:
            b=shifted[at];rows[at]=validate_bar(at,(b.open,b.high,b.low,b.close,b.volume),FIVE,D('.01'))
        r=self.engine(p,dict(sorted(rows.items())));self.independent_match(p,dict(sorted(rows.items())),r)
        q=next(t for t in r.trades if t['entry_at']==self.at('13:45'))
        self.assertEqual(q['exit_at'],self.at('13:55'));self.assertEqual(q['exit_reason'],'SESSION_FLAT')
        del rows[self.at('13:55')];rows=dict(sorted(rows.items()));r=self.engine(p,rows);self.independent_match(p,rows,r)
        self.assertTrue(any(t['entry_at']==self.at('13:45') for t in r.data_quality_exclusions))

    def test_cny_historical_grid_all_ratios(self):
        self.symbol='CNYRUBF'
        for day in (date(2023,9,27),date(2023,9,28)):
            self.day=day;tick=self.rules.tick(self.symbol,self.at('10:00'))
            self.assertEqual(tick,D('.01') if day.day==27 else D('.001'))
            for tp in range(2,11):
                for side in (1,-1):
                    p=self.params(4,2,tp);rows=self.rows(side,4,level=D(12),tick=tick)
                    r=self.engine(p,rows);self.independent_match(p,rows,r)
                    self.assertEqual(r.trades[0]['planned_net_to_net_R'],D(tp))
                    self.assertEqual(r.trades[0]['cost_c1'],2*tick)
        transition=self.rules.at(date(2023,9,27),'19:00')
        self.assertEqual(self.rules.tick(self.symbol,transition-FIVE),D('.01'));self.assertEqual(self.rules.tick(self.symbol,transition),D('.001'))

    def test_admission_buffer_risk_geometry_no_relocation(self):
        for sb in (1,2):
            for displacement in (-1,0,1,2,3,4,5,13):
                rows=self.rows();at=self.at('10:15');op=D(101)-displacement*D('.01')
                rows[at]=validate_bar(at,(op,D(102),D(100),op,D(10)),FIVE,D('.01'))
                r=self.engine(self.params(sb=sb),rows);self.independent_match(self.params(sb=sb),rows,r)
                self.assertEqual(r.signals[0]['stop'],D(101)+sb*D('.01'))
                self.assertEqual(r.signals[0]['model_filled'],displacement>=0 and displacement<=4 and displacement+sb>=3)

    def test_round_outward_full_net_formula(self):
        for side in (1,-1):
            risk,take=entry_geometry(D(100),side,D(100)-side*D('.035'),D('.01'),D(2),target_mode='FULL_NET_C1_R')
            self.assertEqual(side*(take-D(100)),D('.13'))
            self.assertGreaterEqual((side*(take-D(100))-D('.02'))/(risk+D('.02')),D(2))

    def test_numeric_sample_and_neighbor_criteria_no_loss_pf(self):
        m=economics([]);self.assertEqual(m['PF_R'],'NOT_AVAILABLE');self.assertFalse(criteria(m,self.policy['selection'])['sample'])
        rows=[]
        for t in (2,3,4):
            rows.append(dict(configuration_id=f'A_OPT2023_T{t}_SB1_TP3',instrument='USDRUBF',touches=t,stop_buffer_ticks=1,target_net_R='3',
                CLOSED=100,entry_days=40,entry_months=6,PF_R=D(2),PF_price=D(2),expectancy_R=D(1),positive_exit_months=9,
                conditional_closed_only_DD_R=D(5),largest_winner_share_R=D('.1'),largest_positive_month_share_R=D('.2')))
            rows[-1].update({f'pass_{k}':v for k,v in criteria(rows[-1],self.policy['selection']).items()})
        _,selection=select(rows,self.policy)
        self.assertEqual(selection['instruments']['USDRUBF']['ranked_ids'],['A_OPT2023_T3_SB1_TP3'])
        self.assertEqual(rows[0]['status'],'DOES_NOT_QUALIFY')

    def test_source_guard_denies_future_bytes_buffered_and_other_paths(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);(root/'allowed.csv').write_bytes(b'a\nb\nfuture\n');(root/'forbidden.csv').write_bytes(b'future')
            cfg=dict(inputs={'USDRUBF':dict(path='allowed.csv',prefix_bytes=4,blob='synthetic')})
            with bounded_reads(root,cfg) as receipts:
                with (root/'allowed.csv').open('rb',buffering=0) as f:
                    self.assertEqual(f.read(4),b'a\nb\n')
                    with self.assertRaisesRegex(ValueError,'FUTURE'):f.read(1)
                with self.assertRaisesRegex(ValueError,'PATH_OR_BUFFERING'):(root/'forbidden.csv').open('rb',buffering=0)
                with self.assertRaisesRegex(ValueError,'PATH_OR_BUFFERING'):(root/'allowed.csv').open('rb')
            self.assertEqual(receipts[0]['bytes_read'],4);self.assertEqual(receipts[0]['candle_rows_read'],1)

    def test_parameters_and_research_dates_are_bounded(self):
        for k,v in [('touches',6),('stop_buffer_ticks',3),('target_net_R','11'),('maximum_rebound_ticks',5),('tolerance_ticks',1)]:
            with self.assertRaisesRegex(ValueError,'UNAPPROVED'):EqualHighLowM5OptimizationA(dict(self.params(),**{k:v}))
        with self.assertRaisesRegex(ValueError,'development'):
            self.engine(self.params(),self.rows(),end=date(2024,1,2))

    def test_skip_recovers_exclusion_blocks_and_next_day_flat_is_conditional(self):
        p=self.params();rows=self.rows()
        for i in range(3):
            at=self.at('10:30')+i*FIVE
            rows[at]=validate_bar(at,(D('101.97'),D(102),D(101)-i*D('.01'),D('101.97'),D(10)),FIVE,D('.01'))
        at=self.at('10:45');rows[at]=validate_bar(at,tuple(map(D,('101.97','101.98','101.96','101.97','10'))),FIVE,D('.01'))
        del rows[self.at('10:15')];rows=dict(sorted(rows.items()));r=self.engine(p,rows)
        self.independent_match(p,rows,r);self.assertTrue(any(s['model_filled'] for s in r.signals if s['signal_at']==self.at('10:45')))
        rows=self.rows();del rows[self.at('10:20')]
        for i in range(3):
            at=self.at('10:30')+i*FIVE
            rows[at]=validate_bar(at,(D('101.97'),D(102),D(101)-i*D('.01'),D('101.97'),D(10)),FIVE,D('.01'))
        following={at+timedelta(days=1):validate_bar(at+timedelta(days=1),(b.open,b.high,b.low,b.close,b.volume),FIVE,D('.01')) for at,b in self.rows().items()}
        rows.update(following);rows=dict(sorted(rows.items()));end=self.day+timedelta(days=2)
        r=self.engine(p,rows,end);self.independent_match(p,rows,r,end)
        self.assertTrue(any(s['reason']=='DATA_QUALITY_POSITION_BLOCK' for s in r.signals))
        self.assertTrue(any(t['prior_exclusion_requires_flat_assumption'] for t in r.trades))
        self.assertTrue(all(not t['initial_flat_proven'] for t in r.trades))

    def test_gap_and_session_reset_no_overlapping_windows(self):
        for t in range(2,6):
            p=self.params(t);rows=self.rows(t=t);del rows[self.at('10:00')+(t-2)*FIVE]
            r=self.engine(p,rows);self.independent_match(p,rows,r)
            self.assertFalse(any(s['base_reason']=='SIGNAL' for s in r.signals))
        self.assertEqual(self.rules.windows(date(2023,3,15))[1][0].strftime('%H:%M'),'14:15')
        self.assertEqual(self.rules.windows(date(2023,3,21))[1][0].strftime('%H:%M'),'14:05')
        self.assertEqual(self.rules.windows(date(2023,3,8)),[])

    def test_auditor_detects_corrupted_economics_and_path(self):
        p=self.params();rows=self.rows();r=self.engine(p,rows);original=deepcopy(r)
        r.trades[0]['net_R_c1']+=D(1)
        with self.assertRaises(AssertionError):self.independent_match(p,rows,r)
        original.signals[0]['stop']+=D('.01')
        with self.assertRaises(AssertionError):self.independent_match(p,rows,original)

    def test_independent_metrics_month_sign_and_no_loss_pf(self):
        for tp in range(2,11):
            p=self.params(tp=tp);rows=self.rows();r=self.engine(p,rows)
            actual=economics(r.trades);expected=auditor.independent_statistics(r.trades)
            for k,v in expected.items():auditor.numeric_equal(actual[k],v,'SYNTHETIC_METRIC '+k)
        q=deepcopy(r.trades[0]);q['net_R_c1']=D(4);q['net_c1']=D('.16');q['gross']=D('.18')
        m=economics([q]);self.assertEqual(m['PF_R'],'NOT_AVAILABLE');self.assertEqual(m['positive_exit_months'],1)
        self.assertFalse(criteria(m,self.policy['selection'])['PF_R'])

    def test_syscall_receipt_parser_on_synthetic_prefixes(self):
        from .validate import trace_receipt
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);specs={}
            for symbol in ('USDRUBF','CNYRUBF'):
                (root/(symbol+'.csv')).write_bytes(b'header\ncandle\nfuture\n')
                specs[symbol]=dict(path=symbol+'.csv',prefix_bytes=14,rows_2023=1,blob='synthetic',prefix_sha256='synthetic')
            trace=root/'trace'
            cmd=['strace','-f','-yy','-s','0','-e','trace=openat,read,pread64,lseek,close']
            for spec in specs.values():cmd+=['-P',str(root/spec['path'])]
            cmd+=['-o',str(trace),sys.executable,'-c',
                'from pathlib import Path; import sys;\nfor path in sys.argv[1:]:\n with Path(path).open("rb",buffering=0) as f:\n  f.tell();f.read(14);f.tell()',*[str(root/s['path']) for s in specs.values()]]
            subprocess.run(cmd,check=True)
            receipt=trace_receipt(trace,dict(inputs=specs,instruments=list(specs)),root)
            self.assertEqual(receipt['status'],'PASS')


if __name__=='__main__':unittest.main()
