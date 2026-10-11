"""Freeze and source-read receipts; contains no signal or trading logic."""
from contextlib import contextmanager
import hashlib
import json
from pathlib import Path
import subprocess
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[2];LAB=ROOT/'IntradayLab'
CONFIG=LAB/'config/equal_high_low_m5_2023_a_v1.json'
OUT=LAB/'results/equal_high_low_m5_2023_a_v1'


def freeze_commit():
    return subprocess.check_output(['git','-C',str(ROOT),'log','-1','--diff-filter=A','--format=%H','--',str(CONFIG.relative_to(ROOT))],text=True).strip()


def verify_freeze():
    freeze=freeze_commit()
    if len(freeze)!=40:
        raise ValueError('PRE_PNL_FREEZE_COMMIT_REQUIRED')
    config_bytes=CONFIG.read_bytes();digest=hashlib.sha256(config_bytes).hexdigest()
    if digest!=CONFIG.with_suffix('.sha256').read_text().split()[0]:
        raise ValueError('CONFIG_HASH')
    committed=subprocess.check_output(['git','-C',str(ROOT),'show',freeze+':'+str(CONFIG.relative_to(ROOT))])
    if config_bytes!=committed:
        raise ValueError('CONFIG_CHANGED_AFTER_FREEZE')
    cfg=json.loads(config_bytes)
    for path,expected in cfg['execution_code_sha256'].items():
        if hashlib.sha256((ROOT/path).read_bytes()).hexdigest()!=expected:
            raise ValueError('FROZEN_CODE_CHANGED '+path)
    return cfg,freeze,digest


def check_output(output):
    output=output.resolve()
    if output!=OUT.resolve() and not output.is_relative_to((LAB/'work').resolve()):
        raise ValueError('OUTPUT_OUTSIDE_DECLARED_INTRADAYLAB_SCOPE')


@contextmanager
def bounded_reads(data_root,cfg):
    """Guard actual Python file reads, including independent LF-budget readers."""
    limits={(data_root/s['path']).resolve():s['prefix_bytes'] for s in cfg['inputs'].values()}
    receipts=[];original=Path.open
    class Reader:
        def __init__(self,stream,path):
            self.stream=stream;self.path=path;self.maximum=0;self.total=0
        def read(self,size=-1):
            if size<0 or self.stream.tell()+size>limits[self.path]:
                raise ValueError('FORBIDDEN_FUTURE_PRICE_READ')
            value=self.stream.read(size);self.total+=len(value);self.maximum=max(self.maximum,self.stream.tell())
            return value
        def __enter__(self):return self
        def __exit__(self,*args):
            self.stream.close();receipts.append(dict(path=str(self.path.relative_to(data_root.resolve())),
                bytes_read=self.total,maximum_offset=self.maximum,approved_prefix_bytes=limits[self.path],bytes_2024_plus_read=0))
        def __getattr__(self,name):
            if name in ('readline','readlines','readinto','seek','__iter__'):
                raise ValueError('UNGUARDED_SOURCE_OPERATION')
            return getattr(self.stream,name)
    def guarded(path,*args,**kwargs):
        resolved=path.resolve()
        if resolved.is_relative_to(data_root.resolve()):
            if resolved not in limits or args!=('rb',) or kwargs.get('buffering')!=0:
                raise ValueError('FORBIDDEN_SOURCE_PATH_OR_BUFFERING')
            return Reader(original(path,*args,**kwargs),resolved)
        return original(path,*args,**kwargs)
    with patch.object(Path,'open',guarded):
        yield receipts


def hashes(folder,excluded=()):
    return {str(p.relative_to(folder)):hashlib.sha256(p.read_bytes()).hexdigest()
        for p in sorted(folder.rglob('*')) if p.is_file() and str(p.relative_to(folder)) not in excluded}


def protected_check(data_root,cfg):
    manifest=json.loads((ROOT/cfg['scope_manifest']).read_text())
    allowed=set(manifest['allowed_existing_changes'])
    changed=subprocess.check_output(['git','-C',str(ROOT),'diff','--name-only',cfg['base_main']],text=True).splitlines()
    if any(not p.startswith('IntradayLab/') for p in changed):
        raise AssertionError('OUTSIDE_INTRADAYLAB_CHANGE')
    kept=0
    for path,digest in manifest['existing_intraday_sha256'].items():
        if path in allowed:continue
        if hashlib.sha256((ROOT/path).read_bytes()).hexdigest()!=digest:
            raise AssertionError('FROZEN_EXISTING_BYTES '+path)
        kept+=1
    if subprocess.check_output(['git','-C',str(data_root),'status','--porcelain=v1','--untracked-files=all'],text=True).strip():
        raise AssertionError('READ_ONLY_DATA_CHANGED')
    if subprocess.check_output(['git','-C',str(data_root),'rev-parse','HEAD'],text=True).strip()!=cfg['source_ref']:
        raise AssertionError('SOURCE_HEAD_CHANGED')
    outside=subprocess.check_output(['git','-C',str(ROOT),'diff','--name-only',cfg['base_main'],'--','.',':(exclude)IntradayLab'],text=True).strip()
    if outside:raise AssertionError('PROTECTED_TREE_DIFF')
    return dict(status='PASS',protected_repository_files=len(manifest['protected_git_blobs']),
        unchanged_existing_intraday_files=kept,allowed_existing_changes=sorted(allowed),
        all_frozen_strategies_configs_results_unchanged=True,TradingSystemLab_diff_empty=True,
        outside_IntradayLab_diff_empty=True,market_pattern_data_clean=True,pr_472_expected_head=manifest['pr_472_head'])
