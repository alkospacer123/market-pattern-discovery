#!/usr/bin/env python3
"""Deterministic storage only; never changes research rows or old results."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
from independent_corrective_review import encoded,sha
from stage2_architecture_analysis import LAB
from run_stage2_architectures import checksums

ALLOWED=('stage2_architecture_diagnostics','stage2_complete_architectures_v1',
    'stage2_vwap_payable_cap_v1','stage2_exit_only_ablation_v1','stage2_architecture_review')

def pack(dest):
    assert (dest.resolve().parent==(LAB/'results').resolve() and dest.name in ALLOWED) or dest.resolve().is_relative_to(Path('/workspace/work'))
    metadata=json.loads((dest/'packaging.json').read_text()) if (dest/'packaging.json').exists() else {}
    for path in sorted(dest.glob('*.csv')):
        if path.stat().st_size<1024*1024:continue
        data=path.read_bytes();packed=gzip.compress(data,compresslevel=9,mtime=0)
        assert gzip.decompress(packed)==data
        target=path.with_suffix('.csv.gz')
        target.write_bytes(packed)
        metadata[path.name]={'stored_as':target.name,'uncompressed_sha256':hashlib.sha256(data).hexdigest(),
            'uncompressed_bytes':len(data),'compressed_sha256':sha(target),
            'compression':'gzip9, mtime0, lossless exact CSV; decompress before hash comparison'}
        path.unlink()
    (dest/'packaging.json').write_text(encoded(metadata));checksums(dest)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('directories',nargs='*',type=Path);a=p.parse_args()
    for path in a.directories or [LAB/'results'/d for d in ALLOWED]:pack(path)
