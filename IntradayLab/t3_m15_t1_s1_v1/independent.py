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
BASE = '249a9f58a726416bee9d3efd259a9824d348e292'
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

def simulate(bars,symbol,version,rule):
    """Independent position state machine: settle old Stop, then surviving Close."""
    trail=VERSIONS[version];ids={'version':version,'rule':rule,'instrument':symbol}
    t,d,e,g,snap=[],[],[],[],[];q=None;previous=None;last=None
    alias={'USDRUBF':'Si','CNYRUBF':'CNY'}.get(symbol,symbol)
    def opened(q,b):
        return ids|{'trade_id':q['id'],'direction':'LONG' if q['sign']==1 else 'SHORT',
            'entry_time':q['at'],'entry_price':q['entry'],'initial_stop':q['initial'],
            'initial_risk':q['risk'],'active_stop':q['stop'],'breakout_level':q['level'],
            'last_close':b['at'],'last_close_price':b['c'],
            'unrealized_gross_R_at_last_close':q['sign']*(b['c']-q['entry'])/q['risk'],
            'pending_exit_decision':None,'status':'OPEN_NOT_LIQUIDATED_EXCLUDED_FROM_CLOSED_TRADE_METRICS'}
    for i,b in enumerate(bars):
        at=b['at'];assert START<=at<END,'FUTURE_OHLC_FORBIDDEN'
        if q and previous.strftime('%Y-%m')!=at.strftime('%Y-%m'):
            snap.append(opened(q,last)|{'month':previous.strftime('%Y-%m'),'year':previous.year})
        allowed,reason=entry_gate(at,previous,rule)
        delta=(at-previous).total_seconds()/60 if previous else None
        gap=delta is not None and delta>15
        overnight=gap and (at-STEP).date()!=(previous-STEP).date()
        if previous is None or gap:
            g.append(ids|{'current_close':at,'previous_close':previous,'delta_minutes':delta,
                'reason':'NO_PREVIOUS_OBSERVED_CLOSE' if previous is None else 'OBSERVED_GAP_GT_15_MIN',
                'cross_date':bool(gap and at.date()!=previous.date()),'cross_observed_open_date':bool(overnight),
                'original_signal':b['signal'],'entry_rule_pass':allowed,'position_before_bar':q['id'] if q else None})
        exited=None
        if q:
            side=q['sign'];entry=q['entry'];stop=q['stop'];risk=q['risk']
            opening=side*(b['o']-stop)<=0
            hit=opening or (b['l']<=stop if side==1 else b['h']>=stop)
            r=ids|{'trade_id':q['id'],'bar_open_time':at-STEP,'bar_close_time':at,
                'active_stop':stop,'initial_risk':risk,'extreme_before':q['extreme'],
                'open':b['o'],'high':b['h'],'low':b['l'],'ATR_at_close':b['atr'],
                'stop_hit':hit,'stop_gap':opening and b['o']!=stop,
                'observed_gap_before_bar':gap,'observed_overnight_gap_before_bar':bool(overnight)}
            q['gaps']+=int(gap);q['overnights']+=int(overnight)
            if hit:
                fill=min(b['o'],stop) if side==1 else max(b['o'],stop)
                t.append(ids|{'trade_id':q['id'],'direction':'LONG' if side==1 else 'SHORT',
                    'entry_time':q['at'],'entry_price':entry,'initial_stop':q['initial'],'initial_risk':risk,
                    'breakout_level':q['level'],'exit_time':at,'exit_bar_open_time':at-STEP,
                    'exit_bar_close_time':at,'exit_price':fill,'gross_R':side*(fill-entry)/risk,
                    'exit_type':'INITIAL_STOP' if stop==q['initial'] else 'RATCHETED_STOP',
                    'active_stop_at_exit':stop,'trailing_updates':q['updates'],'gap_exit':fill!=stop,
                    'exit_at_open':opening,'rule_decision_time':None,'rule_stop_conflict_at_open':False,
                    'bars_held':i-q['index'],'holding_minutes':(at-q['at']).total_seconds()/60,
                    'MAE_R':max(0.,entry-q['min'] if side==1 else q['max']-entry,side*(entry-fill))/risk,
                    'MFE_R':max(0.,q['max']-entry if side==1 else entry-q['min'])/risk,
                    'cross_calendar_day':at.date()!=q['at'].date(),'year':at.year,
                    'observed_gaps_exposed':q['gaps'],'observed_overnight_gaps_exposed':q['overnights'],**q['features']})
                r.update(phase='EXIT',exit_price=fill,extreme_after=None,trail_proposal=None,
                    active_stop_next_bar=None,trailing_changed=False)
                exited=q['id'];q=None
            else:
                q['min']=min(q['min'],b['l']);q['max']=max(q['max'],b['h'])
                q['extreme']=max(q['extreme'],b['h']) if side==1 else min(q['extreme'],b['l'])
                proposal=q['extreme']-side*trail*b['atr']
                next_stop=max(stop,proposal) if side==1 else min(stop,proposal)
                q['stop']=next_stop;q['updates']+=int(next_stop!=stop)
                r.update(phase='SURVIVED',exit_price=None,extreme_after=q['extreme'],trail_proposal=proposal,
                    active_stop_next_bar=next_stop,trailing_changed=next_stop!=stop)
            d.append(r)
        if math.isfinite(b['atr']) and b['signal']:
            busy=q is not None;accept=allowed and not busy
            tid=f'T3-M15-{alias}-{len(t)+1:06d}' if accept else None
            e.append(ids|{'signal_time':at,'previous_observed_close':previous,'delta_minutes':delta,
                'moscow_hour':at.astimezone(TZ).hour,'direction':'LONG' if b['signal']==1 else 'SHORT',
                'original_signal':b['signal'],'rule_pass':allowed,'rule_reason':reason,
                'position_occupied':busy,'occupied_trade_id':q['id'] if busy else None,
                'entry_accepted':accept,'decision_reason':'ACCEPTED' if accept else 'RULE_AND_OCCUPIED' if not allowed and busy else 'RULE_BLOCKED' if not allowed else 'POSITION_OCCUPIED',
                'trade_id':tid,'same_close_exit_trade_id':exited,'entry_price':b['c'],
                'candidate_initial_stop':b['c']-b['signal']*2*b['atr'],'ATR':b['atr'],
                'H1AvailableAt':b['h1']['at'],'PriorHigh':b['upper'],'PriorLow':b['lower']})
            if accept:
                side=b['signal'];initial=b['c']-side*2*b['atr'];risk=abs(b['c']-initial)
                assert risk>0 and b['h1']['at']<=at
                h=b['h1'];ph=b['previous_h1']
                f={'ATR':b['atr'],'PreviousATR':b['previous_atr'],'signal_open':b['o'],'signal_high':b['h'],'signal_low':b['l']}
                for name,key in (('ADX','adx'),('Slope','slope'),('ATRRatio','ratio'),('AvailableAt','at')):
                    f['H1'+name]=h[key];f['H1Previous'+name]=ph[key] if ph else None
                q={'id':tid,'sign':side,'entry':b['c'],'initial':initial,'risk':risk,'stop':initial,
                    'at':at,'index':i,'level':b['upper'] if side==1 else b['lower'],'extreme':b['c'],
                    'min':b['c'],'max':b['c'],'updates':0,'gaps':0,'overnights':0,'features':f}
        previous=at;last=b
    op=opened(q,last) if q else None
    if op:snap.append(op|{'month':last['at'].strftime('%Y-%m'),'year':last['at'].year})
    return t,op,d,e,g,snap

