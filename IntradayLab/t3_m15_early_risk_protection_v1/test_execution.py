"""Synthetic execution fixtures only; no historical outcomes used."""
from datetime import datetime,timedelta
from pathlib import Path
import tempfile,unittest
import pandas as pd
import common as C,engine as E,scalar as S

def fixture(times=None,signals=None,side=1):
    times=times or ['2024-04-01 10:00','2024-04-01 10:15','2024-04-01 10:30']
    signals=signals or [side,0,0]
    out=[]
    for t,s in zip(times,signals):
        at=datetime.fromisoformat(t).replace(tzinfo=C.TZ)
        h={'at':at,'adx':25.,'slope':side*1.,'ratio':1.2,'ema':99.,'c':101.}
        out.append({'at':at,'o':100.,'h':100.5,'l':99.5,'c':100.,'v':1.,'atr':1.,'previous_atr':1.,'upper':99.,'lower':101.,'signal':s,'h1':h,'previous_h1':h|{'ratio':1.1,'at':at-timedelta(hours=1)}})
    return out

def frame(bars):
    rows=[]
    for b in bars:
        r={k:b[v] for k,v in [('Open','o'),('High','h'),('Low','l'),('Close','c'),('Volume','v'),('ATR','atr'),('PreviousATR','previous_atr'),('PriorHigh','upper'),('PriorLow','lower'),('Signal','signal')]}
        for name,key in [('ADX','adx'),('Slope','slope'),('ATRRatio','ratio'),('AvailableAt','at')]:
            r['H1'+name]=b['h1'][key];r['H1Previous'+name]=b['previous_h1'][key]
        rows.append(r)
    return pd.DataFrame(rows,index=pd.DatetimeIndex([b['at'] for b in bars]))

