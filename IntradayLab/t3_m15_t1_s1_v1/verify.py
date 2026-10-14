"""Independent full computation, report validation and fresh byte repeats.

Does not import primary engine/research/reports. Uses only the independent
stdlib parser/features/metrics and its delayed-trailing position machine.
"""
import argparse
import csv
import json
from pathlib import Path
from statistics import median
import subprocess
import sys
import independent as I
import independent_combination as J

def csv_read(path):
    with Path(path).open() as f:return list(csv.DictReader(f))

def compare_reports(c,t,o,sn,e,g,frames,target,rules):
    scopes=('ALL_FOUR',*I.SYMBOLS)
    for name in ('overall_report','instrument_report','yearly_report','monthly_report','direction_report'):
        ref=csv_read(target/(name+'.csv'));actual=[]
        scope_set=I.SYMBOLS if name=='instrument_report' else scopes
        n=len(I.VERSIONS)*len(rules)*len(scope_set)
        n*=2 if name=='yearly_report' else 24 if name=='monthly_report' else 6 if name=='direction_report' else 1
        c.value(len(ref),n,name,-1,'complete_dimension_row_count')
        for r in ref:
            assert r['version'] in I.VERSIONS and r['rule'] in rules and r['scope'] in scope_set
            symbols=I.SYMBOLS if r['scope']=='ALL_FOUR' else (r['scope'],)
            x=[z for z in t if z['version']==r['version'] and z['rule']==r['rule'] and z['instrument'] in symbols]
            op=[z for z in o if z['version']==r['version'] and z['rule']==r['rule'] and z['instrument'] in symbols]
            snapshots=[z for z in sn if z['version']==r['version'] and z['rule']==r['rule'] and z['instrument'] in symbols]
            ids={k:r[k] for k in ('version','rule','scope')};months=I.CALENDAR
            first=min(frames[s][0]['at'] for s in symbols).strftime('%Y-%m')
            if 'year' in r:
                y=r['year'];assert y in ('ALL','2023','2024');ids['year']=y
                if y!='ALL':
                    x=[z for z in x if z['exit_time'].year==int(y)];months=[m for m in months if m.startswith(y)]
                    op=[z for z in snapshots if z['month']==y+'-12']
            if 'direction' in r:
                ids['direction']=r['direction'];assert r['direction'] in ('LONG','SHORT')
                x=[z for z in x if z['direction']==r['direction']];op=[z for z in op if z['direction']==r['direction']]
            if 'month' in r:
                month=r['month'];assert month in I.CALENDAR;ids.update(month=month,coverage='NO_COVERAGE' if month<first else 'AVAILABLE')
                x=[z for z in x if z['exit_time'].strftime('%Y-%m')==month];months=[month];op=[z for z in snapshots if z['month']==month]
            if 'first_available_month' in r:
                covered=[m for m in I.CALENDAR if m>=first]
                ids.update(first_available_month=first,covered_calendar_months=len(covered),
                    positive_share_covered_months=sum(sum(z['gross_R'] for z in x if z['exit_time'].strftime('%Y-%m')==m)>0 for m in covered)/len(covered))
            actual.append(ids|I.metrics(x,months,len(op)))
        keys=[k for k in ('version','rule','scope','year','direction','month') if k in ref[0]]
        assert len({tuple(r[k] for k in keys) for r in ref})==len(ref),'DUPLICATE_REPORT_DIMENSIONS'
        c.rows(actual,ref,name,keys)
    ref=csv_read(target/'november_dependence.csv');actual=[]
    for r in ref:
        x=[z for z in t if z['version']==r['version'] and z['rule']==r['rule'] and (r['scope']=='ALL_FOUR' or z['instrument']==r['scope']) and z['exit_time'].year==2024]
        rest=[z for z in x if z['exit_time'].month!=11];a=I.metrics(x,I.CALENDAR[12:]);b=I.metrics(rest,[m for m in I.CALENDAR[12:] if m!='2024-11'])
        actual.append({k:r[k] for k in ('version','rule','scope')}|{'year':2024,'full_PF':a['gross_PF'],'full_R':a['gross_R'],
            'november_closed':len(x)-len(rest),'november_R':sum(z['gross_R'] for z in x if z['exit_time'].month==11),
            'ex_november_closed':len(rest),'ex_november_PF':b['gross_PF'],'ex_november_R':b['gross_R'],'ex_november_drawdown_R':b['max_drawdown_closed_R']})
    c.rows(actual,ref,'november_dependence',['version','rule','scope'])
    eq,top,runs=[],[],[]
    for v in I.VERSIONS:
        for rule in rules:
            for scope in scopes:
                ids={'version':v,'rule':rule,'scope':scope}
                x=[z for z in t if z['version']==v and z['rule']==rule and (scope=='ALL_FOUR' or z['instrument']==scope)]
                if scope=='ALL_FOUR':
                    peak=equity=0.
                    for z in sorted(x,key=lambda z:(z['exit_time'],z['instrument'],z['trade_id'])):
                        equity+=z['gross_R'];peak=max(peak,equity)
                        eq.append(ids|{k:z[k] for k in ('instrument','trade_id','exit_time')}|{'trade_R':z['gross_R'],'cumulative_closed_R':equity,'drawdown_R':peak-equity})
                for n in (5,10):
                    wins=sorted((z for z in x if z['gross_R']>0),key=lambda z:(-z['gross_R'],z['instrument'],z['trade_id']))[:n]
                    for rank,z in enumerate(wins,1):top.append(ids|{'top_n':n,'rank':rank}|{k:z[k] for k in ('instrument','trade_id','entry_time','exit_time','gross_R')})
                monthly={m:sum(z['gross_R'] for z in x if z['exit_time'].strftime('%Y-%m')==m) for m in I.CALENDAR};run=[]
                for m,val in list(monthly.items())+[('END',0)]:
                    if val<0:run.append(m)
                    elif run:
                        runs.append(ids|{'first_month':run[0],'last_month':run[-1],'months':len(run),'gross_R':sum(monthly[m] for m in run)});run=[]
    for name,rows,keys in [('closed_equity',eq,['version','rule','exit_time','instrument','trade_id']),
        ('top_winners',top,['version','rule','scope','top_n','rank']),('losing_month_runs',runs,['version','rule','scope','first_month'])]:
        c.rows(rows,csv_read(target/(name+'.csv')),name,keys)
    for name in ('signal_funnel','holding_frequency','stop_activation'):
        actual=[];ref=csv_read(target/(name+'.csv'))
        for r in ref:
            v,rule,scope,y=r['version'],r['rule'],r['scope'],r['year'];symbols=I.SYMBOLS if scope=='ALL_FOUR' else (scope,)
            q=[z for z in e if z['version']==v and z['rule']==rule and z['instrument'] in symbols and (y=='ALL' or z['signal_time'].year==int(y))]
            x=[z for z in t if z['version']==v and z['rule']==rule and z['instrument'] in symbols and (y=='ALL' or z['exit_time'].year==int(y))]
            ids={k:r[k] for k in ('version','rule','scope','year')};accepted=sum(z['entry_accepted'] for z in q)
            if name=='signal_funnel':
                rejected=sum(not z['rule_pass'] for z in q);busy=sum(z['rule_pass'] and z['position_occupied'] for z in q)
                row={'original_signals':len(q),'accepted_entries':accepted,'rule_forbidden_signals':rejected,
                    'rule_forbidden_when_flat':sum(not z['rule_pass'] and not z['position_occupied'] for z in q),
                    'rule_forbidden_and_busy':sum(not z['rule_pass'] and z['position_occupied'] for z in q),
                    'allowed_skipped_position_busy':busy,'all_busy_signals':sum(z['position_occupied'] for z in q),'partition_check':accepted+rejected+busy==len(q)}
            elif name=='stop_activation':
                row={'closed_count':len(x),'activated_closed':sum(z['threshold_activated'] for z in x),
                    'unactivated_closed':sum(not z['threshold_activated'] for z in x),
                    'unactivated_closed_R':sum(z['gross_R'] for z in x if not z['threshold_activated']),
                    'activated_closed_R':sum(z['gross_R'] for z in x if z['threshold_activated']),
                    'same_entry_signal_candle_used_for_activation':False}
            else:
                minutes=sorted(z['holding_minutes'] for z in x)
                if minutes:
                    ix=(len(minutes)-1)*.9;lo=int(ix);hi=min(lo+1,len(minutes)-1)
                    p90=minutes[lo]+(minutes[hi]-minutes[lo])*(ix-lo)
                days=[{b['at'].date() for b in frames[s] if y=='ALL' or b['at'].year==int(y)} for s in symbols]
                instrument_days=sum(map(len,days));portfolio_days=len(set.union(*days))
                op=[z for z in o if z['version']==v and z['rule']==rule and z['instrument'] in symbols and (y=='ALL' or z['entry_time'].year==int(y))]
                row={'closed_count':len(x),'terminal_open_entry_cohort_count':len(op),'holding_minutes_mean':sum(minutes)/len(minutes) if minutes else None,
                    'holding_minutes_median':median(minutes) if minutes else None,'holding_minutes_p90':p90 if minutes else None,
                    'bars_held_median':median([z['bars_held'] for z in x]) if x else None,'accepted_entries':accepted,
                    'observed_instrument_days':instrument_days,'observed_portfolio_days':portfolio_days,
                    'entries_per_observed_instrument_day':accepted/instrument_days if instrument_days else None,
                    'entries_per_observed_portfolio_day':accepted/portfolio_days if portfolio_days else None,
                    'closed_with_observed_overnight_gap':sum(z['observed_overnight_gaps_exposed']>0 for z in x),
                    'closed_with_observed_overnight_gap_share':sum(z['observed_overnight_gaps_exposed']>0 for z in x)/len(x) if x else None,
                    'total_observed_overnight_gap_exposures':sum(z['observed_overnight_gaps_exposed'] for z in x),
                    'cross_calendar_day_closed':sum(z['cross_calendar_day'] for z in x)}
            actual.append(ids|row)
        c.rows(actual,ref,name,['version','rule','scope','year'])

