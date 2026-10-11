"""Pre-P&L boundary, causality, geometry and cluster contract scenarios."""
from copy import deepcopy
from datetime import timedelta
from decimal import Decimal as D
import json
from pathlib import Path
import unittest

from IntradayLab.core.backtester import Backtester
from IntradayLab.core.execution import ENTRY_NEXT_OPEN, ENTRY_WAIT_ONE_BAR, entry_admission
from IntradayLab.core.models import Context
from IntradayLab.strategies.equal_high_low_m5 import EqualHighLowM5
from IntradayLab.tests import test_universal_backtester as fixtures
TimedStrategy, FIVE = fixtures.TimedStrategy, fixtures.FIVE

PARAMETERS = dict(version='A_v1', signal_tf='M5', touches=3, tolerance_ticks=0,
    stop_buffer_ticks=1, minimum_risk_ticks=3, maximum_risk_ticks=12,
    maximum_rebound_ticks=4, target_net_R='3', target_mode='FULL_NET_C1_R',
    max_hold_calendar_minutes=120)


class NextOpenTests(unittest.TestCase):
    setUp = fixtures.EngineTests.setUp
    at = fixtures.EngineTests.at
    bar = fixtures.EngineTests.bar
    make_day = fixtures.EngineTests.make_day

    def run_clock(self, strategy=None, rows=None, mode=ENTRY_NEXT_OPEN, end=None):
        return Backtester(self.rules, entry_mode=mode).run(
            strategy or TimedStrategy([self.at('10:20')]), 'USDRUBF',
            self.rows if rows is None else rows, start=self.day,
            end_exclusive=end or self.day+timedelta(days=1))

    def setup_cluster(self, side=-1):
        for i, clock in enumerate(('10:00','10:05','10:10')):
            at=self.at(clock)
            self.rows[at]=self.bar(at, o='100.97', h='101',
                l=str(D('100.90')-i*D('.01')), c='100.97') if side==-1 else self.bar(
                    at,o='101.03',h=str(D('101.10')+i*D('.01')),l='101',c='101.03')
        at=self.at('10:15')
        self.rows[at]=self.bar(at,o='100.97' if side==-1 else '101.03',
            h='101.06',l='100.94',c='101')

    def test_next_boundary_no_wait(self):
        self.rows[self.at('10:20')]=self.bar(self.at('10:20'),o='100.85')
        s,t,_=self.run_clock()
        self.assertEqual(t[0]['entry_at'],s[0]['signal_at'])
        self.assertEqual(t[0]['entry_price'],D('100.85'))
        self.assertIsNone(t[0]['waiting_bar_closed_at'])
        self.assertEqual(t[0]['entry_mode'],ENTRY_NEXT_OPEN)

    def test_default_is_exact_legacy_output(self):
        s=TimedStrategy([self.at('10:20')])
        old=Backtester(self.rules).run(s,'USDRUBF',self.rows,start=self.day,
            end_exclusive=self.day+timedelta(days=1))
        explicit=self.run_clock(mode=ENTRY_WAIT_ONE_BAR)
        self.assertEqual(old,explicit)
        self.assertEqual(old[1][0]['entry_at'],self.at('10:25'))
        self.assertNotIn('entry_mode',old[1][0])

    def test_open_only_invalid_current_hlc_does_not_reject_fill(self):
        self.rows[self.at('10:20')]=self.bar(self.at('10:20'),h='99',v='0')
        _,tt,_=self.run_clock()
        self.assertTrue(tt[0]['model_filled'])
        self.assertEqual(tt[0]['unknown_reason'],'INVALID_EXPOSED_BAR')
        self.assertIsNone(tt[0]['net_R_c1'])

    def test_missing_next_open_never_falls_forward(self):
        del self.rows[self.at('10:20')]
        _,tt,_=self.run_clock()
        self.assertFalse(tt[0]['model_filled'])
        self.assertEqual(tt[0]['unknown_reason'],'MISSING_EXECUTION_BAR')
        self.assertIsNone(tt[0]['entry_at'])
        self.assertIsNone(tt[0]['entry_price'])

    def test_off_grid_next_open_unknown(self):
        self.rows[self.at('10:20')]=self.bar(self.at('10:20'),o='100.901')
        ss,tt,_=self.run_clock()
        self.assertEqual(ss[0]['reason'],'INVALID_EXECUTION_OPEN')
        self.assertIsNone(tt[0]['cost_c1'])

    def test_stop_first_entry_interval_and_gap_precedence(self):
        self.rows[self.at('10:20')]=self.bar(self.at('10:20'),h='101.10',l='100.50')
        _,tt,_=self.run_clock()
        self.assertEqual(tt[0]['exit_reason'],'STOP')
        self.assertTrue(tt[0]['stop_take_conflict'])
        self.rows[self.at('10:20')]=self.bar(self.at('10:20'),l='100.85')
        self.rows[self.at('10:25')]=self.bar(self.at('10:25'),o='101.10',h='101.20',l='101.05',c='101.10')
        _,tt,_=self.run_clock()
        self.assertEqual(tt[0]['exit_at'],self.at('10:25'))
        self.assertEqual(tt[0]['exit_price'],D('101.10'))

    def test_exit_then_signal_same_m5_boundary(self):
        self.rows[self.at('10:20')]=self.bar(self.at('10:20'),h='101.10')
        s,t,_=self.run_clock(TimedStrategy([self.at('10:20'),self.at('10:25')]))
        self.assertTrue(s[1]['model_filled'])
        self.assertEqual(t[1]['entry_at'],self.at('10:25'))

    def test_session_flat_and_no_entry_at_flat(self):
        s,t,_=self.run_clock(TimedStrategy([self.at('13:50'),self.at('13:55')]))
        self.assertEqual(t[0]['exit_at'],self.at('13:55'))
        self.assertEqual(t[0]['exit_reason'],'SESSION_FLAT')
        self.assertEqual(s[1]['reason'],'SESSION_LIMIT')

    def test_future_mutation_does_not_change_signal_or_entry(self):
        self.setup_cluster()
        original=self.run_clock(EqualHighLowM5(PARAMETERS))
        self.rows[self.at('10:15')]=self.bar(self.at('10:15'),o='100.97',h='150',l='90',c='95')
        altered=self.run_clock(EqualHighLowM5(PARAMETERS))
        for key in ('signal_id','signal_at','cluster_level','stop','entry_open','risk','take'):
            self.assertEqual(original[0][0][key],altered[0][0][key])
        self.assertEqual(original[1][0]['entry_price'],altered[1][0]['entry_price'])

    def test_real_open_stop_and_full_net_target_mirrored(self):
        for side in (-1,1):
            self.setup_cluster(side)
            s,t,_=self.run_clock(EqualHighLowM5(PARAMETERS))
            q=t[0]
            self.assertEqual(q['direction'],side)
            self.assertEqual(q['risk'],D('.04'))
            self.assertEqual(q['stop'],D('101')-side*D('.01'))
            self.assertEqual(side*(q['take']-q['entry_price']),D('.20'))
            self.assertEqual(q['planned_net_to_net_R'],D(3))

    def test_all_entry_rejections_before_fill(self):
        cases=[('101.01','OPEN_WRONG_SIDE_OF_CLUSTER'),
            ('101','STOP_BELOW_3_TICKS'),('100.99','STOP_BELOW_3_TICKS'),
            ('100.95','ENTRY_MORE_THAN_4_TICKS_FROM_CLUSTER'),
            ('100.87','STOP_ABOVE_12_TICKS')]
        for op,reason in cases:
            self.setup_cluster()
            at=self.at('10:15')
            self.rows[at]=self.bar(at,o=op,h='101.1',l='100.8',c=op)
            s,t,_=self.run_clock(EqualHighLowM5(PARAMETERS))
            self.assertEqual(s[0]['reason'],reason)
            self.assertFalse(s[0]['model_filled'])
            self.assertFalse(any(q['signal_id']==s[0]['signal_id'] for q in t))

    def test_dated_grid_and_upper_admission_bounds(self):
        before=self.rules.at(self.day,'10:00')
        after=self.rules.at(__import__('datetime').date(2023,9,28),'10:00')
        self.assertEqual(self.rules.tick('CNYRUBF',before),D('.01'))
        self.assertEqual(self.rules.tick('CNYRUBF',after),D('.001'))
        for t in (D('.01'),D('.001'),D('.1'),D('.5')):
            c=dict(directional_reference=D(100),minimum_reference_ticks=0,
                maximum_reference_ticks=4,minimum_risk_ticks=3,maximum_risk_ticks=12)
            for side in (-1,1):
                stop=D(100)-side*t
                self.assertIsNone(entry_admission(D(100)+side*2*t,side,stop,t,c))
                self.assertIsNone(entry_admission(D(100)+side*4*t,side,stop,t,c))
                self.assertEqual(entry_admission(D(100)+side*5*t,side,stop,t,c),'OPEN_REFERENCE_TOO_FAR')

    def test_mode_restrictions(self):
        with self.assertRaisesRegex(ValueError,'UNAPPROVED_ENTRY_MODE'):
            Backtester(self.rules,entry_mode='ENTRY_CLOSE_ORACLE')
        with self.assertRaisesRegex(ValueError,'REQUIRES_M5'):
            Backtester(self.rules,entry_mode=ENTRY_NEXT_OPEN,timeframe_minutes=15)


