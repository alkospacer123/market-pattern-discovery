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
POLICY = STUDY/'OPTIMIZATION_B_POLICY.json'
RESULTS = ROOT/'IntradayLab/results/optimization_b_high_low_cluster_2023_v1'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git(*args):
    return subprocess.check_output(['git','-C',str(ROOT),*args],text=True).strip()


def grid(policy):
    expected=[];published=[];matrix=[]
    for part in ('primary','stop_check'):
        g=policy['grid'][part]
        for n in g['cluster_bars']:
            for w in g['maximum_width_ticks']:
                for t in g['minimum_boundary_touches']:
                    for sb in g['stop_buffer_ticks']:
                        for tp in g['target_net_R']:
                            ident=f'B_OPT2023_N{n}_W{w}_T{t}_SB{sb}_TP{tp}'
                            spec=dict(policy['parameters'],cluster_bars=n,maximum_width_ticks=w,
                                minimum_boundary_touches=t,stop_buffer_ticks=sb,target_net_R=str(tp),configuration_id=ident)
                            expected.append(spec)
                            published.append(dict(spec,grid_part=part,USDRUBF_evaluate=n<10,CNYRUBF_evaluate=True))
                            for symbol in policy['instruments']:
                                if eligible(spec,symbol):matrix.append(dict(configuration_id=ident,instrument=symbol))
    with (STUDY/'GRID.csv').open() as stream:rows=list(csv.DictReader(stream))
    with (STUDY/'EVALUATION_MATRIX.csv').open() as stream:actual=list(csv.DictReader(stream))
    if rows!=[{k:str(v) for k,v in r.items()} for r in published] or actual!=matrix:
        raise ValueError('FULL_FIXED_GRID_AND_585_MATRIX_REQUIRED')
    if len(expected)!=315 or len({r['configuration_id'] for r in expected})!=315 or len(matrix)!=585:
        raise ValueError('EXACT_UNIQUE_BUDGET')
    return expected


def eligible(spec,symbol):
    return symbol=='CNYRUBF' or symbol=='USDRUBF' and spec['cluster_bars']<10


def verify_freeze():
    freeze = git('log','-1','--format=%H','--',str((STUDY/'source_commitments.json').relative_to(ROOT)))
    if len(freeze) != 40:
        raise ValueError('PRE_PNL_FREEZE_COMMIT_REQUIRED')
    branch=git('branch','--show-current')
    remote=git('ls-remote','origin','refs/heads/'+branch).split()
    if not remote:raise ValueError('FREEZE_BRANCH_NOT_PUBLISHED')
    git('fetch','origin',branch)
    if subprocess.run(['git','-C',str(ROOT),'merge-base','--is-ancestor',freeze,remote[0]]).returncode:
        raise ValueError('FREEZE_NOT_ON_PUBLISHED_BRANCH')
    manifest = json.loads((STUDY/'source_commitments.json').read_text())
    required={str(p.relative_to(ROOT)) for p in (ROOT/'IntradayLab/core').glob('*.py')}
    required.update(str(p.relative_to(ROOT)) for p in STUDY.glob('*.py'))
    required.update(str((STUDY/p).relative_to(ROOT)) for p in (
        'OPTIMIZATION_B_POLICY.json','GRID.csv','EVALUATION_MATRIX.csv','pre_pnl_tests.log',
        'protected_file_sha256.json','preflight.json','PREREGISTRATION.md','github_preflight.json',
        'existing_full_tests.log','existing_tests_receipt.log','synthetic_pipeline_receipt.json','synthetic_pipeline.log','optimization_a_regression_tests.log'))
    required.add('IntradayLab/strategies/high_low_cluster_m5_optimization_b_v1.py')
    required.add('IntradayLab/strategies/__init__.py')
    if not required.issubset(manifest['dependencies_sha256']):raise ValueError('REQUIRED_DEPENDENCY_MISSING')
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
