"""Offline tests for an opt-in V2 Windows launcher; no broker or Task access."""
import contextlib
import io
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest

from TradingSystemLab.stage8_robot.execution_grid import EXECUTION_REVISION
from TradingSystemLab.stage8_robot.launcher_revision_guard import (
    LauncherRevisionError, main, validate_state,
)
from TradingSystemLab.stage8_robot.production_runtime import (
    AMENDED_RUNTIME_SCHEMA, MODE, RUNTIME_SCHEMA,
)
from TradingSystemLab.stage8_robot.specification import ACTIVE_IDENTITY, PRODUCTION_SPECIFICATION_ID
from TradingSystemLab.stage8_robot.state import _SCHEMA


class LauncherRevisionGuardTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.db_path = self.root / "state" / "stage8-12-production.sqlite3"
        self.db_path.parent.mkdir()

    def make_db(self, *, mode="v2", identity_override=None):
        identity = {
            "schema_id": AMENDED_RUNTIME_SCHEMA if mode == "v2" else RUNTIME_SCHEMA,
            "production_specification_id": PRODUCTION_SPECIFICATION_ID,
            "active_identity": ACTIVE_IDENTITY,
            "mode": MODE,
        }
        if mode == "v2":
            identity["execution_revision"] = EXECUTION_REVISION
        if identity_override:
            identity.update(identity_override)
        with contextlib.closing(sqlite3.connect(self.db_path)) as db, db:
            db.executescript(_SCHEMA)
            db.execute("INSERT INTO state(key,value) VALUES(?,?)",
                       ("database_identity", json.dumps(identity)))
        return identity

    def assert_denied(self, mode, expected):
        with self.assertRaises(LauncherRevisionError) as caught:
            validate_state(self.root, mode=mode)
        self.assertEqual(str(caught.exception), expected)

    def test_empty_legacy_preserves_first_install(self):
        validate_state(self.root, mode="legacy")

    def test_legacy_database_matches_only_legacy(self):
        self.make_db(mode="legacy")
        validate_state(self.root, mode="legacy")
        self.assert_denied("v2", "STAGE8_493_LAUNCHER_STATE_REVISION_MISMATCH")

    def test_v2_database_matches_only_explicit_v2(self):
        self.make_db()
        validate_state(self.root, mode="v2")
        self.assert_denied("legacy", "STAGE8_493_LAUNCHER_STATE_REVISION_MISMATCH")

    def test_v2_missing_database_fails_closed(self):
        self.assert_denied("v2", "STAGE8_493_V2_DATABASE_REQUIRED")

    def test_unknown_mode_fails_closed(self):
        self.assert_denied("bogus", "STAGE8_493_LAUNCHER_MODE_INVALID")

    def test_identity_differences_rejected(self):
        for changed in (
            {"schema_id": RUNTIME_SCHEMA},
            {"execution_revision": "fake-revision"},
            {"production_specification_id": "wrong"},
            {"active_identity": "wrong"},
            {"mode": "wrong"},
        ):
            with self.subTest(changed=changed):
                self.db_path.unlink(missing_ok=True)
                self.make_db(identity_override=changed)
                self.assert_denied("v2", "STAGE8_493_LAUNCHER_STATE_REVISION_MISMATCH")

    def test_missing_identity_rejected(self):
        self.make_db()
        with contextlib.closing(sqlite3.connect(self.db_path)) as db, db:
            db.execute("DELETE FROM state WHERE key='database_identity'")
        self.assert_denied("v2", "STAGE8_493_LAUNCHER_STATE_REVISION_MISMATCH")

    def test_symlink_state_rejected_even_if_dangling(self):
        try:
            self.db_path.symlink_to(self.root / "not-a-real-db")
        except (NotImplementedError, OSError):
            self.skipTest("symlinks unavailable")
        self.assert_denied("legacy", "STAGE8_493_LAUNCHER_STATE_PATH_INVALID")
        self.assert_denied("v2", "STAGE8_493_LAUNCHER_STATE_PATH_INVALID")

    def test_powershell_launcher_uses_explicit_revision_and_pre_token_gate(self):
        launcher = (Path(__file__).resolve().parents[1]
                    / "deploy" / "windows" / "run-production.ps1").read_text(encoding="utf-8")
        self.assertIn('    [string]$ExecutionRevision = ""', launcher)
        self.assertIn('STOP_TICK_GRID_V2_FILL_PROPOSED', launcher)
        self.assertIn('if ($ExecutionRevision -cne "") { $args += @("--execution-revision", $ExecutionRevision) }', launcher)
        self.assertLess(launcher.index('launcher_revision_guard'), launcher.index('Get-TradingCredential'))
        self.assertLess(launcher.index('launcher_revision_guard'), launcher.index('$env:FINAM_API_SECRET ='))
        self.assertNotIn('Enable-ScheduledTask', launcher)
        self.assertNotIn('Start-ScheduledTask', launcher)

    def test_bad_schema_rejected(self):
        with contextlib.closing(sqlite3.connect(self.db_path)) as db, db:
            db.execute("CREATE TABLE state(key TEXT, value TEXT)")
        self.assert_denied("v2", "STAGE8_493_LAUNCHER_STATE_UNREADABLE")

    def test_bad_json_rejected(self):
        self.make_db()
        with contextlib.closing(sqlite3.connect(self.db_path)) as db, db:
            db.execute("UPDATE state SET value='not-json' WHERE key='database_identity'")
        self.assert_denied("v2", "STAGE8_493_LAUNCHER_STATE_UNREADABLE")

    def test_explicit_v2_fill_gate_remains_closed(self):
        self.make_db()
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            result = main(["--runtime-root", str(self.root), "--mode", "v2"])
        self.assertEqual(result, 1)
        self.assertEqual(output.getvalue().strip(), "STAGE8_493_V2_RELEASE_AUTHORITY_NOT_VERIFIED")

    def test_legacy_main_on_v2_fails_before_credential(self):
        self.make_db()
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            result = main(["--runtime-root", str(self.root), "--mode", "legacy"])
        self.assertEqual(result, 1)
        self.assertEqual(output.getvalue().strip(), "STAGE8_493_LAUNCHER_STATE_REVISION_MISMATCH")

    def test_legacy_main_on_legacy_succeeds(self):
        self.make_db(mode="legacy")
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            result = main(["--runtime-root", str(self.root), "--mode", "legacy"])
        self.assertEqual(result, 0)
        self.assertEqual(output.getvalue().strip(), "STAGE8_493_LAUNCHER_STATE_GATE_PASS")


if __name__ == "__main__":
    unittest.main()
