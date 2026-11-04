"""Descriptive quarterly tails from EXISTING stop-truncated excursion bounds.

No OHLCV scan: derive FP4, strict >5 and ambiguity from pinned MFE bounds.
Actual model net>=4/5, stop/entry-bar/session/time exits use trade denominators.
"""
from __future__ import annotations
from collections import defaultdict
from datetime import datetime
import json
from statistics import mean,median

from .suitability_research import MODES,OLD,NEW
from .regime_monthly_comparison import ROOT,read_csv,dt
from .regime_research import dump_csv

EPS=1e-7
ALL='ALL_INDEPENDENT_ACCOUNTS'


def bounds_quality(event):
    low,high=float(event['mfe_low']),float(event['mfe_high'])
    return dict(fp4=int(low>=4-EPS),amb4=int(low<4-EPS<=high),
        beyond5=int(low>5+EPS),amb_beyond5=int(low<=5+EPS<high),mfe_low=low,mfe_high=high)


def known_raw(rows,as_of):
    # Inspect availability before touching any outcome's numerical fields.
    return [dict(r,outcome=r['outcome'] if r['outcome'] is not None and dt(r['outcome']['available'])<=as_of else None) for r in rows]


def tail_stats(raw,trades):
    paths=[r['outcome'] for r in raw if r['outcome'] is not None]
    n=len(paths);quality=[bounds_quality(p) for p in paths]
    metrics={}
    for target in (2,3,4,5):
        hits=sum(q['fp4'] for q in quality) if target==4 else sum(int(p['fp'+str(target)]) for p in paths)
        amb=sum(q['amb4'] for q in quality) if target==4 else sum(int(p['amb'+str(target)]) for p in paths)
        metrics.update({f'FP{target}_n':hits,f'FP{target}_denominator':n,
            f'FP{target}':hits/n if n else None,f'amb{target}_n':amb,
            f'FP{target}_all_raw_lower':hits/len(raw) if raw else None,
            f'FP{target}_all_raw_upper':(hits+len(raw)-n+amb)/len(raw) if raw else None})
    values=[r['net'] for r in trades];wins=[x for x in values if x>0];losses=[x for x in values if x<0]
    stops=[r for r in trades if r['stop']]
    return dict(raw_total=len(raw),raw_observed=n,raw_censored=len(raw)-n,**metrics,
        beyond5_n=sum(q['beyond5'] for q in quality),beyond5_denominator=n,
        beyond5=sum(q['beyond5'] for q in quality)/n if n else None,
        amb_beyond5_n=sum(q['amb_beyond5'] for q in quality),
        MFE_denominator=n,MFE_low_mean=mean(q['mfe_low'] for q in quality) if n else None,
        MFE_low_median=median(q['mfe_low'] for q in quality) if n else None,
        MFE_high_mean=mean(q['mfe_high'] for q in quality) if n else None,
        raw_stop_n=sum(p['stop_touch']=='True' for p in paths),raw_stop_denominator=n,
        raw_stop_share=sum(p['stop_touch']=='True' for p in paths)/n if n else None,
        trades=len(trades),trade_stops=len(stops),trade_stop_share=len(stops)/len(trades) if trades else None,
        entry_bar_stops=sum(r['reason']==4 for r in trades),first_session_stops=sum(r['session_span']==1 for r in stops),
        trade_exit_denominator=len(trades),stop_exit_denominator=len(stops),
        entry_bar_stop_share=sum(r['reason']==4 for r in trades)/len(trades) if trades else None,
        first_session_stop_share=sum(r['session_span']==1 for r in stops)/len(trades) if trades else None,
        time_exits=sum(r['reason']==3 for r in trades),
        time_exit_share=sum(r['reason']==3 for r in trades)/len(trades) if trades else None,
        actual_net_ge4_n=sum(v>=4 for v in values),actual_net_ge5_n=sum(v>=5 for v in values),
        actual_net_large_denominator=len(trades),
        net_C1_R=sum(values),mean_net_C1_R=mean(values) if values else None,
        PF_C1=sum(wins)/-sum(losses) if losses else None,wins=len(wins),losses=len(losses),
        win_rate=len(wins)/len(values) if values else None,
        mean_win_R=mean(wins) if wins else None,mean_loss_R=mean(losses) if losses else None,
        net_ge5_positive_R=sum(v for v in values if v>=5),
        net_ge5_share_positive_R=sum(v for v in values if v>=5)/sum(wins) if wins else None)


