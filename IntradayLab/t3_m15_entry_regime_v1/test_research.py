"""Hand-calculated event-order and causal-feature tests for new mechanisms."""
import tempfile
from pathlib import Path
import unittest

import numpy as np
import pandas as pd

from engine import E, execute, features, permits
from research import metrics


def bars(values, sign=1):
    f = pd.DataFrame(values,columns=['Open','High','Low','Close','ATR','Signal'],
        index=pd.date_range('2023-01-03 10:00',periods=len(values),freq='15min',tz=E.TZ))
    f['PriorHigh'], f['PriorLow'] = 100., 100.
    for c in ('PreviousATR','H1ADX','H1PreviousADX','H1Slope','H1PreviousSlope','H1ATRRatio','H1PreviousATRRatio'):
        f[c] = 1.
    f['H1AvailableAt'], f['H1PreviousAvailableAt'] = f.index,f.index-pd.Timedelta(hours=1)
    return f


def synthetic(n=1000):
    at = pd.date_range('2023-01-03 09:15',periods=n,freq='15min',tz=E.TZ)
    price = 100+np.arange(n)*.01+np.sin(np.arange(n)/7)
    return pd.DataFrame({'Open':price,'High':price+.2,'Low':price-.2,'Close':price+.05,'Volume':10.},index=at)


class Events(unittest.TestCase):
    def replay(self, values, rule='A1', sign=1):
        return execute(bars(values,sign),'USDRUBF','BASELINE',E.CONFIGS['BASELINE'],rule)

    def test_one_bar_next_open_and_stop_priority(self):
        t,o,d,_ = self.replay([[101,101,101,101,2,1],[101,102,99,100,2,0],[99,106,98,105,2,0]])
        self.assertIsNone(o)
        self.assertEqual(t[0]['exit_price'],99)
        self.assertEqual(t[0]['exit_time'],pd.Timestamp('2023-01-03 10:15',tz=E.TZ))
        self.assertEqual(t[0]['gross_R'],-.5)
        self.assertEqual(t[0]['exit_type'],'A1_NEXT_OPEN')
        self.assertEqual(d[0]['decision_time'],t[0]['rule_decision_time'])
        t,_,_,_ = self.replay([[101,101,101,101,2,1],[101,102,99,100,2,0],[96,110,95,105,2,0]])
        self.assertEqual(t[0]['exit_price'],96)
        self.assertEqual(t[0]['exit_type'],'INITIAL_STOP')
        self.assertTrue(t[0]['rule_stop_conflict_at_open'])

    def test_no_future_intrabar_priority_over_pending_open(self):
        t,_,_,_ = self.replay([[101,101,101,101,2,1],[101,102,99,100,2,0],[100,102,90,101,2,0]])
        self.assertEqual(t[0]['exit_price'],100)  # exited before the later Low 90
        self.assertEqual(t[0]['exit_type'],'A1_NEXT_OPEN')

    def test_protective_exit_prevents_close_decision(self):
        t,_,d,_ = self.replay([[101,101,101,101,1,1],[101,103,98,99,1,0]])
        self.assertEqual(t[0]['exit_price'],99)
        self.assertEqual(d,[])

    def test_one_bar_never_checks_later_return(self):
        _,o,d,_ = self.replay([[101,101,101,101,2,1],[101,102,101,102,2,0],[102,102,99,100,2,0],[100,102,99,101,2,0]])
        self.assertIsNotNone(o)
        self.assertEqual(len(d),1)
        self.assertFalse(d[0]['exit_queued'])

    def test_two_bar_reset_and_trigger_on_fourth(self):
        values = [[101,101,101,101,2,1],[101,102,99,100,2,0],[100,102,99,101,2,0],
            [101,102,99,100,2,0],[100,102,99,100,2,0],[99,101,98,100,2,0]]
        t,o,d,_ = self.replay(values,'A2')
        self.assertIsNone(o)
        self.assertEqual([r['consecutive_wrong'] for r in d],[1,0,1,2])
        self.assertEqual(t[0]['exit_price'],99)
        self.assertEqual(t[0]['exit_type'],'A2_NEXT_OPEN')

    def test_two_bar_disabled_after_fourth(self):
        values = [[101,101,101,101,2,1]]+[[101,102,100,101,2,0]]*3+[[101,102,99,100,2,0]]*3
        t,o,d,_ = self.replay(values,'A2')
        self.assertEqual(t,[])
        self.assertIsNotNone(o)
        self.assertEqual(len(d),4)
        self.assertFalse(any(r['exit_queued'] for r in d))

    def test_short_mirror(self):
        t,_,_,_ = self.replay([[99,99,99,99,2,-1],[99,101,98,100,2,0],[101,102,98,99,2,0]],sign=-1)
        self.assertEqual(t[0]['exit_price'],101)
        self.assertEqual(t[0]['gross_R'],-.5)

    def test_terminal_pending_and_missing_next_open(self):
        t,o,_,_ = self.replay([[101,101,101,101,2,1],[101,102,99,100,2,0]])
        self.assertEqual(t,[])
        self.assertIsNotNone(o['pending_exit_decision'])
        f = bars([[101,101,101,101,2,1],[101,102,99,100,2,0],[98,101,97,100,2,0]])
        f.index = pd.DatetimeIndex([f.index[0],f.index[1],f.index[2]+pd.Timedelta(days=3)])
        t,_,_,_ = execute(f,'USDRUBF','BASELINE',E.CONFIGS['BASELINE'],'A1')
        self.assertEqual(t[0]['exit_price'],98)
        self.assertEqual(t[0]['exit_time'],f.index[2]-pd.Timedelta(minutes=15))

    def test_same_close_reentry_is_recalculated(self):
        t,o,_,signals = self.replay([[101,101,101,101,2,1],[101,102,99,100,2,0],[99,103,98,102,2,1]])
        self.assertEqual(len(t),1)
        self.assertEqual(o['entry_price'],102)
        self.assertEqual(o['entry_time'],'2023-01-03T10:30:00+03:00')
        self.assertTrue(signals[-1]['entry_accepted'])

    def test_stop_before_ratchet_and_next_bar_activation(self):
        t,_,_,_ = self.replay([[101,101,101,101,1,1],[101,110,100,109,1,0],[108,110,106,107,1,0]],'CONTROL')
        self.assertEqual(t[0]['exit_price'],107)
        self.assertEqual(t[0]['active_stop_at_exit'],107)
        self.assertEqual(t[0]['MFE_R'],4.5)


