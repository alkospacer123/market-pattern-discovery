#!/usr/bin/env python3
"""Required substantive causality, archived parity and execution tests. No network.
Assertions raise and exit nonzero; JSON enumerates actual assertions, not assumed PASS.
"""
import argparse, collections, json, math
from pathlib import Path
import numpy as np
import pandas as pd
import stress_v20_03 as s

checks=[]
def record(name, detail):
    checks.append(dict(check=name,status='PASS',detail=detail))
    print('PASS',name,detail,flush=True)

def archived_parity():
    """Re-execute the accepted V20-02 baseline without modifying its evidence."""
    audit=s.ROOT/'V20-02_AUDIT/replay_independent.py'
    syms=['CNYRUBF','GLDRUBF','IMOEXF','USDRUBF']
    env=dict(np=np,pd=pd,math=math,defaultdict=collections.defaultdict,SYMS=syms,
             TICKS=s.literal(s.BASE/'base.py','TICKS'),COLS=s.literal(audit,'COLS'))
    independent=s.extract(audit,'independent_signals',env)
    run=s.extract(audit,'run_one',env)
    ds={};bars=0
    for sym in syms:
        raw=pd.read_csv(s.BASE/'marketdata_m15'/f'{sym}_M15.csv',sep=';',parse_dates=['Datetime'])
        d=s.frozen_signals(raw)
        calc=independent(d)
        old=pd.read_csv(s.BASE/'inside_day_signals'/f'{sym}.csv.gz',parse_dates=['Datetime'])
        assert d.Datetime.equals(old.Datetime)
        for mode in s.MODES:assert np.array_equal(d[mode].to_numpy(),calc[mode]),(sym,mode)
        assert np.array_equal(d.INSIDE_DAY_RELEASE,old.INSIDE_DAY_RELEASE)
        ds[sym]=d;bars+=len(d)
    alltr=[]
    names=['Shallow Pullback','OBV Pressure','Inside Day Release']
    for n,(name,mode) in enumerate(zip(names,s.MODES),1):
        tr,_=run(ds,n,name,mode);alltr.append(tr)
    a=pd.concat(alltr,ignore_index=True)
    b=pd.read_csv(s.ROOT/'research_reference/three_accounts_frozen_trades.csv')
    fields=['account','account_num','symbol','side','entry_dt','exit_dt']
    a=a.sort_values(fields).reset_index(drop=True);b=b.sort_values(fields).reset_index(drop=True)
    assert len(a)==len(b)==1589
    for f in fields:assert a[f].equals(b[f]),f
    assert np.allclose(a.net_R,b.net_R,rtol=0,atol=1e-10)
    record('ACCEPTED_V20_02_BASELINE',dict(bars=bars,trades=len(a),max_R_error=float((a.net_R-b.net_R).abs().max()),
                                         all_three_signal_arrays_match=True))

