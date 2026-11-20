#!/usr/bin/env python3
"""Independent arithmetic/structural audit of R047 outputs (no model calls, no LIVE)."""
from pathlib import Path
import json, math, hashlib
import numpy as np
import pandas as pd
R=Path(__file__).resolve().parent;D=R/'results'
CAT=R/'deps'/'R031_trend_event_catalog.csv' if (R/'deps'/'R031_trend_event_catalog.csv').exists() else Path('/mnt/data/trl_shallow_family/research_r039/R031_trend_event_catalog.csv')
SRC=R/'deps'/'r045_trade_ledger_135k.csv' if (R/'deps'/'r045_trade_ledger_135k.csv').exists() else Path('/mnt/data/sts_r045/results/trade_ledger_135k.csv')
X=pd.read_csv(D/'candidate_cash_trades.csv',parse_dates=['entry_dt','exit_dt'])
portfolio=pd.read_csv(D/'portfolio_comparison.csv')
E=pd.read_csv(CAT,parse_dates=['start_dt','end_dt']);M=E[E.Shallow_entry==0]
TICK={'CNYRUBF':.001,'GLDRUBF':.1,'IMOEXF':.5,'USDRUBF':.01};MUL={'CNYRUBF':1000.,'GLDRUBF':1.,'IMOEXF':10.,'USDRUBF':1000.}
CHECK=[]
for r in X.itertuples():
  p=float(r.lots)*(r.side*(r.exit-r.entry)*MUL[r.symbol]-2*TICK[r.symbol]*MUL[r.symbol]);CHECK.append(abs(p-r.net_rub))
  assert r.lots>0 and r.entry_dt<=r.exit_dt and r.entry_dt.weekday()<5,(r.symbol,r.entry_dt)
  assert math.isclose(abs(r.entry-r.orig_stop),r.risk,abs_tol=1e-7)
  assert math.isclose(round(r.orig_stop/TICK[r.symbol]),r.orig_stop/TICK[r.symbol],abs_tol=1e-7)
assert max(CHECK)<1e-6,('PnL_CALC',max(CHECK))
assert set(X.module)=={'EARLY_TREND_RESUME','TIGHT_DRIFT_BREAK'}
for (mod,ex,go),x in X.groupby(['module','exit_style','go_proxy']):
 assert x.unclosed_positions.sum()==0 if 'unclosed_positions' in x.columns else True
 for sym,z in x.groupby('symbol'):
  ses=(z.entry_dt-pd.Timedelta(hours=9)).dt.normalize()
  assert not ses.duplicated().any(),('one_per_session',mod,ex,go,sym)
 for _,z in x.groupby(x.entry_dt.dt.normalize()):
  assert len(z)<=2,('two_day_entry_cap',mod,ex,go)

a=pd.read_csv(D/'standalone_cash.csv'); assert len(a)==8
for row in a.itertuples():
 z=X[(X.module==row.module)&(X.exit_style==row.exit)&(X.go_proxy==row.go_proxy)]
 assert len(z)==row.trades and abs(z.net_rub.sum()-row.net)<1e-6
s=pd.read_csv(SRC,parse_dates=['exit_dt','entry_dt']);c=s[s.scenario=='V20_45_45_45_135000_OCT2026_PROXY_TP6_PROTECT3_x'];assert abs(c.net_rub.sum()-381607.6)<.06
v=portfolio[(portfolio.model=='V20')&(portfolio.go_proxy=='OCT2026_PROXY')&(portfolio.exit=='TP6_PROTECT3')].iloc[0]
assert v.trades==len(c) and abs(v.net-c.net_rub.sum())<.05
# coverage: event labels derived from future and never used in the model; check all R047 counted event matches
cov=pd.read_csv(D/'missed_event_coverage.csv')
for r in cov.itertuples():
 t=X[(X.module==r.module)&(X.exit_style==r.exit)&(X.go_proxy==r.go_proxy)]
 relevant=0
 for z in M.itertuples():
  if ((t.symbol==z.symbol)&(t.side==z.side)&(t.entry_dt>=z.start_dt)&(t.entry_dt<=z.end_dt)).any():relevant+=1
 assert relevant==r.covered_events,(r.module,r.exit,r.go_proxy,relevant,r.covered_events)
print('AUDIT_INDEPENDENT_PASS',json.dumps(dict(trades=len(X),cash_arithmetic_max_error=max(CHECK),portfolio_comparisons=len(portfolio),episode_classifications_checked=len(cov)*len(M),cost_baseline_verified=True),ensure_ascii=False),flush=True)
(D/'INDEPENDENT_AUDIT.json').write_text(json.dumps(dict(status='PASS',trades_checked=len(X),cash_arithmetic_max_error=max(CHECK),portfolio_comparisons=len(portfolio),episode_classifications_checked=len(cov)*len(M),baseline_parity=True),indent=2),encoding='utf-8')