class Causality(unittest.TestCase):
    def test_features_prefix_and_future_mutation(self):
        full = synthetic()
        a,ah = features(full.iloc[:701],E.CONFIGS['BASELINE'])
        b,bh = features(full,E.CONFIGS['BASELINE'])
        pd.testing.assert_frame_equal(a,b.loc[a.index])
        pd.testing.assert_frame_equal(ah,bh.loc[ah.index])
        full.iloc[701:, :4] *= 9
        c,_ = features(full,E.CONFIGS['BASELINE'])
        pd.testing.assert_frame_equal(a,c.loc[a.index])
        valid = b.H1AvailableAt.notna()
        self.assertTrue((b.loc[valid,'H1AvailableAt'] <= b.index[valid]).all())
        valid_previous = b.H1PreviousAvailableAt.notna()
        self.assertTrue((b.loc[valid_previous,'H1PreviousAvailableAt'] < b.loc[valid_previous,'H1AvailableAt']).all())

    def test_previous_h1_is_not_previous_m15_forward_fill(self):
        low,high = features(synthetic(),E.CONFIGS['BASELINE'])
        at = high.index[100]
        self.assertEqual(low.loc[at,'H1PreviousADX'],high.ADX.iloc[99])
        self.assertEqual(low.loc[at+pd.Timedelta(minutes=15),'H1PreviousADX'],high.ADX.iloc[99])

    def test_donchian_excludes_signal_bar_and_incomplete_blocks(self):
        f = synthetic(100)
        f.iloc[30,f.columns.get_loc('High')] = 9999
        low,_ = features(f,E.CONFIGS['BASELINE'])
        self.assertEqual(low.PriorHigh.iloc[30],f.High.iloc[10:30].max())
        self.assertEqual(len(E.context(f.iloc[:3])),0)
        g = f.iloc[:9].drop(f.index[1])
        self.assertEqual(list(E.context(g).index),[g.index[7]])

    def test_future_ohlc_boundary(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent/'work') as folder:
            p = Path(folder)/'source.csv'
            p.write_text('Ticker;Datetime;Open;High;Low;Close;Volume\nX;2024-12-30 23:45:00;1;2;1;2;10\nX;2025-01-01 00:00:00;MUST_NOT_PARSE\n')
            f,_ = E.read_prefix(p)
            self.assertEqual(len(f),1)

    def test_filter_equality_and_direction(self):
        f = bars([[100,102,98,102,1,1]])
        b = next(f.itertuples())
        self.assertTrue(permits(b,'A3')) # exact half body
        self.assertFalse(permits(b,'A4'))
        self.assertFalse(permits(b,'A5'))
        self.assertFalse(permits(b,'A6'))
        self.assertFalse(permits(b,'A7'))
        f.loc[f.index[0],'Open'] = 103
        self.assertFalse(permits(next(f.itertuples()),'A3'))

    def test_hand_calculated_gross_metrics(self):
        f = pd.DataFrame({'exit_time':pd.date_range('2023-01-01',periods=8,tz=E.TZ),
            'instrument':'X','trade_id':list(map(str,range(8))),'gross_R':[3,-2,-2,1,4,-1,-1,2]})
        m = metrics(f,['2023-01','2023-02'])
        self.assertEqual(m['gross_R'],4)
        self.assertEqual(m['gross_PF'],10/6)
        self.assertEqual(m['max_drawdown_R'],4)
        self.assertEqual(m['positive_months'],1)
        self.assertEqual(m['zero_months'],1)
        self.assertEqual(m['gross_R_without_top5'],-6)


if __name__ == '__main__':unittest.main()
