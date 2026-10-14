"""Separately authored stdlib streaming indicators and dict execution machine.

No primary, frozen engine, io_utils or metrics imports. Reopens source OHLC and
recomputes every feature, signal, entry, stop transition and trade independently.
"""
import argparse,csv,gzip,hashlib,io,json,math
from collections import deque
from datetime import datetime,timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

TZ=ZoneInfo('Europe/Moscow');STEP=timedelta(minutes=15);NAN=float('nan')

class EWM:
    def __init__(self,alpha,min_count):
        self.a=alpha;self.minimum=min_count;self.state=NAN;self.weight=1.;self.count=0
    def update(self,x):
        finite=math.isfinite(x);self.count+=int(finite)
        if math.isfinite(self.state):
            self.weight*=1-self.a
            if finite:
                if self.state!=x:self.state=(self.weight*self.state+self.a*x)/(self.weight+self.a)
                self.weight=1.
        elif finite:self.state=x
        return self.state if self.count>=self.minimum else NAN

def parse(path):
    previous=None
    with open(path,newline='') as f:
        reader=csv.DictReader(f,delimiter=';')
        assert reader.fieldnames==['Ticker','Datetime','Open','High','Low','Close','Volume']
        for r in reader:
            t=datetime.fromisoformat(r['Datetime']).replace(tzinfo=TZ)+STEP
            assert previous is None or t>previous
            previous=t
            b={k:float(r[k]) for k in ('Open','High','Low','Close','Volume')}
            assert all(math.isfinite(x) for x in b.values())
            assert b['Low']<=min(b['Open'],b['Close'])<=max(b['Open'],b['Close'])<=b['High']
            b['at']=t;yield b

def feature_stream(raw):
    ma=EWM(1/14,14);ha=EWM(1/14,14);plus=EWM(1/14,14);minus=EWM(1/14,14)
    adx=EWM(1/14,14);ema=EWM(2/76,75)
    last_close=None;last_h=None;prior=deque(maxlen=20);atr_window=deque(maxlen=20);ema_history=[]
    context=None;day=None;block=[]
    def tr(b,pc):return max(b['High']-b['Low'],abs(b['High']-pc),abs(b['Low']-pc)) if pc is not None else b['High']-b['Low']
    for source in raw:
        b=source.copy();t=b['at']
        b['ATR']=ma.update(tr(b,last_close));last_close=b['Close']
        b['PriorHigh']=max(x['High'] for x in prior) if len(prior)==20 else NAN
        b['PriorLow']=min(x['Low'] for x in prior) if len(prior)==20 else NAN
        prior.append(source)
        if t.date()!=day:day=t.date();block=[]
        block.append(source)
        if len(block)==4:
            if all(block[j]['at']==block[j-1]['at']+STEP for j in (1,2,3)):
                h=dict(High=max(x['High'] for x in block),Low=min(x['Low'] for x in block),Close=b['Close'])
                ar=ha.update(tr(h,last_h['Close'] if last_h else None))
                up=h['High']-last_h['High'] if last_h else NAN
                down=last_h['Low']-h['Low'] if last_h else NAN
                p=plus.update(up if up>0 and up>down else 0.)
                m=minus.update(down if down>0 and down>up else 0.)
                pdi=100*p/ar if ar else NAN;mdi=100*m/ar if ar else NAN
                dx=100*abs(pdi-mdi)/(pdi+mdi) if pdi+mdi else NAN
                ad=adx.update(dx);em=ema.update(h['Close'])
                slope=em-ema_history[-5] if len(ema_history)>=5 else NAN;ema_history.append(em)
                atr_window.append(ar)
                mean=sum(atr_window)/20 if len(atr_window)==20 else NAN
                context=dict(H1EMA=em,H1Slope=slope,H1ADX=ad,H1ATR=ar,H1ATRRatio=ar/mean if mean else NAN,H1Close=h['Close'],H1AvailableAt=t)
                last_h=h
            block=[]
        b.update(context or {k:(None if k=='H1AvailableAt' else NAN) for k in ('H1EMA','H1Slope','H1ADX','H1ATR','H1ATRRatio','H1Close','H1AvailableAt')})
        b['Signal']=0
        if b['H1ADX']>20 and b['H1ATRRatio']>1:
            if b['H1Close']>b['H1EMA'] and b['H1Slope']>0 and b['Close']>b['PriorHigh']:b['Signal']=1
            elif b['H1Close']<b['H1EMA'] and b['H1Slope']<0 and b['Close']<b['PriorLow']:b['Signal']=-1
        yield b

