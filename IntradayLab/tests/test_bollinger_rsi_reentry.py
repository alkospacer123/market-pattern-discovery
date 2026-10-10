"""Pre-P&L synthetic Bollinger/Wilder, causal B/C and shared M15 execution tests."""
from copy import deepcopy
from dataclasses import replace
from datetime import date, timedelta
from decimal import Decimal as D
from fractions import Fraction
import hashlib
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from IntradayLab.core.backtester import Backtester
from IntradayLab.core.calendar import MarketRules
from IntradayLab.core.data_loader import validate_bar, load_market_data
from IntradayLab.core.models import Bar, Context
from IntradayLab.core.m15_bars import aggregate_m15, full_slots, FIVE, FIFTEEN
from IntradayLab.core.reports import csv_write
from IntradayLab.strategies.bollinger_rsi_reentry_m15 import CompletedIndicators, BollingerRSIReentry, FIXED_PARAMETERS
from IntradayLab.tools.audit_bollinger_rsi_reentry_baseline import parent_rows, episodes, replay, batch_indicators, read_csv, check_rows
from IntradayLab.tools.run_bollinger_rsi_reentry_baseline import reachability

LAB=Path(__file__).resolve().parents[1]
CFG=json.loads((LAB/'config/bollinger_rsi_reentry_m15_2023_v1.json').read_text())
RULES=MarketRules(CFG);PRE=date(2023,1,3);DAY=date(2023,1,4)
T=RULES.at(DAY,'10:00');B=T+2*FIFTEEN;C=B+FIFTEEN;SIGNAL=C+FIFTEEN;ENTRY=SIGNAL+FIFTEEN


def source(side=1):
    raw={}
    for day in (PRE,DAY):
        for w in RULES.windows(day):
            for at in full_slots(w):
                vals=(100,100.1,99.9,100)
                if day==DAY and at>=B:vals=(95,95.1,94.9,95)
                if at==B:vals=(100,100,90,90)
                if at==C:vals=(90,95,90,95)
                vals=tuple(D(str(x)) for x in vals)
                if side==-1:
                    o,h,l,c=vals;vals=(200-o,200-l,200-h,200-c)
                for i in range(3):
                    t=at+i*FIVE;raw[t]=validate_bar(t,(*vals,D(1)),FIVE,D('.01'))
    return raw


def set_parent(raw,at,values):
    for i in range(3):
        t=at+i*FIVE;raw[t]=validate_bar(t,tuple(D(str(x)) for x in (*values,1)),FIVE,D('.01'))


def run(raw,strategy=None):
    p,_=aggregate_m15(raw,RULES,PRE,DAY+timedelta(days=1))
    return Backtester(RULES,timeframe_minutes=15,daily_trade_deadline_clock='17:00').run(
        strategy or BollingerRSIReentry(FIXED_PARAMETERS),'USDRUBF',p,start=PRE,end_exclusive=DAY+timedelta(days=1))


def signal(ss):return next(s for s in ss if s['test_start']==C)


def ctx(at,window=None):
    return Context('USDRUBF',at,at+FIFTEEN,window or RULES.windows(at.date())[0],D('.01'),{})


