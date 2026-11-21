"""R7 immutable-Git-tree scope guard for a *disposable* cleanup candidate.

This does not execute repository code, read broker state, or mutate Git/worktree.
It is intentionally NOT wired into ControlCenter's CI until reviewed and
validated against the real full Git checkpoint and the candidate branch.

Modes:
  baseline: HEAD has the exact pinned non-ControlCenter tree.
  cleanup:  HEAD differs from the pinned tree ONLY by removing all six frozen
            A/B/C studies and their results, with 11,491 exact paths removed.

The prior ControlCenter protected-main-tree.json is checked, NOT rewritten.
Requires pinned original Git objects to be present (fail closed if shallow).
"""

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import subprocess
import sys

PIN = 'f15d565755b996252081ed49ed5a094ee1e8d820'
HISTORIC_SHA = '0881d1e08b51a564fb54bb7d334d1578fc130400'
FROZEN_BASELINE_BLOB = 'ff07b592289d975fe644a79f9d1d32f32a003d7a'
PROTECTED_PATH = 'ControlCenter/ci/protected-main-tree.json'

# Reviewed drift from the historical CC-03 baseline to the *actual* pinned main.
# No wildcard, no automatic "rebaseline". These are exact original Git objects.
HISTORIC_TO_PIN = {
    '.github': '040000 tree 978a0c4020cd91d0636f2b6f58b4cbe9522c7d51',
    'README.md': '100644 blob b3c0ec9e488f4ff9c8745e6ce19cc090f0ff6319',
    'TradingResearchLab': '040000 tree 2a97da0d42690e1ecb599c6f7062215b787ceca6',
    'V20_TradingSystem_M15': '040000 tree 1581c596cb30760a27e2412c57da815c7b2e5091',
    'recovery': '040000 tree 6d9b791110c719242d50ae8630fb5bd48baa7560',
}

# Entire frozen A/B/C research complexes, not just their large output files.
# Numbers are independently inventoried file counts at PIN, NOT path glob caps.
ABC = {
    'IntradayLab/optimization_a_2023_v1': 19,
    'IntradayLab/results/optimization_a_equal_high_low_2023_v1': 1174,
    'IntradayLab/optimization_b_high_low_cluster_2023_v1': 23,
    'IntradayLab/results/optimization_b_high_low_cluster_2023_v1': 7053,
    'IntradayLab/optimization_c_return_retest_rejection_2023_v1': 24,
    'IntradayLab/results/optimization_c_return_retest_rejection_2023_v1': 3198,
}
ABC_TOTAL = 11491


class ScopeFailure(Exception):
    pass


def git(repo, *args):
    cp = subprocess.run(['git', '-C', str(repo), *args], stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE, check=False)
    if cp.returncode != 0:
        raise ScopeFailure(f'GIT_FAILURE:{args[0]}:{cp.stderr.decode("utf-8", "replace")[-300:]}')
    return cp.stdout


def git_tree(repo, ref, recursive=False):
    args = ['ls-tree', '--full-tree', '-z']
    if recursive:
        args.append('-r')
    args.append(ref)
    result = {}
    for raw in git(repo, *args).split(b'\x00'):
        if not raw:
            continue
        try:
            meta, path = raw.split(b'\t', 1)
            mode, kind, sha = meta.split(b' ', 2)
        except ValueError as exc:
            raise ScopeFailure('INVALID_GIT_TREE') from exc
        # Preserve original raw path as surrogateescapes on Unix/Windows.
        key = path.decode('utf-8', 'surrogateescape')
        if key in result:
            raise ScopeFailure('DUPLICATE_GIT_PATH')
        result[key] = f'{mode.decode()} {kind.decode()} {sha.decode()}'
    return result


def read_historical_baseline(repo):
    recorded_blob = git(repo, 'rev-parse', f'HEAD:{PROTECTED_PATH}').decode().strip()
    if recorded_blob != FROZEN_BASELINE_BLOB:
        raise ScopeFailure('HISTORICAL_BASELINE_MODIFIED')
    data = json.loads(git(repo, 'show', f'HEAD:{PROTECTED_PATH}').decode('utf-8'))
    if data.get('base_sha') != HISTORIC_SHA or not isinstance(data.get('entries'), dict):
        raise ScopeFailure('HISTORICAL_BASELINE_SCHEMA')
    return data['entries']


