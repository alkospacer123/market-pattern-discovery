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


def entries():
    result = []
    for path in sorted(ROOT.rglob('*')):
        relative = path.relative_to(ROOT)
        if (path == MANIFEST or any(part in EXCLUDED_PARTS for part in relative.parts)
                or path.name in {'receiver-policy.json','source-policy.json'} or not path.is_file()):
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
        if json.loads(MANIFEST.read_text(encoding='utf-8')) != payload:
            raise SystemExit('CC03_MANIFEST_MISMATCH')
        print('CC03_MANIFEST_PASS_READONLY')


if __name__ == '__main__':
    main()
