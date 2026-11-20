"""V20-08.1 two focused fake H1 FINAM tests: frozen exit then flat SLTP cleanup."""
from __future__ import annotations
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import unittest
import pandas as pd
from TradingSystemLab.stage8_robot.finam_api import FinamUncertainSubmission, Response
import V20_TradingSystem_M15.v20_runtime.finam_execution as execution
from V20_TradingSystem_M15.v20_runtime.finam_execution import (
    V20TradeJournal, V20FinamReadAdapter, V20FinamBlocked, V20M15Boundary,
)
from test_finam_trial_transport import (
    ACCOUNT, HASH, ROBOT, OPEN_UTC, CODE_SHA, SYMBOL, FakeFinam,
    OfflineTestClock, TrialBoundaryTests, value,
)

DUE = OfflineTestClock(2026, 10, 26, 6, 0, 5, tzinfo=timezone.utc)


def bar(t, current=False):
    row = {"timestamp": t.isoformat(), "open": value("85.00")}
    if not current:
        row.update(high=value("85.10"), low=value("84.90"),
                   close=value("85.02"), volume=value("100"))
    return row


class ExitFake(FakeFinam):
    def __init__(self):
        super().__init__()
        self.exit_posts = 0
        self.stop_cancels = 0

    def _request(self, method, path, *args, **kwargs):
        if method != "GET" or "TIME_FRAME_M15" not in path:
            raise AssertionError("NO_UNEXPECTED_NETWORK")
        return Response(200, {"symbol": SYMBOL, "bars": [
            bar(datetime(2026, 10, 24, 7, 15, tzinfo=timezone.utc)),
            bar(datetime(2026, 10, 25, 7, 0, tzinfo=timezone.utc)),
            bar(datetime(2026, 10, 26, 5, 45, tzinfo=timezone.utc)),
            bar(datetime(2026, 10, 26, 6, 0, tzinfo=timezone.utc), current=True),
        ]}, None)

    def place_order(self, account_id, payload):
        if payload["side"] == "SIDE_SELL":
            if account_id != ACCOUNT:
                raise AssertionError("FOREIGN_ACCOUNT")
            self.exit_posts += 1
            if self.uncertain_next:
                self.uncertain_next = False
                raise FinamUncertainSubmission("FAKE_EXIT_UNKNOWN")
            self.orders_book.append({
                "order_id": "fake-exit-1", "status": "NEW", "order": dict(payload),
            })
            return {"order_id": "fake-exit-1"}
        return super().place_order(account_id, payload)

    def cancel_order(self, account_id, order_id):
        if account_id != ACCOUNT or order_id != "stop-fake-1" or self.positions:
            raise AssertionError("CANCEL_BEFORE_BROKER_FLAT_FORBIDDEN")
        self.stop_cancels += 1
        for row in self.orders_book:
            if row["order_id"] == order_id:
                row["status"] = "CANCELLED"
        return {"order_id": order_id}