def bucket(path):
    for prefix in ABC:
        if path.startswith(prefix + '/'):
            return prefix
    return None


def audit(repo, phase):
    repo = Path(repo)
    if phase not in ('baseline', 'cleanup'):
        raise ScopeFailure('INVALID_PHASE')
    if git(repo, 'rev-parse', '--show-toplevel').decode().strip() != str(repo.resolve()):
        raise ScopeFailure('ROOT_MUST_BE_GIT_TOPLEVEL')
    original = read_historical_baseline(repo)
    anchor_root = git_tree(repo, PIN)
    head_root = git_tree(repo, 'HEAD')
    original_expected = dict(original)
    original_expected.update(HISTORIC_TO_PIN)
    if {k: v for k, v in anchor_root.items() if k != 'ControlCenter'} != original_expected:
        raise ScopeFailure('PIN_DOES_NOT_MATCH_HISTORIC_AND_EXACT_REVIEWED_DRIFT')
    pin = {k: v for k, v in git_tree(repo, PIN, recursive=True).items()
           if not k.startswith('ControlCenter/')}
    current = {k: v for k, v in git_tree(repo, 'HEAD', recursive=True).items()
               if not k.startswith('ControlCenter/')}
    # Git submodule/symlink/future exotic types cannot silently bypass audit:
    # recursive Git tree gives every tracked item and preserves mode+kind+SHA.
    before_count = Counter(bucket(p) for p in pin if bucket(p))
    if before_count != Counter(ABC):
        raise ScopeFailure(f'PIN_ABC_PATH_COUNTS_MISMATCH:{dict(before_count)}')
    if phase == 'baseline':
        if current != pin or {k: v for k, v in head_root.items()
                              if k != 'ControlCenter'} != original_expected:
            raise ScopeFailure('BASELINE_NON_CC_TREE_CHANGED')
        removed = []
    else:
        removed = sorted(set(pin) - set(current))
        added = sorted(set(current) - set(pin))
        modified = sorted(k for k in pin.keys() & current.keys() if pin[k] != current[k])
        if added or modified:
            raise ScopeFailure(f'UNAUTHORIZED_ADD_OR_MODIFY:added={added[:4]},modified={modified[:4]}')
        actual_counts = Counter(bucket(p) for p in removed)
        if len(removed) != ABC_TOTAL or actual_counts != Counter(ABC):
            raise ScopeFailure(f'UNAUTHORIZED_DELETE:count={len(removed)},groups={dict(actual_counts)}')
        if any(bucket(p) for p in current):
            raise ScopeFailure('FROZEN_STUDY_REMAINS')
        changed_roots = {k for k in set(anchor_root) | set(head_root)
                         if k != 'ControlCenter' and anchor_root.get(k) != head_root.get(k)}
        if changed_roots != {'IntradayLab'}:
            raise ScopeFailure(f'ROOT_DRIFT_OUTSIDE_ABC:{sorted(changed_roots)}')
    return {'status': 'PASS', 'phase': phase, 'pin': PIN,
            'historical_controlcenter_baseline': HISTORIC_SHA,
            'historical_baseline_blob': FROZEN_BASELINE_BLOB,
            'head': git(repo, 'rev-parse', 'HEAD').decode().strip(),
            'protected_non_controlcenter_files_retained': len(current),
            'deleted_abc_files': len(removed),
            'checks': 'EXACT_GIT_MODE_BLOB_SHA_AND_PATH_SET',
            'safety': 'READONLY_NO_LIVE_NO_WORKTREE_MUTATIONS'}


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--repo', default='.')
    p.add_argument('--phase', required=True, choices=('baseline', 'cleanup'))
    a = p.parse_args()
    try:
        result = audit(a.repo, a.phase)
        print(json.dumps(result, indent=2))
    except (ScopeFailure, ValueError, json.JSONDecodeError) as exc:
        print(json.dumps({'status': 'FAIL', 'reason': str(exc)}), file=sys.stderr)
        sys.exit(2)


if __name__ == '__main__':
    main()
