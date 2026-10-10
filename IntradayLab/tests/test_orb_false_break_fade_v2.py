"""V2 ATR/M15 mechanism tests, no historical market-data access."""
from datetime import datetime, timedelta
from decimal import Decimal as D
from pathlib import Path
import sys
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"tools"))
import run_orb_false_break_fade_v2 as v2


def bar(high="101",low="99",close="100",volume="1"):
    return tuple(map(D,("100",high,low,close,volume)))


class V2Features(unittest.TestCase):
    def test_atr_carries_14_real_bars_across_session_gap(self):
        t=datetime(2023,1,3,18,0)
        bars={t+timedelta(minutes=5*i):bar(high="101",low="99") for i in range(10)}
        u=datetime(2023,1,4,10,0)
        bars.update({u+timedelta(minutes=5*i):bar(high="101",low="99") for i in range(4)})
        out=v2.causal_atr14(bars)
        self.assertEqual(out[u+timedelta(minutes=15)],D(2))
        self.assertEqual(v2.independent_atr_at(bars,u+timedelta(minutes=15)),D(2))

    def test_atr_missing_prior_does_not_invent_adjacent_close(self):
        t=datetime(2023,1,3,10,0)
        bars={t+timedelta(minutes=5*i):bar() for i in range(15)}
        del bars[t+timedelta(minutes=40)]
        out=v2.causal_atr14(bars)
        self.assertEqual(len(out),1)
        self.assertEqual(next(iter(out.values())),D(2))

    def test_m15_not_candle_color_gate(self):
        event=dict(base_reason="SIGNAL",direction=-1,or_high=D(101),
                   or_low=D(99),sweep_size=D("0.05"),
                   v2_atr14=D("0.1"),v2_atr_ready=True,
                   v2_atr_pass=True,v2_m15_context_available=True,
                   v2_m15_breakout_accepted_veto=False)
        e=v2.select_architecture([event],{"atr":False,"mtf":True})[0]
        self.assertEqual(e["base_reason"],"SIGNAL")
        event["v2_m15_breakout_accepted_veto"]=True
        e=v2.select_architecture([event],{"atr":False,"mtf":True})[0]
        self.assertEqual(e["base_reason"],"V2_M15_ACCEPTED_BREAKOUT_VETO")

    def test_atr_does_not_block_base_or_mtf(self):
        e=dict(base_reason="SIGNAL",v2_atr_ready=False,v2_atr_pass=False,
               v2_m15_breakout_accepted_veto=False,
               v2_m15_context_available=True)
        for arch in ({"atr":False,"mtf":False},{"atr":False,"mtf":True}):
            self.assertEqual(v2.select_architecture([e],arch)[0]["base_reason"],"SIGNAL")
        self.assertEqual(v2.select_architecture([e],{"atr":True,"mtf":False})[0]["base_reason"],"V2_ATR_UNAVAILABLE")

    def test_no_context_explicitly_neutral(self):
        e=dict(base_reason="SIGNAL",v2_atr_ready=True,v2_atr_pass=True,
               v2_m15_breakout_accepted_veto=False,
               v2_m15_context_available=False)
        s=v2.select_architecture([e],{"atr":False,"mtf":True})[0]
        self.assertEqual(s["base_reason"],"SIGNAL")
        self.assertEqual(s["v2_filter_reason"],"M15_NO_CONTEXT_NEUTRAL_ALLOWED")


if __name__=="__main__":
    unittest.main()
