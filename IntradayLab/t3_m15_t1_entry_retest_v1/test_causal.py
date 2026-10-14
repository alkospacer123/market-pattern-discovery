"""Targeted causality and event-order counterexamples, no new strategies."""
import unittest
from datetime import datetime,timedelta
from zoneinfo import ZoneInfo
import pandas as pd
from primary import replay,features
from verify import simulate,feature_stream
from io_utils import clean

T=datetime(2024,1,10,10,tzinfo=ZoneInfo('Europe/Moscow'));D=timedelta(minutes=15)
def bar(i,signal=0,**kw):
    b=dict(at=T+i*D,Open=100.,High=100.5,Low=99.5,Close=100.,Volume=1.,ATR=1.,PriorHigh=99.,PriorLow=101.,H1AvailableAt=T,Signal=signal);b.update(kw);return b

class Causal(unittest.TestCase):
    def both(self,bars,mode):
        a=replay(bars,'USDRUBF',mode);b=simulate(bars,'USDRUBF',mode)
        self.assertEqual(a,b);return a
    def test_signal_extremes_excluded(self):
        d=self.both([bar(0,1,High=1000.,Low=1.),bar(1)],'SIGNAL_CLOSE')
        self.assertEqual(len(d['trades']),0);self.assertEqual(len(d['stops']),1);self.assertEqual(d['stops'][0]['extreme_before'],100.)
    def test_signal_final_bar_no_stop(self):
        d=self.both([bar(0,1,High=1000.,Low=1.)],'SIGNAL_CLOSE');self.assertEqual(len(d['OPEN']),1);self.assertFalse(d['stops'])
    def test_execution_initial_stop_active(self):
        d=self.both([bar(0,1),bar(1,Low=97.)],'NEXT_OPEN');self.assertEqual(d['trades'][0]['gross_R'],-1.)
    def test_execution_hlc_not_entry_inputs(self):
        a=self.both([bar(0,1),bar(1,Open=101.)],'NEXT_OPEN')
        b=self.both([bar(0,1),bar(1,Open=101.,High=1000.,Low=1.,Close=900.)],'NEXT_OPEN')
        for field in ('entry_price','initial_stop','entry_accepted','signal_time'):
            self.assertEqual(a['signals'][0][field],b['signals'][0][field])
    def test_adjacent_open_no_extra_15min(self):
        d=self.both([bar(0,1),bar(1,Open=101.)],'NEXT_OPEN');self.assertEqual(d['OPEN'][0]['entry_time'],T);self.assertEqual(d['OPEN'][0]['entry_price'],101.)
    def test_gap_cancels_no_future_open(self):
        d=self.both([bar(0,1),bar(2),bar(3)],'NEXT_OPEN');self.assertFalse(d['OPEN']);self.assertEqual(d['signals'][0]['reason'],'MISSING_ADJACENT_OPEN')
    def test_final_signal_unresolved(self):
        d=self.both([bar(0,1)],'NEXT_OPEN');self.assertEqual(d['signals'][0]['reason'],'UNRESOLVED_END_OF_DATA');self.assertFalse(d['OPEN'])
    def test_cancelled_pending_journal_id_reused(self):
        d=self.both([bar(0,1),bar(2,1),bar(3)],'NEXT_OPEN');self.assertEqual(d['signals'][0]['trade_id'],d['signals'][1]['trade_id'])
    def test_next_open_stop_uses_signal_atr(self):
        d=self.both([bar(0,1,ATR=2.),bar(1,Open=110.,High=111.,Low=109.,ATR=30.)],'NEXT_OPEN');self.assertEqual(d['OPEN'][0]['initial_stop'],106.)
    def test_trailing_no_retroactive_touch(self):
        d=self.both([bar(0,1),bar(1,High=120.,Low=99.),bar(2,Open=117.,High=118.,Low=110.)],'SIGNAL_CLOSE')
        self.assertFalse(d['stops'][0]['stop_hit']);self.assertEqual(d['stops'][0]['next_stop'],116.5);self.assertEqual(d['trades'][0]['exit_time'],T+2*D)
    def test_stop_first_no_exit_favorable_extreme(self):
        d=self.both([bar(0,1),bar(1,High=1000.,Low=97.)],'SIGNAL_CLOSE');self.assertEqual(d['trades'][0]['gross_R'],-1.);self.assertEqual(d['trades'][0]['MFE_R'],0.)
    def test_no_plus_one_R_delay(self):
        d=self.both([bar(0,1),bar(1,High=100.5,ATR=.1)],'SIGNAL_CLOSE');self.assertGreater(d['OPEN'][0]['active_stop'],100.)
    def test_adverse_gap_fill_open(self):
        d=self.both([bar(0,1),bar(4,Open=95.,High=96.,Low=94.)],'SIGNAL_CLOSE');self.assertEqual(d['trades'][0]['exit_price'],95.);self.assertEqual(d['trades'][0]['gross_R'],-2.5)
    def test_busy_signals_no_pyramiding(self):
        for mode in ('SIGNAL_CLOSE','NEXT_OPEN'):
            d=self.both([bar(0,1),bar(1,1),bar(2,-1)],mode);self.assertEqual(len(d['OPEN']),1);self.assertEqual(sum(x['entry_accepted'] for x in d['signals']),1)
    def test_same_close_reentry(self):
        d=self.both([bar(0,1),bar(1,-1,Low=97.)],'SIGNAL_CLOSE');self.assertEqual(len(d['trades']),1);self.assertEqual(len(d['OPEN']),1);self.assertIsNotNone(d['signals'][1]['same_close_exit_trade_id'])
    def test_T1_boundaries(self):
        for hour,minute,accept in [(9,45,False),(10,0,True),(17,45,True),(18,0,False)]:
            at=T.replace(hour=hour,minute=minute);d=self.both([bar(0,1,at=at,H1AvailableAt=at)],'SIGNAL_CLOSE');self.assertEqual(bool(d['OPEN']),accept)
    def test_no_forced_18_close(self):
        d=self.both([bar(0,1,at=T.replace(hour=17,minute=45)),bar(1,at=T.replace(hour=18)),bar(2,at=T.replace(hour=18,minute=15))],'SIGNAL_CLOSE');self.assertEqual(len(d['OPEN']),1)
    def test_short_symmetry(self):
        d=self.both([bar(0,-1),bar(1,High=103.)],'SIGNAL_CLOSE');self.assertEqual(d['trades'][0]['gross_R'],-1.);self.assertEqual(d['trades'][0]['initial_stop'],102.)
    def test_cross_year_no_reset(self):
        start=T.replace(year=2024,month=12,day=31,hour=17,minute=45)
        d=self.both([bar(0,1,at=start),bar(1,at=start+timedelta(days=1))],'SIGNAL_CLOSE');self.assertEqual(len(d['OPEN']),1);self.assertEqual(d['snapshots'][0]['month'],'2024-12')
    def test_all_symbols_identical_logic(self):
        bs=[bar(0,1),bar(1,High=120.),bar(2,Low=97.)]
        for mode in ('SIGNAL_CLOSE','NEXT_OPEN'):
            for s in ('USDRUBF','CNYRUBF','GLDRUBF','IMOEXF'):
                d=replay(bs,s,mode);self.assertEqual(d['trades'][0]['gross_R'],simulate(bs,s,mode)['trades'][0]['gross_R'])
    def test_features_prefix_and_future_mutation(self):
        ix=pd.date_range(T,periods=500,freq='15min');values=[100.+i*.01 for i in range(500)]
        f=pd.DataFrame(dict(Open=values,High=[x+1 for x in values],Low=[x-1 for x in values],Close=values,Volume=1.),index=ix)
        full=features(f);prefix=features(f.iloc[:401])
        self.assertEqual(clean(full[:401]),clean(prefix))
        changed=f.copy();changed.iloc[401:,changed.columns.get_loc('High')]=1e6
        self.assertEqual(clean(features(changed)[:401]),clean(prefix))
        for row in full:self.assertTrue(row['H1AvailableAt'] is None or row['H1AvailableAt']<=row['at'])
    def test_donchian_excludes_current(self):
        ix=pd.date_range(T,periods=25,freq='15min');f=pd.DataFrame(dict(Open=100.,High=101.,Low=99.,Close=100.,Volume=1.),index=ix)
        f.iloc[-1,f.columns.get_loc('High')]=1000.;f.iloc[-1,f.columns.get_loc('Low')]=1.
        d=features(f)[-1];self.assertEqual(d['PriorHigh'],101.);self.assertEqual(d['PriorLow'],99.)
    def test_h1_gap_not_repacked(self):
        raw=[bar(i) for i in (0,1,3,4,5,6,7,8)]
        for b in raw:b.pop('ATR');b.pop('Signal')
        d=list(feature_stream(raw));self.assertIsNone(d[3]['H1AvailableAt']);self.assertEqual(d[-1]['H1AvailableAt'],raw[-1]['at'])
    def test_partial_h1_not_published(self):
        raw=[bar(i) for i in (0,1,2)]
        d=list(feature_stream(raw));self.assertTrue(all(x['H1AvailableAt'] is None for x in d))

if __name__=='__main__':unittest.main()
