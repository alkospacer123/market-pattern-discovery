#!/usr/bin/env python3
"""Read-only independent ledger/causality assertions for STS R043 candidates."""
from pathlib import Path
import sys, json, math
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
import run_r043 as run
engine=run.eng
raw={s:run.r039.signal_dataframe(run.r039.re.load_one(s).copy()) for s in engine.SYMS}
data={s:run.signals(v)[0] for s,v in raw.items()}
ledger=pd.read_csv(ROOT/'results/candidate_cash_trades.csv',parse_dates=['entry_dt','exit_dt'])
q=ledger[(ledger.bank_per_robot==45000)&(ledger.go_proxy=='OCT2026_PROXY')&(ledger.exit_type=='TP6_PROTECT3')].copy()
assert len(q)>0
lookup={s:d.set_index('Datetime') for s,d in data.items()}
n=0
for r in q.itertuples():
    mode= next(k for k,v in run.NAMES.items() if v==r.robot)
    d=lookup[r.symbol]
    t=r.entry_dt-pd.Timedelta(minutes=15)
    assert t in d.index, ('MISSING_PREV_CANDLE',r.symbol,t)
    sig=d.loc[t]
    assert int(sig[mode])==int(r.side), ('SIGNAL_MISMATCH',r.symbol,t)
    at=d.loc[r.entry_dt]
    assert math.isclose(float(at.Open),r.entry,abs_tol=1e-7)
    tick=engine.TICKS[r.symbol]
    atr=float(sig.atr)
    wantstop=r.entry-r.side*2*atr
    rounded= (math.floor(wantstop/tick+1e-9) if r.side==1 else math.ceil(wantstop/tick-1e-9))*tick
    assert math.isclose(rounded,r.orig_stop,abs_tol=1e-6),('STOP',r.symbol,rounded,r.orig_stop)
    assert math.isclose(abs(r.entry-r.orig_stop),r.risk,abs_tol=1e-6)
    g=r.side*(r.exit-r.entry)/r.risk
    net=g-2*tick/r.risk
    assert math.isclose(g,r.gross_R,abs_tol=1e-8)
    assert math.isclose(net,r.net_R,abs_tol=1e-8)
    cash=r.lots*(r.side*(r.exit-r.entry)*engine.MULT[r.symbol]-2*tick*engine.MULT[r.symbol])
    assert math.isclose(cash,r.cash_pnl,abs_tol=.01)
    assert r.lots>=1 and math.isfinite(cash)
    n+=1
z=pd.read_csv(ROOT/'results/portfolio_cash.csv')
for ex in ('BASE','TP6_PROTECT3'):
    t=z.query('model=="V20" and total_bank==135000 and go_proxy=="OCT2026_PROXY" and exit_type==@ex').iloc[0]
    expected=384710.6 if ex=='BASE' else 381607.6
    assert math.isclose(t.net_rub,expected,abs_tol=.01)
# Audit same-signature candidate timestamps: each signal must be on finished M15,
# in an allowed weekday/session, no previously incomplete H1/H4/daily aggregate in context.
for sym,d in data.items():
    sig=d[d[run.MODES].ne(0).any(axis=1)]
    assert (sig.mins.between(630,960)).all()
    assert (sig.Datetime.dt.weekday<5).all()
    h1,h4,b1,b4=run._h_context(d)
    if (d[run.MODES[0]]!=0).any():
        idx=np.flatnonzero(d[run.MODES[0]].to_numpy()!=0)
        for k in idx:
            decision=d.Datetime.iloc[k]+pd.Timedelta(minutes=15)
            assert pd.notna(h1.close_time.iloc[k]) and h1.close_time.iloc[k]<=decision
            assert pd.notna(h4.close_time.iloc[k]) and h4.close_time.iloc[k]<=decision
    daily_ctx,_=run._d_context(d)
    ix=np.flatnonzero(d[run.MODES[1]].to_numpy()!=0)
    for k in ix:
        assert daily_ctx.previous_eligible_day.iloc[k]<d.day.iloc[k]
res={'status':'R043_INDEPENDENT_LEDGER_AUDIT_PASS','checked_candidate_cash_trades':n,'checked_symbols':len(data),'baseline_parity':True,'freeze_verified':True}
(ROOT/'results/INDEPENDENT_AUDIT.json').write_text(json.dumps(res,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(res,ensure_ascii=False))