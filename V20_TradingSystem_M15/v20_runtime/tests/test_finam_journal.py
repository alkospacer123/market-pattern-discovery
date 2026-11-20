"""V20-08.1: only new durable H1 SQLite intent/recovery tests; no broker."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from tempfile import TemporaryDirectory
import hashlib
import unittest

from TradingSystemLab.stage8_robot.execution_grid import initial_projection
from TradingSystemLab.stage8_robot.production_runtime import _load_registry

from V20_TradingSystem_M15.v20_runtime.account_risk import AccountAuthority
from V20_TradingSystem_M15.v20_runtime.finam_execution import (
    LiveAccountSnapshot, V20FinamBlocked, V20TradeJournal,
)
from V20_TradingSystem_M15.v20_runtime.offline_planner import FrozenSignal, ProposedEntry
from V20_TradingSystem_M15.v20_runtime.h1_state_journal import IsolatedReferenceJournal


ACCOUNT = "synthetic-fin-account-001"
ROBOT = "v20-shallow"
HASH = hashlib.sha256(ACCOUNT.encode("utf-8")).hexdigest()


def case(symbol="USDRUBF", hour=10, minute=15):
    at = datetime(2026, 10, 24, hour, minute)
    row = _load_registry()[symbol]
    price = Decimal({"USDRUBF": "85.00", "CNYRUBF": "12.000",
                     "GLDRUBF": "10000.0", "IMOEXF": "2450.0"}[symbol])
    atr = Decimal({"USDRUBF": "0.1", "CNYRUBF": "0.03",
                   "GLDRUBF": "10", "IMOEXF": "5"}[symbol])
    step = Decimal(row["price_step"])
    stop, distance = initial_projection("LONG", price, price - 2 * atr, step)
    signal = FrozenSignal("SHALLOW_PULLBACK", symbol, 1, at - timedelta(minutes=15), atr)
    proposed = ProposedEntry(
        "SHALLOW_PULLBACK", symbol, "LONG", at, price, stop, distance, 1,
        Decimal("675"), Decimal("1500"), "synthetic",
    )
    authority = AccountAuthority(
        ACCOUNT, Decimal("45000"), Decimal("45000"), step,
        Decimal(row["tick_value"]), Decimal("1500"),
        int(row["quantity_granularity"]), Decimal("2"),
    )
    snapshot = LiveAccountSnapshot(
        ROBOT, HASH, datetime.now(timezone.utc), Decimal("45000"),
        Decimal("45000"), {}, tuple(),
    )
    return dict(signal=signal, entry=proposed, authority=authority, snapshot=snapshot)


class JournalTests(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / "v20lab"
        self.root.mkdir()

    def test_real_journal_uses_intel_robot_instance_not_legacy_offline(self):
        # Stage07 placed DPAPI, config and Task working dir under robots/.
        # No exchange of state or modification of a prior offline journal.
        installed = self.root / "robots" / "shallow"
        secret_dir = installed / "secrets"
        secret_dir.mkdir(parents=True)
        secret = secret_dir / "finam.dpapi.json"
        secret.write_text("synthetic-never-a-real-token", encoding="utf-8")
        old = self.root / "shallow"
        with IsolatedReferenceJournal(self.root, ROBOT, ACCOUNT) as offline:
            self.assertEqual(offline.instance_root, old)
            self.assertEqual(offline.state_path.name, "v20-offline-reference.sqlite3")
            with V20TradeJournal(self.root, ROBOT, ACCOUNT) as real:
                self.assertEqual(real.instance_root, installed)
                self.assertEqual(real.state_path, installed / "state" /
                                 "v20-real-intents.sqlite3")
                self.assertTrue(real.state_path.exists())
                self.assertNotEqual(real.lock, offline.lock)
                self.assertEqual(real.account_hash, HASH)
        self.assertEqual(secret.read_text(encoding="utf-8"),
                         "synthetic-never-a-real-token")
        self.assertFalse((old / "state" / "v20-real-intents.sqlite3").exists())

    def test_atomic_entry_risk_and_session_quota(self):
        with V20TradeJournal(self.root, ROBOT, ACCOUNT) as journal:
            key = journal.prepare_entry(**case())
            intent = journal.store.intent(key)
            self.assertEqual(intent["status"], "INTENT_PERSISTED")
            self.assertEqual(intent["payload"]["mode"], "PRETRADE_NOT_AUTHORIZED")
            self.assertEqual(intent["payload"]["wire"]["client_order_id"][:2], "s8")
            self.assertEqual(journal.store.get("risk_reservations")[key]["quantity"], 1)
            self.assertEqual(len(journal.store.all_intents()), 1)
            with self.assertRaisesRegex(V20FinamBlocked, "ENTRY_INTENT_ALREADY_PERSISTED_NO_RETRY"):
                journal.prepare_entry(**case())
            with self.assertRaisesRegex(V20FinamBlocked, "ONE_ENTRY_PER_SYMBOL_PER_SESSION"):
                journal.prepare_entry(**case(minute=30))
            journal.prepare_entry(**case("CNYRUBF", minute=30))
            with self.assertRaisesRegex(V20FinamBlocked, "TWO_ENTRIES_PER_SESSION"):
                journal.prepare_entry(**case("GLDRUBF", minute=45))
            self.assertEqual(len(journal.store.all_intents()), 2)

    def test_uncertain_post_never_replayed_even_after_restart(self):
        with V20TradeJournal(self.root, ROBOT, ACCOUNT) as journal:
            key = journal.prepare_entry(**case())
            journal.record_submission_boundary(key)
            self.assertEqual(journal.store.intent(key)["status"], "UNCERTAIN")
            with self.assertRaisesRegex(V20FinamBlocked, "POST_BOUNDARY_ALREADY_CONSUMED"):
                journal.record_submission_boundary(key)
        with V20TradeJournal(self.root, ROBOT, ACCOUNT) as journal:
            self.assertEqual(journal.store.intent(key)["status"], "UNCERTAIN")
            with self.assertRaisesRegex(V20FinamBlocked, "UNKNOWN_POST_NO_RETRANSMIT"):
                journal.reconcile_order(key=key, snapshot=case()["snapshot"])
            with self.assertRaisesRegex(V20FinamBlocked, "JOURNAL_HALTED"):
                journal.prepare_entry(**case("CNYRUBF", minute=30))

    def test_identity_and_exclusive_lock(self):
        with V20TradeJournal(self.root, ROBOT, ACCOUNT) as first:
            self.assertEqual(first.store.get("database_identity")["mode"],
                             "V20_PRETRADE_UNAUTHORIZED")
            with self.assertRaisesRegex(RuntimeError, "SECOND_ROBOT_INSTANCE_BLOCKED"):
                V20TradeJournal(self.root, ROBOT, ACCOUNT)
        with self.assertRaises(RuntimeError):
            V20TradeJournal(self.root, ROBOT, "different-account")

    def test_nonflat_and_broker_mismatch_refuse_preparation(self):
        with V20TradeJournal(self.root, ROBOT, ACCOUNT) as journal:
            entry = case()
            snap = entry["snapshot"]
            entry["snapshot"] = LiveAccountSnapshot(
                snap.robot_id, snap.account_hash, snap.observed_at,
                snap.realized_equity, snap.available_cash,
                {"USDRUBF@RTSX": 1}, tuple(),
            )
            with self.assertRaisesRegex(V20FinamBlocked, "NONFLAT_BROKER_BOOTSTRAP_FORBIDDEN"):
                journal.prepare_entry(**entry)
            self.assertEqual(journal.store.all_intents(), [])
            entry = case()
            wrong = entry["authority"]
            entry["authority"] = AccountAuthority(
                "foreign-account", wrong.realized_equity, wrong.available_cash,
                wrong.price_step, wrong.tick_value, wrong.initial_margin,
                wrong.trade_lot_size, wrong.roundtrip_cost_per_contract,
            )
            with self.assertRaisesRegex(V20FinamBlocked, "PRETRADE_ACCOUNT_AUTHORITY_MISMATCH"):
                journal.prepare_entry(**entry)
            self.assertEqual(journal.store.all_intents(), [])


if __name__ == "__main__":
    unittest.main()
