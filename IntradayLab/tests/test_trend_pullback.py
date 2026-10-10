"""Synthetic causal/clock/unknown contracts, fixed before market returns."""
from copy import deepcopy
from dataclasses import replace
from datetime import date, timedelta
from decimal import Decimal as D
import json
from pathlib import Path
import unittest

from IntradayLab.core.backtester import Backtester
from IntradayLab.core.calendar import MarketRules
from IntradayLab.core.data_loader import validate_bar
from IntradayLab.core.models import Context
from IntradayLab.core.m15_bars import aggregate_m15, full_slots, FIVE, FIFTEEN
from IntradayLab.core.h1_context import H1Context
from IntradayLab.strategies.trend_pullback_m15_h1 import TrendPullback, FIXED_PARAMETERS
from IntradayLab.tools.run_trend_pullback_baseline import reachability
from IntradayLab.tools.audit_trend_pullback_baseline import parent_rows, episodes, replay, check_rows

LAB=Path(__file__).resolve().parents[1]
CFG=json.loads((LAB/'config/trend_pullback_m15_h1_2023_v1.json').read_text())
RULES=MarketRules(CFG);DAY=date(2023,1,3);T=RULES.at(DAY,'10:00')


def source(side=1,day=DAY):
    raw={}
    for w in RULES.windows(day):
        for at in full_slots(w):
            i=int((at-RULES.at(day,'10:00'))/FIFTEEN)
            values=(100+i,101+i,99+i,100.5+i) if i<3 else (105,105.1,104.9,105)
            if i==3: values=(104,104.1,102.9,103)
            if i==4: values=(103,105.1,102.9,105)
            vals=tuple(D(str(x)) for x in values)
            if side==-1:
                o,h,l,c=vals;vals=(200-o,200-l,200-h,200-c)
            for j in range(3):
                t=at+j*FIVE;raw[t]=validate_bar(t,(*vals,D(1)),FIVE,D('.01'))
    return raw


def run(raw,day=DAY,strategy=None):
    parents,diag=aggregate_m15(raw,RULES,day,day+timedelta(days=1))
    strategy=strategy or TrendPullback(FIXED_PARAMETERS)
    ss,tt,dd=Backtester(RULES,timeframe_minutes=15,daily_trade_deadline_clock='17:00').run(
        strategy,'USDRUBF',parents,start=day,end_exclusive=day+timedelta(days=1))
    return ss,tt,dd,strategy


def ctx(at,window=None):
    return Context('USDRUBF',at,at+FIFTEEN,window or RULES.windows(at.date())[0],D('.01'),{})


def set_parent(raw,at,values):
    for i in range(3):
        t=at+i*FIVE;raw[t]=validate_bar(t,tuple(D(str(x)) for x in (*values,1)),FIVE,D('.01'))


class AggregationTests(unittest.TestCase):
    def test_exact_three_ohlcv(self):
        raw=source();p,d=aggregate_m15(raw,RULES,DAY,DAY+timedelta(days=1));bs=[raw[T+i*FIVE] for i in range(3)]
        self.assertEqual((p[T].open,p[T].high,p[T].low,p[T].close,p[T].volume),
            (bs[0].open,max(b.high for b in bs),min(b.low for b in bs),bs[-1].close,D(3)))
        self.assertEqual(p[T].duration,FIFTEEN)

    def test_every_missing_child_invalid_no_fabricated_path(self):
        for i in range(3):
            raw=source();del raw[T+i*FIVE];p,d=aggregate_m15(raw,RULES,DAY,DAY+timedelta(days=1))
            self.assertFalse(next(r for r in d if r['start']==T)['valid'])
            if i==0: self.assertNotIn(T,p)
            else:
                self.assertFalse(p[T].valid);self.assertEqual(p[T].open,D(100));self.assertTrue(p[T].high.is_nan())
                self.assertTrue(p[T].low.is_nan());self.assertTrue(p[T].close.is_nan())

    def test_invalid_child_blocks(self):
        raw=source();raw[T+FIVE]=replace(raw[T+FIVE],problem='ZERO_VOLUME',volume=D(0))
        p,_=aggregate_m15(raw,RULES,DAY,DAY+timedelta(days=1));self.assertFalse(p[T].valid)

    def test_msk_quarter_grid_no_session_partial(self):
        p,_=aggregate_m15(source(),RULES,DAY,DAY+timedelta(days=1))
        self.assertTrue(all(at.minute%15==0 and str(at.utcoffset())=='3:00:00' for at in p))
        self.assertNotIn(RULES.at(DAY,'14:00'),p);self.assertNotIn(RULES.at(DAY,'14:05'),p)
        self.assertIn(RULES.at(DAY,'14:15'),p);self.assertNotIn(RULES.at(DAY,'18:45'),p)

    def test_march_windows(self):
        day=date(2023,3,14);p,_=aggregate_m15(source(day=day),RULES,day,day+timedelta(days=1))
        self.assertEqual(RULES.windows(day)[1][0].strftime('%H:%M'),'14:15');self.assertIn(RULES.at(day,'14:15'),p)

    def test_future_duration_alignment_rejected(self):
        for raw in ({T:replace(source()[T],duration=FIFTEEN)},
                    {T+timedelta(minutes=1):replace(source()[T],start=T+timedelta(minutes=1))},
                    {RULES.at(date(2024,1,1),'10:00'):replace(source()[T],start=RULES.at(date(2024,1,1),'10:00'))}):
            with self.assertRaises(ValueError):aggregate_m15(raw,RULES,DAY,date(2024,1,1))


