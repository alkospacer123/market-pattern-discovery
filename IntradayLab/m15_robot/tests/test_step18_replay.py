"""№18 offline integration: fake FINAM broker and synthetic M15 SQLite only.

No real order transport, auth, tasks, H1 file access or live state mutation.
"""
import hashlib
import tempfile
import unittest
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

from IntradayLab.m15_robot.grid_risk import ContractAuthority, TrailingState, initial_stop
from IntradayLab.m15_robot.offline_intents import OfflineIntentLedger, M15OfflineLedgerError
from IntradayLab.m15_robot.protective_gate import BrokerProtection, decide_protection
from IntradayLab.m15_robot.risk_batch import M15BatchRiskBudget, M15BatchRiskError
from IntradayLab.m15_robot.trailing_gate import (
    propose_trail, confirm_trail, M15TrailingGateError,
)


CONTRACT = ContractAuthority(
    Decimal("1"), Decimal("10"), 1, Decimal("2000"), Decimal("2000"))
CLOCK = datetime(2026, 10, 18, 10, 30, tzinfo=timezone.utc)
KEY = "m15:USDRUBF:synthetic-01"


def broker_stop(price, covered):
    return BrokerProtection(
        "sim-broker-stop", Decimal(str(price)), 100, covered, True)


class OfflineEndToEnd(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        base = Path(self.tmp.name)
        self.kwargs = {
            "runtime_root": base / "m15",
            "h1_runtime_root": base / "h1",
            "repository_root": base / "repo",
            "m15_account_id": "M15-SIM",
            "h1_account_sha256": hashlib.sha256(b"H1-SIM").hexdigest(),
        }
        self.ledger = OfflineIntentLedger(**self.kwargs)
        self.budget = M15BatchRiskBudget(
            realized_equity=Decimal("100000"),
            available_margin_cash=Decimal("100000"),
        )

    def tearDown(self):
        self.ledger.close()
        self.tmp.cleanup()

    def prepare(self):
        stop = initial_stop("LONG", Decimal("100"), Decimal("2"), Decimal("1"))
        order = self.budget.size_and_reserve(
            instrument="USDRUBF", direction="LONG",
            entry=Decimal("100"), stop=stop, contract=CONTRACT,
        )
        self.assertEqual(order.final_quantity, 37)
        self.assertTrue(self.ledger.prepare(
            key=KEY, instrument="USDRUBF", direction="LONG",
            quantity=order.final_quantity))
        self.ledger.synthetic_ack(KEY, "sim-order-1")
        return order

    def test_complete_chain_partial_stop_full_then_trail_ack(self):
        order = self.prepare()
        self.ledger.synthetic_fill(key=KEY, fill_id="sim-fill-1",
                                   broker_order_id="sim-order-1", quantity=10, price="100")
        self.ledger.synthetic_stop_ack(key=KEY, stop_price="96",
                                       synthetic_order_id="sim-stop-1")
        old = broker_stop("96", 10)
        self.assertEqual(decide_protection(
            direction="LONG", actual_entry=Decimal("100"), atr=Decimal("2"),
            price_step=Decimal("1"), broker_position_qty=10,
            broker_stop=old, broker_stop_count=1).action, "HOLD_BROKER_CONFIRMED")
        self.ledger.synthetic_fill(key=KEY, fill_id="sim-fill-2",
                                   broker_order_id="sim-order-1", quantity=27, price="100")
        gap = decide_protection(
            direction="LONG", actual_entry=Decimal("100"), atr=Decimal("2"),
            price_step=Decimal("1"), broker_position_qty=37,
            broker_stop=old, broker_stop_count=1)
        self.assertEqual(gap.action, "REPLACE_REQUIRED_COVERAGE")
        self.assertTrue(gap.old_stop_must_remain)
        self.assertFalse(gap.new_entries_authorized)
        self.ledger.synthetic_stop_ack(key=KEY, stop_price="97",
                                       synthetic_order_id="sim-stop-2")
        updated = broker_stop("97", 37)
        current = TrailingState("USDRUBF", "LONG", Decimal("100"),
                                Decimal("97"), Decimal("100"))
        pending = propose_trail(
            confirmed=current, observed_stop=updated,
            broker_position_qty=37, completed_at=CLOCK,
            high=Decimal("115"), low=Decimal("100"), atr=Decimal("2"),
            price_step=Decimal("1"), survived_completed_bar=True)
        self.assertEqual(pending.candidate.active_stop, Decimal("108"))
        with self.assertRaisesRegex(M15TrailingGateError, "PRICE_OR_ID_MISMATCH"):
            confirm_trail(pending, observed_stop=updated, observed_stop_count=1,
                          broker_position_qty=37, price_step=Decimal("1"))
        self.assertEqual(current.active_stop, Decimal("97"))
        self.ledger.synthetic_stop_ack(key=KEY, stop_price="108",
                                       synthetic_order_id="sim-stop-3")
        proof = confirm_trail(
            pending, observed_stop=broker_stop("108", 37),
            observed_stop_count=1, broker_position_qty=37, price_step=Decimal("1"))
        self.assertEqual(proof.active_stop, Decimal("108"))
        self.assertEqual(self.ledger.filled_quantity(KEY), order.final_quantity)
        self.assertEqual(self.ledger.latest_stop(KEY)["quantity_percent"], 100)
        self.assertFalse(self.ledger.execution_authorized)

    def test_restart_preserves_existing_fill_and_latest_protection(self):
        self.prepare()
        self.ledger.synthetic_fill(key=KEY, fill_id="sim-fill-1",
                                   broker_order_id="sim-order-1", quantity=37, price="100")
        self.ledger.synthetic_stop_ack(key=KEY, stop_price="96",
                                       synthetic_order_id="sim-stop-1")
        self.ledger.close()
        self.ledger = OfflineIntentLedger(**self.kwargs)
        self.assertEqual(self.ledger.filled_quantity(KEY), 37)
        self.assertEqual(self.ledger.latest_stop(KEY)["stop_price"], "96")
        self.assertFalse(self.ledger.prepare(
            key=KEY, instrument="USDRUBF", direction="LONG", quantity=37))
        with self.assertRaisesRegex(M15OfflineLedgerError, "OCCUPIED"):
            self.ledger.prepare(key="m15:USDRUBF:synthetic-02",
                                instrument="USDRUBF", direction="LONG", quantity=1)

    def test_uncertain_entry_no_duplicate_or_unprotected_stop(self):
        stop = initial_stop("SHORT", Decimal("100"), Decimal("2"), Decimal("1"))
        size = self.budget.size_and_reserve(
            instrument="CNYRUBF", direction="SHORT",
            entry=Decimal("100"), stop=stop, contract=CONTRACT)
        self.ledger.prepare(key="m15:uncertain", instrument="CNYRUBF",
                            direction="SHORT", quantity=size.final_quantity)
        self.ledger.uncertain("m15:uncertain")
        with self.assertRaisesRegex(M15OfflineLedgerError, "FILL_BROKER_PROOF"):
            self.ledger.synthetic_fill(
                key="m15:uncertain", fill_id="sim-fill-x",
                broker_order_id="sim-order-x", quantity=1, price="100")
        with self.assertRaisesRegex(M15OfflineLedgerError, "OCCUPIED"):
            self.ledger.prepare(key="m15:other", instrument="CNYRUBF",
                                direction="SHORT", quantity=1)

    def test_go_same_cycle_n4_cannot_double_spend(self):
        tiny = M15BatchRiskBudget(
            realized_equity=Decimal("100000"),
            available_margin_cash=Decimal("3000"))
        qty1 = tiny.size_and_reserve(instrument="USDRUBF", direction="LONG",
                                     entry=Decimal("100"), stop=Decimal("96"),
                                     contract=CONTRACT)
        self.assertEqual(qty1.final_quantity, 1)
        qty2 = tiny.size_and_reserve(instrument="CNYRUBF", direction="SHORT",
                                     entry=Decimal("100"), stop=Decimal("104"),
                                     contract=CONTRACT)
        self.assertEqual(qty2.final_quantity, 0)

    def test_off_grid_stop_stays_unaccepted(self):
        self.prepare()
        self.ledger.synthetic_fill(key=KEY, fill_id="sim-fill-1",
                                   broker_order_id="sim-order-1", quantity=1, price="100")
        with self.assertRaises(ValueError):
            decide_protection(
                direction="LONG", actual_entry=Decimal("100"), atr=Decimal("2"),
                price_step=Decimal("1"), broker_position_qty=1,
                broker_stop=broker_stop("96.5", 1), broker_stop_count=1)
        self.assertIsNone(self.ledger.latest_stop(KEY))

    def test_no_real_broker_transport_in_offline_replay(self):
        self.assertFalse(hasattr(self.ledger, "place_order"))
        self.assertFalse(hasattr(self.ledger, "cancel_order"))
        self.assertFalse(self.ledger.execution_authorized)


if __name__ == "__main__":
    unittest.main()
