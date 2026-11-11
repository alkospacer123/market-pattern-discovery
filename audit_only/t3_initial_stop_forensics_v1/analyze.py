"""Calendar, signal comparison and executable-grid diagnostics; never cash proxies."""
import math,statistics
from collections import defaultdict
from decimal import Decimal,ROUND_FLOOR,ROUND_CEILING
import pandas as pd
from common import *
from forensics import identity,stream_key
EPS=1e-8

def sign(v):return 1 if v>EPS else -1 if v< -EPS else 0
def pf(v):
 losses=-math.fsum(x for x in v if x<0);return math.fsum(x for x in v if x>0)/losses if losses else None
def drawdown(values):
 peak=worst=0.
 for v in values:peak=max(peak,v);worst=max(worst,peak-v)
 return worst

def consecutive(months,basis):
 best=run=0;prior=None
 for r in sorted(months,key=lambda x:x['month']):
  month=pd.Period(r['month'],'M')
  run=run+1 if r.get(basis) is not None and sign(r[basis])<0 and (prior is None or month==prior+1) else 1 if r.get(basis) is not None and sign(r[basis])<0 else 0
  best=max(best,run);prior=month
 return best

def calendar(streams,results,out):
 trades=[t for r in results for t in r['trades']];monthly=[];summaries=[];curves_out=[]
 groups=sorted({(s['system'],s['lifecycle'],s['fold_id']) for s in streams})
 for system,life,fold in groups:
  ss=[s for s in streams if (s['system'],s['lifecycle'],s['fold_id'])==(system,life,fold)]
  coverage=defaultdict(set)
  for s in ss:
   for b in s['bars']:coverage[b['at'].strftime('%Y-%m')].add(s['instrument'])
  variants=('CONTROL','STOP_2p0','STOP_1p5') if system=='H1' else ('CONTROL','STOP_1p5')
  for variant in variants:
   rr=[r for r in results if all(r['marks'][0][k]==v for k,v in zip(('system','lifecycle','fold_id','variant'),(system,life,fold,variant)))]
   frames={r['marks'][0]['instrument']:pd.DataFrame(r['marks']).set_index('at') for r in rr}
   clock=sorted({at for f in frames.values() for at in f.index});columns=('gross_realized_R','gross_MTM_R','C1_normalized_MTM_R','gross_unrealized_R','remaining_quantity')
   curve=pd.DataFrame({col:pd.DataFrame({s:f[col].reindex(clock).ffill().fillna(0.) for s,f in frames.items()}).sum(axis=1) for col in columns})
   for at,row in curve.iterrows():curves_out.append(dict(system=system,lifecycle=life,fold_id=fold,variant=variant,at=at,**row.to_dict()))
   tt=[t for t in trades if (t['system'],t['lifecycle'],t['fold_id'],t['variant'])==(system,life,fold,variant)]
   previous=previous_c1=0.;selected=[]
   monthcurves={str(p):f for p,f in curve.groupby(curve.index.strftime('%Y-%m'))}
   for month in map(str,pd.period_range('2023-01','2026-10',freq='M')):
    instruments=sorted(coverage[month]);active=bool(instruments);sub=monthcurves.get(month);closed=[t for t in tt if t['status']=='CLOSED' and t['exit_time'].strftime('%Y-%m')==month]
    gross=math.fsum(t['gross_R'] for t in closed) if active else None;mtm=float(sub.gross_MTM_R.iloc[-1]-previous) if active else None
    row=dict(system=system,lifecycle=life,fold_id=fold,variant=variant,month=month,timezone='Europe/Moscow',coverage='NO_DATA' if not active else 'N4_OBSERVED' if len(instruments)==4 else 'PARTIAL_N4',observed_instruments='|'.join(instruments),
     period_limit='2023_PARTIAL_N4' if active and month.startswith('2023') else '2026_YTD_PARTIAL' if active and month.startswith('2026') else 'OBSERVED' if active else 'NO_DATA',
     CLOSED_R=gross,MTM_R=mtm,CLOSED_sign=sign(gross) if active else None,MTM_sign=sign(mtm) if active else None,
     C1_normalized_CLOSED_R=math.fsum(t['net_R_C1'] for t in closed) if active and system=='H1' else None,C1_normalized_MTM_R=float(sub.C1_normalized_MTM_R.iloc[-1]-previous_c1) if active and system=='H1' else None,
     CLOSED_trades=len(closed) if active else None,MTM_intramonth_DD_R=drawdown([0.]+(sub.gross_MTM_R-previous).tolist()) if active else None,
     open_positions_at_last_bar=int(sub.remaining_quantity.iloc[-1]) if active else None,unrealized_R_at_last_bar=float(sub.gross_unrealized_R.iloc[-1]) if active else None,
     cash_Net='NOT_VALIDATED',cash_return='NOT_VALIDATED')
    if active:previous=float(sub.gross_MTM_R.iloc[-1]);previous_c1=float(sub.C1_normalized_MTM_R.iloc[-1]);selected.append(row)
    monthly.append(row)
   summaries.extend(summary(system,life,fold,variant,tt,selected,curve))
 # Descriptive disjoint total: no curve concatenation or invented continuous capital.
 for variant in ('CONTROL','STOP_2p0','STOP_1p5'):
  tt=[t for t in trades if t['system']=='H1' and t['lifecycle']!='walk_forward' and t['variant']==variant]
  mm=[m for m in monthly if m['system']=='H1' and m['lifecycle']!='walk_forward' and m['variant']==variant and m['coverage']!='NO_DATA']
  assert len({m['month'] for m in mm})==len(mm)
  summaries.extend(summary('H1','DISJOINT_BASELINE_AND_HISTORICAL_OOS','',variant,tt,mm,None))
 flips=[]
 lookup={(r['system'],r['lifecycle'],r['fold_id'],r['variant'],r['month']):r for r in monthly}
 for m in monthly:
  if m['variant']=='CONTROL' or m['coverage']=='NO_DATA':continue
  a=lookup[(m['system'],m['lifecycle'],m['fold_id'],'CONTROL',m['month'])]
  for basis in ('CLOSED_R','MTM_R'):
   x,y=sign(a[basis]),sign(m[basis]);flips.append(dict(system=m['system'],lifecycle=m['lifecycle'],fold_id=m['fold_id'],variant=m['variant'],month=m['month'],basis=basis,CONTROL_R=a[basis],variant_R=m[basis],delta_R=m[basis]-a[basis],transition='NEGATIVE_TO_POSITIVE' if x<0<y else 'POSITIVE_TO_NEGATIVE' if y<0<x else 'OTHER'))
 csvout(out/'STOP_VARIANT_MONTHLY.csv',monthly);csvout(out/'STOP_VARIANT_SUMMARY.csv',summaries);csvout(out/'MONTH_SIGN_TRANSITIONS.csv',flips);csvout(out/'PORTFOLIO_CURVES.csv.gz',curves_out)
 return summaries,monthly,flips