def compare_lineage(c,t,o,e,target,rules):
    key=lambda r:(r['instrument'],r['direction'],r['entry_time'])
    lineage,new,changes,winners=[],[],[],[]
    for v in I.VERSIONS:
        for variant in rules:
            if variant=='CONTROL':continue
            vt=[z for z in t if z['version']==v and z['rule']==variant];vo=[z for z in o if z['version']==v and z['rule']==variant]
            closed={key(z):z for z in vt};opened={key(z):z for z in vo}
            decisions={(z['instrument'],z['signal_time']):z for z in e if z['version']==v and z['rule']==variant}
            for reference in (('CONTROL','T1','S1') if variant=='COMBINED' else ('CONTROL',)):
                rt=[z for z in t if z['version']==v and z['rule']==reference];ro=[z for z in o if z['version']==v and z['rule']==reference]
                entry_keys={key(z) for z in rt+ro}
                re={(z['instrument'],z['signal_time']):z for z in e if z['version']==v and z['rule']==reference}
                local=[]
                for z in rt:
                    match=closed.get(key(z));op=opened.get(key(z));d=decisions[(z['instrument'],z['entry_time'])]
                    preserved=bool(match and abs(match['gross_R']-z['gross_R'])<=1e-8 and match['exit_time']==z['exit_time'] and abs(match['exit_price']-z['exit_price'])<=1e-8)
                    status='UNCHANGED_CLOSED' if preserved else 'CHANGED_CLOSED' if match else 'TERMINAL_OPEN' if op else 'LOST_ENTRY'
                    r={'version':v,'variant':variant,'reference':reference,'instrument':z['instrument'],'direction':z['direction'],
                        'reference_trade_id':z['trade_id'],'entry_time':z['entry_time'],'reference_exit_time':z['exit_time'],
                        'reference_gross_R':z['gross_R'],'reference_winner_ge_2R':z['gross_R']>=2,'match_status':status,
                        'variant_trade_id':(match or op or {}).get('trade_id'),'variant_exit_time':match['exit_time'] if match else None,
                        'variant_gross_R':match['gross_R'] if match else None,'delta_R':match['gross_R']-z['gross_R'] if match else None,
                        'variant_winner_ge_2R':bool(match and match['gross_R']>=2),'outcome_preserved':preserved,
                        'decision_reason':d['decision_reason'],'rule_reason':d['rule_reason'],'occupied_trade_id':d['occupied_trade_id']}
                    local.append(r);lineage.append(r)
                news=[z for z in vt if key(z) not in entry_keys]
                new.extend(z|{'variant':variant,'reference':reference,'reference_occupied_trade_id':re[(z['instrument'],z['entry_time'])]['occupied_trade_id']} for z in news)
                for k,z in decisions.items():
                    before=re[k]
                    if z['entry_accepted']!=before['entry_accepted'] or z['position_occupied']!=before['position_occupied']:
                        changes.append({'version':v,'variant':variant,'reference':reference,'instrument':z['instrument'],'signal_time':z['signal_time'],
                            'direction':z['direction'],'reference_accepted':before['entry_accepted'],'variant_accepted':z['entry_accepted'],
                            'reference_busy':before['position_occupied'],'variant_busy':z['position_occupied'],
                            'reference_occupied_trade_id':before['occupied_trade_id'],'variant_occupied_trade_id':z['occupied_trade_id'],
                            'variant_rule_pass':z['rule_pass'],'variant_reason':z['decision_reason']})
                for scope in ('ALL_FOUR',*I.SYMBOLS):
                    for year in ('ALL',2023,2024):
                        ss=[z for z in local if (scope=='ALL_FOUR' or z['instrument']==scope) and (year=='ALL' or z['reference_exit_time'].year==year)]
                        ww=[z for z in ss if z['reference_winner_ge_2R']];lost=[z for z in ss if z['match_status']=='LOST_ENTRY']
                        nn=[z for z in news if (scope=='ALL_FOUR' or z['instrument']==scope) and (year=='ALL' or z['exit_time'].year==year)]
                        winners.append({'version':v,'variant':variant,'reference':reference,'scope':scope,'reference_exit_year':year,
                            'reference_large_winners_ge_2R':len(ww),'large_winners_unchanged':sum(z['outcome_preserved'] for z in ww),
                            'large_winners_changed_still_ge_2R':sum(z['match_status']=='CHANGED_CLOSED' and z['variant_winner_ge_2R'] for z in ww),
                            'large_winners_degraded_below_2R':sum(z['match_status']=='CHANGED_CLOSED' and not z['variant_winner_ge_2R'] for z in ww),
                            'large_winners_lost':sum(z['match_status']=='LOST_ENTRY' for z in ww),'large_winners_terminal_OPEN':sum(z['match_status']=='TERMINAL_OPEN' for z in ww),
                            'lost_large_winner_R':sum(z['reference_gross_R'] for z in ww if z['match_status']=='LOST_ENTRY'),
                            'matched_large_winner_delta_R':sum(z['delta_R'] for z in ww if z['delta_R'] is not None),
                            'lost_entry_rule_blocked':sum(z['decision_reason'] in ('RULE_BLOCKED','RULE_AND_OCCUPIED') for z in lost),
                            'lost_entry_busy_only':sum(z['decision_reason']=='POSITION_OCCUPIED' for z in lost),
                            'new_closed_entries':len(nn),'new_closed_losses':sum(z['gross_R']<0 for z in nn),'new_closed_gross_R':sum(z['gross_R'] for z in nn),
                            'new_losses_R_volume':-sum(z['gross_R'] for z in nn if z['gross_R']<0)})
    for name,rows,keys in [('entry_lineage',lineage,['version','variant','reference','instrument','entry_time']),
        ('new_entries',new,['version','variant','reference','instrument','entry_time']),
        ('chronology_changes',changes,['version','variant','reference','instrument','signal_time']),
        ('winner_comparison',winners,['version','variant','reference','scope','reference_exit_year'])]:
        c.rows(rows,csv_read(target/(name+'.csv')),name,keys)