class ClusterTests(unittest.TestCase):
    setUp = fixtures.EngineTests.setUp
    at = fixtures.EngineTests.at
    bar = fixtures.EngineTests.bar
    make_day = fixtures.EngineTests.make_day
    # Explicit callbacks isolate signal grammar from the execution engine.
    def feed(self, specs, gaps=(), window_shift=None):
        st=EqualHighLowM5(PARAMETERS);st.begin_day('USDRUBF',self.day)
        events=[]
        for i,(h,l,c) in enumerate(specs):
            at=self.at('10:00')+i*FIVE
            b=None if i in gaps else self.bar(at,o=c,h=h,l=l,c=c)
            w=(self.at('10:00'),self.at('14:00')) if window_shift!=i else (at,self.at('14:00'))
            ctx=Context('USDRUBF',at,at+FIVE,w,D('.01'),{})
            events.extend(st.on_bar(b,ctx))
        return events

    def test_exact_three_completed_highs_and_no_tolerance(self):
        base=[('101',str(D('100')-i*D('.01')),'100.98') for i in range(3)]
        self.assertEqual(len(self.feed(base)),1)
        self.assertEqual(self.feed(base)[0]['signal_at'],self.at('10:15'))
        self.assertEqual(self.feed(base[:2]),[])
        base[1]=('101.01','99.99','100.98')
        self.assertEqual(self.feed(base),[])

    def test_consumed_run_rearms_only_after_changed_extreme(self):
        specs=[('101',str(D('100')-i*D('.01')),'100.98') for i in range(5)]
        specs += [('101.01','99.90','100.98')]
        specs += [('101',str(D('99.80')-i*D('.01')),'100.98') for i in range(3)]
        e=self.feed(specs)
        self.assertEqual(len(e),2)
        self.assertNotEqual(e[0]['cluster_id'],e[1]['cluster_id'])
        self.assertEqual(e[0]['cluster_start'],self.at('10:00'))
        self.assertEqual(e[1]['cluster_start'],self.at('10:30'))

    def test_close_at_level_delays_first_qualifying_window(self):
        specs=[('101',str(D('100')-i*D('.01')),'101') for i in range(3)]
        self.assertEqual(self.feed(specs),[])
        specs.append(('101','99.97','100.98'))
        e=self.feed(specs)
        self.assertEqual(len(e),1)
        self.assertEqual(e[0]['cluster_run_bars'],4)
        self.assertEqual(e[0]['touch_1_start'],self.at('10:05'))

    def test_ambiguous_both_rejected_and_consumed(self):
        e=self.feed([('101','100','100.5')]*5)
        self.assertEqual(len(e),2)
        self.assertTrue(all(x['base_reason']=='AMBIGUOUS_BOTH_SIDES' for x in e))
        self.assertEqual({x['direction'] for x in e},{-1,1})

    def test_gap_session_and_missing_reset(self):
        specs=[('101',str(D('100')-i*D('.01')),'100.98') for i in range(4)]
        self.assertEqual(self.feed(specs,gaps=(1,)),[])
        self.assertEqual(self.feed(specs,window_shift=2),[])

    def test_uncompleted_or_misaligned_rejected(self):
        st=EqualHighLowM5(PARAMETERS);st.begin_day('USDRUBF',self.day)
        at=self.at('10:00');b=self.bar(at)
        ctx=Context('USDRUBF',at,at+timedelta(minutes=4),
            (at,self.at('14:00')),D('.01'),{})
        with self.assertRaisesRegex(ValueError,'UNCOMPLETED'):
            st.on_bar(b,ctx)

    def test_parameters_cannot_be_tuned(self):
        for key,value in [('touches',4),('tolerance_ticks',1),('target_net_R','5')]:
            with self.assertRaisesRegex(ValueError,'UNAPPROVED'):
                EqualHighLowM5(dict(PARAMETERS,**{key:value}))


if __name__=='__main__':
    unittest.main()
