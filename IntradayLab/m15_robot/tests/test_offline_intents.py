"""Deterministic durable intent/fill/stop rehearsal, no FINAM transport."""
import hashlib
from contextlib import closing
import sqlite3
import tempfile
import unittest
from decimal import Decimal
from pathlib import Path

from IntradayLab.m15_robot.offline_intents import OfflineIntentLedger, M15OfflineLedgerError


class Rehearsal(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        self.kwargs = {
            "runtime_root": root / "m15",
            "h1_runtime_root": root / "h1",
            "repository_root": root / "repository",
            "m15_account_id": "M15-ACCOUNT",
            "h1_account_sha256": hashlib.sha256(b"H1-ACCOUNT").hexdigest(),
        }
        self.ledger = OfflineIntentLedger(**self.kwargs)

    def tearDown(self):
        self.ledger.close()
        self.tmp.cleanup()

    def prepare(self, key="m15:signal-1", instrument="USDRUBF", direction="LONG", quantity=3):
        return self.ledger.prepare(
            key=key, instrument=instrument, direction=direction, quantity=quantity
        )

    def ack(self, key="m15:signal-1", synthetic_id="sim-order-1"):
        self.ledger.synthetic_ack(key, synthetic_id)

    def fill(self, key="m15:signal-1", fill_id="sim-fill-1", qty=1, price="101",
             synthetic_id="sim-order-1"):
        return self.ledger.synthetic_fill(
            key=key, fill_id=fill_id, broker_order_id=synthetic_id,
            quantity=qty, price=price,
        )

    def test_offline_authorization_always_denied(self):
        self.assertFalse(self.ledger.execution_authorized)
        self.assertTrue(self.ledger.unsafe_for_live())

    def test_persist_before_ack(self):
        self.assertTrue(self.prepare())
        self.assertEqual(self.ledger.intent("m15:signal-1")["status"], "PREPARED")
        self.assertEqual(self.ledger.filled_quantity("m15:signal-1"), 0)

    def test_same_key_no_duplicate_entry(self):
        self.assertTrue(self.prepare())
        self.assertFalse(self.prepare())
        self.assertEqual(self.ledger.db.execute("SELECT COUNT(*) FROM intents").fetchone()[0], 1)

    def test_reused_key_conflicting_payload_rejected(self):
        self.prepare()
        with self.assertRaisesRegex(M15OfflineLedgerError, "CONFLICT"):
            self.prepare(direction="SHORT")

    def test_second_open_instrument_rejected(self):
        self.prepare()
        with self.assertRaisesRegex(M15OfflineLedgerError, "OCCUPIED"):
            self.prepare(key="m15:signal-2")

    def test_different_instrument_can_have_own_intent(self):
        self.prepare()
        self.assertTrue(self.prepare(key="m15:signal-2", instrument="CNYRUBF"))

    def test_uncertain_does_not_auto_ack_or_resubmit(self):
        self.prepare()
        self.ledger.uncertain("m15:signal-1")
        self.assertEqual(self.ledger.intent("m15:signal-1")["status"], "UNCERTAIN")
        self.assertFalse(self.prepare())
        with self.assertRaisesRegex(M15OfflineLedgerError, "TRANSITION_DENIED"):
            self.ledger.uncertain("m15:signal-1")
        self.assertEqual(self.ledger.filled_quantity("m15:signal-1"), 0)

    def test_ack_only_with_synthetic_receipt(self):
        self.prepare()
        with self.assertRaisesRegex(M15OfflineLedgerError, "SYNTHETIC"):
            self.ack(synthetic_id="real-exchange-order-id")
        self.ack()
        self.assertEqual(self.ledger.intent("m15:signal-1")["status"], "ACK")

    def test_fill_without_ack_rejected(self):
        self.prepare()
        with self.assertRaisesRegex(M15OfflineLedgerError, "BROKER_PROOF"):
            self.fill()

    def test_partial_then_final_fill_state(self):
        self.prepare()
        self.ack()
        self.assertTrue(self.fill(qty=1, price="100"))
        self.assertEqual(self.ledger.intent("m15:signal-1")["status"], "PARTIAL_FILL")
        self.assertEqual(self.ledger.filled_quantity("m15:signal-1"), 1)
        self.assertTrue(self.fill(fill_id="sim-fill-2", qty=2, price="103"))
        self.assertEqual(self.ledger.intent("m15:signal-1")["status"], "FILLED")
        self.assertEqual(self.ledger.filled_quantity("m15:signal-1"), 3)
        self.assertEqual(self.ledger.synthetic_vwap("m15:signal-1"), Decimal("102"))

    def test_no_overfill(self):
        self.prepare(quantity=2)
        self.ack()
        self.fill(qty=1)
        with self.assertRaisesRegex(M15OfflineLedgerError, "OVERFILL"):
            self.fill(fill_id="sim-fill-2", qty=2)

    def test_same_fill_idempotent_and_conflicting_fill_rejected(self):
        self.prepare()
        self.ack()
        self.assertTrue(self.fill())
        self.assertFalse(self.fill())
        with self.assertRaisesRegex(M15OfflineLedgerError, "CONFLICTING"):
            self.fill(price="105")

    def test_synthetic_initial_stop_requires_realized_fill(self):
        self.prepare()
        self.ack()
        with self.assertRaisesRegex(M15OfflineLedgerError, "WITHOUT_FILL"):
            self.ledger.synthetic_stop_ack(
                key="m15:signal-1", stop_price="96",
                synthetic_order_id="sim-stop-1",
            )

    def test_long_initial_stop_and_tightening_only(self):
        self.prepare()
        self.ack()
        self.fill()
        self.assertEqual(self.ledger.synthetic_stop_ack(
            key="m15:signal-1", stop_price="96", synthetic_order_id="sim-stop-1",
        ), 0)
        with self.assertRaisesRegex(M15OfflineLedgerError, "NOT_TIGHTER"):
            self.ledger.synthetic_stop_ack(
                key="m15:signal-1", stop_price="95", synthetic_order_id="sim-stop-2",
            )
        self.assertEqual(self.ledger.synthetic_stop_ack(
            key="m15:signal-1", stop_price="99", synthetic_order_id="sim-stop-3",
        ), 1)
        self.assertEqual(self.ledger.latest_stop("m15:signal-1")["quantity_percent"], 100)

    def test_short_stop_tightens_down(self):
        self.prepare(direction="SHORT")
        self.ack()
        self.fill(price="100")
        self.ledger.synthetic_stop_ack(
            key="m15:signal-1", stop_price="105", synthetic_order_id="sim-stop-1",
        )
        with self.assertRaisesRegex(M15OfflineLedgerError, "NOT_TIGHTER"):
            self.ledger.synthetic_stop_ack(
                key="m15:signal-1", stop_price="106", synthetic_order_id="sim-stop-2",
            )
        self.ledger.synthetic_stop_ack(
            key="m15:signal-1", stop_price="102", synthetic_order_id="sim-stop-3",
        )
        self.assertEqual(self.ledger.latest_stop("m15:signal-1")["revision"], 1)

    def test_protection_persists_restarts(self):
        self.prepare()
        self.ack()
        self.fill()
        self.ledger.synthetic_stop_ack(
            key="m15:signal-1", stop_price="96", synthetic_order_id="sim-stop-1",
        )
        self.ledger.close()
        self.ledger = OfflineIntentLedger(**self.kwargs)
        self.assertEqual(self.ledger.filled_quantity("m15:signal-1"), 1)
        self.assertEqual(self.ledger.latest_stop("m15:signal-1")["revision"], 0)
        self.assertEqual(self.ledger.intent("m15:signal-1")["status"], "PARTIAL_FILL")

    def test_restart_account_swap_fails(self):
        self.ledger.close()
        with self.assertRaisesRegex(M15OfflineLedgerError, "IDENTITY_MISMATCH"):
            OfflineIntentLedger(**(self.kwargs | {"m15_account_id": "M15-OTHER"}))
        self.ledger = OfflineIntentLedger(**self.kwargs)

    def test_reject_live_h1_account_binding(self):
        self.ledger.close()
        with self.assertRaisesRegex(ValueError, "REUSE"):
            OfflineIntentLedger(**(self.kwargs | {"m15_account_id": "H1-ACCOUNT"}))
        self.ledger = OfflineIntentLedger(**self.kwargs)

    def test_forged_sqlite_identity_denied(self):
        self.ledger.close()
        with closing(sqlite3.connect(self.ledger.path)) as db, db:
            db.execute("UPDATE metadata SET value='{}' WHERE key='identity'")
        with self.assertRaisesRegex(M15OfflineLedgerError, "IDENTITY_MISMATCH"):
            OfflineIntentLedger(**self.kwargs)
        with closing(sqlite3.connect(self.ledger.path)) as db, db:
            import json
            db.execute("UPDATE metadata SET value=? WHERE key='identity'",
                       (json.dumps(self.ledger.identity, sort_keys=True),))
        self.ledger = OfflineIntentLedger(**self.kwargs)

    def test_existing_sqlite_with_deleted_identity_not_reinitialized(self):
        self.ledger.close()
        with closing(sqlite3.connect(self.ledger.path)) as db, db:
            db.execute("DELETE FROM metadata WHERE key='identity'")
        with self.assertRaisesRegex(M15OfflineLedgerError, "EXISTING_IDENTITY_MISSING"):
            OfflineIntentLedger(**self.kwargs)
        # Rebind to the original authority for tearDown without weakening
        # the tested production constructor.
        with closing(sqlite3.connect(self.ledger.path)) as db, db:
            import json
            db.execute("INSERT INTO metadata(key,value) VALUES('identity',?)",
                       (json.dumps(self.ledger.identity, sort_keys=True),))
        self.ledger = OfflineIntentLedger(**self.kwargs)

    def test_unexpected_sqlite_columns_block_on_restart(self):
        self.ledger.close()
        with closing(sqlite3.connect(self.ledger.path)) as db, db:
            db.execute("ALTER TABLE protection ADD COLUMN suspicious TEXT")
        with self.assertRaisesRegex(M15OfflineLedgerError, "COLUMNS_INVALID"):
            OfflineIntentLedger(**self.kwargs)
        # The deliberately corrupted temporary DB cannot be safely repaired
        # by regular runtime; delete synthetic fixture and create clean store.
        self.ledger.path.unlink()
        self.ledger = OfflineIntentLedger(**self.kwargs)

    def test_reject_empty_intent_key_and_invalid_control_char(self):
        with self.assertRaisesRegex(M15OfflineLedgerError, "INTENT_INVALID"):
            self.prepare(key="m15:")
        with self.assertRaisesRegex(M15OfflineLedgerError, "INTENT_INVALID"):
            self.prepare(key="m15:bad\nkey")

    def test_raw_account_id_not_stored_in_sqlite(self):
        self.prepare()
        raw = self.ledger.path.read_bytes()
        self.assertNotIn(b"M15-ACCOUNT", raw)
        self.assertNotIn(b"H1-ACCOUNT", raw)


if __name__ == "__main__":
    unittest.main()
