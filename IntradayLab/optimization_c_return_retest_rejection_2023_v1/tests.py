"""C_v1 causal construction, next-Open, gap accounting and independent corruption tests."""
from copy import deepcopy
from dataclasses import replace
from datetime import date, timedelta
from decimal import Decimal as D
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from IntradayLab.core.backtester import Backtester
from IntradayLab.core.calendar import MarketRules
from IntradayLab.core.data_loader import validate_bar
from IntradayLab.core.models import Context
from IntradayLab.core.reports import csv_write, dump, write_data_quality_reports, data_quality_coverage
from IntradayLab.strategies.return_retest_rejection_m5_optimization_c_v1 import ReturnRetestRejectionM5OptimizationC as ReturnRetestRejectionM5, parameters, FIVE
from .contract import ROOT, POLICY as CONFIG, grid, verify_freeze, output_guard as check_output, bounded_reads
LAB=ROOT/"IntradayLab"
from .auditor import constructions, replay, compare_ledger, audit, event_check, read_csv


class CTests(unittest.TestCase):
    def setUp(self):
        self.cfg=json.loads(CONFIG.read_text());self.cfg['instruments']=['USDRUBF']
        self.cfg['execution']={k:v for k,v in self.cfg['execution'].items() if k not in ('unknown_scope','wait_complete_bars')}
        self.rules=MarketRules(self.cfg);self.day=date(2023,1,4)
        self.origin=self.rules.at(self.day,'10:00')
        self.window=(self.origin,self.rules.at(self.day,'14:00'))

    def bar(self,i,high,side=-1,close=None,low=None):
        x=D(str(high));c=D(str(close)) if close is not None else x+side*D('.01')
        h=x if side==-1 else x+D('.05')
        l=D(str(low)) if low is not None else x if side==1 else x-D('.05')
        return validate_bar(self.origin+i*FIVE,(c,h,l,c,D(1)),FIVE,D('.01'))

    def feed(self,values,side=-1,gaps=(),closes=None,shift=None):
        st=ReturnRetestRejectionM5(parameters());st.begin_day('USDRUBF',self.day);events=[];rows={}
        for i,x in enumerate(values):
            b=None if i in gaps else self.bar(i,x,side,close=closes[i] if closes else None)
            tick=D('.001') if shift==('tick',i) else D('.01')
            win=(self.origin+i*FIVE,self.window[1]) if shift==('session',i) else self.window
            ctx=Context('USDRUBF',self.origin+i*FIVE,self.origin+(i+1)*FIVE,win,tick,{})
            events+=st.on_bar(b,ctx)
            if b:rows[b.start]=b
        return [e for e in events if e['direction']==side],st,rows

    def pattern(self):return ['99.95','99.96','99.97','99.98','99.99','100.00','99.97','100.01','99.97','100.00']

    def test_short_three_distinct(self):
        es,st,_=self.feed(self.pattern());self.assertEqual(len(es),1);e=es[0]
        self.assertEqual(e['base_reason'],'SIGNAL');self.assertEqual(e['stop'],D('100.02'))
        self.assertEqual(e['approach_separation_bars'],[2,2]);self.assertEqual(e['retreat_depth_ticks'],[D(3),D(3)])

    def test_long_mirror(self):
        values=[str(D(200)-D(x)) for x in self.pattern()];es,_,_=self.feed(values,side=1)
        self.assertEqual(len(es),1);self.assertEqual(es[0]['base_reason'],'SIGNAL');self.assertEqual(es[0]['stop'],D('99.98'))

    def test_consecutive_touches_not_three(self):
        es,_,_=self.feed(self.pattern()[:6]+['100']*10);self.assertEqual(es,[])

    def test_only_one_retreat_not_three(self):
        es,_,_=self.feed(self.pattern()[:8]+['100']*10);self.assertEqual(es,[])

    def test_two_tick_retreat_insufficient(self):
        p=self.pattern();p[6]=p[8]='99.98';self.assertEqual(self.feed(p)[0],[])

    def test_exact_three_tick_retreat(self):self.assertEqual(len(self.feed(self.pattern())[0]),1)

    def test_tolerance_edges(self):
        for x in ('99.98','100.02'):
            p=self.pattern();p[7]=x
            es,_,_=self.feed(p);self.assertEqual(len(es),1)

    def test_outer_break_strict(self):
        p=self.pattern();p[7]='100.03';es,st,_=self.feed(p)
        self.assertEqual(es,[]);self.assertTrue(any(e.get('reason')=='OUTER_ZONE_BREAK' for e in st.construction_events))

    def test_inner_side_outside_zone_waits(self):
        p=self.pattern()[:7]+['99.96','99.95','100','99.97','100']
        es,_,_=self.feed(p);self.assertEqual(es[0]['approach_separation_bars'],[4,2])

    def test_exact_24_bars_allowed(self):
        p=self.pattern()[:8]+['99.97']*20+['100'];es,_,_=self.feed(p)
        self.assertEqual(es[0]['construction_bars'],24)

    def test_bar25_expiry(self):
        p=self.pattern()[:8]+['99.97']*21+['100'];es,st,_=self.feed(p)
        self.assertEqual(es,[]);self.assertTrue(any(e.get('reason')=='EXPIRED_24_BARS' for e in st.construction_events))

    def test_failed_third_close_consumed(self):
        p=self.pattern()+['100','99.97','100'];closes=[str(D(x)-D('.01')) for x in p];closes[9]='100'
        es,_,_=self.feed(p,closes=closes);self.assertEqual(len(es),1);self.assertEqual(es[0]['base_reason'],'THIRD_CLOSE_NOT_REJECTED')

    def test_one_signal_consumed(self):
        es,_,_=self.feed(self.pattern()+['99.97','100']*6);self.assertEqual(len(es),1)

    def test_five_prior_required(self):self.assertEqual(self.feed(self.pattern()[3:])[0],[])

    def test_local_extreme_strict(self):
        p=self.pattern();p[4]='100';es,_,_=self.feed(p);self.assertEqual(es,[])

    def test_prior_five_gap_resets(self):self.assertEqual(self.feed(self.pattern(),gaps=(3,))[0],[])
    def test_gap_between_approaches_resets(self):self.assertEqual(self.feed(self.pattern(),gaps=(8,))[0],[])
    def test_session_reset(self):self.assertEqual(self.feed(self.pattern(),shift=('session',8))[0],[])
    def test_tick_reset(self):self.assertEqual(self.feed(self.pattern(),shift=('tick',8))[0],[])

    def test_invalid_bar_resets(self):
        st=ReturnRetestRejectionM5(parameters());st.begin_day('USDRUBF',self.day)
        for i,x in enumerate(self.pattern()):
            b=self.bar(i,x)
            if i==8:b=replace(b,volume=D(0),problem='ZERO_VOLUME')
            es=st.on_bar(b,Context('USDRUBF',b.start,b.available_at,self.window,D('.01'),{}))
        self.assertEqual(es,[])

    def test_day_end_resets(self):
        _,st,_=self.feed(self.pattern()[:8]);st.end_day();self.assertFalse(st.runs);self.assertFalse(st.history)

    def test_uncompleted_rejected(self):
        st=ReturnRetestRejectionM5(parameters());st.begin_day('USDRUBF',self.day);b=self.bar(0,'100')
        with self.assertRaisesRegex(ValueError,'UNCOMPLETED'):st.on_bar(b,Context('USDRUBF',b.start,b.start,self.window,D('.01'),{}))

    def test_parameters_locked(self):
        for k in parameters():
            p=parameters();p[k]='altered'
            with self.assertRaisesRegex(ValueError,'UNAPPROVED'):ReturnRetestRejectionM5(p)

    def test_both_sides_ambiguous(self):
        st=ReturnRetestRejectionM5(parameters());st.begin_day('USDRUBF',self.day);es=[]
        for i in range(10):
            h,l=('100.9','99.1') if i<5 or i in (6,8) else ('101','99')
            b=validate_bar(self.origin+i*FIVE,tuple(map(D,('100',h,l,'100','1'))),FIVE,D('.01'))
            es+=st.on_bar(b,Context('USDRUBF',b.start,b.available_at,self.window,D('.01'),{}))
        self.assertEqual(len(es),2);self.assertTrue(all(e['base_reason']=='AMBIGUOUS_BOTH_SIDES' for e in es))

    def fixture(self,case='normal'):
        rows={};st=ReturnRetestRejectionM5(parameters())
        for a,z in self.rules.windows(self.day):
            while a<z:
                rows[a]=validate_bar(a,tuple(map(D,('99.98','99.99','99.96','99.98','1'))),FIVE,D('.01'));a+=FIVE
        for i,x in enumerate(self.pattern()):rows[self.origin+i*FIVE]=self.bar(i,x)
        entry=self.origin+10*FIVE
        if case=='missing_entry':del rows[entry]
        if case=='invalid_open':rows[entry]=replace(rows[entry],open=D('99.981'),problem='OFF_HISTORICAL_GRID')
        if case=='missing_exposure':del rows[entry+FIVE]
        if case=='invalid_exposure':rows[entry]=replace(rows[entry],volume=D(0),problem='ZERO_VOLUME')
        if case=='stop_gap':rows[entry+FIVE]=replace(rows[entry+FIVE],open=D('100.04'),high=D('100.05'),close=D('100.04'))
        if case=='stop_first':rows[entry]=replace(rows[entry],high=D('100.05'),low=D('99.50'))
        if case=='take':rows[entry+FIVE]=replace(rows[entry+FIVE],low=D('99.70'))
        if case=='entry_take':rows[entry]=replace(rows[entry],low=D('99.70'))
        if case=='missing_time':del rows[entry+timedelta(minutes=120)]
        if case.startswith('open_'):
            op=D(case[5:]);rows[entry]=replace(rows[entry],open=op,high=max(D('100.30'),op),low=min(D('99.70'),op),close=op)
        rows=dict(sorted(rows.items()))
        result=Backtester(self.rules,**self.cfg['execution']).run(st,'USDRUBF',rows,start=date(2023,1,1),end_exclusive=date(2024,1,1))
        raw={at:dict(o=b.open,h=b.high,l=b.low,c=b.close,v=b.volume) for at,b in rows.items()}
        candidates,_=constructions('USDRUBF',raw,self.cfg);expected=replay('USDRUBF',raw,candidates,self.cfg)
        for actual,wanted,name in zip((result.signals,result.trades,result.data_gap_skips,result.data_quality_exclusions),expected,('ss','tt','sk','xx')):
            serialized=[]
            for r in actual:
                serialized.append({k:json.dumps(v,default=str,sort_keys=True) if isinstance(v,(list,dict)) else '' if v is None else str(v) for k,v in r.items()})
            compare_ledger(serialized,wanted,name,ignore=('window_end',))
        return result,st,rows,raw

    def test_independent_next_open_and_net3(self):
        r,_,_,_=self.fixture();t=r.trades[0]
        self.assertEqual(t['entry_at'],self.origin+10*FIVE);self.assertEqual(t['risk'],D('.04'));self.assertEqual(t['take'],D('99.78'))
        self.assertEqual(t['planned_net_to_net_R'],D(3));self.assertEqual(t['net_R_c1'],D('-.5'))

    def test_open_only_admission_not_future_hlc(self):
        r,_,_,_=self.fixture();r2,_,_,_=self.fixture('stop_first')
        for k in ('entry_price','stop','risk','take','entry_at'):self.assertEqual(r.trades[0][k],r2.trades[0][k])

    def test_independent_skips_no_delayed_fill(self):
        for case in ('missing_entry','invalid_open'):
            r,_,_,_=self.fixture(case);self.assertEqual(len(r.data_gap_skips),1);self.assertFalse(r.trades);self.assertFalse(r.data_quality_exclusions)

    def test_independent_exclusions_no_pnl(self):
        for case in ('missing_exposure','invalid_exposure','missing_time'):
            r,_,_,_=self.fixture(case);self.assertEqual(len(r.data_quality_exclusions),1);self.assertFalse(r.trades)
            self.assertTrue(r.data_quality_exclusions[0]['remainder_of_day_blocked']);self.assertTrue(r.days[-1]['prior_exclusion_requires_flat_assumption'])

    def test_independent_stop_take_ordering(self):
        for case,reason in (('stop_gap','STOP'),('stop_first','STOP'),('take','TAKE'),('entry_take','TIME')):
            r,_,_,_=self.fixture(case);self.assertEqual(r.trades[0]['exit_reason'],reason)
        self.assertEqual(self.fixture('stop_gap')[0].trades[0]['exit_price'],D('100.04'))
        self.assertTrue(self.fixture('stop_first')[0].trades[0]['stop_take_conflict'])

    def test_independent_admission_boundaries(self):
        for op,reason in (('100.02','OPEN_WRONG_SIDE_OF_CONSTRUCTION'),('100.01','STOP_BELOW_3_TICKS'),('99.97', ''),('99.96','ENTRY_MORE_THAN_4_TICKS_FROM_CONSTRUCTION'),('99.89','STOP_ABOVE_12_TICKS')):
            r,_,_,_=self.fixture('open_'+op);self.assertEqual(r.signals[0]['reason'],reason)


    def test_full_grid_unique_and_control(self):
        specs=grid(json.loads(CONFIG.read_text()))
        self.assertEqual(len(specs),288)
        self.assertEqual(len({p['configuration_id'] for p in specs}),288)
        self.assertIn('C_OPT2023_APP3_LOOKBACK5_TOL2_MAXBARS24_SB1_TP3',{p['configuration_id'] for p in specs})

    def test_two_approach_final_second(self):
        p=dict(parameters(),approaches=2)
        rows={self.origin+i*FIVE:self.bar(i,x) for i,x in enumerate(self.pattern()+['99.97','100']*5)}
        st=ReturnRetestRejectionM5(p);st.begin_day('USDRUBF',self.day);events=[]
        for b in rows.values():events+=st.on_bar(b,Context('USDRUBF',b.start,b.available_at,self.window,D('.01'),{}))
        es=[e for e in events if e['direction']==-1]
        self.assertEqual(len(es),1);self.assertEqual(len(es[0]['approach_starts']),2)
        self.assertEqual(es[0]['signal_at'],self.origin+8*FIVE)
        self.assertFalse(any(e['event']=='THIRD' and e['direction']==-1 for e in st.construction_events))

    def test_all_288_geometry_and_independent_state_oracle(self):
        for spec in grid(json.loads(CONFIG.read_text())):
            p={k:v for k,v in spec.items() if k!='configuration_id'}
            rows={self.origin+i*FIVE:self.bar(i,x) for i,x in enumerate(self.pattern()+['99.97','100']*25)}
            st=ReturnRetestRejectionM5(p);st.begin_day('USDRUBF',self.day);events=[]
            for b in rows.values():events+=st.on_bar(b,Context('USDRUBF',b.start,b.available_at,self.window,D('.01'),{}))
            st.end_day()
            raw={at:dict(o=b.open,h=b.high,l=b.low,c=b.close,v=b.volume) for at,b in rows.items()}
            cfg=dict(self.cfg,parameters=p)
            es,ee=constructions('USDRUBF',raw,cfg)
            for side in (-1,1):
                a=[e for e in events if e['direction']==side];b=[e for e in es if e['direction']==side]
                self.assertEqual([e['signal_id'] for e in a],[e['signal_id'] for e in b])
                for x,y in zip(a,b):
                    for k in y:
                        if k not in ('window_end','instrument'):self.assertEqual(x[k],y[k],spec['configuration_id']+' '+k)

    def test_adjacent_published_lists_not_numeric_units(self):
        from .aggregation import select
        policy=json.loads(CONFIG.read_text());specs=grid(policy);rows=[]
        for spec in specs:
            rows.append(dict(spec,instrument='USDRUBF',CLOSED=100,entry_days=40,entry_months=6,PF_R=D(2),PF_price=D(2),expectancy_R=D(1),positive_exit_months=9,conditional_closed_only_DD_R=D(5),pass_sample=True,pass_PF_R=True,pass_PF_price=True,pass_positive_expectancy=True,pass_months=True,pass_conditional_DD=True,pass_trade_concentration=True,pass_month_concentration=True))
        edges,selection=select(rows,policy)
        control=policy['historical_control_id']
        neighbors={r['neighbor_id'] for r in edges if r['configuration_id']==control}
        self.assertIn(control.replace('LOOKBACK5','LOOKBACK3'),neighbors)
        self.assertIn(control.replace('MAXBARS24','MAXBARS36'),neighbors)
        self.assertNotIn(control.replace('APP3','APP2').replace('LOOKBACK5','LOOKBACK3'),neighbors)
        self.assertEqual(selection['instruments']['USDRUBF']['full_criteria_pass'],288)

    def test_future_guard_unbuffered_and_one_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);source=root/'x.csv';source.write_bytes(b'2023\n2024\n')
            other=root/'y.csv';other.write_bytes(b'blocked')
            policy={'inputs':{'USDRUBF':dict(path='x.csv',prefix_bytes=5,blob='synthetic')}}
            with bounded_reads(root,policy) as receipts:
                with source.open('rb',buffering=0) as f:
                    self.assertEqual(f.read(5),b'2023\n')
                    with self.assertRaisesRegex(ValueError,'FUTURE'):f.read(1)
                with self.assertRaisesRegex(ValueError,'FORBIDDEN'):other.open('rb',buffering=0)
            self.assertEqual(receipts[0]['bytes_read'],5)