class H1Tests(unittest.TestCase):
    def feed(self,raw,n=5):
        p,_=aggregate_m15(raw,RULES,DAY,DAY+timedelta(days=1));a=H1Context()
        for i in range(n): a.observe(p.get(T+i*FIFTEEN),ctx(T+i*FIFTEEN))
        return a,p

    def test_exact_four_and_12_lineage(self):
        a,p=self.feed(source());r=a.describe(ctx(T+4*FIFTEEN))
        self.assertTrue(r['context_valid']);self.assertEqual(r['h1_open'],D(100));self.assertEqual(r['h1_close'],D(103))
        self.assertEqual(r['h1_volume'],D(12));self.assertEqual(len(r['child_m15_starts'].split(',')),4)
        self.assertEqual(len(r['child_m5_starts'].split(',')),12)

    def test_delivery_not_before_close_plus_five(self):
        a,p=self.feed(source(),4)
        for minute in (60,64): self.assertFalse(a.describe(replace(ctx(T),available_at=T+timedelta(minutes=minute)))['context_valid'])
        self.assertTrue(a.describe(replace(ctx(T),available_at=T+timedelta(minutes=65)))['context_valid'])

    def test_each_missing_of_twelve_blocks_h1(self):
        for i in range(12):
            raw=source();del raw[T+i*FIVE];a,_=self.feed(raw)
            self.assertFalse(a.describe(ctx(T+4*FIFTEEN))['context_valid'])

    def test_gap_immediately_blocks_old_context_then_recovers(self):
        raw=source();del raw[T+timedelta(minutes=80)];a,p=self.feed(raw,6)
        self.assertFalse(a.describe(ctx(T+5*FIFTEEN))['context_valid'])
        for i in range(6,12):a.observe(p.get(T+i*FIFTEEN),ctx(T+i*FIFTEEN))
        self.assertFalse(a.describe(ctx(T+11*FIFTEEN))['context_valid'])
        a.observe(p[T+12*FIFTEEN],ctx(T+12*FIFTEEN));self.assertTrue(a.describe(ctx(T+12*FIFTEEN))['context_valid'])

    def test_latest_incomplete_no_stale_substitute(self):
        raw=source();del raw[T+timedelta(minutes=80)];a,p=self.feed(raw,9)
        r=a.describe(ctx(T+8*FIFTEEN));self.assertEqual(r['h1_start'],T+timedelta(hours=1));self.assertFalse(r['context_valid'])
        self.assertIsNone(r['h1_open'])

    def test_day_session_reset_no_morning_carry(self):
        a,p=self.feed(source());pm=RULES.at(DAY,'14:15');a.observe(p[pm],ctx(pm,RULES.windows(DAY)[1]))
        self.assertFalse(a.describe(ctx(pm,RULES.windows(DAY)[1]))['context_valid']);self.assertFalse(a.parents)

    def test_doiji_has_no_direction(self):
        raw=source();set_parent(raw,T+3*FIFTEEN,(100,101,99,100));a,_=self.feed(raw)
        r=a.describe(ctx(T+4*FIFTEEN));self.assertTrue(r['context_valid']);self.assertEqual(r['context_direction'],0)

    def test_uncompleted_input_rejected(self):
        with self.assertRaises(ValueError): H1Context().observe(None,replace(ctx(T),available_at=T))


