"""V20-08.1 two new fake-only checks for the common H1 single-trial cycle."""
from __future__ import annotations
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import unittest

from TradingSystemLab.stage8_robot.finam_api import Response
import V20_TradingSystem_M15.v20_runtime.finam_execution as execution
from V20_TradingSystem_M15.v20_runtime.finam_execution import (
    V20FinamReadAdapter, V20TradeJournal, V20FinamBlocked,
    read_finam_m15_boundary, frozen_observed_session_exit,
    run_v20_single_trial_cycle,
)
import test_finam_trial_transport as fixture
from test_finam_m15_boundary import FakeFinam as BarFake, bar


class CycleTests(unittest.TestCase):
    def setUp(self):
        guard = patch("TradingSystemLab.stage8_robot.trading_safety_gate.load_kill_switch",
                      return_value=({"state": "ARMED"}, None))
        guard.start()
        self.addCleanup(guard.stop)

    def test_third_observed_session_gap_allowed_for_exit_not_entry(self):
        api = BarFake()
        api.rows = [
            bar(datetime(2026, 10, 24, 7, 15, tzinfo=timezone.utc)),
            bar(datetime(2026, 10, 25, 7, 0, tzinfo=timezone.utc)),
            bar(datetime(2026, 10, 26, 6, 0, tzinfo=timezone.utc), current=True),
        ]
        from test_finam_m15_boundary import ACCOUNT, ACCOUNT_HASH
        reader = V20FinamReadAdapter(
            api=api, robot_id="v20-shallow", account_id=ACCOUNT,
            expected_account_hash=ACCOUNT_HASH,
        )
        reader.authenticate()
        when = datetime(2026, 10, 26, 6, 0, 5, tzinfo=timezone.utc)
        args = dict(
            reader=reader, symbol="USDRUBF",
            from_utc=datetime(2026, 10, 24, 7, 0, tzinfo=timezone.utc),
            now=when,
        )
        with self.assertRaisesRegex(V20FinamBlocked, "M15_FINAL_COMPLETED_BAR_MISSING"):
            read_finam_m15_boundary(**args)
        actual = read_finam_m15_boundary(**args, require_adjacent_completed=False)
        self.assertEqual(frozen_observed_session_exit(
            actual, entry_open_msk=datetime(2026, 10, 24, 10, 15),
        ), "EXIT_AT_THIRD_OBSERVED_SESSION_OPEN")
        self.assertEqual(api.calls[-1][0], "GET")

    def test_owned_fill_posts_one_h1_sltp_then_proves_without_duplicate(self):
        with TemporaryDirectory() as temp:
            root = Path(temp) / "v20lab"
            root.mkdir()
            api = fixture.FakeFinam()
            reader = V20FinamReadAdapter(
                api=api, robot_id=fixture.ROBOT, account_id=fixture.ACCOUNT,
                expected_account_hash=fixture.HASH,
            )
            reader.authenticate()
            self.root, self.api, self.reader = root, api, reader
            with patch.object(execution, "datetime", fixture.OfflineTestClock):
                with V20TradeJournal(root, fixture.ROBOT, fixture.ACCOUNT) as journal:
                    key, snap = fixture.TrialBoundaryTests.entry(self, journal)
                    permit = fixture.TrialBoundaryTests.approval(self, journal, key)
                    sender = fixture.TrialBoundaryTests.transport(self, journal, permit)
                    sender.submit_entry_once(
                        key=key, snapshot=snap, now=fixture.OPEN_UTC,
                    )
                    api.positions = [{
                        "symbol": fixture.SYMBOL, "quantity": fixture.value("1"),
                    }]
                    seen = fixture.OPEN_UTC + timedelta(seconds=3)
                    result = run_v20_single_trial_cycle(
                        sender, now=seen, trial_symbol="USDRUBF",
                        from_utc=fixture.OPEN_UTC - timedelta(hours=1),
                        cost_per_contract=Decimal("2"),
                    )
                    self.assertEqual(result["state"], "STOP_ACK_NEEDS_BROKER_PROOF")
                    self.assertEqual(api.stop_posts, 1)
                    after = fixture.OPEN_UTC + timedelta(minutes=1, seconds=3)
                    confirmed = run_v20_single_trial_cycle(
                        sender, now=after, trial_symbol="USDRUBF",
                        from_utc=fixture.OPEN_UTC - timedelta(hours=1),
                        cost_per_contract=Decimal("2"),
                    )
                    self.assertIn(confirmed["state"], {
                        "STOP_NOW_BROKER_PROVEN", "PROTECTED_AWAIT_NEXT_OPEN",
                    })
                    self.assertEqual(api.stop_posts, 1)
                    self.assertEqual(api.order_posts, 1)
                    self.assertIsNotNone(journal.store.get("protected_fill:" + key))


if __name__ == "__main__":
    unittest.main()
