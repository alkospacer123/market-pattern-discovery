"""Serialization only; never imported by the independent verifier."""
import csv, gzip, hashlib, io, json, math
from datetime import datetime
from pathlib import Path

def clean(x):
    if isinstance(x, datetime): return x.isoformat()
    if isinstance(x, float) and not math.isfinite(x): return None
    if isinstance(x, dict): return {k:clean(v) for k,v in x.items()}
    if isinstance(x, (list,tuple)): return [clean(v) for v in x]
    return x

def digest(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def write_json(path, obj):
    Path(path).write_text(json.dumps(clean(obj), indent=2, sort_keys=True, allow_nan=False, ensure_ascii=False)+'\n')

def write_csv(path, rows, fields=None):
    fields=fields or list(dict.fromkeys(k for row in rows for k in row))
    buff=io.StringIO(newline=''); w=csv.DictWriter(buff,fieldnames=fields,lineterminator='\n')
    w.writeheader(); w.writerows(clean(r) for r in rows)
    raw=buff.getvalue().encode()
    if str(path).endswith('.gz'): raw=gzip.compress(raw,mtime=0)
    Path(path).write_bytes(raw)

def read_csv(path):
    raw=Path(path).read_bytes()
    if str(path).endswith('.gz'): raw=gzip.decompress(raw)
    return list(csv.DictReader(io.StringIO(raw.decode())))
