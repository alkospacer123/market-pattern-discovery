"""Independent stdlib-only timestamp-first, forward causal replay.

No imports of earlier research, its engine, auditor, metrics or dataframes.
Cross-session recursive indicators and prior-20 Donchian deliberately reproduce
the frozen historical specification. H1 is published at its fourth observed
consecutive completed Close in each daily ordinal block, never before.
"""
from collections import deque
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import csv
import hashlib
import io
import json
import math
from pathlib import Path
import subprocess

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent
BASE = 'f1403870abed5097c2c28f89638fc9bccf67fc2c'
DATA_SHA = 'f8486b446cf3d5f9f3cba6dfec32bdef8fd184c8'
TZ = ZoneInfo('Europe/Moscow')
START = datetime(2023, 1, 1, tzinfo=TZ)
END = datetime(2025, 1, 1, tzinfo=TZ)
STEP = timedelta(minutes=15)
SYMBOLS = ('USDRUBF','CNYRUBF','GLDRUBF','IMOEXF')
VERSIONS = {'BASELINE':3., 'OPTIMIZED':3.5}
CALENDAR = [f'{y}-{m:02d}' for y in (2023,2024) for m in range(1,13)]
LABEL = 'GROSS_ONLY / COSTS_DEFERRED / NOT_LIVE_READY'
NAN = float('nan')

def git(*args, root=REPO):
    return subprocess.check_output(['git','-C',str(root),*args])

def historical(path, ref=BASE):
    return git('show',f'{ref}:{path}')

def reference(path):
    return list(csv.DictReader(io.StringIO(historical(path).decode())))

def sha(data):
    return hashlib.sha256(data).hexdigest()

def file_sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda:f.read(1<<20),b''):h.update(b)
    return h.hexdigest()

def plain(x):
    if isinstance(x,datetime):return x.isoformat()
    if isinstance(x,float) and not math.isfinite(x):return None
    if isinstance(x,dict):return {k:plain(v) for k,v in x.items()}
    if isinstance(x,(list,tuple)):return [plain(v) for v in x]
    return x

def write_json(path,x):
    Path(path).write_text(json.dumps(plain(x),indent=2,sort_keys=True,allow_nan=False)+'\n')

def write_csv(path,rows,fields=None):
    fields=fields or list(dict.fromkeys(k for r in rows for k in r))
    with Path(path).open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fields,lineterminator='\n');w.writeheader()
        for r in rows:w.writerow(plain(r))

def parse_prefix(path):
    """Do not even read the numeric suffix of the first 2025+ row."""
    result=[];digest=hashlib.sha256();previous=None
    with Path(path).open('rb') as f:
        header=f.readline()
        assert header.rstrip()==b'Ticker;Datetime;Open;High;Low;Close;Volume'
        digest.update(header)
        while True:
            prefix=bytearray();separators=0
            while separators<2:
                ch=f.read(1)
                if not ch:break
                prefix.extend(ch);separators+=ch==b';'
            if not prefix:break
            assert separators==2,'TRUNCATED_TIMESTAMP'
            at=datetime.fromisoformat(prefix.decode().split(';')[1]).replace(tzinfo=TZ)
            if at>=END:break
            tail=f.readline();digest.update(prefix+tail)
            if at<START:continue
            vals=list(map(float,tail.decode().strip().split(';')))
            assert len(vals)==5 and all(math.isfinite(x) for x in vals)
            o,h,l,c,v=vals
            assert h>=max(o,l,c) and l<=min(o,h,c),'BAD_OHLC'
            assert at.minute%15==0 and at.second==0
            assert previous is None or at>previous,'UNSORTED_OR_DUPLICATE'
            previous=at
            if at+STEP<END:result.append({'at':at+STEP,'o':o,'h':h,'l':l,'c':c,'v':v})
    assert result,'EMPTY_SOURCE'
    return result,digest.hexdigest()

class Recursive:
    """Unadjusted EWM, including weight decay through missing samples."""
    def __init__(self,alpha,minimum):
        self.alpha=alpha;self.minimum=minimum;self.value=NAN;self.weight=1.;self.n=0
    def push(self,x):
        present=math.isfinite(x)
        self.n+=int(present)
        if math.isfinite(self.value):
            self.weight*=1-self.alpha
            if present:
                if self.value!=x:self.value=(self.weight*self.value+self.alpha*x)/(self.weight+self.alpha)
                self.weight=1.
        elif present:self.value=x
        return self.value if self.n>=self.minimum else NAN

def true_range(b,previous):
    return max(b['h']-b['l'],abs(b['h']-previous),abs(b['l']-previous)) if previous is not None else b['h']-b['l']