def verify(root,target,output,benchmarks=False):
    assert target.resolve().is_relative_to(I.HERE) and output.resolve().is_relative_to(I.HERE)
    output.mkdir(parents=True,exist_ok=True);frames,sources=I.load_sources(root)
    rules=('CONTROL','S1','T1') if benchmarks else ('CONTROL','T1','S1','COMBINED')
    if not benchmarks:
        freeze=json.loads((I.HERE/'FREEZE.json').read_text());pre=json.loads((I.HERE/'PRE_COMBINATION_GATE.json').read_text())
        assert pre['status']=='PASS' and freeze['freeze_commit']==pre['freeze_commit']
        for name,digest in freeze['code_and_spec_SHA256'].items():
            assert I.file_sha(I.HERE/name)==digest and I.sha(I.historical('IntradayLab/t3_m15_t1_s1_v1/'+name,freeze['freeze_commit']))==digest
    t,o,d,e,g,sn=[],[],[],[],[],[]
    for rule in rules:
        for v in I.VERSIONS:
            for s in I.SYMBOLS:
                tt,op,ss,ee,gg,nn=J.simulate(frames[s],s,v,rule)
                t.extend(tt);d.extend(ss);e.extend(ee);g.extend(gg);sn.extend(nn)
                if op:o.append(op)
    c=I.Comparison()
    for name,rows,keys in [('trades',t,['version','rule','instrument','entry_time']),('stop_decisions',d,['version','rule','instrument','bar_close_time']),
        ('entry_opportunities',e,['version','rule','instrument','signal_time']),('observed_gaps',g,['version','rule','instrument','current_close'])]:
        c.rows(rows,csv_read(target/(name+'.csv')),name,keys)
        I.write_csv(output/(name+'.csv'),rows)
    c.rows(o,json.loads((target/'OPEN_POSITIONS.json').read_text()),'terminal_OPEN',['version','rule','instrument'])
    c.rows(sn,json.loads((target/'PERIOD_END_OPEN_POSITIONS.json').read_text()),'period_OPEN',['version','rule','instrument','month'])
    I.write_json(output/'OPEN_POSITIONS.json',o);I.write_json(output/'PERIOD_END_OPEN_POSITIONS.json',sn)
    for rule,path in [('CONTROL','IntradayLab/t3_m15_forever_v1/trades.csv'),('CONTROL','IntradayLab/t3_m15_entry_regime_v1/results/trades_CONTROL.csv'),
        ('T1','IntradayLab/t3_m15_session_entry_v1/results/trades_T1.csv'),('S1','IntradayLab/t3_m15_stop_exit_v1/results/trades_S1.csv')]:
        c.rows([z for z in t if z['rule']==rule],I.reference(path),'INDEPENDENT_REFERENCE_'+path,['version','instrument','entry_time'],('C1_R','net_R','c1_price_unit','initial_risk_ticks'))
    compare_reports(c,t,o,sn,e,g,frames,target,rules);compare_lineage(c,t,o,e,target,rules)
    inventory=json.loads((target/'GENERATED_SHA256.json').read_text())
    for name,digest in inventory.items():assert I.file_sha(target/name)==digest,('PRIMARY_ARTIFACT_HASH',name)
    I.write_csv(output/'DISCREPANCIES.csv',c.diffs,['table','row','field','actual','expected'])
    result={'status':'PASS' if not c.diffs else 'FAIL','labels':I.LABEL,'2023_2024':'DEVELOPMENT_EXPOSED','numeric_absolute_tolerance':1e-8,
        'source_SHA':I.DATA_SHA,'future_OHLC_parsed':False,'independent_implementation':'stdlib parser and recurrences / forward H1 / separate state machine / scalar metrics and independently rebuilt diagnostics',
        'primary_engine_or_metrics_imported':False,'fields_compared':c.fields,'differences':len(c.diffs),'maximum_differences':c.maxima,'tables':c.tables,
        'closed_total':len(t),'terminal_OPEN':len(o),'combination_checked':not benchmarks}
    I.write_json(output/'AUDIT_RESULT.json',result)
    I.write_json(output/'GENERATED_SHA256.json',{p.name:I.file_sha(p) for p in sorted(output.iterdir()) if p.is_file() and p.name!='GENERATED_SHA256.json'})
    print(json.dumps({k:result[k] for k in ('status','fields_compared','differences','closed_total','terminal_OPEN','combination_checked')}))
    assert not c.diffs,'INDEPENDENT_COMPARISON_FAIL'
    return result

