"""M15 step14 synthetic FINAM GET receipts with isolated durable SQLite only."""
from __future__ import annotations

from contextlib import closing
from datetime import datetime, timedelta, timezone
import hashlib
from pathlib import Path
import sqlite3
import tempfile
import unittest

from IntradayLab.m15_robot.broker_receipt_store import (
    M15ReadOnlyBrokerReceiptStore, M15BrokerReceiptError,
)
from IntradayLab.m15_robot.broker_reconcile_gate import M15ReconcileGateError
from IntradayLab.m15_robot.tests.test_broker_reconcile_gate import (
    target, account, entry_order, trade, stop_order,
)

AT = datetime(2026, 10, 18, 10, 45, tzinfo=timezone.utc)


class DurableReadOnlyBrokerReceipts(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        base = Path(self.tmp.name)
        self.opts = {
            "runtime_root": base / "m15",
            "h1_runtime_root": base / "h1",
            "repository_root": base / "code",
            "m15_account_id": "M15-SYNTH-ACCOUNT",
            "h1_account_sha256": hashlib.sha256(b"H1-SYNTH-ACCOUNT").hexdigest(),
        }
        self.store = M15ReadOnlyBrokerReceiptStore(**self.opts)

    def tearDown(self):
        self.store.close()
        self.tmp.cleanup()

    def observe(self, *, at=AT, qty=0, trades=None, orders=None, acc=None, expected=None):
        if trades is None:
            trades = []
        if orders is None:
            status = (
                "ORDER_STATUS_FILLED" if len(trades) == 3 else
                "ORDER_STATUS_PARTIAL_FILL" if trades else "ORDER_STATUS_NEW"
            )
            orders = [entry_order(status=status)]
        return self.store.observe(
            observed_at=at, expected=target() if expected is None else expected,
            expected_client_order_id="m15entry0001", stop_trade_tag="trade-1",
            account=account(qty) if acc is None else acc,
            orders_response={"orders": orders},
            trades_response={"trades": trades},
            start="2026-10-18T07:00:00Z", end="2026-10-18T09:00:00Z",
        )

    def test_empty_fill_get_is_receipt_not_authorized_fill(self):
        reply = self.observe()
        self.assertEqual(reply["cycle"], 1)
        self.assertTrue(reply["appended"])
        row = self.store.latest()
        self.assertEqual(row["quantity_status"], "NO_MATCH")
        self.assertEqual(row["matched_quantity"], 0)
        self.assertEqual(row["protection_status"], "NO_CONFIRMED_FILL")
        self.assertFalse(self.store.execution_authorized)
        self.assertFalse(reply["live_authorized"])

    def test_partial_fill_preserves_exact_quantity_without_authority(self):
        self.observe(qty=1, trades=[trade()])
        row = self.store.latest()
        self.assertEqual(row["quantity_status"], "PARTIAL")
        self.assertEqual(row["matched_quantity"], 1)
        self.assertEqual(row["broker_position_quantity"], 1)
        self.assertEqual(row["protection_status"], "UNPROTECTED_BROKER_FILL")

    def test_broker_100_percent_stop_is_not_sufficient_coverage_proof(self):
        rows = [trade(1), trade(2), trade(3)]
        orders = [entry_order(status="ORDER_STATUS_FILLED"), stop_order()]
        self.observe(qty=3, trades=rows, orders=orders)
        row = self.store.latest()
        self.assertEqual(row["quantity_status"], "FULL")
        self.assertEqual(row["active_sltp_count"], 1)
        self.assertEqual(row["protection_status"], "ACTIVE_SLTP_COVERAGE_TIMESTAMP_UNPROVEN")
        self.assertFalse(self.store.execution_authorized)

    def test_restart_and_same_timestamp_identical_observation_is_idempotent(self):
        self.observe()
        first = self.store.latest()
        self.store.close()
        self.store = M15ReadOnlyBrokerReceiptStore(**self.opts)
        replay = self.observe()
        self.assertFalse(replay["appended"])
        self.assertEqual(replay["cycle"], 1)
        self.assertEqual(self.store.latest(), first)
        later = self.observe(at=AT + timedelta(seconds=30))
        self.assertEqual(later["cycle"], 2)

    def test_same_timestamp_changed_position_refused_without_mutation(self):
        self.observe()
        with self.assertRaisesRegex(M15BrokerReceiptError, "CONFLICTING_CYCLE"):
            self.observe(at=AT, qty=1, trades=[trade()])
        self.assertEqual(self.store.latest()["matched_quantity"], 0)

    def test_stale_timestamp_refused_and_original_receipt_unchanged(self):
        self.observe()
        with self.assertRaisesRegex(M15BrokerReceiptError, "STALE_OR_CONFLICTING"):
            self.observe(at=AT - timedelta(seconds=1))
        self.assertEqual(self.store.latest()["cycle"], 1)

    def test_wrong_account_denied_before_sqlite_append(self):
        with self.assertRaisesRegex(M15BrokerReceiptError, "ACCOUNT_BOUNDARY"):
            self.observe(expected=target(account_id="H1-SYNTH-ACCOUNT"))
        self.assertIsNone(self.store.latest())

    def test_broker_position_without_history_not_persisted(self):
        with self.assertRaisesRegex(M15ReconcileGateError, "POSITION_FILL_DIVERGENCE"):
            self.observe(qty=1)
        self.assertIsNone(self.store.latest())

    def test_inconsistent_order_status_and_broker_fill_not_persisted(self):
        with self.assertRaisesRegex(M15ReconcileGateError, "ORDER_STATUS_FILL_DIVERGENCE"):
            self.observe(qty=1, trades=[trade()], orders=[entry_order()])
        self.assertIsNone(self.store.latest())

    def test_broker_identity_mismatch_denied(self):
        with self.assertRaisesRegex(M15ReconcileGateError, "ACCOUNT_BINDING"):
            self.observe(acc=account(account_id="FOREIGN"))
        self.assertIsNone(self.store.latest())

    def test_db_contains_no_raw_account_trade_order_ids(self):
        self.observe(qty=1, trades=[trade()])
        raw = self.store.path.read_bytes()
        for secret in (b"M15-SYNTH-ACCOUNT", b"H1-SYNTH-ACCOUNT",
                       b"broker-entry-01", b"fill-1", b"m15entry0001"):
            self.assertNotIn(secret, raw)

    def test_existing_db_wrong_account_identity_refused_on_restart(self):
        self.observe()
        self.store.close()
        other = self.opts | {"m15_account_id": "DIFFERENT-M15"}
        with self.assertRaisesRegex(M15BrokerReceiptError, "ACCOUNT_IDENTITY_MISMATCH"):
            M15ReadOnlyBrokerReceiptStore(**other)
        self.store = M15ReadOnlyBrokerReceiptStore(**self.opts)
        self.assertEqual(self.store.latest()["cycle"], 1)

    def test_existing_db_identity_deleted_refused_without_reset(self):
        self.observe()
        self.store.close()
        with closing(sqlite3.connect(self.store.path)) as db, db:
            db.execute("DELETE FROM metadata WHERE key='identity'")
        with self.assertRaisesRegex(M15BrokerReceiptError, "EXISTING_IDENTITY_MISSING"):
            M15ReadOnlyBrokerReceiptStore(**self.opts)
        with closing(sqlite3.connect(self.store.path)) as db, db:
            import json
            db.execute("INSERT INTO metadata VALUES('identity',?)",
                       (json.dumps(self.store.identity, sort_keys=True),))
        self.store = M15ReadOnlyBrokerReceiptStore(**self.opts)

    def test_sqlite_insert_fault_does_not_persist_fake_receipt(self):
        with self.store._db:
            self.store._db.execute(
                "CREATE TRIGGER synthetic_fault BEFORE INSERT ON entry_receipts "
                "BEGIN SELECT RAISE(ABORT,'synthetic'); END"
            )
        with self.assertRaisesRegex(M15BrokerReceiptError, "SQLITE_FAULT"):
            self.observe()
        self.assertIsNone(self.store.latest())
        with self.store._db:
            self.store._db.execute("DROP TRIGGER synthetic_fault")
        self.assertEqual(self.observe()["cycle"], 1)

    def test_no_h1_runtime_path_or_live_interface(self):
        self.assertFalse(hasattr(self.store, "place_order"))
        self.assertFalse(hasattr(self.store, "cancel_order"))
        self.assertFalse(hasattr(self.store, "rearm"))
        self.assertFalse(self.store.execution_authorized)
        with self.assertRaisesRegex(ValueError, "OVERLAP"):
            M15ReadOnlyBrokerReceiptStore(
                **(self.opts | {"runtime_root": self.opts["h1_runtime_root"]})
            )

    def test_naive_timestamp_rejected(self):
        with self.assertRaisesRegex(M15BrokerReceiptError, "CLOCK_INVALID"):
            self.observe(at=datetime(2026, 10, 18, 10, 45))
        self.assertIsNone(self.store.latest())


if __name__ == "__main__":
    unittest.main()
