"""Freeze verification and unbuffered source read receipts; no P&L logic."""
from contextlib import contextmanager
import csv
import hashlib
import json
from pathlib import Path
import subprocess
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
STUDY = Path(__file__).resolve().parent
POLICY = STUDY/'OPTIMIZATION_A_POLICY.json'
RESULTS = ROOT/'IntradayLab/results/optimization_a_equal_high_low_2023_v1'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git(*args):
    return subprocess.check_output(['git','-C',str(ROOT),*args],text=True).strip()


def grid(policy):
    with (STUDY/'GRID.csv').open() as stream:
        rows = list(csv.DictReader(stream))
    expected = []
    for t in policy['grid']['touches']:
        for sb in policy['grid']['stop_buffer_ticks']:
            for tp in policy['grid']['target_net_R']:
                expected.append(dict(policy['parameters'], touches=t, stop_buffer_ticks=sb,
                    target_net_R=str(tp), configuration_id=f'A_OPT2023_T{t}_SB{sb}_TP{tp}'))
    if rows != [{k:str(v) for k,v in r.items()} for r in expected]:
        raise ValueError('FULL_FIXED_GRID_REQUIRED')
    return expected


def verify_freeze():
    freeze = git('log','-1','--format=%H','--',str((STUDY/'source_commitments.json').relative_to(ROOT)))
    if len(freeze) != 40:
        raise ValueError('PRE_PNL_FREEZE_COMMIT_REQUIRED')
    manifest = json.loads((STUDY/'source_commitments.json').read_text())
    for path, sha in manifest['dependencies_sha256'].items():
        if digest(ROOT/path) != sha:
            raise ValueError('FROZEN_DEPENDENCY_CHANGED '+path)
        committed = subprocess.check_output(['git','-C',str(ROOT),'show',freeze+':'+path])
        if hashlib.sha256(committed).hexdigest() != sha:
            raise ValueError('DEPENDENCY_NOT_IN_FREEZE '+path)
    committed = subprocess.check_output(['git','-C',str(ROOT),'show',freeze+':'+str((STUDY/'source_commitments.json').relative_to(ROOT))])
    if committed != (STUDY/'source_commitments.json').read_bytes():
        raise ValueError('COMMITMENTS_CHANGED')
    policy = json.loads(POLICY.read_text())
    grid(policy)
    return policy, freeze, manifest


def protected_check(policy):
    changed = git('diff','--name-status',policy['base_main']).splitlines()
    for line in changed:
        status, path = line.split('\t')
        if status != 'A' or not path.startswith('IntradayLab/'):
            raise ValueError('PROTECTED_FILE_CHANGED '+line)
    return dict(status='PASS',base_sha=policy['base_main'],modified_preexisting_files=0,
                baseline_files_unchanged=True,registry_unchanged=True,
                outside_IntradayLab_diff_empty=True,changed_tracked_paths=len(changed))


def output_guard(output):
    output = output.resolve()
    lab = ROOT/'IntradayLab'
    if output != RESULTS and not output.is_relative_to(lab/'work'):
        raise ValueError('OUTPUT_SCOPE')
    if output.exists():
        raise ValueError('IMMUTABLE_OUTPUT_EXISTS')


@contextmanager
def bounded_reads(data_root, policy):
    """Every source open/read is bounded; deny other candle paths and buffering."""
    data_root = data_root.resolve()
    limits = {(data_root/s['path']).resolve():s for s in policy['inputs'].values()}
    receipts = []
    original = Path.open
    class Reader:
        def __init__(self,stream,path):
            self.stream,self.path = stream,path
            self.total=self.lines=self.calls=0
            self.hash=hashlib.sha256()
        def read(self,size=-1):
            spec=limits[self.path]
            if size < 0 or self.stream.tell()+size > spec['prefix_bytes']:
                raise ValueError('FORBIDDEN_FUTURE_CANDLE_READ')
            value=self.stream.read(size)
            self.calls+=1;self.total+=len(value);self.lines+=value.count(b'\n');self.hash.update(value)
            return value
        def __enter__(self): return self
        def __exit__(self,*args):
            offset=self.stream.tell();self.stream.close()
            receipts.append(dict(path=str(self.path.relative_to(data_root)),bytes_read=self.total,
                maximum_offset=offset,lines_read=self.lines,candle_rows_read=max(0,self.lines-1),
                sha256=self.hash.hexdigest(),read_calls=self.calls,source_blob=limits[self.path]['blob'],
                bytes_2024_plus_read=0,rows_2024_plus_read=0))
        def __getattr__(self,name):
            raise ValueError('UNGUARDED_SOURCE_OPERATION '+name)
    def guarded(path,*args,**kwargs):
        resolved=path.resolve()
        if resolved.is_relative_to(data_root) and '.git' not in resolved.relative_to(data_root).parts:
            if resolved not in limits or args!=('rb',) or kwargs!={'buffering':0}:
                raise ValueError('FORBIDDEN_SOURCE_PATH_OR_BUFFERING')
            return Reader(original(path,*args,**kwargs),resolved)
        return original(path,*args,**kwargs)
    with patch.object(Path,'open',guarded):
        yield receipts


def artifact_hashes(folder):
    return {str(p.relative_to(folder)):digest(p) for p in sorted(folder.rglob('*')) if p.is_file()}
