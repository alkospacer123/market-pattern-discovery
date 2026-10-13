"""Independent scalar recomputation of every replay journal and descriptive CSV.

Never imports primary engine, analysis, reporting, or primary metrics. Reuses
#504's separate dict machine and streaming features; accounting is scalar.
"""
import argparse,csv,json,math,re
from pathlib import Path
from collections import defaultdict
from datetime import datetime
import common as C
import scalar as S
from scalar_metrics import stats

NAMES=('trades','OPEN_POSITIONS','stop_decisions','entry_opportunities','observed_gaps','PERIOD_END_OPEN_POSITIONS')

def read(p):return json.loads(p.read_text()) if p.suffix=='.json' else list(csv.DictReader(p.open()))
def natural(r):return '|'.join((r['instrument'],r['direction'],r['signal_time'].isoformat()))

def same(a,b):
    if isinstance(a,(float,int)) and not isinstance(a,bool) and isinstance(b,(float,int)) and not isinstance(b,bool):return abs(a-b)<=1e-8
    return a==b

def path_equal(a,b,x,y):
    trade_fields='entry_time entry_price initial_stop initial_risk exit_time exit_price gross_R activation_time MFE_R MAE_R active_stop last_close last_close_price threshold_activated'.split()
    stop_fields='bar_open_time bar_close_time active_stop active_stop_next_bar phase exit_price activated_before activated_after activation_time_after extreme_before extreme_after stop_hit'.split()
    if {k for k in trade_fields if k in a}!={k for k in trade_fields if k in b}:return False
    for k in trade_fields:
        if not same(a.get(k),b.get(k)):return False
    if len(x)!=len(y):return False
    for i in range(len(x)):
        for k in stop_fields:
            if not same(x[i].get(k),y[i].get(k)):return False
    return True

