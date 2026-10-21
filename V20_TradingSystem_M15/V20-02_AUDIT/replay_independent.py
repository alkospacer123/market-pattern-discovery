#!/usr/bin/env python3
"""V20-02 read-only independent three-account replay. Does not call the frozen replay engine.
The source V20 signal functions define the frozen strategies, while the two V20
signals and the V4 Inside signal are independently recalculated and cross-checked.
All order simulation below is separate pure-Python code with independent per-account state.
"""
from __future__ import annotations
from pathlib import Path
from collections import defaultdict
import sys, math, hashlib, json
import numpy as np
import pandas as pd

HERE=Path(__file__).resolve().parent
SOURCE=next((p for p in [HERE.parent/'V20_workspace'/'V20_Autonomous', HERE.parent/'V20_Autonomous', HERE/'V20_Autonomous'] if p.is_dir()),None)
if SOURCE is None:raise FileNotFoundError('Place V20_Autonomous beside V20-02_AUDIT, or in V20_workspace')
BASE=SOURCE/'research_original_v20'
sys.dont_write_bytecode=True
OUT=HERE
sys.path.insert(0,str(BASE))
import run as v20
import base as locked

SYMS=['CNYRUBF','GLDRUBF','IMOEXF','USDRUBF']
TICKS=locked.TICKS
ACCOUNTS=[('Shallow Pullback','SHALLOW_PULLBACK'),('OBV Pressure','OBV_PRESSURE'),('Inside Day Release','INSIDE_DAY_RELEASE')]
COLS=['account','account_num','symbol','side','signal_dt','entry_dt','exit_dt','entry','exit','stop','risk','gross_R','net_R','exit_reason','entry_session','session_span']


def sha(path:Path):return hashlib.sha256(path.read_bytes()).hexdigest()
def assert_all(name,actual,expected):
    a=np.asarray(actual); b=np.asarray(expected)
    equal=(len(a)==len(b) and np.array_equal(a,b,equal_nan=True))
    if not equal:
        bad=np.nonzero(a!=b)[0] if len(a)==len(b) else []
        raise AssertionError(f'{name}: mismatch at {bad[:10]} of {len(a)}')
    return len(a)


def independent_signals(d):
    # Independently written from frozen protocol; no call to the original signal
    # assignment for any of the three strategies. Inside Day uses V4 finished sessions.
    o,h,l,c,volume=[d[q].astype(float) for q in ['Open','High','Low','Close','Volume']]
    atr=d.atr
    body=c-o; r=h-l
    mins=d.Datetime.dt.hour*60+d.Datetime.dt.minute
    trend_l=(d.ema50>d.ema200)&(d.ema50>d.ema50.shift(4))
    trend_s=(d.ema50<d.ema200)&(d.ema50<d.ema50.shift(4))
    t=mins.between(600,1020)
    max3=h.shift(1).rolling(3,min_periods=3).max()
    min3=l.shift(1).rolling(3,min_periods=3).min()
    drive=c.shift(3)-c.shift(11)
    a_back=atr.shift(3)
    shallow_l=t&(r>0.5*atr)&trend_l&(drive>1.8*a_back)&(min3>c.shift(3)-0.85*atr)&(c>max3)&(body>0.2*atr)
    shallow_s=t&(r>0.5*atr)&trend_s&(drive < -1.8*a_back)&(max3<c.shift(3)+0.85*atr)&(c<min3)&(body < -0.2*atr)
    shallow=np.select([shallow_l,shallow_s],[1,-1],default=0).astype(np.int8)
    prev_v=volume.shift(1).rolling(20,min_periods=20).mean()
    clv=((c-l)-(h-c))/r.replace(0,np.nan)
    signed=(clv.fillna(0)*volume).shift(1).rolling(12,min_periods=12).sum()
    total=volume.shift(1).rolling(12,min_periods=12).sum().replace(0,np.nan)
    pressure=signed/total
    obv_l=t&(volume>=prev_v)&(r>0.65*atr)&trend_l&(pressure>0.35)&(c>h.shift(1).rolling(10).max())&(body>0.3*atr)
    obv_s=t&(volume>=prev_v)&(r>0.65*atr)&trend_s&(pressure < -0.35)&(c<l.shift(1).rolling(10).min())&(body < -0.3*atr)
    obv=np.select([obv_l,obv_s],[1,-1],default=0).astype(np.int8)
    # Source V4 uses 10:00 to 17:45 inclusive as completed DAY session.
    session=d[(mins>=600)&(mins<1080)].copy()
    ss=session.groupby('day',sort=True).agg(n=('Close','size'),sopen=('Open','first'),sclose=('Close','last'),hi=('High','max'),lo=('Low','min'),first_dt=('Datetime','first'),last_dt=('Datetime','last'))
    ss['valid']=(ss.n>=12)&(ss.first_dt.dt.hour*60+ss.first_dt.dt.minute<=615)&(ss.last_dt.dt.hour*60+ss.last_dt.dt.minute>=1035)
    prior=ss.shift(1); prior2=ss.shift(2)
    # V4 condition requires yesterday and day before yesterday both completed.
    pv=d.day.map(prior.valid).fillna(False).astype(bool)
    ppv=d.day.map(prior2.valid).fillna(False).astype(bool)
    ph=d.day.map(prior.hi);pl=d.day.map(prior.lo)
    pph=d.day.map(prior2.hi);ppl=d.day.map(prior2.lo)
    inside=(pv&ppv)&(ph<pph)&(pl>ppl)
    allowed=(mins>=600)&(mins<1020)
    inside_l=allowed&inside&trend_l&(c>ph)&(c.shift(1)<=ph)
    inside_s=allowed&inside&trend_s&(c<pl)&(c.shift(1)>=pl)
    inside_sig=np.select([inside_l,inside_s],[1,-1],default=0).astype(np.int8)
    return {'SHALLOW_PULLBACK':shallow,'OBV_PRESSURE':obv,'INSIDE_DAY_RELEASE':inside_sig}


