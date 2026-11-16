"""R070 read-only handoff: exact V20 journal and H1 FINAM fill proof, NO POST."""
from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from hashlib import sha256
from types import SimpleNamespace
from unittest import TestCase, main
from unittest.mock import Mock, patch
import json

from TradingSystemLab.stage8_robot.broker import compact_client_order_id
from TradingSystemLab.stage8_robot.production_broker_state import BrokerOrderView
from V20_TradingSystem_M15.v20_runtime.account_risk import RiskReservation
from V20_TradingSystem_M15.v20_runtime.finam_execution import (
    LiveAccountSnapshot, V20FinamReadAdapter, V20TradeJournal,
)
from V20_TradingSystem_M15.v20_runtime.r070_linked_sltp import (
    stage_r070_protection_from_v20,
)
from V20_TradingSystem_M15.v20_runtime.tp6_protect3 import TP6Protect3Unsafe


class R070V20HandoffTests(TestCase):
    def fixture(self, *, direction="LONG", partial=False, protected=False):
        account = "synthetic-account-01"
        account_hash = sha256(account.encode()).hexdigest()
        robot = "v20-shallow"
        key = f"v20:{robot}:{account_hash[:16]}:synthetic-entry"
        step = Decimal("0.1")
        desired_qty = 2
        qty = 1 if partial else 2
        signed = qty if direction == "LONG" else -qty
        stop = Decimal("98") if direction == "LONG" else Decimal("102")
        now = datetime(2026, 11, 16, 11, 0, tzinfo=timezone.utc)
        facts = [
            {"trade_id_sha256": sha256(f"trade-{i}".encode()).hexdigest(),
             "quantity": 1, "price": "100",
             "utc_seconds": 10000 + i, "nanoseconds": 0,
             "account_trade_currency": "RUB"}
            for i in range(qty)
        ]
        facts.sort(key=lambda f: f["trade_id_sha256"])
        history = {
            "authority_scope": "READONLY_DIAGNOSTIC_ONLY_NO_RUNTIME_HANDOFF",
            "quantity_observation": (
                "PARTIAL_REQUEST_MATCHED" if partial else "FULL_REQUEST_MATCHED"),
            "matched_quantity": qty,
            "matched_unique_fills": facts,
            "fill_set_sha256": sha256(
                json.dumps(facts, sort_keys=True, separators=(",", ":")).encode()
            ).hexdigest(),
            "weighted_price_exact": {"numerator": "100", "denominator": "1"},
        }
        entry = BrokerOrderView(
            "finam-entry-123", "PARTIALLY_FILLED" if partial else "FILLED",
            partial, "REGULAR", "USDRUBF@FUT",
            compact_client_order_id(key), None,
            "SIDE_BUY" if direction == "LONG" else "SIDE_SELL",
            {"quantity": {"value": "2"}})
        orders = [entry]
        stop_intent = None
        protected_fill = None
        broker_stop = None
        if protected:
            stop_intent = {
                "status": "ACK", "broker_order_id": "finam-sltp-456",
            }
            protected_fill = {
                "account_sha256": account_hash,
                "broker_order_id": entry.order_id,
                "broker_stop_id": "finam-sltp-456",
                "broker_stop_percent": "100",
                "installed_stop": str(stop),
            }
            broker_stop = BrokerOrderView(
                "finam-sltp-456", "WATCHING", True, "SLTP", "USDRUBF@FUT",
                compact_client_order_id(key + ":stop"), key + ":stop",
                "SIDE_SELL" if direction == "LONG" else "SIDE_BUY",
                {"sl_price": {"value": str(stop)},
                 "quantity_sl": {"value": "100"},
                 "sl_qty_measure": "SLTP_QTY_MEASURE_PERCENT",
                 "valid_before": "VALID_BEFORE_GOOD_TILL_CANCEL"})
            orders.append(broker_stop)
        reservation = RiskReservation(
            account, key, "USDRUBF", direction, desired_qty,
            Decimal("100"), stop, Decimal("1"), step,
            Decimal("1"), Decimal("1000"), Decimal("0"),
            Decimal("4"), Decimal("2000"), Decimal("45000"))
        payload = {
            "kind": "ENTRY", "symbol": "USDRUBF",
            "finam_symbol": "USDRUBF@FUT",
            "direction": direction, "quantity": desired_qty,
            "reference_entry": "100", "atr14": "1",
        }
        store = SimpleNamespace(
            intent=Mock(side_effect=lambda target: {
                key: {
                    "status": "ACK", "broker_order_id": entry.order_id,
                    "payload": payload},
                key + ":stop": stop_intent,
            }.get(target)),
            get=Mock(side_effect=lambda target, default=None: {
                "risk_reservations": {key: reservation.record()},
                "entry_submission:" + key: {
                    "account_sha256": account_hash,
                    "submitted_at": (now-timedelta(minutes=3)).isoformat()},
                "protected_fill:" + key: protected_fill,
            }.get(target, default)),
            put=Mock(side_effect=AssertionError("NO_SQLITE_WRITE_ALLOWED")),
            transaction=Mock(side_effect=AssertionError("NO_TRANSACTION_ALLOWED")),
        )
        journal = V20TradeJournal.__new__(V20TradeJournal)
        journal.robot_id = robot
        journal.account_hash = account_hash
        journal.store = store
        reader = V20FinamReadAdapter.__new__(V20FinamReadAdapter)
        reader.robot_id = robot
        reader.account_hash = account_hash
        reader.account_id = account
        reader._fresh = Mock()
        reader.inspect_entry_fills = Mock(return_value=history)
        reader.inspect_protective_stop = Mock(return_value=broker_stop)
        snapshot = LiveAccountSnapshot(
            robot, account_hash, now,
            Decimal("45000"), Decimal("35000"),
            {"USDRUBF@FUT": signed}, tuple(orders))
        registry = {"USDRUBF": {
            "finam_symbol": "USDRUBF@FUT", "price_step": "0.1"}}
        return SimpleNamespace(
            journal=journal, reader=reader, snapshot=snapshot, entry_key=key,
            now=now, store=store, registry=registry, history=history, entry=entry)

    def choose(self, data):
        with patch(
            "TradingSystemLab.stage8_robot.production_runtime._load_registry",
            return_value=data.registry,
        ):
            return stage_r070_protection_from_v20(
                journal=data.journal, reader=data.reader, snapshot=data.snapshot,
                entry_key=data.entry_key, now=data.now)

    def test_full_fill_stages_tp6_from_real_v20_journal_and_finam_proof(self):
        for direction in ("LONG", "SHORT"):
            d = self.fixture(direction=direction)
            choice = self.choose(d)
            self.assertEqual(choice.status, "SINGLE_LINKED_SL_TP6_DRAFT_ONLY")
            self.assertEqual(choice.levels.initial_stop,
                             Decimal("98") if direction == "LONG" else Decimal("102"))
            self.assertEqual(choice.levels.take_profit,
                             Decimal("112") if direction == "LONG" else Decimal("88"))
            self.assertEqual(choice.wire["quantity_sl"], {"value": "100"})
            self.assertEqual(choice.wire["quantity_tp"], {"value": "100"})
            self.assertEqual(choice.wire["comment"], d.entry_key + ":stop")
            d.reader.inspect_entry_fills.assert_called_once()
            d.store.put.assert_not_called()

    def test_partial_fill_calls_existing_stop_first_decision_no_tp(self):
        d = self.fixture(partial=True)
        choice = self.choose(d)
        self.assertEqual(choice.status, "ORIGINAL_V20_SL_REQUIRED_PARTIAL_FILL")
        self.assertIsNone(choice.wire)
        self.assertIsNone(choice.levels)
        d.store.put.assert_not_called()

    def test_existing_stop_cannot_be_replaced_or_followed_by_second_tp(self):
        for partial in (False, True):
            d = self.fixture(partial=partial, protected=True)
            choice = self.choose(d)
            self.assertEqual(choice.status,
                             "KEEP_VERIFIED_ORIGINAL_STOP_NO_TP6_REPLACEMENT")
            self.assertIsNone(choice.wire)
            d.reader.inspect_protective_stop.assert_called_once()
            d.reader.inspect_entry_fills.assert_not_called()

    def test_uncertain_stop_intent_unknown_active_stop_and_bad_account_block(self):
        d = self.fixture()
        d.store.intent = Mock(side_effect=lambda target: {
            d.entry_key: {"status": "ACK", "broker_order_id": d.entry.order_id,
                          "payload": {"kind": "ENTRY", "symbol": "USDRUBF",
                                      "finam_symbol": "USDRUBF@FUT",
                                      "direction": "LONG", "quantity": 2,
                                      "reference_entry": "100", "atr14": "1"}},
            d.entry_key + ":stop": {"status": "UNCERTAIN",
                                    "broker_order_id": None},
        }.get(target))
        with self.assertRaisesRegex(TP6Protect3Unsafe,
                                    "R070_V20_EXISTING_STOP_UNCERTAIN_NO_RETRY"):
            self.choose(d)
        d = self.fixture()
        d.snapshot = replace(d.snapshot, account_hash="0" * 64)
        with self.assertRaisesRegex(TP6Protect3Unsafe,
                                    "R070_V20_ACCOUNT_OR_ENTRY_SCOPE_INVALID"):
            self.choose(d)
        d = self.fixture()
        other = BrokerOrderView(
            "unknown-stop", "WATCHING", True, "SLTP", "USDRUBF@FUT",
            "no-client", "no-comment", "SIDE_SELL",
            {"sl_price": {"value": "98"}})
        d.snapshot = replace(d.snapshot, orders=(d.entry, other))
        with self.assertRaisesRegex(TP6Protect3Unsafe,
                                    "R070_V20_UNKNOWN_ACTIVE_STOP_NO_RETRY"):
            self.choose(d)

    def test_fills_or_price_drift_block_without_trading_command(self):
        for kind in ("qty", "atr", "history", "position"):
            d = self.fixture()
            if kind == "qty":
                d.snapshot = replace(d.snapshot, positions={"USDRUBF@FUT": 3})
            elif kind == "atr":
                old = d.store.intent
                def get_intent(k):
                    found = old(k)
                    if k == d.entry_key:
                        return {**found, "payload": {
                            **found["payload"], "atr14": "2"}}
                    return found
                d.store.intent = Mock(side_effect=get_intent)
            elif kind == "history":
                d.reader.inspect_entry_fills.return_value = {
                    **d.history, "matched_quantity": 1}
            else:
                d.reader.inspect_entry_fills.return_value = {
                    **d.history, "matched_unique_fills": [
                        {**d.history["matched_unique_fills"][0],
                         "price": "99"},
                        d.history["matched_unique_fills"][1]]}
            with self.subTest(kind=kind), self.assertRaises(TP6Protect3Unsafe):
                self.choose(d)
            d.store.put.assert_not_called()


if __name__ == "__main__":
    main()
