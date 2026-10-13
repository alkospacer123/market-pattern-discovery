"""Independent dictionary joins and scalar aggregates; no primary analytics imports."""
import math
import common as C
from scalar_metrics import stats

def calculate(baseline,new,sources):
    out={n:[] for n in ('summary','monthly','trade_comparison','signal_comparison','cohort32','winner_retention','effect_summary')}
    for label,path in [('CONTROL',baseline),('EARLY_PROTECT_05',new)]:
        for scope in ['ALL_FOUR',*C.SYMBOLS]:
            for side in ['ALL','LONG','SHORT']:
                def select(r):return (scope=='ALL_FOUR' or scope==r['instrument']) and (side=='ALL' or side==r['direction'])
                rows=list(filter(select,path['trades']))
                for year in ['2023','2024','ALL']:
                    cal=C.CALENDAR[:] if year=='ALL' else [m for m in C.CALENDAR if m[:4]==year]
                    picked=[r for r in rows if r['exit_time'].strftime('%Y-%m') in cal];m=stats(picked,cal)
                    opens=path['OPEN_POSITIONS'] if year=='ALL' else [r for r in path['PERIOD_END_OPEN_POSITIONS'] if r['month']==year+'-12']
                    nov=math.fsum(r['gross_R'] for r in picked if r['exit_time'].strftime('%Y-%m')=='2024-11')
                    exnov=stats([r for r in picked if r['exit_time'].strftime('%Y-%m')!='2024-11'],[m for m in cal if m!='2024-11'])
                    out['summary'].append(dict(variant=label,scope=scope,direction=side,year=year,**m,period_end_OPEN=sum(select(r) for r in opens),ex_nov2024_PF=exnov['gross_PF'],ex_nov2024_R=exnov['gross_R'],nov2024_R=nov,nov2024_share_R=nov/m['gross_R'] if m['gross_R']>0 and year!='2023' else None))
                first=sorted(s['first_close'][:7] for s in sources if scope=='ALL_FOUR' or s['instrument']==scope)[0]
                for month in C.CALENDAR:
                    coverage='AVAILABLE'
                    if month<first:coverage='NO_COVERAGE'
                    elif month==first and scope in ['GLDRUBF','IMOEXF']:coverage='AVAILABLE_PARTIAL_START'
                    out['monthly'].append(dict(variant=label,scope=scope,direction=side,month=month,coverage=coverage,**stats([r for r in rows if r['exit_time'].strftime('%Y-%m')==month],[month])))
    def identity(t):return t['instrument'],t['signal_time'],t['direction']
    paths=[];status=[];ownership=[];stop_paths=[]
    for path in [baseline,new]:
        idx={};st={};owner={};logs={}
        for state,records in [('CLOSED',path['trades']),('OPEN',path['OPEN_POSITIONS'])]:
            for r in records:
                k=identity(r);assert k not in idx;idx[k]=r;st[k]=state;owner[r['instrument'],r['trade_id']]=r['signal_time']
        for row in path['stop_decisions']:logs.setdefault((row['instrument'],row['trade_id']),[]).append(row)
        paths.append(idx);status.append(st);ownership.append(owner);stop_paths.append(logs)
    for k in sorted(set(paths[0])|set(paths[1])):
        c=paths[0].get(k,{});x=paths[1].get(k,{});cs=status[0].get(k,'ABSENT');xs=status[1].get(k,'ABSENT')
        cr=c.get('gross_R');xr=x.get('gross_R');delta=xr-cr if cr is not None and xr is not None else None
        earlier=cs==xs=='CLOSED' and x['exit_time']<c['exit_time'];damaged=cr is not None and cr>0 and delta is not None and delta<-1e-8
        r=dict(instrument=k[0],signal_time=k[1],direction=k[2],control_trade_id=c.get('trade_id'),experiment_trade_id=x.get('trade_id'),control_status=cs,experiment_status=xs,
          control_entry_time=c.get('entry_time'),experiment_entry_time=x.get('entry_time'),control_exit_time=c.get('exit_time'),experiment_exit_time=x.get('exit_time'),control_gross_R=cr,experiment_gross_R=xr,delta_R=delta,
          exit_earlier=earlier,loss_reduced=cr is not None and cr<0 and delta is not None and delta>1e-8,winner_damaged=damaged,winner_premature=damaged and earlier,
          winner_to_loss=cr is not None and cr>0 and xr is not None and xr<0,original_GE2=cr is not None and cr>=2,original_GE5=cr is not None and cr>=5,
          experiment_stop_source=x.get('stop_source_at_exit'),early_activated=x.get('early_activated'),early_activation_time=x.get('early_activation_time'),early_stop_updates=x.get('early_stop_updates'))
        r['booked_delta_R']=(xr or 0.)-(cr or 0.)
        out['trade_comparison'].append(r)
        if r['original_GE2']:out['winner_retention'].append(dict(r))
    first={(r['instrument'],r['signal_time']):r for r in baseline['entry_opportunities']};second={(r['instrument'],r['signal_time']):r for r in new['entry_opportunities']}
    assert set(first)==set(second)
    for k in first:
        a=first[k];b=second[k];assert a['direction']==b['direction'] and a['rule_pass']==b['rule_pass']
        co=ownership[0].get((k[0],a.get('occupied_trade_id')));xo=ownership[1].get((k[0],b.get('occupied_trade_id')))
        out['signal_comparison'].append(dict(instrument=k[0],signal_time=k[1],direction=a['direction'],rule_pass=a['rule_pass'],control_reason=a['decision_reason'],experiment_reason=b['decision_reason'],
            control_accepted=a['entry_accepted'],experiment_accepted=b['entry_accepted'],control_occupied=a['position_occupied'],experiment_occupied=b['position_occupied'],control_owner_signal=co,experiment_owner_signal=xo,
            control_trade_id=a.get('trade_id'),experiment_trade_id=b.get('trade_id'),new_entry=b['entry_accepted'] and not a['entry_accepted'],lost_entry=a['entry_accepted'] and not b['entry_accepted'],
            occupancy_changed=co!=xo or a['position_occupied']!=b['position_occupied'],decision_changed=a['decision_reason']!=b['decision_reason'] or a['entry_accepted']!=b['entry_accepted']))
    compared={identity(r):r for r in out['trade_comparison']}
    for c in baseline['trades']:
        if c['exit_time'].year!=2024 or c['direction']!='SHORT' or not (.5<=c['MFE_R']<1):continue
        seq=stop_paths[0][c['instrument'],c['trade_id']];trigger=None;nxt=None
        for i,r in enumerate(seq):
            if r['phase']=='SURVIVED' and r['favorable_R_after']>=.5:trigger=r;nxt=seq[i+1] if i+1<len(seq) else None;break
        assert trigger is not None
        x=paths[1].get(identity(c));actual_trigger=None;tight=None;available=None
        if x:
            for r in stop_paths[1].get((x['instrument'],x['trade_id']),[]):
                if available is None and tight is not None and r['bar_close_time']>tight['bar_close_time']:available=r
                if r['early_activated_now'] and actual_trigger is None:actual_trigger=r
                if r['early_stop_changed'] and tight is None:tight=r
        out['cohort32'].append(dict(compared[identity(c)],control_MFE_R=c['MFE_R'],control_trigger_close=trigger['bar_close_time'],control_next_observed_open=nxt['bar_open_time'] if nxt else None,
            control_causal_available=nxt is not None,actual_trigger_close=actual_trigger['bar_close_time'] if actual_trigger else None,actual_tightening_close=tight['bar_close_time'] if tight else None,
            actual_protected_next_open=available['bar_open_time'] if available else None,actual_causal_available=available is not None))
    assert len(out['cohort32'])==32
    for scope in ['ALL_FOUR',*C.SYMBOLS]:
        for side in ['ALL','LONG','SHORT']:
            for year in ['2023','2024','ALL']:
                def include(r,at):return (scope=='ALL_FOUR' or scope==r['instrument']) and (side=='ALL' or side==r['direction']) and (year=='ALL' or str(r[at].year)==year)
                c=[r for r in out['trade_comparison'] if r['control_status']=='CLOSED' and include(r,'control_exit_time')];s=[r for r in out['signal_comparison'] if include(r,'signal_time')]
                count=lambda name:sum(r[name] for r in c)
                r=dict(scope=scope,direction=side,year=year,original_closed=len(c),matched_closed=sum(x['experiment_status']=='CLOSED' for x in c),original_not_entered=sum(x['experiment_status']=='ABSENT' for x in c),original_open_experiment=sum(x['experiment_status']=='OPEN' for x in c),
                    loss_reduced=count('loss_reduced'),loss_saving_R=math.fsum(x['delta_R'] for x in c if x['loss_reduced']),winner_premature=count('winner_premature'),winner_damaged=count('winner_damaged'),winner_to_loss=count('winner_to_loss'),
                    winner_lost_R=math.fsum(-x['delta_R'] for x in c if x['winner_damaged']),new_entries=sum(x['new_entry'] for x in s),lost_entries=sum(x['lost_entry'] for x in s),occupancy_changed=sum(x['occupancy_changed'] for x in s),decision_changed=sum(x['decision_changed'] for x in s))
                for threshold in [2,5]:
                    w=[x for x in c if x['control_gross_R']>=threshold];m=[x for x in w if x['experiment_status']=='CLOSED'];prefix='GE'+str(threshold)+'_'
                    terms={'original':len(w),'not_entered':sum(x['experiment_status']=='ABSENT' for x in w),'damaged':sum(x['winner_damaged'] for x in w),'premature':sum(x['winner_premature'] for x in w),'to_loss':sum(x['winner_to_loss'] for x in w),'still_above':sum(x['experiment_gross_R']>=threshold for x in m),'control_R':math.fsum(x['control_gross_R'] for x in w),'matched_experiment_R':math.fsum(x['experiment_gross_R'] for x in m),'matched_loss_R':math.fsum(-x['delta_R'] for x in m if x['winner_damaged'])}
                    r.update({prefix+name:value for name,value in terms.items()})
                out['effect_summary'].append(r)
    return out
