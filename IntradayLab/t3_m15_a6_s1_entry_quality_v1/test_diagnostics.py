"""Synthetic causal and censoring fixtures; no historical outcome selection."""
import unittest,copy
from datetime import datetime
import pandas as pd
import common as C,engine as E
import diagnostics as D,scalar_diagnostics as S

class DiagnosticsCausal(unittest.TestCase):
    def setUp(self):
        self.bars=[]
        for i in range(480):
            p=100+i*.03
            self.bars.append({'at':datetime(2024,4,1,9,tzinfo=C.TZ)+i*C.STEP,'o':p,'h':p+1,'l':p-1,'c':p+.2,'v':1.})
        self.raw=pd.DataFrame([{k:b[v] for k,v in [('Open','o'),('High','h'),('Low','l'),('Close','c'),('Volume','v')]} for b in self.bars],index=pd.DatetimeIndex([b['at'] for b in self.bars]))
    def test_feature_prefix_invariance_and_availability(self):
        whole=E.features(self.raw);prefix=E.features(self.raw.iloc[:420]);scalar=C.build_features(self.bars);short=C.build_features(self.bars[:420])
        for i in (350,400,419):
            at=self.bars[i]['at'];a=D.feature(whole.loc[at],at,'USDRUBF',1);b=D.feature(prefix.loc[at],at,'USDRUBF',1)
            self.assertEqual(C.plain(a),C.plain(b));self.assertEqual(S.causal_fields(scalar[i],'USDRUBF',1),S.causal_fields(short[i],'USDRUBF',1))
            cmp=C.Comparison();cmp.rows([a],[S.causal_fields(scalar[i],'USDRUBF',1)],'feature',['signal_time']);self.assertFalse(cmp.diffs)
            self.assertLessEqual(a['H1AvailableAt'],at)
    def test_future_outcomes_never_in_causal_fields(self):
        row=C.build_features(self.bars)[400];f=S.causal_fields(row,'USDRUBF',1)
        self.assertFalse(set(f)&{'gross_R','MFE_R','MAE_R','bars_held','exit_time','window_recross','window_no_1ATR'})
        poisoned=dict(row,gross_R=1e9,MFE_R=1e9,MAE_R=1e9,exit_time=row['at']+C.STEP)
        self.assertEqual(f,S.causal_fields(poisoned,'USDRUBF',1))
    def test_unfinished_h1_cannot_change_signal_fields(self):
        poisoned=copy.deepcopy(self.bars);poisoned[401].update(h=1e9,l=-1e9,c=2e5)
        a=E.features(self.raw);raw=self.raw.copy();raw.iloc[401]=[100,1e9,-1e9,2e5,1];b=E.features(raw)
        at=self.bars[400]['at'];self.assertEqual(C.plain(D.feature(a.loc[at],at,'USDRUBF',1)),C.plain(D.feature(b.loc[at],at,'USDRUBF',1)))
        self.assertEqual(S.causal_fields(C.build_features(self.bars)[400],'USDRUBF',1),S.causal_fields(C.build_features(poisoned)[400],'USDRUBF',1))
    def test_window_complete_matches_both_implementations(self):
        i=400;at=self.bars[i]['at'];a=D.future_window(self.raw,at,120,2,1);b=S.market_window(self.bars,i,120,2,1)
        self.assertEqual(a,b);self.assertEqual(a['window_status'],'COMPLETE')
    def test_gap_window_censored(self):
        bars=copy.deepcopy(self.bars);bars[401]['at']+=C.STEP
        frame=self.raw.drop(self.raw.index[401]);at=self.bars[400]['at']
        self.assertEqual(D.future_window(frame,at,120,2,1)['window_status'],'CENSORED');self.assertEqual(S.market_window(bars,400,120,2,1)['window_status'],'CENSORED')
    def test_window_day_cross_and_terminal_censored(self):
        for i in (59,477):
            self.assertEqual(S.market_window(self.bars,i,120,2,1)['window_status'],'CENSORED');self.assertEqual(D.future_window(self.raw,self.bars[i]['at'],120,2,1)['window_status'],'CENSORED')
    def test_diagnostic_bin_edge_membership(self):
        b=C.build_features(self.bars)[400];row=E.features(self.raw).iloc[400];at=b['at']
        for side in (1,-1):
            for edge in D.SPEC['diagnostic_bins']['H1ADX']:
                for value in (edge-1e-9,edge,edge+1e-9):
                    r=row.copy();r['H1ADX']=value;s=copy.deepcopy(b);s['h1']['adx']=value
                    self.assertEqual(D.feature(r,at,'USDRUBF',side)['H1ADX_bin'],S.causal_fields(s,'USDRUBF',side)['H1ADX_bin'])
    def test_single_frozen_configuration_no_filter_replay(self):
        self.assertEqual(C.VERSIONS,{'TRAIL_375':3.75});self.assertEqual(D.SPEC['new_strategies'],0);self.assertEqual(D.SPEC['filter_replays'],0)
    def test_original_engines_and_parameters_preserved(self):
        for n in ('engine.py','scalar.py','primary_metrics.py','scalar_metrics.py'):
            self.assertEqual((C.HERE/n).read_bytes(),C.historical('IntradayLab/t3_m15_a6_s1_trail_plateau_v2/'+n))
        source=__import__('json').loads(C.historical('IntradayLab/t3_m15_a6_s1_trail_optimization_v1/SPEC.json'))
        self.assertEqual(D.SPEC['configuration'],source['configurations']['TRAIL_375'])

if __name__=='__main__':unittest.main(verbosity=2)
