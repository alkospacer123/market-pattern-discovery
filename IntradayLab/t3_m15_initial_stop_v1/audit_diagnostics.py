"""Independent scalar audit of descriptive artifacts from independently replayed rows."""
import csv
import json
from datetime import datetime
from pathlib import Path


def read(path):
    with path.open() as f:return list(csv.DictReader(f))


def quantile(values,q):
    if not values:return None
    values=sorted(values);index=(len(values)-1)*q;left=int(index);right=min(left+1,len(values)-1)
    return values[left]+(values[right]-values[left])*(index-left)


def audit_diagnostics(trades,entries,opened,output,check,summary,calendar):
    count=0
    def verify(values,row,label):
        nonlocal count
        for k,v in values.items():check(v,row[k],label+'.'+k);count+=1
    def selected(rows,r):
        return [a for a in rows if a['version']==r['version'] and a['rule']==r['rule'] and
            ('instrument' not in r or a['instrument']==r['instrument']) and
            ('scope' not in r or r['scope']=='ALL_FOUR' or a['instrument']==r['scope'])]
    for r in read(output/'risk_distribution.csv'):
        f=[e for e in selected(entries,r) if e['entry_accepted'] and
            (r['entry_year']=='ALL' or e['signal_time'].year==int(r['entry_year'])) and
            (r['direction']=='ALL' or e['direction']==r['direction'])]
        x=[a['candidate_risk_exchange_ticks'] for a in f]
        values={'accepted_entries_including_terminal_open':len(f),'risk_le_1_tick':sum(a<=1+1e-9 for a in x),
            'risk_le_2_ticks':sum(a<=2+1e-9 for a in x),'risk_le_5_ticks':sum(a<=5+1e-9 for a in x),
            'risk_le_2_ticks_share':sum(a<=2+1e-9 for a in x)/len(x) if x else None}
        for unit,xs in [('price',[a['candidate_initial_risk'] for a in f]),
            ('ATR',[a['candidate_initial_risk']/a['ATR'] for a in f]),('exchange_ticks',x)]:
            for q,label in [(0,'min'),(.01,'p01'),(.05,'p05'),(.25,'p25'),(.5,'median'),(.75,'p75'),(.95,'p95'),(.99,'p99'),(1,'max')]:values[f'risk_{unit}_{label}']=quantile(xs,q)
            values[f'risk_{unit}_mean']=sum(xs)/len(xs) if xs else None
        verify(values,r,'risk')
    for r in read(output/'entry_validity.csv'):
        f=selected(entries,r)
        verify({'signal_opportunities':len(f),'accepted':sum(a['entry_accepted'] for a in f),'busy':sum(a['position_occupied'] for a in f),
            'invalid_candidate_count':sum(not a['initial_stop_valid'] for a in f),
            'invalid_unoccupied_skipped':sum(not a['initial_stop_valid'] and not a['position_occupied'] for a in f),
            'nonpositive_risk':sum(a['validity_reason']=='NONPOSITIVE_INITIAL_RISK' for a in f),
            'nonfinite_risk':sum(a['validity_reason']=='NONFINITE_INITIAL_RISK' for a in f),'fallbacks':0},r,'validity')
    for r in read(output/'november_dependence.csv'):
        f=selected(trades,r)
        if r['year']!='ALL':f=[a for a in f if a['exit_time'].year==int(r['year'])]
        col='gross_R' if r['normalization']=='ACTUAL_INITIAL_RISK' else 'reference_2ATR_R'
        n=[a for a in f if a['exit_time'].strftime('%Y-%m')=='2024-11'];rest=[a for a in f if a not in n]
        cal=calendar if r['year']=='ALL' else [m for m in calendar if m.startswith(r['year'])]
        full=summary(f,cal,col,0);removed=summary(rest,[m for m in cal if m!='2024-11'],col,0)
        verify({'november_closed':len(n),'november_R':sum(a[col] for a in n),'full_R':full['gross_R'],'full_PF':full['gross_PF'],
            'ex_november_R':removed['gross_R'],'ex_november_PF':removed['gross_PF'],'ex_november_drawdown_R':removed['max_drawdown_closed_R']},r,'november')
    key=lambda a:(a['instrument'],a['direction'],a.get('entry_time',a.get('signal_time')))
    lineage={}
    for r in read(output/'trade_lineage.csv'):
        original=next(a for a in trades if a['version']==r['version'] and a['rule']=='CONTROL' and a['instrument']==r['instrument'] and a['trade_id']==r['control_trade_id'])
        attempt=next(a for a in entries if a['version']==r['version'] and a['rule']==r['rule'] and key(a)==key(original))
        a=next((a for a in trades if a['version']==r['version'] and a['rule']==r['rule'] and key(a)==key(original)),None)
        op=next((a for a in opened if a['version']==r['version'] and a['rule']==r['rule'] and key(a)==key(original)),None)
        status='CLOSED_MATCH' if a else 'OPEN_TERMINAL' if op else attempt['outcome']
        values={'entry_time':original['entry_time'],'control_exit_time':original['exit_time'],
            'control_gross_R':original['gross_R'],'control_price_pnl':original['gross_price_pnl'],
            'control_winner_ge_2R':original['gross_R']>=2,'variant_status':status,
            'variant_trade_id':a['trade_id'] if a else op['trade_id'] if op else None,'occupied_trade_id':attempt['occupied_trade_id'],
            'variant_gross_R':a['gross_R'] if a else None,'variant_reference_2ATR_R':a['reference_2ATR_R'] if a else None,
            'variant_price_pnl':a['gross_price_pnl'] if a else None,'variant_exit_time':a['exit_time'] if a else None,
            'same_exit_price_and_time':bool(a and a['exit_price']==original['exit_price'] and a['exit_time']==original['exit_time']),
            'price_pnl_preserved':bool(a and a['gross_price_pnl']>=original['gross_price_pnl']-1e-8),
            'reference_2ATR_R_preserved':bool(a and a['reference_2ATR_R']>=original['gross_R']-1e-8),
            'actual_R_preserved':bool(a and a['gross_R']>=original['gross_R']-1e-8)}
        verify(values,r,'lineage')
        lineage[(r['version'],r['rule'],r['instrument'],r['control_trade_id'])]=values | {'instrument':r['instrument'],'direction':r['direction']}
    for r in read(output/'winner_occupancy_changes.csv'):
        f=[a for k,a in lineage.items() if k[0]==r['version'] and k[1]==r['rule'] and
            (r['scope']=='ALL_FOUR' or a['instrument']==r['scope']) and
            (r['control_exit_year']=='ALL' or a['control_exit_time'].year==int(r['control_exit_year']))]
        winners=[a for a in f if a['control_winner_ge_2R']]
        controls={key(a) for a in trades+opened if a['version']==r['version'] and a['rule']=='CONTROL'}
        new=[a for a in selected(trades,r) if key(a) not in controls and
            (r['control_exit_year']=='ALL' or a['exit_time'].year==int(r['control_exit_year']))]
        verify({'control_closed':len(f),'missed_busy_entries':sum(a['variant_status']=='POSITION_OCCUPIED' for a in f),
            'missed_invalid_entries':sum(a['variant_status'].endswith('INITIAL_RISK') for a in f),
            'control_large_winners_ge_2R':len(winners),'large_winner_entry_busy':sum(a['variant_status']=='POSITION_OCCUPIED' for a in winners),
            'large_winner_entry_invalid':sum(a['variant_status'].endswith('INITIAL_RISK') for a in winners),
            'large_winner_terminal_open':sum(a['variant_status']=='OPEN_TERMINAL' for a in winners),
            'large_winner_price_pnl_preserved':sum(a['price_pnl_preserved'] for a in winners),
            'large_winner_reference_R_preserved':sum(a['reference_2ATR_R_preserved'] for a in winners),
            'large_winner_actual_R_preserved':sum(a['actual_R_preserved'] for a in winners),
            'large_winners_turned_losses':sum(a['variant_gross_R'] is not None and a['variant_gross_R']<0 for a in winners),
            'all_control_winners_turned_losses':sum(a['control_gross_R']>0 and a['variant_gross_R'] is not None and a['variant_gross_R']<0 for a in f),
            'new_closed_entries':len(new),'new_closed_losses':sum(a['gross_R']<0 for a in new),
            'new_entry_actual_R':sum(a['gross_R'] for a in new),'new_entry_reference_2ATR_R':sum(a['reference_2ATR_R'] for a in new)},r,'changes')
    for file,predicate,rows in [('narrow_stop_entries.csv',lambda a:a['entry_accepted'] and a['candidate_risk_exchange_ticks']<=2+1e-9,entries),
        ('gap_losses_gt_1R.csv',lambda a:a['gap_exit'] and a['gross_R']<-1-1e-9,trades),
        ('invalid_stop_opportunities.csv',lambda a:not a['initial_stop_valid'],entries),
        ('new_entries.csv',lambda a:a['rule']!='CONTROL' and key(a) not in {key(c) for c in trades+opened if c['version']==a['version'] and c['rule']=='CONTROL'},trades)]:
        expected=[a for a in rows if predicate(a)];saved=read(output/file)
        ident=lambda a:(a['version'],a['rule'],a['instrument'],a.get('trade_id') or '',str(a.get('signal_time',a.get('entry_time'))))
        expected.sort(key=ident);saved.sort(key=lambda a:(a['version'],a['rule'],a['instrument'],a.get('trade_id') or '',str(datetime.fromisoformat(a.get('signal_time',a.get('entry_time'))))))
        assert len(expected)==len(saved),(file,len(expected),len(saved))
        for a,b in zip(expected,saved):verify(a,b,file)
    for r in json.loads((output/'OBJECTIVE_ASSESSMENT.json').read_text())['rows']:
        f=selected(trades,r)
        actual=summary(f,calendar,'gross_R',0)['gross_PF'];reference=summary(f,calendar,'reference_2ATR_R',0)['gross_PF']
        verify({'gross_PF_actual':actual,'gross_PF_reference_2ATR':reference,
            'numerical_goal_actual_PF_ge_2':actual>=2,'reference_PF_ge_2':reference>=2,
            'accepted_risks_le_2_ticks':sum(a['entry_accepted'] and a['candidate_risk_exchange_ticks']<=2+1e-9 for a in selected(entries,r)),
            'economic_advantage_proven':False,'selection':'NONE'},r,'objective')
    # Reconstruct portfolio closed equity in the saved row order, separately for each R basis.
    states={}
    lookup={(a['version'],a['rule'],a['instrument'],a['trade_id']):a for a in trades}
    for r in read(output/'closed_equity.csv'):
        a=lookup[(r['version'],r['rule'],r['instrument'],r['trade_id'])]
        norm=(r['version'],r['rule'],r['normalization']);total,peak=states.get(norm,(0.,0.))
        x=a['gross_R'] if r['normalization']=='ACTUAL_INITIAL_RISK' else a['reference_2ATR_R']
        total+=x;peak=max(peak,total);states[norm]=(total,peak)
        verify({'trade_R':x,'cumulative_closed_R':total,'drawdown_R':peak-total},r,'equity')
    return count
