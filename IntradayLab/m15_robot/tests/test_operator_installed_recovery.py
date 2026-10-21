"""Reopen the actual M15 durable journal, never an offline replacement."""
import hashlib
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch

from IntradayLab.m15_robot.finam_readonly import M15FinamReadOnlyAPI
from IntradayLab.m15_robot.live_execution import M15OutboundJournal
from IntradayLab.m15_robot.step23_install import REPO, H1_PATH_SENTINEL
from IntradayLab.m15_robot.operator_installed_recovery import (
    M15InstalledRecoveryError, run_installed_recovery_once,
)


class TestInstalledRecovery(TestCase):
    def setUp(self):
        self.temp=TemporaryDirectory(prefix="m15-installed-test-")
        self.root=Path(self.temp.name).resolve()
        (self.root / "state").mkdir()
        (self.root / "state" / "kill-switch.json").write_text(
            '{"state":"HALTED"}', encoding="utf-8")
        self.m15="M15-SYNTH"
        self.h1="H1-SEPARATE"
        self.kw=dict(runtime_root=self.root, repository_root=REPO,
                     h1_runtime_root=H1_PATH_SENTINEL,
                     m15_account_id=self.m15,
                     h1_account_sha256=hashlib.sha256(
                         self.h1.encode()).hexdigest())
        self.api=object.__new__(M15FinamReadOnlyAPI)

    def tearDown(self):
        self.temp.cleanup()

    def call(self):
        with (patch("IntradayLab.m15_robot.operator_installed_recovery.ROOT",
                    self.root),
              patch.object(M15FinamReadOnlyAPI, "readonly_bound", True),
              patch.object(M15FinamReadOnlyAPI, "account_id", self.m15),
              patch.object(M15FinamReadOnlyAPI, "account", return_value={
                  "account_id": self.m15, "status":"ACCOUNT_ACTIVE",
                  "positions":[]}),
              patch.object(M15FinamReadOnlyAPI, "orders", return_value={
                  "orders":[]})):
            return run_installed_recovery_once(
                api=self.api, m15_account_id=self.m15,
                h1_account_id=self.h1, runtime_root=self.root,
                repository_root=REPO)

    def test_requires_installed_db_no_implicit_bootstrap(self):
        with self.assertRaisesRegex(
            M15InstalledRecoveryError, "EXISTING_SQLITE_REQUIRED"):
            self.call()
        self.assertFalse((self.root / "state" /
                          "m15-production-outbound-intents.sqlite3").exists())

    def test_installed_journal_live_frozen_broker_cycle(self):
        journal=M15OutboundJournal(**self.kw)
        journal.close()
        result=self.call()
        self.assertTrue(result["existing_journal_reconciled"])
        self.assertEqual(result["broker_positions"], 0)
        self.assertEqual(result["durable_intents"], 0)
        self.assertFalse(result["live_authorized"])
        heartbeat=self.root/"diagnostics"/"m15-readonly-execution-recovery.json"
        content=json.loads(heartbeat.read_text(encoding="utf-8"))
        self.assertEqual(content["status"], "HALTED_READONLY_RECOVERY")
        self.assertFalse(content["order_post_permitted"])

    def test_fails_closed_on_wrong_m15_account_identity(self):
        journal=M15OutboundJournal(**self.kw)
        journal.close()
        with (patch("IntradayLab.m15_robot.operator_installed_recovery.ROOT",
                    self.root),
              patch.object(M15FinamReadOnlyAPI, "readonly_bound", True),
              patch.object(M15FinamReadOnlyAPI, "account_id", "FOREIGN"),
              self.assertRaisesRegex(M15InstalledRecoveryError,
                                      "IDENTITY_INVALID")):
            run_installed_recovery_once(
                api=self.api, m15_account_id=self.m15,
                h1_account_id=self.h1, runtime_root=self.root,
                repository_root=REPO)