def repeat(root):
    manifest=json.loads((I.HERE/'results/GENERATED_SHA256.json').read_text())
    independent_manifest=json.loads((I.HERE/'independent_results/GENERATED_SHA256.json').read_text())
    first_gate_files={p.name:I.file_sha(p) for p in (I.HERE/'audit_499').iterdir() if p.is_file()}
    runs=[]
    for n in (1,2):
        output=I.HERE/'work'/f'repeat{n}';assert not output.exists(),'FRESH_DIRECTORY_REQUIRED'
        r=subprocess.run([sys.executable,str(I.HERE/'research.py'),'--data-root',str(root),'--output',str(output)],capture_output=True,text=True)
        (I.HERE/f'REPEAT_{n}_LOG.txt').write_text(r.stdout+r.stderr);assert r.returncode==0,r.stderr
        other=json.loads((output/'GENERATED_SHA256.json').read_text());assert manifest==other
        for name in [*manifest,'GENERATED_SHA256.json']:
            assert (output/name).read_bytes()==(I.HERE/'results'/name).read_bytes(),('BYTE_REPEAT_FAIL',n,name)
        ind=I.HERE/'work'/f'independent_repeat{n}';audit=I.HERE/'work'/f'audit499_repeat{n}'
        assert not ind.exists() and not audit.exists(),'FRESH_INDEPENDENT_DIRECTORY_REQUIRED'
        for script,args,log in [('verify.py',['--target',str(output),'--output',str(ind)],f'INDEPENDENT_REPEAT_{n}_LOG.txt'),
            ('audit_499.py',['--output',str(audit)],f'AUDIT499_REPEAT_{n}_LOG.txt')]:
            fresh=subprocess.run([sys.executable,str(I.HERE/script),'--data-root',str(root),*args],capture_output=True,text=True)
            (I.HERE/log).write_text(I.LABEL+'\n2023–2024: DEVELOPMENT_EXPOSED\n'+fresh.stdout+fresh.stderr)
            assert fresh.returncode==0,fresh.stderr
        assert json.loads((ind/'GENERATED_SHA256.json').read_text())==independent_manifest
        for name in [*independent_manifest,'GENERATED_SHA256.json']:
            assert (ind/name).read_bytes()==(I.HERE/'independent_results'/name).read_bytes(),('INDEPENDENT_BYTE_REPEAT_FAIL',n,name)
        assert {p.name:I.file_sha(p) for p in audit.iterdir() if p.is_file()}==first_gate_files
        for name in first_gate_files:
            assert (audit/name).read_bytes()==(I.HERE/'audit_499'/name).read_bytes(),('FIRST_GATE_BYTE_REPEAT_FAIL',n,name)
        runs.append({'repeat':n,'fresh_process':True,'direct_byte_equality':True,'generated_files':len(manifest)+1,
            'independent_generated_files':len(independent_manifest)+1,'FIRST_GATE_files':len(first_gate_files),
            'independent_direct_byte_equality':True,'FIRST_GATE_direct_byte_equality':True,
            'manifest_SHA256':I.file_sha(output/'GENERATED_SHA256.json'),
            'independent_manifest_SHA256':I.file_sha(ind/'GENERATED_SHA256.json')})
    I.write_json(I.HERE/'REPEATABILITY.json',{'status':'PASS','labels':I.LABEL,'2023_2024':'DEVELOPMENT_EXPOSED',
        'two_full_fresh_byte_repeats':True,'runs':runs,'scope':'primary eight replays + independent eight replays + FIRST GATE #499; every generated trade/Stop/entry/gap/OPEN journal, source manifest, metric, lineage, diagnostic and readable report'})
    print(json.dumps({'repeatability':'PASS','files_per_repeat':len(manifest)+1}))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--data-root',type=Path,required=True);p.add_argument('--target',type=Path,default=I.HERE/'results');p.add_argument('--output',type=Path,default=I.HERE/'independent_results');p.add_argument('--benchmarks-only',action='store_true');p.add_argument('--repeat',action='store_true')
    a=p.parse_args()
    if a.repeat:repeat(a.data_root)
    else:verify(a.data_root,a.target,a.output,a.benchmarks_only)
