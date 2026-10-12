"""Hand-calculated execution chronology, censoring and causality checks."""
import unittest
from types import SimpleNamespace
import pandas as pd
import diagnose as D

class DiagnosticsTests(unittest.TestCase):
    def fixture(self, after, fill, mfe, mae, updates, stop, gap=False):
        at=pd.Timestamp('2023-01-02 23:45',tz=D.E.TZ)
        low=pd.DataFrame([[100,101,99,100,1,1,99,98,1]]+after,
            columns=['Open','High','Low','Close','ATR','Signal','PriorHigh','PriorLow','Regime'],
            index=pd.date_range(at,periods=1+len(after),freq='15min'))
        high=pd.DataFrame([[100,99,1,25,2,1]],columns=['Close','EMA','Slope','ADX','ATR','ATRMean'],index=[at])
        t={'version':'BASELINE','instrument':'USDRUBF','trade_id':'HAND','direction':'LONG',
            'entry_time':at,'exit_time':low.index[-1],'entry_price':100.,'initial_stop':98.,'initial_risk':2.,
            'exit_price':fill,'gross_R':(fill-100)/2,'C1_R':.001,'net_R':(fill-100)/2-.001,
            'MFE_R':mfe,'MAE_R':mae,'active_stop_at_exit':stop,'trailing_updates':updates,
            'holding_minutes':len(after)*15,'bars_held':len(after),'gap_exit':gap}
        return t,low,high

    def test_stop_first_and_unknown_exit_wick(self):
        t,l,h=self.fixture([[100,104,99,103,1,0,99,98,1],[103,110,100,102,1,0,99,98,1]],101,2,.5,1,101)
        i,p,c=D.path_for_trade(t,l,h,D.E.Parameters())
        self.assertEqual(i['observed_MFE_lower_R'],2)
        self.assertEqual(i['possible_MFE_upper_R'],5)
        self.assertEqual(p[1]['stop_after'],101)
        self.assertEqual(p[2]['event'],'EXIT')
        self.assertFalse(c[1]['completed_before_exit'])
        self.assertTrue(c[1]['exit_on_horizon_bar'])
        self.assertEqual(i['calendar_midnights'],1)
        self.assertEqual(i['carry'],'CROSS_MIDNIGHT')

    def test_gap_does_not_admit_later_wick(self):
        t,l,h=self.fixture([[97,110,96,105,1,0,99,98,1]],97,0,1.5,0,98,True)
        i,p,c=D.path_for_trade(t,l,h,D.E.Parameters())
        self.assertEqual(i['possible_MFE_upper_R'],0)
        self.assertTrue(i['no_favorable_confirmed'])
        self.assertEqual(c[0]['bar_favorable_R'],5)
        self.assertFalse(c[0]['completed_before_exit'])

    def test_open_exactly_on_stop_excludes_later_wick(self):
        t,l,h=self.fixture([[98,110,97,105,1,0,99,98,1]],98,0,1,0,98)
        i,p,c=D.path_for_trade(t,l,h,D.E.Parameters())
        self.assertEqual(i['possible_MFE_upper_R'],0)
        self.assertTrue(i['exit_at_open'])
        self.assertFalse(p[-1]['gap_exit'])

    def test_atr_contraction_tightens_without_new_high(self):
        t,l,h=self.fixture([[100,102,99,101,1,0,99,98,1],[101,102,100,101,.5,0,99,98,1],[101,102,100,101,.5,0,99,98,1]],100.5,1,.5,2,100.5)
        i,p,c=D.path_for_trade(t,l,h,D.E.Parameters())
        self.assertTrue(p[2]['tightened_without_new_extreme'])
        self.assertEqual(i['first_positive_stop_bar'],2)

    def test_future_does_not_change_preentry_features(self):
        idx=pd.date_range('2023-01-01',periods=500,freq='15min',tz=D.E.TZ)
        x=pd.Series(range(500),index=idx)*.1+100
        f=pd.DataFrame({'Open':x,'High':x+1,'Low':x-1,'Close':x+.2,'Volume':1})
        a,ha=D.E.indicators(f,D.E.Parameters())
        altered=f.copy();altered.iloc[450:,:4]*=10
        b,hb=D.E.indicators(altered,D.E.Parameters())
        pd.testing.assert_frame_equal(a.iloc[:450],b.iloc[:450])
        pd.testing.assert_frame_equal(ha.loc[:idx[449]],hb.loc[:idx[449]])

    def test_short_mirrors_long(self):
        t,l,h=self.fixture([[100,104,99,103,1,0,99,98,1],[103,110,100,102,1,0,99,98,1]],101,2,.5,1,101)
        long,_,_=D.path_for_trade(t,l,h,D.E.Parameters())
        short=l.copy()
        short['Open']=200-l.Open;short['Close']=200-l.Close
        short['High']=200-l.Low;short['Low']=200-l.High
        short['PriorLow']=200-l.PriorHigh;short['Signal']=-l.Signal;short['Regime']=-1
        hs=h.copy();hs['EMA']=200-h.EMA;hs['Close']=200-h.Close;hs['Slope']=-h.Slope
        ts=t|{'direction':'SHORT','initial_stop':102.,'exit_price':99.,'active_stop_at_exit':99.}
        mirrored,_,_=D.path_for_trade(ts,short,hs,D.E.Parameters())
        for col in ['recorded_MFE_R','observed_MFE_lower_R','possible_MFE_upper_R','exit_stop_R','giveback_recorded_R']:
            self.assertEqual(long[col],mirrored[col])

if __name__=='__main__':unittest.main()
