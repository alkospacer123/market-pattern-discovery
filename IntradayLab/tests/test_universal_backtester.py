"""Contract scenarios with explicit expected prices/times, not P&L tuning."""
from copy import deepcopy
from datetime import date, datetime, timedelta
from decimal import Decimal as D
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from IntradayLab.core.backtester import Backtester
from IntradayLab.core.calendar import MarketRules
from IntradayLab.core.data_loader import load_market_data, validate_bar
from IntradayLab.core.execution import cost, entry_geometry
from IntradayLab.core.indicators import Indicators
from IntradayLab.core.metrics import summarize
from IntradayLab.strategies.orb_false_break_fade import ORBFalseBreakFade

CONFIG=Path(__file__).resolve().parents[1]/'config/orb_a_base_2023_canonical_v1.json'
FIVE=timedelta(minutes=5)


class TimedStrategy:
    name='INDEPENDENT_TEST_CANDIDATE'
    def __init__(self, requests):
        self.requests=requests
        self.observations=[]
    def begin_day(self,symbol,day):
        self.symbol=symbol
    def on_bar(self,bar,ctx):
        self.observations.append(ctx)
        if ctx.available_at in self.requests:
            return [dict(signal_id=str(ctx.available_at),direction=-1,stop=D('101.02'),
                         signal_at=ctx.available_at,base_reason='SIGNAL',target_gross_R='1.5',
                         max_hold_calendar_minutes=60)]
        return []
    def end_day(self):
        return []


