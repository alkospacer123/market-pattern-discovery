"""Pre-result paired causal fixtures; historical COMBINED results not run here."""
import unittest
import pandas as pd
import independent as I
import independent_combination as J
import engine as E
from test_causal import fixture, at

def frame(bars):
    rows=[]
    for b in bars:
        r={k:b[v] for k,v in [('Open','o'),('High','h'),('Low','l'),('Close','c'),('Volume','v'),
            ('ATR','atr'),('PreviousATR','previous_atr'),('PriorHigh','upper'),('PriorLow','lower'),('Signal','signal')]}
        for name,key in [('ADX','adx'),('Slope','slope'),('ATRRatio','ratio'),('AvailableAt','at')]:
            r['H1'+name]=b['h1'][key];r['H1Previous'+name]=b['previous_h1'][key]
        rows.append(r)
    return pd.DataFrame(rows,index=pd.DatetimeIndex([b['at'] for b in bars],name='CloseTime'))

class Combination(unittest.TestCase):
    def both(self,bars,rule='COMBINED',version='BASELINE'):
        a=E.replay(frame(bars),'USDRUBF',version,rule);b=J.simulate(bars,'USDRUBF',version,rule)
        c=I.Comparison()
        for name,aa,bb,keys in [('trades',a[0],b[0],['entry_time']),('stops',a[2],b[2],['bar_close_time']),('entries',a[3],b[3],['signal_time']),('gaps',a[4],b[4],['current_close']),('snapshots',a[5],b[5],['month'])]:
            c.rows(aa,bb,name,keys)
        c.rows([a[1]] if a[1] else [],[b[1]] if b[1] else [],'OPEN',['entry_time'])
        self.assertFalse(c.diffs,c.diffs[:3]);return a
    def test_combo_fixed_hours(self):
        f=fixture(['2024-04-01 09:45','2024-04-01 10:00','2024-04-01 18:00'],[1,1,1])
        a=self.both(f);self.assertFalse(a[3][0]['entry_accepted']);self.assertTrue(a[3][1]['entry_accepted']);self.assertFalse(a[3][2]['entry_accepted'])
    def test_initial_stop_2ATR_both_sides_versions(self):
        for side in (1,-1):
            for v in I.VERSIONS:
                f=fixture(['2024-04-01 10:00'],[side],side)
                a=self.both(f,version=v);self.assertEqual(a[1]['initial_stop'],100-side*2);self.assertEqual(a[1]['initial_risk'],2.)
    def test_entry_candle_favorable_extreme_ignored(self):
        for side in (1,-1):
            f=fixture(['2024-04-01 10:00'],[side],side);f[0].update(h=200.,l=1.)
            a=self.both(f);self.assertFalse(a[1]['threshold_activated']);self.assertEqual(a[1]['favorable_extreme'],100.)
    def test_stop_unchanged_before_1R_both_sides(self):
        for side in (1,-1):
            f=fixture(['2024-04-01 10:00','2024-04-01 10:15'],[side,0],side);f[1]['atr']=.1
            a=self.both(f);self.assertEqual(a[1]['active_stop'],100-side*2);self.assertFalse(a[1]['threshold_activated'])
    def test_exact_1R_survived_activation_next_bar_both_sides(self):
        for side in (1,-1):
            for version,trail in I.VERSIONS.items():
                f=fixture(['2024-04-01 10:00','2024-04-01 10:15','2024-04-02 09:15'],[side,0,0],side)
                f[1].update(h=102. if side==1 else 101.,l=99. if side==1 else 98.,atr=.1)
                f[2].update(o=100+side*1.5,h=103.,l=97.)
                a=self.both(f,version=version)
                self.assertEqual(a[2][0]['active_stop'],100-side*2);self.assertFalse(a[2][0]['stop_hit'])
                self.assertTrue(a[2][0]['threshold_activated_now']);self.assertEqual(a[2][0]['active_stop_next_bar'],100+side*(2-trail*.1))
                self.assertEqual(a[0][0]['exit_price'],100+side*1.5)
    def test_stop_hit_on_activation_candle_stop_first_both_sides(self):
        for side in (1,-1):
            f=fixture(['2024-04-01 10:00','2024-04-01 10:15'],[side,0],side);f[1].update(h=110.,l=90.)
            a=self.both(f);self.assertFalse(a[0][0]['threshold_activated']);self.assertEqual(a[0][0]['MFE_R'],0.);self.assertEqual(a[0][0]['gross_R'],-1.)
    def test_immutable_initial_R_activation(self):
        f=fixture(['2024-04-01 10:00','2024-04-01 10:15'],[1,0]);f[1].update(h=101.9,atr=.01)
        a=self.both(f);self.assertFalse(a[1]['threshold_activated']);self.assertEqual(a[1]['initial_risk'],2.)
    def test_all_accumulated_extrema_after_activation_both_sides(self):
        for side in (1,-1):
            f=fixture(['2024-04-01 10:00','2024-04-01 10:15','2024-04-01 10:30'],[side,0,0],side)
            f[1].update(h=103. if side==1 else 101.,l=99. if side==1 else 97.,atr=2.)
            f[2].update(h=102. if side==1 else 101.,l=99. if side==1 else 98.,atr=.5)
            a=self.both(f);self.assertEqual(a[1]['active_stop'],100+side*1.5);self.assertEqual(a[1]['favorable_extreme'],100+side*3.)
    def test_stop_never_weakens(self):
        for side in (1,-1):
            f=fixture(['2024-04-01 10:00','2024-04-01 10:15','2024-04-01 10:30'],[side,0,0],side)
            f[1].update(h=103. if side==1 else 101.,l=99. if side==1 else 97.,atr=1.)
            f[2].update(o=101. if side==1 else 99.,h=103. if side==1 else 99.5,l=100.5 if side==1 else 97.,atr=1000.)
            a=self.both(f);self.assertEqual(a[2][0]['active_stop_next_bar'],a[2][1]['active_stop_next_bar'])
    def test_holding_activation_outside_core_hours(self):
        f=fixture(['2024-04-01 17:45','2024-04-01 18:00','2024-04-02 09:15'],[1,0,0]);f[1].update(h=103.)
        f[2].update(o=101.,h=102.,l=100.5,c=101.)
        a=self.both(f);self.assertEqual(a[1]['entry_time'],at('2024-04-01 17:45'));self.assertEqual(a[1]['activation_time'],at('2024-04-01 18:00'))
    def test_adverse_gap_before_activation(self):
        for side in (1,-1):
            f=fixture(['2024-04-01 10:00','2024-04-02 10:00'],[side,0],side)
            f[1].update(o=100-side*10,h=110.,l=90.)
            a=self.both(f);self.assertEqual(a[0][0]['gross_R'],-5.);self.assertFalse(a[0][0]['threshold_activated'])
    def test_same_close_reentry_after_stop_gated(self):
        for stamp,allowed in [('10:15',True),('18:00',False)]:
            f=fixture(['2024-04-01 10:00','2024-04-01 '+stamp],[1,1]);f[1]['l']=97.
            a=self.both(f);self.assertEqual(a[3][-1]['entry_accepted'],allowed)
    def test_prefix_invariance_all_four_rules(self):
        f=fixture(['2024-04-01 09:45','2024-04-01 10:00','2024-04-01 10:15','2024-04-02 09:15'],[1,1,1,0])
        for rule in E.RULES:
            a=self.both(f,rule);b=self.both(f[:3],rule)
            self.assertEqual(a[2][:len(b[2])],b[2]);self.assertEqual(a[3][:len(b[3])],b[3])
    def test_primary_raw_future_poison(self):
        import tempfile
        from pathlib import Path
        with tempfile.TemporaryDirectory(dir=I.HERE/'work') as tmp:
            path=Path(tmp)/'poison.csv';path.write_text('Ticker;Datetime;Open;High;Low;Close;Volume\nX;2024-12-30 10:00:00;1;2;0;1;1\nX;2025-01-01 10:00:00;FORBIDDEN;OHLC;POISON\n')
            self.assertEqual(len(E.read_source(path)),1)
    def test_primary_feature_prefix_and_independent_signal(self):
        from test_causal import Features
        raw=Features().raw(600)
        f=pd.DataFrame([{k:b[v] for k,v in [('Open','o'),('High','h'),('Low','l'),('Close','c'),('Volume','v')]} for b in raw],index=pd.DatetimeIndex([b['at'] for b in raw],name='CloseTime'))
        a=E.features(f);b=E.features(f.iloc[:477]);pd.testing.assert_frame_equal(a.iloc[:477],b)
        independent=I.build_features(raw)
        self.assertEqual(list(a.Signal),[b['signal'] for b in independent])
        for i,b in enumerate(independent):
            if b['h1']:self.assertEqual(a.H1AvailableAt.iloc[i],b['h1']['at'])

if __name__=='__main__':unittest.main(verbosity=2)
