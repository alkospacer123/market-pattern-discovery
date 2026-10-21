"""#23 M15 journal installer: synthetic broker, no LIVE or H1 file IO."""
from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest.mock import patch

from IntradayLab.m15_robot.finam_readonly import M15FinamReadOnlyAPI
from IntradayLab.m15_robot.step23_install import (
    M15InstallError, install_m15_journal_once, ROOT,
)


class TestM15Step23Install(unittest.TestCase):
    def test_refuses_account_reuse_before_any_broker_call(self):
        api = object.__new__(M15FinamReadOnlyAPI)
        with self.assertRaisesRegex(M15InstallError, "DISTINCT_ACCOUNT"):
            install_m15_journal_once(
                api=api, m15_account_id="same", h1_account_id="same")

    def test_refuses_foreign_runtime_before_get(self):
        api = object.__new__(M15FinamReadOnlyAPI)
        with tempfile.TemporaryDirectory() as folder:
            with self.assertRaisesRegex(M15InstallError, "RUNTIME_OR_SESSION"):
                install_m15_journal_once(
                    api=api, m15_account_id="m15", h1_account_id="h1",
                    runtime_root=Path(folder).resolve())

    def test_refuses_preexisting_live_permission(self):
        api = object.__new__(M15FinamReadOnlyAPI)
        with patch("IntradayLab.m15_robot.step23_install.M15_ORDER_POST_RELEASED", True):
            with self.assertRaisesRegex(M15InstallError, "LIVE_FREEZE"):
                install_m15_journal_once(
                    api=api, m15_account_id="m15", h1_account_id="h1")


if __name__ == "__main__":
    unittest.main()
