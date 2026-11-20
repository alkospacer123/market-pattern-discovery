"""Self-contained offline tests, no GitHub or FINAM dependency."""
import pathlib
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))
from r7_dependency_scan import scan, SCHEMA


def git(repo, *args):
    return subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True, text=True)


class TestScanner(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = pathlib.Path(self.tmp.name)
        git(self.root, "init", "-q")
        git(self.root, "config", "user.name", "Tester")
        git(self.root, "config", "user.email", "tester@example.invalid")
        for x in ("V20_TradingSystem_M15", "TradingSystemLab", "BBW", "src/bbw_system", "TradingResearchLab", ".github/workflows"):
            (self.root/x).mkdir(parents=True, exist_ok=True)
        (self.root/"V20_TradingSystem_M15"/"live.py").write_text("from TradingSystemLab.stage8_robot import foo\n", encoding="utf-8")
        (self.root/"TradingResearchLab"/"README.md").write_text("Not import bbw_system, docs only\n", encoding="utf-8")
        (self.root/"TradingSystemLab"/"README.md").write_text("See ../research_domains.md. Do not use BBW/results.\n", encoding="utf-8")
        (self.root/"BBW"/"README.md").write_text("Install src/bbw_system, not FINAM\n", encoding="utf-8")
        (self.root/"src/bbw_system"/"__init__.py").write_text("# historical\n", encoding="utf-8")
        (self.root/"pyproject.toml").write_text("[tool.pytest.ini_options]\ntestpaths=['tests']\n", encoding="utf-8")
        (self.root/".github/workflows"/"ci.yml").write_text("# tests for src/bbw_system\n", encoding="utf-8")
        git(self.root, "add", ".")
        git(self.root, "commit", "-qm", "test fixture")

    def test_scoped_matches_and_manifest(self):
        r = scan(self.root)
        self.assertEqual(r["schema"], SCHEMA)
        self.assertEqual(r["total_tracked"], 7)
        self.assertEqual(r["legacy_bundle_tracked"], 3)
        self.assertFalse(r["tracked_tree_modified"])
        self.assertEqual(r["text_files_scanned"], 7)
        self.assertGreater(r["reference_hits_by_scope"]["protected_or_entrypoint"], 0)
        self.assertEqual(r["verdict"], "LITERAL_SCAN_ONLY_NOT_DEPENDENCY_CLOSURE")
        self.assertFalse((self.root / "report.json").exists())

    def test_reject_mismatch(self):
        with self.assertRaisesRegex(ValueError, "HEAD mismatch"):
            scan(self.root, expected_head="a"*40)

    def test_dirty_flag_without_modification(self):
        (self.root/"BBW"/"README.md").write_text("different but not staged\n", encoding="utf-8")
        r = scan(self.root)
        self.assertTrue(r["tracked_tree_modified"])
        self.assertEqual(git(self.root, "status", "--porcelain").stdout.strip(), "M BBW/README.md")

    def test_no_repo_write(self):
        git(self.root, "status", "--porcelain")
        before = git(self.root, "status", "--porcelain").stdout
        r = scan(self.root)
        after = git(self.root, "status", "--porcelain").stdout
        self.assertEqual(before, after)


if __name__ == "__main__":
    unittest.main()