def metrics(trades,months,opened=0):
    ordered=sorted(trades,key=lambda x:(x['exit_time'],x['instrument'],x['trade_id']))
    x=[r['gross_R'] for r in ordered];positive=sum(v for v in x if v>0);negative=-sum(v for v in x if v<0)
    monthly={m:sum(r['gross_R'] for r in ordered if r['exit_time'].strftime('%Y-%m')==m) for m in months}
    peak=equity=dd=0.;streak=longest=0
    for v in x:
        equity+=v;peak=max(peak,equity);dd=max(dd,peak-equity)
        streak=streak+1 if v<0 else 0;longest=max(longest,streak)
    worst=min(monthly,key=monthly.get) if monthly else None
    out={'closed_trades':len(x),'open_positions_at_period_end':opened,'gross_PF':positive/negative if negative else None,
        'gross_R':sum(x),'expectancy_R':sum(x)/len(x) if x else None,'positive_R':positive,'negative_R_volume':negative,
        'max_drawdown_closed_R':dd,'max_consecutive_losses':longest,'calendar_months':len(months),
        'positive_months':sum(v>0 for v in monthly.values()),'negative_months':sum(v<0 for v in monthly.values()),
        'zero_months':sum(v==0 for v in monthly.values()),
        'no_closed_trade_months':sum(not any(r['exit_time'].strftime('%Y-%m')==m for r in ordered) for m in months),
        'worst_month':worst,'worst_month_R':monthly.get(worst),'win_rate':sum(v>0 for v in x)/len(x) if x else None}
    for sign in ('positive','negative','zero'):out[sign+'_month_share']=out[sign+'_months']/len(months) if months else None
    streak=longest=0
    for v in monthly.values():streak=streak+1 if v<0 else 0;longest=max(longest,streak)
    out['max_losing_month_streak']=longest
    wins=sorted((v for v in x if v>0),reverse=True)
    for n in (5,10):
        top=sum(wins[:n]);out.update({f'top{n}_positive_R':top,f'top{n}_share_positive_R':top/positive if positive else None,
            f'gross_R_without_top{n}':sum(x)-top,f'gross_PF_without_top{n}':(positive-top)/negative if negative else None})
    return out

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