class EngineTests(unittest.TestCase):
    def setUp(self):
        self.config=json.loads(CONFIG.read_text())
        self.rules=MarketRules(self.config)
        self.day=date(2023,1,4)
        self.rows=self.make_day(self.day)
    def at(self,clock,day=None):
        return self.rules.at(day or self.day,clock)
    def bar(self,at,o='100.90',h='100.95',l='100.80',c='100.90',v='10'):
        return validate_bar(at,tuple(map(D,(o,h,l,c,v))),FIVE,self.rules.tick('USDRUBF',at))
    def make_day(self,day):
        out={}
        for a,z in self.rules.windows(day):
            while a<z:
                out[a]=self.bar(a)
                a+=FIVE
        return out
    def run_engine(self,requests=None,rows=None,strategy=None,end=None):
        strategy=strategy or TimedStrategy(requests or [self.at('10:20')])
        out=Backtester(self.rules).run(strategy,'USDRUBF',rows if rows is not None else self.rows,
            start=self.day,end_exclusive=end or self.day+timedelta(days=1))
        return out
    def orb_rows(self):
        for clock in ('10:00','10:05','10:10'):
            self.rows[self.at(clock)]=self.bar(self.at(clock),o='100.5',h='101',l='100',c='100.5')
        self.rows[self.at('10:15')]=self.bar(self.at('10:15'),o='100.9',h='101.01',l='100.8',c='100.98')
        return self.rows
    def test_non_orb_strategy_uses_same_engine(self):
        ss,tt,_=self.run_engine()
        self.assertEqual(tt[0]['strategy'],'INDEPENDENT_TEST_CANDIDATE')
        self.assertEqual(ss[0]['planned_execution_at'],self.at('10:25'))
    def test_signal_wait_entry_sequence(self):
        ss,tt,_=self.run_engine()
        self.assertEqual(tt[0]['signal_at'],self.at('10:20'))
        self.assertEqual(tt[0]['waiting_bar_closed_at'],self.at('10:25'))
        self.assertEqual(tt[0]['entry_at'],self.at('10:25'))
    def test_open_only_no_future_entry_rejection(self):
        bad=self.bar(self.at('10:25'),h='99',c='100.9',v='0')
        self.rows[bad.start]=bad
        ss,tt,_=self.run_engine()
        self.assertTrue(ss[0]['order_admitted'])
        self.assertTrue(tt[0]['model_filled'])
        self.assertEqual(tt[0]['unknown_reason'],'INVALID_EXPOSED_BAR')
    def test_missing_waiting_bar_means_no_order(self):
        del self.rows[self.at('10:20')]
        ss,tt,_=self.run_engine()
        self.assertEqual(ss[0]['reason'],'NO_WAITING_BAR')
        self.assertFalse(ss[0]['order_admitted'])
        self.assertEqual(tt,[])
    def test_missing_entry_unknown_possible_fill(self):
        del self.rows[self.at('10:25')]
        ss,tt,_=self.run_engine()
        self.assertEqual(tt[0]['unknown_reason'],'MISSING_EXECUTION_BAR')
        self.assertFalse(tt[0]['model_filled'])
        self.assertIsNone(tt[0]['net_R_c1'])
    def test_invalid_entry_open_is_unknown_not_nonfill(self):
        self.rows[self.at('10:25')]=self.bar(self.at('10:25'),o='100.901')
        ss,tt,_=self.run_engine()
        self.assertEqual(ss[0]['status'],'UNKNOWN')
        self.assertEqual(tt[0]['unknown_reason'],'INVALID_EXECUTION_OPEN')
        self.assertFalse(tt[0]['model_filled'])
    def test_missing_management_keeps_unknown(self):
        del self.rows[self.at('10:30')]
        _,tt,_=self.run_engine()
        self.assertEqual(tt[0]['unknown_reason'],'MISSING_EXPOSED_BAR')
        self.assertEqual(tt[0]['cost_entry_c1'],D('.01'))
        self.assertIsNone(tt[0]['cost_c1'])
        self.assertIsNone(tt[0]['exit_price'])
    def test_unknown_blocks_same_day_but_not_next_day(self):
        del self.rows[self.at('10:30')]
        next_day=self.day+timedelta(days=1)
        self.rows.update(self.make_day(next_day))
        requests=[self.at('10:20'),self.at('11:00'),self.at('10:20',next_day)]
        ss,tt,dd=self.run_engine(requests,end=next_day+timedelta(days=1))
        self.assertEqual(ss[1]['reason'],'UNKNOWN_POSITION_BLOCK')
        self.assertEqual(len(tt),2)
        self.assertEqual(tt[0]['status'],'UNKNOWN')
        self.assertEqual(tt[1]['status'],'CLOSED')
        self.assertTrue(tt[1]['prior_unknown_requires_flat_assumption'])
        self.assertFalse(tt[1]['initial_flat_proven'])
    def test_one_position_and_pending_order(self):
        ss,tt,_=self.run_engine([self.at('10:20'),self.at('10:25'),self.at('10:35')])
        self.assertEqual(len(tt),1)
        self.assertEqual([s['reason'] for s in ss[1:]],['POSITION_BUSY','POSITION_BUSY'])
    def test_simultaneous_candidates_sorted_by_id(self):
        class Simultaneous(TimedStrategy):
            def on_bar(self,bar,ctx):
                events=super().on_bar(bar,ctx)
                if events:
                    return [dict(events[0],signal_id='Z'),dict(events[0],signal_id='A')]
                return []
        ss,tt,_=self.run_engine(strategy=Simultaneous([self.at('10:20')]))
        self.assertEqual(tt[0]['signal_id'],'A')
        self.assertEqual(ss[1]['reason'],'POSITION_BUSY')
    def test_small_valid_stop_not_filtered(self):
        class SmallStop(TimedStrategy):
            def on_bar(self,bar,ctx):
                return [dict(e,stop=D('100.91')) for e in super().on_bar(bar,ctx)]
        ss,tt,_=self.run_engine(strategy=SmallStop([self.at('10:20')]))
        self.assertTrue(ss[0]['model_filled'])
        self.assertEqual(tt[0]['risk'],D('.01'))
    def test_stop_first_same_bar(self):
        self.rows[self.at('10:30')]=self.bar(self.at('10:30'),h='101.10',l='100.50')
        _,tt,_=self.run_engine()
        self.assertEqual(tt[0]['exit_reason'],'STOP')
        self.assertEqual(tt[0]['exit_price'],D('101.02'))
        self.assertTrue(tt[0]['stop_take_conflict'])
    def test_long_side_target_stop_and_cost(self):
        class Long(TimedStrategy):
            def on_bar(self,bar,ctx):
                return [dict(e,direction=1,stop=D('100.78')) for e in super().on_bar(bar,ctx)]
        self.rows[self.at('10:30')]=self.bar(self.at('10:30'),h='101.10')
        _,tt,_=self.run_engine(strategy=Long([self.at('10:20')]))
        self.assertEqual(tt[0]['exit_reason'],'TAKE')
        self.assertEqual(tt[0]['exit_price'],D('101.08'))
        self.assertEqual(tt[0]['net_R_c1'],D('.16')/D('.12'))
        self.rows[self.at('10:30')]=self.bar(self.at('10:30'),h='101.10',l='100.70')
        _,tt,_=self.run_engine(strategy=Long([self.at('10:20')]))
        self.assertEqual(tt[0]['exit_price'],D('100.78'))
        self.assertTrue(tt[0]['stop_take_conflict'])
    def test_entry_bar_stop_allowed_take_forbidden(self):
        self.rows[self.at('10:25')]=self.bar(self.at('10:25'),l='100.50')
        _,tt,_=self.run_engine()
        self.assertEqual(tt[0]['exit_reason'],'TIME')
        self.rows[self.at('10:25')]=self.bar(self.at('10:25'),h='101.10',l='100.50')
        _,tt,_=self.run_engine()
        self.assertEqual(tt[0]['exit_reason'],'STOP')
    def test_take_at_target_without_gap_improvement(self):
        self.rows[self.at('10:30')]=self.bar(self.at('10:30'),o='100.60',h='100.65',l='100.50',c='100.60')
        _,tt,_=self.run_engine()
        self.assertEqual(tt[0]['take'],D('100.72'))
        self.assertEqual(tt[0]['exit_price'],D('100.72'))
    def test_adverse_stop_gap_and_c1(self):
        self.rows[self.at('10:30')]=self.bar(self.at('10:30'),o='101.10',h='101.20',l='101.05',c='101.10')
        _,tt,_=self.run_engine()
        q=tt[0]
        self.assertEqual(q['exit_price'],D('101.10'))
        self.assertEqual(q['exit_at'],self.at('10:30'))
        self.assertEqual(q['cost_c1'],D('.02'))
        self.assertEqual(q['net_R_c1'],D('-.22')/D('.12'))
    def test_scheduled_exit_reads_only_open(self):
        self.rows[self.at('11:25')]=self.bar(self.at('11:25'),h='150',l='90',v='0')
        _,tt,_=self.run_engine()
        self.assertEqual(tt[0]['exit_reason'],'TIME')
        self.assertEqual(tt[0]['exit_at'],self.at('11:25'))
    def test_stop_gap_precedes_time_exit(self):
        self.rows[self.at('11:25')]=self.bar(self.at('11:25'),o='101.10',h='101.20',l='101.05',c='101.10')
        _,tt,_=self.run_engine()
        self.assertEqual(tt[0]['exit_reason'],'STOP')
    def test_missing_mandatory_exit_is_unknown(self):
        del self.rows[self.at('11:25')]
        _,tt,_=self.run_engine()
        self.assertEqual(tt[0]['status'],'UNKNOWN')
    def test_forced_flat_and_late_entry_limit(self):
        ss,tt,_=self.run_engine([self.at('13:45'),self.at('18:40')])
        self.assertEqual(tt[0]['exit_reason'],'SESSION_FLAT')
        self.assertEqual(tt[0]['exit_at'],self.at('13:55'))
        self.assertEqual(ss[1]['reason'],'SESSION_LIMIT')
    def test_historical_cny_tick_and_different_side_costs(self):
        self.assertEqual(self.rules.tick('CNYRUBF',self.at('18:55',date(2023,9,27))),D('.01'))
        self.assertEqual(self.rules.tick('CNYRUBF',self.at('19:00',date(2023,9,27))),D('.001'))
        self.assertEqual(cost(D('.01'),D('.001'),1),D('.011'))
        self.assertEqual(entry_geometry(D('10.000'),1,D('9.997'),D('.001'),D('1.5')),(D('.003'),D('10.005')))
    def test_calendar_and_extended_lunch(self):
        self.assertEqual(self.rules.windows(date(2023,3,8)),[])
        self.assertEqual(self.rules.windows(date(2023,3,11)),[])
        self.assertEqual(self.rules.windows(date(2023,3,13))[1][0].strftime('%H:%M'),'14:15')
        self.assertEqual(self.rules.windows(date(2023,3,21))[1][0].strftime('%H:%M'),'14:05')
    def test_orb_frozen_same_bar_reclaim(self):
        self.orb_rows()
        ss,tt,_=self.run_engine(strategy=ORBFalseBreakFade(self.config['parameters']))
        self.assertEqual(tt[0]['stop'],D('101.02'))
        self.assertEqual(tt[0]['take'],D('100.72'))
        self.assertEqual(tt[0]['entry_at'],self.at('10:25'))
        self.assertEqual(sum(s['base_reason']=='SIGNAL' for s in ss),1)
    def test_next_reclaim_stop_uses_whole_episode(self):
        self.orb_rows()
        self.rows[self.at('10:15')]=self.bar(self.at('10:15'),h='101.05',c='101.03')
        self.rows[self.at('10:20')]=self.bar(self.at('10:20'),h='101.08',c='100.98')
        _,tt,_=self.run_engine(strategy=ORBFalseBreakFade(self.config['parameters']))
        self.assertEqual(tt[0]['stop'],D('101.09'))
        self.assertEqual(tt[0]['entry_at'],self.at('10:30'))
    def test_missing_reclaim_successor_consumes_attempt(self):
        self.orb_rows()
        self.rows[self.at('10:15')]=self.bar(self.at('10:15'),h='101.05',c='101.03')
        del self.rows[self.at('10:20')]
        self.rows[self.at('10:25')]=self.bar(self.at('10:25'),h='101.05',c='100.98')
        ss,tt,_=self.run_engine(strategy=ORBFalseBreakFade(self.config['parameters']))
        self.assertEqual(tt,[])
        self.assertEqual(ss[0]['reason'],'NO_RECLAIM_GAP')
    def test_both_sides_ambiguous_consumes_both(self):
        self.orb_rows()
        self.rows[self.at('10:15')]=self.bar(self.at('10:15'),h='101.01',l='99.99')
        ss,tt,_=self.run_engine(strategy=ORBFalseBreakFade(self.config['parameters']))
        self.assertEqual(tt,[])
        self.assertEqual(ss[0]['reason'],'AMBIGUOUS_BOTH_SIDES')
    def test_missing_or_no_synthetic_range(self):
        self.orb_rows()
        del self.rows[self.at('10:05')]
        ss,tt,_=self.run_engine(strategy=ORBFalseBreakFade(self.config['parameters']))
        self.assertEqual(tt,[])
        self.assertEqual(ss[-1]['reason'],'NO_OR')
    def test_future_suffix_does_not_change_past_signals(self):
        self.orb_rows()
        strategy=lambda: ORBFalseBreakFade(self.config['parameters'])
        first=self.run_engine(strategy=strategy())[0]
        self.rows[self.at('11:00')]=self.bar(self.at('11:00'),h='200',l='1')
        second=self.run_engine(strategy=strategy())[0]
        limit=self.at('11:00')
        self.assertEqual([s for s in first if s.get('recorded_at',limit)<limit],
                         [s for s in second if s.get('recorded_at',limit)<limit])
    def test_warmup_prior_day_and_pre_open_history(self):
        earlier=self.day-timedelta(days=1)
        for i in range(14):
            at=self.at('21:00',earlier)+i*FIVE
            self.rows[at]=self.bar(at)
        self.rows=dict(sorted(self.rows.items()))
        s=TimedStrategy([])
        self.run_engine(strategy=s)
        self.assertEqual(s.observations[0].indicators['observed_bars'],15)
        self.assertIsNotNone(s.observations[0].indicators['atr14'])
    def test_indicator_forbids_uncompleted_observation(self):
        b=self.rows[self.at('10:00')]
        with self.assertRaisesRegex(ValueError,'UNCOMPLETED'):
            Indicators().observe(b,b.start)
    def test_indicator_gap_has_no_invented_jump(self):
        i=Indicators(period=2)
        a=self.bar(self.at('10:00'))
        b=self.bar(self.at('11:00'),o='200',h='201',l='199',c='200')
        i.observe(a,a.available_at)
        values=i.observe(b,b.available_at)
        self.assertEqual(values['atr14'],D('1.075'))
    def test_repeat_is_exact(self):
        self.assertEqual(self.run_engine(),self.run_engine())
    def test_annual_unknown_metrics_remain_null(self):
        del self.rows[self.at('10:30')]
        ss,tt,_=self.run_engine()
        m=summarize(tt,ss,[{'status':'COMPLETE'}])
        self.assertFalse(m['annual_complete'])
        self.assertTrue(all(x is None for x in m['annual'].values()))
    def test_time_guard_rejects_wf_and_future_rows(self):
        with self.assertRaisesRegex(ValueError,'development'):
            self.run_engine(end=date(2024,1,2))
        self.rows[self.at('10:00',date(2024,1,4))]=self.bar(self.at('10:00',date(2024,1,4)))
        with self.assertRaises(ValueError):
            self.run_engine()
    def test_ordering_and_timezone_validation(self):
        with self.assertRaisesRegex(ValueError,'TIMEZONE'):
            self.run_engine(rows=dict(reversed(list(self.rows.items()))))
    def test_wrong_bar_duration_or_label_rejected(self):
        from dataclasses import replace
        self.rows[self.at('10:00')]=replace(self.rows[self.at('10:00')],duration=timedelta(minutes=15))
        with self.assertRaisesRegex(ValueError,'BAR_LABEL'):
            self.run_engine()