class IndicatorTests(unittest.TestCase):
    def test_population_bollinger_exact_twenty_manual(self):
        a=CompletedIndicators()
        for x in range(1,21):r=a.observe(D(x))
        self.assertEqual(r['sma20'],D('10.5'));self.assertEqual(r['population_sigma'],D('33.25').sqrt())
        self.assertEqual(r['lower_band'],D('10.5')-2*D('33.25').sqrt())
        self.assertEqual(r['upper_band'],D('10.5')+2*D('33.25').sqrt())
        r=a.observe(D(21));self.assertEqual(r['sma20'],D('11.5'))

    def test_wilder_manual_seed_and_following_changes(self):
        closes=[D(100+i%2) for i in range(15)]+[D(102),D(99)]
        a=CompletedIndicators();values=[a.observe(x)['rsi14'] for x in closes]
        self.assertTrue(all(x is None for x in values[:14]));self.assertEqual(values[14],D(50))
        for index,fraction in ((15,Fraction(170,3)),(16,Fraction(11050,237))):
            expected=D(fraction.numerator)/D(fraction.denominator)
            self.assertLess(abs(values[index]-expected),D('1e-24'))

    def test_wilder_classic_published_manual_seed(self):
        closes=list(map(D,['44.34','44.09','44.15','43.61','44.33','44.83','45.10','45.42','45.84','46.08','45.89','46.03','45.61','46.28','46.28','46.00']))
        a=CompletedIndicators();r=[a.observe(x) for x in closes]
        expected=D(100)-D(100)/(1+D('3.34')/D('1.40'))
        self.assertLess(abs(r[14]['rsi14']-expected),D('1e-24'))
        expected_next=D(100)*D('3.34')*13/(D('3.34')*13+D('1.40')*13+D('.28')*14)
        self.assertLess(abs(r[15]['rsi14']-expected_next),D('1e-24'))

    def test_zero_cases_deterministic(self):
        for values,expected in (([100]*20,50),(list(range(100,120)),100),(list(range(120,100,-1)),0)):
            a=CompletedIndicators();r=[a.observe(D(x)) for x in values]
            self.assertEqual(r[-1]['rsi14'],D(expected))

    def test_full_twenty_warmup_no_partial_sma(self):
        a=CompletedIndicators()
        for i in range(19):self.assertFalse(a.observe(D(100+i))['indicators_ready'])
        self.assertTrue(a.observe(D(119))['indicators_ready'])

    def test_independent_weighted_expansion_and_future_suffix(self):
        values=[D(100)+(D(i*i%17)/100) for i in range(60)]
        expected=batch_indicators(values);a=CompletedIndicators()
        for x,e in zip(values,expected):
            r=a.observe(x)
            for k in ('sma20','population_sigma','lower_band','upper_band','rsi14'):
                if e[k] is None:self.assertIsNone(r[k])
                else:self.assertLess(abs(r[k]-e[k]),D('1e-22'))
        self.assertEqual(expected[:30],batch_indicators(values[:30]+[D(1)]*30)[:30])

    def test_no_signal_before_complete_warmup(self):
        raw={t:b for t,b in source().items() if t.date()==DAY}
        ss,tt,_=run(raw)
        self.assertFalse(tt);self.assertEqual(signal(ss)['base_reason'],'INDICATORS_NOT_READY')

    def test_real_prior_sessions_warm_without_synthetic_breaks(self):
        ss,_,_=run(source());r=signal(ss)
        self.assertEqual(r['base_reason'],'SIGNAL');self.assertEqual(r['change_count'],37)
        self.assertEqual(r['close_count'],20)

    def test_gap_and_incomplete_clear_entire_warmup(self):
        for offset in (0,5,10):
            raw=source();del raw[T+timedelta(minutes=offset)]
            ss,tt,_=run(raw);self.assertEqual(signal(ss)['base_reason'],'INDICATORS_NOT_READY');self.assertFalse(tt)

    def test_missing_full_research_day_resets(self):
        raw=source();day=date(2023,1,6)
        raw.update({t+timedelta(days=2):replace(b,start=t+timedelta(days=2)) for t,b in raw.copy().items() if t.date()==DAY})
        p,_=aggregate_m15(raw,RULES,PRE,day+timedelta(days=1))
        ss,_,_=Backtester(RULES,timeframe_minutes=15,daily_trade_deadline_clock='17:00').run(BollingerRSIReentry(FIXED_PARAMETERS),'USDRUBF',p,start=PRE,end_exclusive=day+timedelta(days=1))
        self.assertEqual(next(s for s in ss if s['test_start']==C+timedelta(days=2))['base_reason'],'INDICATORS_NOT_READY')

    def test_gap_recovery_requires_twenty_new_real_closes(self):
        raw=source();del raw[T]
        ss,_,_=run(raw)
        after=[s for s in ss if s['test_start']>T and s.get('indicators_ready') is not None]
        self.assertTrue(all(not s['indicators_ready'] for s in after[:19]))
        self.assertTrue(after[19]['indicators_ready']);self.assertEqual(after[19]['change_count'],19)

    def test_invalid_close_rejected(self):
        for x in ('NaN','0','-1'):
            with self.assertRaises(ValueError):CompletedIndicators().observe(D(x))