def load_signals():
    ds={}; summary=[]
    for sym in SYMS:
        d=v20.signals(sym)
        calc=independent_signals(d)
        v4=pd.read_csv(BASE/'inside_day_signals'/f'{sym}.csv.gz',compression='gzip',parse_dates=['Datetime'])
        assert_all(f'{sym} V4 datetime',d.Datetime.to_numpy(),v4.Datetime.to_numpy())
        assert np.allclose(d.atr.to_numpy(),v4.atr.to_numpy(),rtol=1e-12,atol=1e-12,equal_nan=True), f'{sym} V4 ATR mismatch'
        for k in ('SHALLOW_PULLBACK','OBV_PRESSURE'):
            assert_all(f'{sym} {k} frozen vs independently calculated',calc[k],d[k])
            d[k]=calc[k]
        assert_all(f'{sym} INSIDE_DAY_RELEASE frozen V4 vs independently calculated',calc['INSIDE_DAY_RELEASE'],v4.INSIDE_DAY_RELEASE.astype(np.int8))
        d['INSIDE_DAY_RELEASE']=calc['INSIDE_DAY_RELEASE']
        ds[sym]=d
        for _,k in ACCOUNTS:
            summary.append(dict(symbol=sym,strategy=k,bars=len(d),signal_count=int(np.count_nonzero(calc[k])),signal_parity='PASS',v4_source_sha256=sha(BASE/'marketdata_m15'/f'{sym}_M15.csv')))
    return ds,pd.DataFrame(summary)