class LoaderTests(unittest.TestCase):
    def setUp(self):
        self.config=json.loads(CONFIG.read_text())
        self.rules=MarketRules(self.config)
    def fixture(self,line):
        raw=b'Ticker;Datetime;Open;High;Low;Close;Volume\n'+line
        c=deepcopy(self.config)
        c['instruments']=['USDRUBF']
        c['inputs']={'USDRUBF':dict(path='input.csv',blob='a'*40,prefix_bytes=len(raw),
            prefix_sha256=hashlib.sha256(raw).hexdigest(),rows_2023=len(raw.splitlines())-1,
            first='2023-01-03 09:00:00')}
        return raw,c
    def load(self,raw,c):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            (root/'input.csv').write_bytes(raw+b'2024 and 2025 FUTURE POISON NEVER READ\n')
            def fake_git(root,*args):
                return c['source_ref'] if args[0]=='rev-parse' else '' if args[0]=='status' else '100644 '+'a'*40+' 0\tinput.csv'
            with patch('IntradayLab.core.data_loader.git',fake_git):
                return load_market_data(root,c,self.rules)
    def test_exact_prefix_future_bytes_not_read(self):
        raw,c=self.fixture(b'USDRUBF;2023-01-03 09:00:00;70;70.01;69.99;70;1\n')
        rows,receipts=self.load(raw,c)
        self.assertEqual(receipts['USDRUBF']['bytes_read'],len(raw))
        self.assertEqual(receipts['USDRUBF']['bytes_2024_plus_read'],0)
        b=next(iter(rows['USDRUBF'].values()))
        self.assertEqual(str(b.start.tzinfo),'Europe/Moscow')
        self.assertEqual(b.available_at-b.start,FIVE)
    def test_duplicates_rejected(self):
        raw,c=self.fixture(b'USDRUBF;2023-01-03 09:00:00;70;70.01;69.99;70;1\n'*2)
        with self.assertRaisesRegex(ValueError,'DUPLICATE'):
            self.load(raw,c)
    def test_integrity_and_grid_diagnosed(self):
        raw,c=self.fixture(b'USDRUBF;2023-01-03 09:00:00;70;70.001;69.99;70;1\n')
        rows,_=self.load(raw,c)
        self.assertFalse(next(iter(rows['USDRUBF'].values())).valid)
    def test_pinned_hash_rejected(self):
        raw,c=self.fixture(b'USDRUBF;2023-01-03 09:00:00;70;70.01;69.99;70;1\n')
        c['inputs']['USDRUBF']['prefix_sha256']='0'*64
        with self.assertRaisesRegex(ValueError,'PREFIX'):
            self.load(raw,c)


if __name__=='__main__':
    unittest.main()
