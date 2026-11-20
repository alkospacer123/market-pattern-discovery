"""R070 candidate-only real H1 one-shot transport test.

This module MUST run ONLY in Windows CI after temporary application of
V20-08/r070-tp6-one-shot-candidate.patch. The original SHA-pinned V20
execution file is restored immediately afterward. All broker operations
are mocks; no tokens, FINAM requests or LIVE SQLite are used.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal
from hashlib import sha256
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest import TestCase, main
from unittest.mock import Mock, patch
import json

from TradingSystemLab.stage8_robot.broker import compact_client_order_id
from TradingSystemLab.stage8_robot.production_broker_state import BrokerOrderView
from TradingSystemLab.stage8_robot.state import StateStore
from V20_TradingSystem_M15.v20_runtime.account_risk import RiskReservation
from V20_TradingSystem_M15.v20_runtime.finam_execution import (
    V20FinamBlocked, V20FinamReadAdapter, V20SingleTradeTransport,
    V20TradeJournal, LiveAccountSnapshot,
)


class R070OneShotCandidateTests(TestCase):
    def setup_scenario(self, tmp, *, direction="LONG", partial=False, uncertain=False):
        account = "synthetic-account-01"
        account_hash = sha256(account.encode()).hexdigest()
        robot = "v20-shallow"
        key = f"v20:{robot}:{account_hash[:16]}:synthetic"
        qty = 1 if partial else 2
        signed = qty if direction == "LONG" else -qty
        stop = Decimal("98") if direction == "LONG" else Decimal("102")
        now = datetime.now(timezone.utc).replace(microsecond=0)
        store = StateStore(Path(tmp) / "test-r070.sqlite")
        registry = {"USDRUBF": {
            "finam_symbol": "USDRUBF@FUT", "price_step": "0.1",
        }}
        reservation = RiskReservation(
            account, key, "USDRUBF", direction, 2, Decimal("100"),
            stop, Decimal("1"), Decimal("0.1"), Decimal("1"),
            Decimal("1000"), Decimal("0"), Decimal("40"),
            Decimal("2000"), Decimal("45000"))
        entry_payload = {
            "kind": "ENTRY", "symbol": "USDRUBF",
            "finam_symbol": "USDRUBF@FUT",
            "quantity": 2, "direction": direction,
            "reference_entry": "100", "atr14": "1",
        }
        self.assertTrue(store.persist_intent(key, entry_payload))
        store.transition_intent(key, "ACK", "finam-entry-123")
        store.put("risk_reservations", {key: reservation.record()})
        store.put("entry_submission:" + key, {
            "account_sha256": account_hash,
            "submitted_at": (now-timedelta(minutes=2)).isoformat(),
        })
        facts = [
            {"trade_id_sha256": sha256(f"test-fill-{i}".encode()).hexdigest(),
             "quantity": 1, "price": "100", "utc_seconds": 10000+i,
             "nanoseconds": 0, "account_trade_currency": "RUB"}
            for i in range(qty)
        ]
        facts.sort(key=lambda x: x["trade_id_sha256"])
        history = {
            "authority_scope": "READONLY_DIAGNOSTIC_ONLY_NO_RUNTIME_HANDOFF",
            "quantity_observation": (
                "PARTIAL_REQUEST_MATCHED" if partial else "FULL_REQUEST_MATCHED"),
            "matched_quantity": qty, "matched_unique_fills": facts,
            "fill_set_sha256": sha256(json.dumps(
                facts, sort_keys=True, separators=(",", ":")).encode()).hexdigest(),
            "weighted_price_exact": {"numerator": "100", "denominator": "1"},
        }
        entry_order = BrokerOrderView(
            "finam-entry-123", "PARTIALLY_FILLED" if partial else "FILLED",
            partial, "REGULAR", "USDRUBF@FUT", compact_client_order_id(key),
            None, "SIDE_BUY" if direction == "LONG" else "SIDE_SELL",
            {"quantity": {"value": "2"}},
        )
        snapshot = LiveAccountSnapshot(
            robot, account_hash, now, Decimal("45000"), Decimal("35000"),
            {"USDRUBF@FUT": signed}, (entry_order,),
        )
        journal = V20TradeJournal.__new__(V20TradeJournal)
        journal.robot_id = robot
        journal.account_hash = account_hash
        journal.store = store
        reader = V20FinamReadAdapter.__new__(V20FinamReadAdapter)
        reader.robot_id = robot
        reader.account_id = account
        reader.account_hash = account_hash
        reader._fresh = Mock()
        reader.snapshot = Mock(return_value=snapshot)
        reader.inspect_entry_fills = Mock(return_value=history)
        sent = []
        def place_sltp(received_account, wire):
            self.assertEqual(received_account, account)
            one_shot = store.intent(key + ":stop")
            self.assertIsNotNone(one_shot)
            self.assertEqual(one_shot["status"], "UNCERTAIN")
            self.assertEqual(one_shot["payload"]["wire"], wire)
            sent.append(wire.copy())
            if uncertain:
                raise TimeoutError("SIMULATED_BROKER_UNKNOWN_POST")
            return {"order_id": "finam-sltp-456"}
        reader.api = SimpleNamespace(place_sltp_order=Mock(side_effect=place_sltp))
        sender = SimpleNamespace(
            reader=reader, journal=journal,
            _permit=Mock(return_value={
                "instrument": "USDRUBF", "direction": direction,
            }))
        return SimpleNamespace(
            sender=sender, reader=reader, journal=journal, store=store,
            key=key, snapshot=snapshot, now=now, stop=stop,
            sent=sent, registry=registry,
        )

    def run_transport(self, d):
        with patch(
            "V20_TradingSystem_M15.v20_runtime.finam_execution._load_registry",
            return_value=d.registry,
        ):
            return V20SingleTradeTransport.submit_protection_once(
                d.sender, key=d.key, snapshot=d.snapshot, stop_price=d.stop,
                now=d.now)

    def test_full_long_and_short_one_post_with_durable_linked_tp6(self):
        for direction in ("LONG", "SHORT"):
            with self.subTest(direction=direction), TemporaryDirectory() as tmp:
                d = self.setup_scenario(tmp, direction=direction)
                try:
                    self.assertEqual(self.run_transport(d), "finam-sltp-456")
                    self.assertEqual(len(d.sent), 1)
                    wire = d.sent[0]
                    self.assertEqual(wire["quantity_sl"], {"value": "100"})
                    self.assertEqual(wire["quantity_tp"], {"value": "100"})
                    self.assertEqual(wire["tp_qty_measure"], "SLTP_QTY_MEASURE_PERCENT")
                    self.assertEqual(
                        Decimal(wire["tp_price"]["value"]),
                        Decimal("112") if direction == "LONG" else Decimal("88"))
                    self.assertEqual(d.store.intent(d.key + ":stop")["status"], "ACK")
                    with self.assertRaisesRegex(V20FinamBlocked,
                                                "STOP_ALREADY_ATTEMPTED_NO_RETRANSMIT"):
                        self.run_transport(d)
                    self.assertEqual(len(d.sent), 1)
                finally:
                    d.store.close()

    def test_partial_fill_posts_original_stop_without_tp(self):
        with TemporaryDirectory() as tmp:
            d = self.setup_scenario(tmp, partial=True)
            try:
                self.assertEqual(self.run_transport(d), "finam-sltp-456")
                self.assertEqual(len(d.sent), 1)
                self.assertNotIn("tp_price", d.sent[0])
                self.assertEqual(d.sent[0]["quantity_sl"], {"value": "100"})
                self.assertEqual(d.store.intent(d.key + ":stop")["status"], "ACK")
            finally:
                d.store.close()

    def test_unknown_stop_post_is_checkpointed_and_never_retried(self):
        with TemporaryDirectory() as tmp:
            d = self.setup_scenario(tmp, uncertain=True)
            try:
                with self.assertRaisesRegex(TimeoutError, "SIMULATED_BROKER_UNKNOWN_POST"):
                    self.run_transport(d)
                self.assertEqual(len(d.sent), 1)
                self.assertEqual(d.store.intent(d.key + ":stop")["status"], "UNCERTAIN")
                self.assertEqual(d.store.get("execution_halt"),
                                 "STOP_POST_OUTCOME_UNVERIFIED")
                with self.assertRaisesRegex(V20FinamBlocked,
                                            "STOP_ALREADY_ATTEMPTED_NO_RETRANSMIT"):
                    self.run_transport(d)
                self.assertEqual(len(d.sent), 1)
            finally:
                d.store.close()


if __name__ == "__main__":
    main()
