"""Pre-result causal boundaries, execution invariance, source guard and audit fixtures."""
import io
from pathlib import Path
import tempfile
import unittest
from dataclasses import asdict
import pandas as pd
from engine import E,HERE,features,permits,execute
import audit


def at(s):return pd.Timestamp(s,tz=E.TZ)

def fixture(times,signals=None,side=1):
    ix=pd.DatetimeIndex([at(t) for t in times],name='CloseTime')
    rows=[]
    for i,x in enumerate(ix):
        rows.append({'Open':100.,'High':101.,'Low':99.,'Close':100.,'Volume':1.,'ATR':1.,
            'Signal':(signals or [side]*len(ix))[i],'PriorHigh':99.,'PriorLow':101.,'PreviousATR':1.,
            'H1ADX':25.,'H1PreviousADX':24.,'H1Slope':float(side),'H1PreviousSlope':float(side),
            'H1ATRRatio':1.2,'H1PreviousATRRatio':1.1,'H1AvailableAt':x,'H1PreviousAvailableAt':x-pd.Timedelta(hours=1)})
    return pd.DataFrame(rows,index=ix)


class Gates(unittest.TestCase):
    def test_t1_exact_boundaries(self):
        for stamp,expected in [('09:45',False),('10:00',True),('10:15',True),('17:45',True),('18:00',False),('18:15',False),('00:00',False)]:
            with self.subTest(stamp=stamp):self.assertEqual(permits(at('2024-04-01 '+stamp),None,'T1')[0],expected)
    def test_t1_utc_equivalence(self):
        for x in ('2024-04-01 10:00','2024-04-01 18:00'):
            now=at(x);self.assertEqual(permits(now,None,'T1'),permits(now.tz_convert('UTC'),None,'T1'))
    def test_t2_missing_previous(self):self.assertEqual(permits(at('2024-04-01 10:00'),None,'T2'),(False,'NO_PREVIOUS_OBSERVED_CLOSE'))
    def test_t2_exact_15_allowed(self):self.assertTrue(permits(at('2024-04-01 10:15'),at('2024-04-01 10:00'),'T2')[0])
    def test_t2_first_after_gap_only(self):
        self.assertFalse(permits(at('2024-04-01 10:30'),at('2024-04-01 10:00'),'T2')[0])
        self.assertTrue(permits(at('2024-04-01 10:45'),at('2024-04-01 10:30'),'T2')[0])
    def test_t2_continuous_midnight(self):self.assertTrue(permits(at('2024-04-02 00:00'),at('2024-04-01 23:45'),'T2')[0])
    def test_t2_day_and_weekend_gaps(self):
        for previous,current in [('2024-04-01 23:45','2024-04-02 09:15'),('2024-04-05 23:45','2024-04-08 09:15')]:
            self.assertFalse(permits(at(current),at(previous),'T2')[0])
    def test_t2_previous_every_bar_not_previous_signal(self):
        f=fixture(['2024-04-01 10:00','2024-04-01 10:15'],[0,1])
        self.assertTrue(execute(f,'USDRUBF','BASELINE',E.CONFIGS['BASELINE'],'T2')[3][0]['entry_accepted'])
    def test_timezone_required(self):
        with self.assertRaises(ValueError):permits(pd.Timestamp('2024-04-01 10:00'),None,'T1')
    def test_monotonic_required(self):
        with self.assertRaises(ValueError):permits(at('2024-04-01 10:00'),at('2024-04-01 10:15'),'T2')
    def test_rules_closed(self):
        with self.assertRaises(AssertionError):permits(at('2024-04-01 10:00'),None,'T1+T2')
    def test_independent_gates(self):
        for current,previous in [('2024-04-01 09:45',None),('2024-04-01 10:00','2024-04-01 09:45'),('2024-04-01 18:00','2024-04-01 17:45'),('2024-04-08 09:15','2024-04-05 23:45')]:
            x=at(current);p=at(previous) if previous else None
            for rule in ('CONTROL','T1','T2'):self.assertEqual(permits(x,p,rule),audit.gate(x.to_pydatetime(),p.to_pydatetime() if p else None,rule))


