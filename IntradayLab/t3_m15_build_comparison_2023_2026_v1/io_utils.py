import csv,gzip,hashlib,io,json,math
from datetime import datetime
from pathlib import Path
def plain(x):
 if x.__class__.__name__=='NaTType':return None
 if isinstance(x,dict):return {k:plain(v) for k,v in x.items()}
 if isinstance(x,(list,tuple)):return [plain(v) for v in x]
 if hasattr(x,'isoformat'):return x.isoformat()
 if hasattr(x,'item'):return plain(x.item())
 if isinstance(x,float) and not math.isfinite(x):return None
 return x
def write_json(p,x):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(plain(x),sort_keys=True,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
def write_csv(p,rows):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True)
 fields=sorted(set(k for r in rows for k in r)) or ['status']
 if p.suffix=='.gz':
  with p.open('wb') as raw,gzip.GzipFile(fileobj=raw,filename='',mode='wb',mtime=0) as zipped,io.TextIOWrapper(zipped,encoding='utf-8',newline='') as f:
   w=csv.DictWriter(f,fieldnames=fields,lineterminator='\n');w.writeheader();w.writerows(plain(rows))
 else:
  with p.open('w',encoding='utf-8',newline='') as f:
   w=csv.DictWriter(f,fieldnames=fields,lineterminator='\n');w.writeheader();w.writerows(plain(rows))
def read_csv(p):
 opener=gzip.open if str(p).endswith('.gz') else open
 with opener(p,'rt',encoding='utf-8',newline='') as f:return list(csv.DictReader(f))
def hash_file(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
