"""Meaningful causality, cost and unknown-outcome regressions for new exits."""
import io
import json
from datetime import datetime,timedelta
from decimal import Decimal as D
from pathlib import Path
import sys
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from m5_conditional_v2 import Replay, FIVE
from session_mtf import Bar
from stage2_architecture_analysis import Indicators, attribution
from stage2_architecture_replay import ArchitectureReplay, ArchitectureFeatures
from independent_corrective_review import aggregate, exact_lines

LAB=Path(__file__).resolve().parents[1]
M=json.loads((LAB/'config/stage2_complete_architectures_v1.json').read_text())
P=M['parameters']; DEFAULTS=M['defaults']; T=datetime(2023,1,3,10)

def bar(t,o='100',h='100.2',l='99.8',c='100',symbol='USDRUBF'):
    return Bar(t,*map(D,(o,h,l,c,'10')),symbol=symbol)


def opened(strategy='MOMENTUM'):
    r=ArchitectureReplay('USDRUBF',strategy,P,'MANAGEMENT',DEFAULTS)
    b=bar(T+10*FIVE)
    f={'atr':D(1),'vwap':D(103),'range_high':D('99.5'),'range_low':D(98),strategy:1}
    Replay.decision(r,b,b.timestamp+2*FIVE,f)
    r.signals[0].update(swing_low=D('99.5'),swing_high=D('100.2'))
    at=T+13*FIVE
    r.execute(bar(at),at+2*FIVE)
    r.current_context={'atr14':D(1)}
    return r,at


