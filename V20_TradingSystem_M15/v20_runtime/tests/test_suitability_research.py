"""Targeted causal time, separate accounts, uncertainty and rotation tests."""
import unittest
from datetime import datetime,timedelta

from V20_TradingSystem_M15.v20_runtime.suitability_research import (
    Evidence,result_available,performance,evaluate_future,make_tracks,
    weak_periods,rotation_evaluation,MODES,METHODS,monthly_rows,GOOD,BAD,Track)

T=datetime(2018,1,1)
M=MODES[0]


def trades(values,instrument='Si',start=T,strategy=M):
    return [dict(strategy=strategy,instrument=instrument,contract=instrument,
        signal=start+timedelta(days=i),entry=start+timedelta(days=i,minutes=15),
        available=start+timedelta(days=i+1),exit=start+timedelta(days=i+1),
        net=float(v),gross=float(v)+.1,stop=v<0,reason=1 if v<0 else 3)
        for i,v in enumerate(values)]


def evidence(groups):
    return Evidence(groups,{s:(T,T+timedelta(days=1000)) for s in ('Si','MIX','CNY','USDRUBF','CNYRUBF','GLDRUBF','IMOEXF')})


class SuitabilityTests(unittest.TestCase):
    def test_stop_not_known_at_bar_open(self):
        for reason in (1,4):self.assertEqual(result_available(T,reason),T+timedelta(minutes=15))
        for reason in (2,3):self.assertEqual(result_available(T,reason),T)

    def test_future_poison_and_own_outcome_excluded(self):
        rows=trades([1]*60)
        class Poison:
            def __float__(self):raise AssertionError('future parsed')
        rows.append(dict(rows[-1],available=T+timedelta(days=100),net=Poison(),gross=Poison()))
        ev=evidence({(M,'Si'):rows})
        card=ev.at(M,'Si',T+timedelta(days=60))
        self.assertEqual(card['known'],60);self.assertEqual(card['short']['net_mean'],1)

    def test_horizon_fp_unavailable_after_early_stop(self):
        row=trades([-1])[0]
        row['path']=dict(available=str(T+timedelta(days=3)),fp2='1',fp5='0',raw_R='10',stop_aware='-1')
        self.assertEqual(performance([row],T+timedelta(days=1))['horizon_known_n'],0)
        self.assertEqual(performance([row],T+timedelta(days=3))['FP2'],1)

    def test_atomic_closes_and_exact_windows(self):
        rows=trades(range(61));rows[-1]['available']=rows[-2]['available']
        card=evidence({(M,'Si'):rows}).at(M,'Si',T+timedelta(days=60))
        self.assertEqual(card['known'],61);self.assertEqual(card['long']['n'],60)
        self.assertEqual(card['short']['net_mean'],50.5)

    def test_no_robot_or_old_modern_pooling(self):
        ev=evidence({(M,'Si'):trades([1]*59),(MODES[1],'Si'):trades([1]*60,strategy=MODES[1]),
                     (M,'USDRUBF'):trades([1]*60,'USDRUBF')})
        self.assertEqual(ev.at(M,'Si',T+timedelta(days=60))['state'],'INSUFFICIENT')
        self.assertEqual(ev.alternative(M,'Si',T+timedelta(days=60)),(None,None))

    def test_uncertain_negative_is_not_replacement(self):
        ev=evidence({(M,'Si'):trades([-2,1.9]*30)})
        c=ev.at(M,'Si',T+timedelta(days=60))
        self.assertLess(c['long']['net_mean'],0)
        self.assertNotEqual(c['state'],'NO_EDGE_CONFIRMED')

    def test_small_lucky_candidate_not_ranked(self):
        ev=evidence({(M,'Si'):trades([-1]*60),(M,'MIX'):trades([100]*59)})
        self.assertEqual(ev.alternative(M,'Si',T+timedelta(days=60)),(None,None))

    def test_candidate_same_strategy_and_available_at_date(self):
        ev=evidence({(M,'Si'):trades([-1]*60),(M,'MIX'):trades([1]*60)})
        self.assertEqual(ev.alternative(M,'Si',T+timedelta(days=60))[0],'MIX')
        self.assertIsNone(ev.alternative(M,'Si',T+timedelta(days=59))[0])
        self.assertIsNone(ev.alternative(M,'Si',T+timedelta(days=151))[0])

    def test_future_evaluation_excludes_pending_and_not_circular(self):
        rows=trades([-1]*40+[1]*40)
        pending=[dict(rows[0],entry=T-timedelta(days=1),available=T+timedelta(days=20),net=-100)]
        got=evaluate_future(rows+pending,T+timedelta(days=41),-1)
        self.assertEqual(got['future20_net'],1);self.assertEqual(got['future_verdict'],'UNRESOLVED')
        got=evaluate_future(trades([1]*40,start=T+timedelta(days=1)),T,-1)
        self.assertEqual(got['future_verdict'],'FALSE')

    def test_no_candidate_is_no_rotation(self):
        ev=evidence({(M,'Si'):trades([-1]*60)})
        # An actual recommendation can be evaluated without inventing alt trades.
        d=dict(strategy=M,instrument='Si',as_of=T+timedelta(days=60),status='NO_EDGE_CONFIRMED',
               alternative=None,w60_net_mean=-1)
        row=rotation_evaluation([d],ev)[0]
        self.assertEqual(row['replacement_verdict'],'NO_CANDIDATE')

    def test_rotation_masks_only_with_confirmed_alternative(self):
        for candidate in (False,True):
            groups={(M,'Si'):trades([-1]*60)}
            if candidate:groups[M,'MIX']=trades([1]*60,'MIX')
            ev=evidence(groups)
            old={(s,m):Track([(T,GOOD)],*bounds) for s,bounds in ev.bounds.items()
                 for m in ('RAW20_CONFIRM5','TWO_BLOCK_20')}
            tracks,_=make_tracks(ev,old)
            t=T+timedelta(days=60)
            self.assertEqual(tracks[M,'Si','EDGE_20_60'].at(t),BAD)
            self.assertEqual(tracks[M,'Si','EDGE_20_60_ROTATION'].at(t)==BAD,candidate)
            if candidate:self.assertEqual(tracks[M,'MIX','EDGE_20_60_ROTATION'].at(t),GOOD)

    def test_weak_truth_requires_two_complete_blocks(self):
        self.assertEqual(weak_periods({(M,'Si'):trades([-1]*39)}),[])
        got=weak_periods({(M,'Si'):trades([-1]*40)})
        self.assertEqual(len(got),1);self.assertEqual(got[0]['blocks'],2)

    def test_month_names_use_start_and_midnight_entry_next_month(self):
        end=datetime(2018,3,1)
        ev=Evidence({},dict(Si=(T,end)))
        tracks={(m,'Si',method):Track([(T,GOOD)],T,end) for m in MODES for method in METHODS}
        raw=[dict(strategy=M,instrument='Si',decision=datetime(2018,2,1),outcome=None)]
        rows=monthly_rows(ev,tracks,[],[],[],[],raw,{m:[] for m in METHODS})
        chosen=[r for r in rows if r['strategy']==M and r['method']=='BASELINE']
        self.assertEqual([r['month'] for r in chosen],['2018-01','2018-02'])
        self.assertEqual([r['raw_signals'] for r in chosen],[0,1])


if __name__=='__main__':unittest.main()
