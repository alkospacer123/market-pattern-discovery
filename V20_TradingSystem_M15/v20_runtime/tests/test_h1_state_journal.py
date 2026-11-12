"""New H1 StateStore reuse checks: disposable V20Lab only, no FINAM or orders."""
from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from V20_TradingSystem_M15.v20_runtime.offline_planner import (
    FrozenSignal, OfflinePlanner,
)
from V20_TradingSystem_M15.v20_runtime.h1_state_journal import (
    IsolatedReferenceJournal, V20StateBoundaryError, LIVE_ENABLED,
)


T = datetime(2026, 10, 22, 10, 0)


def plan(strategy, symbol="CNYRUBF", at=T, side=1):
    signal = FrozenSignal(strategy, symbol, side, at, Decimal("0.013"))
    planner = OfflinePlanner(strategy)
    entry = planner.reference_next_open(
        signal, at=at + timedelta(minutes=15), entry_open="10.00",
        realized_equity="500000", price_step="0.01", tick_value="100",
        initial_margin="10000", available_cash="200000",
        trade_lot_size=1, cost_buffer_per_contract="50")
    return signal, entry


class H1StateReuseTests(unittest.TestCase):
    def test_offline_never_live(self):
        self.assertIs(LIVE_ENABLED, False)

    def test_first_and_repeated_reference_idempotent(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp) / "V20Lab"
            signal, entry = plan("SHALLOW_PULLBACK")
            with IsolatedReferenceJournal(root, "v20-shallow", "test-account-1") as j:
                key = j.record_reference(signal, entry)
                self.assertEqual(key, j.record_reference(signal, entry))
                self.assertEqual(len(j.offline_snapshot()), 1)
                self.assertEqual(j.offline_snapshot()[0]["mode"],
                                 "OFFLINE_REFERENCE_NOT_ORDER")
                self.assertEqual(j.store.unresolved_intent_count(), 0)

    def test_reopen_same_exact_identity_preserves_records(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp) / "V20Lab"
            sig, entry = plan("OBV_PRESSURE", "USDRUBF")
            with IsolatedReferenceJournal(root, "v20-obv", "account-one") as j:
                original = j.record_reference(sig, entry)
            with IsolatedReferenceJournal(root, "v20-obv", "account-one") as j:
                self.assertEqual(j.offline_snapshot()[0]["reference_id"], original)

    def test_wrong_account_refused_on_existing_database(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp) / "V20Lab"
            with IsolatedReferenceJournal(root, "v20-inside", "account-one"):
                pass
            with self.assertRaisesRegex(V20StateBoundaryError,
                                        "ACCOUNT_OR_STRATEGY_MISMATCH"):
                IsolatedReferenceJournal(root, "v20-inside", "account-two")

    def test_three_accounts_independent_same_symbol(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp) / "V20Lab"
            refs = []
            for robot, strategy in (
                ("v20-shallow", "SHALLOW_PULLBACK"),
                ("v20-obv", "OBV_PRESSURE"),
                ("v20-inside", "INSIDE_DAY_RELEASE"),
            ):
                with IsolatedReferenceJournal(root, robot, robot + "-account") as journal:
                    refs.append(journal.record_reference(*plan(strategy)))
                    self.assertEqual(len(journal.offline_snapshot()), 1)
            self.assertEqual(len(set(refs)), 3)
            self.assertEqual(len(tuple(root.glob("*/state/*.sqlite3"))), 3)

    def test_two_entries_per_session_and_symbol_deduplication(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp) / "V20Lab"
            with IsolatedReferenceJournal(root, "v20-shallow", "acct") as journal:
                for symbol in ("USDRUBF", "CNYRUBF"):
                    journal.record_reference(*plan("SHALLOW_PULLBACK", symbol))
                with self.assertRaisesRegex(V20StateBoundaryError, "TWO_NEW_ENTRIES"):
                    journal.record_reference(*plan("SHALLOW_PULLBACK", "IMOEXF"))
                self.assertEqual(len(journal.offline_snapshot()), 2)

    def test_symbol_once_per_session_even_if_direction_changes(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp) / "V20Lab"
            with IsolatedReferenceJournal(root, "v20-obv", "acct") as journal:
                journal.record_reference(*plan("OBV_PRESSURE", "CNYRUBF", side=1))
                with self.assertRaisesRegex(V20StateBoundaryError, "ONE_ENTRY_PER_SYMBOL"):
                    journal.record_reference(*plan("OBV_PRESSURE", "CNYRUBF", side=-1))

    def test_old_database_wrong_root_rejected_before_open(self):
        with TemporaryDirectory() as tmp:
            wrong = Path(tmp) / "TradingSystemLab"
            with self.assertRaisesRegex(V20StateBoundaryError, "ISOLATED_V20LAB"):
                IsolatedReferenceJournal(wrong, "v20-shallow", "acct")

    def test_duplicate_instance_process_lock(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp) / "V20Lab"
            with IsolatedReferenceJournal(root, "v20-obv", "acct"):
                with self.assertRaisesRegex(RuntimeError, "SECOND_ROBOT_INSTANCE_BLOCKED"):
                    IsolatedReferenceJournal(root, "v20-obv", "acct")

    def test_reject_strategy_mismatch_without_persisting(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp) / "V20Lab"
            with IsolatedReferenceJournal(root, "v20-inside", "acct") as journal:
                with self.assertRaisesRegex(V20StateBoundaryError, "REFERENCE_STRATEGY"):
                    journal.record_reference(*plan("OBV_PRESSURE"))
                self.assertEqual(journal.offline_snapshot(), [])


if __name__ == "__main__":
    unittest.main()
