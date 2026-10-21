"""Package checksum manifest. Default/check is read-only; --write regenerates locally.

Integrity only. Authenticate the release commit and manifest through PR review.
Runtime active policies, environments, wheels, caches and this manifest excluded.
"""
import argparse
from hashlib import sha256
import json
from pathlib import Path

ROOT = Path(__file__).absolute().parents[1]
MANIFEST = ROOT / 'deployment' / 'manifest.json'
EXCLUDED_PARTS = {'.git', '.venv', '__pycache__', '.pytest_cache', 'wheelhouse'}
# The protected, frozen source package on Intel is staged directly under
# C:\Control Center; app, venv and data are separate CC-owned runtime roots.
# Do not hash installed runtime bytes as part of the immutable source package.
RUNTIME_ROOTS = {'app', 'venv', 'data', 'runtime'}


def entries():
    result = []
    # Path ordering is case-sensitive on POSIX and case-insensitive on Windows.
    # Manifest order must use the same portable package-relative spelling.
    for path in sorted(ROOT.rglob('*'), key=lambda item: item.relative_to(ROOT).as_posix()):
        relative = path.relative_to(ROOT)
        if (path == MANIFEST or relative.parts[0] in RUNTIME_ROOTS
                or any(part in EXCLUDED_PARTS for part in relative.parts)
                or path.name in {'receiver-policy.json','source-policy.json','os-policy.json','preflight-policy.json',
                                 'manual-os-policy.json','broker-readonly-policy.json'} or not path.is_file()):
            continue
        if path.is_symlink():
            raise ValueError('PACKAGE_SYMLINK_FORBIDDEN')
        result.append(dict(path=relative.as_posix(), sha256=sha256(path.read_bytes()).hexdigest()))
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write', action='store_true')
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    payload = dict(schema_id='cc03.package-manifest.v1', files=entries())
    if args.write:
        MANIFEST.write_text(json.dumps(payload, indent=2) + '\n', encoding='utf-8')
        print('CC03_MANIFEST_WRITTEN')
    else:
        expected = json.loads(MANIFEST.read_text(encoding='utf-8'))
        if expected != payload:
            old = {entry['path']: entry['sha256'] for entry in expected['files']}
            actual = {entry['path']: entry['sha256'] for entry in payload['files']}
            print(json.dumps(dict(missing=sorted(old.keys()-actual.keys()),
                                  unexpected=sorted(actual.keys()-old.keys()),
                                  changed=sorted(name for name in old.keys() & actual.keys() if old[name] != actual[name]),
                                  order_only=old == actual)))
            raise SystemExit('CC03_MANIFEST_MISMATCH')
        print('CC03_MANIFEST_PASS_READONLY')


if __name__ == '__main__':
    main()
