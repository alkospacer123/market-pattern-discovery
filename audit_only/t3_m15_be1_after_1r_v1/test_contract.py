"""Synthetic causal timing and one-position contracts for both implementations."""
import copy,math,unittest
from datetime import datetime,timedelta
from zoneinfo import ZoneInfo
import engine,verifier
TZ=ZoneInfo('Europe/Moscow');STEP=timedelta(minutes=15)

def seq(side=1):
 t=datetime(2024,1,10,10,tzinfo=TZ)
 return [dict(at=t+i*STEP,Open=100.,High=101.,Low=99.,Close=100.,ATR=10.,Signal=side if i==0 else 0,PriorHigh=99.,PriorLow=101.,H1AvailableAt=t) for i in range(4)]

class Contracts(unittest.TestCase):
 def both(self,bs,mode='BE1'):
  a=engine.replay(copy.deepcopy(bs),'USDRUBF',mode);b=verifier.replay(copy.deepcopy(bs),'USDRUBF',mode)
  for table,rows in b.items():
   actual=[a[table]] if table=='occupancy' else a[table];self.assertEqual(len(actual),len(rows),table)
   for x,y in zip(actual,rows):
    for k,v in y.items():
     if isinstance(v,float):self.assertAlmostEqual(x[k],v,places=8,msg=k)
     else:self.assertEqual(x[k],v,k)
  return a
 def test_long_exact_1R(self):
  bs=seq();bs[1].update(High=120.,Close=110.);r=self.both(bs);self.assertEqual(r['stops'][0]['next_stop'],100.);self.assertTrue(r['stops'][0]['BE1_raised_now']);self.assertEqual(r['trades'][0]['gross_R'],0.)
 def test_short_exact_1R(self):
  bs=seq(-1);bs[1].update(Low=80.,Close=90.);r=self.both(bs);self.assertEqual(r['stops'][0]['next_stop'],100.);self.assertEqual(r['trades'][0]['gross_R'],0.)
 def test_just_below_no_activation(self):
  bs=seq();bs[1]['High']=119.999;r=self.both(bs);self.assertFalse(r['OPEN'][0]['BE1_reached']);self.assertFalse(r['OPEN'][0]['BE1_raised'])
 def test_survived_activation_bar_no_same_bar_BE(self):
  bs=seq();bs[1].update(High=120.,Low=90.,Close=95.);r=self.both(bs[:2]);self.assertFalse(r['trades']);self.assertEqual(r['OPEN'][0]['active_stop'],100.);self.assertEqual(r['OPEN'][0]['unrealized_gross_R'],-.25)
 def test_exit_bar_high_cannot_activate(self):
  bs=seq();bs[1].update(High=500.,Low=70.);r=self.both(bs);self.assertEqual(r['trades'][0]['gross_R'],-1.);self.assertFalse(r['trades'][0]['BE1_reached']);self.assertIsNone(r['stops'][0]['next_stop']);self.assertEqual(r['trades'][0]['MFE_R'],0.)
 def test_exit_bar_low_cannot_activate_short(self):
  bs=seq(-1);bs[1].update(High=130.,Low=1.);r=self.both(bs);self.assertEqual(r['trades'][0]['gross_R'],-1.);self.assertFalse(r['trades'][0]['BE1_reached'])
 def test_gap_BE_can_lose(self):
  bs=seq();bs[1]['High']=120.;bs[2].update(Open=95.,High=110.,Low=90.,Close=100.);r=self.both(bs);self.assertEqual(r['trades'][0]['gross_R'],-.25);self.assertTrue(r['trades'][0]['gap_exit'])
 def test_short_gap_BE_can_lose(self):
  bs=seq(-1);bs[1]['Low']=80.;bs[2].update(Open=105.,High=110.,Low=90.);r=self.both(bs);self.assertEqual(r['trades'][0]['gross_R'],-.25)
 def test_does_not_weaken_better_trailing(self):
  bs=seq();bs[1].update(High=150.,Close=140.);r=self.both(bs[:2]);self.assertEqual(r['OPEN'][0]['active_stop'],115.);self.assertFalse(r['OPEN'][0]['BE1_raised']);self.assertEqual(r['OPEN'][0]['stop_source'],'TRAIL')
 def test_short_does_not_weaken(self):
  bs=seq(-1);bs[1].update(Low=50.,Close=60.);r=self.both(bs[:2]);self.assertEqual(r['OPEN'][0]['active_stop'],85.);self.assertFalse(r['OPEN'][0]['BE1_raised'])
 def test_BE_then_trailing_strengthens(self):
  bs=seq();bs[1]['High']=120.;bs[2].update(Open=110.,Low=105.,High=150.,Close=140.);r=self.both(bs[:3]);self.assertEqual(r['OPEN'][0]['active_stop'],115.);self.assertEqual(r['OPEN'][0]['stop_source'],'TRAIL')
 def test_ATR_expansion_cannot_weaken(self):
  bs=seq();bs[1]['High']=120.;bs[2].update(Open=110.,Low=105.,High=119.,ATR=100.);r=self.both(bs[:3]);self.assertEqual(r['OPEN'][0]['active_stop'],100.);self.assertEqual(r['OPEN'][0]['initial_risk'],20.)
 def test_original_signal_ATR_from_next_open(self):
  bs=seq();bs[1].update(Open=105.,High=106.,Low=104.,ATR=100.);r=self.both(bs[:2]);self.assertEqual(r['OPEN'][0]['initial_stop'],85.);self.assertEqual(r['OPEN'][0]['entry_price'],105.)
 def test_stop_live_entry_bar(self):
  bs=seq();bs[1]['Low']=79.;self.assertEqual(self.both(bs)['trades'][0]['exit_time'],bs[1]['at'])
 def test_occupancy_then_same_close_reentry(self):
  bs=seq();bs[1].update(High=120.,Signal=1);bs[2]['Signal']=-1;r=self.both(bs);self.assertEqual(r['signals'][1]['reason'],'POSITION_OCCUPIED');self.assertTrue(r['signals'][2]['entry_accepted']);self.assertEqual(r['OPEN'][0]['direction'],'SHORT')
 def test_missing_adjacent_open(self):
  bs=seq();del bs[1];r=self.both(bs);self.assertEqual(r['signals'][0]['reason'],'MISSING_ADJACENT_OPEN');self.assertFalse(r['OPEN'])
 def test_next_observed_after_gap(self):
  bs=seq();bs[1]['High']=120.;bs[2]['at']+=timedelta(days=3);r=self.both(bs[:3]);self.assertEqual(r['trades'][0]['gross_R'],0.);self.assertTrue(r['stops'][1]['observed_gap'])
 def test_session_18_excluded(self):
  bs=seq();bs[0]['at']+=timedelta(hours=8);r=self.both(bs[:1]);self.assertEqual(r['signals'][0]['reason'],'OUTSIDE_T1')
 def test_1745_signal_18_open_allowed(self):
  bs=seq();delta=timedelta(hours=7,minutes=45)
  for b in bs:b['at']+=delta;b['H1AvailableAt']+=delta
  self.assertTrue(self.both(bs)['signals'][0]['entry_accepted'])
 def test_terminal_pending(self):
  r=self.both(seq()[:1]);self.assertEqual(r['signals'][0]['reason'],'UNRESOLVED_END_OF_DATA');self.assertFalse(r['OPEN'])
 def test_year_boundary_no_reset(self):
  bs=seq();base=datetime(2023,12,29,17,45,tzinfo=TZ)
  for i,b in enumerate(bs):b['at']=base+i*STEP;b['H1AvailableAt']=base
  bs[1]['High']=120.;bs[2]['at']=datetime(2024,1,3,10,tzinfo=TZ);r=self.both(bs[:3]);self.assertEqual(r['trades'][0]['entry_price'],100.);self.assertEqual(r['trades'][0]['gross_R'],0.);self.assertEqual(r['snapshots'][0]['month'],'2023-12')
 def test_CONTROL_no_BE_floor(self):
  bs=seq();bs[1]['High']=120.;r=self.both(bs,'CONTROL');self.assertFalse(r['trades']);self.assertFalse(r['OPEN'][0]['BE1_raised']);self.assertEqual(r['OPEN'][0]['active_stop'],85.)
 def test_prefix_and_future_suffix(self):
  from support import development_frame,frozen
  f=development_frame('USDRUBF').iloc[:1600];p=frozen();prefix=p.features(f.iloc[:1200]);full=p.features(f);mutated=f.copy();mutated.iloc[1200:,:4]*=1.37;future=p.features(mutated)
  for i,b in enumerate(prefix):
   for k,v in b.items():
    for other in (full,future):
     if isinstance(v,float) and math.isnan(v):self.assertTrue(math.isnan(other[i][k]))
     else:self.assertEqual(v,other[i][k])
  a=self.both(full);b=self.both(future);end=prefix[-1]['at']
  for table,time in [('stops','bar_close'),('marks','at'),('trades','exit_time')]:self.assertEqual([r for r in a[table] if r[time]<=end],[r for r in b[table] if r[time]<=end])

def run():
 result=unittest.TextTestRunner(verbosity=1).run(unittest.defaultTestLoader.loadTestsFromTestCase(Contracts));assert result.wasSuccessful()
 return dict(status='PASS',tests=result.testsRun,failures=0,errors=0,both_execution_algorithms=True,prefix_and_future_suffix=True)
if __name__=='__main__':run()
