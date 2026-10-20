"""Descriptive calendar analysis. No strategy selection or monetary proxy."""
import math,statistics
from collections import defaultdict
import pandas as pd
from common import *

EPS=1e-8
def sign(x):return 1 if x>EPS else -1 if x< -EPS else 0
def max_streak(xs):
    best=run=0
    for x in xs:
        run=run+1 if sign(x)<0 else 0;best=max(best,run)
    return best
def dd(values):
    peak=values[0] if values else 0.;worst=0.
    for v in values:peak=max(peak,v);worst=max(worst,peak-v)
    return worst
def pf(values):
    pos=math.fsum(v for v in values if v>0);neg=-math.fsum(v for v in values if v<0)
    return pos/neg if neg else None
def trade_stats(ts):
    rs=[t['gross_R'] for t in ts if t['status']=='CLOSED'];w=[v for v in rs if v>0];l=[v for v in rs if v<0]
    return dict(closed_positions=len(rs),open_positions=sum(t['status']=='OPEN' for t in ts),gross_PF=pf(rs),gross_R=math.fsum(rs),expectancy_gross_R=statistics.mean(rs) if rs else None,
        win_rate=len(w)/len(rs) if rs else None,average_win_R=statistics.mean(w) if w else None,average_loss_R=statistics.mean(l) if l else None,
        average_win_abs_loss_ratio=statistics.mean(w)/abs(statistics.mean(l)) if w and l else None,
        positions_observed_reaching_2R=sum(t['reached_2R'] for t in ts),fractional_partial_positions=sum(t['partial_executed'] for t in ts),
        actually_executable_partial_positions=None,
        gross_R_without_top5=math.fsum(rs)-math.fsum(sorted(w,reverse=True)[:5]),gross_PF_without_top5=pf(sorted(rs,reverse=True)[min(5,len(w)):]),
        gross_R_without_top10=math.fsum(rs)-math.fsum(sorted(w,reverse=True)[:10]),gross_PF_without_top10=pf(sorted(rs,reverse=True)[min(10,len(w)):]))