def simulate(bars,symbol,mode):
    results={k:[] for k in ('trades','signals','stops','snapshots','OPEN')}
    state=None;queued=None;previous=None;counter=0;checked=0;model='T1_'+mode+'_TRAIL_3p5'
    def new(signal,price,index,ident):
        sign=signal['Signal'];sl=price-sign*2*signal['ATR'];risk=abs(sl-price)
        assert risk>0 and signal['H1AvailableAt']<=signal['at']
        return dict(signal=signal,side=sign,entry=price,initial=sl,risk=risk,stop=sl,hi=price,lo=price,extreme=price,index=index,id=ident,updates=0,gaps=0)
    def identity(p):
        s=p['signal']
        return dict(model=model,instrument=symbol,trade_id=p['id'],direction='LONG' if p['side']==1 else 'SHORT',signal_time=s['at'],entry_time=s['at'],signal_close=s['Close'],entry_price=p['entry'],initial_stop=p['initial'],initial_risk=p['risk'],ATR=s['ATR'],H1AvailableAt=s['H1AvailableAt'],breakout_level=s['PriorHigh'] if p['side']==1 else s['PriorLow'])
    def boundary(p,b):
        return identity(p)|dict(month=b['at'].strftime('%Y-%m'),last_close=b['at'],last_close_price=b['Close'],active_stop=p['stop'],unrealized_gross_R=p['side']*(b['Close']-p['entry'])/p['risk'],status='OPEN_NOT_LIQUIDATED')
    for index,b in enumerate(bars):
        at=b['at'];exited=None
        if state and previous['at'].strftime('%Y-%m')!=at.strftime('%Y-%m'):results['snapshots'].append(boundary(state,previous))
        if queued:
            s,ix,event=queued
            assert state is None
            if at-s['at']==STEP:
                state=new(s,b['Open'],ix,event['trade_id'])
                event['reason']='EXECUTED_NEXT_OPEN';event['entry_accepted']=True
                event['entry_price']=state['entry'];event['initial_stop']=state['initial'];event['execution_bar_close']=at
            else:event.update(reason='MISSING_ADJACENT_OPEN',next_observed_close=at)
            queued=None
        if state:
            checked+=1;p=state;sign=p['side'];sl=p['stop'];gap=bool(previous and at-previous['at']>STEP)
            p['gaps']+=int(gap)
            open_hit=b['Open']<=sl if sign==1 else b['Open']>=sl
            intrabar=b['Low']<=sl if sign==1 else b['High']>=sl
            hit=open_hit or intrabar
            event=dict(model=model,instrument=symbol,trade_id=p['id'],bar_close=at,active_stop=sl,extreme_before=p['extreme'],ATR=b['ATR'],stop_hit=hit,observed_gap=gap,exit_price=None,next_stop=None,extreme_after=None,proposal=None)
            if hit:
                fill=min(b['Open'],sl) if sign==1 else max(b['Open'],sl)
                results['trades'].append(identity(p)|dict(exit_time=at,exit_bar_open_time=at-STEP,exit_price=fill,gross_R=sign*(fill-p['entry'])/p['risk'],active_stop_at_exit=sl,exit_at_open=open_hit,gap_exit=fill!=sl,exit_type='INITIAL_STOP' if sl==p['initial'] else 'RATCHETED_STOP',trailing_updates=p['updates'],bars_held=index-p['index'],holding_minutes=(at-p['signal']['at']).total_seconds()/60,observed_gaps_exposed=p['gaps'],MFE_R=max(0.,p['hi']-p['entry'] if sign==1 else p['entry']-p['lo'])/p['risk'],MAE_R=max(0.,p['entry']-p['lo'] if sign==1 else p['hi']-p['entry'],sign*(p['entry']-fill))/p['risk']))
                event['exit_price']=fill;exited=p['id'];state=None
            else:
                p['hi']=max(p['hi'],b['High']);p['lo']=min(p['lo'],b['Low']);p['extreme']=p['hi'] if sign==1 else p['lo']
                proposal=p['extreme']-sign*3.5*b['ATR']
                next_sl=max(sl,proposal) if sign==1 else min(sl,proposal)
                p['updates']+=int(next_sl!=sl);p['stop']=next_sl
                event.update(next_stop=next_sl,extreme_after=p['extreme'],proposal=proposal)
            results['stops'].append(event)
        if b['Signal']!=0 and math.isfinite(b['ATR']):
            allowed=10<=at.hour<18;occupied=state is not None;take=allowed and not occupied
            if take:counter=len(results['trades'])+1
            label={'USDRUBF':'Si','CNYRUBF':'CNY'}.get(symbol,symbol)
            tid=f'T3-M15-{label}-{counter:06d}' if take else None
            reason='ACCEPTED' if take else 'OUTSIDE_T1_AND_OCCUPIED' if occupied and not allowed else 'POSITION_OCCUPIED' if occupied else 'OUTSIDE_T1'
            event=dict(model=model,instrument=symbol,signal_time=at,direction='LONG' if b['Signal']==1 else 'SHORT',signal_close=b['Close'],ATR=b['ATR'],H1AvailableAt=b['H1AvailableAt'],PriorHigh=b['PriorHigh'],PriorLow=b['PriorLow'],rule_pass=allowed,position_occupied=occupied,occupied_trade_id=state['id'] if occupied else None,same_close_exit_trade_id=exited,entry_accepted=take,reason=reason,trade_id=tid,entry_price=b['Close'] if take else None,initial_stop=b['Close']-b['Signal']*2*b['ATR'] if take else None,execution_bar_close=None,next_observed_close=None)
            results['signals'].append(event)
            if take:
                if mode=='NEXT_OPEN':
                    event.update(reason='PENDING_NEXT_OPEN',entry_accepted=False,entry_price=None,initial_stop=None)
                    queued=(b,index,event)
                else:state=new(b,b['Close'],index,tid)
        previous=b
    if queued:queued[2]['reason']='UNRESOLVED_END_OF_DATA'
    if state:
        results['OPEN'].append(boundary(state,bars[-1]));results['snapshots'].extend(results['OPEN'])
    results['occupancy']=dict(instrument=symbol,model=model,observed_bars=len(bars),stop_checked_bars=checked,denominator=len(bars)-1,occupancy=checked/(len(bars)-1) if len(bars)>1 else None)
    return results

