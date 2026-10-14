"""Fixed post-replay comparisons. Outcomes never feed entry/Stop decisions."""
import json
from pathlib import Path
import pandas as pd
from engine import E, HERE

PAIRS=(('C1','CONTROL'),('C1','A6'),('C1','S1'),('C2','CONTROL'),('C2','A7'),('C2','S1'))
FIELDS=('gross_PF','gross_R','closed_trades','gross_expectancy_R','max_drawdown_R','positive_months','worst_month_R','top5_share_positive_R','top10_share_positive_R')


def csv(path,rows):
    pd.DataFrame(rows).to_csv(path,index=False,float_format='%.15g',lineterminator='\n')


def diagnostics(trades,opened,frames,decisions,opportunities,output):
    # ALL and separate exit years, with strictly observed-bar occupancy.
    frequency=[]
    for v in E.CONFIGS:
        for r in ('CONTROL','A6','A7','S1','C1','C2'):
            for scope in ('ALL_FOUR',*E.SYMBOLS):
                symbols=E.SYMBOLS if scope=='ALL_FOUR' else (scope,)
                for year in ('ALL',2023,2024):
                    e=opportunities.loc[opportunities.version.eq(v)&opportunities.rule.eq(r)&opportunities.instrument.isin(symbols)]
                    d=decisions.loc[decisions.version.eq(v)&decisions.rule.eq(r)&decisions.instrument.isin(symbols)]
                    f=trades.loc[trades.version.eq(v)&trades.rule.eq(r)&trades.instrument.isin(symbols)]
                    available=eligible=0
                    for s in symbols:
                        index=frames[s].index
                        available+=len(index) if year=='ALL' else sum(index.year==year)
                        eligible+=len(index[1:]) if year=='ALL' else sum(index[1:].year==year)
                    if year!='ALL':
                        e=e.loc[e.signal_time.dt.year.eq(year)];d=d.loc[d.bar_close_time.dt.year.eq(year)];f=f.loc[f.exit_time.dt.year.eq(year)]
                    occupied=int(e.position_occupied.sum());pass_filter=int(e.rule_pass.sum());accepted=int(e.entry_accepted.sum())
                    frequency.append({'version':v,'rule':r,'scope':scope,'year':year,'observed_bars':available,
                        'eligible_position_bars':eligible,'occupied_position_bars':len(d),'observed_bar_occupancy':len(d)/eligible if eligible else None,
                        'raw_signal_opportunities':len(e),'filter_pass':pass_filter,'filter_failed':len(e)-pass_filter,
                        'occupied_at_signal_close':occupied,'filter_pass_but_occupied':int((e.rule_pass&e.position_occupied).sum()),
                        'accepted_entries':accepted,'accepted_entries_per_1000_observed_bars':1000*accepted/available if available else None,
                        'closed_trades':len(f),'mean_closed_bars_held':float(f.bars_held.mean()) if len(f) else None,
                        'mean_closed_holding_minutes':float(f.holding_minutes.mean()) if len(f) else None})
    csv(output/'frequency_occupancy.csv',frequency)
    # Deltas in every central report; different calendars retain their original definition.
    comparisons=[]
    for name,period_keys in [('overall_report.csv',[]),('yearly_report.csv',['year']),('monthly_report.csv',['month']),('direction_report.csv',['year','direction']),('monthly_direction_report.csv',['month','direction'])]:
        f=pd.read_csv(output/name)
        keys=['version','scope',*period_keys]
        for variant,reference in PAIRS:
            a=f.loc[f.rule.eq(variant)];b=f.loc[f.rule.eq(reference)]
            paired=a.merge(b,on=keys,suffixes=('_variant','_reference'),validate='one_to_one')
            for t in paired.to_dict('records'):
                ids={k:t[k] for k in keys}
                for field in FIELDS:
                    va,ref=t[field+'_variant'],t[field+'_reference']
                    comparisons.append({'report':name,'variant':variant,'reference':reference,**ids,'metric':field,
                        'variant_value':va,'reference_value':ref,'delta':va-ref if pd.notna(va) and pd.notna(ref) else None})
    csv(output/'component_comparisons.csv',comparisons)
    freq=pd.DataFrame(frequency);freq_comparison=[]
    for v in E.CONFIGS:
        for variant,reference in PAIRS:
            for scope in ('ALL_FOUR',*E.SYMBOLS):
                for year in ('ALL',2023,2024):
                    lookup=lambda r:freq.loc[freq.version.eq(v)&freq.rule.eq(r)&freq.scope.eq(scope)&freq.year.eq(year)].iloc[0]
                    a,b=lookup(variant),lookup(reference)
                    row={'version':v,'variant':variant,'reference':reference,'scope':scope,'year':year}
                    for field in ('accepted_entries','closed_trades','occupied_position_bars','observed_bar_occupancy','accepted_entries_per_1000_observed_bars','mean_closed_bars_held','mean_closed_holding_minutes'):
                        row['variant_'+field]=a[field];row['reference_'+field]=b[field];row['delta_'+field]=a[field]-b[field] if pd.notna(a[field]) and pd.notna(b[field]) else None
                    freq_comparison.append(row)
    csv(output/'frequency_comparison.csv',freq_comparison)
    # Winner cohorts measured against CONTROL and each standalone component.
    lineage=[];cohorts=[]
    key=lambda t:(t['instrument'],t['direction'],pd.Timestamp(t['entry_time']))
    for v in E.CONFIGS:
        for variant,reference in PAIRS:
            old=trades.loc[trades.version.eq(v)&trades.rule.eq(reference)].to_dict('records')
            new=trades.loc[trades.version.eq(v)&trades.rule.eq(variant)].to_dict('records')
            lookup={key(t):t for t in new};opens={key(t):t for t in opened if t['version']==v and t['rule']==variant}
            local=[]
            for t in old:
                n=lookup.get(key(t));op=opens.get(key(t))
                status='CLOSED_MATCH' if n else 'OPEN_TERMINAL' if op else 'NO_MATCHING_ENTRY'
                r={'version':v,'variant':variant,'reference':reference,'instrument':t['instrument'],'direction':t['direction'],
                    'reference_trade_id':t['trade_id'],'reference_entry_time':t['entry_time'],'reference_exit_time':t['exit_time'],
                    'reference_exit_year':t['exit_time'].year,'reference_gross_R':t['gross_R'],'reference_is_ge2R':t['gross_R']>=2,
                    'match_status':status,'variant_trade_id':n['trade_id'] if n else op['trade_id'] if op else None,
                    'variant_gross_R':n['gross_R'] if n else None,'variant_exit_time':n['exit_time'] if n else None}
                local.append(r);lineage.append(r)
            for scope in ('ALL_FOUR',*E.SYMBOLS):
                for year in ('ALL',2023,2024):
                    sel=[t for t in local if t['reference_is_ge2R'] and (scope=='ALL_FOUR' or t['instrument']==scope) and (year=='ALL' or t['reference_exit_year']==year)]
                    closed=lambda t:t['match_status']=='CLOSED_MATCH'
                    cohorts.append({'version':v,'variant':variant,'reference':reference,'scope':scope,'year':year,
                        'reference_ge2R_winners':len(sel),'reference_ge2R_R':sum(t['reference_gross_R'] for t in sel),
                        'fully_preserved':sum(closed(t) and t['variant_gross_R']>=t['reference_gross_R']-1e-8 for t in sel),
                        'reduced':sum(closed(t) and t['variant_gross_R']<t['reference_gross_R']-1e-8 for t in sel),
                        'lost_entry':sum(t['match_status']=='NO_MATCHING_ENTRY' for t in sel),
                        'terminal_open':sum(t['match_status']=='OPEN_TERMINAL' for t in sel),
                        'matched_below_2R':sum(closed(t) and t['variant_gross_R']<2 for t in sel),
                        'matched_nonpositive':sum(closed(t) and t['variant_gross_R']<=0 for t in sel),
                        'matched_variant_R':sum(t['variant_gross_R'] for t in sel if closed(t))})
    csv(output/'component_trade_lineage.csv',lineage);csv(output/'component_winner_retention.csv',cohorts)
    # Event paths for mandatory reproductions, with all common frozen fields.
    matches=[]
    for rule,folder in [('CONTROL','t3_m15_stop_exit_v1'),('A6','t3_m15_entry_regime_v1'),('A7','t3_m15_entry_regime_v1'),('S1','t3_m15_stop_exit_v1')]:
        roots=HERE.parent/folder/'results'
        for name,actual in [('entry_opportunities.csv',opportunities),('stop_decisions.csv',decisions)]:
            if not (roots/name).exists():continue
            ref=pd.read_csv(roots/name);ref=ref.loc[ref.rule.eq(rule)].reset_index(drop=True)
            a=actual.loc[actual.rule.eq(rule)].reset_index(drop=True)
            common=sorted(set(a.columns)&set(ref.columns));assert len(a)==len(ref),(rule,name,len(a),len(ref))
            for c in common:
                x,y=a[c],ref[c]
                if c.endswith('_time') or 'AvailableAt' in c:x,y=pd.to_datetime(x,utc=True),pd.to_datetime(y,utc=True)
                if pd.api.types.is_numeric_dtype(x) and not pd.api.types.is_bool_dtype(x):
                    assert ((x-y).abs().fillna(0)<=1e-8).all() and (x.isna()==y.isna()).all(),(rule,name,c)
                else:assert (x.eq(y)|(x.isna()&y.isna())).all(),(rule,name,c)
            matches.append({'rule':rule,'file':name,'rows':len(a),'common_fields':common,'status':'PASS'})
    (output/'REFERENCE_PATH_REPRODUCTION.json').write_text(json.dumps({'status':'PASS','details':matches},sort_keys=True,indent=2)+'\n')
