"""Independent hand-calculated adversaries for the predeclared M15 contract."""
import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from datetime import datetime as DT,timedelta as TD
from decimal import Decimal as D
from dataclasses import replace
from unittest.mock import patch
from session_mtf import Bar
from squeeze_m15_replay import Replay,Indicators,Cycles,geometry,compose,flat_slot,next_slot,windows,tick
from causal_mtf import DerivedContext
from run_squeeze_m15 import coverage,payoff


def bar(t,o='100',h='100.1',l='99.9',c='100'):
    return Bar(t,D(o),D(h),D(l),D(c),D(1),symbol='USDRUBF')


def signal(t=DT(2023,1,3,12)):
    return dict(signal_id='test',direction='LONG',direction_sign=1,signal_at=t,available_at=t+TD(minutes=20),planned_execution_at=t+TD(minutes=30),range_high=D('100.1'),range_low=D('99.9'),edge=D('100.1'),atr7=D('.4'),stop=D('100'),cap=D('100.3'))


def prepared():
    r=Replay('USDRUBF','SQUEEZE_M15');r.order=signal()
    b=bar(DT(2023,1,3,12,30),'100.18','100.3','100.12','100.2');r.entry(b,b.timestamp+TD(minutes=20));return r


class M15Tests(unittest.TestCase):
    def fixture(self,delay=10,missing=None,short=False,early=False,failed=False):
        class Fixed:
            def __init__(self):self.reset()
            def reset(self):self.n=0
            def observe(self,b):
                self.n+=1
                start=1 if early else 7
                return None if self.n<start else dict(at=b.timestamp,atr7=D('.4'),squeeze=start<=self.n<start+2)
        a=DT(2023,1,3,10);bars=[];off=a+TD(minutes=30 if early else 120)
        for i in range(48):
            t=a+TD(minutes=i*5)
            b=bar(t) if t<off else bar(t,'100.18','100.3','100.12','100.2')
            if failed and DT(2023,1,3,12,45)<=t<DT(2023,1,3,13):b=bar(t,'100.18','100.2','100.04','100.08')
            if short:b=replace(b,open=200-b.open,high=200-b.low,low=200-b.high,close=200-b.close)
            if t!=missing:bars.append(b)
        with patch('squeeze_m15_replay.Indicators',Fixed):return Replay('USDRUBF','SQUEEZE_M15',delay).run(bars)

    def test_same_future_open_for_two_latencies(self):
        for minute in (0,15,30,45):
            t=DT(2023,1,3,11,minute)
            self.assertEqual(next_slot(t+TD(minutes=20)),next_slot(t+TD(minutes=25)))
            self.assertEqual(next_slot(t+TD(minutes=25)),t+TD(minutes=30))

    def test_common_flat_ack_safety(self):
        for w in windows(DT(2023,1,3).date()):
            self.assertLessEqual(flat_slot(w)+TD(minutes=25),w[1]-TD(minutes=10))
        self.assertEqual(flat_slot(windows(DT(2023,1,3).date())[0]),DT(2023,1,3,13,15))

    def test_exact_composition_no_partial_no_clearing(self):
        a=DT(2023,1,3,14);raw=[bar(a+TD(minutes=5*i)) for i in range(15)]
        parents=compose(raw,15)
        self.assertNotIn(a,parents)
        self.assertEqual(parents[a+TD(minutes=15)].volume,3)
        self.assertIsNone(compose([b for b in raw if b.timestamp!=a+TD(minutes=20)],15)[a+TD(minutes=15)])
        self.assertEqual(compose(raw,60)[a+TD(hours=1)],None)

    def test_seven_complete_indicator_seed_and_reset(self):
        f=Indicators();a=DT(2023,1,3,10)
        for i in range(6):self.assertIsNone(f.observe(bar(a+TD(minutes=15*i))))
        q=f.observe(bar(a+TD(minutes=90)))
        self.assertEqual(q['sma7'],100);self.assertEqual(q['atr7'],D('.2'));self.assertTrue(q['squeeze'])
        f.reset();self.assertIsNone(f.observe(bar(a+TD(minutes=120))))

    def test_two_bar_cycle_range_excludes_breakout_consumes_once(self):
        c=Cycles('USDRUBF');a=DT(2023,1,3,11,30)
        for i in range(2):self.assertIsNone(c.observe(bar(a+TD(minutes=15*i)),{'squeeze':True},a+TD(minutes=20+15*i)))
        b=bar(a+TD(minutes=30),'100','101','99','100.2')
        s=c.observe(b,{'squeeze':False},b.timestamp+TD(minutes=20))
        self.assertEqual(s['range_high'],D('100.1'));self.assertEqual(s['squeeze_bars'],2)
        self.assertIsNone(c.observe(b,{'squeeze':False},b.timestamp+TD(minutes=35)))

    def test_geometry_symmetric_net_three_r(self):
        s=signal();g,_=geometry('USDRUBF',s,D('100.18'),s['available_at'])
        self.assertEqual(g['take'],D('100.74'));self.assertGreaterEqual(g['planned_net_RR'],3)
        s.update(direction_sign=-1,edge=D('99.9'),stop=D('100'),cap=D('99.7'))
        q,_=geometry('USDRUBF',s,D('99.82'),s['available_at']);self.assertEqual(q['take'],D('99.26'))

    def test_geometry_nonfill_bounds(self):
        for price,reason in [('100.1','BREAKOUT_NOT_PERSISTENT'),('100.31','EXTENSION_OVER_0_5_ATR'),('100.111','OPEN_OFF_GRID')]:
            self.assertEqual(geometry('USDRUBF',signal(),D(price),DT(2023,1,3,12,30))[1],reason)

    def test_stop_first_and_adverse_gap(self):
        r=prepared();b=bar(DT(2023,1,3,12,45),'99.9','101','99.8','100')
        r.resident(b,b.timestamp+TD(minutes=20));p=r.ledger[0]
        self.assertEqual(p['exit'],D('99.9'));self.assertEqual(p['exit_reason'],'STOP')
        self.assertIn('STOP_FIRST_BOTH_LEVELS',p['flags']);self.assertIn('ADVERSE_STOP_GAP',p['flags'])
        self.assertEqual(p['mfe_R'],0)

    def test_entry_bar_take_forbidden_and_penetration(self):
        r=prepared();b=bar(DT(2023,1,3,12,30),'100.18','101','100.1','100.2')
        r.resident(b,b.timestamp+TD(minutes=20),True);self.assertIsNotNone(r.position)
        b=replace(b,timestamp=DT(2023,1,3,12,45),high=r.position['take'])
        r.resident(b,b.timestamp+TD(minutes=20));self.assertIsNotNone(r.position)
        b=replace(b,high=r.position['take']+D('.01'));r.resident(b,b.timestamp+TD(minutes=20));self.assertEqual(r.ledger[0]['exit_reason'],'TAKE')

    def test_actual_loop_session_and_symmetric_fills(self):
        for delay in (10,15):
            for short in (False,True):
                r=self.fixture(delay,short=short);p=r.ledger[0]
                self.assertEqual(p['entry_at'],DT(2023,1,3,12,30));self.assertEqual(p['exit_at'],DT(2023,1,3,13,15))
                self.assertEqual(p['exit_reason'],'SESSION_FLAT');self.assertFalse(p['flat_target_breach'])

    def test_maxhold_timer_and_failed_breakout_future_only(self):
        p=self.fixture(early=True).ledger[0];self.assertEqual(p['hold_minutes'],120);self.assertEqual(p['exit_reason'],'MAX_HOLD')
        p=self.fixture(failed=True).ledger[0];self.assertEqual(p['exit_at'],DT(2023,1,3,13,15));self.assertEqual(p['exit_reason'],'FAILED_BREAKOUT')

    def test_incomplete_target_unknown_never_zero_nonfill(self):
        r=self.fixture(missing=DT(2023,1,3,12,35));p=r.ledger[0]
        self.assertEqual(p['status'],'UNKNOWN');self.assertIsNone(p['entry']);self.assertIsNone(p['net']);self.assertIsNone(p['initial_risk'])
        self.assertEqual(r.signals[0]['status'],'UNKNOWN_POSSIBLE_ENTRY_FILL');self.assertIsNotNone(p['model_flat_at'])
        q=payoff(r.ledger);self.assertEqual(q['entries'],0);self.assertEqual(q['unknown_entry_orders'],1);self.assertIsNone(q['full_net'])

    def test_missing_exposure_preserves_past_unknown_after_flat(self):
        r=self.fixture(missing=DT(2023,1,3,12,50));p=r.ledger[0]
        self.assertEqual(p['status'],'UNKNOWN');self.assertIsNotNone(p['entry']);self.assertIsNone(p['net']);self.assertIsNotNone(p['model_flat_at'])

    def test_h1_never_stale_fallback_or_gap_bridge(self):
        a=DT(2023,1,3,10);raw=[bar(a+TD(minutes=5*i)) for i in range(48)]
        r=Replay('USDRUBF','SQUEEZE_H1_M15');r.raw_index={b.timestamp:b for b in raw};r.mtf=DerivedContext(raw,60,{'availability_minutes':10})
        self.assertIsNone(r.context(DT(2023,1,3,12,20),windows(a.date())[0],1)[1])
        r.raw_index.pop(DT(2023,1,3,12,5));self.assertEqual(r.context(DT(2023,1,3,12,20),windows(a.date())[0],1)[1],'MTF_CONTINUITY_GAP')
        raw=[b for b in raw if b.timestamp!=DT(2023,1,3,11,5)];r.mtf=DerivedContext(raw,60,{'availability_minutes':10})
        self.assertEqual(r.context(DT(2023,1,3,12,20),windows(a.date())[0],1)[1],'MTF_INCOMPLETE_CHILD_BUCKET')

    def test_dated_cny_each_side_and_c2_identical_execution(self):
        self.assertEqual(tick('CNYRUBF',DT(2023,9,27,18,45)),D('.01'));self.assertEqual(tick('CNYRUBF',DT(2023,9,27,19)),D('.001'))
        r=prepared();r.finish(DT(2023,1,3,13,15),DT(2023,1,3,13,35),D('100.2'),'SESSION_FLAT')
        self.assertEqual(payoff(r.ledger,2)['closed_net'],payoff(r.ledger)['closed_net']-D('.02'))

    def test_source_coverage_keeps_missing_m5_not_only_parent_slots(self):
        months,_=coverage([bar(DT(2023,7,11,10)),bar(DT(2023,7,11,10,5))])
        self.assertEqual(months['2023-07']['observed_slots'],2);self.assertEqual(months['2023-06']['coverage_status'],'NO_COVERAGE');self.assertEqual(months['2023-07']['coverage_status'],'PARTIAL_LAUNCH')

if __name__=='__main__':unittest.main()
