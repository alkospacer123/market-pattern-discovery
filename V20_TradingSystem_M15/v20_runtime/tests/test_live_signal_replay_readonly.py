"""Offline historical replay may not include M15 bars from the future."""
from __future__ import annotations

from datetime import datetime, timezone
import importlib.util
from pathlib import Path
from unittest import TestCase, mock

from TradingSystemLab.stage8_robot.finam_api import FinamAPI, Response

AUDIT = Path(__file__).resolve().parents[2] / "V20-08" / "v20-08-three-entries-frozen-signal-audit.py"
spec = importlib.util.spec_from_file_location("historical_frozen_signal_audit", AUDIT)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class HistoricalReplayTimeBoundary(TestCase):
    def test_ignore_currently_published_future_bar_not_known_at_entry(self):
        asof = datetime(2026, 10, 27, 8, 0, 30, tzinfo=timezone.utc)
        body = {"bars": [
            {"timestamp": "2026-10-27T07:45:00Z", "open": {"value": "1"}},
            {"timestamp": "2026-10-27T08:00:00Z", "open": {"value": "2"}},
            {"timestamp": "2026-10-27T08:15:00Z", "open": {"value": "3"}},
        ]}
        with mock.patch.object(FinamAPI, "_request", return_value=Response(200,body,None)):
            api = module.HistoricalAsOfAPI("synthetic-token", asof)
            reply = api._request("GET", "/v1/instruments/test/bars?timeframe=TIME_FRAME_M15")
            self.assertEqual([v["timestamp"] for v in reply.body["bars"]],
                             ["2026-10-27T07:45:00Z","2026-10-27T08:00:00Z"])
            self.assertEqual(len(body["bars"]),3, "source broker response unchanged")

    def test_never_allows_order_or_stop_mutations(self):
        api = module.HistoricalAsOfAPI("synthetic-token",
                                       datetime(2026, 10, 27, 8, tzinfo=timezone.utc))
        for name in ("place_order","place_sltp_order","cancel_order"):
            with self.subTest(name=name), self.assertRaisesRegex(RuntimeError,"FORBIDDEN"):
                getattr(api,name)()

    def test_original_case_sides_are_all_short_and_independent(self):
        self.assertEqual(set(module.CASES),
                         {"v20-shallow","v20-obv","v20-inside"})
        self.assertEqual({x[0] for x in module.CASES.values()},
                         {"SHALLOW_PULLBACK","OBV_PRESSURE","INSIDE_DAY_RELEASE"})
        self.assertEqual({x[2] for x in module.CASES.values()},{"SHORT"})


if __name__ == "__main__":
    import unittest
    unittest.main()