class ArchitectureCausality(unittest.TestCase):
    def test_wilder_initialization_and_gap_reset(self):
        ind=Indicators()
        for i in range(27):
            x=D(100)+D(i)/2
            c=ind.observe(bar(T+i*FIVE,str(x),str(x+D('.5')),str(x-D('.5')),str(x)))
        self.assertIsNone(c['adx14'])
        x=D('113.5')
        c=ind.observe(bar(T+27*FIVE,str(x),str(x+D('.5')),str(x-D('.5')),str(x)))
        self.assertEqual(c['adx14'],100)
        self.assertGreater(c['plus_di14'],c['minus_di14'])
        self.assertIsNone(ind.observe(bar(T+29*FIVE))['adx14'])

    def test_indicator_window_reset_no_overnight_carry(self):
        ind=Indicators()
        for i in range(40):ind.observe(bar(T+i*FIVE))
        self.assertIsNotNone(ind.adx)
        self.assertIsNone(ind.observe(bar(datetime(2023,1,4,10)))['adx14'])
        self.assertIsNone(ind.observe(bar(datetime(2023,1,4,14,5)))['adx14'])

    def test_features_reject_early_delivery(self):
        f=ArchitectureFeatures(P,Indicators(),False)
        with self.assertRaises(ValueError):f.observe(bar(T),T+FIVE)

    def test_unavailable_future_stop_amendment_does_not_touch_elapsed_bar(self):
        r,at=opened()
        b=bar(at+FIVE,o='101.4',h='101.7',l='101.3',c='101.6')
        r.manage(b,b.timestamp+2*FIVE,None)
        self.assertEqual(r.pending_amendments[0]['effective_at'],at+4*FIVE)
        r.execute(bar(at+2*FIVE,l='99.5'),at+4*FIVE)
        self.assertIsNotNone(r.position)
        self.assertEqual(r.position.stop,D('98.5'))
        r.execute(bar(at+4*FIVE,o='100.05',h='100.1',l='99.9',c='100'),at+6*FIVE)
        self.assertIsNone(r.position)
        self.assertEqual(r.ledger[0]['exit_reason'],'BREAKEVEN_STOP')
        self.assertEqual(r.ledger[0]['net_model_c1'],ZERO)

    def test_pending_amendments_keep_earlier_effective_time(self):
        r,at=opened()
        b=bar(at+FIVE,o='101.4',h='101.7',l='101.3',c='101.6')
        r.manage(b,b.timestamp+2*FIVE,None)
        b2=bar(at+2*FIVE,o='103',h='103.3',l='102.9',c='103.1')
        r.manage(b2,b2.timestamp+2*FIVE,None)
        self.assertEqual([a['effective_at'] for a in r.pending_amendments],[at+4*FIVE,at+5*FIVE])
        r.execute(bar(at+4*FIVE,o='102',h='102.1',l='101.8',c='102'),at+6*FIVE)
        self.assertEqual(r.position.stop,D('100.02'))
        r.execute(bar(at+5*FIVE,o='102',h='102.1',l='101.8',c='102'),at+7*FIVE)
        self.assertEqual(r.position.stop,D('101.3'))

    def test_intrabar_high_does_not_arm_be_or_trail(self):
        r,at=opened()
        r.manage(bar(at+FIVE,h='104',l='99.9',c='100'),at+3*FIVE,None)
        self.assertFalse(r.pending_amendments)

    def test_failed_breakout_uses_future_open_not_observed_close(self):
        r,at=opened()
        b=bar(at+FIVE,o='100',h='100.1',l='99.2',c='99.4')
        now=b.timestamp+2*FIVE;r.manage(b,now,None)
        self.assertEqual(r.close_order['reason'],'FAILED_BREAKOUT')
        self.assertEqual(r.close_order['target'],now+FIVE)
        r.execute(bar(now+FIVE,o='99.3',h='99.5',l='99.1',c='99.4'),now+3*FIVE)
        self.assertEqual(r.ledger[0]['exit'],D('99.3'))

    def test_runner_can_pass_original_fixed_take_without_exit(self):
        r,at=opened()
        r.execute(bar(at+FIVE,o='102.9',h='104',l='102.8',c='103.8'),at+3*FIVE)
        self.assertIsNotNone(r.position)
        self.assertEqual(r.ledger[0]['take'],D('103'))

    def test_gap_through_be_is_adverse_open_not_fictitious_zero(self):
        r,at=opened()
        r.manage(bar(at+FIVE,o='101.4',h='101.7',l='101.3',c='101.6'),at+3*FIVE,None)
        r.execute(bar(at+4*FIVE,o='99.9',h='100',l='99.8',c='99.9'),at+6*FIVE)
        self.assertEqual(r.ledger[0]['exit'],D('99.9'))
        self.assertLess(r.ledger[0]['net_model_c1'],0)

    def test_stop_can_only_tighten(self):
        r,at=opened()
        r.manage(bar(at+FIVE,o='103',h='103.3',l='102.9',c='103.1'),at+3*FIVE,None)
        old=r.pending_amendments[-1]['stop']
        r.current_context={'atr14':D(2)}
        r.manage(bar(at+2*FIVE,o='102',h='102.1',l='101.9',c='102'),at+4*FIVE,None)
        self.assertEqual(r.pending_amendments[-1]['stop'],old)

    def test_unknown_path_cannot_trigger_numeric_management(self):
        r,at=opened();r.position.flags.add('UNKNOWN_PATH_OUTCOME')
        r.manage(bar(at+FIVE,o='104',h='104.1',l='103.9',c='104'),at+3*FIVE,None)
        self.assertFalse(r.pending_amendments)
        self.assertIsNone(r.close_order)

    def test_vwap_take_is_frozen_and_premise_exit_is_scheduled(self):
        r,at=opened('VWAP_MR')
        b=bar(at+FIVE,o='100',h='100.1',l='99.2',c='99.4')
        r.manage(b,at+3*FIVE,None)
        self.assertEqual(r.ledger[0]['take'],D(103))
        self.assertEqual(r.close_order['reason'],'VWAP_PREMISE_FAILED')
        self.assertEqual(r.close_order['target'],at+4*FIVE)

    def test_cost_guard_uses_dated_cny_ticks(self):
        r=ArchitectureReplay('CNYRUBF','VWAP_MR',P,'ENTRY',DEFAULTS)
        s={'direction_sign':1,'planned_execution_at':'2023-01-03 11:00:00','stop':D('6.95'),'take':D('7.08')}
        self.assertEqual(r.gate_entry(s,D(7)),'NET_TARGET_BELOW_NET_RISK')
        s['planned_execution_at']='2023-09-28 11:00:00'
        self.assertIsNone(r.gate_entry(s,D(7)))

    def test_momentum_guard_rejects_late_inside_and_overextended_fills(self):
        r=ArchitectureReplay('USDRUBF','MOMENTUM',P,'ENTRY',DEFAULTS)
        s={'direction_sign':1,'planned_execution_at':'2023-01-03 11:00:00','stop':D(98),'take':D(106),
            'range_high_shifted':D(100),'range_low_shifted':D(97),'atr_shifted':D(1)}
        self.assertEqual(r.gate_entry(s,D(100)),'BREAKOUT_NOT_PERSISTENT')
        self.assertEqual(r.gate_entry(s,D('101.1')),'BREAKOUT_ALREADY_EXTENDED')
        self.assertIsNone(r.gate_entry(s,D('100.5')))

    def test_unknown_and_partial_calendar_full_metrics_remain_null(self):
        r,at=opened();row=r.ledger[0]|{'status':'UNRESOLVED','net_model_c1':None,'exit_reason':'UNKNOWN'}
        out=aggregate([row],'COVERED')
        self.assertIsNone(out['Net']);self.assertIsNone(out['full_PF'])
        row.update(status='MODELLED',net_model_c1=D(1),gross_price_pnl=D('1.02'),c1_total=D('.02'))
        self.assertIsNone(aggregate([row],'PARTIAL_COVERAGE')['Net'])

    def test_exit_bar_extrema_not_presumed_achieved_before_exit(self):
        r,at=opened();r.execute(bar(at+FIVE,l='98',h='104',c='100'),at+3*FIVE)
        row=r.ledger[0];s=r.signals[0]
        idx={at:bar(at),at+FIVE:bar(at+FIVE,l='98',h='104',c='100')}
        out=attribution(row,s,idx,{})
        self.assertFalse(out['reached_1R_before_exit_confirmed'])
        self.assertTrue(out['reached_1R_terminal_ambiguous'])
        self.assertEqual(out['mfe_pre_exit_lower_bound_R'],D('.2')/D('1.5'))

ZERO=D(0)
if __name__=='__main__':unittest.main()
