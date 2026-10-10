"""Synthetic no-forward-information checks, not a market-data audit."""
import sys
from datetime import datetime, timedelta
from decimal import Decimal as D
from pathlib import Path
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"tools"))
from run_level_rejection_opportunities import analyze, event_signal
from m5_baseline import windows, tick

CFG={"parameters":{"level_lookback_completed_m5":6,"min_level_penetration_ticks":1,
"min_close_reentry_ticks":1,"dedup_same_instrument_same_direction_minutes":30,
"max_session_entry_slack_minutes":35,"min_initial_price_risk_ticks":4}}

def b(stamp,o,h,l,c,v=1):
    return (stamp,D(str(o)),D(str(h)),D(str(l)),D(str(c)),D(str(v)))


class LevelRejectionTests(unittest.TestCase):
    def test_six_past_no_future(self):
        t=datetime(2023,1,10,10,30)
        old=[b(t-timedelta(minutes=i*5),75,75.10,74.90,75) for i in range(6,0,-1)]
        bar=b(t,75.05,75.12,74.94,75.08)
        s,reason=event_signal("USDRUBF",bar,old,CFG["parameters"])
        self.assertEqual(reason,None)
        self.assertEqual(s["direction"],-1)
        self.assertEqual(s["level"],D("75.10"))
        self.assertEqual(s["stop"],D("75.13"))
        new=b(t+timedelta(minutes=5),50,100,10,50)
        s2,reason2=event_signal("USDRUBF",bar,old,CFG["parameters"])
        self.assertEqual(s,s2)
        self.assertIsNone(reason2)
        self.assertIsNotNone(new)

    def test_no_signal_if_close_outside(self):
        t=datetime(2023,1,10,10,30)
        old=[b(t-timedelta(minutes=i*5),75,75.10,74.90,75) for i in range(6,0,-1)]
        s,reason=event_signal("USDRUBF",b(t,75,75.12,74.95,75.11),old,CFG["parameters"])
        self.assertIsNone(s)
        self.assertEqual(reason,"NO_REJECTION")

    def test_ambiguous_both_sides(self):
        t=datetime(2023,1,10,10,30)
        old=[b(t-timedelta(minutes=i*5),75,75.10,74.90,75) for i in range(6,0,-1)]
        # One candle cannot close simultaneously below 75.09 and above 74.91?
        # Here both conditions CAN occur as the prior range is 20 ticks wide.
        s,why=event_signal("USDRUBF",b(t,75,75.12,74.88,75),old,CFG["parameters"])
        self.assertIsNone(s)
        self.assertEqual(why,"AMBIGUOUS_BOTH_SIDES")

    def test_signal_clock_and_no_future_high_low(self):
        t=datetime(2023,1,10,10)
        old=[b(t+timedelta(minutes=i*5),75,75.10,74.90,75) for i in range(6)]
        signal=b(t+timedelta(minutes=30),75.05,75.12,74.94,75.08)
        a=b(t+timedelta(minutes=50),75.07,100,5,90)
        other=b(t+timedelta(minutes=50),75.07,76,73,75)
        # Scheduled T10 target is start+20; entry OPEN invariant to its later OHLC.
        x,_,_=analyze("USDRUBF",old+[signal,a],10,CFG)
        y,_,_=analyze("USDRUBF",old+[signal,other],10,CFG)
        self.assertEqual(x,y)
        self.assertEqual(x[0]["target_at"],"2023-01-10 10:50:00")

    def test_missing_entry_stays_unknown(self):
        t=datetime(2023,1,10,10)
        old=[b(t+timedelta(minutes=i*5),75,75.10,74.90,75) for i in range(6)]
        signal=b(t+timedelta(minutes=30),75.05,75.12,74.94,75.08)
        x,_,_=analyze("USDRUBF",old+[signal],10,CFG)
        self.assertEqual(x[0]["status"],"UNKNOWN")
        self.assertEqual(x[0]["reason"],"MISSING_SCHEDULED_M5_OPEN")

    def test_cny_tick_historical(self):
        self.assertEqual(tick("CNYRUBF",datetime(2023,9,27,18,30)),D("0.01"))
        self.assertEqual(tick("CNYRUBF",datetime(2023,9,28,10,0)),D("0.001"))

    def test_no_pnl_fields_present(self):
        t=datetime(2023,1,10,10)
        rows=[b(t+timedelta(minutes=i*5),75,75.10,74.90,75) for i in range(6)]
        rows.append(b(t+timedelta(minutes=30),75.05,75.12,74.94,75.08))
        rows.append(b(t+timedelta(minutes=50),75.07,75.1,75.02,75.06))
        x,_,_=analyze("USDRUBF",rows,10,CFG)
        self.assertEqual(x[0]["status"],"ELIGIBLE_GEOMETRY")
        self.assertNotIn("net",x[0])
        self.assertNotIn("pf",x[0])
        self.assertNotIn("exit",x[0])


if __name__=="__main__":
    unittest.main()
