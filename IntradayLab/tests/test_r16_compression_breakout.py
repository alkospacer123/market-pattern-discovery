"""Fixed R16 signal geometry and shared execution contracts, synthetic only."""
from datetime import date, timedelta
from decimal import Decimal as D
import json
from pathlib import Path
import unittest

from IntradayLab.core.backtester import Backtester
from IntradayLab.core.calendar import MarketRules
from IntradayLab.core.data_loader import validate_bar
from IntradayLab.core.models import Context
from IntradayLab.strategies.compression_breakout import CompressionBreakout

CONFIG=Path(__file__).resolve().parents[1]/'config/r16_compression_breakout_2023_m5_v1.json'
FIVE=timedelta(minutes=5)


class R16Tests(unittest.TestCase):
    def setUp(self):
        self.cfg=json.loads(CONFIG.read_text());self.rules=MarketRules(self.cfg)
        self.day=date(2023,1,4);self.symbol='USDRUBF'
        self.strategy=CompressionBreakout(self.cfg['parameters'])
        self.strategy.begin_day(self.symbol,self.day)

    def at(self,clock):
        return self.rules.at(self.day,clock)

    def bar(self,at,o='100.5',h='101',l='100',c='100.5',v='10'):
        at=self.at(at) if isinstance(at,str) else at
        return validate_bar(at,tuple(map(D,(o,h,l,c,v))),FIVE,self.rules.tick(self.symbol,at))

    def observe(self,at,bar,atr='1'):
        at=self.at(at) if isinstance(at,str) else at
        window=next(w for w in self.rules.windows(self.day) if w[0]<=at<w[1])
        ctx=Context(self.symbol,at,at+FIVE,window,self.rules.tick(self.symbol,at),
                    {'atr14':D(atr) if atr is not None else None})
        return self.strategy.on_bar(bar,ctx)

    def seed(self,origin='10:00',count=8,atr='1'):
        for i in range(count):
            at=self.at(origin)+i*FIVE;self.observe(at,self.bar(at),atr)

    def breakout(self,at='10:40',side=1,**changes):
        defaults=dict(o='101',h='101.2',l='100.5',c='101.01') if side==1 else dict(o='100',h='100.5',l='99.8',c='99.99')
        return self.bar(at,**dict(defaults,**changes))

    def test_exactly_eight_previous_current_excluded(self):
        self.seed()
        e=self.observe('10:40',self.breakout(h='200',l='1'),atr='100')[0]
        self.assertEqual(e['base_reason'],'SIGNAL');self.assertEqual(e['compression_bars'],8)
        self.assertEqual((e['compression_high'],e['compression_low']),(D(101),D(100)))
        self.assertEqual(e['compression_start'],self.at('10:00'))
        self.assertEqual(e['compression_end'],self.at('10:40'))
        self.assertEqual(e['ATR_ref'],D(1));self.assertEqual(e['ATR_ref_bar_start'],self.at('10:35'))

    def test_seven_bars_insufficient(self):
        self.seed(count=7)
        self.assertEqual(self.observe('10:35',self.breakout('10:35')),[])

    def test_sliding_window_discards_ninth_old_bar(self):
        self.observe('10:00',self.bar('10:00',h='200',l='1'))
        self.seed('10:05')
        self.assertEqual(self.observe('10:45',self.breakout('10:45'))[0]['compression_width'],D(1))

    def test_missing_and_invalid_reset_require_eight_new_bars(self):
        for invalid in (None,self.bar('10:40',v='0')):
            self.setUp();self.seed()
            self.assertIn(self.observe('10:40',invalid)[0]['base_reason'],('COMPRESSION_MISSING_BAR','COMPRESSION_INVALID_BAR'))
            self.seed('10:45',count=7)
            self.assertEqual(self.observe('11:20',self.bar('11:20')),[])
            self.assertEqual(self.observe('11:25',self.breakout('11:25'))[0]['base_reason'],'SIGNAL')

    def test_nonconsecutive_callbacks_reset(self):
        self.seed()
        self.assertEqual(self.observe('10:45',self.breakout('10:45'))[0]['reset_reason'],'NONCONSECUTIVE_CALLBACK')
        self.assertEqual(len(self.strategy.history),1)

    def test_day_and_lunch_reset(self):
        self.seed();self.observe('14:05',self.bar('14:05'))
        self.assertEqual(len(self.strategy.history),1)
        self.strategy.begin_day(self.symbol,self.day+timedelta(days=1))
        self.assertEqual(len(self.strategy.history),0)

    def test_march_session_has_new_eight_bar_window(self):
        self.day=date(2023,3,13);self.strategy.begin_day(self.symbol,self.day)
        self.seed('14:15')
        e=self.observe('14:55',self.breakout('14:55'))[0]
        self.assertEqual(e['compression_start'],self.at('14:15'))

    def test_prior_atr_missing_or_zero_diagnosed(self):
        for atr,reason in ((None,'ATR_UNAVAILABLE'),('0','ATR_ZERO')):
            self.setUp();self.seed(atr=atr)
            self.assertEqual(self.observe('10:40',self.breakout(),atr='100')[0]['base_reason'],reason)

    def test_exact_width_threshold_and_above(self):
        self.seed(atr='.5')
        self.assertEqual(self.observe('10:40',self.breakout())[0]['base_reason'],'SIGNAL')
        self.setUp();self.seed(atr='.49')
        self.assertEqual(self.observe('10:40',self.breakout()),[])

    def test_long_short_opposite_stop(self):
        for side,stop in ((1,'99.99'),(-1,'101.01')):
            self.setUp();self.seed();e=self.observe('10:40',self.breakout(side=side))[0]
            self.assertEqual(e['direction'],side);self.assertEqual(e['stop'],D(stop))
            self.assertEqual(e['signal_at'],self.at('10:45'))

    def test_already_opened_outside_rejected(self):
        for side,o in ((1,'101.01'),(-1,'99.99')):
            self.setUp();self.seed()
            self.assertEqual(self.observe('10:40',self.breakout(side=side,o=o))[0]['base_reason'],'ALREADY_OUTSIDE_RANGE')

    def test_close_without_full_tick_no_signal(self):
        self.seed();self.assertEqual(self.observe('10:40',self.breakout(c='101')),[])

    def test_cny_dated_ticks(self):
        self.symbol='CNYRUBF'
        for day,step in ((date(2023,9,27),'.01'),(date(2023,9,28),'.001')):
            self.day=day;self.strategy.begin_day(self.symbol,day);self.seed()
            e=self.observe('10:40',self.breakout(c=str(D(101)+D(step))))[0]
            self.assertEqual(e['stop'],D(100)-D(step));self.assertEqual(e['breakout_tick'],D(step))

    def test_malformed_both_sides_refuses_direction(self):
        # Positive historical ticks and valid OHLC cannot trigger both sides.
        # A malformed context must still refuse an arbitrary direction.
        self.seed();at=self.at('10:40')
        ctx=Context(self.symbol,at,at+FIVE,self.rules.windows(self.day)[0],D('-1'),{'atr14':D(1)})
        e=self.strategy.on_bar(self.bar(at),ctx)[0]
        self.assertEqual(e['base_reason'],'AMBIGUOUS_BREAKOUT');self.assertEqual(e['direction'],0)

    def test_uncompleted_bar_rejected(self):
        at=self.at('10:00');ctx=Context(self.symbol,at,at,self.rules.windows(self.day)[0],D('.01'),{'atr14':D(1)})
        with self.assertRaisesRegex(ValueError,'UNCOMPLETED'):
            self.strategy.on_bar(self.bar(at),ctx)

    def rows(self,breakout_clock='10:40'):
        rows={}
        for a,z in self.rules.windows(self.day):
            while a<z:
                rows[a]=self.bar(a);a+=FIVE
        for i in range(14):
            at=self.at('08:50')+i*FIVE;rows[at]=self.bar(at)
        rows[self.at(breakout_clock)]=self.breakout(breakout_clock)
        return dict(sorted(rows.items()))

    def run_engine(self,rows):
        return Backtester(self.rules,daily_trade_deadline_clock='17:00').run(
            CompressionBreakout(self.cfg['parameters']),self.symbol,rows,
            start=self.day,end_exclusive=self.day+timedelta(days=1))

    def test_shared_clock_time_and_c1(self):
        ss,tt,_=self.run_engine(self.rows());q=tt[0]
        self.assertEqual(q['signal_at'],self.at('10:45'));self.assertEqual(q['entry_at'],self.at('10:50'))
        self.assertEqual(q['waiting_bar_closed_at'],self.at('10:50'))
        self.assertEqual(q['exit_at'],self.at('12:50'));self.assertEqual(q['exit_reason'],'TIME')
        self.assertEqual(q['cost_c1'],D('.02'));self.assertEqual(q['risk'],D('.51'))

    def test_no_daily_signal_quota(self):
        rows=self.rows();rows[self.at('12:55')]=self.breakout('12:55')
        _,tt,_=self.run_engine(rows)
        self.assertEqual(len(tt),2);self.assertEqual(tt[1]['exit_reason'],'SESSION_FLAT')
        self.assertEqual(tt[1]['exit_at'],self.at('13:55'))

    def test_busy_position_rejection(self):
        rows=self.rows();rows[self.at('11:30')]=self.breakout('11:30')
        ss,tt,_=self.run_engine(rows)
        self.assertEqual(len(tt),1)
        self.assertIn('POSITION_BUSY',[s['reason'] for s in ss])

    def test_stop_first_entry_take_forbidden_and_adverse_gap(self):
        rows=self.rows();rows[self.at('10:50')]=self.bar('10:50',h='110')
        self.assertEqual(self.run_engine(rows)[1][0]['exit_reason'],'TIME')
        rows[self.at('10:55')]=self.bar('10:55',h='110',l='99')
        q=self.run_engine(rows)[1][0];self.assertEqual(q['exit_price'],D('99.99'))
        self.assertTrue(q['stop_take_conflict'])
        rows[self.at('10:55')]=self.bar('10:55',o='99',h='99.5',l='98.5',c='99')
        q=self.run_engine(rows)[1][0];self.assertEqual(q['exit_at'],self.at('10:55'))
        self.assertEqual(q['exit_price'],D(99));self.assertEqual(q['net_c1'],D('-1.52'))

    def test_invalid_stop_geometry_and_no_minimum_stop_filter(self):
        rows=self.rows();rows[self.at('10:50')]=self.bar('10:50',o='99.99',h='100',l='99.9',c='99.99')
        self.assertIn('INVALID_STOP_GEOMETRY',[s['reason'] for s in self.run_engine(rows)[0]])
        self.assertEqual(self.run_engine(rows)[1],[])
        rows[self.at('10:50')]=self.bar('10:50',o='100',h='100',l='100',c='100')
        self.assertEqual(self.run_engine(rows)[1][0]['risk'],D('.01'))

    def test_missing_waiting_entry_management_and_exit(self):
        for clock in ('10:45','10:50','10:55','12:50'):
            rows=self.rows();del rows[self.at(clock)]
            ss,tt,_=self.run_engine(rows)
            if clock=='10:45':
                self.assertEqual(tt,[]);self.assertIn('NO_WAITING_BAR',[s['reason'] for s in ss])
            else:
                self.assertEqual(tt[0]['status'],'UNKNOWN')
                for key in ('net_R_c1','net_c1','exit_price','cost_c1'):
                    self.assertIsNone(tt[0][key])

    def test_exact_1700_open_only_and_missing(self):
        rows=self.rows('16:00');rows[self.at('17:00')]=self.bar('17:00',h='200',l='1',v='0')
        q=self.run_engine(rows)[1][0];self.assertEqual(q['exit_at'],self.at('17:00'))
        self.assertEqual(q['exit_reason'],'TRADE_DEADLINE')
        del rows[self.at('17:00')]
        self.assertEqual(self.run_engine(rows)[1][0]['status'],'UNKNOWN')

    def test_late_entry_before_deadline_and_rejection_at_deadline(self):
        ss,tt,_=self.run_engine(self.rows('16:45'))
        self.assertEqual(tt[0]['entry_at'],self.at('16:55'))
        self.assertEqual(tt[0]['exit_at'],self.at('17:00'))
        ss,tt,_=self.run_engine(self.rows('16:50'))
        self.assertEqual(tt,[]);self.assertIn('TRADE_DEADLINE',[s['reason'] for s in ss])

    def test_future_suffix_does_not_change_past_signals(self):
        rows=self.rows();first=self.run_engine(rows)[0]
        rows[self.at('11:00')]=self.bar('11:00',h='200',l='1')
        second=self.run_engine(rows)[0]
        self.assertEqual([s for s in first if s['recorded_at']<self.at('11:00')],
                         [s for s in second if s['recorded_at']<self.at('11:00')])


if __name__=='__main__':
    unittest.main()
