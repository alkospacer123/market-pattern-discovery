"""B-only freeze, immutable outputs and protected-tree checks; no trading logic."""
import hashlib
import json
from pathlib import Path
import subprocess
from IntradayLab.tools.equal_high_low_contract import bounded_reads, hashes

ROOT=Path(__file__).resolve().parents[2]
LAB=ROOT/'IntradayLab'
BASE='8db73e6338bc5b89eda385e21167e22c74e5a299'


def config_path(n):
    if n not in (4,7,10): raise ValueError('UNAPPROVED_DURATION')
    return LAB/f'config/high_low_cluster_m5_2023_b{n}_v1.json'


def output_path(n):
    return LAB/f'results/high_low_cluster_m5_2023_b{n}_v1'


def check_output(output,n):
    output=output.resolve()
    if output!=output_path(n).resolve() and not output.is_relative_to((LAB/'work').resolve()):
        raise ValueError('OUTPUT_OUTSIDE_INTRADAYLAB_SCOPE')
    if output.exists() and any(output.iterdir()):
        raise ValueError('IMMUTABLE_OUTPUT_EXISTS')


def verify_freeze(n):
    config=config_path(n)
    freeze=subprocess.check_output(['git','-C',str(ROOT),'log','-1','--diff-filter=A','--format=%H','--',str(config.relative_to(ROOT))],text=True).strip()
    if len(freeze)!=40: raise ValueError('PRE_PNL_FREEZE_COMMIT_REQUIRED')
    raw=config.read_bytes();cfg=json.loads(raw);digest=hashlib.sha256(raw).hexdigest()
    if digest!=config.with_suffix('.sha256').read_text().split()[0]:raise ValueError('CONFIG_HASH')
    if raw!=subprocess.check_output(['git','-C',str(ROOT),'show',freeze+':'+str(config.relative_to(ROOT))]):
        raise ValueError('CONFIG_CHANGED_AFTER_FREEZE')
    for path,expected in cfg['execution_code_sha256'].items():
        current=(ROOT/path).read_bytes()
        if hashlib.sha256(current).hexdigest()!=expected:raise ValueError('FROZEN_CODE_CHANGED '+path)
        if current!=subprocess.check_output(['git','-C',str(ROOT),'show',freeze+':'+path]):
            raise ValueError('CODE_NOT_COMMITTED_AT_FREEZE '+path)
    for duration in (4,7,10):
        other=config_path(duration)
        if other.read_bytes()!=subprocess.check_output(['git','-C',str(ROOT),'show',freeze+':'+str(other.relative_to(ROOT))]):
            raise ValueError('ALL_THREE_MUST_SHARE_FREEZE')
    return cfg,freeze,digest


def protected_check(data_root,cfg):
    manifest=json.loads((ROOT/cfg['scope_manifest']).read_text())
    tracked=subprocess.check_output(['git','-C',str(ROOT),'diff','--name-only',cfg['base_main']],text=True).splitlines()
    untracked=subprocess.check_output(['git','-C',str(ROOT),'ls-files','--others','--exclude-standard'],text=True).splitlines()
    if any(not p.startswith('IntradayLab/') for p in tracked+untracked):raise AssertionError('OUTSIDE_INTRADAYLAB_CHANGE')
    for path,digest in manifest['existing_intraday_sha256'].items():
        if hashlib.sha256((ROOT/path).read_bytes()).hexdigest()!=digest:raise AssertionError('FROZEN_EXISTING_BYTES '+path)
    for path,blob in manifest['protected_git_blobs'].items():
        # Read local protected bytes only for integrity, without parsing market prices.
        actual=subprocess.check_output(['git','-C',str(ROOT),'hash-object','--',path],text=True).strip()
        if actual!=blob:raise AssertionError('PROTECTED_FILE_BYTES '+path)
    if subprocess.check_output(['git','-C',str(data_root),'status','--porcelain=v1','--untracked-files=all'],text=True).strip():
        raise AssertionError('READ_ONLY_DATA_CHANGED')
    if subprocess.check_output(['git','-C',str(data_root),'rev-parse','HEAD'],text=True).strip()!=cfg['source_ref']:
        raise AssertionError('SOURCE_HEAD_CHANGED')
    return dict(status='PASS',base_main=cfg['base_main'],unchanged_existing_intraday_files=len(manifest['existing_intraday_sha256']),
        protected_repository_files=len(manifest['protected_git_blobs']),TradingSystemLab_diff_empty=True,
        outside_IntradayLab_diff_empty=True,market_pattern_data_clean=True,all_frozen_strategies_configs_results_unchanged=True)
