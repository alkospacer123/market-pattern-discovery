"""Pre-result synthetic execution, symmetry, occupancy, and future-data guards."""
import ast
from pathlib import Path
import tempfile
import unittest
import numpy as np
import pandas as pd
from engine import E,HERE,RULES,execute,features,initial,tick


def bars(values):
    at=pd.Timestamp('2023-02-01 10:15',tz=E.TZ)
    rows=[]
    for i,values_i in enumerate(values):
        b={'Open':100.,'High':101.,'Low':99.,'Close':100.,'ATR':1.,'Signal':0,'PriorHigh':99.,'PriorLow':101.,
            'PreviousATR':1.,'H1ADX':25.,'H1PreviousADX':24.,'H1Slope':1.,'H1PreviousSlope':.8,
            'H1ATRRatio':1.1,'H1PreviousATRRatio':1.,'H1AvailableAt':at,'H1PreviousAvailableAt':at-pd.Timedelta(hours=1)}
        b.update(values_i);rows.append(b)
    return pd.DataFrame(rows,index=pd.date_range(at,periods=len(rows),freq='15min'))


def replay(f,rule='CONTROL',version='BASELINE'):
    return execute(f,'USDRUBF',version,E.CONFIGS[version],rule)


class Mechanics(unittest.TestCase):
    def test_four_exact_mechanisms_both_directions(self):
        for sign in (1,-1):
            f=bars([{'Signal':sign,'Low':99.5,'High':100.5,'PriorHigh':99.8,'PriorLow':100.2}])
            b=next(f.itertuples())
            expected={'CONTROL':100-sign*2,'I1':100-sign*.5,'I2':100-sign*.2,'I3':100-sign*.5}
            for rule,x in expected.items():self.assertAlmostEqual(initial(b,rule),x)
    def test_cap_never_expands(self):
        for sign in (1,-1):
            for dist in (.25,1.,2.,4.,10.):
                f=bars([{'Signal':sign,'Low':100-dist,'High':100+dist}])
                b=next(f.itertuples());self.assertLessEqual(abs(100-initial(b,'I3')),2.)
    def test_zero_stop_skips_and_later_signal_executes(self):
        for sign in (1,-1):
            f=bars([{'Signal':sign,'Low':100.,'High':100.},{'Signal':sign}])
            for rule in ('I1','I3'):
                t,o,d,e,y=replay(f,rule)
                self.assertEqual(e[0]['outcome'],'NONPOSITIVE_INITIAL_RISK');self.assertFalse(e[0]['entry_accepted'])
                self.assertTrue(e[1]['entry_accepted']);self.assertEqual(o['trade_id'],'T3-M15-Si-000001')
    def test_nonfinite_stop_no_fallback(self):
        for sign in (1,-1):
            f=bars([{'Signal':sign,'PriorHigh':np.nan,'PriorLow':np.nan}])
            t,o,d,e,y=replay(f,'I2');self.assertIsNone(o)
            self.assertEqual(e[0]['outcome'],'NONFINITE_INITIAL_RISK')
    def test_nonfinite_control_risk(self):
        f=bars([{'Signal':1,'ATR':np.inf}]);t,o,d,e,y=replay(f)
        self.assertFalse(e[0]['entry_accepted']);self.assertEqual(e[0]['validity_reason'],'NONFINITE_INITIAL_RISK')
    def test_gap_long_short(self):
        for sign in (1,-1):
            f=bars([{'Signal':sign},{'Open':100-sign*3.,'Low':96.,'High':104.}])
            t,o,d,e,y=replay(f);self.assertEqual(t[0]['exit_price'],100-sign*3.)
            self.assertEqual(t[0]['gross_R'],-1.5);self.assertTrue(t[0]['gap_exit'])
    def test_stop_before_extreme_long_short(self):
        for sign in (1,-1):
            f=bars([{'Signal':sign},{'Low':97.,'High':103.}])
            t,o,d,e,y=replay(f);self.assertEqual(t[0]['gross_R'],-1.)
            self.assertEqual(t[0]['MFE_R'],0.);self.assertIsNone(d[0]['extreme_after'])
    def test_trailing_effective_next_bar(self):
        f=bars([{'Signal':1},{'High':105.,'Low':99.,'Close':101.},{'Open':101.,'High':103.,'Low':100.}])
        t,o,d,e,y=replay(f);self.assertEqual(t[0]['bars_held'],2)
        self.assertEqual(d[0]['active_stop'],98.);self.assertEqual(d[0]['active_stop_next_bar'],102.)
        self.assertEqual(t[0]['exit_price'],101.);self.assertEqual(t[0]['initial_risk'],2.)
        self.assertEqual(t[0]['gross_R'],.5)
    def test_trailing_short_reflection(self):
        f=bars([{'Signal':-1},{'High':101.,'Low':95.,'Close':99.},{'Open':99.,'High':100.,'Low':97.}])
        t,o,d,e,y=replay(f);self.assertEqual(t[0]['exit_price'],99.);self.assertEqual(t[0]['gross_R'],.5)
        self.assertEqual(d[0]['active_stop_next_bar'],98.)
    def test_same_bar_reentry_after_exit(self):
        f=bars([{'Signal':1},{'Signal':-1,'Low':97.},{'High':103.}])
        t,o,d,e,y=replay(f);self.assertEqual(len(t),2);self.assertEqual(t[1]['entry_time'],t[0]['exit_time'])
        self.assertEqual([x['direction'] for x in t],['LONG','SHORT'])
    def test_busy_signals_not_filled(self):
        f=bars([{'Signal':1},{'Signal':1},{'Signal':-1}])
        t,o,d,e,y=replay(f);self.assertEqual([x['outcome'] for x in e],['ACCEPTED','POSITION_OCCUPIED','POSITION_OCCUPIED'])
    def test_invalid_candidate_logged_even_if_busy(self):
        f=bars([{'Signal':1},{'Signal':1,'PriorHigh':np.nan,'Low':99.5}])
        t,o,d,e,y=replay(f,'I2');self.assertEqual(e[1]['outcome'],'POSITION_OCCUPIED')
        self.assertEqual(e[1]['validity_reason'],'NONFINITE_INITIAL_RISK')
    def test_standalone_occupancy_changes_reentries(self):
        f=bars([{'Signal':1},{'Signal':1,'Low':98.5},{'Low':99.}])
        a=replay(f,'CONTROL');b=replay(f,'I1')
        self.assertFalse(a[3][1]['entry_accepted']);self.assertTrue(b[3][1]['entry_accepted'])
    def test_both_trailing_constants(self):
        f=bars([{'Signal':1},{'High':105.,'Low':99.}])
        self.assertEqual(replay(f,'CONTROL','BASELINE')[2][0]['active_stop_next_bar'],102.)
        self.assertEqual(replay(f,'CONTROL','OPTIMIZED')[2][0]['active_stop_next_bar'],101.5)
    def test_no_year_forced_exit_and_boundary_snapshot(self):
        f=bars([{'Signal':1},{},{'Low':97.}])
        f.index=pd.DatetimeIndex([pd.Timestamp(t,tz=E.TZ) for t in ('2023-12-29 23:45','2024-01-03 10:15','2024-01-03 10:30')])
        t,o,d,e,y=replay(f);self.assertEqual(len(t),1);self.assertEqual(t[0]['year'],2024)
        self.assertEqual(y[0]['year'],2023);self.assertEqual(t[0]['bars_held'],2)
    def test_terminal_open_not_in_closed(self):
        t,o,d,e,y=replay(bars([{'Signal':1},{}]));self.assertFalse(t);self.assertIsNotNone(o)
    def test_fixed_reference_risk_separate(self):
        f=bars([{'Signal':1,'Low':99.5},{'Low':99.}]);t,o,d,e,y=replay(f,'I1')
        self.assertEqual(t[0]['gross_R'],-1.);self.assertEqual(t[0]['reference_2ATR_R'],-.25)
    def test_exchange_ticks_not_reproduction_units(self):
        at=pd.Timestamp('2023-09-27 18:59',tz=E.TZ);after=at+pd.Timedelta(minutes=1)
        self.assertEqual(tick('CNYRUBF',at),.01);self.assertEqual(tick('CNYRUBF',after),.001)
        self.assertEqual(tick('USDRUBF',at),.01);self.assertEqual(tick('GLDRUBF',at),.1);self.assertEqual(tick('IMOEXF',at),.5)