def run(root,primary,output):
    output.mkdir(parents=True,exist_ok=True);cmp=C.Comparison()
    frozen=json.loads((C.HERE/'FREEZE.json').read_text())
    for name,sha in frozen['code_spec_sha256'].items():assert C.file_sha(C.HERE/name)==sha and C.sha(C.historical('IntradayLab/t3_m15_a6_s1_trail_optimization_v1/'+name,frozen['commit']))==sha
    frames,sources=C.load_sources(root)
    pools={};combined={k:[] for k in NAMES}
    # Scalar control gate before scalar candidate calculation.
    import control as G
    controls=G.compute(frames,G.CONTROLS,True);G.persist(controls,output/'control_scalar');gate=G.gate(controls,output/'control_scalar',True)
    for v in C.VERSIONS:
        out={k:[r for r in controls[k] if r['version']==v] for k in NAMES} if v in G.CONTROLS else G.compute(frames,[v],True)
        pools[v]=out
        for k in NAMES:combined[k]+=out[k]
    for k,rows in combined.items():
        expected=read(primary/'replay'/(k+('.json' if 'POSITIONS' in k else '.csv')))
        keys=['version','instrument']+(['trade_id'] if k in ('trades','OPEN_POSITIONS') else ['bar_close_time'] if k=='stop_decisions' else ['signal_time'] if k=='entry_opportunities' else ['current_close'] if k=='observed_gaps' else ['month'])
        fields={k for r in expected for k in r};cmp.rows([{k:r.get(k) for k in fields} for r in rows],expected,'REPLAY_'+k,keys)
    computed={k:[] for k in ('summary','monthly','funnel_occupancy','lineage','winner_retention','new_entries','november','closed_equity','negative_results','top_winners','comparison','neighbor_comparison','historical_references')}
    for name in ('summary','monthly'):
        expected_rows=read(primary/(name+'.csv'))
        import itertools
        dims=list(itertools.product(C.VERSIONS,('ALL_FOUR',*C.SYMBOLS),('ALL','LONG','SHORT'),('ALL','2023','2024') if name=='summary' else C.CALENDAR))
        key=lambda r:(r['variant'],r['scope'],r['direction'],r['year'] if name=='summary' else r['month'])
        assert len(expected_rows)==len(dims) and set(map(key,expected_rows))==set(dims),'MISSING_REPORT_DIMENSIONS'
        for i,r in enumerate(read(primary/(name+'.csv'))):
            p=pools[r['variant']];t=[x for x in p['trades'] if (r['scope']=='ALL_FOUR' or x['instrument']==r['scope']) and (r['direction']=='ALL' or x['direction']==r['direction'])]
            calendar=C.CALENDAR
            if name=='summary' and r['year']!='ALL':calendar=[m for m in calendar if m.startswith(r['year'])];t=[x for x in t if str(x['exit_time'].year)==r['year']]
            if name=='monthly':calendar=[r['month']];t=[x for x in t if x['exit_time'].strftime('%Y-%m')==r['month']]
            actual={k:r[k] for k in ('variant','scope','direction')}|{'trail_atr':C.VERSIONS[r['variant']]};actual.update(stats(t,calendar))
            if name=='summary':
                o=p['OPEN_POSITIONS'] if r['year']=='ALL' else [x for x in p['PERIOD_END_OPEN_POSITIONS'] if x['month']==r['year']+'-12']
                actual.update(year=r['year'],period_end_OPEN=sum((r['scope']=='ALL_FOUR' or x['instrument']==r['scope']) and (r['direction']=='ALL' or x['direction']==r['direction']) for x in o))
            else:
                symbols=C.SYMBOLS if r['scope']=='ALL_FOUR' else [r['scope']];first=min(frames[s][0]['at'] for s in symbols).strftime('%Y-%m')
                actual.update(month=r['month'],coverage='NO_COVERAGE' if r['month']<first else 'AVAILABLE_PARTIAL_START' if r['month']==first and r['scope'] in ('GLDRUBF','IMOEXF') else 'AVAILABLE')
            for k,v in actual.items():cmp.value(v,r[k],name,i,k)
            computed[name].append(actual)
    for v,p in pools.items():
        ident={'variant':v,'trail_atr':C.VERSIONS[v]};t=p['trades'];e=p['entry_opportunities'];d=p['stop_decisions']
        for scope in ('ALL_FOUR',*C.SYMBOLS):
            symbols=C.SYMBOLS if scope=='ALL_FOUR' else [scope]
            for year in ('ALL',2023,2024):
                ee=[r for r in e if r['instrument'] in symbols and (year=='ALL' or r['signal_time'].year==year)];dd=[r for r in d if r['instrument'] in symbols and (year=='ALL' or r['bar_close_time'].year==year)]
                count=defaultdict(int)
                for r in ee:
                    if r['entry_accepted']:count['executed_entries']+=1
                    elif not r['rule_pass']:count['filtered']+=1
                    elif r['position_occupied']:count['occupied_allowed_signals']+=1
                    elif r['decision_reason']=='SKIPPED_MISSING_ADJACENT_OPEN':count['missing_adjacent_open']+=1
                    elif r['decision_reason']=='UNRESOLVED_END_OF_DATA':count['unresolved_pending']+=1
                    else:raise AssertionError('UNPARTITIONED_SIGNAL')
                denominator=sum(sum(year=='ALL' or b['at'].year==year for b in frames[s][1:]) for s in symbols)
                computed['funnel_occupancy'].append(ident|{'scope':scope,'year':year,'signals':len(ee)}|{k:count[k] for k in ('executed_entries','filtered','occupied_allowed_signals','missing_adjacent_open','unresolved_pending')}|{'occupied_observed_bars':len(dd),'observed_bar_denominator':denominator,'occupancy_share':len(dd)/denominator if denominator else None,'partition_PASS':sum(count.values())==len(ee)})
            annual=[r for r in t if r['instrument'] in symbols and r['exit_time'].year==2024];nov=[r for r in annual if r['exit_time'].month==11];remaining=[r for r in annual if r['exit_time'].month!=11];a=stats(annual,C.CALENDAR[12:]);b=stats(remaining,[m for m in C.CALENDAR[12:] if m!='2024-11']);nr=math.fsum(r['gross_R'] for r in nov)
            computed['november'].append(ident|{'scope':scope,'november_CLOSED':len(nov),'november_PF':stats(nov,['2024-11'])['gross_PF'],'november_R':nr,'november_share_2024_R':nr/a['gross_R'] if a['gross_R']>0 else None,'ex_november_PF':b['gross_PF'],'ex_november_R':b['gross_R'],'ex_november_DD':b['closed_R_drawdown'],'november_best_month':a['top1_months']=='2024-11'})
        accumulated=0.;peak=0.
        for r in sorted(t,key=lambda r:(r['exit_time'],r['instrument'],r['trade_id'])):
            accumulated+=r['gross_R'];peak=max(peak,accumulated);computed['closed_equity'].append(ident|{k:r[k] for k in ('instrument','trade_id','exit_time','gross_R')}|{'entry_id':natural(r),'cumulative_R':accumulated,'drawdown_R':peak-accumulated})
        for year in ('ALL',2023,2024):
            winners=sorted([r for r in t if r['gross_R']>0 and (year=='ALL' or r['exit_time'].year==year)],key=lambda r:(-r['gross_R'],r['exit_time'],r['instrument'],r['trade_id']))[:10]
            for rank,r in enumerate(winners,1):computed['top_winners'].append(ident|{'year':year,'rank':rank,'in_top5':rank<=5,'entry_id':natural(r)}|{k:r[k] for k in ('instrument','direction','signal_time','entry_time','exit_time','entry_price','exit_price','gross_R','bars_held')})
    for ref in ('TRAIL_300','TRAIL_350'):
        originals={natural(r):r for r in pools[ref]['trades']+pools[ref]['OPEN_POSITIONS']};original_paths=defaultdict(list)
        for r in pools[ref]['stop_decisions']:original_paths[(r['instrument'],r['trade_id'])].append(r)
        for v,p in pools.items():
            candidates={natural(r):r for r in p['trades']+p['OPEN_POSITIONS']};paths=defaultdict(list);decision={(r['instrument'],r['signal_time']):r for r in p['entry_opportunities']}
            for r in p['stop_decisions']:paths[(r['instrument'],r['trade_id'])].append(r)
            lineage=[]
            for identity,r in originals.items():
                n=candidates.get(identity);original_closed='gross_R' in r;candidate_closed=n is not None and 'gross_R' in n;status='ORIGINAL_OPEN'
                if original_closed:
                    if n is None:status='LOST_ENTRY'
                    elif not candidate_closed:status='TERMINAL_OPEN'
                    elif n['gross_R']>=r['gross_R']-1e-8:status='PRESERVED_OR_IMPROVED_R'
                    elif n['gross_R']<0:status='TURNED_LOSS'
                    else:status='PARTIALLY_REDUCED'
                reason=decision[(r['instrument'],r['signal_time'])]['decision_reason']
                eq=False if n is None else path_equal(r,n,original_paths[(r['instrument'],r['trade_id'])],paths[(n['instrument'],n['trade_id'])])
                lineage.append({'reference':ref,'variant':v,'entry_id':identity,'instrument':r['instrument'],'direction':r['direction'],'signal_time':r['signal_time'],'reference_trade_id':r['trade_id'],'candidate_trade_id':n['trade_id'] if n else None,'original_status':'CLOSED' if original_closed else 'OPEN','original_exit_year':r['exit_time'].year if original_closed else None,'original_R':r.get('gross_R'),'candidate_R':n.get('gross_R') if n else None,'status':status,'entry_id_matched':n is not None,'economic_trajectory_equivalent':eq,'decision_reason':reason,'lost_due_occupancy':n is None and reason=='POSITION_OCCUPIED','candidate_status':'CLOSED' if candidate_closed else 'OPEN' if n else 'NOT_ENTERED','original_exit_time':r.get('exit_time'),'candidate_exit_time':n.get('exit_time') if n else None,'R_change':n['gross_R']-r['gross_R'] if original_closed and candidate_closed else None})
            computed['lineage']+=lineage
            for year in ('ALL',2023,2024):
                for threshold in (2.,5.):
                    cohort=[r for r in lineage if r['original_status']=='CLOSED' and r['original_R']>=threshold and (year=='ALL' or r['original_exit_year']==year)]
                    computed['winner_retention'].append({'reference':ref,'variant':v,'year':year,'threshold_R':threshold,'original_winners':len(cohort),'preserved_or_improved_R':sum(r['status']=='PRESERVED_OR_IMPROVED_R' for r in cohort),'partially_reduced':sum(r['status']=='PARTIALLY_REDUCED' for r in cohort),'turned_loss':sum(r['status']=='TURNED_LOSS' for r in cohort),'lost_entry':sum(r['status']=='LOST_ENTRY' for r in cohort),'lost_due_occupancy':sum(r['lost_due_occupancy'] for r in cohort),'terminal_OPEN':sum(r['status']=='TERMINAL_OPEN' for r in cohort),'entry_id_matched':sum(r['entry_id_matched'] for r in cohort),'economic_trajectory_equivalent':sum(r['economic_trajectory_equivalent'] for r in cohort),'still_at_threshold':sum(r['candidate_R'] is not None and r['candidate_R']>=threshold for r in cohort),'original_R_sum':math.fsum(r['original_R'] for r in cohort),'candidate_matched_closed_R_sum':math.fsum(r['candidate_R'] for r in cohort if r['candidate_R'] is not None)})
            for identity,r in candidates.items():
                if identity not in originals:computed['new_entries'].append({'reference':ref,'variant':v,'entry_id':identity,'status':'CLOSED' if 'gross_R' in r else 'OPEN'}|{k:r.get(k) for k in ('instrument','direction','signal_time','entry_time','exit_time','gross_R')})
    get=lambda v,y:next(r for r in computed['summary'] if r['variant']==v and r['year']==str(y) and r['scope']=='ALL_FOUR' and r['direction']=='ALL')
    for v in C.VERSIONS:
        a=get(v,2023);b=get(v,2024);m=get(v,'ALL');n=next(r for r in computed['november'] if r['variant']==v and r['scope']=='ALL_FOUR');gate=a['gross_PF'] is not None and b['gross_PF'] is not None and a['gross_PF']>=1.7 and b['gross_PF']>=1.7
        computed['comparison'].append({'variant':v,'trail_atr':C.VERSIONS[v],'PF2023':a['gross_PF'],'PF2024':b['gross_PF'],'PF_ALL':m['gross_PF'],'R2023':a['gross_R'],'R2024':b['gross_R'],'R_ALL':m['gross_R'],'CLOSED':m['closed'],'OPEN':m['period_end_OPEN'],'positive2023':a['positive_months'],'positive2024':b['positive_months'],'positive_ALL':m['positive_months'],'DD_ALL':m['closed_R_drawdown'],'worst_month':m['worst_month'],'worst_month_R':m['worst_month_R'],'max_negative_month_run':m['max_negative_month_run'],'november_share_2024_R':n['november_share_2024_R'],'ex_november_PF':n['ex_november_PF'],'ex_november_R':n['ex_november_R'],'ANNUAL_PF_MINIMUM_MET':gate,'annual_category':'ANNUAL_PF_GATE_MET' if gate else 'NOT MET','PREFERRED_PF_TARGET_MET':a['gross_PF'] is not None and b['gross_PF'] is not None and a['gross_PF']>2 and b['gross_PF']>2})
        for year in (2023,2024):
            r=get(v,year)
            if r['gross_PF'] is None or r['gross_PF']<1.7:computed['negative_results'].append({'variant':v,'trail_atr':C.VERSIONS[v],'year':year,'finding':'ANNUAL_PF_MINIMUM_NOT_MET','value':r['gross_PF']})
        for r in computed['monthly']:
            if r['variant']==v and r['scope']=='ALL_FOUR' and r['direction']=='ALL' and r['gross_R']<0:computed['negative_results'].append({'variant':v,'trail_atr':C.VERSIONS[v],'year':int(r['month'][:4]),'month':r['month'],'finding':'NEGATIVE_MONTH','value':r['gross_R']})
    for a,b in zip(computed['comparison'],computed['comparison'][1:]):computed['neighbor_comparison'].append({'left':a['variant'],'right':b['variant']}|{'delta_'+k:b[k]-a[k] for k in ('PF2023','PF2024','PF_ALL','R_ALL','positive_ALL','DD_ALL','november_share_2024_R','worst_month_R')})
    for pr,folder in [(497,'t3_m15_combined_v1/results'),(504,'t3_m15_execution_sensitivity_v1/results/next_open')]:
        original=C.reference('IntradayLab/'+folder+'/trades.csv')
        for v in ('BASELINE','OPTIMIZED'):
            rows=[r|{'exit_time':datetime.fromisoformat(r['exit_time']),'gross_R':float(r['gross_R'])} for r in original if r['rule']=='C1' and r['version']==v]
            for year in ('ALL',2023,2024):computed['historical_references'].append({'PR':pr,'execution':'SIGNAL_CLOSE' if pr==497 else 'NEXT_OPEN','version':v,'year':year}|stats([r for r in rows if year=='ALL' or r['exit_time'].year==year],[m for m in C.CALENDAR if year=='ALL' or m.startswith(str(year))]))
    keys={'funnel_occupancy':['variant','scope','year'],'november':['variant','scope'],'closed_equity':['variant','instrument','trade_id'],'top_winners':['variant','year','rank'],'lineage':['reference','variant','entry_id'],'winner_retention':['reference','variant','year','threshold_R'],'new_entries':['reference','variant','entry_id'],'comparison':['variant'],'neighbor_comparison':['left','right'],'historical_references':['PR','version','year'],'negative_results':['variant','year','month','finding']}
    for name,fields in keys.items():
        expected=read(primary/(name+'.csv'));allfields={k for r in expected for k in r}
        cmp.rows([{k:r.get(k) for k in allfields} for r in computed[name]],expected,name,fields)
    # Source tables independently audited above; verify every displayed Markdown row.
    presentation=presentation_audit(primary,computed)
    C.write_json(output/'PRESENTATION_AUDIT.json',presentation)
    C.write_csv(output/'DIFFERENCES.csv',cmp.diffs,['table','row','field','actual','expected'])
    C.write_json(output/'OPEN_POSITIONS.json',combined['OPEN_POSITIONS']);C.write_json(output/'PERIOD_END_OPEN_POSITIONS.json',combined['PERIOD_END_OPEN_POSITIONS'])
    result={'status':'PASS' if not cmp.diffs else 'FAIL','fields_compared':cmp.fields,'differences':len(cmp.diffs),'max_numeric_delta':max(cmp.maxima.values(),default=0),'absolute_tolerance':1e-8,'CLOSED':len(combined['trades']),'terminal_OPEN':len(combined['OPEN_POSITIONS']),'stop_decisions':len(combined['stop_decisions']),'signal_decisions':len(combined['entry_opportunities']),'tables':cmp.tables,'independence':'separate streaming/dict/scalar; primary engine/analysis/metrics not imported; same author; external human review PENDING'}
    C.write_json(output/'AUDIT_RESULT.json',result);assert not cmp.diffs,'INDEPENDENT_AUDIT_FAILED';print(json.dumps(result,indent=2))

