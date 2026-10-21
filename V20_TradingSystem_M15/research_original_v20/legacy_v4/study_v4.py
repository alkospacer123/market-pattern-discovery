"""Eight rule-fixed independent causal M15 trend structures; protocol file frozen before run."""
import sys,json,hashlib
from pathlib import Path
import numpy as np,pandas as pd
sys.path.insert(0,'/mnt/data/newtrend_v4/dependencies')
from study import prep,TICKS,ROOT,calc_pf
from portfolio_cap import portfolio
OUT=Path('/mnt/data/newtrend_v4'); OUT.mkdir(exist_ok=True)
SYMS=['CNYRUBF','GLDRUBF','IMOEXF','USDRUBF']
MODES=['PREVDAY_BREAK','INSIDE_DAY_RELEASE','GAP_FOLLOW_30','FX_PAIR_CONTINUATION','BREADTH_RECLAIM','RELATIVE_LEADER','H1_RETEST','DAY_COMPRESSION_EXPANSION']


def add_indicators(d,sym):
    d=d.copy();c=d.Close;hi=d.High;lo=d.Low;d['symname']=sym
    openmins=d.Datetime.dt.hour*60+d.Datetime.dt.minute
    allowed=(openmins>=600)&(openmins<1020)
    b=(d.ema50>d.ema200)&(d.ema50>d.ema50.shift(4))
    s=(d.ema50<d.ema200)&(d.ema50<d.ema50.shift(4))
    close0=c.shift(1)
    # Previous *finished* regular M15 daytime session, with >=12 distinct source bars.
    work=d[(openmins>=600)&(openmins<1080)].copy()
    agg=work.groupby('day',sort=True).agg(n=('Close','size'),start=('Open','first'),end=('Close','last'),high=('High','max'),low=('Low','min'),first_dt=('Datetime','first'),last_dt=('Datetime','last'))
    agg['valid']=(agg.n>=12)&(agg.first_dt.dt.hour*60+agg.first_dt.dt.minute<=615)&(agg.last_dt.dt.hour*60+agg.last_dt.dt.minute>=1035)
    for v in ['start','end','high','low','valid']:
        d['p_'+v]=d.day.map(agg[v].shift(1));d['pp_'+v]=d.day.map(agg[v].shift(2))
    valid=d.p_valid.fillna(False).astype(bool)
    vl=allowed&valid&(d.p_end>d.p_start)&b&(c>d.p_high)&(close0<=d.p_high)
    vs=allowed&valid&(d.p_end<d.p_start)&s&(c<d.p_low)&(close0>=d.p_low)
    d[MODES[0]]=np.select([vl,vs],[1,-1],0).astype(np.int8)
    valid2=valid&d.pp_valid.fillna(False).astype(bool)
    inside=valid2&(d.p_high<d.pp_high)&(d.p_low>d.pp_low)
    il=allowed&inside&b&(c>d.p_high)&(close0<=d.p_high)
    ist=allowed&inside&s&(c<d.p_low)&(close0>=d.p_low)
    d[MODES[1]]=np.select([il,ist],[1,-1],0).astype(np.int8)
    # 10:00 observation already exists; 10:15 candle closes at 10:30.
    o10=d.loc[openmins==600,['day','Datetime','Open']].set_index('day')
    d['opening_open']=d.day.map(o10.Open)
    same10=(d.Datetime-pd.Timedelta(minutes=15)).isin(o10.Datetime)
    oldatr=d.atr.shift(2) # value just before 10:00 M15 candle at 10:15 signal
    go=allowed&(openmins==615)&same10&valid&oldatr.gt(0)
    gl=go&b&(d.opening_open>=d.p_end+.35*oldatr)&(c>d.opening_open)&(c>d.Open)
    gs=go&s&(d.opening_open<=d.p_end-.35*oldatr)&(c<d.opening_open)&(c<d.Open)
    d[MODES[2]]=np.select([gl,gs],[1,-1],0).astype(np.int8)
    # signals for relative strength, market breadth and FX are derived later by same completed timestamp.
    d['momentum16']=((c-c.shift(16))/d.atr.replace(0,np.nan)).replace([np.inf,-np.inf],np.nan)
    d['direction16']=np.where(d.momentum16>0,1,np.where(d.momentum16<0,-1,0))
    d['bull']=b;d['bear']=s
    # Prev completed H1 true bar, built only out of 4 correctly adjacent M15 rows.
    h1key=d.Datetime.dt.floor('h')
    h1=d.groupby(h1key,sort=True).agg(first=('Datetime','min'),last=('Datetime','max'),n=('Datetime','size'),h=('High','max'),l=('Low','min'))
    h1=h1[(h1.n==4)&(h1['first']==h1.index)&(h1['last']==h1.index+pd.Timedelta(minutes=45))].copy()
    h1['pub']=h1.index+pd.Timedelta(hours=1)
    h1['prevh']=h1.h.shift(1);h1['prevl']=h1.l.shift(1)
    h1['bullh']=(h1.h>h1.prevh)&(h1.l>h1.prevl)
    h1['bearh']=(h1.h<h1.prevh)&(h1.l<h1.prevl)
    ready=pd.merge_asof(pd.DataFrame({'obs':d.Datetime+pd.Timedelta(minutes=15)}),h1[['pub','prevh','prevl','bullh','bearh']].sort_values('pub'),left_on='obs',right_on='pub',direction='backward')
    hl=allowed&b&ready.bullh.fillna(False).to_numpy()&(lo<=ready.prevh.to_numpy())&(c>ready.prevh.to_numpy())&(c>d.Open)
    hs=allowed&s&ready.bearh.fillna(False).to_numpy()&(hi>=ready.prevl.to_numpy())&(c<ready.prevl.to_numpy())&(c<d.Open)
    d[MODES[6]]=np.select([hl,hs],[1,-1],0).astype(np.int8)
    # Prior session compression vs session before last; cross previous midpoint in direction of p close.
    comp=valid2 & ((d.p_high-d.p_low) < .8*(d.pp_high-d.pp_low))
    mid=(d.p_high+d.p_low)/2
    dl=allowed&comp&b&(d.p_end>mid)&(c>mid)&(close0<=mid)
    ds=allowed&comp&s&(d.p_end<mid)&(c<mid)&(close0>=mid)
    d[MODES[7]]=np.select([dl,ds],[1,-1],0).astype(np.int8)
    # independent executable follow-through levels: 8 previously completed M15 highs/lows
    d['high8']=hi.shift(1).rolling(8,min_periods=8).max()
    d['low8']=lo.shift(1).rolling(8,min_periods=8).min()
    d['cross8_up']=allowed&b&(c>d.high8)&(close0<=d.high8)
    d['cross8_dn']=allowed&s&(c<d.low8)&(close0>=d.low8)
    d['reclaim_up']=allowed&b&(c>d.ema20)&(close0<=d.ema20.shift(1))
    d['reclaim_dn']=allowed&s&(c<d.ema20)&(close0>=d.ema20.shift(1))
    return d


