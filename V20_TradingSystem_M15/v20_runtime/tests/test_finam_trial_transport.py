"""Only new V20-08.1 order-capable adapter tests, with fake FINAM only.

All approval files are artificial fixtures in TemporaryDirectory. These tests
do NOT authorize any user account, Task or real transaction.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal
import hashlib
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from TradingSystemLab.stage8_robot.broker import compact_client_order_id
from TradingSystemLab.stage8_robot.finam_api import FinamAPI, FinamUncertainSubmission
from TradingSystemLab.stage8_robot.execution_grid import initial_projection

import V20_TradingSystem_M15.v20_runtime.finam_execution as execution
from V20_TradingSystem_M15.v20_runtime.finam_execution import (
    V20TradeJournal, V20FinamReadAdapter, V20FinamBlocked,
    V20SingleTradeTransport, LiveAccountSnapshot,
)
from V20_TradingSystem_M15.v20_runtime.offline_planner import FrozenSignal, ProposedEntry
from V20_TradingSystem_M15.v20_runtime.account_risk import AccountAuthority


ACCOUNT = "isolated-trial-fake-account"
ROBOT = "v20-shallow"
HASH = hashlib.sha256(ACCOUNT.encode()).hexdigest()
CODE_SHA = "a" * 40
class OfflineTestClock(datetime):
    """A datetime subclass keeps isinstance() checks real, never a MagicMock."""
    @classmethod
    def now(cls, tz=None):
        value = OPEN_UTC
        return value if tz is not None else value.replace(tzinfo=None)


OPEN_UTC = OfflineTestClock(2026, 10, 24, 7, 15, 5, tzinfo=timezone.utc)
SYMBOL = "USDRUBF@RTSX"


def value(x):
    return {"value": str(x)}


class FakeFinam(FinamAPI):
    def __init__(self):
        self.positions = []
        self.orders_book = []
        self.order_posts = 0
        self.stop_posts = 0
        self.uncertain_next = False
        self.sent_stops = []
        self.fill_price = '85.00'
        self.include_trade = True

    def create_session(self):
        return None

    def session_details(self):
        return {"readonly": False, "account_ids": [ACCOUNT]}

    def account(self, account_id):
        if account_id != ACCOUNT:
            raise AssertionError("FOREIGN_ACCOUNT")
        return {"account_id": ACCOUNT, "status": "ACCOUNT_ACTIVE",
                "type": "FORTS", "equity": value("45000"),
                "unrealized_profit": value("0"),
                "portfolio_forts": {"available_cash": value("45000"),
                                    "money_reserved": value("0")},
                "positions": self.positions}

    def orders(self, account_id):
        if account_id != ACCOUNT:
            raise AssertionError("FOREIGN_ACCOUNT")
        return {"orders": self.orders_book}

    def trades(self, account_id, *, start=None, end=None, limit=1000):
        if account_id != ACCOUNT:
            raise AssertionError("FOREIGN_ACCOUNT")
        if not self.include_trade or not self.orders_book:
            return {"trades": []}
        return {"trades": [{
            "account_id": ACCOUNT,
            "order_id": "entry-fake-1",
            "trade_id": "fill-fake-001",
            "symbol": SYMBOL,
            "side": "SIDE_BUY",
            "currency": "RUB",
            "price": value(self.fill_price),
            "size": value("1"),
            "timestamp": (OPEN_UTC + timedelta(seconds=1)).isoformat(),
        }]}

    def place_order(self, account_id, payload):
        if account_id != ACCOUNT:
            raise AssertionError("FOREIGN_ACCOUNT")
        self.order_posts += 1
        if self.uncertain_next:
            self.uncertain_next = False
            raise FinamUncertainSubmission("FAKE_TIMEOUT")
        self.orders_book.append({
            "order_id": "entry-fake-1", "status": "NEW",
            "order": dict(payload),
        })
        return {"order_id": "entry-fake-1"}

    def place_sltp_order(self, account_id, payload):
        if account_id != ACCOUNT:
            raise AssertionError("FOREIGN_ACCOUNT")
        self.stop_posts += 1
        self.sent_stops.append(dict(payload))
        self.orders_book.append({
            "order_id": "stop-fake-1", "status": "NEW",
            "sltp_order": dict(payload),
        })
        return {"order_id": "stop-fake-1"}

    def cancel_order(self, *_):
        raise AssertionError("STOP_CANCEL_NOT_AUTHORIZED")


class TrialBoundaryTests(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / "v20lab"
        self.root.mkdir()
        self.api = FakeFinam()
        self.reader = V20FinamReadAdapter(api=self.api, robot_id=ROBOT,
                                          account_id=ACCOUNT, expected_account_hash=HASH)
        self.reader.authenticate()
        # Every authorized fake entry exercises the real final-post arm gate.
        guard = patch("TradingSystemLab.stage8_robot.trading_safety_gate.load_kill_switch",
                      return_value=({"state": "ARMED"}, None))
        guard.start()
        self.addCleanup(guard.stop)

    def entry(self, journal):
        bar = datetime(2026, 10, 24, 10, 15)
        price = Decimal("85.00")
        atr = Decimal("0.10")
        stop, distance = initial_projection("LONG", price,
                                            price-2*atr, Decimal("0.01"))
        signal = FrozenSignal("SHALLOW_PULLBACK", "USDRUBF", 1,
                              bar-timedelta(minutes=15), atr)
        entry = ProposedEntry("SHALLOW_PULLBACK", "USDRUBF", "LONG", bar,
                              price, stop, distance, 1, Decimal("675"),
                              Decimal("1500"), "SYNTHETIC")
        authority = AccountAuthority(ACCOUNT, Decimal("45000"), Decimal("45000"),
                                     Decimal("0.01"), Decimal("10"),
                                     Decimal("1500"), 1, Decimal("2"))
        snap = self.reader.snapshot(now=OPEN_UTC)
        return journal.prepare_entry(signal=signal, entry=entry,
                                     authority=authority, snapshot=snap), snap

    def approval(self, journal, key, *, valid=True):
        permit = {
            "schema": "v20.08.2.single_trial.v1",
            "scope": "ONE_SPECIFIC_APPROVED_TRIAL",
            "source_commit": CODE_SHA, "robot_id": ROBOT,
            "account_sha256": HASH, "entry_key": key,
            "authorized_operations": ["ENTRY", "PROTECTIVE_STOP", "FROZEN_EXIT"],
            "explicit_owner_approval": True,
            "instrument": "USDRUBF" if valid else "CNYRUBF",
            "direction": "LONG", "max_quantity": 1,
            "max_risk_rub": "675",
        }
        permit_path = journal.instance_root / "safety" / "v20-single-trial-approval.json"
        permit_path.parent.mkdir(parents=True, exist_ok=True)
        permit_path.write_text(json.dumps(permit), encoding="utf-8")
        return permit_path

    def transport(self, journal, permit=None):
        return V20SingleTradeTransport(
            journal=journal, reader=self.reader, accepted_commit=CODE_SHA,
            trial_permit_path=permit,
        )

    def test_without_external_approval_no_market_or_sltp_post(self):
        with patch.object(execution, "datetime", OfflineTestClock):
            with V20TradeJournal(self.root, ROBOT, ACCOUNT) as journal:
                key, snap = self.entry(journal)
                with self.assertRaisesRegex(V20FinamBlocked, "SINGLE_TRIAL_EXPLICIT_AUTHORIZATION_MISSING"):
                    self.transport(journal).submit_entry_once(key=key, snapshot=snap, now=OPEN_UTC)
                self.assertEqual(self.api.order_posts, 0)
                self.assertEqual(journal.store.intent(key)["status"], "INTENT_PERSISTED")

    def test_halt_after_preparation_blocks_market_post(self):
        with patch.object(execution, "datetime", OfflineTestClock):
            with V20TradeJournal(self.root, ROBOT, ACCOUNT) as journal:
                key, snap = self.entry(journal)
                permit = self.approval(journal, key)
                with patch("TradingSystemLab.stage8_robot.trading_safety_gate.load_kill_switch",
                           return_value=({"state": "HALTED"}, None)):
                    with self.assertRaisesRegex(
                        V20FinamBlocked, "TRIAL_ENTRY_V20_KILL_SWITCH_NOT_ARMED"
                    ):
                        self.transport(journal, permit).submit_entry_once(
                            key=key, snapshot=snap, now=OPEN_UTC,
                        )
                self.assertEqual(self.api.order_posts, 0)
                self.assertIsNone(journal.store.get("trial_authority_consumed"))
                self.assertEqual(journal.store.intent(key)["status"], "INTENT_PERSISTED")

    def test_wrong_trial_scope_denied_before_post(self):
        with patch.object(execution, "datetime", OfflineTestClock):
            with V20TradeJournal(self.root, ROBOT, ACCOUNT) as journal:
                key, snap = self.entry(journal)
                permit = self.approval(journal, key, valid=False)
                with self.assertRaisesRegex(V20FinamBlocked, "TRIAL_SCOPE_NOT_EXACT"):
                    self.transport(journal, permit).submit_entry_once(
                        key=key, snapshot=snap, now=OPEN_UTC,
                    )
                self.assertEqual(self.api.order_posts, 0)

    def test_exact_single_entry_and_h1_100_percent_stop_never_resubmitted(self):
        with patch.object(execution, "datetime", OfflineTestClock):
            with V20TradeJournal(self.root, ROBOT, ACCOUNT) as journal:
                key, snap = self.entry(journal)
                permit = self.approval(journal, key)
                transport = self.transport(journal, permit)
                oid = transport.submit_entry_once(key=key, snapshot=snap, now=OPEN_UTC)
                self.assertEqual(oid, "entry-fake-1")
                self.assertEqual(journal.store.intent(key)["status"], "ACK")
                self.assertEqual(journal.store.get("trial_authority_consumed"), key)
                self.assertEqual(self.api.order_posts, 1)
                with self.assertRaises(V20FinamBlocked):
                    transport.submit_entry_once(key=key, snapshot=snap, now=OPEN_UTC)
                self.assertEqual(self.api.order_posts, 1)
                self.api.positions = [{"symbol": SYMBOL, "quantity": value("1")}]
                later = OPEN_UTC + timedelta(seconds=3)
                filled_snap = self.reader.snapshot(now=later)
                stop_oid = transport.submit_protection_once(
                    key=key, snapshot=filled_snap, stop_price=Decimal("84.80"), now=later,
                )
                self.assertEqual(stop_oid, "stop-fake-1")
                self.assertEqual(self.api.stop_posts, 1)
                self.assertEqual(self.api.sent_stops[0]["sl_qty_measure"], "SLTP_QTY_MEASURE_PERCENT")
                self.assertEqual(self.api.sent_stops[0]["quantity_sl"], value("100"))
                self.assertEqual(self.api.sent_stops[0]["client_order_id"],
                                 compact_client_order_id(key+":stop"))
                with self.assertRaisesRegex(V20FinamBlocked, "STOP_ALREADY_ATTEMPTED"):
                    transport.submit_protection_once(
                        key=key, snapshot=filled_snap,
                        stop_price=Decimal("84.80"), now=later,
                    )
                self.assertEqual(self.api.stop_posts, 1)

    def test_unproved_or_wrong_vwap_stop_never_posts(self):
        with patch.object(execution, "datetime", OfflineTestClock):
            with V20TradeJournal(self.root, ROBOT, ACCOUNT) as journal:
                key, snap = self.entry(journal)
                permit = self.approval(journal, key)
                sender = self.transport(journal, permit)
                sender.submit_entry_once(key=key, snapshot=snap, now=OPEN_UTC)
                self.api.positions = [{"symbol": SYMBOL, "quantity": value("1")}]
                at = OPEN_UTC + timedelta(seconds=3)
                live = self.reader.snapshot(now=at)
                with self.assertRaisesRegex(V20FinamBlocked, "STOP_NOT_FROM_ACTUAL_FINAM_FILL_VWAP"):
                    sender.submit_protection_once(
                        key=key, snapshot=live, stop_price=Decimal("84.79"), now=at,
                    )
                self.assertEqual(self.api.stop_posts, 0)
                self.api.include_trade = False
                with self.assertRaisesRegex(V20FinamBlocked, "STOP_ENTRY_FILLS_NOT_PROVEN"):
                    sender.submit_protection_once(
                        key=key, snapshot=live, stop_price=Decimal("84.80"), now=at,
                    )
                self.assertEqual(self.api.stop_posts, 0)
                self.assertIsNone(journal.store.intent(key + ":stop"))

    def test_unknown_post_stays_uncertain_after_restart_without_retry(self):
        with patch.object(execution, "datetime", OfflineTestClock):
            with V20TradeJournal(self.root, ROBOT, ACCOUNT) as journal:
                key, snap = self.entry(journal)
                permit = self.approval(journal, key)
                self.api.uncertain_next = True
                with self.assertRaises(FinamUncertainSubmission):
                    self.transport(journal, permit).submit_entry_once(
                        key=key, snapshot=snap, now=OPEN_UTC,
                    )
                self.assertEqual(journal.store.intent(key)["status"], "UNCERTAIN")
                self.assertEqual(self.api.order_posts, 1)
            with V20TradeJournal(self.root, ROBOT, ACCOUNT) as journal:
                with self.assertRaises(V20FinamBlocked):
                    self.transport(journal, permit).submit_entry_once(
                        key=key, snapshot=snap, now=OPEN_UTC,
                    )
                self.assertEqual(self.api.order_posts, 1)


if __name__ == "__main__":
    unittest.main()
