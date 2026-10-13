"""Synthetic causal boundary tests for the one preregistered mechanism."""
import unittest
import common as C, engine as E, scalar as S
from test_execution import fixture, frame

class Early(unittest.TestCase):
    def runs(self,b,version='EARLY_PROTECT_05'):
        return [E.replay(frame(b),'USDRUBF',version,'C1','NEXT_OPEN'),S.simulate(b,'USDRUBF',version,'C1','NEXT_OPEN')]
    def target(self,side=1):
        b=fixture(side=side)
        b[1].update(h=101. if side==1 else 100.5,l=98.5 if side==1 else 99.)
        return b
    def test_exact_half_threshold_survived_next_bar_both_sides(self):
        for side in (1,-1):
            b=self.target(side);b[2].update(h=101.5,l=98.5)
            for t,o,d,e,g,sn in self.runs(b):
                self.assertEqual(d[0]['phase'],'SURVIVED');self.assertEqual(d[0]['active_stop'],100-side*2)
                self.assertTrue(d[0]['early_activated_now']);self.assertEqual(d[0]['active_stop_next_bar'],100-side)
                self.assertFalse(d[0]['activated_after']);self.assertEqual(t[0]['gross_R'],-.5)
                self.assertEqual(t[0]['early_activation_time'],b[1]['at']);self.assertEqual(d[1]['phase'],'EXIT')
    def test_below_half_no_activation(self):
        for side in (1,-1):
            b=fixture(side=side);b[1].update(h=100.999 if side==1 else 100.5,l=99.5 if side==1 else 99.001)
            for t,o,d,e,g,sn in self.runs(b):self.assertTrue(all(not r['early_activated_after'] for r in d))
    def test_dead_bar_extrema_cannot_activate(self):
        for side in (1,-1):
            b=fixture(side=side);b[1].update(h=110.,l=90.)
            for t,o,d,e,g,sn in self.runs(b):
                self.assertEqual(t[0]['gross_R'],-1);self.assertFalse(t[0]['early_activated']);self.assertFalse(d[0]['early_activated_now'])
    def test_signal_extrema_cannot_activate(self):
        for side in (1,-1):
            b=fixture(side=side);b[0].update(h=999.,l=-999.)
            for t,o,d,e,g,sn in self.runs(b):self.assertTrue(all(not r['early_activated_after'] for r in d))
    def test_protection_never_weakens_s1_trail(self):
        for side in (1,-1):
            b=fixture(side=side);b[1].update(h=104. if side==1 else 100.5,l=99.5 if side==1 else 96.)
            for t,o,d,e,g,sn in self.runs(b):
                self.assertTrue(d[0]['early_activated_now']);self.assertTrue(d[0]['threshold_activated_now'])
                self.assertFalse(d[0]['early_stop_changed']);self.assertEqual(d[0]['stop_source_next'],'ATR_TRAIL')
                self.assertEqual(d[0]['active_stop_next_bar'],104.-3.75 if side==1 else 96.+3.75)
    def test_adverse_gap_fill_not_assumed_floor(self):
        for side in (1,-1):
            b=self.target(side);b[2].update(o=98.5 if side==1 else 101.5,h=101.5,l=98.5)
            b[2]['at']+=C.STEP*12
            for t,o,d,e,g,sn in self.runs(b):
                self.assertEqual(t[0]['gross_R'],-.75);self.assertTrue(t[0]['gap_exit']);self.assertTrue(d[1]['observed_gap_before_bar'])
    def test_next_observed_bar_can_be_next_day(self):
        b=self.target();b[2]['at']+=C.STEP*96;b[2].update(l=98.5)
        for t,o,d,e,g,sn in self.runs(b):self.assertEqual(t[0]['gross_R'],-.5)
    def test_reentry_occupancy_replayed(self):
        b=self.target();b[2].update(l=98.5,signal=1)
        extra=fixture(['2024-04-01 10:45'],[0])[0];b.append(extra)
        for t,o,d,e,g,sn in self.runs(b):
            self.assertEqual(len(t),1);self.assertTrue(e[-1]['entry_accepted']);self.assertEqual(o['signal_time'],b[2]['at'])
        for t,o,d,e,g,sn in self.runs(b,'TRAIL_375'):
            self.assertFalse(t);self.assertEqual(e[-1]['decision_reason'],'POSITION_OCCUPIED')
    def test_actual_entry_not_signal_close_is_anchor(self):
        for side in (1,-1):
            b=fixture(side=side);b[1].update(o=110.,h=111. if side==1 else 110.5,l=109.5 if side==1 else 109.,c=110.)
            for t,o,d,e,g,sn in self.runs(b[:2]):
                self.assertEqual(o['entry_price'],110.);self.assertEqual(o['initial_risk'],2.)
                self.assertTrue(o['early_activated']);self.assertEqual(o['active_stop'],110-side)
    def test_completed_prefix_invariant(self):
        for side in (1,-1):
            b=self.target(side);c=self.target(side);c[2].update(h=999.,l=-999.)
            for x,y,z in zip(self.runs(b[:2]),self.runs(b),self.runs(c)):
                self.assertEqual(C.plain(x[2]),C.plain(y[2][:1]));self.assertEqual(C.plain(x[2]),C.plain(z[2][:1]))
    def test_floor_then_original_s1(self):
        b=self.target();b[2].update(o=100.,h=105.,l=99.5,c=104.)
        for t,o,d,e,g,sn in self.runs(b):
            self.assertEqual(d[0]['active_stop_next_bar'],99.);self.assertFalse(d[0]['activated_after'])
            self.assertTrue(d[1]['threshold_activated_now']);self.assertEqual(d[1]['active_stop_next_bar'],101.25)
            self.assertEqual(d[1]['stop_source_next'],'ATR_TRAIL')
    def test_early_effect_on_new_exit_bar_does_not_activate_s1(self):
        b=self.target();b[2].update(h=999.,l=98.5)
        for t,o,d,e,g,sn in self.runs(b):
            self.assertFalse(t[0]['threshold_activated']);self.assertEqual(t[0]['MFE_R'],.5)

if __name__=='__main__':unittest.main(verbosity=2)
