"""Focused 08.1 H1 SQLite order-state regression; no network, no orders."""
from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from TradingSystemLab.stage8_robot.broker import compact_client_order_id
from TradingSystemLab.stage8_robot.production_broker_state import order_views

from V20_TradingSystem_M15.v20_runtime.finam_execution import (
    LiveAccountSnapshot, V20FinamBlocked, V20TradeJournal,
)

ACCOUNT = "isolated-finam-regression-account"
ROBOT = "v20-obv"
ACCOUNT_HASH = hashlib.sha256(ACCOUNT.encode()).hexdigest()


class DurableOrderStateTests(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / "v20lab"
        self.root.mkdir()

    def setup_case(self, journal, status, *, broker_id="broker-order-a"):
        key = f"v20:{ROBOT}:{ACCOUNT_HASH[:16]}:synthetic1"
        wire = {
            "symbol": "CNYRUBF@RTSX",
            "side": "SIDE_BUY",
            "type": "ORDER_TYPE_MARKET",
            "quantity": {"value": "2"},
            "client_order_id": compact_client_order_id(key),
        }
        self.assertTrue(journal.store.persist_intent(
            key, {"mode": "PRETRADE_NOT_AUTHORIZED", "wire": wire},
        ))
        journal.store.transition_intent(key, status, "broker-order-a")
        broker_order = order_views({"orders": [{
            "order_id": broker_id,
            "status": "PARTIAL_FILL",
            "order": wire,
        }]})
        snapshot = LiveAccountSnapshot(
            ROBOT, ACCOUNT_HASH, datetime.now(timezone.utc),
            realized_equity=Decimal("45000"), available_cash=Decimal("43000"),
            positions={"CNYRUBF@RTSX": 1}, orders=tuple(broker_order),
        )
        return key, snapshot

    def test_repeated_h1_order_poll_preserves_fill_states_after_restart(self):
        for state in ("PARTIAL_FILL", "FILL", "RECONCILED"):
            with self.subTest(state=state):
                root = self.root / state.lower() / "v20lab"
                root.mkdir(parents=True)
                with V20TradeJournal(root, ROBOT, ACCOUNT) as journal:
                    key, snapshot = self.setup_case(journal, state)
                    result = journal.reconcile_order(key=key, snapshot=snapshot)
                    self.assertEqual(
                        result, f"BROKER_ORDER_ALREADY_{state}_NO_RETRANSMIT",
                    )
                    self.assertEqual(journal.store.intent(key)["status"], state)
                with V20TradeJournal(root, ROBOT, ACCOUNT) as journal:
                    self.assertEqual(journal.store.intent(key)["status"], state)
                    self.assertEqual(
                        journal.reconcile_order(key=key, snapshot=snapshot),
                        f"BROKER_ORDER_ALREADY_{state}_NO_RETRANSMIT",
                    )
                    self.assertEqual(journal.store.intent(key)["status"], state)

    def test_broker_order_id_change_fails_closed_without_demotion(self):
        with V20TradeJournal(self.root, ROBOT, ACCOUNT) as journal:
            key, changed = self.setup_case(
                journal, "PARTIAL_FILL", broker_id="broker-order-b",
            )
            with self.assertRaisesRegex(V20FinamBlocked, "BROKER_ORDER_ID_CHANGED"):
                journal.reconcile_order(key=key, snapshot=changed)
            self.assertEqual(journal.store.intent(key)["status"], "PARTIAL_FILL")
            self.assertEqual(journal.store.get("execution_halt"), "BROKER_ORDER_ID_CHANGED")


if __name__ == "__main__":
    unittest.main()
