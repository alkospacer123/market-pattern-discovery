"""R088 proof-to-account bootstrap; all tests local synthetic, no FINAM."""
from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase, main
from unittest.mock import patch

from V20_TradingSystem_M15.v20_runtime.ext2_history_bridge import EXT2HistoryBlocked
from V20_TradingSystem_M15.v20_runtime.r088_cny_verified_bootstrap import (
    ARCHIVE, HISTORY_SHA256, _check_physical_report, bootstrap_r088_verified_cny,
)


def report(archive: Path, *, robot="v20-shallow", account="synthetic-account-01"):
    scope = sha256(account.encode("utf-8")).hexdigest()
    return {
        "schema": "r070.cny.finam_readonly_physical.v1",
        "status": "PASS_CNYRUBF_FRESH_M15_READONLY_NO_LIVE",
        "robot": robot, "account_sha256": scope,
        "checkpoint_history_sha256": HISTORY_SHA256,
        "checkpoint_file_sha256": sha256(archive.read_bytes()).hexdigest(),
        "source_r060_zip_sha256": "80291246ba4692485545f58fd28c7563199bf7be28033fc16eb296efee377e31",
        "source_terminal_csv_sha256": "f6ae045a074fea9be3f7c9b5ca47dfc7dedae4481f61e8a71fc60d16b502d4f2",
        "readonly_http_method": "FINAM GET /bars only plus session authentication",
        "observed_at_utc": datetime(2026, 11, 18, 12, 40, tzinfo=timezone.utc).isoformat(),
        "last_completed_open_msk": "2026-11-18T15:30:00",
        "overlap_verified": 32, "m15_missing": 0, "account_bound_sqlite": False,
        "live_authorized": False, "orders_sent": 0, "orders_cancelled": 0,
        "report_contains_token_or_account_id": False,
    }


class R088CNYBootstrapTests(TestCase):
    def test_exact_report_and_archive_sha_must_match_account(self):
        with TemporaryDirectory() as tmp:
            folder = Path(tmp)
            archive = folder / ARCHIVE
            archive.write_bytes(b"offline-fixture")
            record = report(archive)
            receipt = folder / "physical.json"
            receipt.write_text(json.dumps(record))
            digest = _check_physical_report(
                report_path=receipt, archive_path=archive,
                robot="v20-shallow", account_id="synthetic-account-01")
            self.assertEqual(digest, sha256(archive.read_bytes()).hexdigest())
            with self.assertRaisesRegex(EXT2HistoryBlocked, "R088_CNY_PHYSICAL_PROOF_OR_ACCOUNT_MISMATCH"):
                _check_physical_report(
                    report_path=receipt, archive_path=archive,
                    robot="v20-obv", account_id="synthetic-account-01")
            with self.assertRaisesRegex(EXT2HistoryBlocked, "R088_CNY_PHYSICAL_PROOF_OR_ACCOUNT_MISMATCH"):
                _check_physical_report(
                    report_path=receipt, archive_path=archive,
                    robot="v20-shallow", account_id="synthetic-account-02")
            archive.write_bytes(b"changed")
            with self.assertRaisesRegex(EXT2HistoryBlocked, "R088_CNY_PHYSICAL_ARCHIVE_SHA_MISMATCH"):
                _check_physical_report(
                    report_path=receipt, archive_path=archive,
                    robot="v20-shallow", account_id="synthetic-account-01")

    def test_report_cannot_approve_trading_or_wrong_date(self):
        with TemporaryDirectory() as tmp:
            folder = Path(tmp)
            archive = folder / ARCHIVE
            archive.write_bytes(b"archive")
            receipt = folder / "physical.json"
            record = report(archive)
            for key, value in (
                ("orders_sent", 1), ("live_authorized", True),
                ("last_completed_open_msk", "2026-11-18T15:15:00"),
                ("observed_at_utc", "2026-11-17T12:40:00+00:00")
            ):
                changed = dict(record, **{key: value})
                receipt.write_text(json.dumps(changed))
                with self.assertRaisesRegex(EXT2HistoryBlocked, "R088_CNY_PHYSICAL_PROOF_OR_ACCOUNT_MISMATCH"):
                    _check_physical_report(
                        report_path=receipt, archive_path=archive,
                        robot="v20-shallow", account_id="synthetic-account-01")

    def test_only_two_physically_approved_robots(self):
        with self.assertRaisesRegex(EXT2HistoryBlocked, "R088_CNY_ROBOT_NOT_PHYSICALLY_APPROVED"):
            bootstrap_r088_verified_cny(
                root=Path("c:/v20lab"), robot="v20-inside",
                account_id="synthetic-account-01")


if __name__ == "__main__":
    main()
