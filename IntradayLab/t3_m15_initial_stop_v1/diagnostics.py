"""Descriptive risks and occupancy/winner lineage; never feeds decisions."""
import numpy as np
import pandas as pd
from engine import E,RULES
from research import csv,js,LABELS


def diagnostics(trades,opened,entries,output):
    risks,validity,lineage,changes = [],[],[],[]
    for v in E.CONFIGS:
        original = trades.loc[trades.version.eq(v)&trades.rule.eq('CONTROL')]
        key = lambda r:(r['instrument'],r['direction'],pd.Timestamp(r.get('entry_time',r.get('signal_time'))))
        original_keys = {key(r) for r in original.to_dict('records')}
        original_keys.update(key(r) for r in opened if r['version']==v and r['rule']=='CONTROL')
        for rule in RULES:
            e = entries.loc[entries.version.eq(v)&entries.rule.eq(rule)]
            t = trades.loc[trades.version.eq(v)&trades.rule.eq(rule)]
            accepted = e.loc[e.entry_accepted]
            for s in E.SYMBOLS:
                es = e.loc[e.instrument.eq(s)]
                validity.append({'version':v,'rule':rule,'instrument':s,'signal_opportunities':len(es),
                    'accepted':int(es.entry_accepted.sum()),'busy':int(es.position_occupied.sum()),
                    'invalid_candidate_count':int((~es.initial_stop_valid).sum()),
                    'invalid_unoccupied_skipped':int(((~es.initial_stop_valid)&(~es.position_occupied)).sum()),
                    'nonpositive_risk':int(es.validity_reason.eq('NONPOSITIVE_INITIAL_RISK').sum()),
                    'nonfinite_risk':int(es.validity_reason.eq('NONFINITE_INITIAL_RISK').sum()),'fallbacks':0})
                for year in ('ALL',2023,2024):
                    for direction in ('ALL','LONG','SHORT'):
                        f = accepted.loc[accepted.instrument.eq(s)]
                        if year!='ALL':f=f.loc[f.signal_time.dt.year.eq(year)]
                        if direction!='ALL':f=f.loc[f.direction.eq(direction)]
                        ids={'version':v,'rule':rule,'instrument':s,'entry_year':year,'direction':direction,'accepted_entries_including_terminal_open':len(f)}
                        x=f.candidate_risk_exchange_ticks
                        row=ids | {'risk_le_1_tick':int((x<=1+1e-9).sum()),'risk_le_2_ticks':int((x<=2+1e-9).sum()),
                            'risk_le_5_ticks':int((x<=5+1e-9).sum()),'risk_le_2_ticks_share':float((x<=2+1e-9).mean()) if len(f) else None}
                        for name,values in [('price',f.candidate_initial_risk),('ATR',f.candidate_initial_risk/f.ATR),('exchange_ticks',x)]:
                            for q,label in [(0,'min'),(.01,'p01'),(.05,'p05'),(.25,'p25'),(.5,'median'),(.75,'p75'),(.95,'p95'),(.99,'p99'),(1,'max')]:
                                row[f'risk_{name}_{label}']=float(values.quantile(q)) if len(f) else None
                            row[f'risk_{name}_mean']=float(values.mean()) if len(f) else None
                        risks.append(row)
            if rule=='CONTROL':continue
            lookup={key(r):r for r in t.to_dict('records')}
            op={key(r):r for r in opened if r['version']==v and r['rule']==rule}
            ep={key(r):r for r in e.to_dict('records')}
            local=[]
            for r in original.to_dict('records'):
                a=lookup.get(key(r));o=op.get(key(r));attempt=ep[key(r)]
                status='CLOSED_MATCH' if a else 'OPEN_TERMINAL' if o else attempt['outcome']
                local.append({'version':v,'rule':rule,'instrument':r['instrument'],'direction':r['direction'],
                    'control_trade_id':r['trade_id'],'entry_time':r['entry_time'],'control_exit_time':r['exit_time'],
                    'control_gross_R':r['gross_R'],'control_price_pnl':r['gross_price_pnl'],
                    'control_winner_ge_2R':r['gross_R']>=2,'variant_status':status,
                    'variant_trade_id':a['trade_id'] if a else o['trade_id'] if o else None,
                    'occupied_trade_id':attempt['occupied_trade_id'],
                    'variant_gross_R':a['gross_R'] if a else None,'variant_reference_2ATR_R':a['reference_2ATR_R'] if a else None,
                    'variant_price_pnl':a['gross_price_pnl'] if a else None,'variant_exit_time':a['exit_time'] if a else None,
                    'same_exit_price_and_time':bool(a and a['exit_price']==r['exit_price'] and a['exit_time']==r['exit_time']),
                    'price_pnl_preserved':bool(a and a['gross_price_pnl']>=r['gross_price_pnl']-1e-8),
                    'reference_2ATR_R_preserved':bool(a and a['reference_2ATR_R']>=r['gross_R']-1e-8),
                    'actual_R_preserved':bool(a and a['gross_R']>=r['gross_R']-1e-8)})
            lineage.extend(local)
            for scope in ('ALL_FOUR',*E.SYMBOLS):
                for year in ('ALL',2023,2024):
                    selected=[r for r in local if (scope=='ALL_FOUR' or r['instrument']==scope) and (year=='ALL' or r['control_exit_time'].year==year)]
                    winners=[r for r in selected if r['control_winner_ge_2R']]
                    new=[r for r in t.to_dict('records') if key(r) not in original_keys and (scope=='ALL_FOUR' or r['instrument']==scope) and (year=='ALL' or r['exit_time'].year==year)]
                    changes.append({'version':v,'rule':rule,'scope':scope,'control_exit_year':year,
                        'control_closed':len(selected),'missed_busy_entries':sum(r['variant_status']=='POSITION_OCCUPIED' for r in selected),
                        'missed_invalid_entries':sum(r['variant_status'] in ('NONFINITE_INITIAL_RISK','NONPOSITIVE_INITIAL_RISK') for r in selected),
                        'control_large_winners_ge_2R':len(winners),
                        'large_winner_entry_busy':sum(r['variant_status']=='POSITION_OCCUPIED' for r in winners),
                        'large_winner_entry_invalid':sum(r['variant_status'] in ('NONFINITE_INITIAL_RISK','NONPOSITIVE_INITIAL_RISK') for r in winners),
                        'large_winner_terminal_open':sum(r['variant_status']=='OPEN_TERMINAL' for r in winners),
                        'large_winner_price_pnl_preserved':sum(r['price_pnl_preserved'] for r in winners),
                        'large_winner_reference_R_preserved':sum(r['reference_2ATR_R_preserved'] for r in winners),
                        'large_winner_actual_R_preserved':sum(r['actual_R_preserved'] for r in winners),
                        'large_winners_turned_losses':sum(r['variant_gross_R'] is not None and r['variant_gross_R']<0 for r in winners),
                        'all_control_winners_turned_losses':sum(r['control_gross_R']>0 and r['variant_gross_R'] is not None and r['variant_gross_R']<0 for r in selected),
                        'new_closed_entries':len(new),'new_closed_losses':sum(r['gross_R']<0 for r in new),
                        'new_entry_actual_R':sum(r['gross_R'] for r in new),'new_entry_reference_2ATR_R':sum(r['reference_2ATR_R'] for r in new)})
    csv(output/'risk_distribution.csv',risks)
    csv(output/'entry_validity.csv',validity)
    csv(output/'trade_lineage.csv',lineage)
    csv(output/'winner_occupancy_changes.csv',changes)
    csv(output/'narrow_stop_entries.csv',entries.loc[entries.entry_accepted & entries.candidate_risk_exchange_ticks.le(2+1e-9)])
    csv(output/'gap_losses_gt_1R.csv',trades.loc[trades.gap_exit & trades.gross_R.lt(-1-1e-9)])
    csv(output/'invalid_stop_opportunities.csv',entries.loc[~entries.initial_stop_valid])
    csv(output/'new_entries.csv',pd.concat([trades.loc[trades.version.eq(v)&trades.rule.ne('CONTROL')].loc[
        lambda f:~f.apply(lambda r:(r.instrument,r.direction,r.entry_time) in {
            (a.instrument,a.direction,a.entry_time) for a in trades.loc[trades.version.eq(v)&trades.rule.eq('CONTROL')].itertuples()} |
            {(a['instrument'],a['direction'],pd.Timestamp(a['entry_time'])) for a in opened if a['version']==v and a['rule']=='CONTROL'},axis=1)] for v in E.CONFIGS]))
    overall=pd.read_csv(output/'overall_report.csv')
    assessment=[]
    for v in E.CONFIGS:
        for rule in RULES:
            f=overall.loc[overall.version.eq(v)&overall.rule.eq(rule)&overall.scope.eq('ALL_FOUR')]
            actual=f.loc[f.normalization.eq('ACTUAL_INITIAL_RISK')].iloc[0]
            reference=f.loc[f.normalization.eq('REFERENCE_2ATR')].iloc[0]
            a=entries.loc[entries.version.eq(v)&entries.rule.eq(rule)&entries.entry_accepted]
            assessment.append({'version':v,'rule':rule,'gross_PF_actual':float(actual.gross_PF),
                'gross_PF_reference_2ATR':float(reference.gross_PF),'numerical_goal_actual_PF_ge_2':bool(actual.gross_PF>=2),
                'reference_PF_ge_2':bool(reference.gross_PF>=2),'accepted_risks_le_2_ticks':int(a.candidate_risk_exchange_ticks.le(2+1e-9).sum()),
                'economic_advantage_proven':False,'selection':'NONE','labels':LABELS})
    js(output/'OBJECTIVE_ASSESSMENT.json',{'goal':'Pooled four-instrument full 2023-2024 Gross PF >=2.0; diagnostic, no automatic PASS',
        'development_exposed_years':[2023,2024],'rows':assessment,'external_audit':'PENDING'})
