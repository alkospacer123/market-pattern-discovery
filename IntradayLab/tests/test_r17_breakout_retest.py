"""R17 causal grammar and shared-engine deadlines; synthetic data only."""
from copy import deepcopy
from datetime import date, timedelta
from decimal import Decimal as D
import json
from pathlib import Path
import unittest

from IntradayLab.core.backtester import Backtester
from IntradayLab.core.calendar import MarketRules
from IntradayLab.core.data_loader import validate_bar
from IntradayLab.core.metrics import summarize, distribution_metrics, assess_baseline
from IntradayLab.core.models import Context
from IntradayLab.strategies.orb_breakout_retest import ORBBreakoutRetest

CONFIG = Path(__file__).resolve().parents[1]/'config/r17_orb_breakout_retest_2023_m5_v1.json'
FIVE = timedelta(minutes=5)


class R17Tests(unittest.TestCase):
    def setUp(self):
        self.cfg = json.loads(CONFIG.read_text())
        self.rules = MarketRules(self.cfg)
        self.day = date(2023, 1, 4)
        self.strategy = ORBBreakoutRetest(self.cfg['parameters'])
        self.strategy.begin_day('USDRUBF', self.day)

    def at(self, clock):
        return self.rules.at(self.day, clock)

    def bar(self, clock, o='101.1', h='101.2', l='101', c='101.1', v='10'):
        at = self.at(clock)
        return validate_bar(at, tuple(map(D, (o, h, l, c, v))), FIVE, self.rules.tick('USDRUBF', at))

    def observe(self, clock, bar=None, atr='1'):
        at = self.at(clock)
        window = next(w for w in self.rules.windows(self.day) if w[0] <= at < w[1])
        ctx = Context('USDRUBF', at, at+FIVE, window, D('.01'),
                      {'atr14':D(atr) if atr is not None else None, 'observed_bars':14})
        return self.strategy.on_bar(bar, ctx)

    def opening(self, high='101', low='100'):
        for clock in ('10:00','10:05','10:10'):
            self.observe(clock, self.bar(clock, o='100.5', h=high, l=low, c='100.5'))

    def onset(self, side=1):
        self.opening()
        b = self.bar('10:15', o='101', h='101.5', l='101', c='101.3') if side == 1 else self.bar(
            '10:15', o='100', h='100', l='99.5', c='99.7')
        return self.observe('10:15', b)

    def test_or_unavailable_until_exact_third_close(self):
        for clock in ('10:00','10:05'):
            self.observe(clock, self.bar(clock, o='100.5',h='101',l='100',c='100.5'))
        self.assertIsNone(self.strategy.bounds)
        self.observe('10:10',self.bar('10:10',o='100.5',h='101',l='100',c='100.5'))
        self.assertEqual(self.strategy.bounds,(D(101),D(100)))

    def test_missing_or_never_replaced(self):
        self.observe('10:00',self.bar('10:00'))
        self.observe('10:05',None)
        self.observe('10:10',self.bar('10:10'))
        self.observe('10:15',self.bar('10:15',h='200',c='150'))
        self.assertIsNone(self.strategy.bounds)
        self.assertEqual(self.strategy.end_day()[0]['base_reason'],'NO_OR')

    def test_invalid_or_unavailable(self):
        self.observe('10:00',self.bar('10:00',v='0'))
        for clock in ('10:05','10:10'):
            self.observe(clock,self.bar(clock))
        self.assertIsNone(self.strategy.bounds)

    def test_breakout_bar_never_retests_itself(self):
        self.assertEqual(self.onset(),[])
        self.assertIn(1,self.strategy.pending)
        self.assertEqual(self.strategy.pending[1]['next_start'],self.at('10:20'))

    def test_long_retest_mid_stop(self):
        self.onset()
        s=self.observe('10:20',self.bar('10:20'))[0]
        self.assertEqual(s['base_reason'],'SIGNAL')
        self.assertEqual(s['stop'],D('100.49'))
        self.assertEqual(s['signal_at'],self.at('10:25'))
        self.assertEqual(s['breakout_atr14'],D(1))

    def test_short_retest_mid_stop(self):
        self.onset(-1)
        s=self.observe('10:20',self.bar('10:20',o='99.9',h='100',l='99.8',c='99.9'))[0]
        self.assertEqual(s['base_reason'],'SIGNAL')
        self.assertEqual(s['stop'],D('100.51'))

    def test_midpoint_half_tick_rounds_up_on_both_sides(self):
        for side,stop in ((1,'100.50'),(-1,'100.52')):
            self.strategy.begin_day('USDRUBF',self.day)
            self.opening(high='101.01')
            b=self.bar('10:15',o='101',h='101.5',c='101.4') if side==1 else self.bar('10:15',o='100',h='100',l='99.5',c='99.7')
            self.observe('10:15',b)
            b=self.bar('10:20',o='101.01',h='101.2',l='101.01',c='101.01') if side==1 else self.bar('10:20',o='99.9',h='100',l='99.8',c='99.9')
            s=self.observe('10:20',b)[0]
            self.assertEqual(s['or_mid_rounded'],D('100.51'))
            self.assertEqual(s['stop'],D(stop))

    def test_exact_touch_boundary_is_allowed(self):
        self.onset()
        s=self.observe('10:20',self.bar('10:20',o='101.1',l='101.02'))[0]
        self.assertEqual(s['base_reason'],'SIGNAL')

    def test_retest_below_or_low_rejected(self):
        self.onset()
        self.assertEqual(self.observe('10:20',self.bar('10:20',l='99.99'))[0]['base_reason'],'NO_RETEST_CONDITION')

    def test_short_retest_above_or_high_rejected(self):
        self.onset(-1)
        s=self.observe('10:20',self.bar('10:20',o='99.9',h='101.01',l='99.8',c='99.9'))[0]
        self.assertEqual(s['base_reason'],'NO_RETEST_CONDITION')

    def test_missing_retest_consumes_first_attempt(self):
        self.onset()
        self.assertEqual(self.observe('10:20')[0]['base_reason'],'NO_RETEST_MISSING_BAR')
        self.assertEqual(self.observe('10:25',self.bar('10:25',h='102',c='101.5')),[])
        self.assertIn(1,self.strategy.used)

    def test_invalid_retest_consumes_attempt(self):
        self.onset()
        self.assertEqual(self.observe('10:20',self.bar('10:20',v='0'))[0]['base_reason'],'NO_RETEST_INVALID_BAR')

    def test_later_bar_cannot_replace_successor(self):
        self.onset()
        self.assertEqual(self.observe('10:25',self.bar('10:25'))[0]['base_reason'],'NO_RETEST_WINDOW')

    def test_last_noon_start_diagnoses_no_successor(self):
        self.opening()
        s=self.observe('12:55',self.bar('12:55',h='102',c='101.5'))[0]
        self.assertEqual(s['base_reason'],'NO_RETEST_WINDOW')
        self.assertEqual(self.observe('14:05',self.bar('14:05')),[])

    def test_march_signal_window_intersection(self):
        self.day=date(2023,3,13)
        self.strategy.begin_day('USDRUBF',self.day)
        self.opening()
        self.observe('14:15',self.bar('14:15',h='102',c='101.5'))
        self.assertEqual(self.strategy.pending[1]['window'][0],self.at('14:15'))

    def test_no_atr_no_breakout_attempt(self):
        self.opening()
        self.assertEqual(self.observe('10:15',self.bar('10:15',h='102',c='101.5'),atr=None)[0]['base_reason'],'ATR_UNAVAILABLE')
        self.assertEqual(self.strategy.used,set())

    def rows(self):
        rows={}
        for a,z in self.rules.windows(self.day):
            while a<z:
                rows[a]=validate_bar(a,tuple(map(D,('101.1','101.2','101','101.1','10'))),FIVE,D('.01'))
                a+=FIVE
        for clock in ('10:00','10:05','10:10'):
            rows[self.at(clock)]=self.bar(clock,o='100.5',h='101',l='100',c='100.5')
        # Genuine preceding-day observations keep the infrastructure warm-up.
        for i in range(14):
            at=self.at('09:00')-timedelta(days=1)+i*FIVE
            rows[at]=validate_bar(at,tuple(map(D,('100.5','101','100','100.5','10'))),FIVE,D('.01'))
        rows[self.at('10:15')]=self.bar('10:15',o='101',h='101.5',l='101',c='101.3')
        return dict(sorted(rows.items()))

    def run_engine(self, rows):
        return Backtester(self.rules,daily_trade_deadline_clock='17:00').run(
            ORBBreakoutRetest(self.cfg['parameters']),'USDRUBF',rows,
            start=self.day,end_exclusive=self.day+timedelta(days=1))

    def test_shared_wait_clock_and_120_calendar_minutes(self):
        ss,tt,_=self.run_engine(self.rows())
        q=tt[0]
        self.assertEqual(q['entry_at'],self.at('10:30'))
        self.assertEqual(q['exit_at'],self.at('12:30'))
        self.assertEqual(q['exit_reason'],'TIME')
        self.assertEqual(q['cost_c1'],D('.02'))

    def test_future_suffix_does_not_change_prior_signals(self):
        rows=self.rows(); first=self.run_engine(rows)[0]
        rows[self.at('11:00')]=self.bar('11:00',h='200',l='1')
        second=self.run_engine(rows)[0]
        self.assertEqual([s for s in first if s['recorded_at']<self.at('11:00')],
                         [s for s in second if s['recorded_at']<self.at('11:00')])

    def test_invalid_entry_geometry_diagnostic(self):
        rows=self.rows();rows[self.at('10:30')]=self.bar('10:30',o='100.49',h='100.6',l='100.4',c='100.5')
        ss,tt,_=self.run_engine(rows)
        self.assertEqual(ss[0]['reason'],'INVALID_STOP_GEOMETRY')
        self.assertEqual(tt,[])

    def test_generic_deadline_exact_open_and_no_entry_at_deadline(self):
        from IntradayLab.tests.test_universal_backtester import TimedStrategy
        rows=self.rows()
        for at in list(rows):
            if at.date()==self.day:
                rows[at]=self.bar(at.strftime('%H:%M'),o='100.9',h='100.95',l='100.8',c='100.9')
        rows[self.at('17:00')]=self.bar('17:00',o='100.9',h='200',l='1',v='0')
        s=TimedStrategy([self.at('16:00'),self.at('17:00')])
        ss,tt,_=Backtester(self.rules,daily_trade_deadline_clock='17:00').run(s,'USDRUBF',rows,start=self.day,end_exclusive=self.day+timedelta(days=1))
        self.assertEqual(tt[0]['exit_at'],self.at('17:00'))
        self.assertEqual(tt[0]['exit_reason'],'TRADE_DEADLINE')
        self.assertEqual(ss[1]['reason'],'TRADE_DEADLINE')

    def test_stop_gap_precedes_deadline(self):
        from IntradayLab.tests.test_universal_backtester import TimedStrategy
        rows=self.rows()
        for at in list(rows):
            if at.date()==self.day:
                rows[at]=self.bar(at.strftime('%H:%M'),o='100.9',h='100.95',l='100.8',c='100.9')
        rows[self.at('17:00')]=self.bar('17:00',o='102',h='102',l='102',c='102')
        _,tt,_=Backtester(self.rules,daily_trade_deadline_clock='17:00').run(TimedStrategy([self.at('16:00')]),'USDRUBF',rows,start=self.day,end_exclusive=self.day+timedelta(days=1))
        self.assertEqual(tt[0]['exit_reason'],'STOP')

    def test_missing_deadline_open_remains_unknown(self):
        from IntradayLab.tests.test_universal_backtester import TimedStrategy
        rows=self.rows()
        for at in list(rows):
            if at.date()==self.day:
                rows[at]=self.bar(at.strftime('%H:%M'),o='100.9',h='100.95',l='100.8',c='100.9')
        del rows[self.at('17:00')]
        _,tt,_=Backtester(self.rules,daily_trade_deadline_clock='17:00').run(TimedStrategy([self.at('16:00')]),'USDRUBF',rows,start=self.day,end_exclusive=self.day+timedelta(days=1))
        self.assertEqual(tt[0]['status'],'UNKNOWN')
        self.assertIsNone(tt[0]['net_R_c1'])

    def test_assessment_is_computed_and_sparse_high_pf_inconclusive(self):
        trades=[dict(status='CLOSED',model_filled=True,signal_id=str(i),signal_at=f'2023-{i%6+1:02d}-{i//6+1:02d}',resolved_at=str(i),net_R_c1=D('2') if i%3 else D('-1'),net_c1=D('2') if i%3 else D('-1'),cost_c1=D('.02'),exit_reason='TIME') for i in range(36)]
        summary=summarize(trades,[],[{'status':'COMPLETE'}])
        dist=distribution_metrics(trades)
        result=assess_baseline(summary,dist,self.cfg['classification_policy'])
        self.assertEqual(result['status'],'ECONOMICALLY_PROMISING_BASELINE')
        small=trades[:3]
        self.assertEqual(assess_baseline(summarize(small,[],[{'status':'COMPLETE'}]),distribution_metrics(small),self.cfg['classification_policy'])['status'],'INCONCLUSIVE')
        summary['annual_complete']=False
        self.assertEqual(assess_baseline(summary,dist,self.cfg['classification_policy'])['status'],'INCONCLUSIVE')


if __name__=='__main__':
    unittest.main()
