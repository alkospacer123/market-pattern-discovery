"""Fixed strategy / streaming M15 causality and shared-engine integration."""
from dataclasses import replace
from datetime import date, timedelta
from decimal import Decimal as D
import json
from pathlib import Path
import unittest

from IntradayLab.core.backtester import Backtester
from IntradayLab.core.calendar import MarketRules
from IntradayLab.core.data_loader import validate_bar
from IntradayLab.core.execution import entry_geometry
from IntradayLab.core.m15_context import M15Context, FIVE
from IntradayLab.core.models import Bar, Context
from IntradayLab.strategies.swing_pullback_m5_m15 import SwingPullback, FIXED_PARAMETERS

LAB=Path(__file__).resolve().parents[1]
CFG=json.loads((LAB/'config/swing_pullback_m5_m15_2023_v1.json').read_text())
RULES=MarketRules(CFG)
DAY=date(2023,1,3);T=RULES.at(DAY,'10:00')


def bar(at,o,h,l,c,v=1):
    return validate_bar(at,tuple(D(str(x)) for x in (o,h,l,c,v)),FIVE,D('.01'))


def source(side=1, start=T, n=108):
    out={}
    for i in range(n):
        at=start+i*FIVE
        base=100+i//3 if i<9 else 103.5
        vals=(base,base+1,base-1,base+.5) if i<9 else (base,base+.1,base-.1,base)
        if i==9: vals=(103,103.1,102.4,102.5)
        if i==10: vals=(102.5,102.6,101.8,102)
        if i==11: vals=(102,103.6,101.9,103.5)
        if side==-1:
            o,h,l,c=map(D,map(str,vals));vals=(200-o,200-l,200-h,200-c)
        out[at]=bar(at,*vals)
    return out


def ctx(at,window=None,symbol='USDRUBF'):
    return Context(symbol,at,at+FIVE,window or RULES.windows(at.date())[0],RULES.tick(symbol,at),{})


def feed(raw, end=11, window=None):
    adapter=M15Context();record=None
    for i in range(end+1):
        at=T+i*FIVE;c=ctx(at,window)
        adapter.observe(raw.get(at),c);record=adapter.describe(c)
    return adapter,record


def run(raw):
    strategy=SwingPullback(FIXED_PARAMETERS)
    engine=Backtester(RULES,daily_trade_deadline_clock='17:00')
    return (*engine.run(strategy,'USDRUBF',raw,start=DAY,end_exclusive=DAY+timedelta(days=1)),strategy)