def read(path):
    content=Path(path).read_bytes()
    if str(path).endswith('.gz'):content=gzip.decompress(content)
    return list(csv.DictReader(io.StringIO(content.decode())))

class Check:
    def __init__(self):self.fields=0;self.rows=0;self.diffs=[];self.max_abs={}
    def compare(self,a,b,context):
        assert len(a)==len(b),(context,len(a),len(b))
        self.rows+=len(a)
        for i,(left,right) in enumerate(zip(a,b)):
            for field,value in left.items():
                self.fields+=1;actual=right.get(field,'MISSING');ok=False
                if value is None or isinstance(value,float) and not math.isfinite(value):ok=actual==''
                elif isinstance(value,datetime):ok=value.isoformat()==actual
                elif isinstance(value,bool):ok=str(value)==actual
                elif isinstance(value,(int,float)):
                    delta=abs(float(actual)-value);ok=delta<=1e-8
                    self.max_abs[field]=max(delta,self.max_abs.get(field,0.))
                else:ok=str(value)==actual
                if not ok:self.diffs.append(dict(table=context,row=i,field=field,independent=str(value),primary=actual))

def verify(data,out):
    check=Check();observed_months=set();models={m:{k:[] for k in ('trades','signals','stops','snapshots','OPEN','occupancy')} for m in ('SIGNAL_CLOSE','NEXT_OPEN')}
    for symbol in ('USDRUBF','CNYRUBF','GLDRUBF','IMOEXF'):
        bars=list(feature_stream(parse(data/'forever'/symbol/(symbol+'_M15.csv'))))
        observed_months.update(b['at'].strftime('%Y-%m') for b in bars)
        check.compare(bars,read(out/'features'/(symbol+'.csv.gz')),symbol+' features')
        for mode in models:
            scalar=simulate(bars,symbol,mode)
            for table,value in scalar.items():models[mode][table].extend([value] if table=='occupancy' else value)
    for mode,tables in models.items():
        for table,rows in tables.items():
            path=out/(f'{mode.lower()}_{table}.csv'+('.gz' if table in ('signals','stops') else ''))
            check.compare(rows,read(path),mode+' '+table)
    import independent_stats
    statistics=independent_stats.audit(models,observed_months,out)
    result=dict(status='PASS' if not check.diffs else 'FAIL',compared_rows=check.rows,compared_fields=check.fields,max_abs=check.max_abs,differences=check.diffs,statistics=statistics,implementation='Independent stdlib parser, streaming EWM, daily ordinal H1, dict position replay; no primary/frozen imports',external_human_audit='NOT_PERFORMED')
    (out/'independent_verification.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    assert not check.diffs,check.diffs[:10]
    print(json.dumps({k:result[k] for k in ('status','compared_rows','compared_fields')}))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--data-root',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();verify(a.data_root,a.output)