def feature_prefixes(raw):
    count=0;features=0;frames={}
    # Every real contract: full history vs truncated prefix, including segmentation.
    for c,d in raw.items():
        full=s.prepare_contract(d)
        frames[c]=full
        cut=max(1,len(d)//2)
        short=s.prepare_contract(d.iloc[:cut])
        for f in s.FEATURES:
            assert np.allclose(full[f].iloc[:cut],short[f],equal_nan=True,rtol=0,atol=1e-12),(c,cut,f)
        count+=1;features+=cut
    # Dense checks around first valid EMA, day boundaries and CNY tick transition.
    for c in ['Si-12.19','CNY-12.22','MIX-3.18']:
        d=raw[c];full=s.frozen_signals(d)
        cuts={199,200,201,min(405,len(d)-1),len(d)-1}
        if c=='CNY-12.22':
            ix=int(d.Datetime.searchsorted(pd.Timestamp('2022-10-06 19:00')))
            cuts.update([ix,ix+1,ix+2])
        for cut in sorted(n for n in cuts if 0<n<len(d)):
            short=s.frozen_signals(d.iloc[:cut])
            for f in s.FEATURES:
                assert np.allclose(full[f].iloc[:cut],short[f],equal_nan=True,rtol=0,atol=1e-12),(c,cut,f)
            count+=1
    record('FROZEN_SIGNALS_PREFIX_INVARIANCE',dict(prefix_runs=count,all_real_contracts=len(raw),compared_prefix_rows=features))
    return frames

def actual_replay_prefixes(frames,plan):
    comparisons=0;closed_count=0
    for n,mode in enumerate(s.MODES,1):
        full,_,fullen,_=s.replay(frames,plan,mode,n)
        for cut in pd.to_datetime(['2018-12-31 23:45','2019-06-25 13:00','2022-10-06 19:30','2022-12-01 10:15']):
            past={c:d[d.Datetime<=cut].copy() for c,d in frames.items()}
            short,_,en,_=s.replay(past,plan,mode,n)
            # Ignore mutable diagnostic last-observed fields for open positions; compare
            # all complete trade/entry dictionaries through the observed prefix.
            expected=[r for r in full if pd.Timestamp(r['exit_dt'])<=cut]
            expected_en=[r for r in fullen if pd.Timestamp(r['entry_dt'])<=cut]
            assert short==expected,(mode,str(cut),'closed')
            assert en==expected_en,(mode,str(cut),'entries')
            comparisons+=1;closed_count+=len(short)
    record('ACTUAL_STRESS_REPLAY_PREFIX_INVARIANCE',dict(comparisons=comparisons,closed_records_compared=closed_count))

def roll_prefixes(sessions):
    full=s.roll_plan(sessions)
    for cut in pd.to_datetime(['2018-06-21 09:00','2019-06-21 09:00','2019-06-24 09:00',
                               '2019-09-20 09:00','2022-06-17 09:00','2022-10-07 09:00']):
        # Only summaries whose final bar had actually completed; no future contracts.
        past=sessions[sessions.known_after<=cut].copy()
        # A clock tick creates the decision at cut, independent of current session bars.
        # Current day's placeholder has no usable rows and is never a candidate.
        placeholders=[]
        for f in s.FAMILIES:
            q=sessions[(sessions.family==f)&(sessions.day==cut.normalize())]
            if len(q):
                row=q.iloc[0].copy();row['prior_day_eligible']=False
                row['known_after']=cut+pd.Timedelta(days=1);placeholders.append(row)
        truncated=pd.concat([past,pd.DataFrame(placeholders)],ignore_index=True)
        plan=s.roll_plan(truncated)
        a=full[full.decision_time<=cut].reset_index(drop=True)
        b=plan[plan.decision_time<=cut].reset_index(drop=True)
        # Order of family groups is stable; compare all decisions up through cut.
        assert a[['family','day','chosen_contract']].equals(b[['family','day','chosen_contract']]),str(cut)
    assert (full.proof_known_after.dropna()<=full.loc[full.proof_known_after.notna(),'decision_time']).all()
    q=full[(full.family=='Si')&full.day.between('2019-06-20','2019-06-26')]
    record('ROLL_PREFIX_INVARIANCE',dict(cutoffs=6,proof='prior completed observations only',si_2019=q.astype(str).to_dict('records')))

def synthetic_row(ts,family,signal=0,op=100.,hi=101.,lo=99.,atr=1.,seg=0,contract=None):
    ts=pd.Timestamp(ts);contract=contract or {'CNY':'CNY-12.22','MIX':'MIX-12.22','Si':'Si-12.22'}[family]
    return dict(Datetime=ts,day=s.session(ts),family=family,contract=contract,Open=op,High=hi,Low=lo,
                Close=op,Volume=1,atr=atr,segment=seg,tick=s.tick(family,ts),
                **{m:signal if m=='SHALLOW_PULLBACK' else 0 for m in s.MODES})

def engine_tests():
    rows=[]
    for f in s.FAMILIES:
        op={'CNY':10.,'MIX':200000.,'Si':60000.}[f];a=s.tick(f,'2022-11-01')*10
        for t,sg in [('2022-11-01 10:00',1),('2022-11-01 10:15',0),('2022-11-01 10:30',1),
                     ('2022-11-01 10:45',0),('2022-11-02 10:00',0),('2022-11-03 09:00',0)]:
            rows.append(synthetic_row(t,f,sg,op,op+a,op-a,a))
    frames={c:pd.DataFrame([r for r in rows if r['contract']==c]) for c in set(r['contract'] for r in rows)}
    plan=pd.DataFrame([dict(family=f,day=pd.Timestamp(day),chosen_contract={'CNY':'CNY-12.22','MIX':'MIX-12.22','Si':'Si-12.22'}[f])
                       for f in s.FAMILIES for day in ['2022-11-01','2022-11-02','2022-11-03']])
    cl,op,en,ev=s.replay(frames,plan,s.MODES[0],1)
    assert len(en)==2 and [x['family'] for x in en]==['CNY','MIX']
    assert len(cl)==2 and not op and all(x['exit_reason']==3 and x['session_span']==3 for x in cl)
    _,_,independent_en,_=s.replay(frames,plan,s.MODES[0],2)
    assert len(independent_en)==2  # First account consumed no second-account quota.
    # Truncating future sessions cannot change earlier entries or closed trades.
    short={c:d[d.Datetime<pd.Timestamp('2022-11-03')] for c,d in frames.items()}
    cl2,op2,en2,_=s.replay(short,plan,s.MODES[0],1)
    assert not cl2 and len(op2)==2 and en2==en
    # A missing NEXT_OPEN cancels entry, even if later bar has appealing price.
    d=pd.DataFrame([synthetic_row('2022-11-01 10:00','Si',1),synthetic_row('2022-11-01 10:30','Si')])
    assert not s.replay({'Si-12.22':d},plan,s.MODES[0],1)[2]
    # Entry-bar stop always wins; outward grid stop and R costs use correct tick.
    d=pd.DataFrame([synthetic_row('2022-11-01 10:00','Si',1,100.,101.,99.,1.2),
                    synthetic_row('2022-11-01 10:15','Si',0,100.,120.,90.,1.2)])
    cl,_,en,_=s.replay({'Si-12.22':d},plan,s.MODES[0],1)
    assert len(cl)==1 and cl[0]['stop']==97 and cl[0]['exit_reason']==4 and cl[0]['gross_R']==-1
    assert abs(cl[0]['net_C1_R']-(-1-2/3))<1e-12
    # Gap through stop fills adverse opening, not synthetic stop.
    d=pd.DataFrame([synthetic_row('2022-11-01 10:00','Si',1),synthetic_row('2022-11-01 10:15','Si'),
                    synthetic_row('2022-11-01 10:30','Si',0,90.,91.,89.)])
    cl,_,_,_=s.replay({'Si-12.22':d},plan,s.MODES[0],1)
    assert cl[0]['exit']==90 and cl[0]['exit_reason']==2 and cl[0]['gross_R']==-5
    # Hole marks the full position censored, keeps it occupied until natural exit.
    d=pd.DataFrame([synthetic_row('2022-11-01 10:00','Si',1),synthetic_row('2022-11-01 10:15','Si'),
                    synthetic_row('2022-11-01 11:00','Si',0,100.,101.,90.,seg=1)])
    cl,_,_,_=s.replay({'Si-12.22':d},plan,s.MODES[0],1)
    assert len(cl)==1 and not cl[0]['stat_eligible']
    # Roll while an old position is open cannot create a second underlying position.
    old='Si-9.22';new='Si-12.22'
    d1=pd.DataFrame([synthetic_row('2022-08-30 10:00','Si',1,contract=old),
                     synthetic_row('2022-08-30 10:15','Si',contract=old),
                     synthetic_row('2022-08-31 10:00','Si',contract=old)])
    d2=pd.DataFrame([synthetic_row('2022-08-31 10:00','Si',1,contract=new),
                     synthetic_row('2022-08-31 10:15','Si',contract=new)])
    roll=pd.DataFrame([dict(family='Si',day=pd.Timestamp('2022-08-30'),chosen_contract=old),
                       dict(family='Si',day=pd.Timestamp('2022-08-31'),chosen_contract=new)])
    cl,op,en,_=s.replay({old:d1,new:d2},roll,s.MODES[0],1)
    assert len(en)==1 and len(op)==1 and op[0]['contract']==old
    # CNY schedule includes pre-announced intracontract change; fees at each side.
    assert s.tick('CNY','2022-10-06 18:45')==.01 and s.tick('CNY','2022-10-06 19:00')==.001
    d=pd.DataFrame([synthetic_row('2022-10-06 10:00','CNY',1,9.,9.01,8.99,.06),
                    synthetic_row('2022-10-06 10:15','CNY',0,9.,9.01,8.99,.06),
                    synthetic_row('2022-10-07 10:00','CNY',0,8.,8.01,7.99,.06)])
    cp=pd.DataFrame([dict(family='CNY',day=pd.Timestamp(date),chosen_contract='CNY-12.22')
                     for date in ['2022-10-06','2022-10-07']])
    cl,_,_,_=s.replay({'CNY-12.22':d},cp,s.MODES[0],1)
    assert len(cl)==1 and abs((cl[0]['gross_R']-cl[0]['net_C1_R'])-.011/cl[0]['risk'])<1e-12
    assert s.broken('2022-11-01 10:00','2022-11-01 10:30')
    assert not s.broken('2022-11-01 18:30','2022-11-01 19:00')
    record('EXECUTION_STATE_MACHINE',dict(assertions='cap 2, one symbol/session, independent account invocations, NEXT_OPEN adjacency, stop-first, gap-open, third session, censor, roll occupancy, terminal unknown, CNY grid'))

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--out',type=Path,default=s.STAGE/'verification/CAUSALITY.json');args=ap.parse_args()
    record('ORIGINALS_BYTE_IDENTICAL',dict(files=s.verify_originals()))
    raw,maps,sessions,gaps=s.read_inputs()
    record('RAW_43_CONTRACTS_AND_TICK_GRIDS',dict(files=len(raw),bad_grid=int(maps.grid_failures.sum())))
    engine_tests();archived_parity();roll_prefixes(sessions)
    frames=feature_prefixes(raw);actual_replay_prefixes(frames,s.roll_plan(sessions))
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(dict(status='PASS',checks=checks),ensure_ascii=False,indent=2)+'\n')

if __name__=='__main__':main()