class Causal(unittest.TestCase):
    def runs(self,bars,rule='C1',mode='NEXT_OPEN'):
        return [E.replay(frame(bars),'USDRUBF','TRAIL_375',rule,mode),S.simulate(bars,'USDRUBF','TRAIL_375',rule,mode)]
    def test_entry_uses_next_open_and_signal_atr_both_sides(self):
        for side in (1,-1):
            b=fixture(side=side);b[1].update(o=101.,h=101.5,l=100.5,c=101.,atr=9.)
            for t,o,d,e,g,sn in self.runs(b):
                self.assertEqual(e[0]['entry_price'],101.);self.assertEqual(e[0]['candidate_initial_stop'],101.-side*2)
                self.assertEqual(d[0]['initial_risk'],2.);self.assertEqual(d[0]['bar_open_time'],b[0]['at'])
    def test_stop_on_execution_bar_before_activation_both_sides(self):
        for side in (1,-1):
            b=fixture(side=side);b[1].update(h=110.,l=90.)
            for t,o,d,e,g,sn in self.runs(b):
                self.assertEqual(len(t),1);self.assertEqual(t[0]['gross_R'],-1.)
                self.assertFalse(t[0]['threshold_activated']);self.assertEqual(t[0]['MFE_R'],0.)
                self.assertEqual(t[0]['bars_held'],1)
    def test_execution_future_extrema_cannot_change_entry(self):
        a=fixture();b=fixture();b[1].update(h=1e6,l=-1e6,c=4e5)
        for ra,rb in zip(self.runs(a),self.runs(b)):
            for field in ('entry_accepted','entry_price','candidate_initial_stop','execution_open_time'):
                self.assertEqual(ra[3][0][field],rb[3][0][field])
    def test_gaps_skip_instead_of_wait(self):
        for gap in (30,60,24*60,3*24*60):
            b=fixture();b[1]['at']=b[0]['at']+timedelta(minutes=gap);b=b[:2]
            for t,o,d,e,g,sn in self.runs(b):
                self.assertFalse(e[0]['entry_accepted']);self.assertEqual(e[0]['decision_reason'],'SKIPPED_MISSING_ADJACENT_OPEN')
                self.assertFalse(t or o or d)
    def test_pending_last_signal(self):
        for t,o,d,e,g,sn in self.runs(fixture()[:1]):
            self.assertFalse(t or o);self.assertEqual(e[0]['decision_reason'],'UNRESOLVED_END_OF_DATA')
    def test_s1_survived_execution_bar_activation_next_bar_stop(self):
        for side in (1,-1):
            b=fixture(side=side);b[1].update(h=104. if side==1 else 100.5,l=99.5 if side==1 else 96.)
            b[2].update(o=100.,h=100.5,l=99.5)
            for t,o,d,e,g,sn in self.runs(b):
                self.assertEqual(d[0]['phase'],'SURVIVED');self.assertTrue(d[0]['threshold_activated_now'])
                self.assertEqual(d[0]['active_stop_next_bar'],100.25 if side==1 else 99.75)
                self.assertTrue(d[1]['stop_hit']);self.assertTrue(t[0]['exit_at_open'])
    def test_no_s1_activation_from_signal_extreme(self):
        for side in (1,-1):
            b=fixture(side=side);b[0].update(h=1000.,l=-1000.)
            for t,o,d,e,g,sn in self.runs(b):self.assertTrue(all(not r['activated_after'] for r in d))
    def test_s1_threshold_equality_and_ratchet(self):
        b=fixture();b[1]['h']=102.;b[2].update(o=101.,l=100.,h=105.,c=104.)
        for t,o,d,e,g,sn in self.runs(b):
            self.assertTrue(d[0]['threshold_activated_now']);self.assertGreaterEqual(d[1]['active_stop_next_bar'],d[0]['active_stop_next_bar'])
    def test_a6_completed_signal_context_only(self):
        b=fixture();b[1]['h1']['ratio']=0.5
        for t,o,d,e,g,sn in self.runs(b,'C1'):self.assertTrue(e[0]['entry_accepted'])
        b[0]['h1']['ratio']=1.1
        for t,o,d,e,g,sn in self.runs(b,'C1'):self.assertFalse(e[0]['entry_accepted'])
    def test_occupied_signals_not_queued(self):
        b=fixture(signals=[1,1,1])
        for t,o,d,e,g,sn in self.runs(b):
            self.assertEqual(sum(x['entry_accepted'] for x in e),1);self.assertEqual(e[1]['decision_reason'],'POSITION_OCCUPIED')
    def test_same_close_reentry_after_execution_stop(self):
        b=fixture(signals=[1,1,0]);b[1]['l']=97.
        for t,o,d,e,g,sn in self.runs(b):
            self.assertEqual(len(t),1);self.assertTrue(e[1]['entry_accepted']);self.assertEqual(e[1]['same_close_exit_trade_id'],t[0]['trade_id'])
            self.assertEqual(o['signal_time'],b[1]['at'])
    def test_pending_across_2023_2024_adjacent(self):
        b=fixture(['2023-12-31 23:45','2024-01-01 00:00'],[1,0])
        for t,o,d,e,g,sn in self.runs(b,'C1'):self.assertTrue(e[0]['entry_accepted']);self.assertEqual(o['entry_time'],b[0]['at'])
    def test_pending_year_gap_is_skipped(self):
        b=fixture(['2023-12-29 23:45','2024-01-03 09:15'],[1,0])
        for t,o,d,e,g,sn in self.runs(b,'C1'):self.assertEqual(e[0]['decision_reason'],'SKIPPED_MISSING_ADJACENT_OPEN')
    def test_2025_replay_forbidden(self):
        b=fixture(['2024-12-31 23:45','2025-01-01 00:00'],[1,0])
        with self.assertRaises(AssertionError):E.replay(frame(b),'USDRUBF','TRAIL_375','C1','NEXT_OPEN')
        with self.assertRaises(AssertionError):S.simulate(b,'USDRUBF','TRAIL_375','C1','NEXT_OPEN')
    def test_timestamp_first_future_poison(self):
        with tempfile.TemporaryDirectory(dir='/workspace/work') as tmp:
            p=Path(tmp)/'test.csv';p.write_bytes(b'Ticker;Datetime;Open;High;Low;Close;Volume\nX;2024-12-30 10:00:00;100;101;99;100;1\nX;2025-01-01 10:00:00;FUTURE_POISON\n')
            self.assertEqual(len(E.read_source(p)),1);self.assertEqual(len(C.parse_prefix(p)[0]),1)
    def test_adverse_open_gap_later_both_sides(self):
        for side in (1,-1):
            b=fixture(side=side);b[2].update(o=97. if side==1 else 103.,h=103.,l=97.)
            for t,o,d,e,g,sn in self.runs(b):self.assertEqual(t[0]['gross_R'],-1.5);self.assertTrue(t[0]['gap_exit'])
    def test_signal_close_control_excludes_signal_extrema(self):
        b=fixture();b[0].update(h=999.,l=-999.)
        for t,o,d,e,g,sn in self.runs(b,mode='SIGNAL_CLOSE'):self.assertEqual(len(d),2);self.assertEqual(e[0]['entry_price'],100.)
    def test_feature_prefix_and_H1_causality(self):
        b=[]
        for i in range(420):
            at=datetime(2024,1,1,tzinfo=C.TZ)+i*C.STEP;price=100+i*.03
            b.append({'at':at,'o':price,'h':price+1,'l':price-1,'c':price+.2,'v':1})
        def raw(x):return pd.DataFrame([{k:r[v] for k,v in [('Open','o'),('High','h'),('Low','l'),('Close','c'),('Volume','v')]} for r in x],index=pd.DatetimeIndex([r['at'] for r in x]))
        full=E.features(raw(b));prefix=E.features(raw(b[:401]));pd.testing.assert_frame_equal(full.iloc[:401],prefix)
        a=C.build_features(b);p=C.build_features(b[:401]);self.assertEqual(C.plain(a[:401]),C.plain(p))
        for r in a:
            if r['h1']:self.assertLessEqual(r['h1']['at'],r['at'])
    def test_exit_candle_cannot_activate_s1(self):
        b=fixture();b[2].update(h=999.,l=97.)
        for t,o,d,e,g,sn in self.runs(b):self.assertFalse(t[0]['threshold_activated']);self.assertEqual(t[0]['MFE_R'],.25)

    def test_sparse_csv_blank_schema_equivalence(self):
        actual={'decision_reason':'FILTER_FAILED'};expected={'decision_reason':'FILTER_FAILED','entry_scheduled':''}
        cmp=C.Comparison();cmp.rows([{field:actual.get(field) for field in expected}],[expected],'synthetic',['decision_reason'])
        self.assertFalse(cmp.diffs)

    def test_a6_has_no_t1_hour_restriction(self):
        for hour in ('09:15','18:00','23:00'):
            a=datetime.fromisoformat('2024-04-01 '+hour)
            for t,o,d,e,g,sn in self.runs(fixture([(a+i*C.STEP).isoformat() for i in range(2)],[1,0])):
                self.assertTrue(e[0]['entry_accepted'])
    def test_each_trail_full_causal_ratchet_both_sides(self):
        for version,trail in C.VERSIONS.items():
            for side in (1,-1):
                b=fixture(side=side);b[1].update(h=104. if side==1 else 100.5,l=99.5 if side==1 else 96.)
                for result in (E.replay(frame(b),'USDRUBF',version,'C1','NEXT_OPEN'),S.simulate(b,'USDRUBF',version,'C1','NEXT_OPEN')):
                    row=result[2][0]
                    self.assertTrue(row['threshold_activated_now'])
                    self.assertAlmostEqual(row['active_stop_next_bar'],104.-trail if side==1 else 96.+trail)
    def test_metrics_year_denominator_and_loss_streak(self):
        from primary_metrics import metrics
        from scalar_metrics import stats
        rows=[{'exit_time':C.START+C.STEP,'instrument':'USDRUBF','trade_id':str(i),'gross_R':v} for i,v in enumerate((2.,-1.,-1.))]
        for fn in (metrics,stats):
            m=fn(rows,C.CALENDAR[:12]);self.assertEqual(m['months'],12);self.assertEqual(m['max_losing_trade_run'],2);self.assertEqual(m['closed_R_drawdown'],2.)

    def test_short_occupancy_and_same_close_reentry(self):
        b=fixture(signals=[-1,-1,-1],side=-1)
        for t,o,d,e,g,sn in self.runs(b):
            self.assertEqual(sum(r['entry_accepted'] for r in e),1)
            self.assertEqual(e[1]['decision_reason'],'POSITION_OCCUPIED')
        b=fixture(signals=[-1,-1,0],side=-1);b[1]['h']=103.
        for t,o,d,e,g,sn in self.runs(b):
            self.assertEqual(len(t),1);self.assertTrue(e[1]['entry_accepted'])
            self.assertEqual(o['signal_time'],b[1]['at'])


    def test_a6_strict_equality_rejects_both_sides(self):
        for side in (1,-1):
            b=fixture(side=side);b[0]['previous_h1']['ratio']=1.2
            for t,o,d,e,g,sn in self.runs(b):self.assertFalse(e[0]['entry_accepted'])

    def test_gapped_h1_block_skipped_not_repacked(self):
        bars=[]
        for i in range(12):
            at=datetime(2024,4,1,10,tzinfo=C.TZ)+i*C.STEP
            if i>=2:at+=C.STEP
            bars.append({'at':at,'o':100.,'h':101.,'l':99.,'c':100.,'v':1.})
        built=C.build_features(bars)
        self.assertTrue(all(r['h1'] is None for r in built[:7]))
        self.assertEqual(built[7]['h1']['at'],bars[7]['at'])
        raw=pd.DataFrame([{'Open':b['o'],'High':b['h'],'Low':b['l'],'Close':b['c'],'Volume':b['v']} for b in bars],index=pd.DatetimeIndex([b['at'] for b in bars]))
        primary=E.features(raw)
        self.assertTrue(primary.H1AvailableAt.iloc[:7].isna().all())
        self.assertEqual(primary.H1AvailableAt.iloc[7],bars[7]['at'])

if __name__=='__main__':unittest.main(verbosity=2)
