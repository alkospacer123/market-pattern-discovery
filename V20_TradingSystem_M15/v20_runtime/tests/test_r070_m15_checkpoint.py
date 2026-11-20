"""Offline reboot checkpoint tests: no FINAM connection or production paths."""
from __future__ import annotations

from datetime import timedelta
from hashlib import sha256
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase, main
from zipfile import ZipFile
from io import BytesIO

from V20_TradingSystem_M15.v20_runtime.ext2_history_bridge import (
    EXT2HistoryBlocked, m15_history_sha256,
)
from V20_TradingSystem_M15.v20_runtime.r070_m15_checkpoint import (
    load_r070_m15_checkpoint, resume_r070_m15_checkpoint,
    save_r070_m15_checkpoint,
)
from V20_TradingSystem_M15.v20_runtime.tests.test_ext2_history_bridge import make_bars


class R070CheckpointTests(TestCase):
    def fixture(self, root):
        full = make_bars()
        prior = full.iloc[:18*32].copy()
        latest = prior.Datetime.iloc[-1].to_pydatetime()
        dest = Path(root) / "m15-cnyrubf.zip"
        file_sha = save_r070_m15_checkpoint(
            path=dest, symbol="CNYRUBF", verified_history=prior,
            expected_history_sha256=m15_history_sha256(prior))
        return full, prior, latest, dest, file_sha

    def test_save_read_resume_and_atomic_roll_forward(self):
        with TemporaryDirectory() as tmp:
            full, prior, latest, dest, file_sha = self.fixture(tmp)
            cached, digest = load_r070_m15_checkpoint(
                path=dest, symbol="CNYRUBF", expected_checkpoint_sha256=file_sha,
                minimum_last_m15_open_msk=latest)
            self.assertTrue(cached.Datetime.equals(prior.Datetime))
            self.assertEqual(digest, m15_history_sha256(prior))
            signal = full.Datetime.iloc[-1].to_pydatetime()
            recent = full.iloc[17*32:].copy()
            days = tuple(d.date() for d in full.Datetime.iloc[17*32::32])
            advanced, advanced_sha = resume_r070_m15_checkpoint(
                path=dest, symbol="CNYRUBF",
                expected_checkpoint_sha256=file_sha,
                minimum_last_m15_open_msk=latest,
                finam_recent=recent, signal_open_msk=signal,
                observed_at_msk=signal + timedelta(minutes=15),
                independently_verified_open_days=days)
            self.assertTrue(advanced.Datetime.equals(full.Datetime))
            self.assertEqual(advanced_sha, m15_history_sha256(full))
            changed_sha = save_r070_m15_checkpoint(
                path=dest, symbol="CNYRUBF", verified_history=advanced,
                expected_history_sha256=advanced_sha,
                previous_checkpoint_sha256=file_sha)
            self.assertNotEqual(file_sha, changed_sha)
            loaded, loaded_sha = load_r070_m15_checkpoint(
                path=dest, symbol="CNYRUBF", expected_checkpoint_sha256=changed_sha,
                minimum_last_m15_open_msk=signal)
            self.assertEqual(loaded_sha, advanced_sha)
            self.assertTrue(loaded.Datetime.equals(full.Datetime))

    def test_modified_archive_wrong_symbol_or_durable_cursor_blocks(self):
        with TemporaryDirectory() as tmp:
            full, prior, latest, dest, file_sha = self.fixture(tmp)
            args = dict(path=dest, symbol="CNYRUBF",
                        expected_checkpoint_sha256=file_sha,
                        minimum_last_m15_open_msk=latest)
            with self.assertRaisesRegex(EXT2HistoryBlocked, "R070_CHECKPOINT_SYMBOL_INVALID|R070_CHECKPOINT_CONTENT_INVALID"):
                load_r070_m15_checkpoint(**{**args, "symbol": "GLDRUBF"})
            with self.assertRaisesRegex(EXT2HistoryBlocked, "R070_CHECKPOINT_CONTENT_INVALID"):
                load_r070_m15_checkpoint(
                    **{**args, "minimum_last_m15_open_msk": latest + timedelta(minutes=15)})
            with self.assertRaisesRegex(EXT2HistoryBlocked, "R070_CHECKPOINT_SHA_MISMATCH"):
                load_r070_m15_checkpoint(**{**args, "expected_checkpoint_sha256": "0"*64})
            data = dest.read_bytes()
            dest.write_bytes(data[:-3] + b"BAD")
            with self.assertRaisesRegex(EXT2HistoryBlocked, "R070_CHECKPOINT_SHA_MISMATCH"):
                load_r070_m15_checkpoint(**args)

    def test_atomic_failed_update_keeps_original_snapshot(self):
        with TemporaryDirectory() as tmp:
            full, prior, latest, dest, file_sha = self.fixture(tmp)
            previous_bytes = dest.read_bytes()
            with self.assertRaisesRegex(EXT2HistoryBlocked, "R070_CHECKPOINT_OVERWRITE_UNVERIFIED"):
                save_r070_m15_checkpoint(
                    path=dest, symbol="CNYRUBF", verified_history=full,
                    expected_history_sha256=m15_history_sha256(full))
            with self.assertRaisesRegex(EXT2HistoryBlocked, "R070_HISTORY_DIGEST_MISMATCH"):
                save_r070_m15_checkpoint(
                    path=dest, symbol="CNYRUBF", verified_history=full,
                    expected_history_sha256="0"*64,
                    previous_checkpoint_sha256=file_sha)
            self.assertEqual(previous_bytes, dest.read_bytes())
            self.assertEqual(file_sha, sha256(dest.read_bytes()).hexdigest())

    def test_resume_without_fresh_overlap_or_certified_day_blocks(self):
        with TemporaryDirectory() as tmp:
            full, prior, latest, dest, file_sha = self.fixture(tmp)
            signal = full.Datetime.iloc[-1].to_pydatetime()
            args = dict(path=dest, symbol="CNYRUBF",
                        expected_checkpoint_sha256=file_sha,
                        minimum_last_m15_open_msk=latest,
                        signal_open_msk=signal,
                        observed_at_msk=signal + timedelta(minutes=15))
            days = tuple(d.date() for d in full.Datetime.iloc[17*32::32])
            with self.assertRaisesRegex(EXT2HistoryBlocked, "EXT2_SEED_FINAM_OVERLAP_MISSING"):
                resume_r070_m15_checkpoint(
                    **args, finam_recent=full.iloc[18*32:].copy(),
                    independently_verified_open_days=days)
            with self.assertRaisesRegex(EXT2HistoryBlocked, "EXT2_SIGNAL_SESSION_NOT_PROVEN"):
                resume_r070_m15_checkpoint(
                    **args, finam_recent=full.iloc[17*32:].copy(),
                    independently_verified_open_days=days[:1])
            with self.assertRaisesRegex(EXT2HistoryBlocked, "EXT2_RECENT_SESSION_M15_MISSING"):
                broken = full.iloc[17*32:].drop(full.index[-8])
                resume_r070_m15_checkpoint(
                    **args, finam_recent=broken,
                    independently_verified_open_days=days)


if __name__ == "__main__":
    main()
