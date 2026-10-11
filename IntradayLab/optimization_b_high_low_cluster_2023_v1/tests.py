"""Independent synthetic B episodes, causal execution, grid, selection and guards.

No historical candles are read. Full pipeline fixture patches source reading only;
production Backtester/reporting and independent auditor execute all 585 pairs.
"""
from copy import deepcopy
from datetime import date,timedelta
from decimal import Decimal as D
import csv,json
from pathlib import Path
import tempfile,unittest,subprocess,sys
from unittest.mock import patch
from IntradayLab.core.backtester import Backtester
from IntradayLab.core.calendar import MarketRules
from IntradayLab.core.data_loader import validate_bar
from IntradayLab.core.models import Context
from IntradayLab.core.execution import entry_geometry,cost
from IntradayLab.strategies.high_low_cluster_m5_optimization_b_v1 import HighLowClusterM5OptimizationB,parameters,configuration_id
from .contract import POLICY,STUDY,ROOT,grid,bounded_reads,eligible
from .aggregation import economics,criteria,select
from .runner import enrich
from . import auditor
FIVE=timedelta(minutes=5)

class OptimizationBTests(unittest.TestCase):
    def setUp(self):
        self.policy=json.loads(POLICY.read_text());self.rules=MarketRules(self.policy)
        self.day=date(2023,1,4);self.symbol='USDRUBF'
    def at(self,clock):return self.rules.at(self.day,clock)
    def spec(self,p):return dict(p,configuration_id=configuration_id(p))
    def bar(self,at,o,h,l,c=None,tick=None,v=10):
        return validate_bar(at,tuple(map(D,(o,h,l,c if c is not None else o,v))),FIVE,tick or self.rules.tick(self.symbol,at))
    def rows(self,p=None,side=-1,level=D(101)):
        p=p or parameters();n=p['cluster_bars'];step=self.rules.tick(self.symbol,self.at('10:00'));rows={}
        for a,z in self.rules.windows(self.day):
            at=a
            while at<z:
                i=int((at-self.at('10:00'))/FIVE);mid=level+side*3*step
                hi=mid+(10+i)*step;lo=mid-(10+i)*step
                if 0<=i<n:
                    # Exactly three boundary touches; nonzero width within both grids.
                    extreme=level if i in (0,1,n-1) else level+side*step
                    hi=extreme if side==-1 else level+(20+i)*step
                    lo=extreme if side==1 else level-(20+i)*step
                elif i==n:hi=mid+step;lo=mid-step
                rows[at]=self.bar(at,mid,hi,lo,tick=step);at+=FIVE
        return dict(sorted(rows.items()))
    def engine(self,p,rows,end=None):
        st=HighLowClusterM5OptimizationB(p)
        result=Backtester(self.rules,entry_mode='ENTRY_NEXT_OPEN',data_gap_policy='DATA_GAP_SKIP_V2').run(st,self.symbol,rows,start=self.day,end_exclusive=end or self.day+timedelta(days=1))
        enrich(result);return result,st
    def match(self,p,rows,result,st,end=None):
        raw={at:(b.open,b.high,b.low,b.close,b.volume) for at,b in rows.items()}
        events,ledger=auditor.episodes(self.symbol,raw,self.spec(p),self.day,end or self.day+timedelta(days=1),True)
        ss,tt,sk,ex=auditor.replay(self.symbol,raw,events,p);auditor.enrich_expected(ss,tt+ex)
        for actual,expected in ((result.signals,ss),(result.trades,tt),(result.data_gap_skips,sk),(result.data_quality_exclusions,ex)):
            keys={k for r in expected for k in r if k!='unknown_effective_at'}
            auditor.check_rows(actual,expected,keys,'SYNTHETIC')
        aa={r['episode_id']:r for r in st.episode_records};bb={r['episode_id']:r for r in ledger}
        self.assertEqual(set(aa),set(bb))
        for eid,e in bb.items():
            for k,v in e.items():auditor.assert_value(aa[eid][k],v,'SYNTHETIC_EPISODE')
    def feed(self,values,p=None,side=-1,closes=None,gaps=(),tick_change=None,session_change=None):
        p=p or parameters();st=HighLowClusterM5OptimizationB(p);st.begin_day(self.symbol,self.day);events=[]
        for i,value in enumerate(values):
            at=self.at('10:00')+i*FIVE;ext=D(str(value));close=D(str(closes[i])) if closes else ext+side*D('.03')
            hi=ext if side==-1 else D(102)+i*D('.02');lo=ext if side==1 else D(99)-i*D('.02')
            b=None if i in gaps else self.bar(at,close,hi,lo,close)
            step=D('.001') if i==tick_change else D('.01')
            win=(at,self.at('14:00')) if i==session_change else (self.at('10:00'),self.at('14:00'))
            events+=st.on_bar(b,Context(self.symbol,at,at+FIVE,win,step,{}))
        st.end_day();return events,st
    def test_01_exact_315_grid_585_matrix_and_both_directions(self):
        specs=grid(self.policy);self.assertEqual(len(specs),315)
        self.assertEqual(sum(eligible(s,'USDRUBF') for s in specs),270)
        self.assertEqual(sum(eligible(s,'CNYRUBF') for s in specs),315)
        for spec in specs:
            p={k:v for k,v in spec.items() if k!='configuration_id'}
            for side in (1,-1):
                with self.subTest(id=spec['configuration_id'],side=side):
                    rows=self.rows(p,side);r,st=self.engine(p,rows);self.match(p,rows,r,st)
                    q=(r.trades+r.data_quality_exclusions)[0]
                    self.assertEqual(q['entry_at'],self.at('10:00')+p['cluster_bars']*FIVE)
                    self.assertEqual(q['stop'],D(101)-side*p['stop_buffer_ticks']*D('.01'))
                    self.assertEqual(q['planned_net_to_net_R'],D(p['target_net_R']))
                    self.assertEqual(q['risk'],(3+p['stop_buffer_ticks'])*D('.01'))
    def test_02_width_applies_to_entire_envelope_not_only_tail(self):
        # Last four at 99.98/99.99 are narrow; the old 100.01 prefix prevents recycling under W2.
        values=['100.01','100','99.99','99.99','99.98','99.99','99.98','99.99']
        for width in (2,3):
            p=parameters(width=width);events,st=self.feed(values,p)
            self.assertTrue(events)
            self.assertEqual(events[0]['episode_start'],self.at('10:20') if width==2 else self.at('10:00'))
            self.assertTrue(all(e['envelope_max']-e['envelope_min']<=width*D('.01') for e in st.episode_records))
    def test_03_touch_threshold_first_construction(self):
        values=[100,'99.99',100,'99.99',100,'99.99']
        for t,clock in ((2,'10:20'),(3,'10:25')):
            ev,_=self.feed(values,parameters(touches=t))
            # The N4 rolling windows never contain three exact boundary touches here.
            if t==2:self.assertEqual(ev[0]['signal_at'],self.at(clock))
            else:self.assertFalse(ev)
    def test_04_zero_width_is_family_a(self):self.assertFalse(self.feed([100]*20)[0])
    def test_05_width_limit_and_reset_current_bar(self):
        for w in (2,3):
            ev,st=self.feed([100,100-D(w)*D('.01')]*3+[D(100)+D('.04'),D(100)+D('.03')]*3,parameters(width=w))
            self.assertEqual(len(ev),2);self.assertEqual(ev[1]['episode_start'],self.at('10:30'))
            self.assertEqual(st.episode_records[0]['reset_reason'],f'ENVELOPE_ABOVE_{w}_TICKS')
    def test_06_boundary_consumes_even_later_close_valid(self):
        ev,_=self.feed([100,'99.99',100,100,100,'99.99',100,'99.99'],closes=['99.97']*3+[100]+['99.97']*4)
        self.assertEqual(len(ev),1);self.assertEqual(ev[0]['base_reason'],'CLOSE_AT_BOUNDARY')
    def test_07_ambiguous_both_sides_consumed(self):
        st=HighLowClusterM5OptimizationB(parameters());st.begin_day(self.symbol,self.day);ev=[]
        for i in range(12):
            at=self.at('10:00')+i*FIVE;b=self.bar(at,'100.5',101-D(i%2)*D('.01'),100+D(i%2)*D('.01'))
            ev+=st.on_bar(b,Context(self.symbol,at,at+FIVE,(self.at('10:00'),self.at('14:00')),D('.01'),{}))
        self.assertEqual(len(ev),2);self.assertTrue(all(e['base_reason']=='AMBIGUOUS_BOTH_SIDES' for e in ev))
    def test_08_consumption_no_overlapping_retry(self):self.assertEqual(len(self.feed([100,'99.99']*30)[0]),1)
    def test_09_missing_invalid_session_tick_and_day_reset(self):
        for kw in ({'gaps':(2,)},{'tick_change':2},{'session_change':2}):self.assertFalse(self.feed([100,'99.99',100,'99.99'],**kw)[0])
        ev,st=self.feed([100,'99.99',100]);st.begin_day(self.symbol,self.day+timedelta(days=1));self.assertEqual(st.runs,{})
        p=parameters();rows=self.rows(p);b=rows[self.at('10:10')];rows[b.start]=self.bar(b.start,b.open,b.high,b.low,v=0)
        r,st=self.engine(p,rows);self.match(p,rows,r,st);self.assertFalse(r.signals)
    def test_10_uncompleted_misaligned_and_offgrid_refused(self):
        p=parameters();st=HighLowClusterM5OptimizationB(p);st.begin_day(self.symbol,self.day);at=self.at('10:00');b=self.rows()[at]
        with self.assertRaisesRegex(ValueError,'UNCOMPLETED'):st.on_bar(b,Context(self.symbol,at,at+timedelta(minutes=4),(at,self.at('14:00')),D('.01'),{}))
        with self.assertRaisesRegex(ValueError,'OFF_HISTORICAL'):st.on_bar(b,Context(self.symbol,at,at+FIVE,(at,self.at('14:00')),D('.03'),{}))
    def test_11_future_hlc_does_not_change_signal_or_admission(self):
        p=parameters();rows=self.rows(p);before,_=self.engine(p,rows);at=self.at('10:20')
        rows[at]=self.bar(at,rows[at].open,150,50,100);after,st=self.engine(p,rows);self.match(p,rows,after,st)
        for k in ('signal_id','signal_at','cluster_level','entry_open','stop','risk','take'):self.assertEqual(before.signals[0][k],after.signals[0][k])
    def test_12_prefix_invariance_no_future_episode_information(self):
        p=parameters();rows=self.rows(p);r,st=self.engine(p,rows);raw={at:(b.open,b.high,b.low,b.close,b.volume) for at,b in rows.items()}
        a=auditor.episodes(self.symbol,raw,self.spec(p),self.day,self.day+timedelta(days=1))
        raw={at:v for at,v in raw.items() if at<=self.at('10:15')};b=auditor.episodes(self.symbol,raw,self.spec(p),self.day,self.day+timedelta(days=1))
        self.assertEqual(a[0],b[0])
    def test_13_missing_entry_is_skip_missing_exposure_is_excluded(self):
        for clock,kind in [('10:20','SKIP'),('10:25','EXCLUDED')]:
            p=parameters();rows=self.rows(p);del rows[self.at(clock)];r,st=self.engine(p,rows);self.match(p,rows,r,st)
            self.assertEqual(len(r.data_gap_skips),kind=='SKIP');self.assertEqual(len(r.data_quality_exclusions),kind=='EXCLUDED')
            if kind=='EXCLUDED':self.assertNotIn('net_R_c1',r.data_quality_exclusions[0]);self.assertIsNone(r.data_quality_exclusions[0]['exit_price'])
    def test_14_invalid_entry_open_and_exposure_distinct(self):
        for clock in ('10:20','10:25'):
            p=parameters();rows=self.rows(p);at=self.at(clock);b=rows[at];rows[at]=self.bar(at,'100.971',b.high,b.low,b.close)
            r,st=self.engine(p,rows);self.match(p,rows,r,st)
            self.assertEqual(bool(r.data_gap_skips),clock=='10:20');self.assertEqual(bool(r.data_quality_exclusions),clock=='10:25')
    def test_15_entry_take_disabled_stop_first_gap(self):
        for side in (1,-1):
            for kind in ('TAKE_ONLY','BOTH','GAP'):
                p=parameters();rows=self.rows(p,side);at=self.at('10:20');b=rows[at]
                hi=D(102) if side==1 or kind=='BOTH' else D('100.99');lo=D(100) if side==-1 or kind=='BOTH' else D('101.01')
                rows[at]=self.bar(at,b.open,hi,lo,b.close)
                if kind=='GAP':
                    at=self.at('10:25');op=D(101)-side*D('.10');rows[at]=self.bar(at,op,op+D('.01'),op-D('.01'))
                r,st=self.engine(p,rows);self.match(p,rows,r,st);q=r.trades[0]
                if kind=='BOTH':self.assertEqual(q['exit_interval_start'],self.at('10:20'));self.assertEqual(q['exit_reason'],'STOP');self.assertTrue(q['stop_take_conflict'])
                elif kind=='GAP':self.assertEqual(q['exit_price'],op)
                else:self.assertNotEqual(q['exit_interval_start'],self.at('10:20'))
    def test_16_real_open_buffer_constraints_never_move_stop(self):
        for sb in (1,2):
            for d in (-1,0,1,2,3,4,5,13):
                p=parameters(buffer=sb);rows=self.rows(p);at=self.at('10:20');op=D(101)-d*D('.01');rows[at]=self.bar(at,op,102,100)
                r,st=self.engine(p,rows);self.match(p,rows,r,st);s=r.signals[0]
                self.assertEqual(s['stop'],D(101)+sb*D('.01'));self.assertEqual(s['model_filled'],0<=d<=4 and d+sb>=3)
    def test_17_cny_tick_change_both_sides_buffers_targets(self):
        self.symbol='CNYRUBF'
        for day in (date(2023,9,27),date(2023,9,28)):
            self.day=day;step=self.rules.tick(self.symbol,self.at('10:00'))
            self.assertEqual(step,D('.01') if day.day==27 else D('.001'))
            for sb in (1,2):
                for take in range(2,11):
                    for side in (1,-1):
                        p=parameters(buffer=sb,take=take);rows=self.rows(p,side,level=D(12));r,st=self.engine(p,rows);self.match(p,rows,r,st)
                        self.assertEqual(r.trades[0]['cost_c1'],2*step);self.assertEqual(r.trades[0]['planned_net_to_net_R'],D(take))
        a=self.rules.at(date(2023,9,27),'18:55');z=a+FIVE
        self.assertEqual(cost(self.rules.tick(self.symbol,a),self.rules.tick(self.symbol,z),1),D('.011'))
    def test_18_full_net_outward_rounding(self):
        for side in (1,-1):
            risk,take=entry_geometry(D(100),side,D(100)-side*D('.035'),D('.01'),D(2),target_mode='FULL_NET_C1_R')
            self.assertEqual(side*(take-D(100)),D('.13'))
            self.assertGreaterEqual((side*(take-D(100))-D('.02'))/(risk+D('.02')),2)
    def test_19_hold_time_and_missing_deadline(self):
        p=parameters();rows=self.rows(p);mid=D('100.97')
        for at in list(rows):
            if at>=self.at('10:20'):rows[at]=self.bar(at,mid,mid+D('.01'),mid-D('.01'))
        r,st=self.engine(p,rows);self.match(p,rows,r,st);q=r.trades[0]
        self.assertEqual(q['exit_at'],self.at('12:20'));self.assertEqual(q['exit_reason'],'TIME')
        del rows[self.at('12:20')];r,st=self.engine(p,rows);self.match(p,rows,r,st);self.assertTrue(r.data_quality_exclusions)
    def test_20_round_near_and_ordinary_far_are_diagnostics(self):
        for level,kind in ((D(100),'ROUND_NEAR'),(D('100.04'),'ORDINARY_FAR')):
            ev,_=self.feed([level,level-D('.01')]*2);self.assertEqual(ev[0]['level_type'],kind)
    def test_21_corruption_detected_exactly(self):
        p=parameters();rows=self.rows(p);r,st=self.engine(p,rows)
        for obj,key in ((r.signals[0],'cluster_width_ticks'),(r.trades[0],'net_R_c1'),(r.trades[0],'stop')):
            old=obj[key];obj[key]+=D('1e-25')
            with self.assertRaises(AssertionError):self.match(p,rows,r,st)
            obj[key]=old
    def test_22_parameter_grammar_dates_locked(self):
        for key,value in [('cluster_bars',3),('maximum_width_ticks',4),('minimum_boundary_touches',4),('target_net_R','11'),('tolerance_ticks',1),('minimum_width_ticks',0),('maximum_rebound_ticks',5)]:
            with self.assertRaises(ValueError):HighLowClusterM5OptimizationB(dict(parameters(),**{key:value}))
        with self.assertRaises(ValueError):parameters(width=2,buffer=2)
        with self.assertRaisesRegex(ValueError,'development'):self.engine(parameters(),self.rows(),date(2024,1,2))
    def test_23_neighbors_are_actual_instrument_pairs(self):
        rows=[]
        for n in (8,9,10):
            p=parameters(n=n);r=dict(self.spec(p),instrument='USDRUBF',CLOSED=100,entry_days=40,entry_months=6,PF_R=D(2),PF_price=D(2),expectancy_R=D(1),positive_exit_months=9,conditional_closed_only_DD_R=D(5),largest_winner_share_R=D('.1'),largest_positive_month_share_R=D('.2'))
            if n<10:rows.append(r)
        for r in rows:r.update({f'pass_{k}':v for k,v in criteria(r,self.policy['selection']).items()})
        edges,selection=select(rows,self.policy);self.assertTrue(all(r['positive_neighbor_count']==1 for r in rows));self.assertFalse(selection['instruments']['USDRUBF']['ranked_ids'])
        self.assertTrue(all('N10_' not in e['neighbor_id'] for e in edges))
    def test_24_no_loss_pf_unavailable_and_exact_metric_arithmetic(self):
        self.assertEqual(economics([])['PF_R'],'NOT_AVAILABLE')
        p=parameters();r,st=self.engine(p,self.rows(p));a=economics(r.trades);b=auditor.independent_statistics(r.trades)
        for k,v in b.items():auditor.numeric_equal(a[k],v,k)
        with self.assertRaises(AssertionError):auditor.numeric_equal(D(1),D(1)+D('1e-25'),'NO_TOLERANCE')
    def test_25_source_read_guard_future_buffering_paths(self):
        with tempfile.TemporaryDirectory(dir=ROOT/'IntradayLab/work') as d:
            root=Path(d);(root/'allowed.csv').write_bytes(b'a\nb\nfuture\n');(root/'other.csv').write_bytes(b'future')
            cfg=dict(inputs={'USDRUBF':dict(path='allowed.csv',prefix_bytes=4,blob='synthetic')})
            with bounded_reads(root,cfg) as receipts:
                with (root/'allowed.csv').open('rb',buffering=0) as f:
                    self.assertEqual(f.read(4),b'a\nb\n')
                    with self.assertRaisesRegex(ValueError,'FUTURE'):f.read(1)
                with self.assertRaisesRegex(ValueError,'PATH_OR_BUFFERING'):(root/'allowed.csv').open('rb')
                with self.assertRaisesRegex(ValueError,'PATH_OR_BUFFERING'):(root/'other.csv').open('rb',buffering=0)
            self.assertEqual(receipts[0]['bytes_read'],4)
    def test_26_calendar_lunch_holidays(self):
        self.assertEqual(self.rules.windows(date(2023,3,15))[1][0].strftime('%H:%M'),'14:15')
        self.assertEqual(self.rules.windows(date(2023,3,21))[1][0].strftime('%H:%M'),'14:05')
        self.assertEqual(self.rules.windows(date(2023,3,8)),[])
    def test_27_conditional_flat_after_exclusion(self):
        p=parameters();rows=self.rows(p);del rows[self.at('10:25')]
        following={at+timedelta(days=1):self.bar(at+timedelta(days=1),b.open,b.high,b.low,b.close) for at,b in self.rows(p).items()}
        rows.update(following);rows=dict(sorted(rows.items()));end=self.day+timedelta(days=2)
        r,st=self.engine(p,rows,end);self.match(p,rows,r,st,end)
        self.assertTrue(any(t['prior_exclusion_requires_flat_assumption'] for t in r.trades));self.assertTrue(all(not t['initial_flat_proven'] for t in r.trades))
    def test_28_syscall_trace_synthetic(self):
        from .validate import trace_receipt
        with tempfile.TemporaryDirectory(dir=ROOT/'IntradayLab/work') as d:
            root=Path(d);specs={}
            for symbol in ('USDRUBF','CNYRUBF'):
                (root/(symbol+'.csv')).write_bytes(b'header\ncandle\nfuture\n');specs[symbol]=dict(path=symbol+'.csv',prefix_bytes=14,rows_2023=1,blob='synthetic',prefix_sha256='synthetic')
            trace=root/'trace';cmd=['strace','-f','-yy','-s','0','-e','trace=openat,read,pread64,lseek,close']
            for spec in specs.values():cmd+=['-P',str(root/spec['path'])]
            cmd+=['-o',str(trace),sys.executable,'-c','from pathlib import Path;import sys\nfor p in sys.argv[1:]:\n with Path(p).open("rb",buffering=0) as f:f.tell();f.read(14);f.tell()',*[str(root/s['path']) for s in specs.values()]]
            subprocess.run(cmd,check=True);self.assertEqual(trace_receipt(trace,dict(inputs=specs,instruments=list(specs)),root)['status'],'PASS')

    def test_29_session_flat_real_open_and_missing_flat(self):
        p=parameters();rows=self.rows(p);prefix=list(self.rows(p).items())[:5]
        for at,b in prefix:
            stamp=at+timedelta(hours=3,minutes=30)
            rows[stamp]=self.bar(stamp,b.open,b.high,b.low,b.close)
        mid=D('100.97')
        for clock in ('13:55','14:00'):rows[self.at(clock)]=self.bar(self.at(clock),mid,mid+D('.01'),mid-D('.01'))
        rows=dict(sorted(rows.items()));r,st=self.engine(p,rows);self.match(p,rows,r,st)
        q=next(t for t in r.trades if t['entry_at']==self.at('13:50'))
        self.assertEqual(q['exit_at'],self.at('13:55'));self.assertEqual(q['exit_reason'],'SESSION_FLAT')
        del rows[self.at('13:55')];r,st=self.engine(p,rows);self.match(p,rows,r,st)
        self.assertTrue(any(t['entry_at']==self.at('13:50') for t in r.data_quality_exclusions))
    def test_30_skip_recovers_exclusion_blocks_same_day(self):
        p=parameters();source=self.rows(p);rows=dict(source)
        for at,b in list(source.items())[:5]:
            stamp=at+timedelta(minutes=30);rows[stamp]=self.bar(stamp,b.open,b.high,b.low,b.close)
        del rows[self.at('10:20')];rows=dict(sorted(rows.items()));r,st=self.engine(p,rows);self.match(p,rows,r,st)
        self.assertTrue(any(t['entry_at']==self.at('10:50') for t in r.trades))
        rows=dict(source)
        for at,b in list(source.items())[:5]:
            stamp=at+timedelta(minutes=30);rows[stamp]=self.bar(stamp,b.open,b.high,b.low,b.close)
        del rows[self.at('10:25')];rows=dict(sorted(rows.items()));r,st=self.engine(p,rows);self.match(p,rows,r,st)
        self.assertTrue(any(s['signal_at']==self.at('10:50') and s['reason']=='DATA_QUALITY_POSITION_BLOCK' for s in r.signals))
    def test_31_missing_freeze_dependency_stops_before_source(self):
        from . import contract
        original=Path.read_text
        def readtext(path,*a,**kw):
            if path==STUDY/'source_commitments.json':return '{"dependencies_sha256":{}}'
            return original(path,*a,**kw)
        def git(*args):
            if args[0]=='log':return '0'*40
            if args[0]=='branch':return 'synthetic'
            if args[0]=='ls-remote':return '0'*40+' refs/heads/synthetic'
            return ''
        with patch.object(contract,'git',side_effect=git),patch.object(Path,'read_text',readtext),patch.object(contract.subprocess,'run',return_value=subprocess.CompletedProcess([],0)):
            with self.assertRaisesRegex(ValueError,'REQUIRED_DEPENDENCY_MISSING'):contract.verify_freeze()

if __name__=='__main__':unittest.main()
