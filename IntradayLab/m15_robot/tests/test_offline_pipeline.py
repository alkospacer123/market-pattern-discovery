"""H1-style M15 rehearsal: broker clean -> sizing -> durable intent -> fill -> stop.

Only synthetic fake read-side FINAM API, synthetic ACKs and local SQLite.
Not an end-to-end proof of real FINAM executions or LIVE readiness.
"""
import hashlib
import tempfile
import unittest
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

from IntradayLab.m15_robot.grid_risk import ContractAuthority, initial_stop, size_r15
from IntradayLab.m15_robot.shadow_state import ShadowLedger
from IntradayLab.m15_robot.shadow_service import observe_broker_once
from IntradayLab.m15_robot.offline_intents import OfflineIntentLedger, M15OfflineLedgerError


class FakeReadOnlyBroker:
    def __init__(self):
        self.total_reads = 0
        self.order_posts = 0
    def account(self, account_id):
        self.total_reads += 1
        return {"account_id": "M15-ACCOUNT", "status": "ACCOUNT_ACTIVE",
                "positions": []}
    def orders(self, account_id):
        self.total_reads += 1
        return {"orders": []}
    def place_order(self, *args, **kwargs):
        self.order_posts += 1
        raise AssertionError("REAL_ORDER_FORBIDDEN")


class OfflineCycle(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        base = Path(self.temp.name)
        self.args = {
            "runtime_root": base / "m15",
            "h1_runtime_root": base / "h1",
            "repository_root": base / "repo",
            "m15_account_id": "M15-ACCOUNT",
            "h1_account_sha256": hashlib.sha256(b"H1-ACCOUNT").hexdigest(),
        }
        self.shadow = ShadowLedger(**self.args)
        self.ledger = OfflineIntentLedger(**self.args)
        self.broker = FakeReadOnlyBroker()

    def tearDown(self):
        self.ledger.close()
        self.shadow.close()
        self.temp.cleanup()

    def cycle(self):
        return observe_broker_once(
            ledger=self.shadow, read_api=self.broker,
            m15_account_id="M15-ACCOUNT",
            observed_at=datetime(2026, 10, 16, 11, 0, tzinfo=timezone.utc),
        )

    def test_clean_broker_then_durable_full_fill_and_percentage_stop(self):
        state = self.cycle()
        self.assertEqual(state["status"], "HEALTHY_READONLY")
        self.assertFalse(state["execution_authorized"])
        terms = ContractAuthority(
            price_step=Decimal("1"), tick_value=Decimal("10"),
            trade_lot_size=1, long_initial_margin=Decimal("2000"),
            short_initial_margin=Decimal("2000"),
        )
        stop = initial_stop("LONG", Decimal("100"), Decimal("2"), terms.price_step)
        size = size_r15(realized_equity=Decimal("100000"), entry=Decimal("100"),
                        stop=stop, contract=terms, direction="LONG",
                        available_margin_cash=Decimal("100000"))
        self.assertEqual(stop, Decimal("96"))
        self.assertEqual(size.risk_budget, Decimal("1500"))
        self.assertEqual(size.final_quantity, 37)
        key = "m15:USDRUBF:20261016T1100"
        self.assertTrue(self.ledger.prepare(
            key=key, instrument="USDRUBF", direction="LONG",
            quantity=size.final_quantity,
        ))
        self.ledger.synthetic_ack(key, "sim-order-1")
        self.ledger.synthetic_fill(
            key=key, fill_id="sim-fill-1", broker_order_id="sim-order-1",
            quantity=10, price="100",
        )
        self.assertEqual(self.ledger.synthetic_stop_ack(
            key=key, stop_price="96", synthetic_order_id="sim-stop-1",
        ), 0)
        self.ledger.synthetic_fill(
            key=key, fill_id="sim-fill-2", broker_order_id="sim-order-1",
            quantity=27, price="100",
        )
        self.assertEqual(self.ledger.intent(key)["status"], "FILLED")
        self.assertEqual(self.ledger.filled_quantity(key), 37)
        self.assertEqual(self.ledger.latest_stop(key)["quantity_percent"], 100)
        self.assertEqual(self.broker.order_posts, 0)
        self.assertEqual(self.broker.total_reads, 2)

    def test_restart_rejects_duplicate_position(self):
        self.cycle()
        self.ledger.prepare(key="m15:signal-a", instrument="CNYRUBF",
                            direction="SHORT", quantity=1)
        self.ledger.close()
        self.ledger = OfflineIntentLedger(**self.args)
        self.assertFalse(self.ledger.prepare(
            key="m15:signal-a", instrument="CNYRUBF",
            direction="SHORT", quantity=1))
        with self.assertRaisesRegex(M15OfflineLedgerError, "OCCUPIED"):
            self.ledger.prepare(key="m15:signal-b", instrument="CNYRUBF",
                                direction="SHORT", quantity=1)
        self.assertEqual(self.broker.order_posts, 0)

    def test_uncertain_submission_blocks_new_entry(self):
        self.cycle()
        self.ledger.prepare(key="m15:signal-a", instrument="GLDRUBF",
                            direction="LONG", quantity=2)
        self.ledger.uncertain("m15:signal-a")
        with self.assertRaisesRegex(M15OfflineLedgerError, "OCCUPIED"):
            self.ledger.prepare(key="m15:signal-b", instrument="GLDRUBF",
                                direction="LONG", quantity=2)
        self.assertEqual(self.broker.order_posts, 0)


if __name__ == "__main__":
    unittest.main()
