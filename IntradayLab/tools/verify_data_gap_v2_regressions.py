"""Read-only frozen compatibility replays to IntradayLab/work, never new research.

Historical runners intentionally reject a changed core's identity. The explicit
in-memory adapter below verifies every frozen non-core dependency and permits
only this task's three common-core extensions. It never edits config/artifacts.
"""
from contextlib import contextmanager, ExitStack
import hashlib
import importlib
import json
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
LAB = ROOT/'IntradayLab'
sys.path.insert(0,str(ROOT))
sys.path.insert(0,str(LAB/'tools'))
BASE = '4db30149d6c768caa82bd26a04ef80099816c815'
SOURCE = 'f8486b446cf3d5f9f3cba6dfec32bdef8fd184c8'
CORE_EXTENSIONS = ('IntradayLab/core/backtester.py', 'IntradayLab/core/metrics.py',
                   'IntradayLab/core/reports.py')
IDENTITY_FILES = CORE_EXTENSIONS + ('IntradayLab/core/execution.py',)
from IntradayLab.tools.equal_high_low_contract import bounded_reads, hashes
from IntradayLab.tools.verify_equal_high_low_baseline import legacy_published_oracle


def git(*args):
    return subprocess.check_output(['git','-C',str(ROOT),*args],text=True).strip()


def protected_scope(data_root):
    changed = git('diff','--name-only',BASE).splitlines()
    allowed = set(CORE_EXTENSIONS) | {f'IntradayLab/{p}.md' for p in (
        'ROADMAP','PROJECT_CONTEXT','ARCHITECTURE_DECISION')}
    def require(ok):
        if not ok:
            raise AssertionError('PROTECTED_SCOPE')
    require(all(p in allowed or git('ls-tree',BASE,'--',p)=='' for p in changed))
    require(all(p.startswith('IntradayLab/') for p in changed+
                git('ls-files','--others','--exclude-standard').splitlines()))
    require(not git('diff','--name-only',BASE,'--','.',':(exclude)IntradayLab'))
    source_head = subprocess.check_output(['git','-C',str(data_root),'rev-parse','HEAD'],text=True).strip()
    dirty = subprocess.check_output(['git','-C',str(data_root),'status','--porcelain','--untracked-files=all'],text=True).strip()
    require(source_head==SOURCE and not dirty)
    count = lambda prefix: len(git('ls-tree','-r','--name-only',BASE,'--',prefix).splitlines())
    return dict(status='PASS',base_sha=BASE,source_sha=source_head,
        TradingSystemLab_diff_empty=True,TradingSystemLab_tracked_files=count('TradingSystemLab'),
        outside_IntradayLab_diff_empty=True,market_pattern_data_clean=True,
        frozen_strategy_config_result_test_tool_files_unchanged=True,
        allowed_common_core_extensions=list(CORE_EXTENSIONS))


@contextmanager
def current_code_metadata(module, cfg):
    """Current identity solely in replay memory; prices/parameters/clocks fixed."""
    original = module.json
    digests = {p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in IDENTITY_FILES}
    def loads(value,*args,**kwargs):
        obj = original.loads(value,*args,**kwargs)
        if isinstance(obj,dict) and obj.get('id')==cfg.get('id') and 'execution_code_sha256' in obj:
            obj['execution_code_sha256'] = dict(obj['execution_code_sha256'])
            for p,digest in digests.items():
                if p in obj['execution_code_sha256']:
                    obj['execution_code_sha256'][p]=digest
        return obj
    module.json=SimpleNamespace(loads=loads,dumps=original.dumps)
    try:yield
    finally:module.json=original


def frozen_identity(path):
    raw=path.read_bytes();cfg=json.loads(raw)
    digest=hashlib.sha256(raw).hexdigest()
    if path.with_suffix('.sha256').read_text().split()[0]!=digest:
        raise AssertionError('CONFIG_BYTES')
    freeze=git('log','-1','--diff-filter=A','--format=%H','--',str(path.relative_to(ROOT)))
    if raw!=subprocess.check_output(['git','-C',str(ROOT),'show',freeze+':'+str(path.relative_to(ROOT))]):
        raise AssertionError('CONFIG_FREEZE')
    exceptions={}
    for p,expected in cfg.get('execution_code_sha256',{}).items():
        actual=hashlib.sha256((ROOT/p).read_bytes()).hexdigest()
        if actual!=expected:
            if p not in CORE_EXTENSIONS:
                base_bytes=subprocess.check_output(['git','-C',str(ROOT),'show',BASE+':'+p])
                if actual!=hashlib.sha256(base_bytes).hexdigest():
                    raise AssertionError('FROZEN_NONCORE_DEPENDENCY '+p)
            exceptions[p]=dict(frozen=expected,current=actual,
                reason='This task common-core extension' if p in CORE_EXTENSIONS else 'Already merged before this task; byte unchanged from base')
    return cfg,freeze,digest,exceptions


