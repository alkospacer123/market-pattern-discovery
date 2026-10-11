"""Canonical + two complete repeats, syscall evidence and independent audit."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys

from .contract import ROOT,RESULTS,verify_freeze,artifact_hashes,protected_check,output_guard
from IntradayLab.core.reports import dump


def trace_receipt(path,policy,data_root):
    """Linux syscalls: sum real read return lengths, never trust advertised limits."""
    evidence={s:dict(bytes_read=0,read_calls=0,maximum_offset=0,opens=0) for s in policy['instruments']}
    offsets={};fds={}
    source_paths={str((data_root/spec['path']).resolve()):symbol for symbol,spec in policy['inputs'].items()}
    for line in path.read_text().splitlines():
        # -P restricts trace to the two physical source paths; -s 0 hides contents.
        op=re.search(r'openat\(.*"([^"]+)".*\)\s+= (\d+)<([^>]+)>',line)
        if op and op[3] in source_paths:
            key=(line.split()[0],op[2]);fds[key]=source_paths[op[3]];offsets[key]=0
            evidence[source_paths[op[3]]]['opens']+=1
        read=re.search(r'read\((\d+)<([^>]+)>,.*\)\s+= (\d+)',line)
        if read and read[2] in source_paths:
            symbol=source_paths[read[2]];key=(line.split()[0],read[1]);size=int(read[3])
            offsets[key]=offsets.get(key,0)+size
            e=evidence[symbol];e['bytes_read']+=size;e['read_calls']+=1;e['maximum_offset']=max(e['maximum_offset'],offsets[key])
            if offsets[key]>policy['inputs'][symbol]['prefix_bytes']:raise ValueError('SYSCALL_FUTURE_READ')
        if 'pread64(' in line:raise ValueError('UNEXPECTED_SOURCE_POSITIONED_READ')
        seek=re.search(r'lseek\((\d+)<([^>]+)>, (\d+), (\w+)\)\s+= (\d+)',line)
        if seek and seek[2] in source_paths:
            if seek[3]!='0' or seek[4]!='SEEK_CUR':raise ValueError('UNEXPECTED_SOURCE_SEEK')
    for symbol,e in evidence.items():
        if e['bytes_read']!=policy['inputs'][symbol]['prefix_bytes'] or e['maximum_offset']!=e['bytes_read'] or e['opens']!=1:
            raise ValueError('SYSCALL_EXACT_PREFIX_RECEIPT '+symbol+' '+str(e))
        e.update(rows_2023=policy['inputs'][symbol]['rows_2023'],source_blob=policy['inputs'][symbol]['blob'],
            prefix_sha256=policy['inputs'][symbol]['prefix_sha256'],bytes_2024_plus_read=0)
    return dict(status='PASS',trace_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),instruments=evidence,
                scope='strace read syscalls on both physical source files across parent and descendants; no source content displayed')


def invoke(module,data_root,output,logs,label,policy):
    trace=logs/(label+'.strace');log=logs/(label+'.log')
    cmd=['strace','-f','-yy','-s','0','-e','trace=openat,read,pread64,lseek,close']
    for spec in policy['inputs'].values():cmd+=['-P',str((data_root/spec['path']).resolve())]
    cmd+=['-o',str(trace),sys.executable,'-m',module,'--data-root',str(data_root),'--output',str(output)]
    with log.open('w') as f:
        subprocess.run(cmd,cwd=ROOT,stdout=f,stderr=subprocess.STDOUT,check=True)
    return trace_receipt(trace,policy,data_root)


def validate(data_root,output):
    policy,freeze,_=verify_freeze();output_guard(output)
    lab=ROOT/'IntradayLab';name=output.name+'_'+hashlib.sha256(str(output.resolve()).encode()).hexdigest()[:10]
    logs=lab/'work'/(name+'__validation')
    if logs.exists():raise ValueError('IMMUTABLE_VALIDATION_LOGS_EXIST')
    logs.mkdir(parents=True)
    print('Canonical 144 evaluations running; logs '+str(logs),flush=True)
    source={'canonical':invoke('IntradayLab.optimization_a_2023_v1.runner',data_root,output,logs,'canonical',policy)}
    expected=artifact_hashes(output);repeats=[]
    for number in (1,2):
        target=lab/'work'/(name+f'__repeat_{number}')
        print(f'Full repeat {number}: 144 evaluations',flush=True)
        source[f'repeat_{number}']=invoke('IntradayLab.optimization_a_2023_v1.runner',data_root,target,logs,f'repeat_{number}',policy)
        actual=artifact_hashes(target)
        if actual!=expected:
            failures=[p for p in sorted(set(expected)|set(actual)) if expected.get(p)!=actual.get(p)]
            raise ValueError('NONDETERMINISTIC_FULL_REPEAT '+str(failures))
        repeats.append(dict(repeat=number,evaluations=144,deterministic_artifacts=len(expected),byte_identical=True))
    print('Independent raw-M5 audit: all 144 evaluations',flush=True)
    source['independent_audit']=invoke('IntradayLab.optimization_a_2023_v1.auditor',data_root,output,logs,'independent_audit',policy)
    dump(output/'syscall_read_receipts.json',source)
    # Preserve readable run logs; system-call traces remain scratch, receipts hash them.
    (output/'logs').mkdir()
    for p in sorted(logs.glob('*.log')):shutil.copyfile(p,output/'logs'/p.name)
    protected=protected_check(policy)
    tracked_base=json.loads((ROOT/'IntradayLab/optimization_a_2023_v1/protected_file_sha256.json').read_text())
    for name,sha in tracked_base.items():
        if hashlib.sha256((ROOT/name).read_bytes()).hexdigest()!=sha:
            raise ValueError('PREEXISTING_FILE_BYTES_CHANGED '+name)
    protected['preexisting_files_byte_verified']=len(tracked_base)
    dump(output/'protected_scope.json',protected)
    validation=dict(status='PASS',base_main=policy['base_main'],freeze_commit=freeze,evaluations=144,
        full_repeats=repeats,canonical_artifacts_sha256=expected,independent_audit='PASS',
        syscall_read_checks='PASS',bytes_2024_plus_read=0,protected_scope=protected,
        scope='One frozen 144-evaluation search; repeats verify determinism, not additional parameter trials',
        frozen_code_grid_criteria_changed_after_PNL=False,external_review_pending=True)
    dump(output/'validation.json',validation)
    dump(output/'artifact_hashes.json',artifact_hashes(output))
    print(json.dumps({k:v for k,v in validation.items() if k!='canonical_artifacts_sha256'},sort_keys=True),flush=True)
    return validation


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--data-root',type=Path,required=True);p.add_argument('--output',type=Path,default=RESULTS)
    a=p.parse_args();validate(a.data_root,a.output)
