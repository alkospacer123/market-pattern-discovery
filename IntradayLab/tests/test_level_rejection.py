"""Fixed six-bar Level Rejection plus common Open-only economic execution."""
from datetime import date, timedelta
from decimal import Decimal as D
import json
from pathlib import Path
import unittest
from IntradayLab.core.backtester import Backtester
from IntradayLab.core.calendar import MarketRules
from IntradayLab.core.data_loader import validate_bar
from IntradayLab.core.models import Context
from IntradayLab.strategies.level_rejection import LevelRejection

CONFIG=Path(__file__).resolve().parents[1]/'config/level_rejection_2023_m5_v1.json'
FIVE=timedelta(minutes=5)


class LevelRejectionTests(unittest.TestCase):
    def setUp(self):
        self.cfg=json.loads(CONFIG.read_text());self.rules=MarketRules(self.cfg)
        self.day=date(2023,1,4);self.symbol='USDRUBF'
        self.strategy=LevelRejection(self.cfg['parameters']);self.strategy.begin_day(self.symbol,self.day)

    def at(self,clock):
        return self.rules.at(self.day,clock)

    def bar(self,at,o='100.5',h='101',l='100',c='100.5',v='10'):
        at=self.at(at) if isinstance(at,str) else at
        return validate_bar(at,tuple(map(D,(o,h,l,c,v))),FIVE,self.rules.tick(self.symbol,at))

    def observe(self,at,bar):
        at=self.at(at) if isinstance(at,str) else at
        window=next(w for w in self.rules.windows(self.day) if w[0]<=at<w[1])
        return self.strategy.on_bar(bar,Context(self.symbol,at,at+FIVE,window,
            self.rules.tick(self.symbol,at),{}))

    def seed(self,origin='10:00',count=6):
        for i in range(count):
            at=self.at(origin)+i*FIVE;self.observe(at,self.bar(at))

    def rejection(self,at='10:30',side=1,**changes):
        defaults=dict(l='99.98',c='100.01') if side==1 else dict(h='101.02',c='100.99')
        return self.bar(at,**dict(defaults,**changes))

    def test_six_previous_and_current_excluded(self):
        self.seed();e=self.observe('10:30',self.rejection())[0]
        self.assertEqual(e['base_reason'],'SIGNAL');self.assertEqual(e['range_bars'],6)
        self.assertEqual((e['range_high'],e['range_low']),(D(101),D(100)))
        self.assertEqual(e['range_start'],self.at('10:00'));self.assertEqual(e['range_end'],self.at('10:30'))
        self.assertEqual(e['signal_at'],self.at('10:35'))

    def test_five_insufficient_and_seventh_old_bar_discarded(self):
        self.seed(count=5);self.assertEqual(self.observe('10:25',self.rejection('10:25')),[])
        self.setUp();self.observe('10:00',self.bar('10:00',h='200',l='1'));self.seed('10:05')
        self.assertEqual(self.observe('10:35',self.rejection('10:35'))[0]['range_low'],D(100))

    def test_long_short_stop_and_grid(self):
        for side,stop in ((1,'99.97'),(-1,'101.03')):
            self.setUp();self.seed();e=self.observe('10:30',self.rejection(side=side))[0]
            self.assertEqual(e['direction'],side);self.assertEqual(e['stop'],D(stop))

    def test_double_rejection_ambiguous(self):
        self.seed();e=self.observe('10:30',self.rejection(h='101.02',c='100.5'))[0]
        self.assertEqual(e['base_reason'],'AMBIGUOUS_BOTH_SIDES')
        self.assertFalse(e['raw_rejection']);self.assertFalse(e['confirmed_signal'])
        self.assertEqual(self.strategy.last_confirmed,{})

    def test_penetration_and_reentry_each_require_tick(self):
        for low,close in (('100','100.01'),('99.99','100')):
            self.setUp();self.seed();self.assertEqual(self.observe('10:30',self.rejection(l=low,c=close)),[])

    def test_directional_dedup_exact_30_minutes(self):
        self.seed();self.observe('10:30',self.rejection())
        e=self.observe('10:35',self.rejection('10:35',l='99.97',c='100'))[0]
        self.assertEqual(e['base_reason'],'DEDUP_30MIN');self.assertTrue(e['raw_rejection'])
        e=self.observe('10:40',self.rejection('10:40',side=-1))[0]
        self.assertEqual(e['base_reason'],'SIGNAL');self.assertEqual(e['direction'],-1)
        for clock in ('10:45','10:50','10:55'):
            self.observe(clock,self.bar(clock))
        e=self.observe('11:00',self.rejection('11:00',l='99.96',c='100'))[0]
        self.assertEqual(e['base_reason'],'SIGNAL');self.assertEqual(e['previous_confirmed_start'],self.at('10:30'))

    def test_missing_invalid_and_callback_gap_reset_range_and_dedup(self):
        for b in (None,self.bar('10:35',v='0')):
            self.setUp();self.seed();self.observe('10:30',self.rejection())
            self.observe('10:35',b);self.assertEqual(self.strategy.last_confirmed,{})
            self.assertEqual(len(self.strategy.history),0)
            self.seed('10:40',count=5);self.assertEqual(self.observe('11:05',self.bar('11:05')),[])
            self.assertEqual(self.observe('11:10',self.rejection('11:10'))[0]['base_reason'],'SIGNAL')
        self.setUp();self.seed()
        self.assertEqual(self.observe('10:35',self.bar('10:35'))[0]['reset_reason'],'NONCONSECUTIVE_CALLBACK')

    def test_lunch_and_day_reset(self):
        self.seed();self.observe('10:30',self.rejection())
        self.observe('14:05',self.bar('14:05'))
        self.assertEqual(len(self.strategy.history),1);self.assertEqual(self.strategy.last_confirmed,{})
        self.strategy.begin_day(self.symbol,self.day+timedelta(days=1))
        self.assertEqual(len(self.strategy.history),0)

    def test_march_window_starts_1415(self):
        self.day=date(2023,3,13);self.strategy.begin_day(self.symbol,self.day);self.seed('14:15')
        e=self.observe('14:45',self.rejection('14:45'))[0]
        self.assertEqual(e['range_start'],self.at('14:15'))

    def test_cny_historic_tick_both_regimes(self):
        self.symbol='CNYRUBF'
        for day,t in ((date(2023,9,27),D('.01')),(date(2023,9,28),D('.001'))):
            self.day=day;self.strategy.begin_day(self.symbol,day);self.seed()
            e=self.observe('10:30',self.rejection(l=str(D(100)-t),c=str(D(100)+t)))[0]
            self.assertEqual(e['stop'],D(100)-2*t);self.assertEqual(e['signal_tick'],t)

    def test_uncompleted_bar_rejected(self):
        at=self.at('10:00')
        with self.assertRaisesRegex(ValueError,'UNCOMPLETED'):
            self.strategy.on_bar(self.bar(at),Context(self.symbol,at,at,self.rules.windows(self.day)[0],D('.01'),{}))

    def rows(self,test_clock='10:30',side=1):
        rows={}
        for a,z in self.rules.windows(self.day):
            while a<z:
                rows[a]=self.bar(a);a+=FIVE
        rows[self.at(test_clock)]=self.rejection(test_clock,side=side)
        return dict(sorted(rows.items()))

    def run_engine(self,rows):
        return Backtester(self.rules,daily_trade_deadline_clock='17:00').run(LevelRejection(self.cfg['parameters']),
            self.symbol,rows,start=self.day,end_exclusive=self.day+timedelta(days=1))

    def test_one_waiting_bar_clock_120_minutes_and_full_net_target(self):
        ss,tt,_=self.run_engine(self.rows());q=tt[0]
        self.assertEqual(q['signal_at'],self.at('10:35'));self.assertEqual(q['entry_at'],self.at('10:40'))
        self.assertEqual(q['waiting_bar_closed_at'],self.at('10:40'));self.assertEqual(q['exit_at'],self.at('12:40'))
        self.assertEqual(q['risk'],D('.53'));self.assertEqual(q['d_full'],D('1.67'))
        self.assertEqual(q['d_legacy'],D('1.61'));self.assertEqual(q['take'],D('102.17'))
        self.assertEqual(q['planned_net_to_net_R'],D(3));self.assertEqual(q['cost_c1'],D('.02'))

    def test_Open_reclaim_rejected_long_and_short(self):
        for side,price in ((1,'100'),(-1,'101')):
            rows=self.rows(side=side);rows[self.at('10:40')]=self.bar('10:40',o=price,c=price)
            ss,tt,_=self.run_engine(rows)
            self.assertIn('OPEN_RECLAIM_NOT_PERSISTENT',[s['reason'] for s in ss]);self.assertEqual(tt,[])

    def test_risk_four_ticks_and_invalid_sign(self):
        rows=self.rows();rows[self.at('10:30')]=self.rejection(l='99.99')
        rows[self.at('10:40')]=self.bar('10:40',o='100.01',c='100.01')
        ss,tt,_=self.run_engine(rows);self.assertEqual(tt,[])
        self.assertIn('RISK_BELOW_FOUR_TICKS',[s['reason'] for s in ss])
        rows[self.at('10:40')]=self.bar('10:40',o='100.02',c='100.02')
        self.assertEqual(self.run_engine(rows)[1][0]['risk'],D('.04'))
        # Invalid Stop sign is independently guarded by universal scalar helper.
        from IntradayLab.core.execution import entry_admission
        self.assertEqual(entry_admission(D('100.01'),1,D('100.02'),D('.01'),{}),'INVALID_RISK')

    def test_entry_HLC_volume_cannot_change_Open_admission(self):
        rows=self.rows();rows[self.at('10:40')]=self.bar('10:40',h='200',l='1',v='0')
        ss,tt,_=self.run_engine(rows)
        self.assertTrue(tt[0]['model_filled']);self.assertEqual(tt[0]['unknown_reason'],'INVALID_EXPOSED_BAR')
        signal=next(s for s in ss if s['base_reason']=='SIGNAL')
        self.assertTrue(signal['open_admission_passed'])

    def test_busy_signal_still_consumes_dedup(self):
        rows=self.rows();rows[self.at('11:10')]=self.rejection('11:10')
        rows[self.at('11:15')]=self.rejection('11:15',l='99.97',c='100')
        ss,tt,_=self.run_engine(rows)
        self.assertEqual(len(tt),1);self.assertIn('POSITION_BUSY',[s['reason'] for s in ss])
        self.assertIn('DEDUP_30MIN',[s['reason'] for s in ss])

    def test_dedup_after_Open_nonfill(self):
        rows=self.rows();rows[self.at('10:40')]=self.bar('10:40',o='100',c='100')
        rows[self.at('10:45')]=self.rejection('10:45',l='99.97',c='100')
        ss,_,_=self.run_engine(rows);later=next(s for s in ss if s.get('test_start')==self.at('10:45'))
        self.assertEqual(later['base_reason'],'DEDUP_30MIN')

    def test_take_forbidden_entry_then_actual_net_net_three(self):
        rows=self.rows();rows[self.at('10:40')]=self.bar('10:40',h='103')
        self.assertEqual(self.run_engine(rows)[1][0]['exit_reason'],'TIME')
        rows[self.at('10:45')]=self.bar('10:45',h='103')
        q=self.run_engine(rows)[1][0];self.assertEqual(q['exit_reason'],'TAKE')
        self.assertEqual(q['realized_net_to_net_R'],D(3));self.assertGreater(q['net_R_c1'],D(3))

    def test_stop_first_and_adverse_gap(self):
        rows=self.rows();rows[self.at('10:45')]=self.bar('10:45',h='103',l='99')
        q=self.run_engine(rows)[1][0];self.assertEqual(q['exit_price'],D('99.97'))
        self.assertTrue(q['stop_take_conflict']);self.assertEqual(q['realized_net_to_net_R'],D(-1))
        rows[self.at('10:45')]=self.bar('10:45',o='99',h='99',l='99',c='99')
        q=self.run_engine(rows)[1][0];self.assertEqual(q['exit_price'],D(99))
        self.assertEqual(q['exit_at'],self.at('10:45'));self.assertLess(q['realized_net_to_net_R'],D(-1))

    def test_missing_waiting_entry_exposed_and_exit_keep_unknown(self):
        for clock in ('10:35','10:40','10:45','12:40'):
            rows=self.rows();del rows[self.at(clock)];ss,tt,_=self.run_engine(rows)
            if clock=='10:35':
                self.assertEqual(tt,[]);self.assertIn('NO_WAITING_BAR',[s['reason'] for s in ss])
            else:
                self.assertEqual(tt[0]['status'],'UNKNOWN')
                for key in ('net_R_c1','net_c1','gross','cost_c1','exit_price'):
                    self.assertIsNone(tt[0][key])

    def test_reserve_equality_and_cutoff_morning_and_1700(self):
        for clock,allowed,entry,flat in (('13:15',True,'13:25','13:55'),('13:20',False,None,None),
                ('16:15',True,'16:25','17:00'),('16:20',False,None,None)):
            rows=self.rows(clock);ss,tt,_=self.run_engine(rows)
            if allowed:
                self.assertEqual(tt[0]['entry_at'],self.at(entry));self.assertEqual(tt[0]['exit_at'],self.at(flat))
            else:
                self.assertEqual(tt,[]);self.assertIn('SESSION_ENTRY_CUTOFF',[s['reason'] for s in ss])

    def test_exact_deadline_Open_only_and_missing(self):
        rows=self.rows('16:15');rows[self.at('17:00')]=self.bar('17:00',h='200',l='1',v='0')
        q=self.run_engine(rows)[1][0];self.assertEqual(q['exit_at'],self.at('17:00'))
        self.assertEqual(q['exit_reason'],'TRADE_DEADLINE')
        del rows[self.at('17:00')];self.assertEqual(self.run_engine(rows)[1][0]['status'],'UNKNOWN')

    def test_future_mutation_does_not_change_earlier_signals_or_Open_decision(self):
        rows=self.rows();first=self.run_engine(rows)[0]
        rows[self.at('11:00')]=self.bar('11:00',h='200',l='1');second=self.run_engine(rows)[0]
        self.assertEqual([s for s in first if s['recorded_at']<self.at('11:00')],
                         [s for s in second if s['recorded_at']<self.at('11:00')])


if __name__=='__main__':
    unittest.main()
