"""Pinned read-only research imports and deterministic serialization."""
import csv, gzip, hashlib, importlib, io, json, math, subprocess, sys
from pathlib import Path
from datetime import datetime

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
DATA = Path('/workspace/market-pattern-data')
MAIN = 'c3695b1304aef1acdd889264b3451184f7332bf7'
PROTOCOL = 'e00cf40dc7b45d590e914a5d0f66316eca507769'
PINS = {'pr560': ('90a0a552c05f9ae280f4f2350fd013ea507ea00f', 'audit_only/t3_initial_stop_forensics_v1/'),
        'pr557': ('5836971e7ff8e472d8128c675c4f837b40a036ef', 'audit_only/t3_h1_m15_partial_tp_2r_50/'),
        'pr518': ('d85cf85083d6fea047a1a960c9ead441f7b4a6ed', 'IntradayLab/t3_m15_t1_entry_retest_v1/')}
SYMBOLS = ('USDRUBF', 'CNYRUBF', 'GLDRUBF', 'IMOEXF')

def git(*args, root=ROOT):
    return subprocess.check_output(['git', '-C', str(root), *args])

def digest(raw): return hashlib.sha256(raw).hexdigest()
def sha(path): return digest(Path(path).read_bytes())
def clean(x):
    if isinstance(x, datetime): return x.isoformat()
    if isinstance(x, float) and not math.isfinite(x): return None
    if isinstance(x, dict): return {k: clean(v) for k, v in x.items()}
    if isinstance(x, (tuple, list)): return [clean(v) for v in x]
    if hasattr(x, 'item'): return clean(x.item())
    return x
def js(path, obj):
    Path(path).write_text(json.dumps(clean(obj), indent=2, sort_keys=True, ensure_ascii=False, allow_nan=False)+'\n')
def csvout(path, rows, fields=None):
    fields = fields or list(dict.fromkeys(k for row in rows for k in row))
    b = io.StringIO(newline=''); w = csv.DictWriter(b, fieldnames=fields, lineterminator='\n')
    w.writeheader(); w.writerows(clean(row) for row in rows)
    raw = b.getvalue().encode()
    Path(path).write_bytes(gzip.compress(raw, mtime=0) if str(path).endswith('.gz') else raw)
def csvin(path):
    raw = Path(path).read_bytes()
    if str(path).endswith('.gz'): raw = gzip.decompress(raw)
    return list(csv.DictReader(io.StringIO(raw.decode())))

def archives():
    receipts = []
    for name, (commit, prefix) in PINS.items():
        dest = HERE/'work/archives'/name
        dest.mkdir(parents=True, exist_ok=True)
        paths = git('ls-tree', '-r', '--name-only', commit, prefix).decode().splitlines()
        assert paths, ('MISSING_PIN', name)
        for p in paths:
            rel = p[len(prefix):]; target = dest/rel
            target.parent.mkdir(parents=True, exist_ok=True)
            raw = git('show', commit+':'+p)
            if not target.exists() or target.read_bytes() != raw: target.write_bytes(raw)
        for line in (dest/'SHA256SUMS').read_text().splitlines():
            expected, rel = line.split(None, 1); rel = rel.strip()
            assert sha(dest/rel) == expected, ('ARCHIVE_SHA256', name, rel)
            assert (dest/rel).read_bytes() == git('show', commit+':'+prefix+rel)
            receipts.append(dict(scope=name, commit=commit, path=prefix+rel, sha256=expected))
            if name=='pr518':
                assert (ROOT/(prefix+rel)).read_bytes()==(dest/rel).read_bytes(),('MAIN_PR518_BYTES',rel)
    return receipts

def frozen():
    """Only authenticated archived research and frozen strategy code; no robot imports."""
    path = HERE/'work/archives/pr560'
    if str(path) not in sys.path: sys.path.append(str(path))
    common = importlib.import_module('common')
    common.ROOT = ROOT
    common.git = lambda *args, root=ROOT: git(*args, root=root).decode().strip()
    engines = importlib.import_module('engines')
    return engines
