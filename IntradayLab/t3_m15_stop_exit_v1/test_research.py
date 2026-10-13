"""Causal fixtures tested before market outcomes; symmetric LONG/SHORT cases."""
import tempfile
import unittest
from pathlib import Path
import pandas as pd
from engine import E, execute


def frame(bars,sign=1,times=None):
    index = pd.date_range('2024-01-05 23:00',periods=len(bars),freq='15min',tz=E.TZ) if times is None else pd.DatetimeIndex(times)
    rows = []
    for i,(o,h,l,c,atr,sig) in enumerate(bars):
        if sign == -1:o,h,l,c = 200-o,200-l,200-h,200-c
        row = dict(Open=o,High=h,Low=l,Close=c,ATR=atr,Signal=sig*sign,PriorHigh=99,PriorLow=101,
                   PreviousATR=5.,H1ADX=25.,H1PreviousADX=24.,H1Slope=sign,H1PreviousSlope=sign,
                   H1ATRRatio=1.2,H1PreviousATRRatio=1.1,H1AvailableAt=index[0],H1PreviousAvailableAt=index[0]-pd.Timedelta(hours=1))
        rows.append(row)
    return pd.DataFrame(rows,index=index)

ENTRY = (100,140,60,100,5,1)  # Huge signal-bar extremes must never activate a rule.