class Execution(unittest.TestCase):
    def test_forbidden_keeps_position_and_stop(self):
        f=fixture(['2024-04-01 10:00','2024-04-01 18:00','2024-04-02 09:15'],[1,1,1])
        for v,p in E.CONFIGS.items():
            c=execute(f,'USDRUBF',v,p,'CONTROL');t=execute(f,'USDRUBF',v,p,'T1')
            self.assertEqual(c[0],t[0]);self.assertEqual(c[1]['active_stop'],t[1]['active_stop'])
            self.assertEqual(c[1]['entry_time'],t[1]['entry_time']);self.assertEqual(len(t[2]),2)
            self.assertFalse(t[3][1]['rule_pass']);self.assertTrue(t[3][1]['position_occupied'])
    def test_t2_forbidden_keeps_open_after_gap(self):
        f=fixture(['2024-04-01 09:45','2024-04-01 10:00','2024-04-02 09:15'],[0,1,1])
        c=execute(f,'USDRUBF','BASELINE',E.CONFIGS['BASELINE'],'CONTROL');t=execute(f,'USDRUBF','BASELINE',E.CONFIGS['BASELINE'],'T2')
        self.assertEqual(c[1]['active_stop'],t[1]['active_stop']);self.assertTrue(t[3][-1]['position_occupied']);self.assertFalse(t[3][-1]['rule_pass'])
    def test_busy_reprocessed_changes_later_entry(self):
        f=fixture(['2024-04-01 09:45','2024-04-01 10:00','2024-04-01 10:15'])
        c=execute(f,'USDRUBF','BASELINE',E.CONFIGS['BASELINE'],'CONTROL');t=execute(f,'USDRUBF','BASELINE',E.CONFIGS['BASELINE'],'T1')
        self.assertFalse(c[3][1]['entry_accepted']);self.assertTrue(t[3][1]['entry_accepted'])
        self.assertNotEqual(c[1]['entry_time'],t[1]['entry_time'])
    def test_same_close_reentry_gated(self):
        for rule,times in [('T1',['2024-04-01 17:30','2024-04-01 17:45','2024-04-01 18:00']),('T2',['2024-04-01 10:00','2024-04-01 10:15','2024-04-02 10:00'])]:
            f=fixture(times,[0,1,1]);f.iloc[-1,f.columns.get_loc('Low')]=97.
            result=execute(f,'USDRUBF','BASELINE',E.CONFIGS['BASELINE'],rule)
            self.assertEqual(len(result[0]),1);self.assertIsNone(result[1]);self.assertFalse(result[3][-1]['entry_accepted'])
            c=execute(f,'USDRUBF','BASELINE',E.CONFIGS['BASELINE'],'CONTROL');self.assertIsNotNone(c[1])
    def test_same_close_reentry_allowed(self):
        f=fixture(['2024-04-01 10:00','2024-04-01 10:15','2024-04-01 10:30'],[0,1,1]);f.iloc[-1,f.columns.get_loc('Low')]=97.
        for rule in ('CONTROL','T1','T2'):
            t=execute(f,'USDRUBF','BASELINE',E.CONFIGS['BASELINE'],rule)
            self.assertEqual(len(t[0]),1);self.assertIsNotNone(t[1]);self.assertTrue(t[3][-1]['entry_accepted'])
    def test_stop_first_long_short(self):
        for side in (1,-1):
            f=fixture(['2024-04-01 10:00','2024-04-01 10:15'],[side,0],side)
            f.iloc[-1,f.columns.get_loc('Low')]=90.;f.iloc[-1,f.columns.get_loc('High')]=110.
            t=execute(f,'USDRUBF','BASELINE',E.CONFIGS['BASELINE'],'CONTROL')[0][0]
            self.assertEqual(t['gross_R'],-1.);self.assertEqual(t['MFE_R'],0.);self.assertEqual(t['trailing_updates'],0)
    def test_adverse_open_gap_long_short(self):
        for side,opening in ((1,90.),(-1,110.)):
            f=fixture(['2024-04-01 10:00','2024-04-02 10:00'],[side,0],side)
            f.iloc[-1,f.columns.get_loc('Open')]=opening
            f.iloc[-1,f.columns.get_loc('Low')]=min(99.,opening);f.iloc[-1,f.columns.get_loc('High')]=max(101.,opening)
            t=execute(f,'USDRUBF','BASELINE',E.CONFIGS['BASELINE'],'CONTROL')[0][0]
            self.assertEqual(t['exit_price'],opening);self.assertEqual(t['gross_R'],-5.);self.assertTrue(t['gap_exit'])
    def test_trail_only_after_survived_bar(self):
        f=fixture(['2024-04-01 10:00','2024-04-01 10:15','2024-04-01 10:30'],[1,0,0])
        f.iloc[1,f.columns.get_loc('High')]=110.;f.iloc[2,f.columns.get_loc('Open')]=108.
        t=execute(f,'USDRUBF','BASELINE',E.CONFIGS['BASELINE'],'CONTROL')
        self.assertFalse(t[2][0]['stop_hit']);self.assertEqual(t[2][0]['active_stop'],98.)
        self.assertEqual(t[2][0]['active_stop_next_bar'],107.);self.assertEqual(t[0][0]['exit_price'],107.)
    def test_year_transfer_and_open_snapshot(self):
        f=fixture(['2023-12-29 10:00','2024-01-03 10:00'],[1,0])
        t=execute(f,'USDRUBF','BASELINE',E.CONFIGS['BASELINE'],'T1')
        self.assertEqual(len(t[0]),0);self.assertIsNotNone(t[1]);self.assertEqual([s['year'] for s in t[5]],[2023,2024])
    def test_first_bar_is_blocked_in_t2(self):
        f=fixture(['2024-04-01 10:00','2024-04-01 10:15'])
        t=execute(f,'USDRUBF','BASELINE',E.CONFIGS['BASELINE'],'T2')
        self.assertEqual(t[3][0]['rule_reason'],'NO_PREVIOUS_OBSERVED_CLOSE');self.assertFalse(t[3][0]['entry_accepted']);self.assertTrue(t[3][1]['entry_accepted'])
    def test_no_future_bars(self):
        f=fixture(['2025-01-01 10:00'])
        with self.assertRaises(AssertionError):execute(f,'USDRUBF','BASELINE',E.CONFIGS['BASELINE'],'CONTROL')
    def test_future_poison_OHLC_not_parsed(self):
        with tempfile.TemporaryDirectory(dir=HERE/'work') as tmp:
            p=Path(tmp)/'poison.csv';p.write_text('Ticker;Datetime;Open;High;Low;Close;Volume\nX;2024-12-30 10:00:00;1;2;0;1;1\nX;2025-01-01 10:00:00;FORBIDDEN;OHLC;POISON\n')
            self.assertEqual(len(E.read_prefix(p)[0]),1);self.assertEqual(len(audit.prefix(p)),1)
    def test_indicators_prefix_invariant(self):
        ix=pd.date_range('2024-01-03 10:00',periods=600,freq='15min',tz=E.TZ,name='CloseTime')
        f=pd.DataFrame({'Open':[100.+i*.01 for i in range(600)],'High':[101.+i*.01 for i in range(600)],'Low':[99.+i*.01 for i in range(600)],'Close':[100.1+i*.01 for i in range(600)],'Volume':1},index=ix)
        a,_=features(f,E.CONFIGS['BASELINE']);b,_=features(f.iloc[:477],E.CONFIGS['BASELINE'])
        pd.testing.assert_frame_equal(a.iloc[:477],b)
    def test_replay_prefix_no_lookahead(self):
        f=fixture(['2024-04-01 09:45','2024-04-01 10:00','2024-04-01 10:15','2024-04-02 09:15'])
        for rule in ('CONTROL','T1','T2'):
            a=execute(f,'USDRUBF','BASELINE',E.CONFIGS['BASELINE'],rule);b=execute(f.iloc[:3],'USDRUBF','BASELINE',E.CONFIGS['BASELINE'],rule)
            self.assertEqual(a[3][:3],b[3]);self.assertEqual(a[2][:len(b[2])],b[2])
    def test_all_synthetic_records_independent_replay(self):
        f=fixture(['2024-04-01 09:45','2024-04-01 10:00','2024-04-01 10:15','2024-04-02 10:00'])
        f.iloc[-1,f.columns.get_loc('Low')]=97.
        rows=[]
        for b in f.itertuples():
            rows.append({'at':b.Index.to_pydatetime(),'o':b.Open,'h':b.High,'l':b.Low,'c':b.Close,
                'atr':b.ATR,'previous_atr':b.PreviousATR,'signal':b.Signal,'upper':b.PriorHigh,'lower':b.PriorLow,
                'h1':{'at':b.H1AvailableAt.to_pydatetime(),'adx':b.H1ADX,'slope':b.H1Slope,'ratio':b.H1ATRRatio},
                'previous_h1':{'at':b.H1PreviousAvailableAt.to_pydatetime(),'adx':b.H1PreviousADX,'slope':b.H1PreviousSlope,'ratio':b.H1PreviousATRRatio}})
        for rule in ('CONTROL','T1','T2'):
            a=execute(f,'USDRUBF','BASELINE',E.CONFIGS['BASELINE'],rule);b=audit.simulate(rows,asdict(E.CONFIGS['BASELINE']),rule,'USDRUBF','BASELINE')
            self.assertEqual(a,b)

if __name__=='__main__':unittest.main(verbosity=2)