def summary(system,life,fold,variant,trades,months,curve):
 closed=sorted([t for t in trades if t['status']=='CLOSED'],key=lambda t:(t['exit_time'],t['instrument'],t['trade_id']));rs=[t['gross_R'] for t in closed];wins=[x for x in rs if x>0];losses=[x for x in rs if x<0];total=math.fsum(rs)
 # DD of disjoint cold-start lifecycles is intentionally undefined.
 stats=dict(system=system,lifecycle=life,fold_id=fold,variant=variant,CLOSED=len(closed),OPEN=len(trades)-len(closed),gross_PF=pf(rs),gross_R=total,expectancy_R=total/len(rs) if rs else None,
  win_rate=len(wins)/len(rs) if rs else None,average_win_R=statistics.mean(wins) if wins else None,average_loss_R=statistics.mean(losses) if losses else None,
  C1_normalized_R=math.fsum(t['net_R_C1'] for t in closed) if system=='H1' else None,C1_normalized_PF=pf([t['net_R_C1'] for t in closed]) if system=='H1' else None,
  INITIAL_STOP_count=sum(t['exit_reason']=='INITIAL_STOP' for t in closed),INITIAL_STOP_R=math.fsum(t['gross_R'] for t in closed if t['exit_reason']=='INITIAL_STOP'),
  ATR_TRAILING_STOP_count=sum(t['exit_reason']=='ATR_TRAILING_STOP' for t in closed),ATR_TRAILING_STOP_R=math.fsum(t['gross_R'] for t in closed if t['exit_reason']=='ATR_TRAILING_STOP'),
  negative_trailing_count=sum(t['exit_reason']=='ATR_TRAILING_STOP' and t['gross_R']<0 for t in closed),
  top5_winners_R=math.fsum(sorted(wins,reverse=True)[:5]),top10_winners_R=math.fsum(sorted(wins,reverse=True)[:10]),gross_positive_R=math.fsum(wins),gross_negative_R=math.fsum(losses),
  CLOSED_R_DD=drawdown([0.]+list(__import__('itertools').accumulate(rs))) if curve is not None else None,MTM_R_DD=drawdown([0.]+curve.gross_MTM_R.tolist()) if curve is not None else None,
  DD_status='SEPARATE_LIFECYCLE' if curve is not None else 'UNDEFINED_NO_COLD_START_SPLICE',cash_Net='NOT_VALIDATED',RUB_drawdown='NOT_VALIDATED',cash_return='NOT_VALIDATED')
 result=[]
 for basis in ('CLOSED_R','MTM_R'):
  vals=[m[basis] for m in months];streak=consecutive(months,basis)
  if curve is None:streak=max((consecutive([m for m in months if m['lifecycle']==l],basis) for l in {m['lifecycle'] for m in months}),default=0)
  result.append(dict(**stats,monthly_basis=basis,positive_months=sum(sign(x)>0 for x in vals),negative_months=sum(sign(x)<0 for x in vals),zero_months=sum(sign(x)==0 for x in vals),observed_months=len(vals),worst_month_R=min(vals) if vals else None,median_month_R=statistics.median(vals) if vals else None,max_negative_month_streak=streak))
 return result

