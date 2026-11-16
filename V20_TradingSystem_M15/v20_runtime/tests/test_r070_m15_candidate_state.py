"""Offline R070 candidate H1 SQLite pointer and crash-safe ZIP rotation."""
from __future__ import annotations

from datetime import timedelta
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase, main
from unittest.mock import patch

from V20_TradingSystem_M15.v20_runtime.ext2_history_bridge import (
    EXT2HistoryBlocked, m15_history_sha256,
)
from V20_TradingSystem_M15.v20_runtime.r070_m15_candidate_state import (
    R070CandidateCheckpointState,
)
from V20_TradingSystem_M15.v20_runtime.r070_m15_checkpoint import (
    load_r070_m15_checkpoint,
)
from V20_TradingSystem_M15.v20_runtime.tests.test_ext2_history_bridge import (
    make_bars,
)


class R070CandidateSQLiteTests(TestCase):
    def _root(self, parent: str) -> Path:
        p = Path(parent) / "V20Lab"
        p.mkdir()
        return p

    def _fresh(self, root: Path, robot: str = "v20-shallow",
               account: str = "synthetic-account-a"):
        return R070CandidateCheckpointState(
            v20_root=root, robot_id=robot, account_id=account)

    def _fixture(self, parent: str):
        root = self._root(parent)
        full = make_bars()
        old = full.iloc[:18*32].copy()
        return root, full, old

    def _advance(self, state, full):
        signal = full.Datetime.iloc[-1].to_pydatetime()
        return state.restore_and_advance(
            symbol="CNYRUBF", finam_recent=full.iloc[17*32:].copy(),
            signal_open_msk=signal, observed_at_msk=signal+timedelta(minutes=15),
            independently_verified_open_days=tuple(
                d.date() for d in full.Datetime.iloc[17*32::32]),
        )

    def test_bootstrap_reboot_verified_roll_forward_and_reboot_again(self):
        with TemporaryDirectory() as tmp:
            root, full, old = self._fixture(tmp)
            with self._fresh(root) as state:
                first = state.bootstrap(
                    symbol="CNYRUBF", verified_history=old,
                    expected_history_sha256=m15_history_sha256(old))
                self.assertEqual(first["generation"], 1)
                self.assertIsNone(state.verified_cursor("USDRUBF"))
            with self._fresh(root) as state:
                self.assertEqual(state.verified_cursor("CNYRUBF"), first)
                expanded, second = self._advance(state, full)
                self.assertEqual(second["generation"], 2)
                self.assertNotEqual(second["filename"], first["filename"])
                self.assertEqual(m15_history_sha256(expanded),
                                 m15_history_sha256(full))
            with self._fresh(root) as state:
                self.assertEqual(state.verified_cursor("CNYRUBF"), second)
                self.assertTrue((state.archive_dir / first["filename"]).is_file())
                loaded, last_sha = load_r070_m15_checkpoint(
                    path=state.archive_dir / second["filename"],
                    symbol="CNYRUBF",
                    expected_checkpoint_sha256=second["checkpoint_sha256"],
                    minimum_last_m15_open_msk=full.Datetime.iloc[-1].to_pydatetime())
                self.assertTrue(loaded.Datetime.equals(full.Datetime))
                self.assertEqual(last_sha, second["history_sha256"])
                with self.assertRaisesRegex(
                        EXT2HistoryBlocked, "R070_CANDIDATE_CURSOR_NOT_ADVANCED|EXT2_PREFIX_NOT_ADVANCING"):
                    self._advance(state, full)

    def test_after_zip_creation_failure_old_sqlite_pointer_remains(self):
        with TemporaryDirectory() as tmp:
            root, full, old = self._fixture(tmp)
            with self._fresh(root) as state:
                first = state.bootstrap(
                    symbol="CNYRUBF", verified_history=old,
                    expected_history_sha256=m15_history_sha256(old))
                original_put = state.store.put
                def reject_pointer(key, value):
                    if key == "r070_m15_checkpoint:CNYRUBF":
                        raise RuntimeError("SIMULATED_DB_CRASH_BEFORE_COMMIT")
                    return original_put(key, value)
                with patch.object(state.store, "put", side_effect=reject_pointer):
                    with self.assertRaisesRegex(
                            RuntimeError, "SIMULATED_DB_CRASH_BEFORE_COMMIT"):
                        self._advance(state, full)
                self.assertEqual(state.verified_cursor("CNYRUBF"), first)
            with self._fresh(root) as state:
                self.assertEqual(state.verified_cursor("CNYRUBF"), first)
                advanced, next_row = self._advance(state, full)
                self.assertEqual(next_row["generation"], 2)
                self.assertTrue((state.archive_dir / first["filename"]).exists())

    def test_wrong_account_or_robot_isolated_and_second_instance_blocked(self):
        with TemporaryDirectory() as tmp:
            root, _, old = self._fixture(tmp)
            with self._fresh(root) as one:
                one.bootstrap(
                    symbol="GLDRUBF", verified_history=old,
                    expected_history_sha256=m15_history_sha256(old))
                with self.assertRaisesRegex(RuntimeError, "SECOND_ROBOT_INSTANCE_BLOCKED"):
                    self._fresh(root)
                with self._fresh(root, "v20-obv") as other:
                    self.assertIsNone(other.verified_cursor("GLDRUBF"))
            with self.assertRaisesRegex(RuntimeError, "STATE_ENVIRONMENT_ACCOUNT_MISMATCH"):
                self._fresh(root, account="synthetic-different-account")

    def test_missing_live_history_and_broken_calendar_never_advance(self):
        with TemporaryDirectory() as tmp:
            root, full, old = self._fixture(tmp)
            with self._fresh(root) as state:
                first = state.bootstrap(
                    symbol="CNYRUBF", verified_history=old,
                    expected_history_sha256=m15_history_sha256(old))
                signal = full.Datetime.iloc[-1].to_pydatetime()
                days = tuple(d.date() for d in full.Datetime.iloc[17*32::32])
                with self.assertRaisesRegex(
                        EXT2HistoryBlocked, "EXT2_SEED_FINAM_OVERLAP_MISSING"):
                    state.restore_and_advance(
                        symbol="CNYRUBF", finam_recent=full.iloc[18*32:].copy(),
                        signal_open_msk=signal,
                        observed_at_msk=signal+timedelta(minutes=15),
                        independently_verified_open_days=days)
                with self.assertRaisesRegex(
                        EXT2HistoryBlocked, "EXT2_SIGNAL_SESSION_NOT_PROVEN"):
                    state.restore_and_advance(
                        symbol="CNYRUBF", finam_recent=full.iloc[17*32:].copy(),
                        signal_open_msk=signal,
                        observed_at_msk=signal+timedelta(minutes=15),
                        independently_verified_open_days=days[:1])
                self.assertEqual(state.verified_cursor("CNYRUBF"), first)

    def test_never_access_live_robots_tree(self):
        with TemporaryDirectory() as tmp:
            root, _, old = self._fixture(tmp)
            with self._fresh(root) as state:
                state.bootstrap(
                    symbol="CNYRUBF", verified_history=old,
                    expected_history_sha256=m15_history_sha256(old))
            self.assertFalse((root / "robots").exists())
            self.assertTrue((root / "r070-candidate" / "shallow" / "state" /
                             "r070-m15-candidate.sqlite3").is_file())


if __name__ == "__main__":
    main()