class Causality(unittest.TestCase):
    def test_future_prefix_poison_never_parsed(self):
        with tempfile.TemporaryDirectory(dir=HERE/'work') as folder:
            p=Path(folder)/'poison.csv'
            p.write_text('Ticker;Datetime;Open;High;Low;Close;Volume\nX;2023-01-03 10:00:00;100;101;99;100;1\nX;2025-01-01 00:00:00;FUTURE_OHLC_MUST_NOT_PARSE\n')
            raw,_=E.read_prefix(p);self.assertEqual(len(raw),1)
            import audit
            self.assertEqual(len(audit.A.prefix(p)),1)
    def test_future_execution_rejected(self):
        f=bars([{'Signal':1}]);f.index=pd.DatetimeIndex([E.END])
        with self.assertRaisesRegex(AssertionError,'FUTURE_OHLC_FORBIDDEN'):replay(f)
    def test_indicator_and_signal_prefix_invariance(self):
        rng=np.random.default_rng(712)
        indexes=[]
        for day in pd.date_range('2023-01-03',periods=18,freq='B',tz=E.TZ):indexes.extend(pd.date_range(day+pd.Timedelta(hours=10,minutes=15),periods=32,freq='15min'))
        prices=100+np.cumsum(rng.normal(.02,.1,len(indexes)))
        f=pd.DataFrame({'Open':prices,'Close':prices+.03,'High':prices+.2,'Low':prices-.2,'Volume':1.},index=indexes)
        full,h=features(f,E.CONFIGS['BASELINE'])
        for n in (137,256,511):
            prefix,_=features(f.iloc[:n],E.CONFIGS['BASELINE'])
            pd.testing.assert_frame_equal(prefix,full.iloc[:n])
        self.assertTrue((full.H1AvailableAt.dropna()<=full.loc[full.H1AvailableAt.notna()].index).all())
        pd.testing.assert_series_equal(full.PriorHigh,f.High.rolling(20).max().shift(1),check_names=False)
    def test_changed_future_does_not_change_entries_or_stops(self):
        f=bars([{'Signal':1},{'High':105.},{'Low':100.},{'Low':90.}])
        short=replay(f.iloc[:2],'I1');full=replay(f,'I1')
        self.assertEqual(short[3],full[3]);self.assertEqual(short[2],full[2][:1])
    def test_no_production_imports_or_future_file_paths(self):
        for p in HERE.glob('*.py'):
            tree=ast.parse(p.read_text())
            for node in ast.walk(tree):
                if isinstance(node,ast.ImportFrom):self.assertNotIn('TradingSystemLab',node.module or '')
                if isinstance(node,ast.Import):self.assertTrue(all('TradingSystemLab' not in a.name for a in node.names))

if __name__=='__main__':
    (HERE/'work').mkdir(exist_ok=True)
    unittest.main(verbosity=2)
