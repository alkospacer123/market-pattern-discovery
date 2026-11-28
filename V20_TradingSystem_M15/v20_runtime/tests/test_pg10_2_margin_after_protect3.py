"""PG10.2 F3: Protect3 successor margin reflection on disposable broker facts."""
from __future__ import annotations

from contextlib import nullcontext
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from decimal import Decimal
import unittest
from unittest.mock import Mock, patch

from TradingSystemLab.stage8_robot.broker import compact_client_order_id
from TradingSystemLab.stage8_robot.execution_grid import initial_projection
from TradingSystemLab.stage8_robot.production_broker_state import BrokerOrderView

from V20_TradingSystem_M15.v20_runtime.account_risk import AccountAuthority
from V20_TradingSystem_M15.v20_runtime.finam_execution import reserve_entry
from V20_TradingSystem_M15.v20_runtime.offline_planner import FrozenSignal, ProposedEntry
from V20_TradingSystem_M15.v20_runtime.r070_linked_sltp import (
    verify_r070_protect3_effective_stop,
)
from V20_TradingSystem_M15.v20_runtime.tests.test_r070_v20_protection_handoff import (
    R070V20HandoffTests,
)
from V20_TradingSystem_M15.v20_runtime.tp6_protect3 import levels_from_finam_fills