def presentation_audit(primary,computed):
    def formatted(v):
        if v is None or v=='':return 'NA'
        if isinstance(v,bool):return str(v)
        if isinstance(v,(float,int)):
            return f'{v:.6f}' if isinstance(v,float) else str(v)
        # CSV identity metadata copied as strings: decimal formatting only for numeric trail.
        return str(v).replace('|',' / ')
    merged=[]
    for v in C.VERSIONS:
        for m in C.CALENDAR:
            get=lambda s,d='ALL':next(r for r in computed['monthly'] if r['variant']==v and r['month']==m and r['scope']==s and r['direction']==d)
            row=get('ALL_FOUR');merged.append({k:row[k] for k in ('month','gross_PF','gross_R','closed','closed_R_drawdown')}|{s+'_CLOSED':get('ALL_FOUR',s)['closed'] for s in ('LONG','SHORT')}|{s+'_R':get('ALL_FOUR',s)['gross_R'] for s in ('LONG','SHORT')}|{s+'_R':get(s)['gross_R'] for s in C.SYMBOLS})
    # Use full primary metadata formatting (year/variant/trail) after numeric audit.
    sources=[read(primary/(k+'.csv')) for k in computed]+[merged]
    count=tables=cells=0
    for name in ('REPORT.md','MONTHLY_DETAIL.md'):
        header=None;allowed=set()
        for line in (primary/name).read_text().splitlines():
            if not line.startswith('| '):header=None;continue
            values=[x.strip() for x in line.split('|')[1:-1]]
            if all(x=='---' for x in values):continue
            if header is None:
                header=values;tables+=1;allowed=set()
                for source in sources:
                    for r in source:
                        if all(k in r for k in header):
                            vals=[]
                            for k in header:
                                val=r[k]
                                if isinstance(val,str) and val not in ('True','False'):
                                    try:val=float(val);val=int(val) if k in ('year','closed','CLOSED','OPEN','period_end_OPEN','wins','losses','positive_months','negative_months','zero_months','max_losing_trade_run','max_negative_month_run','rank','bars_held','LONG_CLOSED','SHORT_CLOSED','signals','executed_entries','filtered','occupied_allowed_signals','missing_adjacent_open','unresolved_pending','occupied_observed_bars','observed_bar_denominator','november_CLOSED','original_winners','preserved_or_improved_R','partially_reduced','turned_loss','lost_entry','lost_due_occupancy','terminal_OPEN','entry_id_matched','economic_trajectory_equivalent','still_at_threshold','PR','positive2023','positive2024','positive_ALL','delta_positive_ALL') else val
                                    except ValueError:pass
                                vals.append(formatted(val))
                            allowed.add(tuple(vals))
            else:
                assert tuple(values) in allowed,('PRESENTATION_MISMATCH',name,header,values)
                count+=1;cells+=len(values)
    return {'status':'PASS','tables':tables,'rows':count,'cells':cells,'all_rendered_rows_match_audited_CSV_or_independently_combined_monthly_rows':True}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--data-root',type=Path,default=Path('/workspace/market-pattern-data'));p.add_argument('--primary',type=Path,default=C.HERE/'results');p.add_argument('--output',type=Path,default=C.HERE/'audit');a=p.parse_args();run(a.data_root,a.primary,a.output)
