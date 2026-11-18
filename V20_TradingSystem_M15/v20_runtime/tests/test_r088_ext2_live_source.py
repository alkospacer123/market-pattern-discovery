"""R088 account/calendar binding tests; no FINAM or LIVE state used."""
from __future__ import annotations

from datetime import date
from hashlib import sha256
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest import TestCase, main
from unittest.mock import patch

from V20_TradingSystem_M15.v20_runtime.ext2_history_bridge import EXT2HistoryBlocked
from V20_TradingSystem_M15.v20_runtime.r088_ext2_live_source import (
    configure_r088_ext2_live_source, COVERED,
)


class FakeState:
    missing = None

    def __init__(self, **kwargs):
        self.robot = kwargs["robot_id"]

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return False

    def verified_cursor(self, symbol):
        if symbol == self.missing:
            return None
        return {"last_open_msk": "2026-11-15T17:45:00"}


class R088LiveSourceTests(TestCase):
    def setup(self, root: Path, *, robot="v20-shallow", account="dummy-account",
              source="a" * 40):
        (root / "robots" / robot[4:] / "safety").mkdir(parents=True)
        (root / "r070-candidate").mkdir(parents=True)
        cal = {
            "schema": "v20.r088.moex_main_session_calendar.v1",
            "market": "MOEX_FORTS_MAIN_M15_1000_1745",
            "source_url": "https://www.moex.com/n96571",
            "operator_verified": True,
            "verified_open_days": ["2026-11-15", "2026-11-16", "2026-11-17", "2026-11-18"],
        }
        raw = json.dumps(cal).encode()
        (root / "r070-candidate" / "r088-moex-calendar.json").write_bytes(raw)
        authority = {
            "schema": "v20.r088.ext2.account_release.v1",
            "source_commit": source, "robot_id": robot,
            "account_sha256": sha256(account.encode()).hexdigest(),
            "owner_approved": True,
            "symbols": list(COVERED),
            "calendar_sha256": sha256(raw).hexdigest(),
        }
        file = root / "robots" / robot[4:] / "safety" / "r088-ext2-release.json"
        file.write_text(json.dumps(authority))
        sender = SimpleNamespace(
            source=source, journal=SimpleNamespace(
                robot_id=robot,
                account_hash=sha256(account.encode()).hexdigest(),
                live_runtime=True),
            reader=SimpleNamespace(account_hash=sha256(account.encode()).hexdigest()))
        return sender, file, account, source

    def test_bind_requires_all_three_and_pinned_calendar(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp) / "V20Lab"
            sender, file, account, source = self.setup(root)
            with patch(
                "V20_TradingSystem_M15.v20_runtime.r088_ext2_live_source.R070CandidateCheckpointState",
                FakeState):
                self.assertTrue(configure_r088_ext2_live_source(
                    sender=sender, root=root, robot="v20-shallow",
                    account_id=account, source_commit=source))
                self.assertTrue(callable(sender.r070_verified_history_refresh))
                with self.assertRaisesRegex(EXT2HistoryBlocked, "R088_EXT2_REFRESH_CROSS_ACCOUNT_OR_SYMBOL"):
                    sender.r070_verified_history_refresh(
                        robot="v20-obv", symbol="CNYRUBF",
                        signal_open_msk=None, finam_recent=None, observed_at_msk=None)
                with self.assertRaisesRegex(EXT2HistoryBlocked, "R088_EXT2_REFRESH_CROSS_ACCOUNT_OR_SYMBOL"):
                    sender.r070_verified_history_refresh(
                        robot="v20-shallow", symbol="IMOEXF",
                        signal_open_msk=None, finam_recent=None, observed_at_msk=None)

    def test_no_m15_bootstrap_blocks_binding(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp) / "V20Lab"
            sender, file, account, source = self.setup(root)
            with patch(
                "V20_TradingSystem_M15.v20_runtime.r088_ext2_live_source.R070CandidateCheckpointState",
                FakeState):
                FakeState.missing = "USDRUBF"
                try:
                    with self.assertRaisesRegex(EXT2HistoryBlocked,
                            "R088_EXT2_NOT_ALL_N4_HISTORY_BOOTSTRAPPED"):
                        configure_r088_ext2_live_source(
                            sender=sender, root=root, robot="v20-shallow",
                            account_id=account, source_commit=source)
                finally:
                    FakeState.missing = None
                self.assertIsNone(getattr(sender, "r070_verified_history_refresh", None))

    def test_account_or_calendar_tamper_blocks_binding(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp) / "V20Lab"
            sender, file, account, source = self.setup(root)
            with patch(
                "V20_TradingSystem_M15.v20_runtime.r088_ext2_live_source.R070CandidateCheckpointState",
                FakeState):
                with self.assertRaisesRegex(EXT2HistoryBlocked, "R088_EXT2_LIVE_JOURNAL_ACCOUNT_MISMATCH"):
                    configure_r088_ext2_live_source(
                        sender=sender, root=root, robot="v20-shallow",
                        account_id="other-account", source_commit=source)
                (root / "r070-candidate" / "r088-moex-calendar.json").write_text("changed")
                with self.assertRaisesRegex(EXT2HistoryBlocked, "R088_EXT2_CALENDAR_SOURCE_SHA_UNVERIFIED"):
                    configure_r088_ext2_live_source(
                        sender=sender, root=root, robot="v20-shallow",
                        account_id=account, source_commit=source)

    def test_inside_does_not_require_ext2(self):
        self.assertFalse(configure_r088_ext2_live_source(
            sender=None, root=Path("/missing"), robot="v20-inside",
            account_id="", source_commit=""))
    

if __name__ == "__main__":
    main()
