"""Synthetic, offline-only regression; no production clone or broker use."""
import importlib.util
from pathlib import Path
import subprocess
import tempfile
import unittest

SOURCE = Path(__file__).with_name('r7_cc_scope_guard.py')
spec = importlib.util.spec_from_file_location('guard', SOURCE)
guard = importlib.util.module_from_spec(spec)
spec.loader.exec_module(guard)


class ScopeTests(unittest.TestCase):
    def git(self, *args):
        return subprocess.check_output(['git', '-C', str(self.path), *args], stderr=subprocess.PIPE).decode().strip()

    def write(self, path, text='data\n'):
        target = self.path / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text)

    def commit(self, message):
        self.git('add', '-A')
        self.git('commit', '-qm', message)
        return self.git('rev-parse', 'HEAD')

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name)
        subprocess.check_call(['git', 'init', '-q', str(self.path)])
        self.git('config', 'user.email', 'offline@example.invalid')
        self.git('config', 'user.name', 'Offline Guard Test')
        self.prefixes = list(guard.ABC)
        for p in self.prefixes:
            self.write(p + '/frozen.txt')
        self.write('TradingSystemLab/keep.py', 'print("h1")\n')
        self.write('IntradayLab/keep.py', 'print("m15")\n')
        self.write('ControlCenter/ci/placeholder', 'cc\n')
        self.write('README.md', 'old\n')
        self.commit('historic root')
        old_commit = self.git('rev-parse', 'HEAD')
        historic_entries = {k:v for k,v in guard.git_tree(self.path, 'HEAD').items() if k != 'ControlCenter'}
        self.write('ControlCenter/ci/protected-main-tree.json', __import__('json').dumps({
            'base_sha': old_commit, 'entries': historic_entries}, indent=2))
        self.commit('historic snapshot')
        historical_blob = self.git('rev-parse', 'HEAD:ControlCenter/ci/protected-main-tree.json')
        self.write('README.md', 'new\n')
        self.write('.github/workflows/check.yml', 'name: test\n')
        self.write('V20_TradingSystem_M15/main.py')
        self.write('TradingResearchLab/readme.md')
        self.write('recovery/README.md')
        self.pin = self.commit('pinned candidate base')
        new_root = {k:v for k,v in guard.git_tree(self.path, self.pin).items() if k != 'ControlCenter'}
        self.drift = {k:v for k,v in new_root.items() if historic_entries.get(k) != v}
        self.saved = (guard.PIN, guard.HISTORIC_SHA, guard.FROZEN_BASELINE_BLOB,
                      guard.HISTORIC_TO_PIN, guard.ABC, guard.ABC_TOTAL)
        guard.PIN = self.pin
        guard.HISTORIC_SHA = old_commit
        guard.FROZEN_BASELINE_BLOB = historical_blob
        guard.HISTORIC_TO_PIN = self.drift
        guard.ABC = {p:1 for p in self.prefixes}
        guard.ABC_TOTAL = len(self.prefixes)
        self.addCleanup(self.restore_constants)

    def restore_constants(self):
        (guard.PIN, guard.HISTORIC_SHA, guard.FROZEN_BASELINE_BLOB,
         guard.HISTORIC_TO_PIN, guard.ABC, guard.ABC_TOTAL) = self.saved

    def clean_candidate(self):
        for p in self.prefixes:
            (self.path / (p + '/frozen.txt')).unlink()
        return self.commit('delete only six historical studies')

    def result(self, phase):
        return guard.audit(self.path, phase)

    def test_01_original_pass(self):
        self.assertEqual(self.result('baseline')['deleted_abc_files'], 0)

    def test_02_exact_cleanup_pass(self):
        self.clean_candidate()
        self.assertEqual(self.result('cleanup')['deleted_abc_files'], 6)

    def test_03_original_rejects_cleanup(self):
        self.clean_candidate()
        with self.assertRaises(guard.ScopeFailure): self.result('baseline')

    def test_04_partial_cleanup_rejected(self):
        (self.path / (self.prefixes[0] + '/frozen.txt')).unlink()
        self.commit('partial removal')
        with self.assertRaises(guard.ScopeFailure): self.result('cleanup')

    def test_05_extra_deleted_protected_rejected(self):
        self.clean_candidate()
        (self.path / 'TradingSystemLab/keep.py').unlink()
        self.commit('unauthorized delete')
        with self.assertRaises(guard.ScopeFailure): self.result('cleanup')

    def test_06_modified_protected_rejected(self):
        self.clean_candidate()
        self.write('IntradayLab/keep.py', 'changed\n')
        self.commit('unauthorized modification')
        with self.assertRaises(guard.ScopeFailure): self.result('cleanup')

    def test_07_added_protected_rejected(self):
        self.clean_candidate()
        self.write('IntradayLab/extra.txt')
        self.commit('unauthorized addition')
        with self.assertRaises(guard.ScopeFailure): self.result('cleanup')

    def test_08_controlcenter_only_change_allowed(self):
        self.write('ControlCenter/audit_only.py')
        self.commit('CC scope is allowed')
        self.assertEqual(self.result('baseline')['status'], 'PASS')

    def test_09_hist_baseline_tamper_rejected(self):
        self.write('ControlCenter/ci/protected-main-tree.json', '{}')
        self.commit('baseline changed')
        with self.assertRaisesRegex(guard.ScopeFailure, 'HISTORICAL_BASELINE_MODIFIED'):
            self.result('baseline')

    def test_10_other_root_drift_rejected(self):
        self.clean_candidate()
        self.write('recovery/README.md', 'not reviewed\n')
        self.commit('unauthorized recovery edit')
        with self.assertRaises(guard.ScopeFailure): self.result('cleanup')

    def test_11_missing_anchor_rejected(self):
        guard.PIN = '0'*40
        with self.assertRaises(guard.ScopeFailure): self.result('baseline')

    def test_12_replacement_under_removed_prefix_rejected(self):
        self.clean_candidate()
        self.write(self.prefixes[0] + '/new.txt')
        self.commit('incorrect replacement')
        with self.assertRaises(guard.ScopeFailure): self.result('cleanup')


if __name__ == '__main__':
    unittest.main()
