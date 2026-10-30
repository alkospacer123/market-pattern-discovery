"""08.1: new-only offline handoff from H1 broker facts into V20 SQLite.

This uses a fully in-memory FINAM fake, with no token, network or orders.
"""
from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from tempfile import TemporaryDirectory
import hashlib
import unittest

from TradingSystemLab.stage8_robot.finam_api import FinamAPI
from TradingSystemLab.stage8_robot.execution_grid import initial_projection
from TradingSystemLab.stage8_robot.production_runtime import _load_registry
from TradingSystemLab.stage8_robot.broker import compact_client_order_id

from V20_TradingSystem_M15.v20_runtime.account_risk import AccountAuthority
from V20_TradingSystem_M15.v20_runtime.finam_execution import (
    V20FinamBlocked, V20FinamReadAdapter, V20TradeJournal, LiveAccountSnapshot,
)
from V20_TradingSystem_M15.v20_runtime.offline_planner import FrozenSignal, ProposedEntry


ACCOUNT = "synthetic-v20-readonly-proof"
ROBOT = "v20-shallow"
SHA = hashlib.sha256(ACCOUNT.encode()).hexdigest()
FINAM_SYMBOL = _load_registry()["USDRUBF"]["finam_symbol"]


def value(x):
    return {"value": str(x)}


def initial_case():
    bar = datetime(2026, 10, 24, 10, 15)
    price, atr, step = Decimal("85.00"), Decimal("0.10"), Decimal("0.01")
    stop, distance = initial_projection("LONG", price, price-2*atr, step)
    signal = FrozenSignal("SHALLOW_PULLBACK", "USDRUBF", 1, bar-timedelta(minutes=15), atr)
    entry = ProposedEntry("SHALLOW_PULLBACK", "USDRUBF", "LONG", bar,
                          price, stop, distance, 1, Decimal("675"),
                          Decimal("1500"), "SYNTHETIC")
    authority = AccountAuthority(
        ACCOUNT, Decimal("45000"), Decimal("45000"), step, Decimal("10"),
        Decimal("1500"), 1, Decimal("2"),
    )
    snapshot = LiveAccountSnapshot(ROBOT, SHA, datetime.now(timezone.utc),
                                   Decimal("45000"), Decimal("45000"), {}, ())
    return {"signal": signal, "entry": entry,
            "authority": authority, "snapshot": snapshot}


class FakeFinam(FinamAPI):
    """Inert bounded broker facts; never calls the network transport."""
    def __init__(self, entry_key, entry_wire, *, include_stop):
        self.entry_key = entry_key
        self.entry_wire = dict(entry_wire)
        self.include_stop = include_stop
        self.timestamp = None
        self.calls = []

    def create_session(self):
        self.calls.append("session")

    def session_details(self):
        return {"readonly": False, "account_ids": [ACCOUNT]}

    def account(self, account_id):
        if account_id != ACCOUNT:
            raise AssertionError("FOREIGN_ACCOUNT")
        return {
            "account_id": ACCOUNT, "status": "ACCOUNT_ACTIVE", "type": "FORTS",
            "equity": value("45000"), "unrealized_profit": value("0"),
            "portfolio_forts": {"available_cash": value("45000"),
                                "money_reserved": value("0")},
            "positions": [{"symbol": FINAM_SYMBOL, "quantity": value("1")}],
        }

    def orders(self, account_id):
        if account_id != ACCOUNT:
            raise AssertionError("FOREIGN_ACCOUNT")
        rows = [{
            "order_id": "broker-entry-001", "status": "FILLED",
            "order": dict(self.entry_wire),
        }]
        if self.include_stop:
            key = self.entry_key + ":stop"
            rows.append({
                "order_id": "broker-stop-001", "status": "NEW",
                "sltp_order": {
                    "symbol": FINAM_SYMBOL, "side": "SIDE_SELL",
                    "client_order_id": compact_client_order_id(key),
                    "comment": key, "sl_price": value("84.80"),
                    "sl_qty_measure": "SLTP_QTY_MEASURE_PERCENT",
                    "quantity_sl": value("100"),
                    "valid_before": "VALID_BEFORE_GOOD_TILL_CANCEL",
                },
            })
        return {"orders": rows}

    def trades(self, account_id, *, start=None, end=None, limit=1000):
        if account_id != ACCOUNT:
            raise AssertionError("FOREIGN_ACCOUNT")
        self.calls.append("trades")
        return {"trades": [{
            "account_id": ACCOUNT, "order_id": "broker-entry-001",
            "trade_id": "broker-fill-001", "symbol": FINAM_SYMBOL,
            "side": "SIDE_BUY", "currency": "RUB",
            "price": value("85.00"), "size": value("1"),
            "timestamp": self.timestamp,
        }]}

    def place_order(self, *_args, **_kwargs):
        raise AssertionError("NO_ORDER_POST")

    def place_sltp_order(self, *_args, **_kwargs):
        raise AssertionError("NO_STOP_POST")

    def cancel_order(self, *_args, **_kwargs):
        raise AssertionError("NO_CANCEL")


