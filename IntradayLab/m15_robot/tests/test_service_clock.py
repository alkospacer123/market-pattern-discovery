import json
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

from IntradayLab.m15_robot.service_clock import (
    M15OfflineClock, M15ClockError, M15SingleInstance,
)

MSK = ZoneInfo("Europe/Moscow")
AT = datetime(2026, 10, 17, 10, 0, tzinfo=MSK)
SYMS = ("USDRUBF", "CNYRUBF", "GLDRUBF", "IMOEXF")


class OfflineClock(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name) / "m15"
        self.now = AT
        self.bars = {s: [] for s in SYMS}
        self.get = lambda s, now: list(self.bars[s])
        self.make = lambda: M15OfflineClock(root=self.root, completed=self.get, clock=lambda: self.now)

    def tearDown(self):
        self.tmp.cleanup()

    def test_fresh_bar_once_only(self):
        self.bars["USDRUBF"] = [AT]
        c = self.make()
        self.assertEqual(len(c.once()["advanced"]), 1)
        self.assertEqual(len(c.once()["advanced"]), 0)

    def test_restart_watermark(self):
        self.bars["CNYRUBF"] = [AT]
        self.make().once()
        self.assertEqual(self.make().once()["advanced"], [])
        self.bars["CNYRUBF"].append(AT + timedelta(minutes=15))
        self.now += timedelta(minutes=15)
        self.assertEqual(len(self.make().once()["advanced"]), 1)

    def test_gap_does_not_synthesize(self):
        self.bars["GLDRUBF"] = [AT]
        self.make().once()
        self.now += timedelta(minutes=45)
        self.bars["GLDRUBF"] = [AT, AT + timedelta(minutes=45)]
        events = self.make().once()["advanced"]
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["close_utc"], (AT + timedelta(minutes=45)).astimezone(timezone.utc).isoformat())

    def test_multi_instrument(self):
        for s in SYMS: self.bars[s] = [AT]
        self.assertEqual(len(self.make().once()["advanced"]), 4)

    def test_future_close_fails_without_watermark_write(self):
        self.bars["CNYRUBF"] = [AT + timedelta(minutes=15)]
        with self.assertRaisesRegex(M15ClockError, "FUTURE_CLOSE"):
            self.make().once()
        self.assertFalse((self.root / "state" / "m15-offline-service-clock.json").exists())

    def test_offgrid_fails(self):
        self.bars["USDRUBF"] = [AT + timedelta(minutes=1)]
        with self.assertRaisesRegex(M15ClockError, "GRID"):
            self.make().once()

    def test_naive_fails(self):
        self.bars["USDRUBF"] = [AT.replace(tzinfo=None)]
        with self.assertRaisesRegex(M15ClockError, "TIMEZONE"):
            self.make().once()

    def test_unsorted_or_duplicate_fails(self):
        self.bars["USDRUBF"] = [AT, AT]
        with self.assertRaisesRegex(M15ClockError, "UNSORTED_OR_DUPLICATE"):
            self.make().once()

    def test_second_instance_fails(self):
        c = self.make()
        with c.lock():
            with self.assertRaisesRegex(M15ClockError, "SECOND_PROCESS"):
                with self.make().lock(): pass

    def test_corrupt_persisted_watermark_denied(self):
        c = self.make()
        c.once()
        p = self.root / "state" / "m15-offline-service-clock.json"
        p.write_text('{"schema":"BAD","watermarks":{}}')
        with self.assertRaisesRegex(M15ClockError, "WATERMARK_INVALID"):
            self.make().once()

    def test_heartbeat_never_live(self):
        self.make().once()
        p = self.root / "state" / "m15-offline-service-heartbeat.json"
        x = json.loads(p.read_text())
        self.assertFalse(x["live_authorized"])
        self.assertEqual(x["status"], "HEALTHY_OFFLINE_NO_TRADING")

    def test_24h_30s_polls_no_double_decisions(self):
        c = self.make()
        counts = {s:0 for s in SYMS}
        def completed(symbol, observed):
            start = AT
            elapsed = int((observed - start).total_seconds() // 900)
            return [start + timedelta(minutes=15*n) for n in range(elapsed+1)]
        c.completed = completed
        def sleeper(seconds): self.now += timedelta(seconds=seconds)
        cycles = c.simulate(2880, sleeper)
        self.assertEqual(len(cycles), 2880)
        self.assertEqual(sum(len(x["advanced"]) for x in cycles), 96*4)
        self.assertTrue(all(not x["live_authorized"] for x in cycles))

    def test_bad_poll_argument_denied(self):
        with self.assertRaisesRegex(M15ClockError, "POLL_INTERVAL"):
            M15OfflineClock(root=self.root, completed=self.get, clock=lambda:self.now, poll_seconds=0)

    def test_lock_released_after_failure(self):
        self.bars["IMOEXF"] = [AT + timedelta(minutes=1)]
        with self.assertRaises(M15ClockError): self.make().once()
        self.bars["IMOEXF"] = [AT]
        self.assertEqual(len(self.make().once()["advanced"]), 1)


if __name__ == "__main__": unittest.main()