def build(streams,results,out):
    trades=[t for r in results for t in r['trades']];monthly=[];summaries=[];flips=[];exposure=[]
    groups=sorted({(s['system'],s['lifecycle'],s['fold_id']) for s in streams})
    for system,life,fold in groups:
        ss=[s for s in streams if (s['system'],s['lifecycle'],s['fold_id'])==(system,life,fold)]
        # Each WF fold stays separate; no averaging/overlap with Baseline.
        months=pd.period_range('2023-01','2026-09',freq='M') if life!='walk_forward' else pd.period_range('2024-01','2024-12',freq='M')
        for variant in ('CONTROL','PARTIAL_TP_2R_50'):
            rr=[r for r in results if r['marks'][0]['system']==system and r['marks'][0]['lifecycle']==life and r['marks'][0]['fold_id']==fold and r['marks'][0]['variant']==variant]
            tt=[t for t in trades if (t['system'],t['lifecycle'],t['fold_id'],t['variant'])==(system,life,fold,variant)]
            # Aggregate current observations by timestamp, ffill only previous marks.
            series={r['marks'][0]['instrument']:pd.DataFrame(r['marks']).set_index('at') for r in rr}
            clock=sorted(set(at for f in series.values() for at in f.index))
            curves=[]
            for col in ('gross_realized_R','gross_unrealized_R','gross_MTM_R','C1_normalized_MTM_R','remaining_quantity'):
                curves.append(pd.DataFrame({s:f[col].reindex(clock).ffill().fillna(0.) for s,f in series.items()}).sum(axis=1))
            curve=pd.DataFrame(dict(zip(('realized','unrealized','MTM','C1_MTM','remaining'),curves)))
            selected=[]
            prev_mark=prev_c1=0.
            for period in months:
                ym=str(period);sub=curve.loc[[at.strftime('%Y-%m')==ym for at in curve.index]]
                observed=[s['instrument'] for s in ss if any(b['at'].strftime('%Y-%m')==ym for b in s['bars'])]
                active=bool(observed)
                closed=[t for t in tt if t['status']=='CLOSED' and t['exit_time'].strftime('%Y-%m')==ym]
                legs=[(t,part) for t in tt for part in (1,2) if t[f'part{part}_exit_time'] and t[f'part{part}_exit_time'].strftime('%Y-%m')==ym]
                gross=math.fsum(t[f'part{part}_gross_R'] for t,part in legs) if active else None
                cp=math.fsum(t['gross_R'] for t in closed) if active else None
                r=dict(system=system,lifecycle=life,fold_id=fold,variant=variant,model='FRACTIONAL_REFERENCE',month=ym,
                    coverage='NO_DATA' if not active else 'PARTIAL_N4' if len(observed)<4 else 'N4_OBSERVED',observed_instruments='|'.join(observed),
                    period_status='2026_YTD_PARTIAL_ENDPOINT' if ym=='2026-09' and active else '2023_PARTIAL_N4_DIAGNOSTIC' if ym.startswith('2023') and active else 'OBSERVED' if active else 'NO_DATA',
                    gross_closed_leg_R=gross,gross_closed_position_R=cp,
                    gross_MTM_change_R=float(sub.MTM.iloc[-1]-prev_mark) if active else None,
                    gross_MTM_intra_month_DD_R=dd([prev_mark]+sub.MTM.tolist()) if active else None,
                    gross_closed_leg_sign=sign(gross) if active else None,
                    gross_MTM_sign=sign(float(sub.MTM.iloc[-1]-prev_mark)) if active else None,
                    C1_normalized_closed_position_R=math.fsum(t['net_R_C1'] for t in closed) if active and system=='H1' else None,
                    C1_normalized_MTM_change_R=float(sub.C1_MTM.iloc[-1]-prev_c1) if active and system=='H1' else None,
                    closed_positions=len(closed) if active else None,closed_legs=len(legs) if active else None,
                    open_positions_at_last_observation=sum(bool(f.loc[f.index<=sub.index[-1]].iloc[-1].active_trade_id) if pd.notna(f.loc[f.index<=sub.index[-1]].iloc[-1].active_trade_id) else False for f in series.values() if len(f.loc[f.index<=sub.index[-1]])) if active else None,
                    gross_end_unrealized_R=float(sub.unrealized.iloc[-1]) if active else None,
                    capital_MTM_return_pct=None,cash_status='CASH_MODEL_NOT_VALIDATED',net_money_PF=None,net_money_R=None)
                if active:prev_mark=float(sub.MTM.iloc[-1]);prev_c1=float(sub.C1_MTM.iloc[-1]);selected.append(r)
                monthly.append(r)
            metrics=trade_stats(tt)
            for basis,col in [('GROSS_CLOSED_LEG_R','gross_closed_leg_R'),('GROSS_MTM_R','gross_MTM_change_R')]:
                vals=[r[col] for r in selected];n=len(vals)
                summaries.append(dict(system=system,lifecycle=life,fold_id=fold,variant=variant,model='FRACTIONAL_REFERENCE',monthly_basis=basis,
                    positive_months=sum(sign(x)>0 for x in vals),negative_months=sum(sign(x)<0 for x in vals),zero_months=sum(sign(x)==0 for x in vals),covered_months=n,
                    positive_share=sum(sign(x)>0 for x in vals)/n if n else None,negative_share=sum(sign(x)<0 for x in vals)/n if n else None,zero_share=sum(sign(x)==0 for x in vals)/n if n else None,
                    worst_month_R=min(vals) if vals else None,median_month_R=statistics.median(vals) if vals else None,
                    max_consecutive_negative_months=max_streak(vals),max_MTM_intramonth_DD_R=max((r['gross_MTM_intra_month_DD_R'] for r in selected),default=None),
                    C1_normalized_PF=pf([t['net_R_C1'] for t in tt if t['status']=='CLOSED']) if system=='H1' else None,
                    C1_normalized_R=math.fsum(t['net_R_C1'] for t in tt if t['status']=='CLOSED') if system=='H1' else None,
                    **metrics,net_money_PF=None,net_money_R=None,cash_status='CASH_MODEL_NOT_VALIDATED',verdict='INCONCLUSIVE'))
            intervals=[];weighted_qty=occupied=duration=0.
            for r in rr:
                mm=r['marks']
                for a,b in zip(mm,mm[1:]):
                    dt=(b['at']-a['at']).total_seconds();duration+=dt
                    occupied+=dt*bool(a['active_trade_id']);weighted_qty+=dt*a['remaining_quantity']
            exposure.append(dict(system=system,lifecycle=life,fold_id=fold,variant=variant,observed_grid_time_seconds=duration,occupied_seconds=occupied,
                model_quantity_seconds=weighted_qty,occupied_time_share=occupied/duration if duration else None,
                model_quantity_time_share=weighted_qty/duration if duration else None,available_margin_RUB=None,subsequent_entry_changes=0,
                limitation='Time between observed completed bars including closures; research quantity exposure, no money/margin claim'))
    # Disjoint descriptive calendar union; this is explicitly NOT an equity splice.
    for variant in ('CONTROL','PARTIAL_TP_2R_50'):
        tt=[t for t in trades if t['system']=='H1' and t['lifecycle']!='walk_forward' and t['variant']==variant]
        mm=[r for r in monthly if r['system']=='H1' and r['lifecycle']!='walk_forward' and r['variant']==variant and r['coverage']!='NO_DATA']
        mm.sort(key=lambda x:x['month']);assert len({r['month'] for r in mm})==len(mm)
        for basis,col in [('GROSS_CLOSED_LEG_R','gross_closed_leg_R'),('GROSS_MTM_R','gross_MTM_change_R')]:
            vals=[r[col] for r in mm];n=len(vals)
            summaries.append(dict(system='H1',lifecycle='DISJOINT_BASELINE_AND_HISTORICAL_OOS',fold_id='',variant=variant,model='FRACTIONAL_REFERENCE',monthly_basis=basis,
                positive_months=sum(sign(x)>0 for x in vals),negative_months=sum(sign(x)<0 for x in vals),zero_months=sum(sign(x)==0 for x in vals),covered_months=n,
                positive_share=sum(sign(x)>0 for x in vals)/n,negative_share=sum(sign(x)<0 for x in vals)/n,zero_share=sum(sign(x)==0 for x in vals)/n,
                worst_month_R=min(vals),median_month_R=statistics.median(vals),max_consecutive_negative_months=max_streak(vals),
                max_MTM_intramonth_DD_R=max(r['gross_MTM_intra_month_DD_R'] for r in mm),**trade_stats(tt),
                C1_normalized_PF=pf([t['net_R_C1'] for t in tt if t['status']=='CLOSED']),C1_normalized_R=math.fsum(t['net_R_C1'] for t in tt if t['status']=='CLOSED'),
                net_money_PF=None,net_money_R=None,cash_status='CASH_MODEL_NOT_VALIDATED',verdict='INCONCLUSIVE'))
    for key in sorted({(r['system'],r['lifecycle'],r['fold_id'],r['month']) for r in monthly}):
        pair=[r for r in monthly if (r['system'],r['lifecycle'],r['fold_id'],r['month'])==key]
        a,b=pair
        for col in ('gross_closed_leg_R','gross_MTM_change_R'):
            if a[col] is None:continue
            flips.append(dict(system=key[0],lifecycle=key[1],fold_id=key[2],month=key[3],basis=col,CONTROL_R=a[col],PARTIAL_R=b[col],
                transition='NEGATIVE_TO_POSITIVE' if sign(a[col])<0<sign(b[col]) else 'POSITIVE_TO_NEGATIVE' if sign(b[col])<0<sign(a[col]) else 'OTHER',delta_R=b[col]-a[col]))
    feasibility=[];winner=[]
    c={(t['system'],t['lifecycle'],t['fold_id'],t['instrument'],t['trade_id']):t for t in trades if t['variant']=='CONTROL'}
    p={(t['system'],t['lifecycle'],t['fold_id'],t['instrument'],t['trade_id']):t for t in trades if t['variant']!='CONTROL'}
    assert c.keys()==p.keys()
    for key,a in c.items():
        b=p[key];feasibility.append(dict(system=key[0],lifecycle=key[1],fold_id=key[2],instrument=key[3],trade_id=key[4],entry_time=a['entry_time'],
            initial_risk_price=a['initial_risk_price'],model='EXECUTABLE_INTEGER',risk_fraction=.015,aggregate_limit=.06,executed_integer_qty=None,partial_integer_qty=None,
            can_partial=None,realized_equity_RUB=None,historical_GO_RUB=None,available_margin_RUB=None,status='CASH_MODEL_NOT_VALIDATED',
            reason='No complete dated historical GO/specs/equity/cost authority; no integer replay invented',fractional_partial=b['partial_executed']))
        if a['status']=='CLOSED':
            delta=b['gross_R']-a['gross_R'];winner.append(dict(system=key[0],lifecycle=key[1],fold_id=key[2],instrument=key[3],trade_id=key[4],CONTROL_gross_R=a['gross_R'],PARTIAL_gross_R=b['gross_R'],
                delta_R=delta,lost_R=max(0.,-delta),saved_R=max(0.,delta),retained_fraction=b['gross_R']/a['gross_R'] if a['gross_R']>0 else None,partial_executed=b['partial_executed']))
    for group in sorted({(r['system'],r['lifecycle'],r['fold_id']) for r in winner}):
        ww=[r for r in winner if (r['system'],r['lifecycle'],r['fold_id'])==group]
        rank={r['trade_id']+'|'+r['instrument']:i+1 for i,r in enumerate(sorted(ww,key=lambda x:-x['CONTROL_gross_R']))}
        gross_wins=math.fsum(r['CONTROL_gross_R'] for r in ww if r['CONTROL_gross_R']>0)
        for r in ww:r.update(CONTROL_winner_rank=rank[r['trade_id']+'|'+r['instrument']],lost_share_of_CONTROL_positive_R=r['lost_R']/gross_wins if gross_wins else None)
    for system in ('H1','M15'):
        csvout(out/f'{system}_TRADES.csv',[r for r in trades if r['system']==system])
        money_months=[]
        for r in monthly:
            if r['system']!=system:continue
            money_months.append({k:r[k] if k in ('system','lifecycle','fold_id','variant','month','coverage','observed_instruments','period_status','cash_status') else 'EXECUTABLE_INTEGER' if k=='model' else None for k in r})
        money_summaries=[]
        for r in summaries:
            if r['system']!=system or r['monthly_basis']!='GROSS_CLOSED_LEG_R':continue
            money_summaries.append({k:r[k] if k in ('system','lifecycle','fold_id','variant','cash_status','verdict') else 'EXECUTABLE_INTEGER' if k=='model' else 'CAPITAL_MTM_NOT_VALIDATED' if k=='monthly_basis' else None for k in r})
        csvout(out/f'{system}_MONTHLY.csv',[r for r in monthly if r['system']==system]+money_months)
        csvout(out/f'{system}_SUMMARY.csv',[r for r in summaries if r['system']==system]+money_summaries)
    csvout(out/'MONTH_SIGN_TRANSITIONS.csv',flips);csvout(out/'EXPOSURE.csv',exposure)
    csvout(out/'PARTIAL_EXECUTION_FEASIBILITY.csv',feasibility);csvout(out/'WINNER_GIVEBACK.csv',winner)
    return dict(summaries=summaries,monthly=monthly,flips=flips,winners=winner,exposure=exposure)
