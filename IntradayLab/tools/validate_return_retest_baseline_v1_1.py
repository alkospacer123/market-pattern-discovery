"""Versioned reporting-audit adapter; the frozen C runner/config/results stay unchanged."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
from unittest.mock import patch
from IntradayLab.core.reports import dump
from IntradayLab.tools import validate_return_retest_baseline as frozen
from IntradayLab.tools.audit_return_retest_baseline_v1_1 import audit
from IntradayLab.tools.return_retest_contract import ROOT,LAB,OUT,verify_freeze

REVISION=LAB/'config/return_retest_c_v1_audit_revision_1_1.json'


def validate(data_root,baseline,output):
    verify_freeze()
    commit=subprocess.check_output(['git','-C',str(ROOT),'log','-1','--diff-filter=A','--format=%H','--',str(REVISION.relative_to(ROOT))],text=True).strip()
    if len(commit)!=40:raise ValueError('AUDIT_REVISION_COMMIT_REQUIRED')
    raw=REVISION.read_bytes()
    if raw!=subprocess.check_output(['git','-C',str(ROOT),'show',commit+':'+str(REVISION.relative_to(ROOT))]):
        raise ValueError('AUDIT_REVISION_MANIFEST_CHANGED')
    revision=json.loads(raw)
    for path,digest in revision['code_sha256'].items():
        current=(ROOT/path).read_bytes()
        if hashlib.sha256(current).hexdigest()!=digest or current!=subprocess.check_output(['git','-C',str(ROOT),'show',commit+':'+path]):
            raise ValueError('AUDIT_REVISION_BYTES_CHANGED '+path)
    with patch.object(frozen,'audit',audit):
        receipt=frozen.validate(data_root,baseline,output)
    receipt.update(audit_revision_commit=commit,audit_revision=revision)
    dump(output/'validation.json',receipt);dump(baseline/'validation.json',receipt)
    return receipt


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--data-root',type=Path,required=True)
    p.add_argument('--baseline',type=Path,default=OUT);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();r=validate(a.data_root,a.baseline,a.output);print(r['status'])
