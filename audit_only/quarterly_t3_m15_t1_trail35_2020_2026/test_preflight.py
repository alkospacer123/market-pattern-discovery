"""Meaningful source-gate checks; these do not validate a trading strategy."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

import preflight as p
import probe_network as n


class SourceGateTests(unittest.TestCase):
    def test_missing_candles_are_unknown_not_zero(self):
        with tempfile.TemporaryDirectory() as tmp:
            rows = p.coverage(Path(tmp))
            self.assertEqual(len(rows), 42)
            self.assertTrue(all(r['state'] == 'NO_DATA' and r['m15_candles'] is None for r in rows))

    def test_new_m15_does_not_silently_clear_gate(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'futures_quarterly/Si/Si_M15.csv'
            path.parent.mkdir(parents=True)
            path.touch()
            with self.assertRaisesRegex(RuntimeError, 'REQUIRES_PILOT'):
                p.coverage(Path(tmp))

    def test_cached_blocked_probe_never_calls_network(self):
        with tempfile.TemporaryDirectory() as tmp:
            cache = Path(tmp)
            url = n.URLS[0]
            meta = cache / (hashlib.sha256(url.encode()).hexdigest() + '.json')
            row = dict(url=url, result='BLOCKED_BY_EXECUTOR_PROXY_BEFORE_PROVIDER', source_sha256=None)
            meta.write_text(json.dumps(row))
            with patch('urllib.request.build_opener', side_effect=AssertionError('NETWORK_RETRY')):
                self.assertEqual(n.probe(url, cache), row)

    def test_corrupted_success_cache_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            cache = Path(tmp)
            url = n.URLS[0]
            key = hashlib.sha256(url.encode()).hexdigest()
            (cache / (key + '.json')).write_text(json.dumps(dict(url=url, source_sha256='wrong')))
            (cache / (key + '.bin')).write_bytes(b'corrupt')
            with self.assertRaisesRegex(RuntimeError, 'CACHE_HASH_MISMATCH'):
                n.probe(url, cache)

    def test_real_sources_and_no_trade_artifacts(self):
        data = Path(os.environ['M15_AUDIT_DATA'])
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            p.run(data, out)
            s = json.loads((out / 'summary.json').read_text())
            self.assertEqual(s['EXPLORATORY_REPLAY'], 'NOT_RUN')
            self.assertIsNone(s['gross_R'])
            self.assertEqual({x.suffix for x in out.iterdir()}, {'.json'})
            manifest = json.loads((out / 'SOURCE_MANIFEST.json').read_text())
            legacy = [r for r in manifest['input_files'] if r['role'] == 'LEGACY_FILENAME_IDENTITY_CHECK']
            self.assertEqual(len(legacy), 22)
            self.assertEqual({t for r in legacy for t in r['observed_tickers']}, {'USDRUBF', 'CNYRUBF'})
            self.assertTrue(all(not r['eligible_for_quarterly_replay'] for r in legacy))
            self.assertTrue(all(r['matches_frozen_518_sha256'] for r in manifest['input_files']
                                if r['role'] == 'FROZEN_N4_CONTROL_ONLY'))

    def test_receipt_rejects_changed_real_git_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            subprocess.run(['git', 'init', '-q', str(repo)], check=True)
            (repo / 'input').write_bytes(b'original')
            subprocess.run(['git', '-C', str(repo), 'add', 'input'], check=True)
            subprocess.run(['git', '-C', str(repo), '-c', 'user.name=Test', '-c',
                            'user.email=test@example.invalid', 'commit', '-qm', 'source'], check=True)
            p.receipt(repo, 'input', 'HEAD')
            (repo / 'input').write_bytes(b'changed')
            with self.assertRaisesRegex(RuntimeError, 'SOURCE_BYTES_CHANGED'):
                p.receipt(repo, 'input', 'HEAD')


if __name__ == '__main__':
    unittest.main(verbosity=2)