def run_one(ds,account_num,account,mode):
    # Single-account chronological state machine; completely independent from
    # original numba replay. Tie-breaking is deterministic CNY > GLD > IMOEX > USD.
    stacks=[]
    for symbol_index,sym in enumerate(SYMS):
        d=ds[sym]
        stacks.append(pd.DataFrame(dict(
            ts=d.Datetime.to_numpy(dtype='datetime64[ns]'),
            day=d.day.to_numpy(dtype='datetime64[ns]'),
            session=pd.factorize(d.day)[0],
            sym=np.full(len(d),symbol_index,dtype=np.int8),
            o=d.Open.to_numpy(dtype=np.float64), h=d.High.to_numpy(dtype=np.float64),
            l=d.Low.to_numpy(dtype=np.float64), a=d.atr.to_numpy(dtype=np.float64),
            sig=d[mode].to_numpy(dtype=np.int8))))
    z=pd.concat(stacks,ignore_index=True).sort_values(['ts','sym'],kind='stable').reset_index(drop=True)
    ts=z.ts.to_numpy('datetime64[ns]').astype('int64')
    days=z.day.to_numpy('datetime64[ns]').astype('int64')
    si=z.sym.to_numpy('int8');se=z.session.to_numpy('int64')
    o=z.o.to_numpy(float);h=z.h.to_numpy(float);l=z.l.to_numpy(float);a=z.a.to_numpy(float);sig=z.sig.to_numpy('int8')
    stop_ns=900000000000
    state=[None]*4; pending=[-1]*4; used=[-1]*4; rows=[]
    current_day=-1; entries_today=0; exits=defaultdict(int); checks=defaultdict(int)
    def close(st,i,x,reason):
        direction=st['side']; sym=st['sym'];tick=TICKS[sym]
        gross=direction*(x-st['entry'])/st['risk']
        net=gross-2*tick/st['risk']
        rows.append([account,account_num,sym,direction,str(pd.Timestamp(ts[st['sg']])+pd.Timedelta(minutes=15)),str(pd.Timestamp(ts[st['en']])),str(pd.Timestamp(ts[i])),st['entry'],x,st['stop'],st['risk'],gross,net,reason,str(pd.Timestamp(days[st['en']]).date()),int(se[i]-st['se']+1)])
        exits[reason]+=1
    for i in range(len(z)):
        s=int(si[i]);sym=SYMS[s];tick=TICKS[sym]
        if days[i]!=current_day:
            current_day=days[i];entries_today=0
        st=state[s]
        if st is not None:
            direction=st['side'];x=None;reason=None
            if se[i]-st['se']>=2:x=o[i];reason=3
            elif (direction==1 and o[i]<=st['stop']+tick*1e-7) or (direction==-1 and o[i]>=st['stop']-tick*1e-7):x=o[i];reason=2
            elif (direction==1 and l[i]<=st['stop']+tick*1e-7) or (direction==-1 and h[i]>=st['stop']-tick*1e-7):x=st['stop'];reason=1
            if reason is not None:
                close(st,i,x,reason);state[s]=None
        at=pending[s]
        if at>=0:
            if ts[i]==ts[at]+stop_ns and state[s] is None and used[s]!=se[i] and entries_today<2:
                direction=int(sig[at]);entry=float(o[i]);target=entry-direction*2*a[at]
                # Frozen tick-grid formula with guard against float boundary drift.
                raw_grid=target/tick
                sp=(math.floor(raw_grid+1e-9) if direction==1 else math.ceil(raw_grid-1e-9))*tick
                risk=abs(entry-sp)
                if risk>0 and math.isfinite(risk):
                    st=dict(sym=sym,side=direction,entry=entry,stop=sp,risk=risk,sg=at,en=i,se=int(se[i]))
                    assert ts[i]==ts[at]+stop_ns
                    assert risk+1e-9>=2*a[at]
                    assert abs(sp/tick-round(sp/tick))<1e-6
                    assert (entry>sp if direction==1 else entry<sp)
                    state[s]=st;used[s]=int(se[i]);entries_today+=1
                    checks['entries']+=1
                    assert entries_today<=2
                    if (direction==1 and l[i]<=sp+tick*1e-7) or (direction==-1 and h[i]>=sp-tick*1e-7):
                        close(st,i,sp,4);state[s]=None
            pending[s]=-1
        if sig[i]!=0 and state[s] is None and used[s]!=se[i] and math.isfinite(a[i]) and a[i]>0:
            pending[s]=i
    terminals=[dict(symbol=x['sym'],side=x['side'],entry_dt=str(pd.Timestamp(ts[x['en']])),initial_stop=x['stop'],entry_price=x['entry'],risk_price_units=x['risk']) for x in state if x is not None]
    return pd.DataFrame(rows,columns=COLS),dict(unclosed=len(terminals),terminal_positions=terminals,exits=dict(exits),checks=dict(checks))


def compare_to_reference(actual,reference):
    a=actual.rename(columns={'entry_dt':'entry_dt','exit_dt':'exit_dt'}).copy()
    x=reference.copy()
    fields=['account','account_num','symbol','side','entry_dt','exit_dt']
    a=a.sort_values(fields).reset_index(drop=True);x=x.sort_values(fields).reset_index(drop=True)
    if len(a)!=len(x):raise AssertionError(f'trade count {len(a)} != {len(x)}')
    for col in fields:
        if not a[col].equals(x[col]):
            ix=(a[col]!=x[col]).to_numpy().nonzero()[0]
            raise AssertionError(f'{col} mismatch at {ix[:10]}')
    delta=(a.net_R-x.net_R).abs()
    if (delta>1e-10).any():raise AssertionError(f'net_R mismatch at {list(np.flatnonzero(delta>1e-10)[:10])}')
    a['reference_net_R']=x.net_R
    a['reference_pnl_rub_hypothetical']=x.pnl_rub
    a['abs_error_net_R']=delta
    a['PARITY']='PASS'
    # Verify reference's 'rub' is merely flat 7500R, NOT real PnL.
    assert np.allclose(a.reference_pnl_rub_hypothetical,7500*a.net_R,rtol=1e-10,atol=1e-6)
    return a


def compare_to_original(actual):
    original=pd.read_csv(BASE/'trades.csv')
    for name,mode in ACCOUNTS[:2]:
        a=actual[actual.account==name].sort_values(['symbol','entry_dt','exit_dt']).reset_index(drop=True)
        b=original[original.model==mode].sort_values(['symbol','entry_time','exit_time']).reset_index(drop=True)
        assert len(a)==len(b)
        for x,y in [('symbol','symbol'),('side','side'),('signal_dt','signal_time'),('entry_dt','entry_time'),('exit_dt','exit_time'),('entry','entry'),('exit','exit'),('stop','stop'),('risk','risk'),('exit_reason','exit_reason')]:
            if a[x].dtype==object:
                assert a[x].equals(b[y]), f'{name}: source trade {x}'
            else:
                assert np.allclose(a[x],b[y],rtol=0,atol=1e-9),f'{name}: source trade {x}'
        assert np.allclose(a.net_R,b.net_R,rtol=0,atol=1e-10)