class StrategyExecutionTests(unittest.TestCase):
    def signal(self,ss):return next(s for s in ss if s['test_start']==T+4*FIFTEEN)

    def test_only_fixed_parameters_and_two_allowed_timeframes(self):
        with self.assertRaises(ValueError):TrendPullback(dict(FIXED_PARAMETERS,pullback_bars=2))
        with self.assertRaises(ValueError):Backtester(RULES,timeframe_minutes=30)
        Backtester(RULES,timeframe_minutes=5);Backtester(RULES,timeframe_minutes=15)

    def test_long_one_correction_separate_confirmation_stop(self):
        ss,tt,_,s=run(source());r=self.signal(ss)
        self.assertEqual(r['base_reason'],'SIGNAL');self.assertEqual(r['direction'],1)
        self.assertEqual(r['correction_start'],T+3*FIFTEEN);self.assertEqual(r['stop'],D('102.89'))
        self.assertEqual(r['signal_at'],T+5*FIFTEEN);self.assertEqual(len(s.context_records),len(ss))

    def test_short(self):
        ss,tt,*_=run(source(-1));r=self.signal(ss)
        self.assertEqual(r['base_reason'],'SIGNAL');self.assertEqual(r['direction'],-1);self.assertEqual(r['stop'],D('97.11'))

    def test_signal_body_and_tick_close_threshold(self):
        for vals in ((105,105.1,102.9,105),(103,104.1,102.9,104.1)):
            raw=source();set_parent(raw,T+4*FIFTEEN,vals);ss,*_=run(raw)
            self.assertEqual(self.signal(ss)['base_reason'],'NO_M15_CONTINUATION')
        raw=source();set_parent(raw,T+4*FIFTEEN,(103,104.11,102.9,104.11));ss,*_=run(raw)
        self.assertEqual(self.signal(ss)['base_reason'],'SIGNAL')

    def test_opposite_correction_required(self):
        raw=source();set_parent(raw,T+3*FIFTEEN,(103,104.1,102.9,103));ss,*_=run(raw)
        self.assertEqual(self.signal(ss)['base_reason'],'NO_M15_CORRECTION')

    def test_signal_wait_one_full_m15_then_open(self):
        _,tt,*_=run(source());q=tt[0]
        self.assertEqual(q['signal_at'],RULES.at(DAY,'11:15'));self.assertEqual(q['entry_at'],RULES.at(DAY,'11:30'))
        self.assertEqual(q['waiting_bar_closed_at'],q['entry_at']);self.assertEqual(q['entry_price'],D(105))
        self.assertEqual(q['take']-q['entry_price'],3*q['risk']+D('.08'));self.assertEqual(q['planned_net_to_net_R'],D(3))

    def test_missing_waiting_no_order(self):
        raw=source();del raw[T+5*FIFTEEN+FIVE];ss,tt,*_=run(raw)
        self.assertEqual(self.signal(ss)['reason'],'NO_WAITING_BAR');self.assertFalse(tt)

    def test_known_open_incomplete_entry_filled_then_unknown(self):
        for i in (1,2):
            raw=source();del raw[T+6*FIFTEEN+i*FIVE];_,tt,*_=run(raw)
            self.assertTrue(tt[0]['model_filled']);self.assertEqual(tt[0]['entry_price'],D(105))
            self.assertEqual(tt[0]['status'],'UNKNOWN');self.assertIsNone(tt[0]['net_R_c1'])
            self.assertEqual(tt[0]['unknown_reason'],'INVALID_EXPOSED_BAR')

    def test_missing_first_open_unknown_possible_fill(self):
        raw=source();del raw[T+6*FIFTEEN];_,tt,*_=run(raw)
        self.assertFalse(tt[0]['model_filled']);self.assertEqual(tt[0]['unknown_reason'],'MISSING_EXECUTION_BAR')
        self.assertIsNone(tt[0]['entry_price']);self.assertIsNone(tt[0]['net_R_c1'])

    def test_four_tick_risk_and_wrong_stop_side(self):
        for op,reason in ((102.92,'RISK_BELOW_FOUR_TICKS'),(102.89,'INVALID_RISK'),(102.88,'INVALID_RISK')):
            raw=source();set_parent(raw,T+6*FIFTEEN,(op,105.1,102.8,105));ss,tt,*_=run(raw)
            self.assertEqual(self.signal(ss)['reason'],reason);self.assertFalse(tt)
        raw=source();set_parent(raw,T+6*FIFTEEN,(102.93,105.1,102.9,105));_,tt,*_=run(raw);self.assertTrue(tt[0]['model_filled'])

    def test_stop_first_and_entry_take_disabled(self):
        raw=source();set_parent(raw,T+6*FIFTEEN,(105,120,104.9,105));_,tt,*_=run(raw)
        self.assertEqual(tt[0]['exit_reason'],'TIME')
        set_parent(raw,T+7*FIFTEEN,(105,120,100,105));_,tt,*_=run(raw)
        self.assertEqual(tt[0]['exit_reason'],'STOP');self.assertTrue(tt[0]['stop_take_conflict'])

    def test_adverse_stop_gap(self):
        raw=source();set_parent(raw,T+7*FIFTEEN,(101,102,100,101));_,tt,*_=run(raw)
        self.assertEqual(tt[0]['exit_reason'],'STOP');self.assertEqual(tt[0]['exit_price'],D(101))
        self.assertEqual(tt[0]['exit_at'],T+7*FIFTEEN)

    def test_take_fully_net_three_r(self):
        raw=source();set_parent(raw,T+7*FIFTEEN,(105,120,104.9,105));_,tt,*_=run(raw)
        self.assertEqual(tt[0]['exit_reason'],'TAKE');self.assertEqual(tt[0]['realized_net_to_net_R'],D(3))
        self.assertGreater(tt[0]['net_R_c1'],3)

    def test_time_max_120(self):
        _,tt,*_=run(source());self.assertEqual(tt[0]['exit_reason'],'TIME')
        self.assertEqual(tt[0]['exit_at']-tt[0]['entry_at'],timedelta(minutes=120))

    def test_no_future_context_recheck_or_stop_change(self):
        raw=source();a=run(raw)[0];set_parent(raw,T+5*FIFTEEN,(105,500,104.9,105))
        b=run(raw)[0];self.assertEqual(self.signal(a),self.signal(b))

    def test_future_mutations_do_not_change_past_decisions(self):
        raw=source();a=run(raw)[3].context_records;cut=T+5*FIFTEEN
        changed={t:(replace(b,high=D(900),close=D(1),problem='FUTURE') if t>=cut else b) for t,b in raw.items()}
        c=run(changed)[3].context_records
        self.assertEqual([s for s in a if s['signal_decision_at']<=cut],[s for s in c if s['signal_decision_at']<=cut])

    def test_cny_historical_transition(self):
        self.assertEqual(RULES.tick('CNYRUBF',RULES.at(date(2023,9,27),'18:55')),D('.01'))
        self.assertEqual(RULES.tick('CNYRUBF',RULES.at(date(2023,9,27),'19:00')),D('.001'))

    def test_calendar_pm_impossible(self):
        r=reachability(CFG,RULES);self.assertTrue(r['PM_structurally_impossible']);self.assertEqual(r['PM_admissible_slots'],0)
        self.assertEqual(r['AM_slots_per_day'],['11:30','11:45','12:00','12:15','12:30','12:45','13:00'])

    def test_session_flat_and_1700_on_m15_opens(self):
        class Scheduled:
            name='SYNTHETIC'
            def __init__(self,clock):self.clock=clock
            def begin_day(self,symbol,day):pass
            def end_day(self):return []
            def on_bar(self,b,c):
                return [dict(signal_id=str(c.available_at),base_reason='SIGNAL',signal_at=c.available_at,
                    direction=1,stop=D(90),target_gross_R=D(3),max_hold_calendar_minutes=120,
                    entry_constraints=dict(minimum_risk_ticks=4,reserve_minutes=35))] if c.available_at.strftime('%H:%M')==self.clock else []
        for clock,exit_clock,reason in (('12:45','13:45','SESSION_FLAT'),('16:00','17:00','TRADE_DEADLINE')):
            _,tt,*_=run(source(),strategy=Scheduled(clock));self.assertEqual(tt[0]['exit_at'],RULES.at(DAY,exit_clock));self.assertEqual(tt[0]['exit_reason'],reason)

    def test_independent_raw_oracle_signals_paths_and_economics(self):
        raw=source();ss,tt,*_=run(raw);tuples={t:(b.open,b.high,b.low,b.close,b.volume) for t,b in raw.items()}
        p=parent_rows('USDRUBF',tuples);ev=episodes('USDRUBF',p);ev=[s for s in ev if s['date']==str(DAY)]
        a,b=replay('USDRUBF',p,ev)
        def serialized(rows):return [{k:str(v) if v is not None else '' for k,v in r.items()} for r in rows]
        check_rows(serialized(ss),a,('signal_id','base_reason','stop','status','reason','model_filled'),'SIGNALS')
        check_rows(serialized(tt),b,('entry_at','entry_price','exit_at','exit_price','net_R_c1','realized_net_to_net_R'),'TRADES')


if __name__=='__main__':unittest.main()