class Protect3MarginReflectionTests(unittest.TestCase):
    def fixture(self, mutation=None):
        helper = R070V20HandoffTests(
            methodName="test_protect3_effective_stop_resealed_after_reboot_readonly")
        d, old, proof, wire = helper.prepared_restart()
        levels = levels_from_finam_fills(
            direction="LONG", fills=[(2, "100")],
            initial_stop=proof["installed_stop"], tick="0.1")
        comment = d.entry_key + ":protect3:1r"
        new_wire = {
            **wire, "sl_price": {"value": str(levels.locked_stop_1r)},
            "comment": comment,
            "client_order_id": compact_client_order_id(comment),
        }
        record = {
            "schema": "r070.protect3.cancel_first.candidate.v1",
            "state": "PROTECTED", "account_sha256": d.reader.account_hash,
            "robot": d.reader.robot_id, "symbol": "USDRUBF@FUT",
            "entry_key": d.entry_key, "old_broker_id": old.order_id,
            "position_quantity": 2,
            "new_client_order_id": new_wire["client_order_id"],
            "new_wire": new_wire, "new_broker_id": "successor-margin-01",
        }
        successor = BrokerOrderView(
            record["new_broker_id"], "WATCHING", True, "SLTP", "USDRUBF@FUT",
            new_wire["client_order_id"], comment, new_wire["side"], new_wire.copy())
        if mutation == "unknown_transition":
            record["state"] = "NEW_POST_OUTCOME_UNKNOWN"
        elif mutation == "wrong_broker_id":
            record["new_broker_id"] = "different-broker-order"
        old_get = d.store.get.side_effect

        def get(key, default=None):
            if key == "r070_protect3:" + d.entry_key:
                return record
            if key == "session_entries":
                return {}
            return old_get(key, default)

        d.store.get = Mock(side_effect=get)
        d.store.transaction = Mock(side_effect=nullcontext)
        d.store.persist_intent = Mock(return_value=True)
        d.store.put = Mock()
        d.journal.live_runtime = True
        d.journal.strategy = "SHALLOW_PULLBACK"
        cancelled = replace(old, status="CANCELLED", active=False)
        now = datetime.now(timezone.utc)
        d.snapshot = replace(
            d.snapshot, observed_at=now,
            orders=(d.entry, cancelled, successor))
        d.now = now
        d.registry = {
            "USDRUBF": {
                "finam_symbol": "USDRUBF@FUT", "price_step": "0.1",
                "tick_value": "1", "quantity_granularity": 1,
            },
            "CNYRUBF": {
                "finam_symbol": "CNYRUBF@FUT", "price_step": "0.001",
                "tick_value": "1", "quantity_granularity": 1,
            },
        }
        price, atr = Decimal("12.000"), Decimal("0.003")
        stop, distance = initial_projection("LONG", price, price - 2 * atr, Decimal("0.001"))
        at = datetime(2026, 11, 28, 10, 15)
        d.case = dict(
            signal=FrozenSignal(
                "SHALLOW_PULLBACK", "CNYRUBF", 1,
                at - timedelta(minutes=15), atr),
            entry=ProposedEntry(
                "SHALLOW_PULLBACK", "CNYRUBF", "LONG", at, price, stop,
                distance, 30, Decimal("675"), Decimal("1500"), "PG10_2_F3"),
            authority=AccountAuthority(
                d.reader.account_id, Decimal("45000"), Decimal("35000"),
                Decimal("0.001"), Decimal("1"), Decimal("1500"), 1, Decimal("2")),
            snapshot=d.snapshot,
        )
        return d

    def prepare(self, d, *, successor_proof):
        kwargs = dict(d.case)
        if successor_proof:
            kwargs.update(reader=d.reader, now=d.now)
        captured = {}

        def measured(**kwargs):
            reservation = reserve_entry(**kwargs)
            captured["reservation"] = reservation
            return reservation

        with patch(
            "V20_TradingSystem_M15.v20_runtime.finam_execution._load_registry",
            return_value=d.registry,
        ), patch(
            "TradingSystemLab.stage8_robot.production_runtime._load_registry",
            return_value=d.registry,
        ), patch(
            "V20_TradingSystem_M15.v20_runtime.finam_execution.reserve_entry",
            side_effect=measured,
        ) as observed:
            key = d.journal.prepare_entry(**kwargs)
        authority = observed.call_args.kwargs["authority"]
        reservation = observed.call_args.kwargs["current_reservations"]
        quantity = captured["reservation"].quantity
        return key, authority, reservation, quantity

    def test_base_mechanism_double_reserves_broker_accounted_margin(self):
        d = self.fixture()
        with patch(
            "TradingSystemLab.stage8_robot.production_runtime._load_registry",
            return_value=d.registry,
        ):
            self.assertEqual(verify_r070_protect3_effective_stop(
                journal=d.journal, reader=d.reader, snapshot=d.snapshot,
                entry_key=d.entry_key, now=d.now).order_id, "successor-margin-01")
        _, authority, reservations, quantity = self.prepare(d, successor_proof=False)
        self.assertEqual(quantity, 21)
        self.assertEqual(authority.margin_reflected_client_ids, ())
        self.assertEqual(reservations[0].reserved_margin, Decimal("2000"))

    def test_verified_successor_releases_only_broker_reflected_margin(self):
        d = self.fixture()
        original_stop = d.store.intent(d.entry_key + ":stop")
        _, authority, _, quantity = self.prepare(d, successor_proof=True)
        self.assertEqual(quantity, 23)
        self.assertEqual(
            authority.margin_reflected_client_ids,
            (compact_client_order_id(d.entry_key),))
        self.assertEqual(d.store.intent(d.entry_key + ":stop"), original_stop)
        self.assertNotIn("r070_protect3", str(d.store.put.call_args_list))

    def test_unknown_or_mismatched_successor_keeps_conservative_reserve(self):
        for mutation in ("unknown_transition", "wrong_broker_id"):
            with self.subTest(mutation=mutation):
                d = self.fixture(mutation)
                _, authority, _, quantity = self.prepare(d, successor_proof=True)
                self.assertEqual(quantity, 21)
                self.assertEqual(authority.margin_reflected_client_ids, ())

    def test_missing_fresh_reader_cannot_release_margin(self):
        d = self.fixture()
        _, authority, _, quantity = self.prepare(d, successor_proof=False)
        self.assertEqual(quantity, 21)
        self.assertEqual(authority.margin_reflected_client_ids, ())


if __name__ == "__main__":
    unittest.main()
