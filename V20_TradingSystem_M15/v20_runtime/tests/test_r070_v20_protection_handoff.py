"""R070 read-only handoff: exact V20 journal and H1 FINAM fill proof, NO POST."""
from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from hashlib import sha256
from types import SimpleNamespace
from unittest import TestCase, main, skipUnless
import os
from unittest.mock import Mock, patch
import json

from TradingSystemLab.stage8_robot.broker import compact_client_order_id
from TradingSystemLab.stage8_robot.production_broker_state import BrokerOrderView
from V20_TradingSystem_M15.v20_runtime.account_risk import RiskReservation
from V20_TradingSystem_M15.v20_runtime.finam_execution import (
    LiveAccountSnapshot, V20FinamReadAdapter, V20TradeJournal,
)
from V20_TradingSystem_M15.v20_runtime.r070_linked_sltp import (
    stage_r070_protection_from_v20, verify_r070_tp6_after_restart,
    verify_r070_protect3_effective_stop,
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

    def prepared_restart(self, *, direction="LONG"):
        d = self.fixture(direction=direction)
        choice = self.choose(d)
        wire = choice.wire
        old_intent = d.store.intent.side_effect
        old_get = d.store.get.side_effect
        broker_stop = BrokerOrderView(
            "finam-sltp-456", "WATCHING", True, "SLTP",
            "USDRUBF@FUT", wire["client_order_id"], wire["comment"],
            wire["side"], wire.copy())
        d.store.intent = Mock(side_effect=lambda key:
            {"status": "ACK", "broker_order_id": broker_stop.order_id,
             "payload": {
                 "kind": "STOP", "entry_key": d.entry_key,
                 "wire": wire,
                 "account_sha256": d.reader.account_hash,
                 "observed_position_quantity": (
                     2 if direction == "LONG" else -2),
             }}
            if key == d.entry_key + ":stop" else
            {"status": "RECONCILED",
             "broker_order_id": d.entry.order_id,
             "payload": old_intent(d.entry_key)["payload"]}
            if key == d.entry_key else None)
        proof = {
            "account_sha256": d.reader.account_hash,
            "broker_order_id": d.entry.order_id,
            "broker_stop_id": broker_stop.order_id,
            "broker_stop_percent": "100",
            "filled_quantity": 2,
            "average_exact": "100",
            "installed_stop": str(choice.levels.initial_stop),
            "risk_assessment": {"status": "PASS", "stop_conforms": True},
        }
        d.store.get = Mock(side_effect=lambda key, default=None:
            proof if key == "protected_fill:" + d.entry_key
            else old_get(key, default))
        d.store.fills_for_order = Mock(return_value=[
            {"fill_id": "finam:" + d.reader.account_hash + ":" +
             f["trade_id_sha256"],
             "broker_trade_id_sha256": f["trade_id_sha256"],
             "quantity": str(f["quantity"]), "price": f["price"],
             "trade_id": d.entry_key, "entry_key": d.entry_key,
             "broker_order_id": d.entry.order_id,
             "account_sha256": d.reader.account_hash}
            for f in d.history["matched_unique_fills"]])
        d.snapshot = replace(d.snapshot, orders=(d.entry, broker_stop))
        d.reader.inspect_entry_fills.reset_mock()
        return d, broker_stop, proof, wire

    def restart(self, d):
        with patch(
            "TradingSystemLab.stage8_robot.production_runtime._load_registry",
            return_value=d.registry):
            return verify_r070_tp6_after_restart(
                journal=d.journal, reader=d.reader, snapshot=d.snapshot,
                entry_key=d.entry_key, now=d.now)

    def test_protect3_effective_stop_resealed_after_reboot_readonly(self):
        from V20_TradingSystem_M15.v20_runtime.tp6_protect3 import (
            levels_from_finam_fills,
        )
        for direction in ("LONG", "SHORT"):
            with self.subTest(direction=direction):
                d, old, proof, wire = self.prepared_restart(direction=direction)
                levels = levels_from_finam_fills(
                    direction=direction, fills=[(2, "100")],
                    initial_stop=proof["installed_stop"], tick="0.1")
                updated = {
                    **wire, "sl_price": {"value": str(levels.locked_stop_1r)},
                    "comment": d.entry_key + ":protect3:1r",
                    "client_order_id": compact_client_order_id(
                        d.entry_key + ":protect3:1r"),
                }
                rec = {
                    "schema": "r070.protect3.cancel_first.candidate.v1",
                    "state": "PROTECTED", "account_sha256": d.reader.account_hash,
                    "robot": d.reader.robot_id, "symbol": "USDRUBF@FUT",
                    "entry_key": d.entry_key, "old_broker_id": old.order_id,
                    "position_quantity": 2 if direction == "LONG" else -2,
                    "new_client_order_id": updated["client_order_id"],
                    "new_wire": updated, "new_broker_id": "new-sltp-789",
                }
                old_get = d.store.get.side_effect
                d.store.get = Mock(
                    side_effect=lambda key, default=None:
                    rec if key == "r070_protect3:" + d.entry_key
                    else old_get(key, default))
                successor = BrokerOrderView(
                    "new-sltp-789", "WATCHING", True, "SLTP",
                    "USDRUBF@FUT", updated["client_order_id"],
                    updated["comment"], updated["side"], updated.copy())
                cancelled = replace(old, status="CANCELLED", active=False)
                d.snapshot = replace(d.snapshot, orders=(d.entry, cancelled, successor))
                def prove():
                    with patch(
                        "TradingSystemLab.stage8_robot.production_runtime._load_registry",
                        return_value=d.registry):
                        return verify_r070_protect3_effective_stop(
                            journal=d.journal, reader=d.reader, snapshot=d.snapshot,
                            entry_key=d.entry_key, now=d.now)
                self.assertEqual(prove(), successor)
                d.store.put.assert_not_called()
                d.reader.inspect_entry_fills.assert_not_called()

                # An old stop still live => two close orders, NEVER protected.
                d.snapshot = replace(d.snapshot, orders=(d.entry, old, successor))
                with self.assertRaises(TP6Protect3Unsafe):
                    prove()
                d.snapshot = replace(d.snapshot, orders=(d.entry, cancelled, successor))

                # Unknown POST, changed stop, position, wrong broker ID =>
                # no claims of broker protection or new orders.
                for state in ("CANCEL_ACK_UNVERIFIED", "NEW_POST_OUTCOME_UNKNOWN"):
                    rec["state"] = state
                    with self.assertRaisesRegex(
                            TP6Protect3Unsafe, "R070_EFFECTIVE_STOP_DURABLE_PROOF_INVALID"):
                        prove()
                rec["state"] = "PROTECTED"
                rec["new_broker_id"] = "foreign-id"
                with self.assertRaises(TP6Protect3Unsafe):
                    prove()
                rec["new_broker_id"] = "new-sltp-789"
                d.snapshot = replace(
                    d.snapshot, positions={"USDRUBF@FUT": 1})
                with self.assertRaisesRegex(
                        TP6Protect3Unsafe, "R070_EFFECTIVE_STOP_POSITION_CHANGED"):
                    prove()
                d.snapshot = replace(
                    d.snapshot, positions={"USDRUBF@FUT": rec["position_quantity"]})
                rec["new_wire"] = {**updated, "tp_price": {"value": "200"}}
                with self.assertRaisesRegex(
                        TP6Protect3Unsafe, "R070_EFFECTIVE_STOP_LEVELS_OR_FILLS_UNVERIFIED"):
                    prove()
                d.store.put.assert_not_called()

    @skipUnless(os.environ.get("R070_PROTECT3_FLAT_PATCH_ACTIVE") == "1",
                "ephemeral flat-cleanup patch required; production SHA unchanged")
    def test_staged_broker_flat_cancels_only_successor_sltp(self):
        from V20_TradingSystem_M15.v20_runtime.finam_live import V20LiveJournal, _ownership
        from contextlib import nullcontext
        from V20_TradingSystem_M15.v20_runtime.finam_execution import (
            V20SingleTradeTransport, V20FinamBlocked,
        )
        from V20_TradingSystem_M15.v20_runtime.tp6_protect3 import (
            levels_from_finam_fills,
        )
        for empty_client in (False, True):
            with self.subTest(empty_client=empty_client):
                d, old, proof, wire = self.prepared_restart()
                levels = levels_from_finam_fills(
                    direction="LONG", fills=[(2, "100")],
                    initial_stop=proof["installed_stop"], tick="0.1")
                comment = d.entry_key + ":protect3:1r"
                new_wire = {**wire,
                    "sl_price": {"value": str(levels.locked_stop_1r)},
                    "comment": comment,
                    "client_order_id": compact_client_order_id(comment)}
                replacement = {
                    "schema": "r070.protect3.cancel_first.candidate.v1",
                    "state": "PROTECTED", "account_sha256": d.reader.account_hash,
                    "robot": d.reader.robot_id, "symbol": "USDRUBF@FUT",
                    "entry_key": d.entry_key, "old_broker_id": old.order_id,
                    "position_quantity": 2,
                    "new_client_order_id": new_wire["client_order_id"],
                    "new_wire": new_wire, "new_broker_id": "successor-789"}
                original_get = d.store.get.side_effect
                d.store.get = Mock(side_effect=lambda k, default=None:
                    replacement if k == "r070_protect3:" + d.entry_key
                    else original_get(k, default))
                successor = BrokerOrderView(
                    "successor-789", "WATCHING", True, "SLTP",
                    "USDRUBF@FUT",
                    "" if empty_client else new_wire["client_order_id"],
                    comment, new_wire["side"], new_wire.copy())
                d.snapshot = replace(
                    d.snapshot,
                    positions={"USDRUBF@FUT": 0},
                    orders=(d.entry, replace(old, active=False, status="CANCELLED"),
                            successor))
                d.reader.snapshot = Mock(return_value=d.snapshot)
                api = SimpleNamespace(cancel_order=Mock(return_value={}))
                d.reader.api = api
                # The LIVE ownership pass runs BEFORE flat cleanup.
                # It must recognize the replacement even at position=0.
                entry = d.store.intent(d.entry_key)
                row = {"idempotency_key": d.entry_key, "status": "RECONCILED",
                       "payload": {**entry["payload"],
                                   "mode": "PRETRADE_NOT_AUTHORIZED",
                                   "robot_id": d.reader.robot_id,
                                   "account_sha256": d.reader.account_hash}}
                d.store.all_intents = Mock(return_value=[row])
                live = V20LiveJournal.__new__(V20LiveJournal)
                live.store, live.robot_id, live.account_hash = (
                    d.store, d.reader.robot_id, d.reader.account_hash)
                with patch(
                    "V20_TradingSystem_M15.v20_runtime.finam_live._load_registry",
                    return_value=d.registry,
                ):
                    self.assertEqual(_ownership(
                        live, d.snapshot, reader=d.reader, now=d.now), [row])
                d.store.transaction = Mock(side_effect=lambda: nullcontext())
                durable = {}
                original_intent = d.store.intent.side_effect
                d.store.intent = Mock(
                    side_effect=lambda k: durable.get(k, original_intent(k)))
                def persist(k, payload):
                    durable[k] = {"status": "INTENT_PERSISTED",
                                  "payload": payload, "broker_order_id": None}
                    return True
                def transition(k, status, broker_order_id=None):
                    durable[k]["status"] = status
                    durable[k]["broker_order_id"] = broker_order_id
                d.store.persist_intent = Mock(side_effect=persist)
                d.store.transition_intent = Mock(side_effect=transition)
                sender = SimpleNamespace(
                    journal=d.journal, reader=d.reader, _live_mode=True,
                    _permit=Mock(return_value={}))
                def cancel():
                    return V20SingleTradeTransport.cancel_stop_after_flat_once(
                        sender, key=d.entry_key, snapshot=d.snapshot, now=d.now)
                self.assertEqual(cancel(),
                                 "CANCEL_ACK_REQUIRE_BROKER_NO_STOP_CONFIRMATION")
                api.cancel_order.assert_called_once_with(d.reader.account_id, "successor-789")
                intent = durable[d.entry_key + ":cancel-after-flat"]
                self.assertEqual(intent["payload"]["broker_order_id"], "successor-789")
                self.assertEqual(intent["status"], "ACK")
                with self.assertRaisesRegex(
                        V20FinamBlocked, "FLAT_CANCEL_ALREADY_ATTEMPTED_NO_RETRANSMIT"):
                    cancel()
                self.assertEqual(api.cancel_order.call_count, 1)

                # Reset only persisted cancel state; an UNKNOWN transition
                # or a foreign successor must never dispatch another CANCEL.
                durable.clear()
                replacement["state"] = "NEW_POST_OUTCOME_UNKNOWN"
                with self.assertRaisesRegex(
                        V20FinamBlocked, "R070_FLAT_CLEANUP_UNSETTLED_ORDERS"):
                    cancel()
                replacement["state"] = "PROTECTED"
                replacement["new_broker_id"] = "foreign-order"
                with self.assertRaisesRegex(
                        V20FinamBlocked, "R070_FLAT_CLEANUP_REPLACED_STOP_INVALID"):
                    cancel()
                self.assertEqual(api.cancel_order.call_count, 1)

    @skipUnless(os.environ.get("R070_PROTECT3_PATCH_ACTIVE") == "1",
                "ephemeral broker-ID patch required; LIVE source unchanged")
    def test_staged_protect3_new_broker_id_is_owned_and_sealed(self):
        from V20_TradingSystem_M15.v20_runtime.finam_live import (
            V20LiveJournal, _ownership, _verify_sealed_protection,
        )
        from V20_TradingSystem_M15.v20_runtime.finam_execution import V20FinamBlocked
        from V20_TradingSystem_M15.v20_runtime.tp6_protect3 import (
            levels_from_finam_fills,
        )
        d, old, proof, wire = self.prepared_restart()
        levels = levels_from_finam_fills(
            direction="LONG", fills=[(2, "100")],
            initial_stop=proof["installed_stop"], tick="0.1")
        new_comment = d.entry_key + ":protect3:1r"
        new_wire = {
            **wire, "sl_price": {"value": str(levels.locked_stop_1r)},
            "comment": new_comment,
            "client_order_id": compact_client_order_id(new_comment),
        }
        record = {
            "schema": "r070.protect3.cancel_first.candidate.v1",
            "state": "PROTECTED", "account_sha256": d.reader.account_hash,
            "robot": d.reader.robot_id, "symbol": "USDRUBF@FUT",
            "entry_key": d.entry_key, "old_broker_id": old.order_id,
            "position_quantity": 2,
            "new_client_order_id": new_wire["client_order_id"],
            "new_wire": new_wire, "new_broker_id": "successor-sltp-01",
        }
        old_get = d.store.get.side_effect
        d.store.get = Mock(side_effect=lambda key, default=None:
            record if key == "r070_protect3:" + d.entry_key
            else old_get(key, default))
        successor = BrokerOrderView(
            "successor-sltp-01", "WATCHING", True, "SLTP",
            "USDRUBF@FUT", new_wire["client_order_id"],
            new_comment, new_wire["side"], new_wire.copy())
        cancelled = replace(old, active=False, status="CANCELLED")
        d.snapshot = replace(
            d.snapshot, orders=(d.entry, cancelled, successor))
        original = d.store.intent(d.entry_key)
        row = {
            "idempotency_key": d.entry_key,
            "status": "RECONCILED",
            "broker_order_id": d.entry.order_id,
            "payload": {
                **original["payload"], "mode": "PRETRADE_NOT_AUTHORIZED",
                "robot_id": d.reader.robot_id,
                "account_sha256": d.reader.account_hash,
            },
        }
        d.store.all_intents = Mock(return_value=[row])
        live = V20LiveJournal.__new__(V20LiveJournal)
        live.store = d.store
        live.robot_id = d.reader.robot_id
        live.account_hash = d.reader.account_hash

        def verify():
            with patch(
                "V20_TradingSystem_M15.v20_runtime.finam_live._load_registry",
                return_value=d.registry,
            ), patch(
                "TradingSystemLab.stage8_robot.production_runtime._load_registry",
                return_value=d.registry,
            ):
                self.assertEqual(_ownership(
                    live, d.snapshot, reader=d.reader, now=d.now), [row])
                _verify_sealed_protection(
                    live, d.reader, d.snapshot, d.now, row)

        verify()
        self.assertEqual(d.reader.inspect_protective_stop.call_count, 0)
        # FINAM can omit a WATCHING SLTP's client_order_id.
        d.snapshot = replace(
            d.snapshot, orders=(d.entry, cancelled,
                                replace(successor, client_order_id="")))
        verify()
        d.snapshot = replace(
            d.snapshot, orders=(d.entry, cancelled, successor))
        record["state"] = "NEW_POST_OUTCOME_UNKNOWN"
        with self.assertRaises(V20FinamBlocked):
            verify()
        record["state"] = "PROTECTED"
        d.snapshot = replace(
            d.snapshot, orders=(d.entry, old, successor))
        with self.assertRaises(V20FinamBlocked):
            verify()
        d.store.put.assert_not_called()

    def test_sealed_tp6_survives_restart_without_trades_get_or_sqlite_write(self):
        for side in ("LONG", "SHORT"):
            with self.subTest(side=side):
                d, order, proof, wire = self.prepared_restart(direction=side)
                self.assertEqual(self.restart(d), order)
                d.store.fills_for_order.assert_called_once_with(d.entry.order_id)
                d.reader.inspect_entry_fills.assert_not_called()
                d.store.put.assert_not_called()

    def test_restart_rejects_plain_sl_missing_tp_or_wrong_broker_tp(self):
        d, order, proof, wire = self.prepared_restart()
        mutated = dict(wire)
        mutated.pop("quantity_tp")
        previous = d.store.intent.side_effect
        d.store.intent = Mock(side_effect=lambda key:
            {**previous(key), "payload": {
                **previous(key)["payload"], "wire": mutated}}
            if key == d.entry_key + ":stop" else previous(key))
        with self.assertRaisesRegex(
                TP6Protect3Unsafe, "R070_RESTART_STOP_INTENT_NOT_LINKED_TP6"):
            self.restart(d)
        d, order, proof, wire = self.prepared_restart()
        amended = {**wire, "tp_price": {"value": "111"}}
        d.snapshot = replace(d.snapshot, orders=(
            d.entry, replace(order, request=amended)))
        with self.assertRaises(TP6Protect3Unsafe):
            self.restart(d)
        d.store.put.assert_not_called()

    def test_restart_rejects_tampered_fills_partial_and_second_order(self):
        d, order, proof, wire = self.prepared_restart()
        modified = d.store.fills_for_order.return_value.copy()
        modified[0] = {**modified[0], "price": "101"}
        d.store.fills_for_order.return_value = modified
        with self.assertRaisesRegex(
                TP6Protect3Unsafe, "R070_RESTART_FILL_VWAP_OR_QUANTITY_CHANGED"):
            self.restart(d)
        d, order, proof, wire = self.prepared_restart()
        d.snapshot = replace(d.snapshot, positions={"USDRUBF@FUT": 1})
        with self.assertRaisesRegex(
                TP6Protect3Unsafe, "R070_RESTART_POSITION_NOT_FULL"):
            self.restart(d)
        d, order, proof, wire = self.prepared_restart()
        child = BrokerOrderView(
            "trigger-child", "NEW", True, "REGULAR", "USDRUBF@FUT",
            "child", "executing", "SIDE_SELL", {"quantity": {"value": "2"}})
        d.snapshot = replace(d.snapshot, orders=(
            *d.snapshot.orders, child))
        with self.assertRaisesRegex(
                TP6Protect3Unsafe, "R070_SLTP_ACTIVE_CHILD_OR_OTHER_ORDER_UNVERIFIED"):
            self.restart(d)
        d.store.put.assert_not_called()

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

    def test_existing_stop_with_competing_broker_child_cannot_be_certified(self):
        d = self.fixture(protected=True)
        child = BrokerOrderView(
            "triggered-child", "NEW", True, "REGULAR", "USDRUBF@FUT",
            "child-id", "triggered", "SIDE_SELL",
            {"quantity": {"value": "2"}})
        d.snapshot = replace(d.snapshot, orders=(*d.snapshot.orders, child))
        with self.assertRaisesRegex(
                TP6Protect3Unsafe, "R070_V20_EXISTING_STOP_OTHER_ACTIVE_ORDER"):
            self.choose(d)
        d.reader.inspect_entry_fills.assert_not_called()
        d.store.put.assert_not_called()

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