class CausalTests(unittest.TestCase):
    def run_case(self,bars,rule,sign=1,version='BASELINE',times=None):
        return execute(frame(bars,sign,times),'USDRUBF',version,E.CONFIGS[version],rule)

    def test_signal_candle_extreme_excluded(self):
        for rule in ('S1','S2','S3'):
            for s in (1,-1):
                with self.subTest(rule=rule,sign=s):
                    t,o,d,e = self.run_case([ENTRY],rule,s)
                    self.assertEqual(t,[]);self.assertFalse(o['threshold_activated']);self.assertEqual(d,[])
                    self.assertEqual(o['favorable_extreme'],100);self.assertEqual(o['active_stop'],100-s*10)

    def test_old_stop_before_activation_on_ambiguous_bar(self):
        for rule in ('CONTROL','S1','S2','S3'):
            for s in (1,-1):
                with self.subTest(rule=rule,sign=s):
                    t,o,d,e = self.run_case([ENTRY,(100,130,89,105,1,0)],rule,s)
                    self.assertEqual(t[0]['gross_R'],-1);self.assertFalse(t[0]['threshold_activated'])
                    self.assertEqual(t[0]['MFE_R'],0);self.assertIsNone(d[0]['favorable_extreme_after'])
                    self.assertFalse(d[0]['threshold_activated_now']);self.assertIsNone(o)

    def test_s1_initial_stop_fixed_before_1r(self):
        for s in (1,-1):
            t,o,d,e = self.run_case([ENTRY,(100,109,95,100,1,0),(100,108,95,100,1,0)],'S1',s)
            self.assertEqual(o['active_stop'],100-s*10);self.assertFalse(o['threshold_activated'])
            self.assertEqual(o['stop_updates'],0)

    def test_s1_accumulated_extreme_and_next_bar_activation(self):
        for s in (1,-1):
            bars=[ENTRY,(100,109,95,100,1,0),(100,110,94,100,5,0),(100,108,96,100,1,0)]
            t,o,d,e=self.run_case(bars,'S1',s)
            self.assertEqual(t,[]);self.assertTrue(d[1]['threshold_activated_now'])
            self.assertEqual(d[1]['active_stop_next_bar'],100-s*5)
            self.assertEqual(o['active_stop'],100+s*7)  # accumulated 110, not last 108
            self.assertEqual(o['initial_risk'],10)

    def test_be_activation_same_bar_return_does_not_exit(self):
        for s in (1,-1):
            t,o,d,e=self.run_case([ENTRY,(100,110,95,98,5,0),(101,102,99,100,5,0)],'S2',s)
            self.assertEqual(len(t),1);self.assertEqual(t[0]['bars_held'],2)
            self.assertEqual(t[0]['gross_R'],0);self.assertTrue(t[0]['threshold_activated'])
            self.assertEqual(d[0]['active_stop_next_bar'],100);self.assertEqual(d[0]['phase'],'SURVIVED')

    def test_lock_activation_same_bar_return_does_not_exit(self):
        for s in (1,-1):
            t,o,d,e=self.run_case([ENTRY,(100,120,95,105,10,0),(112,114,109,111,10,0)],'S3',s)
            self.assertEqual(t[0]['gross_R'],1);self.assertEqual(t[0]['bars_held'],2)
            self.assertEqual(d[0]['active_stop_next_bar'],100+s*10)
            self.assertTrue(d[0]['threshold_activated_now'])

    def test_immutable_initial_risk_with_already_ratchet_stop(self):
        for s in (1,-1):
            bars=[ENTRY,(100,109,98,107,1,0),(107,110,107,108,5,0)]
            t,o,d,e=self.run_case(bars,'S3',s)
            self.assertEqual(t,[]);self.assertEqual(o['initial_risk'],10)
            self.assertFalse(o['threshold_activated']);self.assertEqual(o['active_stop'],100+s*6)

    def test_trail_can_be_tighter_than_be_or_lock(self):
        for rule,h in [('S2',115),('S3',125)]:
            for s in (1,-1):
                t,o,d,e=self.run_case([ENTRY,(100,h,95,110,1,0)],rule,s)
                self.assertEqual(o['active_stop'],100+s*(h-103));self.assertEqual(o['stop_source'],'ATR_TRAIL')

    def test_never_loosen_after_atr_expansion_or_price_retreat(self):
        for rule in ('CONTROL','S1','S2','S3'):
            for s in (1,-1):
                t,o,d,e=self.run_case([ENTRY,(100,125,95,120,1,0),(124,125,123,124,20,0)],rule,s)
                self.assertEqual(t,[]);self.assertEqual(o['active_stop'],100+s*22)
                self.assertFalse(d[1]['ratchet_changed'])

    def test_gap_exceeds_initial_one_r_loss(self):
        for rule in ('CONTROL','S1','S2','S3'):
            for s in (1,-1):
                t,o,d,e=self.run_case([ENTRY,(85,130,80,105,1,0)],rule,s)
                self.assertEqual(t[0]['gross_R'],-1.5);self.assertEqual(t[0]['exit_price'],100-s*15)
                self.assertTrue(t[0]['gap_exit']);self.assertFalse(t[0]['threshold_activated'])

    def test_gap_after_be_or_lock_honors_open(self):
        for rule,h,target in [('S2',110,-.2),('S3',120,.8)]:
            for s in (1,-1):
                op=100+target*10
                t,o,d,e=self.run_case([ENTRY,(100,h,95,105,10,0),(op,130,op-5,105,1,0)],rule,s)
                self.assertAlmostEqual(t[0]['gross_R'],target);self.assertTrue(t[0]['gap_exit'])
                self.assertEqual(t[0]['MFE_R'],(h-100)/10)

    def test_survived_threshold_equality_and_below(self):
        for rule,threshold in [('S1',110),('S2',110),('S3',120)]:
            for s in (1,-1):
                for high in (threshold-0.01,threshold):
                    t,o,d,e=self.run_case([ENTRY,(100,high,95,105,10,0)],rule,s)
                    self.assertEqual(o['threshold_activated'],high==threshold)

    def test_stop_touch_is_exit(self):
        for s in (1,-1):
            t,o,d,e=self.run_case([ENTRY,(100,130,90,100,1,0)],'S3',s)
            self.assertEqual(t[0]['gross_R'],-1);self.assertFalse(t[0]['threshold_activated'])

    def test_terminal_trigger_remains_open_without_liquidation(self):
        for s in (1,-1):
            t,o,d,e=self.run_case([ENTRY,(100,120,95,105,10,0)],'S3',s)
            self.assertEqual(t,[]);self.assertEqual(o['active_stop'],100+s*10)
            self.assertTrue(o['threshold_activated']);self.assertIn('EXCLUDED',o['status'])

    def test_sessions_weekend_year_boundary_persist_state(self):
        times=pd.to_datetime(['2023-12-29T23:45:00+03:00','2023-12-30T00:00:00+03:00','2024-01-03T09:15:00+03:00'])
        for s in (1,-1):
            t,o,d,e=self.run_case([ENTRY,(100,120,95,105,10,0),(108,130,105,110,1,0)],'S3',s,times=times)
            self.assertEqual(t[0]['gross_R'],.8);self.assertEqual(t[0]['initial_risk'],10)
            self.assertTrue(t[0]['cross_calendar_day']);self.assertEqual(t[0]['bars_held'],2)

    def test_occupancy_and_same_close_reentry_are_replayed(self):
        for s in (1,-1):
            t,o,d,e=self.run_case([ENTRY,(100,109,95,100,5,1),(100,120,89,105,5,1)],'S1',s)
            self.assertEqual([r['entry_accepted'] for r in e],[True,False,True])
            self.assertEqual(len(t),1);self.assertIsNotNone(o);self.assertFalse(o['threshold_activated'])
            self.assertEqual(o['entry_price'],100+s*5)

    def test_both_control_multipliers_preserved(self):
        for v,m in [('BASELINE',3),('OPTIMIZED',3.5)]:
            for s in (1,-1):
                t,o,d,e=self.run_case([ENTRY,(100,125,95,120,1,0)],'S1',s,v)
                self.assertEqual(o['active_stop'],100+s*(25-m))

    def test_future_ohlc_never_parsed(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'fixture.csv'
            p.write_text('Ticker;Datetime;Open;High;Low;Close;Volume\nUSDRUBF;2024-12-30 10:00:00;100;101;99;100;1\nUSDRUBF;2025-01-01 10:00:00;NOT;NUMERIC;OHLC;FORBIDDEN;\n')
            f,h=E.read_prefix(p);self.assertEqual(len(f),1)
            import audit
            self.assertEqual(len(audit.A.prefix(p)),1)

    def test_h1_unfinished_and_gapped_blocks_not_used(self):
        index=pd.to_datetime(['2024-01-03T09:15:00+03:00','2024-01-03T09:30:00+03:00','2024-01-03T10:00:00+03:00','2024-01-03T10:15:00+03:00','2024-01-03T10:30:00+03:00','2024-01-03T10:45:00+03:00','2024-01-03T11:00:00+03:00'])
        f=pd.DataFrame(dict(Open=100,High=101,Low=99,Close=100,Volume=1),index=index)
        self.assertTrue(E.context(f).empty)

    def test_prefix_invariance_of_signal_features(self):
        n=420;index=pd.date_range('2024-01-03 09:15',periods=n,freq='15min',tz=E.TZ)
        c=pd.Series([100+i*.05 for i in range(n)],index=index)
        f=pd.DataFrame(dict(Open=c,High=c+.1,Low=c-.1,Close=c,Volume=1))
        full,_=E.indicators(f,E.CONFIGS['BASELINE'])
        prefix,_=E.indicators(f.iloc[:405],E.CONFIGS['BASELINE'])
        pd.testing.assert_frame_equal(full.iloc[:405],prefix)


if __name__=='__main__':unittest.main()