class CausalSignalTests(unittest.TestCase):
    def test_only_fixed_parameters(self):
        with self.assertRaises(ValueError):BollingerRSIReentry(dict(FIXED_PARAMETERS,rsi_period=15))

    def test_long_reentry_own_bands_rsi_and_fixed_stop(self):
        r=signal(run(source())[0]);self.assertEqual(r['direction'],1);self.assertEqual(r['stop'],D('89.99'))
        self.assertLess(r['breach_close'],r['breach_lower_band']);self.assertLessEqual(r['breach_rsi14'],35)
        self.assertGreater(r['rsi14'],r['breach_rsi14']);self.assertGreaterEqual(r['test_close'],r['lower_band'])
        self.assertLessEqual(r['test_close'],r['upper_band']);self.assertEqual(r['signal_at'],SIGNAL)
        self.assertEqual(r['breach_start'],B)

    def test_short_reentry(self):
        r=signal(run(source(-1))[0]);self.assertEqual(r['base_reason'],'SIGNAL');self.assertEqual(r['direction'],-1)
        self.assertEqual(r['stop'],D('110.01'));self.assertLess(r['rsi14'],r['breach_rsi14'])

    def test_close_outside_bands_rejects_both_sides(self):
        for vals in ((90,90,89,89),(90,120,90,120)):
            raw=source();set_parent(raw,C,vals);r=signal(run(raw)[0]);self.assertEqual(r['base_reason'],'NO_REENTRY_C')

    def test_b_rsi_threshold_not_extra_cross(self):
        raw=source();set_parent(raw,B,(100,100,100,100));r=signal(run(raw)[0])
        self.assertEqual(r['base_reason'],'NO_BREACH_B')

    def test_bands_inclusive_and_rsi_strict(self):
        # Hand-installed snapshots isolate the declared boundary grammar, no prices.
        for side,old_rsi,new_rsi,close,expected in ((1,35,36,90,'SIGNAL'),(-1,65,64,110,'SIGNAL'),(1,35,35,90,'NO_RSI_IMPROVEMENT'),(-1,65,65,110,'NO_RSI_IMPROVEMENT'),(1,D('35.01'),36,90,'NO_BREACH_B'),(-1,D('64.99'),64,110,'NO_BREACH_B')):
            a=BollingerRSIReentry(FIXED_PARAMETERS);a.begin_day('USDRUBF',DAY);a.window=ctx(C).window;a.last_start=B
            bar=Bar(B,FIFTEEN,D(100),D(112),D(88),D(89 if side==1 else 111),D(1))
            bi=dict(indicators_ready=True,sma20=D(100),population_sigma=D(5),lower_band=D(90),upper_band=D(110),rsi14=D(old_rsi))
            a.previous=(bar,bi)
            with patch.object(a.indicators,'observe',return_value=dict(bi,rsi14=D(new_rsi))):
                c=replace(bar,start=C,close=D(close));r=a.on_bar(c,ctx(C))[0]
            self.assertEqual(r['base_reason'],expected)

    def test_boundary_no_b_c_across_day_or_lunch(self):
        a=BollingerRSIReentry(FIXED_PARAMETERS);a.begin_day('USDRUBF',DAY)
        p,_=aggregate_m15(source(),RULES,PRE,DAY+timedelta(days=1))
        for at in sorted(t for t in p if t.date()==PRE):
            a.day=PRE;a.on_bar(p[at],ctx(at,next(w for w in RULES.windows(PRE) if w[0]<=at<w[1])))
        a.begin_day('USDRUBF',DAY);r=a.on_bar(p[T],ctx(T))[0]
        self.assertEqual(r['base_reason'],'B_NOT_READY_OR_BOUNDARY')
        pm=RULES.at(DAY,'14:15');r=a.on_bar(p[pm],ctx(pm,RULES.windows(DAY)[1]))[0]
        self.assertEqual(r['base_reason'],'B_NOT_READY_OR_BOUNDARY')

    def test_future_mutations_leave_past_decisions_unchanged(self):
        def emitted(raw):
            parents,_=aggregate_m15(raw,RULES,PRE,DAY+timedelta(days=1))
            a=BollingerRSIReentry(FIXED_PARAMETERS);records=[]
            for day in (PRE,DAY):
                a.begin_day('USDRUBF',day)
                for window in RULES.windows(day):
                    for at in full_slots(window):
                        records.extend(a.on_bar(parents.get(at),ctx(at,window)))
            return [r for r in records if r['test_closed_at']<=SIGNAL]
        raw=source();original=emitted(raw)
        changed={t:(replace(b,high=D(999),close=D(1),problem='FUTURE') if t>=SIGNAL else b) for t,b in raw.items()}
        self.assertEqual(original,emitted(changed))

    def test_uncompleted_input_or_wrong_label_rejected(self):
        a=BollingerRSIReentry(FIXED_PARAMETERS);a.begin_day('USDRUBF',DAY)
        with self.assertRaises(ValueError):a.on_bar(None,replace(ctx(T),available_at=T))