def comparisons(results,out):
 alltrades=[t for r in results for t in r['trades']];control={identity(t):t for t in alltrades if t['variant']=='CONTROL'};rows=[];entryrows=[]
 # Every raw signal has a stable identifier, even while the instrument is occupied.
 signals={}
 for result in results:
  for s in result['signals']:
   key='|'.join(str(s[k]) for k in ('system','lifecycle','fold_id','instrument'))+'|'+s['at'].isoformat()+'|'+('LONG' if s['side']==1 else 'SHORT')
   signals[(s['variant'],key)]=s
 for system in ('H1','M15'):
  variants=('STOP_2p0','STOP_1p5') if system=='H1' else ('STOP_1p5',)
  for variant in variants:
   other={identity(t):t for t in alltrades if t['system']==system and t['variant']==variant};base={k:v for k,v in control.items() if v['system']==system}
   for key in sorted(base.keys()|other.keys()):
    a=base.get(key);b=other.get(key);t=a or b;both=a is not None and b is not None;closed=both and a['status']==b['status']=='CLOSED';side=1 if t['direction']=='LONG' else -1
    pr=side*(b['exit_price']-a['entry_price'])/a['initial_risk_price'] if closed else None
    delta=pr-a['gross_R'] if closed else None
    lost=closed and a['gross_R']>0>b['gross_R'];improved=closed and a['gross_R']<0 and delta>EPS
    early=bool(both and system=='H1' and b['trail1_activation_time'] is not None and (a['trail1_activation_time'] is None or b['trail1_activation_time']<a['trail1_activation_time']))
    earlyexit=bool(closed and early and b['exit_reason']=='ATR_TRAILING_STOP' and (a['trail1_activation_time'] is None or b['exit_time']<a['trail1_activation_time']))
    row=dict(system=system,lifecycle=t['lifecycle'],fold_id=t['fold_id'],symbol=t['instrument'],direction=t['direction'],signal_id=key,signal_time=t.get('signal_time',t['entry_time']),variant=variant,match='COMMON_SIGNAL' if both else 'MISSED_CONTROL_ENTRY' if a else 'NEW_VARIANT_ENTRY',
     CONTROL_trade_id=a['trade_id'] if a else None,variant_trade_id=b['trade_id'] if b else None,CONTROL_status=a['status'] if a else None,variant_status=b['status'] if b else None,
     CONTROL_R=a['gross_R'] if a else None,variant_own_R=b['gross_R'] if b else None,variant_exit_in_CONTROL_R0=pr,delta_exit_in_CONTROL_R0=delta,
     CONTROL_entry=a['entry_price'] if a else None,variant_entry=b['entry_price'] if b else None,CONTROL_R0=a['initial_risk_price'] if a else None,variant_R0=b['initial_risk_price'] if b else None,
     CONTROL_exit_time=a.get('exit_time') if a else None,variant_exit_time=b.get('exit_time') if b else None,CONTROL_exit_reason=a.get('exit_reason') if a else None,variant_exit_reason=b.get('exit_reason') if b else None,
     TIGHT_STOP_LOST_WINNER=lost,original_loss_improved_price=improved,original_loss_improved_ownR=closed and a['gross_R']<0 and b['gross_R']>a['gross_R']+EPS,
     original_loss_closed_earlier=closed and a['gross_R']<0 and b['exit_time']<a['exit_time'],original_loss_turned_positive=closed and a['gross_R']<0<b['gross_R'],
     CONTROL_trigger_time=a.get('trigger_bar_time') if a else None,variant_trigger_time=b.get('trigger_bar_time') if b else None,CONTROL_activation_time=a.get('trail1_activation_time') if a else None,variant_activation_time=b.get('trail1_activation_time') if b else None,
     H1_earlier_activation=early,H1_trailing_exit_before_CONTROL_activation=earlyexit,H1_early_activation_delta_CONTROL_R0=delta if earlyexit else None,
     CONTROL_signal_state=signals.get(('CONTROL',key),{}).get('reason','ACCEPTED' if a else 'OCCUPIED'),variant_signal_state=signals.get((variant,key),{}).get('reason','ACCEPTED' if b else 'OCCUPIED'),
     CONTROL_occupied_trade=signals.get(('CONTROL',key),{}).get('occupied_trade_id'),variant_occupied_trade=signals.get((variant,key),{}).get('occupied_trade_id'))
    rows.append(row)
    if not both:entryrows.append(row)
 for system in ('H1','M15'):
  for life,fold in sorted({(t['lifecycle'],t['fold_id']) for t in alltrades if t['system']==system}):
   winners=sorted([t for t in control.values() if t['system']==system and t['lifecycle']==life and t['fold_id']==fold and t['status']=='CLOSED' and t['gross_R']>0],key=lambda t:-t['gross_R']);ranks={identity(t):i+1 for i,t in enumerate(winners)};profit=math.fsum(t['gross_R'] for t in winners)
   for row in rows:
    if row['system']==system and row['lifecycle']==life and row['fold_id']==fold:
     row['CONTROL_winner_rank']=ranks.get(row['signal_id']);row['CONTROL_positive_R_total']=profit
     row['positive_profit_lost_CONTROL_R0']=max(0.,-row['delta_exit_in_CONTROL_R0']) if row['signal_id'] in ranks and row['delta_exit_in_CONTROL_R0'] is not None else None
     row['positive_profit_lost_share']=row['positive_profit_lost_CONTROL_R0']/profit if row.get('positive_profit_lost_CONTROL_R0') is not None and profit else None
 csvout(out/'STOP_VARIANT_TRADE_COMPARISON.csv',rows);csvout(out/'NEW_AND_MISSED_ENTRIES.csv',entryrows)
 csvout(out/'LOST_WINNERS.csv',[r for r in rows if r['TIGHT_STOP_LOST_WINNER']],fields=list(rows[0]) if rows else None)
 csvout(out/'LARGE_WINNERS.csv',[r for r in rows if r.get('CONTROL_winner_rank') and r['CONTROL_winner_rank']<=10])
 return rows

