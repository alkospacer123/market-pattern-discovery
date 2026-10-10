"""Synthetic no-forward-information checks, not a market-data audit."""
import sys
from datetime import datetime, timedelta
from decimal import Decimal as D
from pathlib import Path
import unittest
import hashlib
import tempfile
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"tools"))
from run_level_rejection_opportunities import analyze, event_signal, load_bars, run
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
        x,_,_=analyze("USDRUBF",old+[signal,b(t+timedelta(minutes=35),75,75.1,74.9,75),a],10,CFG)
        y,_,_=analyze("USDRUBF",old+[signal,b(t+timedelta(minutes=35),75,75.1,74.9,75),other],10,CFG)
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
        rows.append(b(t+timedelta(minutes=35),75,75.1,74.9,75))
        rows.append(b(t+timedelta(minutes=50),75.07,75.1,75.02,75.06))
        x,_,_=analyze("USDRUBF",rows,10,CFG)
        self.assertEqual(x[0]["status"],"ELIGIBLE_GEOMETRY")
        self.assertNotIn("net",x[0])
        self.assertNotIn("pf",x[0])
        self.assertNotIn("exit",x[0])


    def fixture(self, entry=75.07, start=datetime(2023,1,10,10), long=False):
        rows=[b(start+timedelta(minutes=i*5),75,75.10,74.90,75) for i in range(6)]
        at=start+timedelta(minutes=30)
        rows.append(b(at,75,75.06,74.88,74.92) if long else b(at,75,75.12,74.94,75.08))
        rows.extend(b(at+timedelta(minutes=i*5),75,75.1,74.9,75) for i in (1,2,3))
        rows.append(b(at+timedelta(minutes=20),entry,76,74,entry))
        rows.append(b(at+timedelta(minutes=25),entry,76,74,entry))
        return rows

    def test_exact_t10_t15_and_both_ratios(self):
        for delay, minute in ((10,50),(15,55)):
            x,_,_=analyze("USDRUBF",self.fixture(),delay,CFG)
            e=x[0]
            self.assertEqual(e["target_at"],f"2023-01-10 10:{minute}:00")
            self.assertEqual(e["status"],"ELIGIBLE_GEOMETRY")
            self.assertEqual(D(e["legacy_net_reward_to_gross_risk"]),3)
            self.assertEqual(D(e["full_net_reward_to_net_stop_loss"]),3)
            s=D(e["risk"]); t=D(e["tick"])
            self.assertLess((D(e["entry_open"])-D(e["legacy_take"])-2*t)/(s+2*t),3)

    def test_long_stop_and_full_net_target(self):
        e=analyze("USDRUBF",self.fixture(entry=74.93,long=True),10,CFG)[0][0]
        self.assertEqual(e["status"],"ELIGIBLE_GEOMETRY")
        self.assertEqual(D(e["stop"]),D("74.87"))
        self.assertGreater(D(e["full_net_take"]),D(e["entry_open"]))

    def test_four_ticks_inclusive(self):
        e=analyze("USDRUBF",self.fixture(entry=75.09),10,CFG)[0][0]
        self.assertEqual(e["status"],"ELIGIBLE_GEOMETRY")
        self.assertEqual(D(e["risk"]),D("0.04"))

    def test_three_ticks_rejected_after_reclaim(self):
        rows=self.fixture(entry=75.09)
        rows[6]=b(rows[6][0],75,75.11,74.94,75.09)
        self.assertEqual(analyze("USDRUBF",rows,10,CFG)[0][0]["reason"],"RISK_BELOW_FOUR_TICKS")

    def test_directional_dedup_thirty_minutes_inclusive(self):
        t=datetime(2023,1,10,10)
        rows=[b(t+timedelta(minutes=i*5),75,75.1,74.9,75) for i in range(18)]
        for i,h,c in ((6,75.12,75.08),(8,75.14,75.10),(12,75.16,75.12)):
            rows[i]=b(rows[i][0],75,h,74.94,c)
        events,counts,_=analyze("USDRUBF",rows,10,CFG)
        self.assertEqual(counts["raw_rejections"],3)
        self.assertEqual(counts["DEDUP_30MIN"],1)
        self.assertEqual([e["signal_at"] for e in events],["2023-01-10 10:30:00","2023-01-10 11:00:00"])

    def test_nonfill_reclaim(self):
        e=analyze("USDRUBF",self.fixture(entry=75.10),10,CFG)[0][0]
        self.assertEqual(e["reason"],"OPEN_RECLAIM_NOT_PERSISTENT")

    def test_observable_gap_cancels_pending(self):
        rows=self.fixture()
        del rows[7]  # Test+5 candle's delivery deadline equals target Open.
        e=analyze("USDRUBF",rows,10,CFG)[0][0]
        self.assertEqual(e["reason"],"OBSERVABLE_GAP_RESET_BEFORE_ENTRY")

    def test_not_yet_observable_gap_keeps_pending(self):
        rows=self.fixture()
        del rows[8]  # Test+10 absence is not observable at target Open.
        e=analyze("USDRUBF",rows,10,CFG)[0][0]
        self.assertEqual(e["status"],"ELIGIBLE_GEOMETRY")

    def test_zero_volume_target_unknown(self):
        rows=self.fixture(); old=rows[10]; rows[10]=old[:-1]+(D(0),)
        e=analyze("USDRUBF",rows,10,CFG)[0][0]
        self.assertEqual(e["status"],"UNKNOWN")
        self.assertEqual(e["reason"],"ZERO_VOLUME_SCHEDULED_M5")

    def test_missing_target_unknown_despite_intermediate_gap(self):
        rows=self.fixture(); rows.pop(10); rows.pop(7)
        self.assertEqual(analyze("USDRUBF",rows,10,CFG)[0][0]["status"],"UNKNOWN")

    def test_session_cutoff_inclusive(self):
        # 13:05 test -> 13:25 entry +35 =14:00 accepted; next slot rejected.
        self.assertEqual(analyze("USDRUBF",self.fixture(start=datetime(2023,1,10,12,35)),10,CFG)[0][0]["status"],"ELIGIBLE_GEOMETRY")
        self.assertEqual(analyze("USDRUBF",self.fixture(start=datetime(2023,1,10,12,40)),10,CFG)[0][0]["reason"],"SESSION_ENTRY_CUTOFF")

    def test_lunch_day_gap_zero_reset_six_bars(self):
        base=self.fixture()[:6]
        for at in (datetime(2023,1,10,14,5),datetime(2023,1,11,10),datetime(2023,1,10,10,35)):
            rows=base+[b(at,75,75.12,74.94,75.08)]
            self.assertEqual(analyze("USDRUBF",rows,10,CFG)[0],[])
        rows=base+[b(datetime(2023,1,10,10,30),75,75.1,74.9,75,v=0),b(datetime(2023,1,10,10,35),75,75.12,74.94,75.08)]
        self.assertEqual(analyze("USDRUBF",rows,10,CFG)[0],[])

    def test_march_windows(self):
        self.assertEqual(windows(datetime(2023,3,13).date())[1][0].minute,15)
        self.assertEqual(windows(datetime(2023,3,21).date())[1][0].minute,5)

    def test_switch_exact_boundary(self):
        self.assertEqual(tick("CNYRUBF",datetime(2023,9,27,18,59)),D("0.01"))
        self.assertEqual(tick("CNYRUBF",datetime(2023,9,27,19)),D("0.001"))

    def test_future_mutation_changes_no_earlier_signal_or_entry(self):
        rows=self.fixture()
        expected=analyze("USDRUBF",rows,10,CFG)[0][0]
        mutated=rows[:]
        for i in (8,9,10,11):
            at,o,_,_,_,v=mutated[i]
            mutated[i]=b(at,o,100,1,50,v)
        self.assertEqual(analyze("USDRUBF",mutated,10,CFG)[0][0],expected)
        # Open changes at unscheduled future slots cannot change this entry.
        mutated[8]=b(mutated[8][0],20,100,1,50)
        self.assertEqual(analyze("USDRUBF",mutated,10,CFG)[0][0],expected)

    def parse_fixture(self, change=None, corrupt_hash=False):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d); m={"source_ref":"PIN", "inputs":{}}
            for symbol in ("USDRUBF","CNYRUBF","GLDRUBF","IMOEXF"):
                text=f"Ticker;Datetime;Open;High;Low;Close;Volume\n{symbol};2023-01-03 10:00:00;10;10;10;10;1\n"
                if change: text=change(text)
                content=text.encode(); path=f"{symbol}.csv"
                (root/path).write_bytes(content+b"PROTECTED_2025_SENTINEL")
                m["inputs"][symbol]={"path":path,"blob":"BLOB","prefix_bytes":len(content),"prefix_sha256":hashlib.sha256(content).hexdigest(),"rows_2023":1,"first":"2023-01-03 10:00:00"}
                if corrupt_hash: m["inputs"][symbol]["prefix_sha256"]="bad"
            def fake_git(root,*args):
                return "PIN" if args[0]=="rev-parse" else "" if args[0]=="status" else "100644 BLOB 0 file"
            with patch("run_level_rejection_opportunities.git",side_effect=fake_git):
                original_open=Path.open
                def guarded_open(path,mode='r',*args,**kwargs):
                    if mode=='rb': self.assertEqual(kwargs.get('buffering'),0)
                    return original_open(path,mode,*args,**kwargs)
                with patch.object(Path,'open',guarded_open):
                    return load_bars(root,m)

    def test_real_semicolon_parser_bounded_prefix(self):
        self.assertEqual(len(self.parse_fixture()["USDRUBF"]),1)

    def test_parser_rejects_sha_mismatch(self):
        with self.assertRaisesRegex(RuntimeError,"HASH_MISMATCH"):
            self.parse_fixture(corrupt_hash=True)

    def test_parser_rejects_unaligned_and_protected_timestamps(self):
        for old,new in (("10:00:00","10:01:00"),("10:00:00","10:00:01"),("2023-01","2025-01"),("10:00:00","10:00:00+03:00")):
            with self.assertRaisesRegex(RuntimeError,"DATE_OR_ORDER"):
                self.parse_fixture(change=lambda s:s.replace(old,new))

    def test_parser_rejects_grid_and_schema(self):
        for old,new in ((";10;10;10;10;1",";10;10.005;10;10;1"),("Ticker;Datetime","Wrong;Datetime")):
            with self.assertRaises(RuntimeError):
                self.parse_fixture(change=lambda s:s.replace(old,new))


if __name__=="__main__":
    unittest.main()
