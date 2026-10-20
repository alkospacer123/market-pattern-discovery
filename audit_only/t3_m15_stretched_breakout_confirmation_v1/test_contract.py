"""Meaningful causal contracts for one-bar timing and unchanged stop semantics."""
import copy,math,unittest
from datetime import datetime,timedelta
from zoneinfo import ZoneInfo
import engine,verifier
TZ=ZoneInfo('Europe/Moscow');STEP=timedelta(minutes=15)

def bar(at='2024-01-10T10:00:00',close=110.,signal=0,atr=20.,**kwargs):
 t=datetime.fromisoformat(at).replace(tzinfo=TZ)
 return dict(at=t,Open=close,High=close+1,Low=close-1,Close=close,ATR=atr,Signal=signal,PriorHigh=100.,PriorLow=100.,H1AvailableAt=t)|kwargs

def sequence(**first):
 a=bar(signal=1,**first);b=bar('2024-01-10T10:15:00',111);c=bar('2024-01-10T10:30:00',112,Open=111.5);d=bar('2024-01-10T10:45:00',113)
 return [a,b,c,d]

class Contracts(unittest.TestCase):
 def check_both(self,bs):
  a=engine.replay(copy.deepcopy(bs),'USDRUBF','CONFIRM');b=verifier.replay(copy.deepcopy(bs),'USDRUBF','CONFIRM')
  for table in b:
   actual=[a[table]] if table=='occupancy' else a[table]
   self.assertEqual(len(actual),len(b[table]),table)
   for x,y in zip(actual,b[table]):
    for k,v in y.items():
     if isinstance(v,float):self.assertAlmostEqual(x[k],v,places=8,msg=k)
     else:self.assertEqual(x[k],v,k)
  return a
 def test_exact_half_delays(self):
  r=self.check_both(sequence());self.assertTrue(r['signals'][0]['entry_accepted']);self.assertEqual(r['OPEN'][0]['actual_entry_time'],r['signals'][0]['signal_time']+STEP)
 def test_less_half_unchanged(self):
  r=self.check_both(sequence(close=109.999));self.assertEqual(r['OPEN'][0]['actual_entry_time'],r['signals'][0]['signal_time']);self.assertFalse(r['OPEN'][0]['confirmed'])
 def test_strict_confirmation(self):
  bs=sequence();bs[1]['Close']=110.;r=self.check_both(bs);self.assertEqual(r['signals'][0]['reason'],'CONFIRMATION_FAILED');self.assertFalse(r['OPEN'])
 def test_short(self):
  bs=[bar(close=90,signal=-1),bar('2024-01-10T10:15:00',89),bar('2024-01-10T10:30:00',88)]
  r=self.check_both(bs);self.assertEqual(r['OPEN'][0]['initial_stop'],128.)
 def test_no_third_confirmation(self):
  bs=sequence();bs[1]['Close']=109.;self.assertFalse(self.check_both(bs)['OPEN'])
 def test_gap_confirmation(self):
  bs=sequence();del bs[1];r=self.check_both(bs);self.assertEqual(r['signals'][0]['reason'],'MISSING_ADJACENT_CONFIRMATION')
 def test_gap_entry(self):
  bs=sequence();del bs[2];r=self.check_both(bs);self.assertEqual(r['signals'][0]['reason'],'MISSING_ADJACENT_OPEN')
 def test_confirmation_18_excluded(self):
  bs=sequence();delta=timedelta(hours=7,minutes=45)
  for b in bs:b['at']+=delta;b['H1AvailableAt']+=delta
  self.assertEqual(self.check_both(bs)['signals'][0]['reason'],'CONFIRMATION_OUTSIDE_T1')
 def test_confirmation_1745_entry_allowed(self):
  bs=sequence();delta=timedelta(hours=7,minutes=30)
  for b in bs:b['at']+=delta;b['H1AvailableAt']+=delta
  self.assertTrue(self.check_both(bs)['signals'][0]['entry_accepted'])
 def test_original_ATR_and_no_preentry_extremes(self):
  bs=sequence();bs[1].update(ATR=50.,High=1000.,Low=0.)
  r=self.check_both(bs);self.assertEqual(r['OPEN'][0]['initial_stop'],71.5);self.assertEqual(r['stops'][0]['extreme_before'],111.5)
 def test_entry_bar_stop_live(self):
  bs=sequence();bs[2]['Low']=60.;r=self.check_both(bs);self.assertEqual(len(r['trades']),1);self.assertEqual(r['trades'][0]['gross_R'],-1.)
 def test_occupied_and_reserved(self):
  bs=sequence();bs[1]['Signal']=1;bs[2]['Signal']=1;r=self.check_both(bs)
  self.assertEqual(r['signals'][1]['reason'],'CONFIRMATION_ENTRY_RESERVED');self.assertEqual(r['signals'][2]['reason'],'POSITION_OCCUPIED')
 def test_failed_original_fresh_signal(self):
  bs=sequence();bs[1].update(Close=109.,Signal=1);r=self.check_both(bs)
  self.assertEqual(r['signals'][0]['reason'],'CONFIRMATION_FAILED');self.assertTrue(r['signals'][1]['entry_accepted']);self.assertFalse(r['signals'][1]['stretched_delay'])
 def test_end_confirmation_unresolved(self):
  r=self.check_both(sequence()[:1]);self.assertEqual(r['signals'][0]['reason'],'UNRESOLVED_CONFIRMATION_END_OF_DATA')
 def test_end_entry_unresolved(self):
  r=self.check_both(sequence()[:2]);self.assertEqual(r['signals'][0]['reason'],'UNRESOLVED_END_OF_DATA')
 def test_signal_outside_T1(self):
  bs=sequence();bs[0]['at']-=timedelta(hours=1);r=self.check_both(bs);self.assertEqual(r['signals'][0]['reason'],'OUTSIDE_T1')
 def test_stop_first_trail_next_bar_and_gap_fill(self):
  bs=sequence(close=109.);bs[1].update(Open=110.,High=200.,Low=100.,Close=190.,ATR=10.);bs[2].update(Open=150.,High=180.,Low=140.,Close=160.)
  r=self.check_both(bs);self.assertFalse(r['stops'][0]['stop_hit']);self.assertEqual(r['stops'][0]['next_stop'],165.);self.assertEqual(r['trades'][0]['exit_price'],150.);self.assertTrue(r['trades'][0]['exit_at_open'])
 def test_feature_prefix_and_future_suffix(self):
  from support import development_frame,frozen
  p=frozen();f=development_frame('USDRUBF').iloc[:1600];prefix=p.features(f.iloc[:1200]);full=p.features(f)
  mutated=f.copy();mutated.iloc[1200:,:4]*=1.37;perturbed=p.features(mutated)
  for i,b in enumerate(prefix):
   for k,v in b.items():
    for other in (full,perturbed):
     if isinstance(v,float) and math.isnan(v):self.assertTrue(math.isnan(other[i][k]))
     else:self.assertEqual(v,other[i][k])
  a=engine.replay(full,'USDRUBF','CONFIRM');b=engine.replay(perturbed,'USDRUBF','CONFIRM');end=prefix[-1]['at']
  for table,time in [('stops','bar_close'),('marks','at'),('trades','exit_time')]:self.assertEqual([r for r in a[table] if r[time]<=end],[r for r in b[table] if r[time]<=end])

def run():
 suite=unittest.defaultTestLoader.loadTestsFromTestCase(Contracts);result=unittest.TextTestRunner(verbosity=1).run(suite);assert result.wasSuccessful()
 return dict(status='PASS',tests=result.testsRun,failures=0,errors=0,causal_features='prefix invariance and future OHLC suffix perturbation',both_execution_algorithms=True)
if __name__=='__main__':run()
