"""#23 M15 journal installer: synthetic broker, no LIVE or H1 file IO."""
from pathlib import Path
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


    def test_readonly_token_can_install_isolated_journal_without_orders(self):
        """Installation is state setup; a TRADING credential is not required."""
        from IntradayLab.m15_robot.step23_install import REPO
        from IntradayLab.m15_robot.live_execution import M15OutboundJournal
        with tempfile.TemporaryDirectory(prefix="m15-install-test-") as d:
            folder = Path(d).resolve()
            (folder / "state").mkdir()
            api = object.__new__(M15FinamReadOnlyAPI)
            with (patch("IntradayLab.m15_robot.step23_install.ROOT", folder),
                  patch.object(M15FinamReadOnlyAPI, "account_id", "M15-SYNTH"),
                  patch.object(M15FinamReadOnlyAPI, "readonly_bound", True),
                  patch("IntradayLab.m15_robot.step23_install.verify_m15_step23_financial_preflight",
                        return_value={"status": "PASS_FINANCIAL_GET_ONLY"}) as proof):
                result = install_m15_journal_once(
                    api=api, m15_account_id="M15-SYNTH",
                    h1_account_id="H1-SEPARATE",
                    runtime_root=folder, repository_root=REPO)
                proof.assert_called_once()
            self.assertTrue(result["m15_persistent_intent_sqlite"])
            self.assertFalse(result["production_authorized"])
            from sqlite3 import connect
            db = connect(folder / "state" / "m15-production-outbound-intents.sqlite3")
            try:
                self.assertEqual(db.execute("PRAGMA integrity_check").fetchone(),
                                 ("ok",))
                self.assertEqual(db.execute("SELECT COUNT(*) FROM outbound").fetchone(),
                                 (0,))
            finally:
                db.close()

    def test_readonly_installer_does_not_reuse_existing_sqlite(self):
        from IntradayLab.m15_robot.step23_install import REPO
        with tempfile.TemporaryDirectory(prefix="m15-install-test-") as d:
            folder = Path(d).resolve()
            (folder / "state").mkdir()
            db = folder / "state" / "m15-production-outbound-intents.sqlite3"
            db.write_bytes(b"existing operator data must not be overwritten")
            api = object.__new__(M15FinamReadOnlyAPI)
            with (patch("IntradayLab.m15_robot.step23_install.ROOT", folder),
                  patch.object(M15FinamReadOnlyAPI, "account_id", "M15-SYNTH"),
                  patch.object(M15FinamReadOnlyAPI, "readonly_bound", True),
                  patch("IntradayLab.m15_robot.step23_install.verify_m15_step23_financial_preflight",
                        return_value={"status": "PASS_FINANCIAL_GET_ONLY"}),
                  self.assertRaisesRegex(M15InstallError, "STATE_ALREADY_PRESENT")):
                install_m15_journal_once(
                    api=api, m15_account_id="M15-SYNTH",
                    h1_account_id="H1-SEPARATE",
                    runtime_root=folder, repository_root=REPO)
            self.assertEqual(db.read_bytes(),
                             b"existing operator data must not be overwritten")

if __name__ == "__main__":
    unittest.main()
