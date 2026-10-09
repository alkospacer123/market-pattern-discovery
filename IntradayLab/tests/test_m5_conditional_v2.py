"""v2 regressions; synthetic OHLCV plus explicitly bounded 2023 source checks."""
import copy
from datetime import datetime, timedelta
from decimal import Decimal as D
import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from m5_conditional_v2 import (Replay, Features, close_submission_deadline, next_slot,
    available, tick, FIVE, metrics)
from m5_baseline import Replay as SubmittedOrderReplay
from run_m5_baseline import inputs, load_manifest
from session_mtf import Bar

P=load_manifest()[0]['parameters']
T=datetime(2023,1,3,10)

def bar(t, o='100',h='100.2',l='99.8',c='100',delivery=None,symbol='USDRUBF'):
    return Bar(t,*map(D,(o,h,l,c,'10')),symbol=symbol,available_at=delivery)

def data(n=106):
    return [bar(T+i*FIVE) for i in range(n)]

class Scripted(Replay):
    def __init__(self, scheduled=(T+11*FIVE,), params=None, **kwargs):
        super().__init__('USDRUBF','MOMENTUM',params or P,**kwargs)
        self.scheduled=scheduled
    def decision(self,b,now,f):
        if b.timestamp in self.scheduled:
            super().decision(b,now,{'atr':D(1),'vwap':D(99),
                'range_high':D(99),'range_low':D(98),'MOMENTUM':1})