def write_freeze():
    required=[*sorted(BASE.glob('marketdata_m15/*.csv')),
              *sorted(BASE.glob('inside_day_signals/*.csv.gz')),
              BASE/'base.py',BASE/'run.py',BASE/'legacy_v4/study_v4.py',
              BASE/'legacy_v4/dependencies/study.py',BASE/'legacy_v4/dependencies/portfolio_cap.py',
              BASE/'PROTOCOL_RU.md',BASE/'legacy_v4/PROTOCOL.md',
              SOURCE/'research_reference/three_accounts_frozen_trades.csv',
              SOURCE/'docs/ROADMAP_RU.md',HERE/'replay_independent.py']
    lines=[]
    for p in required:
        rel=('V20_Autonomous/'+p.relative_to(SOURCE).as_posix() if p.is_relative_to(SOURCE) else 'V20-02_AUDIT/'+p.relative_to(HERE).as_posix())
        lines.append(sha(p)+'  '+rel+'\n')
    (OUT/'freeze.sha256').write_text(''.join(lines),encoding='utf-8')
    return len(required)


def main():
    ds,sigs=load_signals()
    alltr=[]; meta={}
    for account_num,(account,mode) in enumerate(ACCOUNTS,1):
        tr,info=run_one(ds,account_num,account,mode);alltr.append(tr);meta[mode]=info
        print(mode,len(tr),'remaining',info['unclosed'],'PF',(tr.net_R[tr.net_R>0].sum()/-tr.net_R[tr.net_R<0].sum()),flush=True)
    computed=pd.concat(alltr,ignore_index=True)
    ref=pd.read_csv(SOURCE/'research_reference/three_accounts_frozen_trades.csv')
    parity=compare_to_reference(computed,ref)
    compare_to_original(computed)
    expected={'SHALLOW_PULLBACK':797,'OBV_PRESSURE':612,'INSIDE_DAY_RELEASE':180}
    assert {mode:len(parity.loc[parity.account==account]) for account,mode in ACCOUNTS}==expected
    summaries=[]
    for account,mode in ACCOUNTS:
        q=parity[parity.account==account];r=q.net_R
        pf=r[r>0].sum()/(-r[r<0].sum())
        summaries.append(dict(account=account,model=mode,trades=len(q),PF=pf,net_R=r.sum(),max_abs_diff_R=q.abs_error_net_R.max(),bar_signal_parity='PASS',price_stop_cost_parity='PASS',reference_trade_parity='PASS',remaining_open=meta[mode]['unclosed']))
    overall=parity.net_R
    summaries.append(dict(account='ALL THREE INDEPENDENT',model='ALL',trades=len(parity),PF=overall[overall>0].sum()/-overall[overall<0].sum(),net_R=overall.sum(),max_abs_diff_R=parity.abs_error_net_R.max(),bar_signal_parity='PASS',price_stop_cost_parity='PASS',reference_trade_parity='PASS',remaining_open=sum(z['unclosed'] for z in meta.values())))
    parity.to_csv(OUT/'PARITY_REPORT.csv',index=False)
    pd.DataFrame(summaries).to_csv(OUT/'PARITY_SUMMARY.csv',index=False)
    sigs.to_csv(OUT/'SIGNAL_AUDIT.csv',index=False)
    nfreeze=write_freeze()
    report={'stage':'V20-02','status':'PASS','archive_file_sha256':(sha(Path('/mnt/data/V20_Autonomous_12_etapov_FULL.zip')) if Path('/mnt/data/V20_Autonomous_12_etapov_FULL.zip').exists() else (OUT/'INPUT_ARCHIVE.sha256').read_text().split()[0]),'source':'fully offline; no broker, no new repo, no server mutation','real_broker_orders':0,'main_observed_sha':'c3695b1304aef1acdd889264b3451184f7332bf7','independent_replay':'pure Python multi-account finite state replay (not frozen numba replay)','signal_validation':'Independent formulas match V20 Shallow/OBV and archived V4 Inside at every source M15 bar','parity_trades':len(parity),'unexpected_differences':0,'frozen_input_files':nfreeze,'meta':meta,'summary':summaries}
    (OUT/'ACCEPTANCE_V20_02.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(pd.DataFrame(summaries).to_string(index=False))
    print('FULL V20-02 PASS; report files', len(parity),'rows',flush=True)

if __name__=='__main__':main()