class SharedExecutionTests(unittest.TestCase):
    def test_wait_complete_m15_then_next_open(self):
        _,tt,_=run(source());q=tt[0]
        self.assertEqual(q['signal_at'],SIGNAL);self.assertEqual(q['waiting_bar_closed_at'],ENTRY)
        self.assertEqual(q['entry_at'],ENTRY);self.assertEqual(q['entry_price'],D(95))

    def test_missing_waiting_reject_before_order(self):
        raw=source();del raw[SIGNAL+FIVE];ss,tt,_=run(raw)
        self.assertEqual(signal(ss)['reason'],'NO_WAITING_BAR');self.assertFalse(tt);self.assertFalse(signal(ss)['order_admitted'])

    def test_missing_entry_open_unknown_possible_fill(self):
        raw=source();del raw[ENTRY];_,tt,_=run(raw)
        self.assertEqual(tt[0]['unknown_reason'],'MISSING_EXECUTION_BAR');self.assertFalse(tt[0]['model_filled'])
        self.assertIsNone(tt[0]['net_R_c1']);self.assertIsNone(tt[0]['entry_price'])

    def test_known_entry_open_incomplete_path_unknown(self):
        for i in (1,2):
            raw=source();del raw[ENTRY+i*FIVE];_,tt,_=run(raw)
            self.assertTrue(tt[0]['model_filled']);self.assertEqual(tt[0]['entry_price'],D(95))
            self.assertEqual(tt[0]['unknown_reason'],'INVALID_EXPOSED_BAR');self.assertIsNone(tt[0]['net_R_c1'])
            self.assertEqual(tt[0]['cost_entry_c1'],D('.01'))

    def test_stop_side_minimum_risk_and_open_grid(self):
        for price,reason in (('89.98','INVALID_RISK'),('89.99','INVALID_RISK'),('90.02','RISK_BELOW_FOUR_TICKS')):
            raw=source();set_parent(raw,ENTRY,(price,95.1,89,95));ss,tt,_=run(raw)
            self.assertEqual(signal(ss)['reason'],reason);self.assertFalse(tt)
        raw=source();set_parent(raw,ENTRY,('90.03',95.1,90,95));_,tt,_=run(raw)
        self.assertTrue(tt[0]['model_filled']);self.assertEqual(tt[0]['risk'],D('.04'))
        raw=source();raw[ENTRY]=replace(raw[ENTRY],open=D('95.005'));_,tt,_=run(raw)
        self.assertEqual(tt[0]['unknown_reason'],'INVALID_EXECUTION_OPEN')

    def test_target_cost_outward_rounding_long_short(self):
        for side in (1,-1):
            _,tt,_=run(source(side));q=tt[0];distance=side*(q['take']-q['entry_price'])
            self.assertGreaterEqual(distance,D('1.5')*q['risk']+D('.05'))
            self.assertLess(distance,D('1.5')*q['risk']+D('.06'))
            self.assertGreaterEqual(q['planned_net_to_net_R'],D('1.5'))
            self.assertEqual(q['take']%D('.01'),0);self.assertEqual(q['cost_c1'],D('.02'))

    def test_take_after_entry_and_c1_ledger(self):
        raw=source();set_parent(raw,ENTRY+FIFTEEN,(95,120,94.9,95));_,tt,_=run(raw);q=tt[0]
        self.assertEqual(q['exit_reason'],'TAKE');self.assertGreaterEqual(q['realized_net_to_net_R'],D('1.5'))
        self.assertEqual(q['net_c1'],q['gross']-D('.02'))

    def test_stop_first_conflict(self):
        raw=source();set_parent(raw,ENTRY+FIFTEEN,(95,120,80,95));_,tt,_=run(raw)
        self.assertEqual(tt[0]['exit_reason'],'STOP');self.assertTrue(tt[0]['stop_take_conflict'])

    def test_adverse_gap_stop_at_open(self):
        raw=source();set_parent(raw,ENTRY+FIFTEEN,(85,86,84,85));_,tt,_=run(raw)
        self.assertEqual(tt[0]['exit_reason'],'STOP');self.assertEqual(tt[0]['exit_price'],D(85))
        self.assertEqual(tt[0]['exit_at'],ENTRY+FIFTEEN)

    def test_no_entry_bar_take(self):
        raw=source();set_parent(raw,ENTRY,(95,120,94.9,95));_,tt,_=run(raw)
        self.assertEqual(tt[0]['exit_reason'],'TIME')

    def test_max_hold_120_and_missing_exit_open(self):
        raw=source();_,tt,_=run(raw);self.assertEqual(tt[0]['exit_at'],ENTRY+timedelta(minutes=120))
        self.assertEqual(tt[0]['exit_reason'],'TIME')
        del raw[ENTRY+timedelta(minutes=120)];_,tt,_=run(raw)
        self.assertEqual(tt[0]['status'],'UNKNOWN');self.assertIsNone(tt[0]['exit_price'])

    def test_missing_exposed_open_or_path_unknown(self):
        for offset in (15,20):
            raw=source();del raw[ENTRY+timedelta(minutes=offset)];_,tt,_=run(raw)
            self.assertEqual(tt[0]['status'],'UNKNOWN');self.assertIsNone(tt[0]['gross'])

    def test_one_pending_open_position(self):
        raw=source();set_parent(raw,T+7*FIFTEEN,(95,95,85,85));set_parent(raw,T+8*FIFTEEN,(85,95,85,95))
        ss,tt,_=run(raw)
        self.assertTrue(all(a['resolved_at']<=b['entry_at'] for a,b in zip(tt,tt[1:]) if a['status']==b['status']=='CLOSED'))

    def test_cny_historical_tick_change(self):
        self.assertEqual(RULES.tick('CNYRUBF',RULES.at(date(2023,9,27),'18:55')),D('.01'))
        self.assertEqual(RULES.tick('CNYRUBF',RULES.at(date(2023,9,27),'19:00')),D('.001'))

    def test_session_flat_1700_reserve_and_march(self):
        class Scheduled:
            name='SYNTHETIC'
            def __init__(self,clock):self.clock=clock
            def begin_day(self,symbol,day):self.day=day
            def end_day(self):return []
            def on_bar(self,b,c):
                return [dict(signal_id=str(c.available_at),base_reason='SIGNAL',signal_at=c.available_at,direction=1,
                    stop=D(80),target_gross_R=D('1.5'),target_net_R=D('1.5'),target_mode='FULL_NET_C1_R',max_hold_calendar_minutes=120,
                    entry_constraints=dict(minimum_risk_ticks=4,reserve_minutes=35))] if self.day==DAY and c.available_at.strftime('%H:%M')==self.clock else []
        for clock,exit_clock,reason in (('12:45','13:45','SESSION_FLAT'),('16:00','17:00','TRADE_DEADLINE')):
            _,tt,_=run(source(),Scheduled(clock));self.assertEqual(tt[0]['exit_at'],RULES.at(DAY,exit_clock));self.assertEqual(tt[0]['exit_reason'],reason)
        for clock,reason in (('13:00','SESSION_ENTRY_CUTOFF'),('16:15','SESSION_ENTRY_CUTOFF'),('16:45','TRADE_DEADLINE')):
            ss,tt,_=run(source(),Scheduled(clock));self.assertFalse(tt);self.assertEqual(ss[0]['reason'],reason)
        r=reachability(CFG,RULES)
        self.assertEqual(RULES.windows(date(2023,3,14))[1][0].strftime('%H:%M'),'14:15')
        self.assertTrue(any('16:15' in x['admissible_entry_slots'] for x in r['records'] if x['window_start']!='10:00'))
        self.assertTrue(all('16:30' not in x['admissible_entry_slots'] for x in r['records']))