class M15AdapterTests(unittest.TestCase):
    def test_exact_three_aggregation(self):
        a,_=feed(source(),2);p=a.parents[T]
        self.assertEqual((p['open'],p['high'],p['low'],p['close'],p['volume']),tuple(map(D,('100','101','99','100.5','3'))))
        self.assertEqual(p['child_m5_starts'],'10:00,10:05,10:10')
        self.assertEqual(p['closed_at'],T+3*FIVE)
        self.assertEqual(p['available_at'],T+4*FIVE)

    def test_release_not_before_close_plus_five(self):
        raw=source();a,_=feed(raw,8)
        self.assertFalse(a.describe(ctx(T+8*FIVE))['context_valid']) # decision10:45
        a.observe(raw[T+9*FIVE],ctx(T+9*FIVE))
        self.assertTrue(a.describe(ctx(T+9*FIVE))['context_valid']) # decision10:50

    def test_long_three_strict_structures(self):
        _,r=feed(source());self.assertTrue(r['context_valid']);self.assertEqual(r['context_direction'],1)
        self.assertEqual([r[f'p{i}_start'] for i in (1,2,3)],[T,T+3*FIVE,T+6*FIVE])

    def test_short_three_strict_structures(self):
        _,r=feed(source(-1));self.assertEqual(r['context_direction'],-1)

    def test_equal_high_or_low_or_opposite_close_no_trend(self):
        for changes in ({'high':D(102)}, {'low':D(100)}, {'close':D(100)}):
            raw=source()
            for i in range(6,9): raw[T+i*FIVE]=replace(raw[T+i*FIVE],**changes)
            _,r=feed(raw);self.assertEqual(r['context_direction'],0);self.assertEqual(r['context_reason'],'MTF_NO_TREND')

    def test_each_of_nine_missing_children_forbids_context(self):
        for i in range(9):
            raw=source();del raw[T+i*FIVE]
            _,r=feed(raw);self.assertFalse(r['context_valid'])

    def test_invalid_and_zero_volume_child_forbid_parent(self):
        for change in ({'problem':'OFF_HISTORICAL_GRID'},{'volume':D(0)}):
            raw=source();raw[T+FIVE]=replace(raw[T+FIVE],**change)
            a,r=feed(raw);self.assertNotIn(T,a.parents);self.assertFalse(r['context_valid'])

    def test_known_gap_immediately_invalidates_no_stale_fallback(self):
        raw=source();a,r=feed(raw,9);self.assertTrue(r['context_valid'])
        a.observe(None,ctx(T+10*FIVE));r=a.describe(ctx(T+10*FIVE))
        self.assertFalse(r['context_valid']);self.assertFalse(a.parents)
        for i in range(11,20): a.observe(raw[T+i*FIVE],ctx(T+i*FIVE))
        self.assertFalse(a.describe(ctx(T+19*FIVE))['context_valid'])
        a.observe(raw[T+20*FIVE],ctx(T+20*FIVE))
        self.assertFalse(a.describe(ctx(T+20*FIVE))['context_valid'])
        a.observe(raw[T+21*FIVE],ctx(T+21*FIVE))
        self.assertTrue(a.describe(ctx(T+21*FIVE))['context_valid'])

    def test_session_boundary_and_wall_alignment(self):
        start=RULES.at(DAY,'14:05');raw=source(start=start,n=9);a=M15Context();w=RULES.windows(DAY)[1]
        for at,b in raw.items(): a.observe(b,ctx(at,w))
        self.assertNotIn(start,a.parents);self.assertNotIn(RULES.at(DAY,'14:00'),a.parents)
        self.assertEqual(min(a.parents),RULES.at(DAY,'14:15'))
        a.observe(source()[T],ctx(T));self.assertFalse(a.describe(ctx(T))['context_valid'])

    def test_march_extended_lunch(self):
        day=date(2023,3,14);w=RULES.windows(day)[1]
        self.assertEqual(w[0].strftime('%H:%M'),'14:15')
        a=M15Context()
        for at,b in source(start=w[0],n=9).items(): a.observe(b,ctx(at,w))
        self.assertFalse(a.describe(ctx(w[0]+8*FIVE,w))['context_valid'])

    def test_day_and_callback_gap_reset(self):
        a,_=feed(source());at=T+14*FIVE
        a.observe(source()[at],ctx(at));self.assertFalse(a.describe(ctx(at))['context_valid'])
        tomorrow=RULES.at(DAY+timedelta(days=1),'10:00')
        a.observe(bar(tomorrow,100,101,99,100),ctx(tomorrow));self.assertFalse(a.parents)

    def test_reject_uncompleted_unaligned_duration(self):
        for b,c in ((replace(source()[T],duration=2*FIVE),ctx(T)),
                    (source()[T],replace(ctx(T),available_at=T)),
                    (None,ctx(T+timedelta(minutes=1)))):
            with self.assertRaises(ValueError):M15Context().observe(b,c)

    def test_future_completed_but_undelivered_parent_not_selected(self):
        raw=source();raw[T+9*FIVE]=replace(raw[T+9*FIVE],high=D(900))
        _,r=feed(raw);self.assertEqual(r['p3_start'],T+6*FIVE);self.assertEqual(r['context_direction'],1)


