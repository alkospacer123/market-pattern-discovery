"""Offline Git mirror/bundle checkpoint tests; never touches real trading files."""
import pathlib
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from r7_git_checkpoint import checkpoint


def g(*args, cwd=None):
    return subprocess.run(["git", *args], cwd=cwd, capture_output=True,
                          text=True, check=True).stdout.strip()


class TestGitCheckpoint(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = pathlib.Path(tmp.name)
        self.src = self.root / "source"
        self.src.mkdir()
        g("init", "-q", "-b", "main", cwd=self.src)
        g("config", "user.name", "Synthetic Test", cwd=self.src)
        g("config", "user.email", "no-real-identity@example.invalid", cwd=self.src)
        (self.src / "README.md").write_text("Test-only, no brokers\n", encoding="utf-8")
        g("add", ".", cwd=self.src)
        g("commit", "-qm", "initial", cwd=self.src)
        g("tag", "test-tag", cwd=self.src)
        g("branch", "feature/source", cwd=self.src)
        self.head = g("rev-parse", "HEAD", cwd=self.src)

    def test_mirror_bundle_clone_and_exact_refs(self):
        dest = self.root / "copy"
        r = checkpoint(str(self.src), dest, self.head)
        self.assertEqual(r["mirror_fsck"], "PASS")
        self.assertEqual(r["cold_git_bundle_clone_fsck"], "PASS")
        self.assertEqual(r["main_sha"], self.head)
        self.assertGreaterEqual(r["refs_count"], 3)
        self.assertTrue((dest / "market-pattern-discovery.bundle").is_file())
        self.assertTrue((dest / "checkpoint-report.json").is_file())
        self.assertTrue((dest / "dependency-report.json").is_file())
        self.assertEqual(r["dependency_legacy_bundle_tracked"], 0)
        self.assertGreaterEqual(r["dependency_text_files_scanned"], 1)
        self.assertEqual(r["independent_media_copy"], "NOT_VERIFIED")
        self.assertEqual(r["r7_checkpoint_status"], "PARTIAL_GIT_ONLY_NOT_FINAL_RECOVERY")

    def test_wrong_expected_sha_fails_no_false_pass(self):
        dest = self.root / "mismatch"
        with self.assertRaisesRegex(ValueError, "main SHA mismatch"):
            checkpoint(str(self.src), dest, "a"*40)
        self.assertFalse((dest / "checkpoint-report.json").exists())

    def test_existing_destination_refused(self):
        dest = self.root / "existing"
        dest.mkdir()
        with self.assertRaisesRegex(ValueError, "already exists"):
            checkpoint(str(self.src), dest, self.head)
        self.assertEqual(list(dest.iterdir()), [])

    def test_destination_inside_source_refused(self):
        with self.assertRaisesRegex(ValueError, "separate"):
            checkpoint(str(self.src), self.src / "backup", self.head)
        self.assertFalse((self.src / "backup").exists())


if __name__ == "__main__":
    unittest.main()
