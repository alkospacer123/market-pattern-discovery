"""Compatibility of all earlier standalone Baseline batches; unchanged rules.

Old fixed-output runners are redirected in memory to fresh IntradayLab/work.
Pinned 2023 byte limits apply also to old raw FileIO line-budget readers.
"""
from contextlib import contextmanager
import gzip
import hashlib
import importlib
import io
import json
from pathlib import Path
import shutil
import subprocess
import sys
from unittest.mock import patch

from IntradayLab.tools.verify_data_gap_v2_regressions import LAB, ROOT, BASE, protected_scope


@contextmanager
def raw_read_guard(root):
    cfg=json.loads((LAB/'config/orb_a_base_2023_canonical_v1.json').read_text())
    limits={(root/s['path']).resolve():s['prefix_bytes'] for s in cfg['inputs'].values()}
    receipts=[];original=Path.open
    class Reader(io.FileIO):
        def __init__(self,path):
            super().__init__(path,'rb');self.source_path=path;self.maximum=0;self.total=0
        def read(self,size=-1):
            if size<0 or self.tell()+size>limits[self.source_path]:
                raise ValueError('FORBIDDEN_FUTURE_PRICE_READ')
            value=super().read(size);self.total+=len(value);self.maximum=max(self.maximum,self.tell())
            return value
        def close(self):
            if not self.closed:
                receipts.append(dict(path=str(self.source_path.relative_to(root.resolve())),
                    bytes_read=self.total,maximum_offset=self.maximum,
                    approved_prefix_bytes=limits[self.source_path],bytes_2024_plus_read=0))
            super().close()
        def seek(self,*args):raise ValueError('UNGUARDED_SEEK')
        def readall(self):raise ValueError('UNBOUNDED_SOURCE_READ')
        def readline(self,*args):raise ValueError('UNGUARDED_LINE_READ')
        def readinto(self,*args):raise ValueError('UNGUARDED_READINTO')
    def guarded(path,*args,**kwargs):
        resolved=path.resolve()
        if resolved.is_relative_to(root.resolve()):
            if resolved not in limits or args!=('rb',) or kwargs.get('buffering')!=0:
                raise ValueError('FORBIDDEN_SOURCE_PATH_OR_BUFFERING')
            return Reader(resolved)
        return original(path,*args,**kwargs)
    with patch.object(Path,'open',guarded):yield receipts


def compare(archive, dest):
    verified={};workflow={}
    for path in sorted(dest.iterdir()):
        if path.suffix=='.csv' or path.name.endswith('.csv.gz'):
            old=archive/path.name
            actual=path.read_bytes()
            if not old.exists() and path.suffix=='.csv':
                old=archive/(path.name+'.gz')
                # Published batches use two standard deterministic gzip writers.
                # Reproduce their container too, including its OS header byte.
                if old.exists() and old.read_bytes()[9]==255:
                    buffer=io.BytesIO()
                    with gzip.GzipFile(filename='',mode='wb',compresslevel=9,fileobj=buffer,mtime=0) as zipped:
                        zipped.write(actual)
                    actual=buffer.getvalue()
                else:
                    actual=gzip.compress(actual,compresslevel=9,mtime=0)
            if not old.exists() or old.read_bytes()!=actual:
                raise AssertionError('EARLIER_BYTE_REGRESSION '+str(old))
            verified[old.name]=hashlib.sha256(actual).hexdigest()
        elif path.name in ('results.json','delay_sensitivity.json','correction_history.json'):
            old=archive/path.name
            if old.read_bytes()==path.read_bytes():
                verified[path.name]=hashlib.sha256(path.read_bytes()).hexdigest()
            else:
                before,after=json.loads(old.read_text()),json.loads(path.read_text())
                differences=[k for k in set(before)|set(after) if before.get(k)!=after.get(k)]
                if any(k not in ('verdict','verdicts','next_strategy','stages') for k in differences):
                    raise AssertionError('EARLIER_JSON_ECONOMICS '+path.name+' '+str(differences))
                workflow[path.name]=dict(different_workflow_fields=differences,
                    economics_and_runs_identical=True)
    if not verified:raise AssertionError('NO_EARLIER_ARTIFACTS')
    return dict(status='PASS',byte_identical_result_files=len(verified),sha256=verified,
                workflow_annotation_exceptions=workflow,archived_files_untouched=True)