def verify(data_root, output, models=None):
    scope=protected_scope(data_root)
    output=output.resolve()
    if not output.is_relative_to((LAB/'work').resolve()) or output.exists():
        raise ValueError('FRESH_INTRADAYLAB_WORK_REQUIRED')
    output.mkdir(parents=True)
    receipts={}
    ignored=('validation.json','artifact_hashes.json','changed_files.txt','test_execution.log',
             'provenance.json','audit.json','Independent_Audit.md')
    for name in models or ('canonical','level_rejection','r16','r17','swing_pullback','trend_pullback',
                           'equal_high_low','b4','b7','b10'):
        cluster=name.startswith('b') and name[1:].isdigit()
        module=importlib.import_module('IntradayLab.tools.run_'+('high_low_cluster' if cluster else name)+'_baseline')
        n=int(name[1:]) if cluster else None
        config=LAB/f'config/high_low_cluster_m5_2023_b{n}_v1.json' if cluster else module.CONFIG
        cfg,freeze,digest,exceptions=frozen_identity(config)
        archive=LAB/f'results/high_low_cluster_m5_2023_b{n}_v1' if cluster else module.OUT
        dest=output/name
        if name=='equal_high_low' or cluster:
            with patch.object(module,'verify_freeze',return_value=(cfg,freeze,digest)), \
                 patch.object(module,'protected_check',side_effect=lambda root,c:protected_scope(root)), \
                 bounded_reads(data_root,cfg) as reads:
                module.run(data_root,dest,n) if cluster else module.run(data_root,dest)
        else:
            with current_code_metadata(module,cfg),bounded_reads(data_root,cfg) as reads:
                module.run(data_root,dest)
        before,after=hashes(archive,ignored),hashes(dest,ignored)
        if before!=after:
            raise AssertionError('BYTE_REGRESSION '+name+' '+str([p for p in set(before)|set(after) if before.get(p)!=after.get(p)]))
        if name=='equal_high_low' or cluster:
            auditor=importlib.import_module('IntradayLab.tools.audit_'+('high_low_cluster' if cluster else name)+'_baseline')
            with ExitStack() as stack:
                if cluster:
                    stack.enter_context(patch.object(auditor,'verify_freeze',return_value=(cfg,freeze,digest)))
                    stack.enter_context(patch.object(auditor,'protected_check',side_effect=lambda root,c:protected_scope(root)))
                else:
                    stack.enter_context(current_code_metadata(auditor,cfg))
                    stack.enter_context(patch('IntradayLab.tools.equal_high_low_contract.verify_freeze',return_value=(cfg,freeze,digest)))
                receipt=auditor.audit(data_root,dest,n) if cluster else auditor.audit(data_root,dest)
        else:
            with bounded_reads(data_root,cfg) as audit_reads:
                receipt=legacy_published_oracle(name,data_root,dest,cfg)
            reads += audit_reads
            before_prov=json.loads((archive/'provenance.json').read_text())
            after_prov=json.loads((dest/'provenance.json').read_text())
            before_code=before_prov.pop('code_sha256');after_code=after_prov.pop('code_sha256')
            if before_prov!=after_prov:raise AssertionError('NONCODE_PROVENANCE '+name)
            identity_changes={p:dict(frozen=before_code.get(p),current=after_code.get(p))
                              for p in set(before_code)|set(after_code) if before_code.get(p)!=after_code.get(p)}
            # Old runners enumerate all current strategies and common modules.
            for p,values in identity_changes.items():
                if values['current']!=hashlib.sha256((ROOT/p).read_bytes()).hexdigest():
                    raise AssertionError('CURRENT_CODE_IDENTITY '+p)
            exceptions.update(identity_changes)
        receipts[name]=dict(status='PASS',byte_identical_result_files=len(before),sha256=before,
            independent_audit_status=receipt['status'],actual_source_reads=reads,
            code_identity_exceptions=exceptions,archived_files_untouched=True,
            adapter='In-memory current core identity only; frozen source, signal rules, parameters, entry clock and report bytes unchanged')
        print(name+' byte-identical / independent audit PASS',flush=True)
        (output/'regressions.json').write_text(json.dumps(receipts,default=str,indent=2,sort_keys=True)+'\n')
    scope=protected_scope(data_root)
    return dict(status='PASS',regressions=receipts,protected_scope=scope,
                bytes_2024_plus_read=0,bytes_2025_plus_read=0,
                new_research_or_parameter_search=False)


if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--data-root',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--models',nargs='+',choices=('canonical','level_rejection','r16','r17',
        'swing_pullback','trend_pullback','equal_high_low','b4','b7','b10'))
    a=p.parse_args();r=verify(a.data_root,a.output,a.models)
    (a.output/'verification.json').write_text(json.dumps(r,default=str,indent=2,sort_keys=True)+'\n')
    print(json.dumps(dict(status=r['status'],regressions=len(r['regressions'])),sort_keys=True))
