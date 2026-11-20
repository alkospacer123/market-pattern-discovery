"""Addressed path arithmetic, causal prefixes, continuity and error accounting."""
from datetime import datetime, timedelta
import unittest

from V20_TradingSystem_M15.v20_runtime.market_suitability import M15Bar, STEP
from V20_TradingSystem_M15.v20_runtime.regime_research import (
    path_quality, er_values, causal_states, truth_periods, evaluate, published_events,
    BAD, GOOD, UNKNOWN,
)

T = datetime(2018,1,3,10)


def bar(i,o=100,h=100,l=100,c=100):
    return M15Bar(T+i*STEP,o,h,l,c,1)


def path(bars,side=1):
    return dict(entry_time=T,available=bars[-1].open_time,entry=100,side=side,
                risk=10,stop_touch=True)


def events(n=100):
    return [dict(available=T+timedelta(days=i+2),signal=T+timedelta(days=i),
                 entry_time=T+timedelta(days=i,minutes=15),contract='Si',
                 raw_R=2.0 if i<40 else -1.0,fp2=int(i<40),stop_aware=2.0 if i<40 else -1.0,
                 mfe_low=2.0 if i<40 else 0.0,mfe_high=2.0 if i<40 else 0.0,
                 amb2=0,fp1=int(i<40),fp3=0,fp5=0,stop_touch=i>=40,
                 bars1=1 if i<40 else None,bars2=2 if i<40 else None)
            for i in range(n)]