def add_crosssection(D):
    # Only current timestamp's COMPLETED M15 rows are joined, NEVER ffill or look-ahead.
    frames=[]
    for sym,d in D.items():
        p=d[['Datetime','momentum16','direction16','bull','bear','ema50','ema200']].copy();p['symname']=sym;frames.append(p)
    z=pd.concat(frames,ignore_index=True)
    elig=z.momentum16.notna()
    zz=z.copy();zz.loc[~elig,'direction16']=0
    zz['eligible']=elig.astype(int)
    zgrp=zz.groupby('Datetime',sort=False)
    breadth=zgrp.agg(n=('eligible','sum'),sumdir=('direction16','sum'))
    # 3 of 4 observed and same direction; in 2023 some instruments unavailable -> require n>=3 (no fake third vote).
    z['breadth_up']=z.Datetime.map(((breadth.n>=3)&(breadth.sumdir>=3)))
    z['breadth_dn']=z.Datetime.map(((breadth.n>=3)&(breadth.sumdir<=-3)))
    # Rank target by absolute signed normalized returns among >=2 observed contemporaneous members.
    z['nobs']=z.Datetime.map(breadth.n)
    z['top']=z.momentum16.eq(zgrp.momentum16.transform('max'))&z.momentum16.gt(0)
    z['bottom']=z.momentum16.eq(zgrp.momentum16.transform('min'))&z.momentum16.lt(0)
    pfx=z[z.symname.isin(['CNYRUBF','USDRUBF'])].pivot(index='Datetime',columns='symname',values=['direction16','bull','bear'])
    # join exactly same end timestamp, not previous-day score.
    if all((k,v) in pfx.columns for k in ('direction16','bull','bear') for v in ('USDRUBF','CNYRUBF')):
        up=(pfx[('bull','USDRUBF')].fillna(False)&pfx[('bull','CNYRUBF')].fillna(False)&pfx[('direction16','USDRUBF')].eq(1)&pfx[('direction16','CNYRUBF')].eq(1))
        dn=(pfx[('bear','USDRUBF')].fillna(False)&pfx[('bear','CNYRUBF')].fillna(False)&pfx[('direction16','USDRUBF')].eq(-1)&pfx[('direction16','CNYRUBF')].eq(-1))
    else: raise AssertionError('pair missing')
    z['fx_up']=z.Datetime.map(up).fillna(False);z['fx_dn']=z.Datetime.map(dn).fillna(False)
    for sym,d in D.items():
        c=z.loc[z.symname==sym].set_index('Datetime').reindex(d.Datetime)
        assert len(c)==len(d) and not c.index.has_duplicates
        fxok=(sym in ('CNYRUBF','USDRUBF'))
        fl=d.cross8_up & c.fx_up.to_numpy(dtype=bool) if fxok else np.zeros(len(d),dtype=bool)
        fs=d.cross8_dn & c.fx_dn.to_numpy(dtype=bool) if fxok else np.zeros(len(d),dtype=bool)
        d[MODES[3]]=np.select([fl,fs],[1,-1],0).astype(np.int8)
        bl=d.reclaim_up & c.breadth_up.to_numpy(dtype=bool)
        bs=d.reclaim_dn & c.breadth_dn.to_numpy(dtype=bool)
        d[MODES[4]]=np.select([bl,bs],[1,-1],0).astype(np.int8)
        rl=d.reclaim_up & c['top'].to_numpy(dtype=bool)&(c.nobs.to_numpy()>=2)
        rs=d.reclaim_dn & c.bottom.to_numpy(dtype=bool)&(c.nobs.to_numpy()>=2)
        d[MODES[5]]=np.select([rl,rs],[1,-1],0).astype(np.int8)
    return D