def verify(root, output, versions=None):
    if output.exists() or not output.resolve().is_relative_to((LAB/'work').resolve()):
        raise ValueError('FRESH_INTRADAYLAB_WORK_REQUIRED')
    output.mkdir(parents=True);receipts={}
    sys.path.insert(0,str(LAB/'tools'))
    batches=(('run_m5_baseline','stage2_m5'),('run_m5_conditional_v2','stage2_m5_conditional_v2'),
        ('run_stage2_architectures','stage2_complete_architectures_v1'),
        ('stage2_vwap_payable_cap','stage2_vwap_payable_cap_v1'),
        ('stage2_exit_only_ablation','stage2_exit_only_ablation_v1'),
        ('run_causal_mtf','stage2_causal_mtf_v1'),
        ('run_squeeze','stage2_squeeze_v1'),('run_squeeze_m15','stage2_squeeze_m15_v1'))
    for module_name, version in batches:
        if versions and version not in versions:continue
        protected_scope(root)
        module=importlib.import_module(module_name)
        archive=LAB/'results'/version;dest=output/version
        with raw_read_guard(root) as reads:
            if module_name in ('run_m5_baseline','run_m5_conditional_v2'):
                dest.mkdir()
                for name in ('input_provenance.json','correction_history.json'):
                    if (archive/name).exists():shutil.copy2(archive/name,dest/name)
                with patch.object(module,'DEST',dest):module.run(root)
            elif module_name in ('run_squeeze','run_squeeze_m15'):
                with patch.object(sys,'argv',[module_name,'--data-root',str(root),'--output',str(dest)]):
                    module.main()
                if module_name=='run_squeeze_m15':
                    finalized=output/(version+'_finalized')
                    importlib.import_module('finalize_squeeze_m15_reporting').finalize(root,dest,finalized)
                    dest=finalized
            else:
                if module_name=='run_causal_mtf':
                    def retained_metadata():
                        metadata=json.loads((archive/'preflight.json').read_text())['retained_files_sha256']
                        for path,digest in metadata.items():
                            if path in ('IntradayLab/ROADMAP.md','IntradayLab/PROJECT_CONTEXT.md'):
                                continue  # These exceptions already exist in the old verifier.
                            current=(ROOT/path).read_bytes()
                            if path=='IntradayLab/README.md':
                                expected=subprocess.check_output(['git','-C',str(ROOT),'show',BASE+':'+path])
                                if current!=expected:raise AssertionError('BASE_README_CHANGED')
                            elif hashlib.sha256(current).hexdigest()!=digest:
                                raise AssertionError('RETAINED_TRADING_FILE '+path)
                        return metadata
                    # README already changed in merged main, before this task.
                    # All actual trading/config/result hashes still match freeze.
                    with patch.object(module,'preserved',side_effect=retained_metadata):module.run(root,dest)
                else:
                    module.run(root,dest)
        receipts[version]=dict(**compare(archive,dest),actual_source_reads=reads,
            implementation='Unchanged archived standalone engine; no common Backtester import',
            output_adapter='Only DEST redirected for two fixed-destination runners; unchanged pre-return metadata copied into scratch')
        if module_name=='run_causal_mtf':
            receipts[version]['metadata_exception']='Historical retained README hash predates merged main; README verified byte-identical to task base. Original ROADMAP/PROJECT_CONTEXT exceptions retained. Trading/config/results unchanged.'
        print(version+' byte-identical PASS',flush=True)
        (output/'regressions.json').write_text(json.dumps(receipts,indent=2,sort_keys=True)+'\n')
    return dict(status='PASS',regressions=receipts,protected_scope=protected_scope(root),
        bytes_2024_plus_read=0,bytes_2025_plus_read=0,new_research_or_parameter_search=False)


if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--data-root',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--versions',nargs='+',choices=('stage2_m5','stage2_m5_conditional_v2',
        'stage2_complete_architectures_v1','stage2_vwap_payable_cap_v1',
        'stage2_exit_only_ablation_v1','stage2_causal_mtf_v1',
        'stage2_squeeze_v1','stage2_squeeze_m15_v1'))
    args=p.parse_args();result=verify(args.data_root,args.output,args.versions)
    (args.output/'verification.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print(json.dumps(dict(status=result['status'],batches=len(result['regressions'])),sort_keys=True))
