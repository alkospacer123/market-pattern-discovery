"""Pre-outcome causal fixtures for the exact six permitted replays."""
import tempfile
import unittest
from pathlib import Path
import pandas as pd
from engine import E, RULES, execute, features


def frame(bars,sign=1,times=None):
    index=pd.date_range('2024-01-05 23:00',periods=len(bars),freq='15min',tz=E.TZ) if times is None else pd.DatetimeIndex(times)
    rows=[]
    for o,h,l,c,atr,sig in bars:
        if sign==-1:o,h,l,c=200-o,200-l,200-h,200-c
        rows.append(dict(Open=o,High=h,Low=l,Close=c,ATR=atr,Signal=sig*sign,PriorHigh=99,PriorLow=101,
            PreviousATR=atr*.9,H1ADX=25.,H1PreviousADX=24.,H1Slope=sign,H1PreviousSlope=sign,
            H1ATRRatio=1.2,H1PreviousATRRatio=1.1,H1AvailableAt=index[0],H1PreviousAvailableAt=index[0]-pd.Timedelta(hours=1)))
    return pd.DataFrame(rows,index=index)

ENTRY=(100,140,60,100,5,1)


class CausalTests(unittest.TestCase):
    def run_case(self,bars,rule,sign=1,version='BASELINE',times=None):
        return execute(frame(bars,sign,times),'USDRUBF',version,E.CONFIGS[version],rule)

    def test_exact_scope(self):
        self.assertEqual(RULES,('CONTROL','A6','A7','S1','C1','C2'))

    def test_signal_extreme_excluded(self):
        for rule in RULES:
            for s in (1,-1):
                t,o,d,e=self.run_case([ENTRY],rule,s)
                self.assertEqual(t,[]);self.assertEqual(d,[]);self.assertFalse(o['threshold_activated'])
                self.assertEqual(o['favorable_extreme'],100);self.assertEqual(o['active_stop'],100-s*10)

    def test_old_stop_before_activation(self):
        for rule in RULES:
            for s in (1,-1):
                t,o,d,e=self.run_case([ENTRY,(100,130,89,105,1,0)],rule,s)
                self.assertEqual(t[0]['gross_R'],-1);self.assertFalse(t[0]['threshold_activated'])
                self.assertEqual(t[0]['MFE_R'],0);self.assertIsNone(d[0]['favorable_extreme_after']);self.assertIsNone(o)

    def test_initial_stop_fixed_before_1r(self):
        for rule in ('S1','C1','C2'):
            for s in (1,-1):
                t,o,d,e=self.run_case([ENTRY,(100,109,95,100,1,0),(100,108,95,100,1,0)],rule,s)
                self.assertEqual(o['active_stop'],100-s*10);self.assertFalse(o['threshold_activated']);self.assertEqual(o['stop_updates'],0)

    def test_accumulated_extreme_next_bar_activation(self):
        for rule in ('S1','C1','C2'):
            for s in (1,-1):
                t,o,d,e=self.run_case([ENTRY,(100,109,95,100,1,0),(100,110,94,100,5,0),(100,108,96,100,1,0)],rule,s)
                self.assertEqual(t,[]);self.assertTrue(d[1]['threshold_activated_now']);self.assertEqual(d[1]['active_stop_next_bar'],100-s*5)
                self.assertEqual(o['active_stop'],100+s*7);self.assertEqual(o['initial_risk'],10)

    def test_threshold_equality(self):
        for rule in ('S1','C1','C2'):
            for s in (1,-1):
                for hi in (109.99,110):
                    t,o,d,e=self.run_case([ENTRY,(100,hi,95,105,10,0)],rule,s)
                    self.assertEqual(o['threshold_activated'],hi==110)

    def test_new_stop_no_retroactive_exit(self):
        for rule in ('S1','C1','C2'):
            for s in (1,-1):
                t,o,d,e=self.run_case([ENTRY,(100,110,95,98,1,0)],rule,s)
                self.assertEqual(t,[]);self.assertEqual(o['active_stop'],100+s*7);self.assertEqual(d[0]['phase'],'SURVIVED')
                t,o,d,e=self.run_case([ENTRY,(100,110,95,98,1,0),(98,111,95,105,1,0)],rule,s)
                self.assertEqual(t[0]['gross_R'],-.2);self.assertTrue(t[0]['gap_exit'])

    def test_never_loosen(self):
        for rule in RULES:
            for s in (1,-1):
                t,o,d,e=self.run_case([ENTRY,(100,125,95,120,1,0),(124,125,123,124,20,0)],rule,s)
                self.assertEqual(t,[]);self.assertEqual(o['active_stop'],100+s*22);self.assertFalse(d[1]['ratchet_changed'])

    def test_gap_exceeds_initial_risk(self):
        for rule in RULES:
            for s in (1,-1):
                t,o,d,e=self.run_case([ENTRY,(85,130,80,105,1,0)],rule,s)
                self.assertEqual(t[0]['gross_R'],-1.5);self.assertFalse(t[0]['threshold_activated']);self.assertTrue(t[0]['gap_exit'])

    def test_stop_touch_exits(self):
        for rule in ('S1','C1','C2'):
            for s in (1,-1):
                t,o,d,e=self.run_case([ENTRY,(100,130,90,100,1,0)],rule,s)
                self.assertEqual(t[0]['gross_R'],-1);self.assertFalse(t[0]['threshold_activated'])

    def test_terminal_open_not_liquidated(self):
        for rule in ('S1','C1','C2'):
            for s in (1,-1):
                t,o,d,e=self.run_case([ENTRY,(100,110,95,105,1,0)],rule,s)
                self.assertEqual(t,[]);self.assertTrue(o['threshold_activated']);self.assertIn('EXCLUDED',o['status'])

    def test_session_year_state_persists(self):
        times=pd.to_datetime(['2023-12-29T23:45:00+03:00','2023-12-30T00:00:00+03:00','2024-01-03T09:15:00+03:00'])
        for rule in ('S1','C1','C2'):
            for s in (1,-1):
                t,o,d,e=self.run_case([ENTRY,(100,110,95,105,1,0),(105,130,95,110,1,0)],rule,s,times=times)
                self.assertEqual(t[0]['gross_R'],.5);self.assertEqual(t[0]['initial_risk'],10);self.assertTrue(t[0]['cross_calendar_day'])

    def test_same_close_reentry_and_occupancy(self):
        for rule in RULES:
            for s in (1,-1):
                t,o,d,e=self.run_case([ENTRY,(100,109,95,100,5,1),(100,120,89,105,5,1)],rule,s)
                self.assertEqual([r['entry_accepted'] for r in e],[True,False,True]);self.assertEqual(len(t),1)
                self.assertFalse(o['threshold_activated']);self.assertEqual(o['entry_price'],100+s*5)

    def test_two_trail_multipliers(self):
        for rule in RULES:
            for v,m in [('BASELINE',3),('OPTIMIZED',3.5)]:
                for s in (1,-1):
                    t,o,d,e=self.run_case([ENTRY,(100,125,95,120,1,0)],rule,s,v)
                    self.assertEqual(o['active_stop'],100+s*(25-m))

    def test_a6_strict_and_missing_previous_h1(self):
        for rule in ('A6','C1'):
            for s in (1,-1):
                for prev in (1.2,1.3,float('nan')):
                    f=frame([ENTRY],s);f['H1PreviousATRRatio']=prev
                    t,o,d,e=execute(f,'USDRUBF','BASELINE',E.CONFIGS['BASELINE'],rule)
                    self.assertIsNone(o);self.assertFalse(e[0]['rule_pass']);self.assertEqual(e[0]['decision_reason'],'FILTER_FAILED')

    def test_a7_strict_and_missing_previous_m15(self):
        for rule in ('A7','C2'):
            for s in (1,-1):
                for prev in (5,6,float('nan')):
                    f=frame([ENTRY],s);f['PreviousATR']=prev
                    t,o,d,e=execute(f,'USDRUBF','BASELINE',E.CONFIGS['BASELINE'],rule)
                    self.assertIsNone(o);self.assertFalse(e[0]['rule_pass'])

    def test_filters_do_not_affect_existing_position(self):
        for rule in ('C1','C2'):
            f=frame([ENTRY,(100,110,95,100,1,1),(100,120,89,105,5,1)])
            f.loc[f.index[1],'H1PreviousATRRatio']=2;f.loc[f.index[1],'PreviousATR']=2
            t,o,d,e=execute(f,'USDRUBF','BASELINE',E.CONFIGS['BASELINE'],rule)
            self.assertFalse(e[1]['rule_pass']);self.assertTrue(e[1]['position_occupied']);self.assertEqual(e[1]['decision_reason'],'FILTER_AND_OCCUPIED')
            self.assertTrue(d[0]['threshold_activated_now']);self.assertEqual(len(t),1)

    def test_future_ohlc_never_parsed(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'fixture.csv'
            p.write_text('Ticker;Datetime;Open;High;Low;Close;Volume\nUSDRUBF;2024-12-30 10:00:00;100;101;99;100;1\nUSDRUBF;2025-01-01 10:00:00;NOT;NUMERIC;OHLC;FORBIDDEN;\n')
            f,h=E.read_prefix(p);self.assertEqual(len(f),1)
            import audit
            self.assertEqual(len(audit.A.prefix(p)),1)

    def test_incomplete_gapped_h1_not_used(self):
        index=pd.to_datetime(['2024-01-03T09:15:00+03:00','2024-01-03T09:30:00+03:00','2024-01-03T10:00:00+03:00','2024-01-03T10:15:00+03:00','2024-01-03T10:30:00+03:00','2024-01-03T10:45:00+03:00','2024-01-03T11:00:00+03:00'])
        f=pd.DataFrame(dict(Open=100,High=101,Low=99,Close=100,Volume=1),index=index)
        self.assertTrue(E.context(f).empty)

    def test_prefix_invariance(self):
        n=420;index=pd.date_range('2024-01-03 09:15',periods=n,freq='15min',tz=E.TZ)
        c=pd.Series([100+i*.05 for i in range(n)],index=index);f=pd.DataFrame(dict(Open=c,High=c+.1,Low=c-.1,Close=c,Volume=1))
        full,_=features(f,E.CONFIGS['BASELINE']);prefix,_=features(f.iloc[:405],E.CONFIGS['BASELINE'])
        pd.testing.assert_frame_equal(full.iloc[:405],prefix)


if __name__=='__main__':unittest.main()