def run_model(D,mode,cap=2):
    parts=[]
    for si,sym in enumerate(SYMS):
        d=D[sym][['Datetime','day','Open','High','Low','Close','atr',mode]].copy();d['sym']=si;d['tick']=TICKS[sym];d['day_sess']=pd.factorize(d.day)[0];parts.append(d)
    z=pd.concat(parts,ignore_index=True).sort_values(['Datetime','sym'],kind='mergesort').reset_index(drop=True)
    z['day_num']=pd.factorize(z.day)[0]
    ts=z.Datetime.to_numpy(dtype='datetime64[ns]').astype(np.int64)
    ev,opns=portfolio(ts,z.sym.to_numpy(np.int64),z.day_num.to_numpy(np.int64),z.day_sess.to_numpy(np.int64),*[z[f].to_numpy(np.float64) for f in ['Open','High','Low','Close','atr']],z[mode].to_numpy(np.int64),z.tick.to_numpy(np.float64),cap)
    rows=[]
    for sig,en,ex,s,side,entry,exitpx,stop,risk,gross,net,reason in ev:
        rows.append(dict(model=mode,symbol=SYMS[s],side=int(side),signal_dt=str(pd.Timestamp(ts[sig])+pd.Timedelta(minutes=15)),entry_dt=str(pd.Timestamp(ts[en])),exit_dt=str(pd.Timestamp(ts[ex])),entry_session=str(pd.Timestamp(z.day.iloc[en]).date()),entry=float(entry),exit=float(exitpx),stop=float(stop),risk=float(risk),gross_R=float(gross),net_C1_R=float(net),reason=int(reason),exit_year=pd.Timestamp(ts[ex]).year,exit_month=pd.Timestamp(ts[ex]).strftime('%Y-%m'),held_hours=float((ts[ex]-ts[en])/3.6e12),session_span=int(z.day_sess.iloc[ex]-z.day_sess.iloc[en]+1)))
    return pd.DataFrame(rows),opns