class FreezeGuardTests(unittest.TestCase):
    def test_missing_freeze_stops_before_source(self):
        from . import contract
        with patch.object(contract,'git',return_value=''):
            with self.assertRaisesRegex(ValueError,'FREEZE'):contract.verify_freeze()

    def test_guard_missing_dependency_rejected(self):
        from . import contract
        import hashlib
        fake={'dependencies_sha256':{}}
        original=Path.read_text
        def read(path,*a,**kw):
            return json.dumps(fake) if path==contract.STUDY/'source_commitments.json' else original(path,*a,**kw)
        def git(*args):
            if args[0]=='log':return 'a'*40
            if args[0]=='branch':return 'synthetic'
            if args[0]=='ls-remote':return 'a'*40+' refs/heads/synthetic'
            if args[0]=='fetch':return ''
            raise AssertionError(args)
        with patch.object(contract,'git',git),patch.object(Path,'read_text',read),patch.object(contract.subprocess,'run',return_value=type('Status',(),{'returncode':0})()):
            with self.assertRaisesRegex(ValueError,'DEPENDENCY_MISSING'):contract.verify_freeze()

    def test_immutable_output(self):
        with tempfile.TemporaryDirectory(dir=LAB/'work') as temp:
            with self.assertRaisesRegex(ValueError,'IMMUTABLE'):check_output(Path(temp))

    def test_exact_metrics_no_losses_unavailable(self):
        from .aggregation import economics
        self.assertEqual(economics([])['PF_R'],'NOT_AVAILABLE')
        self.assertEqual(economics([])['positive_exit_months'],0)

    def test_full_gate_failure_not_ranked(self):
        from .aggregation import select,criteria
        policy=json.loads(CONFIG.read_text());spec=grid(policy)[0]
        m=dict(spec,instrument='USDRUBF',CLOSED=99,entry_days=80,entry_months=12,PF_R=D(10),PF_price=D(10),expectancy_R=D(5),positive_exit_months=12,conditional_closed_only_DD_R=D(1),largest_winner_share_R=D('.1'),largest_positive_month_share_R=D('.2'))
        m.update({'pass_'+k:v for k,v in criteria(m,policy['selection']).items()})
        _,r=select([m],policy)
        self.assertEqual(m['rank'],'NOT_AVAILABLE');self.assertIn('sample',m['failure_reasons'])
        self.assertEqual(r['overall_result'],'NO QUALIFYING OPTIMIZATION CANDIDATE')

    def test_maximum36_current_bar_causal_restart(self):
        fx=CTests();fx.setUp();p=dict(parameters(),maximum_construction_bars=36)
        xs=fx.pattern()[:8]+['99.97']*32+['100']
        st=ReturnRetestRejectionM5(p);st.begin_day('USDRUBF',fx.day);es=[]
        for i,x in enumerate(xs):
            b=fx.bar(i,x);es+=st.on_bar(b,Context('USDRUBF',b.start,b.available_at,fx.window,D('.01'),{}))
        self.assertEqual(es[0]['construction_bars'],36)

    def test_stop_buffer2_fixed_no_risk_repair(self):
        fx=CTests();fx.setUp();p=dict(parameters(),stop_buffer_ticks=2)
        st=ReturnRetestRejectionM5(p);st.begin_day('USDRUBF',fx.day);es=[]
        for i,x in enumerate(fx.pattern()):
            b=fx.bar(i,x);es+=st.on_bar(b,Context('USDRUBF',b.start,b.available_at,fx.window,D('.01'),{}))
        self.assertEqual(es[0]['stop'],D('100.03'))

    def test_second_failed_close_consumes(self):
        fx=CTests();fx.setUp();p=dict(parameters(),approaches=2)
        st=ReturnRetestRejectionM5(p);st.begin_day('USDRUBF',fx.day);es=[]
        for i,x in enumerate(fx.pattern()+['99.97','100']*5):
            b=fx.bar(i,x,close='100' if i==7 else None);es+=st.on_bar(b,Context('USDRUBF',b.start,b.available_at,fx.window,D('.01'),{}))
        ss=[e for e in es if e['direction']==-1]
        self.assertEqual(len(ss),1);self.assertEqual(ss[0]['base_reason'],'SECOND_CLOSE_NOT_REJECTED')

if __name__=='__main__':unittest.main(verbosity=2)
