"""Pinned read-only inputs. No production modules or services imported."""
import csv,hashlib,importlib.util,io,json,subprocess,sys,tarfile
from pathlib import Path
from datetime import datetime,timedelta
from zoneinfo import ZoneInfo
from io_utils import digest,write_json
HERE=Path(__file__).resolve().parent
ROOT=HERE.parent.parent
WORK=ROOT/'work/t3_be1'
DATA=ROOT.parent/'market-pattern-data'
SYMBOLS=('USDRUBF','CNYRUBF','GLDRUBF','IMOEXF')
PINS={'pr518':'d85cf85083d6fea047a1a960c9ead441f7b4a6ed','pr560':'90a0a552c05f9ae280f4f2350fd013ea507ea00f','pr562':'40b59a495936adc8110a60f8c25028bbbc9c2e8d','pr563':'91b36991ea9b559cb318993948b061e154710e2c','pr496':'7d068c7f524ff4ba58bd852c457c28aa5e619738'}
FROZEN=ROOT/'IntradayLab/t3_m15_t1_entry_retest_v1'
EXPECTED=dict(USDRUBF='fef80630080a4e2a5e968d620b663f51acd1b7ab9d5d326a42c68cf2b80c67b8',CNYRUBF='259298733d1528c0d917b100118896009519a9f08bdad33d4b373d9ce86f99b4',GLDRUBF='7381d672485b5687ca2c4d92aa5960c24bb132f527589bae3c622b2dfa20a83d',IMOEXF='a1b9fa6102a955103d61b28e81533ed19de68117e30fd84ceb53e8e617559773')

def git(*args,root=ROOT):return subprocess.check_output(['git','-C',str(root),*args])
def module(name,path):
 spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);sys.modules[name]=m;spec.loader.exec_module(m);return m

def authenticate():
 assert git('rev-parse','HEAD',root=DATA).decode().strip()=='f8486b446cf3d5f9f3cba6dfec32bdef8fd184c8'
 assert not git('status','--porcelain',root=DATA).strip()
 files={}
 for s in SYMBOLS:
  p=DATA/f'forever/{s}/{s}_M15.csv';assert digest(p)==EXPECTED[s];files[str(p.relative_to(DATA))]=digest(p)
 code={}
 for name in ('primary.py','verify.py','io_utils.py','SPEC.json'):
  rel=str((FROZEN/name).relative_to(ROOT));raw=git('show',PINS['pr518']+':'+rel)
  assert raw==(FROZEN/name).read_bytes();code[rel]=digest(FROZEN/name)
 archives={}
 for pin,relative in [('pr560','audit_only/t3_initial_stop_forensics_v1'),('pr562','audit_only/t3_entry_diagnostics_v1'),('pr563','audit_only/t3_m15_stretched_breakout_confirmation_v1')]:
  target=WORK/pin;target.mkdir(parents=True,exist_ok=True)
  data=git('archive',PINS[pin],relative)
  with tarfile.open(fileobj=io.BytesIO(data)) as t:t.extractall(target,filter='data')
  folder=target/relative
  archives[pin]=dict(commit=PINS[pin],archive_sha256=hashlib.sha256(data).hexdigest(),files=len(list(folder.rglob('*'))))
 return dict(pins=PINS,data_commit=git('rev-parse','HEAD',root=DATA).decode().strip(),source_sha256=files,frozen_code_sha256=code,archives=archives,raw_OHLC_copied_into_git=False)

def frozen():return module('frozen_primary518',FROZEN/'primary.py')
def scalar():return module('frozen_scalar518',FROZEN/'verify.py')
def development_frame(symbol):
 import pandas as pd
 rows=[]
 path=DATA/f'forever/{symbol}/{symbol}_M15.csv'
 with path.open() as f:
  for r in csv.DictReader(f,delimiter=';'):
   close=datetime.fromisoformat(r['Datetime'])+timedelta(minutes=15)
   if close>=datetime(2025,1,1):break
   rows.append({k:float(r[k]) for k in ('Open','High','Low','Close','Volume')}|{'at':close})
 frame=pd.DataFrame(rows).set_index('at');frame.index=pd.DatetimeIndex(frame.index).tz_localize('Europe/Moscow')
 return frame

def archive(pin,name):
 relative={'pr560':'audit_only/t3_initial_stop_forensics_v1','pr562':'audit_only/t3_entry_diagnostics_v1','pr563':'audit_only/t3_m15_stretched_breakout_confirmation_v1'}[pin]
 return WORK/pin/relative/name