class SourceBoundaryTests(unittest.TestCase):
    def test_runtime_byte_guard_refuses_future_and_other_timeframes(self):
        from IntradayLab.tools.validate_bollinger_rsi_reentry_baseline import guarded_source_reads
        with TemporaryDirectory(dir=LAB/'work') as folder:
            root=Path(folder);path=root/'M5.csv';path.write_bytes(b'2023\nFUTURE')
            other=root/'M15.csv';other.write_bytes(b'FUTURE')
            cfg={'inputs':{'USDRUBF':dict(path='M5.csv',prefix_bytes=5)}}
            with guarded_source_reads(root,cfg) as receipt:
                with path.open('rb',buffering=0) as stream:
                    self.assertEqual(stream.read(5),b'2023\n')
                    with self.assertRaises(AssertionError):stream.read(1)
                with self.assertRaises(AssertionError):other.open('rb',buffering=0)
            self.assertEqual(receipt['M5.csv']['highest_offset'],5)
            self.assertEqual(receipt['M5.csv']['bytes_2024_plus_read'],0)

    def test_verified_loader_never_reads_future_suffix(self):
        header='Ticker;Datetime;Open;High;Low;Close;Volume\n';line='USDRUBF;2023-01-03 10:00:00;100;101;99;100;1\n'
        prefix=(header+line).encode();cfg=deepcopy(CFG);cfg['instruments']=['USDRUBF'];cfg['timeframe_minutes']=5
        cfg['inputs']={'USDRUBF':dict(path='fake.csv',blob='fakeblob',prefix_bytes=len(prefix),prefix_sha256=hashlib.sha256(prefix).hexdigest(),rows_2023=1,first='2023-01-03 10:00:00')}
        with TemporaryDirectory(dir=LAB/'work') as folder:
            root=Path(folder);p=root/'fake.csv';p.write_bytes(prefix+b'2024+ PRICE BYTES MUST NEVER BE READ')
            opened=[];original=Path.open
            class Guard:
                def __init__(self,stream):self.stream=stream
                def __enter__(self):return self
                def __exit__(self,*a):self.stream.close()
                def read(self,n=-1):
                    self_test.assertEqual(n,len(prefix));opened.append(n);return self.stream.read(n)
            self_test=self
            def guarded(path,*args,**kwargs):
                stream=original(path,*args,**kwargs)
                return Guard(stream) if path==p else stream
            def fake_git(root,*args):
                return cfg['source_ref'] if args[0]=='rev-parse' else '' if args[0]=='status' else '100644 fakeblob 0 fake.csv'
            with patch('IntradayLab.core.data_loader.git',side_effect=fake_git),patch.object(Path,'open',guarded):
                data,receipt=load_market_data(root,cfg,RULES)
            self.assertEqual(opened,[len(prefix)]);self.assertEqual(receipt['USDRUBF']['bytes_2024_plus_read'],0)
            self.assertEqual(len(data['USDRUBF']),1)

    def test_backtester_and_aggregation_reject_2024(self):
        at=RULES.at(date(2024,1,1),'10:00');b=replace(source()[T],start=at)
        with self.assertRaises(ValueError):aggregate_m15({at:b},RULES,PRE,date(2024,1,1))
        with self.assertRaises(ValueError):Backtester(RULES,timeframe_minutes=15).run(BollingerRSIReentry(FIXED_PARAMETERS),'USDRUBF',{at:replace(b,duration=FIFTEEN)},start=PRE,end_exclusive=date(2024,1,1))


if __name__=='__main__':unittest.main()