def build_features(bars):
    """Streaming M15 + H1 state; H1 blocks cannot use unread future bars."""
    atr=Recursive(1/14,14);ha=Recursive(1/14,14);ht=Recursive(1/14,14)
    plus=Recursive(1/14,14);minus=Recursive(1/14,14);adx=Recursive(1/14,14)
    ema=Recursive(2/76,75);emas=[];hatrs=deque(maxlen=20)
    prior=deque(maxlen=20);previous_close=None;previous_atr=NAN
    previous_hbar=None;h1=None;previous_h1=None;block=[];day=None;out=[]
    for source in bars:
        b=dict(source);at=b['at'];assert START<=at<END
        b['atr']=atr.push(true_range(b,previous_close))
        b['previous_atr']=previous_atr;previous_atr=b['atr'];previous_close=b['c']
        b['upper']=max(x['h'] for x in prior) if len(prior)==20 else NAN
        b['lower']=min(x['l'] for x in prior) if len(prior)==20 else NAN
        prior.append(b)
        if at.date()!=day:day=at.date();block=[]
        block.append(b)
        if len(block)==4:
            if all(block[i]['at']-block[i-1]['at']==STEP for i in range(1,4)):
                hb={'at':at,'o':block[0]['o'],'h':max(x['h'] for x in block),
                    'l':min(x['l'] for x in block),'c':b['c']}
                tr=true_range(hb,previous_hbar['c'] if previous_hbar else None)
                av=ht.push(tr);av_atr=ha.push(tr)
                up=hb['h']-previous_hbar['h'] if previous_hbar else NAN
                down=previous_hbar['l']-hb['l'] if previous_hbar else NAN
                pu=plus.push(up if up>down and up>0 else 0.)
                md=minus.push(down if down>up and down>0 else 0.)
                pdi=100*pu/av if av else NAN;mdi=100*md/av if av else NAN
                dx=100*abs(pdi-mdi)/(pdi+mdi) if pdi+mdi else NAN
                a=adx.push(dx);e=ema.push(hb['c'])
                slope=e-emas[-5] if len(emas)>=5 else NAN;emas.append(e)
                hatrs.append(av_atr)
                mean=sum(hatrs)/20 if len(hatrs)==20 else NAN
                ratio=av_atr/mean if mean else NAN
                previous_h1=h1
                h1={'at':at,'adx':a,'slope':slope,'ratio':ratio,'ema':e,'c':hb['c']}
                previous_hbar=hb
            block=[]
        b['h1']=h1;b['previous_h1']=previous_h1;b['signal']=0
        if h1 and h1['adx']>20 and h1['ratio']>1:
            if h1['c']>h1['ema'] and h1['slope']>0 and b['c']>b['upper']:b['signal']=1
            if h1['c']<h1['ema'] and h1['slope']<0 and b['c']<b['lower']:b['signal']=-1
        out.append(b)
    return out

def entry_gate(at,previous,rule):
    assert rule in ('CONTROL','T1','T2')
    assert at.tzinfo is not None
    at=at.astimezone(TZ)
    assert previous is None or at>previous,'NONINCREASING_CLOSE'
    if rule=='CONTROL':return True,'CONTROL'
    if rule=='T1':
        ok=600<=at.hour*60+at.minute<1080
        return ok,'CORE_HOURS' if ok else 'OUTSIDE_CORE_HOURS'
    if previous is None:return False,'NO_PREVIOUS_OBSERVED_CLOSE'
    if at-previous>STEP:return False,'FIRST_BAR_AFTER_OBSERVED_GAP'
    return True,'CONTINUOUS_OBSERVED_CLOSES'

class Comparison:
    def __init__(self):self.fields=0;self.diffs=[];self.maxima={};self.tables=[]
    def value(self,a,r,table,row,field):
        self.fields+=1;delta=None
        if isinstance(a,datetime):
            try:ok=a==datetime.fromisoformat(str(r))
            except (ValueError,TypeError):ok=False
        elif isinstance(a,bool):ok=str(a)==str(r)
        elif isinstance(a,(int,float)):
            if not math.isfinite(a):ok=r in ('',None)
            else:
                try:delta=abs(a-float(r));ok=math.isfinite(delta) and delta<=1e-8
                except (ValueError,TypeError):ok=False
        elif a is None:ok=r in ('',None)
        else:ok=str(a)==str(r)
        if delta is not None:self.maxima[table+'.'+field]=max(delta,self.maxima.get(table+'.'+field,0.))
        if not ok:self.diffs.append({'table':table,'row':row,'field':field,'actual':str(a),'expected':str(r)})
    def rows(self,actual,expected,table,keys,exclude=()):
        sort=lambda r:tuple(str(plain(r.get(k)) or '').replace('T',' ') for k in keys)
        actual=sorted(actual,key=sort);expected=sorted(expected,key=sort)
        self.value(len(actual),len(expected),table,-1,'row_count')
        before=self.fields
        for i,(a,r) in enumerate(zip(actual,expected)):
            for k,v in r.items():
                if k in exclude:continue
                if k not in a:self.diffs.append({'table':table,'row':i,'field':k,'actual':'MISSING','expected':str(v)})
                else:self.value(a[k],v,table,i,k)
        self.tables.append({'table':table,'actual_rows':len(actual),'reference_rows':len(expected),'fields':self.fields-before})

def load_sources(root):
    assert git('rev-parse','HEAD',root=root).decode().strip()==DATA_SHA
    assert not git('status','--porcelain',root=root).strip(),'DATA_DIRTY'
    frames={};sources=[]
    frozen=json.loads(historical('IntradayLab/t3_m15_session_entry_v1/results/SOURCE_MANIFEST.json'))
    for expected in frozen['sources']:
        path=expected['path'];full=file_sha(root/path)
        blob=git('rev-parse',f'{DATA_SHA}:{path}',root=root).decode().strip()
        observed=git('hash-object','--',str(root/path),root=root).decode().strip()
        assert blob==observed==expected['git_blob_sha'] and full==expected['full_sha256'],'SOURCE_HASH_MISMATCH'
        raw,prefix=parse_prefix(root/path);s=expected['instrument'];frames[s]=build_features(raw)
        assert prefix==expected['historical_prefix_sha256'] and len(raw)==expected['used_candles']
        assert raw[0]['at'].isoformat()==expected['first_close'] and raw[-1]['at'].isoformat()==expected['last_close']
        sources.append(expected)
    return frames,sources