class V2Contract(unittest.TestCase):
    def test_parameters_and_v1_sha_unchanged(self):
        lab=Path(__file__).resolve().parents[1]
        m=json.loads((lab/'config/stage2_m5_conditional_v2.json').read_text())
        self.assertEqual(m['parameters'],P)
        self.assertEqual(m['parent_manifest_sha256'],load_manifest()[1])

    def test_missing_entry_is_no_model_fill_no_latch_no_later_retime(self):
        target=T+14*FIVE
        r=Scripted((T+11*FIVE,T+35*FIVE)).run([b for b in data() if b.timestamp!=target])
        self.assertEqual(r.signals[0]['status'],'NO_BAR_NO_MODEL_FILL')
        self.assertEqual(len(r.no_bar_entries),1)
        self.assertIsNone(r.unknown_entry)
        self.assertFalse(r.unknown_entries)
        self.assertEqual(r.signals[1]['status'],'MODELLED')
        self.assertEqual(len(r.ledger),1)
        self.assertEqual(r.ledger[0]['entry_interval_start'],str(T+38*FIVE))
        self.assertFalse(any(e['kind']=='ENTRY' and e['signal_id']==r.signals[0]['signal_id'] for e in r.events))

    def test_real_features_restore_only_after_thirteen_prior_contiguous(self):
        f=Features(P)
        for b in data(16): f.observe(b,b.timestamp+2*FIVE)
        f.reset() # missing observation at index 16
        resumed=[bar(T+i*FIVE) for i in range(17,31)]
        for b in resumed[:13]: self.assertIsNone(f.observe(b,b.timestamp+2*FIVE))
        self.assertEqual(f.observe(resumed[13],resumed[13].timestamp+2*FIVE)['prior_bars'],13)

    def test_missing_position_path_has_no_price_exit_cost_or_pnl(self):
        r=Scripted().run([b for b in data() if b.timestamp!=T+16*FIVE])
        row=r.ledger[0]
        self.assertEqual(row['status'],'UNRESOLVED')
        for key in ('exit','gross_price_pnl','c1_exit','c1_total','net_model_c1','exit_filled_model_units'):
            self.assertIsNone(row[key],key)
        self.assertEqual(row['exit_reason'],'UNKNOWN_PATH_CONDITIONAL_REDUCE_ALL')
        self.assertEqual(row['model_flat_scenario_at'],str(T+19*FIVE))
        self.assertEqual(row['model_flat_confirmed_at'],str(T+21*FIVE))
        self.assertEqual(row['residual_model_units'],0)
        self.assertIsNone(metrics(r.ledger)['full_PF'])
        self.assertFalse(any(e['kind']=='EXIT' for e in r.events))

    def test_absent_flatten_bar_does_not_confirm_flat(self):
        r=Scripted().run(data(16))
        row=r.ledger[0]
        self.assertEqual(row['status'],'UNRESOLVED')
        self.assertIsNone(row['model_flat_confirmed_at'])
        self.assertIsNone(row['possible_residual_model_units'])
        self.assertFalse(metrics(r.ledger)['model_flat_confirmed'])

    def test_unknown_path_reduce_all_zero_capacity_keeps_uncertainty(self):
        r=Scripted(capacities={('EXIT',T+19*FIVE):0}).run([b for b in data() if b.timestamp!=T+16*FIVE])
        self.assertTrue(any(e['kind']=='MODEL_FLAT_CONFIRMATION' and e['status']=='UNCONFIRMED' for e in r.events))
        self.assertEqual(r.ledger[0]['model_flat_scenario_at'],str(T+22*FIVE))
        self.assertIsNone(r.ledger[0]['net_model_c1'])

    def test_unknown_submitted_order_still_blocks_next_session(self):
        class LiveScript(SubmittedOrderReplay):
            def decision(self,b,now,f):
                if b.timestamp in (T+11*FIVE,T+35*FIVE,datetime(2023,1,4,11)):
                    super().decision(b,now,{'atr':D(1),'vwap':D(99),'range_high':D(99),
                        'range_low':D(98),'MOMENTUM':1})
        bs=[b for b in data() if b.timestamp!=T+14*FIVE]+[bar(datetime(2023,1,4,11))]
        r=LiveScript('USDRUBF','MOMENTUM',P).run(bs)
        self.assertEqual([s['status'] for s in r.signals],['UNRESOLVED_POSSIBLE_ENTRY_FILL','BLOCKED','BLOCKED'])
        self.assertIsNone(metrics(r.ledger,r.unknown_entries)['full_PF'])

    def test_nominal_boundary_latest_submission(self):
        boundary=datetime(2023,1,3,14)
        self.assertEqual(close_submission_deadline(boundary,P),datetime(2023,1,3,13,35))
        sent=close_submission_deadline(boundary,P)
        self.assertEqual(next_slot(sent)+2*FIVE,boundary-2*FIVE)
        self.assertGreater(next_slot(sent+FIVE)+2*FIVE,boundary-2*FIVE)
        r=Scripted((datetime(2023,1,3,13),)).run(data())
        row=r.ledger[0]
        self.assertEqual(row['exit_interval_start'],'2023-01-03 13:40:00')
        self.assertEqual(row['exit_confirmed_at'],'2023-01-03 13:50:00')
        self.assertFalse(row['flat_target_breach'])
        self.assertEqual([e['at'] for e in r.events if e['kind']=='EXIT_ORDER'],['2023-01-03 13:35:00'])

    def test_late_boundary_confirmation_is_not_flat_at_b_minus_ten(self):
        bs=data()
        bs[44]=bar(T+44*FIVE,delivery=T+47*FIVE)
        r=Scripted((datetime(2023,1,3,13),)).run(bs)
        self.assertTrue(r.ledger[0]['flat_target_breach'])
        self.assertTrue(any(e['kind']=='FLAT_TARGET' and e['status']=='UNCONFIRMED' for e in r.events))

    def test_t15_and_order_delay_deadlines_derived_causally(self):
        p=P|{'availability_minutes':15}
        self.assertEqual(close_submission_deadline(datetime(2023,1,3,14),p),datetime(2023,1,3,13,30))
        p=P|{'order_delay_minutes':2}
        self.assertEqual(close_submission_deadline(datetime(2023,1,3,14),p),datetime(2023,1,3,13,35))

    def test_no_lookahead_future_prices_and_target_existence(self):
        bs=data(); original=Scripted().run(bs)
        altered=copy.copy(bs); altered[14]=bar(T+14*FIVE,o='120',h='121',l='119',c='120')
        changed=Scripted().run(altered)
        absent=Scripted().run([b for b in bs if b.timestamp!=T+14*FIVE])
        fields=['signal_at','available_at','ready_at','planned_execution_at','stop','take','cap','signal_close']
        for r in (changed,absent):
            self.assertEqual([original.signals[0][k] for k in fields],[r.signals[0][k] for k in fields])
        self.assertEqual(original.signals[0]['available_at'],str(T+13*FIVE))
        self.assertEqual(original.signals[0]['planned_execution_at'],str(T+14*FIVE))

    def test_early_feature_access_rejected(self):
        b=data()[0]
        with self.assertRaises(ValueError): Features(P).observe(b,b.timestamp+FIVE)

    def test_expired_late_entry_never_revives(self):
        bs=data(); bs[14]=bar(T+14*FIVE,delivery=T+17*FIVE)
        r=Scripted().run(bs)
        self.assertEqual(r.signals[0]['status'],'NO_BAR_NO_MODEL_FILL')
        self.assertFalse(r.ledger)

    def test_cny_grid_switch_and_conservative_rounding(self):
        self.assertEqual(tick('CNYRUBF',datetime(2023,9,27,18,59,59)),D('.01'))
        self.assertEqual(tick('CNYRUBF',datetime(2023,9,27,19)),D('.001'))
        self.assertEqual(tick('CNYRUBF',datetime(2023,9,28,10)),D('.001'))

class ActualMissingBars(unittest.TestCase):
    def test_all_eight_physical_2023_slots_absent(self):
        root=Path('/workspace/market-pattern-data')
        if not root.is_dir(): self.skipTest('Source checkout required; independent audit must repeat this check')
        bs,_=inputs(root,load_manifest()[0])
        cases={
            'USDRUBF':['2023-02-02 15:40:00','2023-02-03 16:15:00'],
            'CNYRUBF':['2023-01-06 17:15:00','2023-01-19 15:25:00'],
            'GLDRUBF':['2023-08-17 16:00:00','2023-07-12 11:40:00'],
            'IMOEXF':['2023-11-30 17:20:00','2023-11-15 16:25:00']}
        for symbol,times in cases.items():
            observed={b.timestamp for b in bs[symbol]}
            for t in times:
                at=datetime.fromisoformat(t)
                self.assertTrue(at not in observed,f'{symbol} {at} must be absent')
                self.assertTrue(any(x<at for x in observed))
                self.assertTrue(any(x>at for x in observed))

if __name__=='__main__': unittest.main()
