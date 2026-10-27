"""Focused H1 main -> V20 LIVE broker lifecycle parity. Synthetic only.

H1 origin: production_service.py._reconcile_intents, _flat_cleanup_and_exit,
production_runtime.py.record_entry_submission/_handoff_entry_history,
trading_safety_gate.py.emergency_halt.
No FINAM network, DPAPI, Windows Task or order POST.
"""
from __future__ import annotations

from contextlib import nullcontext
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch
import unittest

from TradingSystemLab.stage8_robot.account_cleanliness import TERMINAL_ORDER_STATUSES
from TradingSystemLab.stage8_robot.broker import compact_client_order_id
from TradingSystemLab.stage8_robot.production_broker_state import BrokerOrderView

from V20_TradingSystem_M15.v20_runtime.finam_live import (
    _follow_existing, V20FinamBlocked,
)
from V20_TradingSystem_M15.v20_runtime.finam_execution import V20LiveTransport, V20SingleTradeTransport

KEY = "live-20261027-test-entry"
STOP_KEY = KEY + ":stop"
SYMBOL = "FUTUSDRUBF"
NOW = datetime(2026, 10, 27, 7, 34, 11, tzinfo=timezone.utc)
ACCOUNT_HASH = "b" * 64


class Store:
    def __init__(self, intents, state=None):
        self.intents = intents
        self.state = state or {}
        self.written = []

    def intent(self, key):
        return self.intents.get(key)

    def get(self, key, default=None):
        return self.state.get(key, default)

    def put(self, key, value):
        self.state[key] = value
        self.written.append((key, value))

    def transaction(self):
        return nullcontext()

    def persist_intent(self, key, payload):
        self.intents[key] = {"payload": payload, "status": "INTENT_PERSISTED", "broker_order_id": None}

    def transition_intent(self, key, status, broker_order_id=None):
        self.intents[key]["status"] = status
        if broker_order_id is not None:
            self.intents[key]["broker_order_id"] = broker_order_id


def broker_order(*, kind="SLTP", status="NEW", broker_id="stop-100", key=STOP_KEY):
    wire = {"symbol": SYMBOL, "client_order_id": compact_client_order_id(key),
            "side": "SIDE_BUY", "quantity": {"value": "2"}}
    return BrokerOrderView(order_id=broker_id, status=status,
                           active=status not in TERMINAL_ORDER_STATUSES,
                           kind=kind, symbol=SYMBOL, client_order_id=wire["client_order_id"],
                           comment=key, side="SIDE_BUY", request=wire)


def example(*, pos=0, exit_status=None, stop_status="NEW"):
    payload = {"kind": "ENTRY", "symbol": "USDRUBF", "finam_symbol": SYMBOL,
               "direction": "SHORT", "quantity": 2, "entry_at": "2026-10-27T10:30:00"}
    entries={KEY: {"payload":payload, "idempotency_key":KEY,
                   "status":"RECONCILED", "broker_order_id":"entry-100"},
             STOP_KEY:{"payload":{"kind":"STOP","entry_key":KEY},
                       "status":"ACK","broker_order_id":"stop-100"}}
    if exit_status is not None:
        entries[KEY+":frozen-exit"]={
            "payload":{"kind":"FROZEN_EXIT", "wire":{"symbol": SYMBOL,
                         "side":"SIDE_BUY","quantity":{"value":"2"}}},
            "status":"ACK", "broker_order_id":"exit-100",
        }
    protected={"account_sha256":ACCOUNT_HASH, "broker_order_id":"entry-100",
               "broker_stop_id":"stop-100", "filled_quantity":2,
               "broker_stop_percent":"100","installed_stop":"80.92",
               "risk_assessment":{"status":"PASS"}}
    store=Store(entries, {"protected_fill:"+KEY:protected,
                          "risk_reservations":{KEY:{"reserved_risk":"620"}}})
    journal=SimpleNamespace(store=store,account_hash=ACCOUNT_HASH,robot_id="v20-obv")
    journal.reconcile_order=Mock(return_value="BROKER_ORDER_ALREADY_RECONCILED_NO_RETRANSMIT")
    journal.observe_protected_entry=Mock(return_value=protected)
    stops=[broker_order(status=stop_status)]
    if exit_status is not None:
        stops.append(broker_order(kind="REGULAR", status=exit_status,
                                  broker_id="exit-100",key=KEY+":frozen-exit"))
    snapshot=SimpleNamespace(positions={SYMBOL: pos} if pos else {},orders=stops,
                             account_hash=ACCOUNT_HASH,robot_id="v20-obv")
    reader=SimpleNamespace(snapshot=Mock(return_value=snapshot),
                           _fresh=Mock(), api=SimpleNamespace(cancel_order=Mock(return_value={"order_id":"stop-100"})))
    sender=SimpleNamespace(journal=journal,reader=reader,
                           cancel_stop_after_flat_once=Mock(return_value="CANCEL_ACK_REQUIRE_BROKER_NO_STOP_CONFIRMATION"),
                           submit_frozen_exit_once=Mock())
    return journal, sender, snapshot