class FrozenExitTests(unittest.TestCase):
    entry = TrialBoundaryTests.entry
    approval = TrialBoundaryTests.approval
    transport = TrialBoundaryTests.transport

    def setUp(self):
        self.temp = TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / "v20lab"
        self.root.mkdir()
        self.api = ExitFake()
        self.reader = V20FinamReadAdapter(
            api=self.api, robot_id=ROBOT, account_id=ACCOUNT,
            expected_account_hash=HASH,
        )
        self.reader.authenticate()
        guard = patch("TradingSystemLab.stage8_robot.trading_safety_gate.load_kill_switch",
                      return_value=({"state": "ARMED"}, None))
        guard.start()
        self.addCleanup(guard.stop)

    def setup_protected(self, journal):
        key, snap = self.entry(journal)
        permit = self.approval(journal, key)
        sender = self.transport(journal, permit)
        sender.submit_entry_once(key=key, snapshot=snap, now=OPEN_UTC)
        self.api.positions = [{"symbol": SYMBOL, "quantity": value("1")}]
        at = OPEN_UTC + timedelta(seconds=3)
        live = self.reader.snapshot(now=at)
        sender.submit_protection_once(key=key, snapshot=live,
                                      stop_price=Decimal("84.80"), now=at)
        protected_snap = self.reader.snapshot(now=at + timedelta(seconds=1))
        journal.observe_protected_entry(
            key=key, reader=self.reader, snapshot=protected_snap,
            now=at + timedelta(seconds=1),
        )
        return key, sender

    def boundary(self):
        return V20M15Boundary(
            "USDRUBF", datetime(2026, 10, 26, 9, 0),
            pd.DataFrame({"Datetime": [
                datetime(2026, 10, 24, 10, 15),
                datetime(2026, 10, 25, 10, 0),
                datetime(2026, 10, 26, 8, 45),
            ]}), Decimal("85.00"), DUE,
        )

    def test_protected_third_session_exit_then_flat_stop_cancel_only(self):
        with patch.object(execution, "datetime", OfflineTestClock):
            with V20TradeJournal(self.root, ROBOT, ACCOUNT) as journal:
                key, sender = self.setup_protected(journal)
                snap = self.reader.snapshot(now=DUE)
                boundary = self.boundary()
                self.assertEqual(sender.submit_frozen_exit_once(
                    key=key, boundary=boundary, snapshot=snap, now=DUE,
                ), "fake-exit-1")
                self.assertEqual(self.api.exit_posts, 1)
                self.assertEqual(self.api.stop_cancels, 0)
                with self.assertRaisesRegex(V20FinamBlocked, "FLAT_CLEANUP_POSITION_OPEN"):
                    sender.cancel_stop_after_flat_once(
                        key=key, snapshot=self.reader.snapshot(now=DUE), now=DUE,
                    )
                self.api.positions = []
                flat = self.reader.snapshot(now=DUE+timedelta(seconds=1))
                self.assertEqual(sender.cancel_stop_after_flat_once(
                    key=key, snapshot=flat, now=DUE+timedelta(seconds=1),
                ), "CANCEL_ACK_REQUIRE_BROKER_NO_STOP_CONFIRMATION")
                self.assertEqual(self.api.stop_cancels, 1)
                after = self.reader.snapshot(now=DUE+timedelta(seconds=2))
                self.assertEqual(sender.cancel_stop_after_flat_once(
                    key=key, snapshot=after, now=DUE+timedelta(seconds=2),
                ), "BROKER_FLAT_NO_ACTIVE_STOP")
                self.assertEqual(self.api.stop_cancels, 1)

    def test_unknown_exit_keeps_stop_and_blocks_retransmission(self):
        with patch.object(execution, "datetime", OfflineTestClock):
            with V20TradeJournal(self.root, ROBOT, ACCOUNT) as journal:
                key, sender = self.setup_protected(journal)
                due = self.boundary()
                self.api.uncertain_next = True
                with self.assertRaises(FinamUncertainSubmission):
                    sender.submit_frozen_exit_once(
                        key=key, boundary=due,
                        snapshot=self.reader.snapshot(now=DUE), now=DUE,
                    )
                self.assertEqual(journal.store.intent(key+":frozen-exit")["status"], "UNCERTAIN")
                self.assertEqual(self.api.exit_posts, 1)
                self.assertEqual(self.api.stop_cancels, 0)
                self.assertEqual(sum(o["status"] == "NEW" and "sltp_order" in o
                                     for o in self.api.orders_book), 1)
                with self.assertRaisesRegex(V20FinamBlocked, "EXIT_ALREADY_ATTEMPTED_NO_RETRANSMIT"):
                    sender.submit_frozen_exit_once(
                        key=key, boundary=due,
                        snapshot=self.reader.snapshot(now=DUE), now=DUE,
                    )
                self.assertEqual(self.api.exit_posts, 1)


if __name__ == "__main__":
    unittest.main()
