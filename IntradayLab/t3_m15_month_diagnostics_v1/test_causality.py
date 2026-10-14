"""Targeted causal diagnostic checks; historical 40 replay fixtures run separately."""
import sys,unittest,tempfile
from pathlib import Path
import numpy as np,pandas as pd
import diagnose as D

class DiagnosticCausality(unittest.TestCase):
    def test_all_entry_and_market_features_prefix_invariant(self):
        # Includes incomplete H1 blocks, a missing M15 and calendar boundaries.
        idx=pd.date_range('2023-02-01 09:15',periods=1100,freq='15min',tz='Europe/Moscow').delete([53,54,109,192,333])
        x=np.arange(len(idx));c=100+.01*x+np.sin(x/7)
        raw=pd.DataFrame({'Open':c-.05,'High':c+.2,'Low':c-.25,'Close':c,'Volume':100.},index=idx)
        whole=D.extended(raw)
        for n in [300,301,302,303,304,510,701,1090]:
            prefix=D.extended(raw.iloc[:n]);pd.testing.assert_frame_equal(prefix,whole.iloc[:n],check_exact=True,check_freq=False)
    def test_future_numeric_suffix_never_read(self):
        work=D.HERE/'work';work.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=work) as folder:
            p=Path(folder)/'poison.csv';p.write_text('Ticker;Datetime;Open;High;Low;Close;Volume\nX;2024-12-30 10:00:00;1;2;1;2;0\nX;2025-01-01 10:00:00;DO_NOT_PARSE_OR_READ_OHLC')
            self.assertEqual(len(D.E.read_source(p)),1)
            self.assertEqual(len(D.C.parse_prefix(p)[0]),1)
    def test_breakout_forward_window_gap_is_censored(self):
        ix=pd.DatetimeIndex(['2024-04-01 10:00','2024-04-01 10:15','2024-04-01 10:45','2024-04-01 11:00','2024-04-01 11:15'],tz='Europe/Moscow')
        f=pd.DataFrame({'raw_breakout':[1,0,0,0,0],'ready':True,'PriorHigh':1.,'PriorLow':0.,'Close':1.1,'High':1.2,'Low':1.,'ATR':.1,'year':2024,'month':'2024-04','Signal':1,'core':True,'matched':False},index=ix)
        r=D.breakout_events(f,'X')[0];self.assertFalse(r['window_complete']);self.assertIsNone(r['no_continuation'])

if __name__=='__main__':unittest.main(verbosity=2)
