"""Synthetic signal, clock, raw-oracle corruption and report contract scenarios."""
from copy import deepcopy
from datetime import timedelta,date
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
from IntradayLab.strategies.high_low_cluster_m5 import HighLowClusterM5,parameters,FIVE
from IntradayLab.tests import test_universal_backtester as fixtures
from IntradayLab.tools.audit_high_low_cluster_baseline import episodes,expected_records
from IntradayLab.tools.audit_canonical_baseline import check_rows
from IntradayLab.tools.high_low_cluster_contract import config_path,check_output,LAB


class ClusterTests(unittest.TestCase):
    setUp=fixtures.EngineTests.setUp
    at=fixtures.EngineTests.at
    bar=fixtures.EngineTests.bar
    make_day=fixtures.EngineTests.make_day

    def feed(self,highs,n=4,side=-1,closes=None,gaps=(),tick_change=None,session_change=None):
        st=HighLowClusterM5(parameters(n));st.begin_day('USDRUBF',self.day);out=[]
        for i,value in enumerate(highs):
            at=self.at('10:00')+i*FIVE;ext=D(str(value));c=D(str(closes[i])) if closes else ext+side*D('.03')
            high=ext if side==-1 else D('101')+i*D('.02')
            low=ext if side==1 else D('99')-i*D('.02')
            b=None if i in gaps else self.bar(at,o=c,h=str(high),l=str(low),c=str(c))
            w=(self.at('10:00'),self.at('14:00')) if session_change!=i else (at,self.at('14:00'))
            ctx=Context('USDRUBF',at,at+FIVE,w,D('.001') if tick_change==i else D('.01'),{})
            out.extend(st.on_bar(b,ctx))
        st.end_day()
        return out,st

    def setup_cluster(self,n=4,side=-1):
        for i in range(n):
            at=self.at('10:00')+i*FIVE;ext=D(100)-(D('.01') if i%2 else D(0)) if side==-1 else D(100)+(D('.01') if i%2 else D(0))
            c=D(100)+side*D('.03')
            self.rows[at]=self.bar(at,o=str(c),h=str(ext if side==-1 else D(101)+i*D('.02')),l=str(ext if side==1 else D(99)-i*D('.02')),c=str(c))
        at=self.at('10:00')+n*FIVE;c=D(100)+side*D('.03')
        self.rows[at]=self.bar(at,o=str(c),h=str(c+D('.01')),l=str(c-D('.01')),c=str(c))

    def compare(self,n=4):
        rows=dict(sorted(self.rows.items()));raw={t:(b.open,b.high,b.low,b.close,b.volume) for t,b in rows.items()}
        ss,tt,_=Backtester(self.rules,entry_mode='ENTRY_NEXT_OPEN').run(HighLowClusterM5(parameters(n)),'USDRUBF',rows,start=self.day,end_exclusive=max(rows).date()+timedelta(days=1))
        es,et=expected_records('USDRUBF',raw,n)
        for actual,expected,label in ((ss,es,'signals'),(tt,et,'trades')):
            # Runner-only labels are tested through full synthetic report/audit below.
            keys=sorted({k for r in expected for k in r if k not in ('unknown_effective_at','extrema','extreme_times','episode_id','level_type','boundary_touches','cluster_bars','cluster_min','cluster_max','cluster_width_ticks','cluster_level','round_distance_ticks','signal_close','entry_distance_ticks','open_vs_close_ticks','holding_lower_minutes','holding_upper_minutes') or label=='signals' and k in ('episode_id','cluster_min','cluster_max','cluster_bars','boundary_touches','cluster_level','signal_close','level_type','round_distance_ticks','cluster_width_ticks')})
            check_rows(actual,expected,keys,label)
        return ss,tt,raw

    def test_all_three_exact_lengths_and_mirror(self):
        for n in (4,7,10):
            for side in (-1,1):
                values=[100+(side==1)*.01 if i%2 else 100 for i in range(n)] if side==1 else [100-.01 if i%2 else 100 for i in range(n)]
                events,_=self.feed(values,n,side)
                self.assertEqual(len(events),1);e=events[0]
                self.assertEqual(e['cluster_bars'],n);self.assertEqual(e['signal_at'],self.at('10:00')+n*FIVE)
                self.assertEqual(e['boundary_touches'],(n+1)//2)
                self.assertEqual(e['cluster_width_ticks'],D(1))

    def test_zero_width_excluded(self):self.assertEqual(self.feed([100]*15)[0],[])
    def test_width_one_and_three_included_four_resets(self):
        for low in (99.99,99.97):self.assertEqual(len(self.feed([100,low,100,low])[0]),1)
        self.assertEqual(self.feed([100,99.96,100,99.96])[0],[])
    def test_at_least_two_boundary_hits(self):self.assertEqual(self.feed([99.98,99.99,99.99,100])[0],[])
    def test_no_overlapping_duplicate_rejected_or_filled(self):
        e,st=self.feed([100,99.99]*20)
        self.assertEqual(len(e),1);self.assertEqual(len(st.episode_records),1)
        self.assertEqual(st.episode_records[0]['episode_bars'],40)
    def test_reset_starts_current_bar_without_recycling(self):
        e,st=self.feed([100,99.99]*3+[100.04,100.03]*3)
        self.assertEqual(len(e),2);self.assertEqual(e[1]['episode_start'],self.at('10:30'))
        self.assertEqual(st.episode_records[0]['reset_reason'],'ENVELOPE_ABOVE_3_TICKS')
    def test_common_episode_identity_across_n(self):
        events=[self.feed([100,99.99]*6,n)[0][0] for n in (4,7,10)]
        self.assertEqual(len({e['episode_id'] for e in events}),1)
        self.assertEqual(len({e['cluster_id'] for e in events}),3)
    def test_close_at_boundary_consumes_first_formed_window(self):
        e,_=self.feed([100,99.99,100,100,100,99.99,100,99.99],closes=[99.97,99.97,99.97,100,99.97,99.97,99.97,99.97])
        self.assertEqual(len(e),1);self.assertEqual(e[0]['base_reason'],'CLOSE_AT_BOUNDARY')
    def test_gap_session_and_tick_reset(self):
        for kwargs in ({'gaps':(2,)},{'session_change':2},{'tick_change':2}):self.assertEqual(self.feed([100,99.99,100,99.99],**kwargs)[0],[])
    def test_day_reset(self):
        e,st=self.feed([100,99.99,100]);st.begin_day('USDRUBF',self.day+timedelta(days=1));self.assertEqual(st.runs,{})
    def test_uncompleted_bar_refused(self):
        st=HighLowClusterM5(parameters(4));st.begin_day('USDRUBF',self.day);at=self.at('10:00')
        with self.assertRaisesRegex(ValueError,'UNCOMPLETED'):st.on_bar(self.bar(at),Context('USDRUBF',at,at+timedelta(minutes=4),(at,self.at('14:00')),D('.01'),{}))
    def test_parameters_locked(self):
        for key,value in [('cluster_bars',5),('maximum_width_ticks',4),('target_net_R','5')]:
            with self.assertRaises(ValueError):HighLowClusterM5(dict(parameters(4),**{key:value}))
    def test_next_open_and_all_geometry_in_independent_oracle(self):
        for n in (4,7,10):
            for side in (-1,1):
                self.setUp();self.setup_cluster(n,side);s,t,_=self.compare(n)
                self.assertEqual(t[0]['entry_at'],s[0]['signal_at']);self.assertEqual(t[0]['risk'],D('.04'))
                self.assertEqual(t[0]['planned_net_to_net_R'],D(3))
    def test_independent_missing_open_and_future_hlc(self):
        self.setup_cluster();at=self.at('10:20');del self.rows[at];_,t,_=self.compare();self.assertIsNone(t[0]['entry_price'])
        self.setUp();self.setup_cluster();before=self.compare()[0][0]
        self.rows[at]=self.bar(at,o='99.97',h='150',l='50',c='100');after=self.compare()[0][0]
        for key in ('signal_id','cluster_level','entry_open','risk','take'):self.assertEqual(before[key],after[key])
    def test_independent_rejections(self):
        for op,reason in [('100.01','OPEN_WRONG_SIDE_OF_CLUSTER'),('100','STOP_BELOW_3_TICKS'),('99.99','STOP_BELOW_3_TICKS'),('99.95','ENTRY_MORE_THAN_4_TICKS_FROM_CLUSTER'),('99.87','STOP_ABOVE_12_TICKS')]:
            self.setUp();self.setup_cluster();at=self.at('10:20');self.rows[at]=self.bar(at,o=op,h='100.1',l='99.8',c=op)
            s,t,_=self.compare();self.assertEqual(s[0]['reason'],reason)
    def test_simultaneous_sides_consumed(self):
        st=HighLowClusterM5(parameters(4));st.begin_day('USDRUBF',self.day);events=[]
        for i in range(8):
            at=self.at('10:00')+i*FIVE;b=self.bar(at,o='99.5',h='100' if i%2==0 else '99.99',l='99' if i%2==0 else '99.01',c='99.5')
            events.extend(st.on_bar(b,Context('USDRUBF',at,at+FIVE,(self.at('10:00'),self.at('14:00')),D('.01'),{})))
        self.assertEqual(len(events),2);self.assertTrue(all(e['base_reason']=='AMBIGUOUS_BOTH_SIDES' for e in events))
    def test_round_grid_changes_no_signal_rules(self):
        e,_=self.feed([100,99.99,100,99.99]);self.assertEqual(e[0]['level_type'],'ROUND_NEAR')
        e,_=self.feed([100.04,100.03,100.04,100.03]);self.assertEqual(e[0]['level_type'],'ORDINARY_FAR')
        self.assertEqual(e[0]['round_distance_ticks'],D(4))
    def test_corrupted_raw_extreme_or_width_detected(self):
        self.setup_cluster();s,_,raw=self.compare();expected=episodes('USDRUBF',raw,4);altered=deepcopy(s);altered[0]['cluster_width_ticks']=D(2)
        with self.assertRaises(AssertionError):check_rows(altered,expected,('cluster_width_ticks',),'CORRUPT')
    def test_immutable_output(self):
        with tempfile.TemporaryDirectory(dir=LAB/'work') as tmp:
            p=Path(tmp);check_output(p,4);(p/'config.json').write_text('{}')
            with self.assertRaisesRegex(ValueError,'IMMUTABLE'):check_output(p,4)
    def test_synthetic_all_instrument_reports_and_independent_audit(self):
        from IntradayLab.tools import run_high_low_cluster_baseline as runner,audit_high_low_cluster_baseline as auditor
        cfg=json.loads(config_path(4).read_text());rules=MarketRules(cfg);day=date(2023,1,4);raw={};oracle={}
        for symbol in cfg['instruments']:
            rows={};step=rules.tick(symbol,rules.at(day,'10:00'))
            for a,z in rules.windows(day):
                at=a
                while at<z:
                    prices=[D(100),D(100)+5*step,D(100)-5*step,D(100),D(10)]
                    if at<rules.at(day,'10:20'):
                        i=int((at-rules.at(day,'10:00'))/FIVE);prices=[D(100)-3*step,D(100)-(i%2)*step,D(100)-(20+i)*step,D(100)-3*step,D(10)]
                    elif at==rules.at(day,'10:20'):prices=[D(100)-3*step,D(100)-2*step,D(100)-4*step,D(100)-3*step,D(10)]
                    rows[at]=validate_bar(at,tuple(prices),FIVE,step);at+=FIVE
            raw[symbol]=rows;oracle[symbol]={t:(b.open,b.high,b.low,b.close,b.volume) for t,b in rows.items()}
        with tempfile.TemporaryDirectory(dir=LAB/'work') as tmp:
            out=Path(tmp)
            with patch.object(runner,'verify_freeze',return_value=(cfg,'0'*40,'synthetic')),patch.object(runner,'protected_check'),patch.object(runner,'load_market_data',return_value=(raw,{})):runner.run(Path('/workspace/market-pattern-data'),out,4)
            with patch.object(auditor,'verify_freeze',return_value=(cfg,'0'*40,'synthetic')),patch.object(auditor,'protected_check'),patch.object(auditor,'read_source',return_value=(oracle,{})):result=auditor.audit(Path('/workspace/market-pattern-data'),out,4)
            self.assertEqual(result['status'],'PASS')


if __name__=='__main__':unittest.main()