class H1ParityTests(unittest.TestCase):
    def test_flat_external_close_reuses_h1_stop_cleanup_even_without_frozen_exit(self):
        journal,sender,snap=example()
        with patch("V20_TradingSystem_M15.v20_runtime.finam_live._ownership",
                   return_value=[journal.store.intents[KEY]]):
            state=_follow_existing(sender,NOW,snap)
        self.assertEqual(state,"CANCEL_ACK_REQUIRE_BROKER_NO_STOP_CONFIRMATION")
        sender.cancel_stop_after_flat_once.assert_called_once_with(key=KEY,snapshot=snap,now=NOW)
        sender.submit_frozen_exit_once.assert_not_called()

    def test_stop_filled_flat_closes_without_second_broker_post(self):
        journal,sender,snap=example(stop_status="SL_EXECUTED")
        with patch("V20_TradingSystem_M15.v20_runtime.finam_live._ownership",
                   return_value=[journal.store.intents[KEY]]):
            state=_follow_existing(sender,NOW,snap)
        self.assertEqual(state,"STOP_EXECUTED_FLAT")
        self.assertEqual(journal.store.get("flat_cleanup:"+KEY)["status"], "STOP_EXECUTED_FINAM_FLAT")
        sender.cancel_stop_after_flat_once.assert_not_called()
        self.assertNotIn(KEY,journal.store.get("risk_reservations"))

    def test_terminal_exit_with_open_position_fails_closed_stop_untouched(self):
        for exit_state in ("REJECTED","CANCELLED","EXPIRED","FILLED","EXECUTED"):
            with self.subTest(exit_state=exit_state):
                journal,sender,snap=example(pos=-2,exit_status=exit_state)
                with patch("V20_TradingSystem_M15.v20_runtime.finam_live._ownership",
                           return_value=[journal.store.intents[KEY]]):
                    with self.assertRaisesRegex(V20FinamBlocked,"V20_LIVE_EXIT_TERMINAL_POSITION_STILL_OPEN"):
                        _follow_existing(sender,NOW,snap)
                self.assertEqual(journal.store.get("execution_halt"),
                                 "FROZEN_EXIT_BROKER_TERMINAL_WITH_POSITION")
                sender.cancel_stop_after_flat_once.assert_not_called()
                sender.submit_frozen_exit_once.assert_not_called()

    def test_active_exit_with_open_position_waits_no_repost(self):
        journal,sender,snap=example(pos=-2,exit_status="NEW")
        with patch("V20_TradingSystem_M15.v20_runtime.finam_live._ownership",
                   return_value=[journal.store.intents[KEY]]):
            self.assertEqual(_follow_existing(sender,NOW,snap),"EXIT_POSTED_AWAIT_BROKER_FLAT")
        sender.submit_frozen_exit_once.assert_not_called()
        self.assertIsNone(journal.store.get("execution_halt"))

    def test_live_manual_broker_flat_cancel_only_after_exact_broker_position_proof(self):
        journal,sender,snap=example()
        transport=object.__new__(V20LiveTransport)
        transport.journal=journal
        transport.reader=sender.reader
        with patch.object(V20LiveTransport,"_permit",
                          return_value={"instrument":"USDRUBF","direction":"SHORT","max_quantity":2}):
            self.assertEqual(transport.cancel_stop_after_flat_once(
                key=KEY,snapshot=snap,now=NOW),"CANCEL_ACK_REQUIRE_BROKER_NO_STOP_CONFIRMATION")
            sender.reader.api.cancel_order.assert_called_once_with(sender.reader.account_id if hasattr(sender.reader,"account_id") else None, "stop-100")

    def test_technical_transport_manual_flat_does_not_autocancel(self):
        journal,sender,snap=example()
        transport=object.__new__(V20SingleTradeTransport)
        transport.journal=journal
        transport.reader=sender.reader
        with patch.object(V20SingleTradeTransport,"_permit",
                          return_value={"instrument":"USDRUBF","direction":"SHORT","max_quantity":2}):
            with self.assertRaisesRegex(V20FinamBlocked, "FLAT_CLEANUP_MANUAL_BROKER_PROOF_REQUIRED"):
                transport.cancel_stop_after_flat_once(key=KEY,snapshot=snap,now=NOW)
        sender.reader.api.cancel_order.assert_not_called()


if __name__=="__main__":
    unittest.main()