def summarize(trades,universe):
    rows=[]; bysym=[]; month=[];days=[]
    for mode in MODES:
        t=trades[trades.model==mode];t=t.copy()
        t['entry_year']=pd.to_datetime(t.entry_dt).dt.year
        for period,years in [('DEV',[2023,2024]),('LATE',[2025,2026]),('ALL',[2023,2024,2025,2026]),('2023',[2023]),('2024',[2024]),('2025',[2025]),('2026',[2026])]:
            q=t[t.exit_year.isin(years)].copy();a=q.net_C1_R
            tradingdates=[x for x in universe if int(x[:4]) in years]
            ec=t[t.entry_year.isin(years)].groupby('entry_session').size().reindex(tradingdates,fill_value=0)
            ms=sorted({x[:7] for x in tradingdates});m=q.groupby('exit_month').net_C1_R.sum().reindex(ms,fill_value=0)
            x=a.to_numpy();cum=np.cumsum(x);dd=(np.maximum.accumulate(np.r_[0,cum])[1:]-cum).max() if len(x) else np.nan
            pos=a[a>0].sum();neg=-a[a<0].sum()
            rows.append(dict(model=mode,period=period,closed=len(q),pf=float(pos/neg) if neg else float('nan'),sum_R=float(a.sum()),gross_R=float(q.gross_R.sum()),win_pct=float((a>0).mean()*100),negative_months=int((m<0).sum()),worst_month_R=float(m.min()),max_closed_R_DD=float(dd),avg_entries_per_day=float(ec.mean()),pct_days_1or2=float(ec.between(1,2).mean()*100),pct_days_zero=float(ec.eq(0).mean()*100),pct_days_gt2=float(ec.gt(2).mean()*100),median_holding_hours=float(q.held_hours.median()),pct_positions_next_session=float(q.session_span.ge(2).mean()*100),big_winners_ge2R=int((a>=2).sum())))
            for sym,sub in q.groupby('symbol'):
                pa=sub.net_C1_R;bysym.append(dict(model=mode,period=period,symbol=sym,closed=len(sub),pf=calc_pf(pa),sum_R=pa.sum()))
            if period in ('DEV','LATE'):
                for day,n in ec.items():days.append(dict(model=mode,period=period,day=day,n_entries=int(n)))
            if period in ('DEV','LATE'):
                for mm,v in m.items():month.append(dict(model=mode,period=period,month=mm,R=v))
    return pd.DataFrame(rows),pd.DataFrame(bysym),pd.DataFrame(days),pd.DataFrame(month)


def main():
    assert hashlib.sha256((OUT/'PROTOCOL.md').read_bytes()).hexdigest()=='c5c5cfa025cfc10b691fb163459645cac9b0764a47ea842d9caf89e86d7e660b'
    D={};hashes={};universe=set()
    for sym in SYMS:
        print('PREP',sym,flush=True)
        hashes[sym]=hashlib.sha256((ROOT/f'{sym}_M15.csv').read_bytes()).hexdigest()
        d=add_indicators(prep(sym),sym);D[sym]=d
        universe.update(d.loc[(d.mins>=600)&(d.mins<1020),'day'].dt.strftime('%Y-%m-%d'))
    add_crosssection(D)
    print('FEATURES DONE',flush=True)
    fd=OUT/'signals';fd.mkdir(exist_ok=True)
    for sym,d in D.items():d[['Datetime','day','atr']+MODES].to_csv(fd/f'{sym}.csv.gz',index=False,compression='gzip')
    allt=[];opens={};
    for mode in MODES:
        t,opns=run_model(D,mode,2);opens[mode]=opns;allt.append(t)
        print('RUN',mode,len(t),'OPEN',opns,flush=True)
    trades=pd.concat(allt,ignore_index=True).sort_values(['model','entry_dt','symbol'])
    trades.to_csv(OUT/'trades.csv',index=False)
    ss,bb,dd,mm=summarize(trades,sorted(universe))
    for name,df in [('summary',ss),('by_symbol',bb),('daily_frequency',dd),('monthly',mm)]:df.to_csv(OUT/(name+'.csv'),index=False)
    (OUT/'source_hashes.json').write_text(json.dumps(hashes,indent=2));(OUT/'terminal_open.json').write_text(json.dumps(opens,indent=2))
    print(ss[ss.period.isin(['DEV','LATE'])].to_string(index=False),flush=True)

if __name__=='__main__':main()
