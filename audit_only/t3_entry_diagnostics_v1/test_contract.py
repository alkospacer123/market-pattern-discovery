"""Meaningful synthetic boundary/arithmetic/cluster checks, no strategy variants."""
import math,unittest
from datetime import datetime,timedelta
from zoneinfo import ZoneInfo
from verify import indicators,EWM
from analysis_tables import ratio_ci,difference,monthly,weights
import numpy as np

class Contract(unittest.TestCase):
    def test_context_ewm_warmup(self):
        x=EWM(2/76,75);values=[x.update(float(i)) for i in range(75)]
        self.assertTrue(all(math.isnan(v) for v in values[:74]));self.assertTrue(math.isfinite(values[74]))
    def test_wilder_atr_first_true_range_and_gap(self):
        tz=ZoneInfo('Europe/Moscow');bars=[]
        for i in range(15):
            close=10 if i<14 else 15
            bars.append(dict(at=datetime(2024,1,1,tzinfo=tz)+timedelta(hours=i),Open=close,High=close+1,Low=close-1,Close=close))
        out=indicators(bars,100)
        self.assertTrue(math.isnan(out[12]['ATR']));self.assertEqual(out[13]['ATR'],2)
        self.assertAlmostEqual(out[14]['ATR'],2*13/14+6/14)
    def test_ema_slope_uses_published_values(self):
        tz=ZoneInfo('Europe/Moscow')
        bars=[dict(at=datetime(2024,1,1,tzinfo=tz)+timedelta(hours=i),Open=i+10,High=i+11,Low=i+9,Close=i+10) for i in range(110)]
        out=indicators(bars,100)
        self.assertTrue(math.isnan(out[103]['Slope']));self.assertAlmostEqual(out[104]['Slope'],out[104]['EMA']-out[99]['EMA'])
    def test_locked_year_midnight_msk(self):
        at=datetime.fromisoformat('2024-12-31T21:00:00+00:00').astimezone(ZoneInfo('Europe/Moscow'))
        self.assertEqual((at.year,at.month,at.day,at.hour),(2025,1,1,0))
    def test_signal_calendar_vs_open_label(self):
        close=datetime.fromisoformat('2024-01-02T00:00:00+03:00');opening=close-timedelta(hours=1)
        self.assertNotEqual(close.date(),opening.date())
    def test_cluster_resampling_is_paired(self):
        n=np.arange(1,25,dtype=float);x=n*.25
        self.assertTrue(np.allclose(ratio_ci(x,n),.25));self.assertTrue(np.allclose(ratio_ci(x,n,True),.25))
    def test_empty_bootstrap_is_missing(self):
        self.assertTrue(np.isnan(ratio_ci(np.zeros(24),np.zeros(24))).all())
    def test_seed_and_cluster_size(self):
        w=weights(24);self.assertTrue(np.array_equal(w,weights(24)));self.assertTrue(np.all(w.sum(axis=1)==24))
if __name__=='__main__':unittest.main()