def build_tail_tables(output,groups,raw,bounds,episodes):
    from .calendar_review import quarter,shift_month,history_start
    # Add already published session_span without recalculating any trade path.
    spans={}
    for name,modern in (('V20-03/results/CLOSED_TRADES.csv',False),('V20-03/comparison/DIAGNOSTIC_REPLAY_TRADES.csv',True)):
        for r in read_csv(ROOT/name):
            instrument=r['symbol'] if modern else r['family']
            spans[r['account'],instrument,r['entry_dt']]=int(r['session_span'])
    trades=[]
    for (strategy,instrument),rows in groups.items():
        for r in rows:
            trades.append(dict(r,session_span=spans[strategy,instrument,str(r['entry'])]))
    def raw_for(strategy,instrument,a,b):
        selected=[r for r in raw if (strategy==ALL or r['strategy']==strategy) and
            (instrument=='ALL' or r['instrument']==instrument) and a<=r['signal']<b]
        if strategy==ALL:
            selected=list({(r['instrument'],r['signal']):r for r in selected}.values())
        return selected
    def trade_for(strategy,instrument,a,b):
        return [r for r in trades if (strategy==ALL or r['strategy']==strategy) and
            (instrument=='ALL' or r['instrument']==instrument) and a<=r['entry']<b]
    def row(strategy,instrument,a,b,label):
        end=bounds[instrument][1] if instrument!='ALL' else max(e for s,e in bounds.values())
        start=bounds[instrument][0] if instrument!='ALL' else min(s for s,e in bounds.values())
        active=a<end and b>start
        active_symbols=[instrument] if instrument!='ALL' else [s for s,(lo,hi) in bounds.items() if a<hi and b>lo]
        partial=bool(active and any(bounds[s][1]<b or a<history_start(s,bounds)<b for s in active_symbols))
        paths=raw_for(strategy,instrument,a,b);fills=trade_for(strategy,instrument,a,b)
        known=tail_stats(known_raw(paths,b),[r for r in fills if r['available']<=b])
        return dict(strategy=strategy,instrument=instrument,period=label,start=a,end=b,
            available=active,partial=partial,
            **tail_stats(paths,fills),
            **{'known_at_review_'+k:v for k,v in known.items()},
            horizon_pending_at_review=sum(r['outcome'] is not None and dt(r['outcome']['available'])>b for r in paths),
            model_pending_at_review=sum(r['available']>b for r in fills))
    quarterly=[];a=datetime(2018,1,1)
    while a<max(e for s,e in bounds.values()):
        b=shift_month(a,3);label=f'{a.year}Q{(a.month-1)//3+1}'
        for strategy in (*MODES,ALL):
            for instrument in (*OLD,*NEW,'ALL'):quarterly.append(row(strategy,instrument,a,b,label))
        a=b
    epochs=[]
    for a,b,label in ((datetime(2018,1,1),datetime(2019,1,1),'2018'),
                       (datetime(2019,1,1),datetime(2023,1,1),'2019-2022'),
                       (datetime(2023,1,1),datetime(2027,1,1),'2023-2026')):
        for strategy in (*MODES,ALL):
            for instrument in (*OLD,*NEW,'ALL'):epochs.append(row(strategy,instrument,a,b,label))
    transitions=[]
    lookup={(r['strategy'],r['instrument'],r['start']):r for r in quarterly}
    for r in quarterly:
        if r['strategy']==ALL or r['instrument']=='ALL' or r['net_C1_R']>=0:continue
        prev=lookup.get((r['strategy'],r['instrument'],shift_month(r['start'],-3)))
        nxt=lookup.get((r['strategy'],r['instrument'],r['end']))
        if prev is None or nxt is None:continue
        enough=all(q['raw_observed']>=10 and q['trades']>=10 and not q['partial'] and q['available'] for q in (prev,r,nxt))
        falling4=bool(enough and r['FP4']<prev['FP4']);falling5=bool(enough and r['FP5']<prev['FP5'])
        risingstop=bool(enough and r['raw_stop_share']>prev['raw_stop_share'])
        restored=bool(enough and nxt['FP4']>r['FP4'] and nxt['FP5']>r['FP5'])
        causal_enough=bool(enough and all(q['known_at_review_raw_observed']>=10 and q['known_at_review_trades']>=10 for q in (prev,r))
                          and r['known_at_review_net_C1_R']<0)
        causal_f4=bool(causal_enough and r['known_at_review_FP4']<prev['known_at_review_FP4'])
        causal_f5=bool(causal_enough and r['known_at_review_FP5']<prev['known_at_review_FP5'])
        causal_stops=bool(causal_enough and r['known_at_review_raw_stop_share']>prev['known_at_review_raw_stop_share'])
        cost=[]
        for ep in episodes:
            if (ep['strategy'],ep['instrument'])!=(r['strategy'],r['instrument']):continue
            if ep['episode_start']<nxt['end'] and ep['episode_end']>nxt['start']:
                selected=[t for t in trade_for(r['strategy'],r['instrument'],nxt['start'],nxt['end'])
                    if ep['episode_start']<=t['entry']<ep['episode_end']]
                cost.append(dict(method=ep['method'],lost_positive_R=sum(max(0,t['net']) for t in selected),
                    avoided_negative_R=-sum(min(0,t['net']) for t in selected),lost_wins=sum(t['net']>0 for t in selected)))
        transitions.append(dict(strategy=r['strategy'],instrument=r['instrument'],weak_quarter=r['period'],
            next_quarter=nxt['period'],sufficient_comparison=enough,weak_FP4=r['FP4'],weak_FP5=r['FP5'],weak_stops=r['raw_stop_share'],
            next_FP4=nxt['FP4'],next_FP5=nxt['FP5'],next_stops=nxt['raw_stop_share'],
            next_net_C1_R=nxt['net_C1_R'],next_actual_net_ge4_n=nxt['actual_net_ge4_n'],next_actual_net_ge5_n=nxt['actual_net_ge5_n'],
            falling_FP4=falling4,falling_FP5=falling5,rising_stops=risingstop,restored_FP4_FP5=restored,
            profitable_next=bool(enough and nxt['net_C1_R']>0),
            warning_signature=bool(falling4 and falling5 and risingstop),
            false_signature=bool(falling4 and falling5 and risingstop and nxt['net_C1_R']>0),
            sufficient_causal_comparison=causal_enough,causal_falling_FP4=causal_f4,causal_falling_FP5=causal_f5,
            causal_rising_stops=causal_stops,causal_signature=causal_f4 and causal_f5 and causal_stops,
            causal_signature_followed_profit=bool(causal_f4 and causal_f5 and causal_stops and nxt['net_C1_R']>0),
            filter_costs_json=json.dumps(cost,separators=(',',':'))))
    dump_csv(output/'V20_CALENDAR_LARGE_MOVES_QUARTERLY.csv',quarterly)
    dump_csv(output/'V20_CALENDAR_LARGE_MOVES_EPOCHS.csv',epochs)
    dump_csv(output/'V20_CALENDAR_LARGE_MOVES_RECOVERIES.csv',transitions)
    association=[]
    for epoch,years in (('2018',{2018}),('2019-2022',set(range(2019,2023))),('2023-2026',set(range(2023,2027)))):
        for strategy in (*MODES,ALL):
            for kind in ('NEGATIVE','POSITIVE'):
                selected=[r for r in quarterly if r['start'].year in years and r['strategy']==strategy and r['instrument']!='ALL'
                    and r['available'] and not r['partial'] and r['trades']>=10 and r['raw_observed']>=10
                    and (r['net_C1_R']<0 if kind=='NEGATIVE' else r['net_C1_R']>0)]
                n=sum(r['raw_observed'] for r in selected)
                association.append(dict(epoch=epoch,strategy=strategy,quality=kind,quarters=len(selected),raw_observed=n,
                    FP4=sum(r['FP4_n'] for r in selected)/n if n else None,
                    FP5=sum(r['FP5_n'] for r in selected)/n if n else None,
                    stop_share=sum(r['raw_stop_n'] for r in selected)/n if n else None,
                    MFE_low_mean=sum(r['MFE_low_mean']*r['raw_observed'] for r in selected)/n if n else None))
    dump_csv(output/'V20_CALENDAR_LARGE_MOVES_BY_QUALITY.csv',association)
    valid=[r for r in transitions if r['sufficient_comparison']]
    return dict(quarterly_rows=len(quarterly),epoch_rows=len(epochs),negative_quarter_transitions=len(transitions),
        sufficient_transitions=len(valid),falling4=sum(r['falling_FP4'] for r in valid),
        falling5=sum(r['falling_FP5'] for r in valid),rising_stops=sum(r['rising_stops'] for r in valid),
        warning_signature=sum(r['warning_signature'] for r in valid),
        signature_followed_by_profit=sum(r['false_signature'] for r in valid),
        causal_sufficient_transitions=sum(r['sufficient_causal_comparison'] for r in transitions),
        causal_warning_signature=sum(r['causal_signature'] for r in transitions),
        causal_signature_followed_profit=sum(r['causal_signature_followed_profit'] for r in transitions),
        both_FP4_FP5_restored=sum(r['restored_FP4_FP5'] for r in valid))
