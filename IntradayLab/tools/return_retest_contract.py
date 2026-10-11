"""C-only freeze/source/scope guards, without trade decisions."""
import hashlib
import json
from pathlib import Path
import subprocess
from IntradayLab.tools.equal_high_low_contract import bounded_reads, hashes

ROOT = Path(__file__).resolve().parents[2]
LAB = ROOT / 'IntradayLab'
CONFIG = LAB / 'config/return_retest_rejection_m5_2023_c_v1.json'
OUT = LAB / 'results/return_retest_rejection_m5_2023_c_v1'
BASE = 'f0e56f5df557ac4eae19af333b6d438524f5f6ff'


def verify_freeze():
    freeze = subprocess.check_output(['git', '-C', str(ROOT), 'log', '-1', '--diff-filter=A',
        '--format=%H', '--', str(CONFIG.relative_to(ROOT))], text=True).strip()
    if len(freeze) != 40:
        raise ValueError('PRE_PNL_FREEZE_COMMIT_REQUIRED')
    raw = CONFIG.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    if digest != CONFIG.with_suffix('.sha256').read_text().split()[0]:
        raise ValueError('CONFIG_HASH')
    if raw != subprocess.check_output(['git', '-C', str(ROOT), 'show', freeze+':'+str(CONFIG.relative_to(ROOT))]):
        raise ValueError('CONFIG_CHANGED_AFTER_FREEZE')
    cfg = json.loads(raw)
    for path, expected in cfg['execution_code_sha256'].items():
        current = (ROOT/path).read_bytes()
        if hashlib.sha256(current).hexdigest() != expected:
            raise ValueError('FROZEN_CODE_CHANGED '+path)
        if current != subprocess.check_output(['git', '-C', str(ROOT), 'show', freeze+':'+path]):
            raise ValueError('DEPENDENCY_NOT_COMMITTED_AT_FREEZE '+path)
    return cfg, freeze, digest


def check_output(output):
    output = output.resolve()
    if output != OUT.resolve() and not output.is_relative_to((LAB/'work').resolve()):
        raise ValueError('OUTPUT_OUTSIDE_C_SCOPE')
    if output.exists() and any(output.iterdir()):
        raise ValueError('IMMUTABLE_OUTPUT_EXISTS')


def protected_check(data_root, cfg):
    manifest = json.loads((ROOT/cfg['scope_manifest']).read_text())
    changed = subprocess.check_output(['git','-C',str(ROOT),'diff','--name-only',BASE],text=True).splitlines()
    untracked = subprocess.check_output(['git','-C',str(ROOT),'ls-files','--others','--exclude-standard'],text=True).splitlines()
    if any(not p.startswith('IntradayLab/') for p in changed+untracked):
        raise AssertionError('OUTSIDE_INTRADAYLAB_CHANGE')
    for path, expected in manifest['existing_intraday_sha256'].items():
        if path not in manifest['allowed_existing_changes'] and hashlib.sha256((ROOT/path).read_bytes()).hexdigest() != expected:
            raise AssertionError('EXISTING_BYTES_CHANGED '+path)
    for path, blob in manifest['protected_git_blobs'].items():
        if subprocess.check_output(['git','-C',str(ROOT),'hash-object','--',path],text=True).strip() != blob:
            raise AssertionError('PROTECTED_BYTES_CHANGED '+path)
    if subprocess.check_output(['git','-C',str(data_root),'status','--porcelain=v1','--untracked-files=all'],text=True).strip():
        raise AssertionError('SOURCE_NOT_CLEAN')
    if subprocess.check_output(['git','-C',str(data_root),'rev-parse','HEAD'],text=True).strip() != cfg['source_ref']:
        raise AssertionError('SOURCE_HEAD')
    return dict(status='PASS', TradingSystemLab_diff_empty=True, common_core_unchanged=True,
        frozen_A_B_results_unchanged=True, source_clean=True,
        protected_repository_files=len(manifest['protected_git_blobs']),
        preserved_intraday_files=len(manifest['existing_intraday_sha256'])-len(manifest['allowed_existing_changes']))
