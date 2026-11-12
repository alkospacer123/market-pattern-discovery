"""Calendar boundaries, causal outcomes, restoration and frozen slot replay."""
import unittest
from datetime import datetime,timedelta
from types import SimpleNamespace

from V20_TradingSystem_M15.v20_runtime.calendar_review import (
    shift_month,completion_period,completed_window,rule,effective_at,forward_result,statistics,
    exclusion_episodes,detect_periods,MODES,METHODS,Track,GOOD,BAD,UNKNOWN,ROOT)
from V20_TradingSystem_M15.v20_runtime.calendar_tail_diagnostics import bounds_quality,known_raw,tail_stats
from V20_TradingSystem_M15.v20_runtime.suitability_replay import module,masks

T=datetime(2020,7,1)
M=MODES[0]


def trade(t,net=1,entry=None):
    return dict(strategy=M,instrument='Si',contract='Si',entry=entry or t-timedelta(days=1),
        available=t,exit=t,signal=t-timedelta(days=1,minutes=15),net=net,gross=net+.1,
        stop=net<0,reason=1 if net<0 else 3,session_span=1)


def window(net,n=10,sufficient=True):return dict(net_R=net,n=n,sufficient=sufficient)


class CalendarTests(unittest.TestCase):
    def test_calendar_month_arithmetic(self):
        self.assertEqual(shift_month(datetime(2020,1,1),-3),datetime(2019,10,1))
        self.assertEqual(shift_month(datetime(2020,7,1),6),datetime(2021,1,1))

    def test_midnight_result_has_same_month_in_windows_and_yearly_tables(self):
        self.assertEqual(completion_period(datetime(2021,1,1)).strftime('%Y-%m'),'2020-12')
        self.assertEqual(completion_period(datetime(2021,1,1,0,15)).strftime('%Y-%m'),'2021-01')

    def test_completed_boundary_and_future_poison(self):
        class Poison:
            def __add__(self,other):raise AssertionError('future result used')
        rows=[trade(shift_month(T,-3),1000)]+[trade(T-timedelta(days=i),1) for i in range(10)]
        rows.append(dict(trade(T+timedelta(minutes=15)),net=Poison(),gross=Poison()))
        w=completed_window(rows,T,3,datetime(2018,1,1))
        self.assertEqual(w['n'],10);self.assertEqual(w['net_R'],10);self.assertTrue(w['sufficient'])

    def test_insufficient_history_even_if_ten_trades(self):
        rows=[trade(T-timedelta(days=i)) for i in range(10)]
        self.assertFalse(completed_window(rows,T,3,datetime(2020,5,1))['sufficient'])

    def test_completed_trade_does_not_parse_unfinished_raw_path(self):
        rows=[dict(trade(T-timedelta(days=i)),path=dict(available=str(T+timedelta(days=2)),fp2=object())) for i in range(10)]
        w=completed_window(rows,T,3,datetime(2018,1,1))
        self.assertEqual(w['n'],10);self.assertEqual(w['net_R'],10)

    def test_minimum_is_not_optimized(self):
        for months,n in ((3,10),(6,20)):
            rows=[trade(T-timedelta(days=i)) for i in range(n-1)]
            self.assertFalse(completed_window(rows,T,months,datetime(2018,1,1))['sufficient'])

    def test_quarter_and_half_rules_sign(self):
        self.assertEqual(rule('QUARTER_3M',window(-1),window(100)),('EXCLUDE',True))
        self.assertEqual(rule('HALF_YEAR_6M',window(-1),window(100)),('GOOD',False))
        self.assertEqual(rule('QUARTER_3M',window(0),window(-1)),('NEUTRAL',False))

    def test_combination_warning_without_exclusion(self):
        self.assertEqual(rule('QUARTER_3M_6M',window(-1),window(2)),('WARNING',False))
        self.assertEqual(rule('QUARTER_3M_6M',window(-1),window(-2)),('EXCLUDE',True))

    def test_combination_recovers_on_positive_quarter_only(self):
        self.assertEqual(rule('QUARTER_3M_6M',window(1),window(-2),True),('RECOVERED',False))
        self.assertEqual(rule('QUARTER_3M_6M',window(0),window(2),True),('EXCLUDE_PENDING_RECOVERY',True))

    def test_insufficient_status_is_distinct_from_carried_action(self):
        self.assertEqual(rule('QUARTER_3M_6M',window(-1,sufficient=False),window(-2),True),('INSUFFICIENT',True))
        self.assertEqual(rule('QUARTER_3M',window(-1,sufficient=False),window(-2),True),('INSUFFICIENT',False))

    def test_effect_uses_first_observed_session_not_monthend(self):
        clocks={'Si':[T+timedelta(days=2,hours=10),T+timedelta(days=3,hours=10)]}
        self.assertEqual(effective_at(clocks,'Si',T),T+timedelta(days=2,hours=10))
        self.assertIsNone(effective_at(clocks,'Si',T+timedelta(days=4)))

    def test_next_quarter_partial_or_censored_unresolved(self):
        rows=[trade(T+timedelta(days=i+1)) for i in range(10)]
        self.assertEqual(forward_result(rows,T,3,(T,T+timedelta(days=89)),[],10)['verdict'],'UNRESOLVED')
        self.assertEqual(forward_result(rows,T,3,(T,T+timedelta(days=100)),[],10)['verdict'],'FALSE')
        self.assertEqual(forward_result(rows,T,3,(T,T+timedelta(days=100)),[dict(entry=T,available=T+timedelta(days=1))],10)['verdict'],'UNRESOLVED')

    def test_pending_result_counts_but_is_not_new_entry(self):
        rows=[trade(T+timedelta(days=i+1),entry=T-timedelta(days=1)) for i in range(10)]
        r=forward_result(rows,T,3,(T,T+timedelta(days=100)),[],10)
        self.assertEqual(r['pending_at_decision'],10)
        self.assertFalse(any(r['entry']>=T for r in rows))

    def test_episode_count_does_not_count_repeat_review_twice(self):
        end=shift_month(T,6);mid=shift_month(T,3)
        track=Track([(T,BAD),(mid,BAD),(end,GOOD)],T,end+timedelta(days=1))
        reviews=[dict(strategy=M,instrument='Si',method='QUARTER_3M',decision_at=t,effective_at=t,
            assessment='EXCLUDE' if t<end else 'GOOD',action='EXCLUDE' if t<end else 'ALLOW',next_q_verdict='FALSE') for t in (T,mid,end)]
        rows=[trade(t+timedelta(days=1),entry=t+timedelta(hours=10)) for t in (T,mid)]
        e=exclusion_episodes(reviews,{(M,'Si','QUARTER_3M'):track},{(M,'Si'):rows})
        self.assertEqual(len(e),1);self.assertEqual(e[0]['lost_positive_R'],2)
        self.assertEqual(sum(r.get('lost_positive_R',0) for r in reviews),2)

    def test_multi_account_dd_is_not_portfolio_money(self):
        rows=[trade(T,-1),dict(trade(T,2),strategy=MODES[1])]
        self.assertIsNone(statistics(rows)['DD_closed_R'])

    def test_expired_overnight_exclusion_is_not_timely_detection(self):
        first=T+timedelta(hours=10);later=shift_month(T,3)+timedelta(hours=10);end=shift_month(T,6)
        track=Track([(T,BAD),(first,GOOD),(later,BAD)],T,end)
        tracks={(M,'Si',m):track for m in METHODS}
        result=detect_periods([dict(strategy=M,instrument='Si',start=T,end=end)],tracks,{},dict(Si=[first,later]))
        self.assertTrue(all(r['detected_at']==later for r in result))

    def test_fp4_stop_same_bar_is_conservative(self):
        r=bounds_quality(dict(mfe_low='2',mfe_high='5'))
        self.assertEqual((r['fp4'],r['amb4']),(0,1))
        r=bounds_quality(dict(mfe_low='4',mfe_high='4'))
        self.assertEqual((r['fp4'],r['amb4']),(1,0))

    def test_strict_beyond_five_and_model_profit_are_different(self):
        r=bounds_quality(dict(mfe_low='5',mfe_high='5'))
        self.assertEqual(r['beyond5'],0)
        event=dict(mfe_low='6',mfe_high='6',fp2=1,fp3=1,fp5=1,amb2=0,amb3=0,amb5=0,stop_touch='False')
        q=tail_stats([dict(outcome=event)],[trade(T,.1)])
        self.assertEqual(q['FP5'],1);self.assertEqual(q['actual_net_ge5_n'],0)

    def test_tail_availability_precedes_numerical_parse(self):
        rows=[dict(outcome=dict(available=str(T+timedelta(days=1)),mfe_low=object()))]
        q=tail_stats(known_raw(rows,T),[])
        self.assertEqual(q['raw_observed'],0);self.assertEqual(q['raw_censored'],1)

    def test_original_replay_freed_daily_slot_differs_from_row_deletion(self):
        import pandas as pd,numpy as np,math
        from collections import defaultdict
        b=module(ROOT/'V20-03/comparison/build_diagnostics.py')
        path=ROOT/'V20-02_AUDIT/replay_independent.py'
        syms=['CNYRUBF','GLDRUBF','IMOEXF','USDRUBF']
        ticks={'CNYRUBF':.001,'GLDRUBF':.1,'IMOEXF':.5,'USDRUBF':.01}
        engine=b.fn(path,'run_one',dict(pd=pd,np=np,math=math,defaultdict=defaultdict,SYMS=syms,TICKS=ticks,COLS=b.lit(path,'COLS')))
        dates=[datetime(2020,7,day,10)+timedelta(minutes=15*i) for day in (1,2,3) for i in range(4)]
        frames={}
        for symbol in syms:
            d=pd.DataFrame(dict(Datetime=dates,Open=100.,High=100.01,Low=99.99,atr=.1))
            d['day']=d.Datetime.dt.normalize()
            for mode in MODES:d[mode]=0
            if symbol in ('CNYRUBF','GLDRUBF'):d.loc[0,M]=1
            if symbol=='USDRUBF':d.loc[1,M]=1
            frames[symbol]=d
        before={s:d[M].copy() for s,d in frames.items()}
        base,_=engine(frames,1,M,M)
        tracks={(mode,s,'TEST'):Track([(dates[0],BAD if s=='CNYRUBF' else GOOD)],dates[0],dates[-1]+timedelta(days=1)) for mode in MODES for s in syms}
        masked,_=masks(frames,'TEST',tracks,True)
        after,_=engine(masked,1,M,M)
        self.assertEqual(list(base.symbol),['CNYRUBF','GLDRUBF'])
        self.assertEqual(list(after.symbol),['GLDRUBF','USDRUBF'])
        self.assertEqual(len(base[base.symbol!='CNYRUBF']),1);self.assertEqual(len(after),2)
        for s in syms:pd.testing.assert_series_equal(frames[s][M],before[s])


if __name__=='__main__':unittest.main()
