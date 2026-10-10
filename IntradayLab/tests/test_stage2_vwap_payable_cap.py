"""Algebraic price bounds and actual scheduled-Open eligibility, not PF tests."""
from datetime import datetime
from decimal import Decimal as D
import json
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from stage2_vwap_payable_cap import PayableCapReplay
from session_mtf import Bar
M=json.loads((Path(__file__).resolve().parents[1]/'config/stage2_vwap_payable_cap_v1.json').read_text())

class PayableBounds(unittest.TestCase):
    def replay(self):return PayableCapReplay('USDRUBF',M['parameters'],'PAYABLE_CAP_ENTRY',M['defaults'])
    def test_long_bound_includes_both_risk_and_reward_costs(self):
        r=self.replay();r.planning=True
        s={'direction_sign':1,'planned_execution_at':'2023-01-03 11:00:00','stop':D(98),'take':D(101),'cap':D('100.25')}
        self.assertIsNone(r.gate_entry(s,s['cap']))
        self.assertEqual(s['cap'],D('99.48'))
        r.planning=False
        self.assertEqual(r.gate_entry(s,D('99.49')),'NET_TARGET_BELOW_NET_RISK')
        self.assertIsNone(r.gate_entry(s,D('99.48')))
    def test_short_bound_rounds_toward_safe_price(self):
        r=self.replay();r.planning=True
        s={'direction_sign':-1,'planned_execution_at':'2023-01-03 11:00:00','stop':D(102),'take':D('99.01'),'cap':D('99.75')}
        self.assertIsNone(r.gate_entry(s,s['cap']))
        self.assertEqual(s['cap'],D('100.53'))
        r.planning=False
        self.assertEqual(r.gate_entry(s,D('100.52')),'NET_TARGET_BELOW_NET_RISK')
    def test_actual_favorable_open_cannot_shrink_risk_below_four_ticks(self):
        r=self.replay();r.planning=True
        s={'direction_sign':1,'planned_execution_at':'2023-01-03 11:00:00','stop':D(98),'take':D(101),'cap':D('100.25')}
        r.gate_entry(s,s['cap']);r.planning=False
        self.assertEqual(r.gate_entry(s,D('98.02')),'RISK_BELOW_FOUR_TICKS')
    def test_price_cap_is_not_recomputed_from_future_open(self):
        r=self.replay();r.planning=True
        s={'direction_sign':1,'planned_execution_at':'2023-01-03 11:00:00','stop':D(98),'take':D(101),'cap':D('100.25')}
        r.gate_entry(s,s['cap']);r.planning=False;original=s['cap']
        for price in [D(99),D(100),D(105)]:r.gate_entry(s,price)
        self.assertEqual(s['cap'],original)
    def test_only_scheduled_open_can_fill_even_if_intrabar_low_touches_cap(self):
        r=self.replay();s={'run':'VWAP_MR_USDRUBF','signal_id':'test','strategy':'VWAP_MR','instrument':'USDRUBF','direction':'LONG','direction_sign':1,'planned_execution_at':'2023-01-03 11:00:00','stop':D(98),'take':D(101),'cap':D('99.48'),'status':'SUBMITTED'}
        r.entry_order={'target':datetime(2023,1,3,11),'signal':s}
        b=Bar(datetime(2023,1,3,11),D(100),D(100),D(99),D(100),D(1),symbol='USDRUBF')
        r.execute(b,datetime(2023,1,3,11,10))
        self.assertFalse(r.ledger)
        self.assertEqual(s['status'],'NONFILL')
if __name__=='__main__':unittest.main()