class RegimeResearchTest(unittest.TestCase):
    def test_same_bar_target_stop_is_ambiguous_and_bounded(self):
        bs=[bar(0,h=125,l=85,c=100),bar(1)]
        result=path_quality(path(bs),bs)
        self.assertEqual((result['fp2'],result['amb2'],result['bars2']),(0,1,None))
        self.assertEqual((result['mfe_low'],result['mfe_high']),(0,2.5))

    def test_target_before_later_stop_and_short_symmetry(self):
        bs=[bar(0,h=125,l=95,c=120),bar(1,o=120,h=120,l=85),bar(2)]
        result=path_quality(path(bs),bs)
        self.assertEqual((result['fp2'],result['amb2'],result['bars2']),(1,0,1))
        mirrored=[M15Bar(b.open_time,200-b.open,200-b.low,200-b.high,200-b.close,1) for b in bs]
        self.assertEqual(path_quality(path(mirrored,-1),mirrored),result)

    def test_open_target_precedes_same_bar_stop(self):
        bs=[bar(0,h=105,l=95),bar(1,o=125,h=130,l=85,c=100),bar(2)]
        result=path_quality(path(bs),bs)
        self.assertEqual((result['fp2'],result['amb2'],result['bars2']),(1,0,1))

    def test_horizon_high_low_cannot_be_read_and_open_stop_is_counted(self):
        bs=[bar(0,h=105,l=95),bar(1,o=90,h=999,l=1,c=100)]
        result=path_quality(path(bs),bs)
        self.assertEqual((result['fp2'],result['amb2'],result['mfe_high']),(0,0,.5))

    def test_er_exact_scales_and_future_bar_not_read(self):
        bs=[('Si',bar(i,o=100+i,h=100+i,l=100+i,c=100+i)) for i in range(82)]
        prefix=list(er_values(bs,set(),as_of=T+81*STEP))
        self.assertIsNone(prefix[19]['er20'])
        self.assertEqual(prefix[20]['er20'],1)
        self.assertIsNone(prefix[79]['er80'])
        self.assertEqual(prefix[80]['er80'],1)
        class Future:
            open_time=T+100*STEP
            @property
            def close(self):
                raise AssertionError('future Close accessed')
        self.assertEqual(list(er_values(bs[:81]+[('Si',Future())],set(),as_of=T+81*STEP)),prefix)

    def test_er_roll_unknown_gap_and_missing_session_reset(self):
        base=[('Si',bar(i)) for i in range(21)]
        self.assertEqual(list(er_values(base,set()))[-1]['er20'],0)
        for changed in (base+[('Si2',bar(21))],base+[('Si',bar(23))]):
            self.assertIsNone(list(er_values(changed,set()))[-1]['er20'])
        monday=datetime(2018,1,8,10)
        changed=base+[('Si',M15Bar(monday,100,100,100,100,1))]
        calendar={T.date()+timedelta(days=i) for i in (0,1,2,5)}
        self.assertIsNone(list(er_values(changed,calendar))[-1]['er20'])

    def test_state_prefix_identical_with_poisoned_future_and_atomic_ties(self):
        rows=events()
        rows[41]['available']=rows[40]['available']
        cutoff=rows[60]['available']
        full,_=causal_states(rows,[])
        poison=[dict(r) for r in rows]
        for r in poison:
            if r['available']>cutoff:
                r['fp2']=r['raw_R']=object()
        partial,_=causal_states(poison,[],as_of=cutoff)
        self.assertEqual([r for r in full if r['as_of']<=cutoff],partial)
        state=next(r for r in full if r['as_of']==rows[40]['available'])
        self.assertEqual(state['n'],42)
        self.assertEqual(len([r for r in full if r['as_of']==state['as_of']]),1)

    def test_confirmation_uses_atomic_dates_and_staleness_is_unknown(self):
        rows=events(45)
        rows[44]['available']=rows[43]['available']
        expiry=rows[-1]['available']+timedelta(days=91)
        result,_=causal_states(rows,[],clocks={expiry})
        self.assertEqual(result[-2]['RAW20'],BAD)
        self.assertEqual(result[-2]['RAW20_CONFIRM5'],GOOD)
        self.assertEqual(result[-1]['RAW20'],UNKNOWN)
        self.assertEqual(result[-1]['FP2_CUSUM'],UNKNOWN)

    def test_cusum_recovers_at_old_baseline_without_requiring_new_high(self):
        rows=events(80)
        for r in rows[60:]:
            r.update(fp2=1,raw_R=2,stop_aware=2)
        states,_=causal_states(rows,[])
        self.assertEqual(states[50]['FP2_CUSUM'],BAD)
        self.assertEqual(states[-1]['FP2_CUSUM'],GOOD)
        self.assertEqual(states[-1]['cusum_base'],1)

    def test_false_and_unresolved_warnings_and_misses_are_not_successes(self):
        rows=events(140)
        blocks,weak,recovery=truth_periods(rows)
        normal=[dict(as_of=T,n=0,RAW20=GOOD)]
        metrics,_,_=evaluate(rows,normal,'RAW20',T,rows[-1]['available'],weak,recovery,blocks)
        self.assertEqual(sum(r['missed'] for r in metrics),len(weak))
        no_weak=[]
        states=[dict(as_of=T,n=0,RAW20=BAD),dict(as_of=T+timedelta(days=1),n=0,RAW20=GOOD),
                dict(as_of=rows[-1]['available']-timedelta(days=1),n=139,RAW20=BAD)]
        _,warnings,_=evaluate(rows,states,'RAW20',T,rows[-1]['available'],no_weak,[],blocks)
        self.assertEqual([w['result'] for w in warnings],['FALSE','UNRESOLVED'])

    def test_truth_and_errors_are_separate_from_causal_state(self):
        rows=events(140)
        for r in rows[100:]:
            r.update(raw_R=2,fp2=1,stop_aware=2,fp1=1,bars1=1,bars2=2)
        blocks,weak,recoveries=truth_periods(rows)
        self.assertEqual((len(weak),len(recoveries)),(1,1))
        states,_=causal_states(rows,[])
        before=[dict(r) for r in states]
        metrics,warnings,detections=evaluate(rows,states,'RAW20',T,rows[-1]['available'],weak,recoveries,blocks)
        self.assertEqual(states,before)
        self.assertEqual(sum(r['weak'] for r in metrics),1)
        self.assertEqual(sum(r['missed'] for r in metrics),0)
        self.assertTrue(next(d for d in detections if d['kind']=='RECOVERY')['recovery_transition'])
        self.assertTrue(all(w['evaluation_at']>w['start'] for w in warnings if w['evaluation_at']))

    def test_published_unique_counts_and_duplicate_semantics(self):
        rows=published_events()
        self.assertEqual(len(rows),3990)
        self.assertEqual(sum(r['robots'] for r in rows),4431)
        self.assertEqual(sum(r['robots']>1 for r in rows),439)
        self.assertEqual({r['instrument'] for r in rows},
                         {'Si','MIX','CNY','USDRUBF','CNYRUBF','GLDRUBF','IMOEXF'})


if __name__=='__main__':
    unittest.main()