class SwingStrategyTests(unittest.TestCase):
    def test_fixed_only_no_parameter_variants(self):
        p=dict(FIXED_PARAMETERS,pullback_bars=3)
        with self.assertRaises(ValueError):SwingPullback(p)

    def test_long_signal_separate_confirmation_structural_stop(self):
        ss,tt,_,strategy=run(source())
        s=next(s for s in ss if s['test_start']==T+11*FIVE)
        self.assertEqual(s['base_reason'],'SIGNAL');self.assertEqual(s['direction'],1)
        self.assertEqual(s['stop'],D('101.79'));self.assertEqual(s['signal_at'],T+12*FIVE)
        self.assertEqual(s['correction_1_start'],T+9*FIVE);self.assertEqual(s['correction_2_start'],T+10*FIVE)
        self.assertEqual(len(strategy.context_records),len(ss))

    def test_short_signal_stop(self):
        ss,tt,_,_=run(source(-1));s=next(s for s in ss if s['test_start']==T+11*FIVE)
        self.assertEqual(s['base_reason'],'SIGNAL');self.assertEqual(s['direction'],-1);self.assertEqual(s['stop'],D('98.21'))

    def test_correction_requires_two_bodies_and_one_tick_close_change(self):
        for i,change in ((9,{'open':D('102.5')}),(10,{'open':D(102)}),(10,{'close':D('102.5')})):
            raw=source();raw[T+i*FIVE]=replace(raw[T+i*FIVE],**change)
            ss,*_=run(raw);s=next(s for s in ss if s['test_start']==T+11*FIVE)
            self.assertEqual(s['base_reason'],'NO_TWO_BAR_PULLBACK')

    def test_signal_body_and_one_tick_break_required(self):
        for change in ({'open':D('103.5')},{'close':D('102.6')}):
            raw=source();raw[T+11*FIVE]=replace(raw[T+11*FIVE],**change)
            ss,*_=run(raw);s=next(s for s in ss if s['test_start']==T+11*FIVE)
            self.assertEqual(s['base_reason'],'NO_CONTINUATION_CONFIRMATION')
        raw=source();raw[T+11*FIVE]=replace(raw[T+11*FIVE],close=D('102.61'))
        ss,*_=run(raw);self.assertEqual(next(s for s in ss if s['test_start']==T+11*FIVE)['base_reason'],'SIGNAL')

    def test_gap_prevents_correction_signal_and_day_state(self):
        raw=source();del raw[T+10*FIVE];ss,tt,*_=run(raw)
        self.assertFalse(any(s['base_reason']=='SIGNAL' for s in ss));self.assertFalse(tt)

    def test_one_full_waiting_bar_then_entry_open(self):
        ss,tt,*_=run(source());q=tt[0]
        self.assertEqual(q['entry_at'],T+13*FIVE)
        self.assertEqual(q['waiting_bar_closed_at'],q['entry_at'])
        self.assertEqual(q['entry_price'],D('103.5'))
        self.assertEqual(q['take']-q['entry_price'],3*q['risk']+D('.08'))
        self.assertEqual(q['planned_net_to_net_R'],D(3))

    def test_entry_no_extra_price_confirmation_and_no_future_trend_recheck(self):
        raw=source();entry=T+13*FIVE
        raw[entry]=bar(entry,102,102.2,101.9,102)
        # New parent10:45 becomes available exactly at entry and is not HH/HL.
        ss,tt,*_=run(raw);q=tt[0]
        self.assertTrue(q['model_filled']);self.assertEqual(q['entry_price'],D(102))
        self.assertLess(q['entry_price'],D('102.6'))

    def test_minimum_risk_four_ticks_and_stop_side(self):
        for op,reason in (('101.82','RISK_BELOW_FOUR_TICKS'),('101.79','INVALID_RISK'),('101.78','INVALID_RISK')):
            raw=source();entry=T+13*FIVE;raw[entry]=bar(entry,op,103.6,101.7,102)
            ss,tt,*_=run(raw);s=next(s for s in ss if s['base_reason']=='SIGNAL')
            self.assertEqual(s['reason'],reason);self.assertFalse(tt)
        raw=source();entry=T+13*FIVE;raw[entry]=bar(entry,101.83,103.6,101.8,102)
        _,tt,*_=run(raw);self.assertTrue(tt[0]['model_filled'])

    def test_missing_waiting_rejects_before_submission(self):
        raw=source();del raw[T+12*FIVE];ss,tt,*_=run(raw)
        s=next(s for s in ss if s['base_reason']=='SIGNAL')
        self.assertEqual(s['reason'],'NO_WAITING_BAR');self.assertFalse(s['order_admitted']);self.assertFalse(tt)

    def test_missing_entry_unknown_possible_fill(self):
        raw=source();del raw[T+13*FIVE];_,tt,*_=run(raw)
        self.assertEqual(tt[0]['status'],'UNKNOWN');self.assertFalse(tt[0]['model_filled'])
        self.assertEqual(tt[0]['unknown_reason'],'MISSING_EXECUTION_BAR');self.assertIsNone(tt[0]['net_R_c1'])

    def test_entry_open_grid_only_future_hlcv_does_not_affect_admission(self):
        raw=source();entry=T+13*FIVE
        raw[entry]=replace(raw[entry],volume=D(0),problem='ZERO_VOLUME')
        _,tt,*_=run(raw);self.assertTrue(tt[0]['model_filled']);self.assertEqual(tt[0]['status'],'UNKNOWN')
        raw[entry]=replace(raw[entry],open=D('103.505'))
        _,tt,*_=run(raw);self.assertFalse(tt[0]['model_filled']);self.assertEqual(tt[0]['unknown_reason'],'INVALID_EXECUTION_OPEN')

    def test_missing_exposed_path_unknown(self):
        raw=source();del raw[T+15*FIVE];_,tt,*_=run(raw)
        self.assertEqual(tt[0]['unknown_reason'],'MISSING_EXPOSED_BAR');self.assertIsNone(tt[0]['net_R_c1'])

    def test_stop_first_and_entry_take_disabled(self):
        raw=source();entry=T+13*FIVE
        raw[entry]=bar(entry,103.5,120,103.4,103.5)
        _,tt,*_=run(raw);self.assertEqual(tt[0]['exit_reason'],'TIME')
        raw[entry+FIVE]=bar(entry+FIVE,103.5,120,101,103.5)
        _,tt,*_=run(raw);self.assertEqual(tt[0]['exit_reason'],'STOP');self.assertTrue(tt[0]['stop_take_conflict'])

    def test_adverse_stop_gap_at_open(self):
        raw=source();at=T+14*FIVE;raw[at]=bar(at,101,101.1,100.9,101)
        _,tt,*_=run(raw);q=tt[0]
        self.assertEqual(q['exit_price'],D(101));self.assertEqual(q['exit_at'],at);self.assertLess(q['realized_net_to_net_R'],-1)

    def test_take_actual_full_net_ratio_distinct_from_standard_R(self):
        raw=source();at=T+14*FIVE;raw[at]=bar(at,103.5,110,103.4,103.5)
        _,tt,*_=run(raw);q=tt[0]
        self.assertEqual(q['exit_reason'],'TAKE');self.assertEqual(q['realized_net_to_net_R'],D(3));self.assertGreater(q['net_R_c1'],3)

    def test_time_session_flat_and_1700(self):
        for start,reason,clock in ((T,'TIME','13:05'),(RULES.at(DAY,'12:00'),'SESSION_FLAT','13:55'),(RULES.at(DAY,'15:00'),'TRADE_DEADLINE','17:00')):
            raw=source(start=start,n=80);_,tt,*_=run(raw);q=tt[0]
            self.assertEqual(q['exit_reason'],reason);self.assertEqual(q['exit_at'],RULES.at(DAY,clock))

    def test_reserve_35_minutes_to_actual_session_flat(self):
        for clock,filled in (('12:15',True),('12:20',False),('15:20',True),('15:25',False)):
            # entry is +65 minutes from fixture start.
            raw=source(start=RULES.at(DAY,clock),n=60);ss,tt,*_=run(raw)
            signals=[s for s in ss if s['base_reason']=='SIGNAL']
            self.assertTrue(signals)
            self.assertEqual(bool(tt),filled)
            if not filled:self.assertEqual(signals[0]['reason'],'SESSION_ENTRY_CUTOFF')

    def test_missing_deadline_open_stays_unknown(self):
        raw=source();del raw[RULES.at(DAY,'13:05')];_,tt,*_=run(raw)
        self.assertEqual(tt[0]['status'],'UNKNOWN');self.assertIsNone(tt[0]['exit_price'])

    def test_future_m5_m15_mutations_leave_original_decision_and_entry(self):
        raw=source();ss,tt,_,s=run(raw)
        other={at:replace(b,high=D(1000),low=D(1),close=D(2)) if at>T+13*FIVE else b for at,b in raw.items()}
        ss2,tt2,_,s2=run(other)
        self.assertEqual([x for x in ss if x['test_start']<=T+11*FIVE],[x for x in ss2 if x['test_start']<=T+11*FIVE])
        self.assertEqual(s.context_records[:12],s2.context_records[:12])
        for k in ('signal_at','entry_at','entry_price','stop','take','risk'):
            self.assertEqual(tt[0][k],tt2[0][k])

    def test_cny_historical_tick_and_three_net_R(self):
        for stamp,grid in (('2023-09-27 16:00','.01'),('2023-09-28 10:00','.001')):
            from datetime import datetime
            at=datetime.fromisoformat(stamp).replace(tzinfo=RULES.zone);t=RULES.tick('CNYRUBF',at)
            self.assertEqual(t,D(grid));risk,take=entry_geometry(D(10),1,D(10)-4*t,t,D(3),target_mode='FULL_NET_C1_R')
            self.assertEqual((take-D(10)-2*t)/(risk+2*t),3);self.assertEqual(take%t,0)


if __name__=='__main__':unittest.main()