def round_stop(price,side,tick):
 p,t=Decimal(str(price)),Decimal(str(tick));return float((p/t).to_integral_value(rounding=ROUND_FLOOR if side==1 else ROUND_CEILING)*t)

def capital(results,out):
 registry={r['research_symbol']:r for r in csvin(ROOT/'TradingSystemLab/stage8_robot/production_instrument_registry.csv')};rows=[]
 for result in results:
  for t in result['trades']:
   s=t['instrument'];side=1 if t['direction']=='LONG' else -1;tick=float(registry[s]['price_step']);value=float(registry[s]['tick_value']);rounded=round_stop(t['initial_stop_price'],side,tick);risk=abs(t['entry_price']-rounded)
   # Static one-lot sensitivity, never claimed historical executable Net.
   rows.append(dict(system=t['system'],lifecycle=t['lifecycle'],fold_id=t['fold_id'],variant=t['variant'],signal_id=identity(t),symbol=s,entry=t['entry_price'],research_initial_stop=t['initial_stop_price'],research_R0=t['initial_risk_price'],
    static_tick_size=tick,static_tick_value_RUB=value,static_contract_size=registry[s]['contract_size'],quantity_step=1,initial_on_static_grid=abs(t['initial_stop_price']/tick-round(t['initial_stop_price']/tick))<1e-8,
    outward_rounded_stop=rounded,outward_rounded_Risk0=risk,risk_change_fraction=risk/t['initial_risk_price']-1,
    static_1lot_stop_distance_RUB=risk/tick*value,static_1lot_research_risk_RUB=t['initial_risk_price']/tick*value,
    R15=.015,nominal_limit=.06,integer_qty=None,realized_equity_RUB=None,dated_GO_RUB=None,available_margin_RUB=None,documented_broker_cost_RUB=None,
    money_Net='NOT_VALIDATED',RUB_DD='NOT_VALIDATED',cash_return='NOT_VALIDATED',historical_grid_authority='NOT_VALIDATED_STATIC_SNAPSHOT_ONLY',
    quantity_formula='floor(min(0.015*realized_equity / risk_per_lot_RUB, available_margin / dated_GO)); cap total reserved nominal initial risk at 0.06*realized_equity',
    grid_diagnostic='Outward static-grid sensitivity only; frozen replay stops NOT rounded or replaced'))
 csvout(out/'CAPITAL_FEASIBILITY.csv',rows)
 trailing=[]
 for r in results:
  for t in r['trace']:
   tick=float(registry[t['instrument']]['price_step'])
   for field in ('stop_entering','stop_after'):
    if t.get(field) is not None:trailing.append(dict(system=t['system'],lifecycle=t['lifecycle'],fold_id=t['fold_id'],variant=t['variant'],symbol=t['instrument'],at=t['at'],trade_id=t['trade_id'],field=field,on_static_grid=abs(t[field]/tick-round(t[field]/tick))<1e-8))
 groups=defaultdict(list)
 for t in trailing:groups[tuple(t[k] for k in ('system','lifecycle','fold_id','variant','symbol','field'))].append(t)
 grid=[dict(zip(('system','lifecycle','fold_id','variant','symbol','field'),key),observations=len(ts),off_grid=sum(not t['on_static_grid'] for t in ts)) for key,ts in sorted(groups.items())]
 csvout(out/'STOP_GRID_SUMMARY.csv',grid)
 js(out/'CAPITAL_FEASIBILITY.json',dict(status='NOT_VALIDATED',risk_fraction=.015,nominal_limit=.06,static_registry_sha256=sha(ROOT/'TradingSystemLab/stage8_robot/production_instrument_registry.csv'),missing=['starting equity and cashflows for every separate account/lifecycle','dated historical GO and margin constraints','dated contract/tick-size/tick-value authority for full history','verified fees, slippage, funding and settlement costs'],no_cash_return_inferred_from_R=True,normalised_costs='H1 C1 .002/Risk0 round trip, not broker fees; M15 GROSS_ONLY',grid=grid))
 return rows
