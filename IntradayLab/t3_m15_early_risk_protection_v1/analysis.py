"""Fixed comparisons of two full paths; entry identity never uses ordinal trade IDs."""
from collections import defaultdict
import math
import common as C
from primary_metrics import metrics

def key(t):return (t['instrument'],t.get('signal_time'),t['direction'])
def build(control,experiment,sources):
    tables={'summary':[],'monthly':[],'trade_comparison':[],'signal_comparison':[],'cohort32':[],'winner_retention':[],'effect_summary':[]}
    paths={'CONTROL':control,'EARLY_PROTECT_05':experiment}
    for variant,out in paths.items():
        for scope in ('ALL_FOUR',)+C.SYMBOLS:
            for direction in ('ALL','LONG','SHORT'):
                t=[r for r in out['trades'] if (scope=='ALL_FOUR' or r['instrument']==scope) and (direction=='ALL' or r['direction']==direction)]
                op=lambda r:(scope=='ALL_FOUR' or r['instrument']==scope) and (direction=='ALL' or r['direction']==direction)
                for year in ('2023','2024','ALL'):
                    cal=[m for m in C.CALENDAR if year=='ALL' or m.startswith(year)]
                    selected=[r for r in t if year=='ALL' or str(r['year'])==year]
                    opens=out['OPEN_POSITIONS'] if year=='ALL' else [r for r in out['PERIOD_END_OPEN_POSITIONS'] if r['month']==year+'-12']
                    m=metrics(selected,cal);nov=sum(r['gross_R'] for r in selected if r['exit_time'].strftime('%Y-%m')=='2024-11')
                    exnov=metrics([r for r in selected if r['exit_time'].strftime('%Y-%m')!='2024-11'],[m for m in cal if m!='2024-11'])
                    tables['summary'].append({'variant':variant,'scope':scope,'direction':direction,'year':year,**m,'period_end_OPEN':sum(op(r) for r in opens),'ex_nov2024_PF':exnov['gross_PF'],'ex_nov2024_R':exnov['gross_R'],'nov2024_R':nov,'nov2024_share_R':nov/m['gross_R'] if m['gross_R']>0 and year!='2023' else None})
                first=min(r['first_close'][:7] for r in sources if scope=='ALL_FOUR' or r['instrument']==scope)
                for month in C.CALENDAR:
                    tables['monthly'].append({'variant':variant,'scope':scope,'direction':direction,'month':month,'coverage':'NO_COVERAGE' if month<first else 'AVAILABLE_PARTIAL_START' if scope in ('GLDRUBF','IMOEXF') and month==first else 'AVAILABLE',**metrics([r for r in t if r['exit_time'].strftime('%Y-%m')==month],[month])})
    base={key(t):t for t in control['trades']+control['OPEN_POSITIONS']};exp={key(t):t for t in experiment['trades']+experiment['OPEN_POSITIONS']}
    assert len(base)==len(control['trades'])+len(control['OPEN_POSITIONS']);assert len(exp)==len(experiment['trades'])+len(experiment['OPEN_POSITIONS'])
    bclosed={key(t) for t in control['trades']};eclosed={key(t) for t in experiment['trades']}
    for k in sorted(base.keys()|exp.keys()):
        b=base.get(k);e=exp.get(k);bc=k in bclosed;ec=k in eclosed
        br=b['gross_R'] if bc else None;er=e['gross_R'] if ec else None;delta=er-br if br is not None and er is not None else None
        earlier=bool(bc and ec and e['exit_time']<b['exit_time'])
        r={'instrument':k[0],'signal_time':k[1],'direction':k[2],'control_trade_id':b['trade_id'] if b else None,'experiment_trade_id':e['trade_id'] if e else None,
           'control_status':'CLOSED' if bc else 'OPEN' if b else 'ABSENT','experiment_status':'CLOSED' if ec else 'OPEN' if e else 'ABSENT',
           'control_entry_time':b['entry_time'] if b else None,'experiment_entry_time':e['entry_time'] if e else None,
           'control_exit_time':b['exit_time'] if bc else None,'experiment_exit_time':e['exit_time'] if ec else None,
           'control_gross_R':br,'experiment_gross_R':er,'delta_R':delta,'exit_earlier':earlier,
           'loss_reduced':bool(br is not None and br<0 and delta is not None and delta>1e-8),
           'winner_damaged':bool(br is not None and br>0 and delta is not None and delta<-1e-8),
           'winner_premature':bool(br is not None and br>0 and earlier and delta is not None and delta<-1e-8),
           'winner_to_loss':bool(br is not None and br>0 and er is not None and er<0),
           'original_GE2':bool(br is not None and br>=2),'original_GE5':bool(br is not None and br>=5),
           'experiment_stop_source':e.get('stop_source_at_exit') if e else None,'early_activated':e.get('early_activated') if e else None,
           'early_activation_time':e.get('early_activation_time') if e else None,'early_stop_updates':e.get('early_stop_updates') if e else None}
        r['booked_delta_R']=(er or 0.)-(br or 0.)
        tables['trade_comparison'].append(r)
        if r['original_GE2']:tables['winner_retention'].append(r)
    owners={v:{(r['instrument'],r['trade_id']):r['signal_time'] for r in out['trades']+out['OPEN_POSITIONS']} for v,out in paths.items()}
    bm={(r['instrument'],r['signal_time']):r for r in control['entry_opportunities']};em={(r['instrument'],r['signal_time']):r for r in experiment['entry_opportunities']};assert bm.keys()==em.keys()
    for k,b in bm.items():
        e=em[k];bo=owners['CONTROL'].get((k[0],b.get('occupied_trade_id')));eo=owners['EARLY_PROTECT_05'].get((k[0],e.get('occupied_trade_id')))
        r={'instrument':k[0],'signal_time':k[1],'direction':b['direction'],'rule_pass':b['rule_pass'],
           'control_reason':b['decision_reason'],'experiment_reason':e['decision_reason'],'control_accepted':b['entry_accepted'],'experiment_accepted':e['entry_accepted'],
           'control_occupied':b['position_occupied'],'experiment_occupied':e['position_occupied'],'control_owner_signal':bo,'experiment_owner_signal':eo,
           'control_trade_id':b.get('trade_id'),'experiment_trade_id':e.get('trade_id'),'new_entry':not b['entry_accepted'] and e['entry_accepted'],'lost_entry':b['entry_accepted'] and not e['entry_accepted'],
           'occupancy_changed':b['position_occupied']!=e['position_occupied'] or bo!=eo,'decision_changed':b['decision_reason']!=e['decision_reason'] or b['entry_accepted']!=e['entry_accepted']}
        assert b['direction']==e['direction'] and b['rule_pass']==e['rule_pass'];tables['signal_comparison'].append(r)
    stops=defaultdict(list);estops=defaultdict(list)
    for r in control['stop_decisions']:stops[(r['instrument'],r['trade_id'])].append(r)
    for r in experiment['stop_decisions']:estops[(r['instrument'],r['trade_id'])].append(r)
    comparisons={key(r):r for r in tables['trade_comparison']}
    for b in control['trades']:
        if not (b['year']==2024 and b['direction']=='SHORT' and .5<=b['MFE_R']<1):continue
        ss=stops[(b['instrument'],b['trade_id'])];idx=next(i for i,r in enumerate(ss) if r['phase']=='SURVIVED' and r['favorable_R_after']>=.5)
        trigger=ss[idx];n=ss[idx+1] if idx+1<len(ss) else None;e=exp.get(key(b));es=estops[(e['instrument'],e['trade_id'])] if e else []
        er=next((r for r in es if r['early_activated_now']),None);tight=next((r for r in es if r['early_stop_changed']),None)
        en=next((r for r in es if tight and r['bar_close_time']>tight['bar_close_time']),None)
        tables['cohort32'].append(comparisons[key(b)]|{'control_MFE_R':b['MFE_R'],'control_trigger_close':trigger['bar_close_time'],'control_next_observed_open':n['bar_open_time'] if n else None,
            'control_causal_available':n is not None,'actual_trigger_close':er['bar_close_time'] if er else None,'actual_tightening_close':tight['bar_close_time'] if tight else None,
            'actual_protected_next_open':en['bar_open_time'] if en else None,'actual_causal_available':en is not None})
    assert len(tables['cohort32'])==32,'PR507_COHORT_MISMATCH'
    for scope in ('ALL_FOUR',)+C.SYMBOLS:
        for direction in ('ALL','LONG','SHORT'):
            for year in ('2023','2024','ALL'):
                comp=[r for r in tables['trade_comparison'] if r['control_status']=='CLOSED' and (scope=='ALL_FOUR' or r['instrument']==scope) and (direction=='ALL' or r['direction']==direction) and (year=='ALL' or str(r['control_exit_time'].year)==year)]
                sig=[r for r in tables['signal_comparison'] if (scope=='ALL_FOUR' or r['instrument']==scope) and (direction=='ALL' or r['direction']==direction) and (year=='ALL' or str(r['signal_time'].year)==year)]
                row={'scope':scope,'direction':direction,'year':year,'original_closed':len(comp),'matched_closed':sum(r['experiment_status']=='CLOSED' for r in comp),'original_not_entered':sum(r['experiment_status']=='ABSENT' for r in comp),'original_open_experiment':sum(r['experiment_status']=='OPEN' for r in comp),
                     'loss_reduced':sum(r['loss_reduced'] for r in comp),'loss_saving_R':math.fsum(r['delta_R'] for r in comp if r['loss_reduced']),
                     'winner_premature':sum(r['winner_premature'] for r in comp),'winner_damaged':sum(r['winner_damaged'] for r in comp),'winner_to_loss':sum(r['winner_to_loss'] for r in comp),
                     'winner_lost_R':math.fsum(-r['delta_R'] for r in comp if r['winner_damaged']),
                     'new_entries':sum(r['new_entry'] for r in sig),'lost_entries':sum(r['lost_entry'] for r in sig),'occupancy_changed':sum(r['occupancy_changed'] for r in sig),'decision_changed':sum(r['decision_changed'] for r in sig)}
                for n in (2,5):
                    w=[r for r in comp if r[f'original_GE{n}']];same=[r for r in w if r['experiment_status']=='CLOSED']
                    row.update({f'GE{n}_original':len(w),f'GE{n}_not_entered':sum(r['experiment_status']=='ABSENT' for r in w),f'GE{n}_damaged':sum(r['winner_damaged'] for r in w),f'GE{n}_premature':sum(r['winner_premature'] for r in w),f'GE{n}_to_loss':sum(r['winner_to_loss'] for r in w),f'GE{n}_still_above':sum(r['experiment_gross_R']>=n for r in same),f'GE{n}_control_R':math.fsum(r['control_gross_R'] for r in w),f'GE{n}_matched_experiment_R':math.fsum(r['experiment_gross_R'] for r in same),f'GE{n}_matched_loss_R':math.fsum(-r['delta_R'] for r in same if r['winner_damaged'])})
                tables['effect_summary'].append(row)
    return tables