class H1ProtectedHandoffTests(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / "v20lab"
        self.root.mkdir()

    def setup_broker(self, journal, key, *, include_stop):
        now = datetime.now(timezone.utc)
        journal.record_submission_boundary(key, at=now-timedelta(seconds=5))
        api = FakeFinam(key, journal.store.intent(key)["payload"]["wire"],
                        include_stop=include_stop)
        api.timestamp = (now-timedelta(seconds=2)).isoformat()
        reader = V20FinamReadAdapter(
            api=api, robot_id=ROBOT, account_id=ACCOUNT,
            expected_account_hash=SHA,
        )
        reader.authenticate()
        snap = reader.snapshot(now=now)
        self.assertEqual(
            journal.reconcile_order(key=key, snapshot=snap),
            "BROKER_ACK_NO_FILL_OR_SLTP_PROOF",
        )
        return reader, snap, now, api

    def test_real_h1_fill_and_active_100_percent_stop_persist_across_restart(self):
        with V20TradeJournal(self.root, ROBOT, ACCOUNT) as journal:
            key = journal.prepare_entry(**initial_case())
            reader, snap, now, api = self.setup_broker(journal, key, include_stop=True)
            result = journal.observe_protected_entry(
                key=key, reader=reader, snapshot=snap, now=now,
            )
            self.assertEqual(result["filled_quantity"], 1)
            self.assertEqual(result["broker_stop_percent"], "100")
            self.assertEqual(result["installed_stop"], "84.80")
            self.assertEqual(result["fees_status"], "BUDGETED_ONLY_NOT_ACTUAL")
            self.assertEqual(journal.store.intent(key)["status"], "RECONCILED")
            self.assertEqual(len(journal.store.all_fills()), 1)
            self.assertEqual(journal.store.get("execution_halt"),
                             "ACTUAL_FINAM_FEE_AUTHORITY_PENDING")
            self.assertEqual(
                journal.reconcile_order(key=key, snapshot=snap),
                "BROKER_ORDER_ALREADY_RECONCILED_NO_RETRANSMIT",
            )
        with V20TradeJournal(self.root, ROBOT, ACCOUNT) as journal:
            self.assertEqual(len(journal.store.all_fills()), 1)
            again = journal.observe_protected_entry(
                key=key, reader=reader, snapshot=snap, now=now,
            )
            self.assertEqual(again["fill_set_sha256"], result["fill_set_sha256"])
            self.assertEqual(len(journal.store.all_fills()), 1)
        self.assertEqual(api.calls.count("trades"), 2)

    def test_live_exact_protected_fill_releases_only_resolved_pre_post_checkpoint(self):
        # The pre-POST UNCERTAIN marker cannot outlive full broker proof.
        from V20_TradingSystem_M15.v20_runtime.finam_live import V20LiveJournal
        with V20LiveJournal(self.root, ROBOT, ACCOUNT) as journal:
            key = journal.prepare_entry(**initial_case())
            reader, snap, now, _ = self.setup_broker(journal, key, include_stop=True)
            self.assertEqual(journal.store.get("execution_halt"),
                             "UNKNOWN_POST_REQUIRE_BROKER_RECONCILIATION")
            observation = journal.observe_protected_entry(
                key=key, reader=reader, snapshot=snap, now=now)
            self.assertEqual(observation["risk_assessment"]["status"], "PASS")
            self.assertIsNone(journal.store.get("execution_halt"))
            self.assertEqual(journal.store.intent(key)["status"], "RECONCILED")
            self.assertEqual(observation["broker_stop_percent"], "100")

    def test_live_protected_fill_never_clears_other_durable_halt_reason(self):
        from V20_TradingSystem_M15.v20_runtime.finam_live import V20LiveJournal
        with V20LiveJournal(self.root, ROBOT, ACCOUNT) as journal:
            key = journal.prepare_entry(**initial_case())
            reader, snap, now, _ = self.setup_broker(journal, key, include_stop=True)
            journal.store.put("execution_halt", "OPERATOR_REQUIRED_UNRELATED_ERROR")
            observation = journal.observe_protected_entry(
                key=key, reader=reader, snapshot=snap, now=now)
            self.assertEqual(observation["risk_assessment"]["status"], "PASS")
            self.assertEqual(journal.store.get("execution_halt"),
                             "OPERATOR_REQUIRED_UNRELATED_ERROR")

    def test_h1_493_partial_fill_growth_same_active_100pct_stop_no_second_post(self):
        """Reproduce 1->2 growth where VWAP shifts and stop must not be reposted."""
        from V20_TradingSystem_M15.v20_runtime.finam_live import V20LiveJournal

        class GrowingFake(FakeFinam):
            quantity = 1

            def account(self, account_id):
                result = super().account(account_id)
                result["positions"][0]["quantity"] = value(str(self.quantity))
                return result

            def orders(self, account_id):
                result = super().orders(account_id)
                result["orders"][0]["status"] = (
                    "PARTIAL_FILL" if self.quantity == 1 else "FILLED")
                return result

            def trades(self, account_id, *, start=None, end=None, limit=1000):
                result = super().trades(account_id, start=start, end=end, limit=limit)
                if self.quantity == 2:
                    second = dict(result["trades"][0])
                    second["trade_id"] = "broker-fill-growth-002"
                    second["price"] = value("85.10")
                    result["trades"].append(second)
                return result

        with V20LiveJournal(self.root, ROBOT, ACCOUNT) as journal:
            case = initial_case()
            case["entry"] = replace(case["entry"], quantity=2)
            key = journal.prepare_entry(**case)
            now = datetime.now(timezone.utc)
            journal.record_submission_boundary(key, at=now-timedelta(seconds=10))
            api = GrowingFake(key, journal.store.intent(key)["payload"]["wire"],
                              include_stop=True)
            api.timestamp = (now-timedelta(seconds=3)).isoformat()
            reader = V20FinamReadAdapter(
                api=api, robot_id=ROBOT, account_id=ACCOUNT,
                expected_account_hash=SHA)
            reader.authenticate()
            one = reader.snapshot(now=now)
            self.assertEqual(journal.reconcile_order(key=key, snapshot=one),
                             "BROKER_ACK_NO_FILL_OR_SLTP_PROOF")
            first = journal.observe_protected_entry(
                key=key, reader=reader, snapshot=one, now=now)
            self.assertEqual(first["filled_quantity"], 1)
            self.assertEqual(first["installed_stop"], "84.80")
            self.assertTrue(first["risk_assessment"]["stop_conforms"])
            self.assertEqual(journal.store.intent(key)["status"], "PARTIAL_FILL")
            self.assertIsNone(journal.store.get("execution_halt"))

            api.quantity = 2
            later = now + timedelta(seconds=2)
            two = reader.snapshot(now=later)
            journal.reconcile_order(key=key, snapshot=two)
            grown = journal.observe_protected_entry(
                key=key, reader=reader, snapshot=two, now=later)
            self.assertEqual(grown["filled_quantity"], 2)
            self.assertEqual(grown["installed_stop"], "84.80")
            self.assertNotEqual(grown["risk_assessment"]["projected_stop"],
                                grown["installed_stop"])
            self.assertEqual(grown["risk_assessment"]["status"], "PASS")
            self.assertTrue(grown["h1_same_stop_growth_observed"])
            self.assertFalse(grown["h1_stop_growth_physically_proven"])
            self.assertEqual(journal.store.intent(key)["status"], "RECONCILED")
            self.assertIsNone(journal.store.get("execution_halt"))
            self.assertEqual(len(journal.store.all_fills()), 2)
            self.assertEqual([x for x in api.calls if x == "stop_post"], [])

            repeated = journal.observe_protected_entry(
                key=key, reader=reader, snapshot=two, now=later)
            self.assertEqual(repeated["installed_stop"], "84.80")
            self.assertEqual(len(journal.store.all_fills()), 2)
            self.assertIsNone(journal.store.get("execution_halt"))

    def test_broker_fill_without_active_stop_never_becomes_durable_protected(self):
        with V20TradeJournal(self.root, ROBOT, ACCOUNT) as journal:
            key = journal.prepare_entry(**initial_case())
            reader, snap, now, _ = self.setup_broker(journal, key, include_stop=False)
            with self.assertRaisesRegex(V20FinamBlocked, "STOP_NOT_EXACTLY_ACTIVE"):
                journal.observe_protected_entry(
                    key=key, reader=reader, snapshot=snap, now=now,
                )
            self.assertEqual(journal.store.get("execution_halt"),
                             "OPEN_POSITION_PROTECTION_UNVERIFIED")
            self.assertEqual(journal.store.all_fills(), [])
            self.assertEqual(journal.store.intent(key)["status"], "ACK")

    def test_money_snapshot_and_submission_interval_are_durable(self):
        with V20TradeJournal(self.root, ROBOT, ACCOUNT) as journal:
            bad = initial_case()
            snap = bad["snapshot"]
            bad["snapshot"] = LiveAccountSnapshot(
                snap.robot_id, snap.account_hash, snap.observed_at,
                Decimal("46000"), snap.available_cash, {}, (),
            )
            with self.assertRaisesRegex(V20FinamBlocked, "BROKER_MONEY_SNAPSHOT_MISMATCH"):
                journal.prepare_entry(**bad)
            key = journal.prepare_entry(**initial_case())
            at = datetime.now(timezone.utc) - timedelta(seconds=5)
            journal.record_submission_boundary(key, at=at)
            submission = journal.store.get("entry_submission:" + key)
            self.assertEqual(submission["account_sha256"], SHA)
            self.assertEqual(datetime.fromisoformat(submission["submitted_at"]), at)
        with V20TradeJournal(self.root, ROBOT, ACCOUNT) as journal:
            self.assertEqual(journal.store.get("entry_submission:" + key), submission)



if __name__ == "__main__":
    unittest.main()
