import unittest
from datetime import datetime,timedelta
from zoneinfo import ZoneInfo
from common import new_position,protect_and_tp,public,target,partial_quantity
from engines import h1_replay,m15_replay

AT=datetime(2024,12,31,17,tzinfo=ZoneInfo('Europe/Moscow'))
def bar(at=AT,op=100,hi=101,lo=99,cl=100,atr=2,sig=0):
    return dict(at=at,Open=op,High=hi,Low=lo,Close=cl,ATR=atr,Signal=sig,H1AvailableAt=at,PriorHigh=99,PriorLow=101)
def pos(side=1,variant='PARTIAL_TP_2R_50'):
    return new_position('H1','USDRUBF','test','','test',AT,100,90 if side==1 else 110,side,variant,0)
class Synthetic(unittest.TestCase):
    def test_long_partial_then_final(self):
        p=pos();self.assertFalse(protect_and_tp(p,bar(hi=121,lo=95)));self.assertEqual(p['_remaining'],.5)
        self.assertTrue(protect_and_tp(p,bar(at=AT+timedelta(hours=1),op=95,lo=89)));self.assertEqual(p['gross_R'],.5)
    def test_short_partial_then_final(self):
        p=pos(-1);protect_and_tp(p,bar(op=100,hi=105,lo=79));protect_and_tp(p,bar(op=105,hi=111,lo=100));self.assertEqual(p['gross_R'],.5)
    def test_long_stop_first(self):
        p=pos();protect_and_tp(p,bar(hi=121,lo=89));self.assertFalse(p['partial_executed']);self.assertEqual(p['gross_R'],-1.)
    def test_short_stop_first(self):
        p=pos(-1);protect_and_tp(p,bar(hi=111,lo=79));self.assertFalse(p['partial_executed']);self.assertEqual(p['gross_R'],-1.)
    def test_long_adverse_gap(self):
        p=pos();protect_and_tp(p,bar(op=85,hi=87,lo=80));self.assertEqual(p['gross_R'],-1.5)
    def test_short_adverse_gap(self):
        p=pos(-1);protect_and_tp(p,bar(op=115,hi=120,lo=114));self.assertEqual(p['gross_R'],-1.5)
    def test_tp_favorable_gap_observed_open(self):
        p=pos();protect_and_tp(p,bar(op=125,hi=130,lo=124));self.assertEqual(p['part1_exit_price'],125.)
    def test_short_tp_favorable_gap_observed_open(self):
        p=pos(-1);protect_and_tp(p,bar(op=75,hi=76,lo=70));self.assertEqual(p['part1_exit_price'],75.)
    def test_tp_once(self):
        p=pos();protect_and_tp(p,bar(hi=125,lo=95));at=p['part1_exit_time'];protect_and_tp(p,bar(at=AT+timedelta(hours=1),hi=130,lo=95));self.assertEqual(p['part1_exit_time'],at);self.assertEqual(p['_remaining'],.5)
    def test_one_contract(self):self.assertEqual(partial_quantity(1,True),0)
    def test_three_contracts(self):self.assertEqual(partial_quantity(3,True),1);self.assertEqual(3-partial_quantity(3,True),2)
    def test_fractional_half(self):self.assertEqual(partial_quantity(1),.5)
    def test_long_rounding(self):self.assertEqual(target(100,99.993,1,.01),100.02)
    def test_short_rounding(self):self.assertEqual(target(100,100.007,-1,.01),99.98)
    def test_month_year_carry(self):
        p=pos();protect_and_tp(p,bar(hi=121,lo=95));protect_and_tp(p,bar(at=AT+timedelta(days=1),lo=89));self.assertEqual(p['part1_exit_time'].year,2024);self.assertEqual(p['part2_exit_time'].year,2025)
    def test_commission_once(self):
        p=pos();protect_and_tp(p,bar(hi=121,lo=95));protect_and_tp(p,bar(lo=89));t=public(p);self.assertAlmostEqual(sum(t[f'part{p}_{s}_C1_R'] for p in (1,2) for s in ('entry','exit')),.002/10)
    def test_initial_risk_immutable(self):
        p=pos();p['_stop']=105;protect_and_tp(p,bar(op=110,lo=106,hi=121));self.assertEqual(p['initial_risk_price'],10)
    def test_h1_entry_extremes_unavailable(self):
        stream=dict(instrument='USDRUBF',lifecycle='test',fold_id='',bars=[bar(hi=200,lo=50,sig=1)])
        t=h1_replay(stream,'PARTIAL_TP_2R_50')['trades'][0];self.assertEqual(t['status'],'OPEN');self.assertFalse(t['partial_executed'])
    def test_m15_execution_bar_tp(self):
        b=bar(at=AT+timedelta(minutes=15),hi=109,lo=99)
        s=dict(instrument='USDRUBF',lifecycle='test',bars=[bar(sig=1),b])
        t=m15_replay(s,'PARTIAL_TP_2R_50')['trades'][0];self.assertTrue(t['partial_executed']);self.assertEqual(t['part1_exit_time'],b['at'])
    def test_m15_execution_bar_stop_first(self):
        s=dict(instrument='USDRUBF',lifecycle='test',bars=[bar(sig=1),bar(at=AT+timedelta(minutes=15),hi=109,lo=95)])
        t=m15_replay(s,'PARTIAL_TP_2R_50')['trades'][0];self.assertFalse(t['partial_executed']);self.assertEqual(t['gross_R'],-1.)
    def test_m15_gap_cancels_pending(self):
        s=dict(instrument='USDRUBF',lifecycle='test',bars=[bar(sig=1),bar(at=AT+timedelta(minutes=30),hi=109,lo=99)])
        r=m15_replay(s,'PARTIAL_TP_2R_50');self.assertFalse(r['trades']);self.assertEqual(r['signals'][0]['reason'],'MISSING_ADJACENT_OPEN')
    def test_h1_residual_blocks_reentry(self):
        s=dict(instrument='USDRUBF',lifecycle='test',fold_id='',bars=[bar(sig=1),bar(at=AT+timedelta(hours=1),hi=111,lo=99,sig=1)])
        r=h1_replay(s,'PARTIAL_TP_2R_50');self.assertEqual(len(r['trades']),1);self.assertFalse(r['signals'][-1]['accepted'])
    def test_h1_trail1_deferred(self):
        s=dict(instrument='USDRUBF',lifecycle='test',fold_id='',bars=[bar(sig=1),bar(at=AT+timedelta(hours=1),hi=106,lo=99),bar(at=AT+timedelta(hours=2),op=101,hi=102,lo=99)])
        r=h1_replay(s,'CONTROL');self.assertFalse(r['trace'][0]['stop_hit']);self.assertEqual(r['trace'][0]['stop_after'],95.);self.assertEqual(r['trace'][1]['stop_entering'],100.)

if __name__=='__main__':unittest.main()
