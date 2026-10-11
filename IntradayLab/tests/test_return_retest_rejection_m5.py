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
from IntradayLab.strategies.return_retest_rejection_m5 import ReturnRetestRejectionM5, parameters, FIVE
from IntradayLab.tools.return_retest_contract import LAB, CONFIG, verify_freeze, check_output, bounded_reads
from IntradayLab.tools.audit_return_retest_baseline import constructions, replay, compare_ledger, audit
from IntradayLab.tools.run_return_retest_baseline import research_metrics, calendar_rows, diagnostic


class CTests(unittest.TestCase):
    def setUp(self):
        self.cfg=json.loads(CONFIG.read_text());self.cfg['instruments']=['USDRUBF']
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

    def write_fixture(self,path,case='normal'):
        r,st,rows,raw=self.fixture(case)
        write_data_quality_reports(path,r,{'USDRUBF':rows},self.cfg,self.rules)
        cov=data_quality_coverage({'USDRUBF':rows},self.cfg,self.rules,r)
        csv_write(path/'construction_events.csv',st.construction_events)
        csv_write(path/'monthly_report.csv',calendar_rows(r,st.construction_events,cov,['USDRUBF']))
        csv_write(path/'direction_report.csv',[dict(instrument='USDRUBF',direction=side,**diagnostic([t for t in r.trades if t['direction']==side])) for side in (-1,1)])
        dump(path/'research_metrics.json',research_metrics(r,st.construction_events,cov));dump(path/'config.json',self.cfg)
        return raw

    def test_independent_full_reports(self):
        with tempfile.TemporaryDirectory(dir=LAB/'work') as temp:
            path=Path(temp)/'report';raw=self.write_fixture(path)
            receipt=audit(path,None,self.cfg,{'USDRUBF':raw});self.assertEqual(receipt['status'],'PASS')

    def test_auditor_detects_forged_pf(self):
        with tempfile.TemporaryDirectory(dir=LAB/'work') as temp:
            path=Path(temp)/'report';raw=self.write_fixture(path)
            m=json.loads((path/'research_metrics.json').read_text());m['instruments']['USDRUBF']['economics']['PF_C1_R']='9';dump(path/'research_metrics.json',m)
            with self.assertRaisesRegex(AssertionError,'ECON'):audit(path,None,self.cfg,{'USDRUBF':raw})

    def test_auditor_detects_lost_exclusion(self):
        with tempfile.TemporaryDirectory(dir=LAB/'work') as temp:
            path=Path(temp)/'report';raw=self.write_fixture(path,'missing_exposure');csv_write(path/'data_quality_exclusions.csv',[])
            with self.assertRaises(AssertionError):audit(path,None,self.cfg,{'USDRUBF':raw})

    def test_auditor_detects_fake_approach(self):
        with tempfile.TemporaryDirectory(dir=LAB/'work') as temp:
            path=Path(temp)/'report';raw=self.write_fixture(path)
            text=(path/'signals.csv').read_text();(path/'signals.csv').write_text(text.replace('100.01','100.09'))
            with self.assertRaises(AssertionError):audit(path,None,self.cfg,{'USDRUBF':raw})

    def test_auditor_detects_calendar_corruption(self):
        with tempfile.TemporaryDirectory(dir=LAB/'work') as temp:
            path=Path(temp)/'report';raw=self.write_fixture(path)
            import csv
            with (path/'monthly_report.csv').open() as f:rows=list(csv.DictReader(f))
            rows[0]['Net_R']='100';csv_write(path/'monthly_report.csv',rows)
            with self.assertRaisesRegex(AssertionError,'MONTH'):audit(path,None,self.cfg,{'USDRUBF':raw})

    def test_future_source_guard(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);p=root/'x.csv';p.write_bytes(b'2023\n2024\n')
            cfg={'inputs':{'X':dict(path='x.csv',prefix_bytes=5)}}
            with bounded_reads(root,cfg):
                with p.open('rb',buffering=0) as f:
                    self.assertEqual(f.read(5),b'2023\n')
                    with self.assertRaisesRegex(ValueError,'FUTURE'):f.read(1)

    def test_future_engine_input_guard(self):
        _,_,rows,_=self.fixture();b=next(iter(rows.values()));at=self.rules.at(date(2024,1,1),'10:00');rows[at]=replace(b,start=at)
        with self.assertRaisesRegex(ValueError,'FUTURE'):Backtester(self.rules,**self.cfg['execution']).run(ReturnRetestRejectionM5(parameters()),'USDRUBF',rows,start=date(2023,1,1),end_exclusive=date(2024,1,1))

    def test_no_frozen_commit_no_pnl(self):
        with patch('IntradayLab.tools.return_retest_contract.subprocess.check_output',return_value=''):
            with self.assertRaisesRegex(ValueError,'FREEZE'):verify_freeze()

    def test_immutable_output(self):
        with tempfile.TemporaryDirectory(dir=LAB/'work') as temp:
            p=Path(temp);(p/'existing').write_text('x')
            with self.assertRaisesRegex(ValueError,'IMMUTABLE'):check_output(p)
