import unittest
from datetime import datetime,timedelta
from zoneinfo import ZoneInfo
from common import new_position,protect_and_tp,public
from engines import h1_replay,m15_replay,replay
from forensics import excursions,post_stop,identity
from analyze import round_stop,drawdown,consecutive
AT=datetime(2024,12,31,17,tzinfo=ZoneInfo('Europe/Moscow'))
def bar(at=AT,op=100,hi=101,lo=99,cl=100,atr=2,sig=0):return dict(at=at,Open=op,High=hi,Low=lo,Close=cl,ATR=atr,Signal=sig,H1AvailableAt=at,PriorHigh=99,PriorLow=101)
def stream(bars,system='H1'):return dict(system=system,instrument='USDRUBF',lifecycle='test',fold_id='',bars=bars)
def pos(side=1):return new_position('H1','USDRUBF','test','','test',AT,100,90 if side==1 else 110,side,'CONTROL',0)
class Synthetic(unittest.TestCase):
 def test_long_stop(self):
  p=pos();protect_and_tp(p,bar(lo=89));self.assertEqual(p['gross_R'],-1.)
 def test_short_stop(self):
  p=pos(-1);protect_and_tp(p,bar(hi=111));self.assertEqual(p['gross_R'],-1.)
 def test_long_gap(self):
  p=pos();protect_and_tp(p,bar(op=85,hi=87,lo=80));self.assertEqual(p['gross_R'],-1.5)
 def test_short_gap(self):
  p=pos(-1);protect_and_tp(p,bar(op=115,hi=120,lo=114));self.assertEqual(p['gross_R'],-1.5)
 def test_h1_entry_bar_excluded(self):
  r=replay(stream([bar(hi=200,lo=1,sig=1)]),'CONTROL');self.assertEqual(r['trades'][0]['status'],'OPEN');self.assertEqual(r['trace'],[])
 def test_h1_delayed_TRAIL1(self):
  r=replay(stream([bar(sig=1),bar(at=AT+timedelta(hours=1),hi=106,lo=99),bar(at=AT+timedelta(hours=2),op=101,hi=102,lo=99)]),'CONTROL')
  self.assertEqual(r['trace'][0]['stop_after'],95.);self.assertEqual(r['trace'][1]['stop_entering'],100.)
 def test_h1_short_delayed_TRAIL1(self):
  r=replay(stream([bar(sig=-1),bar(at=AT+timedelta(hours=1),hi=101,lo=94),bar(at=AT+timedelta(hours=2),op=99,hi=101,lo=98)]),'CONTROL')
  self.assertEqual(r['trace'][0]['stop_after'],105.);self.assertEqual(r['trace'][1]['stop_entering'],100.)
 def test_h1_R0_changes_trigger(self):
  s=stream([bar(sig=1),bar(at=AT+timedelta(hours=1),hi=104.2,lo=99)])
  a=replay(s,'CONTROL')['trades'][0];b=replay(s,'STOP_2p0')['trades'][0];self.assertIsNone(a['trigger_bar_time']);self.assertIsNotNone(b['trigger_bar_time'])
 def test_m15_next_open(self):
  r=replay(stream([bar(sig=1),bar(at=AT+timedelta(minutes=15),op=101,hi=102,lo=100)],'M15'),'CONTROL');self.assertEqual(r['trades'][0]['entry_price'],101.)
 def test_m15_execution_bar_stop(self):
  r=replay(stream([bar(sig=1),bar(at=AT+timedelta(minutes=15),hi=109,lo=95)],'M15'),'CONTROL');self.assertEqual(r['trades'][0]['gross_R'],-1.)
 def test_m15_no_adjacency(self):
  r=replay(stream([bar(sig=1),bar(at=AT+timedelta(minutes=30))],'M15'),'CONTROL');self.assertEqual(r['trades'],[]);self.assertEqual(r['signals'][0]['reason'],'MISSING_ADJACENT_OPEN')
 def test_m15_session_18_excluded(self):
  r=replay(stream([bar(at=AT+timedelta(hours=1),sig=1),bar(at=AT+timedelta(hours=1,minutes=15))],'M15'),'CONTROL');self.assertEqual(r['trades'],[])
 def test_m15_pending_end_censored(self):
  r=replay(stream([bar(sig=1)],'M15'),'CONTROL');self.assertEqual(r['signals'][0]['reason'],'UNRESOLVED_END_OF_DATA')
 def test_occupancy_blocks(self):
  r=replay(stream([bar(sig=1),bar(at=AT+timedelta(hours=1),sig=1)]),'CONTROL');self.assertEqual(len(r['trades']),1);self.assertFalse(r['signals'][-1]['accepted'])
 def test_shorter_stop_changes_occupancy(self):
  s=stream([bar(sig=1),bar(at=AT+timedelta(hours=1),lo=96.5,sig=1)])
  self.assertEqual(len(replay(s,'CONTROL')['trades']),1);self.assertEqual(len(replay(s,'STOP_1p5')['trades']),2)
 def test_missing_bars_not_fabricated(self):
  r=replay(stream([bar(sig=1),bar(at=AT+timedelta(days=2),lo=94)]),'CONTROL');self.assertEqual(len(r['marks']),2);self.assertEqual(r['trades'][0]['bars_held'],1)
 def test_stop_first_MFE_ambiguous(self):
  s=stream([bar(sig=1),bar(at=AT+timedelta(hours=1),hi=111,lo=94)]);r=replay(s,'CONTROL');t,_=excursions(r['trades'][0],s['bars'],r['trace']);self.assertEqual(t['MFE_pre_stop_R0'],0.);self.assertEqual(t['MFE_before_stop_ge_2p0R'],'AMBIGUOUS_EXIT_BAR')
 def test_survived_MFE_then_stop(self):
  s=stream([bar(sig=1),bar(at=AT+timedelta(hours=1),hi=102.6,lo=99),bar(at=AT+timedelta(hours=2),lo=94)]);r=replay(s,'CONTROL');t,_=excursions(r['trades'][0],s['bars'],r['trace']);self.assertGreater(t['MFE_pre_stop_R0'],.5)
 def test_open_gap_exit_time_bound(self):
  s=stream([bar(sig=1),bar(at=AT+timedelta(hours=1),op=90,hi=92,lo=85)]);r=replay(s,'CONTROL');t,_=excursions(r['trades'][0],s['bars'],r['trace']);self.assertEqual(t['actual_exit_time_upper'],AT)
 def test_grid_long_outward(self):self.assertAlmostEqual(round_stop(99.997,1,.01),99.99)
 def test_grid_short_outward(self):self.assertAlmostEqual(round_stop(100.003,-1,.01),100.01)
 def test_month_year_carry(self):
  at=AT.replace(hour=23);s=stream([bar(at=at,sig=1),bar(at=at+timedelta(hours=2),lo=94)]);t=replay(s,'CONTROL')['trades'][0];self.assertEqual(t['entry_time'].year,2024);self.assertEqual(t['exit_time'].year,2025)
 def test_DD_includes_start_zero(self):self.assertEqual(drawdown([-1,-2,3]),2)
 def test_NO_DATA_breaks_streak(self):self.assertEqual(consecutive([{'month':'2024-01','R':-1},{'month':'2024-03','R':-1}],'R'),1)
 def test_R0_immutable(self):
  p=pos();p['_stop']=105;protect_and_tp(p,bar(op=110,hi=120,lo=104));self.assertEqual(p['initial_risk_price'],10)
 def test_post_stop_CENSORED(self):
  t=dict(system='H1',lifecycle='test',fold_id='',instrument='USDRUBF',trade_id='x',variant='CONTROL',direction='LONG',entry_time=AT,exit_time=AT,entry_price=100,initial_risk_price=10)
  p=post_stop(t,[bar(at=AT),bar(at=AT+timedelta(hours=1))],2);self.assertEqual(p['status'],'CENSORED');self.assertEqual(p['FAVORABLE_1R_status'],'CENSORED')
 def test_post_stop_skips_stop_bar(self):
  t=dict(system='H1',lifecycle='test',fold_id='',instrument='USDRUBF',trade_id='x',direction='LONG',entry_time=AT,exit_time=AT,entry_price=100,initial_risk_price=10)
  p=post_stop(t,[bar(at=AT,hi=130),bar(at=AT+timedelta(hours=1),hi=101)],1);self.assertNotEqual(p['FAVORABLE_2R_status'],'OBSERVED')
 def test_post_stop_samebar_ambiguity(self):
  t=dict(system='H1',lifecycle='test',fold_id='',instrument='USDRUBF',trade_id='x',direction='LONG',entry_time=AT,exit_time=AT,entry_price=100,initial_risk_price=10)
  p=post_stop(t,[bar(at=AT),bar(at=AT+timedelta(hours=1),op=90,hi=101,lo=80)],1);self.assertEqual(p['recovery_vs_adverse_1p5R_order'],'AMBIGUOUS_SAME_BAR')
 def test_post_stop_prior_bar_before_next_open(self):
  t=dict(system='H1',lifecycle='test',fold_id='',instrument='USDRUBF',trade_id='x',direction='LONG',entry_time=AT,exit_time=AT,entry_price=100,initial_risk_price=10)
  p=post_stop(t,[bar(at=AT),bar(at=AT+timedelta(hours=1),op=90,hi=101,lo=89),bar(at=AT+timedelta(hours=2),op=80,hi=81,lo=79)],1);self.assertEqual(p['recovery_vs_adverse_1p5R_order'],'RECOVERY_FIRST')
 def test_signal_identifier_not_sequence(self):
  t=dict(system='H1',lifecycle='test',fold_id='',instrument='USDRUBF',direction='LONG',entry_time=AT,trade_id='1');a=identity(t);t['trade_id']='2';self.assertEqual(identity(t),a)
if __name__=='__main__':unittest.main()
