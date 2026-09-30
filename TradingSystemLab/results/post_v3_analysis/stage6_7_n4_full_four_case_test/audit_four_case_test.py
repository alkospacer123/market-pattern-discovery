"""Independent semantic audit: rebuild every producer table from frozen sources."""
from __future__ import annotations
import argparse, json, tempfile
from pathlib import Path
import pandas as pd
from generate_four_case_test import CORE, generate, TOL

def audit(candidate: Path, write_result=True):
    errors=[]
    with tempfile.TemporaryDirectory() as d:
        expected=Path(d); generate(expected)
        for name in CORE:
            try:
                a=pd.read_csv(candidate/name,keep_default_na=False); b=pd.read_csv(expected/name,keep_default_na=False)
                if list(a.columns)!=list(b.columns) or a.shape!=b.shape: errors.append(f'{name}: schema/shape mismatch'); continue
                for c in a.columns:
                    an=pd.to_numeric(a[c],errors='coerce'); bn=pd.to_numeric(b[c],errors='coerce')
                    numeric=an.notna().all() and bn.notna().all()
                    if numeric:
                        bad=(an.astype(float)-bn.astype(float)).abs()>TOL
                    else: bad=a[c].astype(str)!=b[c].astype(str)
                    if bad.any(): errors.append(f'{name}:{c}: semantic mismatch'); break
            except Exception as e: errors.append(f'{name}: {e}')
    result={'status':'PASS' if not errors else 'FAIL','semantic_source_reconstruction':True,'hash_only_check':False,'tolerance':TOL,'errors':errors}
    if write_result: (candidate/'independent_audit_result.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    return result
if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('--candidate',type=Path,default=Path(__file__).parent); a=p.parse_args(); r=audit(a.candidate); print(json.dumps(r)); raise SystemExit(r['status']!='PASS')
