"""FIRST GATE: an external-to-#499 implementation; imports only this package.

All historical code is read as evidence, never executed or imported. A FAIL or
exception is a blocker; this script cannot calculate the new combination.
"""
import argparse
import json
from pathlib import Path
from statistics import median
import traceback
import independent as I

FOLDER='IntradayLab/t3_m15_session_entry_v1/'
FREEZE='e8feb7ac351c9548d61abee0e06462485e852fc1'
HEAD499='f279ccd7b88505d16fee4a4a6e55a2f0ad1004d0'
PARENT499='4b415f95576e00480e344a1da498c35660eef931'

def verify_git():
    actual=I.git('ls-remote','origin','refs/heads/main').decode().split()[0]
    later=[]
    if actual!=I.BASE:
        assert I.git('merge-base',I.BASE,actual).decode().strip()==I.BASE
        later=I.git('log','--format=%H %s',f'{I.BASE}..{actual}').decode().splitlines()
        changes=I.git('diff','--name-only',I.BASE,actual).decode().splitlines()
        assert not any(p.startswith(('IntradayLab/t3_m15_forever_v1/','IntradayLab/t3_m15_session_entry_v1/','IntradayLab/t3_m15_stop_exit_v1/')) for p in changes),'MAIN_CHANGED_RELEVANT_SCOPE'
    files=I.git('diff','--name-status',PARENT499,HEAD499).decode().splitlines()
    assert len(files)==60 and all(x.startswith('A\t'+FOLDER) for x in files),'PR499_SCOPE'
    frozen=I.git('ls-tree','-r','--name-only',FREEZE,'--',FOLDER).decode().splitlines()
    assert not any('/results/' in p for p in frozen),'RESULTS_IN_FREEZE'
    code=[p for p in frozen if p.endswith('.py') or p.endswith('/EXPERIMENT_SPECS.json')]
    freeze_hashes={}
    for p in code:
        before=I.historical(p,FREEZE);after=I.historical(p)
        assert before==after,('FROZEN_CODE_CHANGED',p)
        freeze_hashes[p]=I.sha(before)
    assert I.git('merge-base','--is-ancestor',FREEZE,HEAD499)==b''
    gate=json.loads(I.historical(FOLDER+'PRE_VARIANT_GATE.json'))
    assert gate['freeze_commit']==FREEZE and gate['before_variant_results'] and gate['control']=='PASS' and gate['tests']=='PASS'
    inventory=json.loads(I.historical(FOLDER+'ARTIFACT_SHA256.json'))
    for name,expected in inventory.items():assert I.sha(I.historical(FOLDER+name))==expected,('ARTIFACT_HASH',name)
    manifest=json.loads(I.historical(FOLDER+'results/SOURCE_MANIFEST.json'))
    for name,expected in manifest['reference_sha256'].items():assert I.sha(I.historical('IntradayLab/'+name))==expected,('REFERENCE_HASH',name)
    return {'actual_remote_main':actual,'expected_main':I.BASE,'later_commits':later,'source_SHA':I.DATA_SHA,
        'PR499_head':HEAD499,'PR499_merge':I.BASE,'PR499_scope_added_files':len(files),
        'pre_result_freeze':FREEZE,'freeze_code_SHA256':freeze_hashes,'freeze_results_absent':True,
        'all_PR499_artifact_hashes_verified':len(inventory),'frozen_reference_hashes_verified':len(manifest['reference_sha256'])}

def report_audit(c,t,o,snap,frames):
    for name in ('overall_report','yearly_report','direction_report','monthly_report','instrument_report'):
        expected=I.reference(FOLDER+'results/'+name+'.csv');actual=[]
        for r in expected:
            v,rule,scope=r['version'],r['rule'],r['scope'];symbols=I.SYMBOLS if scope=='ALL_FOUR' else (scope,)
            selected=[x for x in t if x['version']==v and x['rule']==rule and x['instrument'] in symbols]
            ops=[x for x in o if x['version']==v and x['rule']==rule and x['instrument'] in symbols]
            snapshots=[x for x in snap if x['version']==v and x['rule']==rule and x['instrument'] in symbols]
            months=I.CALENDAR
            ids={k:r[k] for k in ('version','rule','scope')}
            first=min(frames[s][0]['at'] for s in symbols).strftime('%Y-%m')
            if 'year' in r:
                year=r['year'];ids['year']=year
                if year!='ALL':
                    selected=[x for x in selected if x['exit_time'].year==int(year)]
                    months=[m for m in months if m.startswith(year)]
                    ops=[x for x in snapshots if x['month']==year+'-12']
            if 'direction' in r:
                ids['direction']=r['direction'];selected=[x for x in selected if x['direction']==r['direction']]
                ops=[x for x in ops if x['direction']==r['direction']]
            if 'month' in r:
                m=r['month'];ids.update(month=m,coverage='NO_COVERAGE' if m<first else 'AVAILABLE')
                selected=[x for x in selected if x['exit_time'].strftime('%Y-%m')==m];months=[m]
                ops=[x for x in snapshots if x['month']==m]
            if 'first_available_month' in r:
                available=[m for m in I.CALENDAR if m>=first]
                ids.update(first_available_month=first,covered_calendar_months=len(available),
                    positive_share_covered_months=sum(sum(x['gross_R'] for x in selected if x['exit_time'].strftime('%Y-%m')==m)>0 for m in available)/len(available))
            actual.append(ids|I.metrics(selected,months,len(ops)))
        keys=[k for k in ('version','rule','scope','year','direction','month') if k in expected[0]]
        c.rows(actual,expected,name,keys)
    expected=I.reference(FOLDER+'results/november_dependence.csv');actual=[]
    for r in expected:
        x=[x for x in t if x['version']==r['version'] and x['rule']==r['rule'] and (r['scope']=='ALL_FOUR' or x['instrument']==r['scope']) and x['exit_time'].year==2024]
        rest=[x for x in x if x['exit_time'].month!=11];m=I.metrics(x,I.CALENDAR[12:]);ex=I.metrics(rest,[m for m in I.CALENDAR[12:] if m!='2024-11'])
        actual.append({k:r[k] for k in ('version','rule','scope')}|{'year':2024,'full_PF':m['gross_PF'],'full_R':m['gross_R'],
            'november_closed':len(x)-len(rest),'november_R':sum(x['gross_R'] for x in x if x['exit_time'].month==11),
            'ex_november_closed':len(rest),'ex_november_PF':ex['gross_PF'],'ex_november_R':ex['gross_R'],'ex_november_drawdown_R':ex['max_drawdown_closed_R']})
    c.rows(actual,expected,'november_dependence',['version','rule','scope'])
    eq,top,runs=[],[],[]
    for v in I.VERSIONS:
        for rule in ('CONTROL','T1','T2'):
            for scope in ('ALL_FOUR',*I.SYMBOLS):
                ids={'version':v,'rule':rule,'scope':scope}
                x=[x for x in t if x['version']==v and x['rule']==rule and (scope=='ALL_FOUR' or x['instrument']==scope)]
                if scope=='ALL_FOUR':
                    equity=peak=0.
                    for r in sorted(x,key=lambda x:(x['exit_time'],x['instrument'],x['trade_id'])):
                        equity+=r['gross_R'];peak=max(peak,equity)
                        eq.append(ids|{k:r[k] for k in ('exit_time','instrument','trade_id')}|{'trade_R':r['gross_R'],'cumulative_closed_R':equity,'drawdown_R':peak-equity})
                for n in (5,10):
                    wins=sorted((r for r in x if r['gross_R']>0),key=lambda r:(-r['gross_R'],r['instrument'],r['trade_id']))[:n]
                    for rank,r in enumerate(wins,1):top.append(ids|{'top_n':n,'rank':rank}|{k:r[k] for k in ('instrument','trade_id','entry_time','exit_time','gross_R')})
                monthly={m:sum(r['gross_R'] for r in x if r['exit_time'].strftime('%Y-%m')==m) for m in I.CALENDAR};run=[]
                for m,val in list(monthly.items())+[('END',0)]:
                    if val<0:run.append(m)
                    elif run:
                        runs.append(ids|{'first_month':run[0],'last_month':run[-1],'months':len(run),'gross_R':sum(monthly[x] for x in run)});run=[]
    for name,rows,keys in [('closed_equity',eq,['version','rule','exit_time','instrument','trade_id']),
        ('top_winners',top,['version','rule','scope','top_n','rank']),('losing_month_runs',runs,['version','rule','scope','first_month'])]:
        c.rows(rows,I.reference(FOLDER+'results/'+name+'.csv'),name,keys)

def diagnostics_audit(c,t,o,e,g,frames):
    funnel,hours,gaps,holding,lineage,new,changes,winners=[],[],[],[],[],[],[],[]
    key=lambda r:(r['instrument'],r['direction'],r['entry_time'])
    def percentile(x,p):
        x=sorted(x);n=(len(x)-1)*p;lo=int(n);hi=min(lo+1,len(x)-1)
        return x[lo]+(x[hi]-x[lo])*(n-lo)
    for v in I.VERSIONS:
        controls=[r for r in t if r['version']==v and r['rule']=='CONTROL']
        control_keys={key(r) for r in controls}|{key(r) for r in o if r['version']==v and r['rule']=='CONTROL'}
        ce={(r['instrument'],r['signal_time']):r for r in e if r['version']==v and r['rule']=='CONTROL'}
        for rule in ('CONTROL','T1','T2'):
            entries=[r for r in e if r['version']==v and r['rule']==rule];gg=[r for r in g if r['version']==v and r['rule']==rule]
            trades=[r for r in t if r['version']==v and r['rule']==rule]
            for scope in ('ALL_FOUR',*I.SYMBOLS):
                symbols=I.SYMBOLS if scope=='ALL_FOUR' else (scope,)
                for year in ('ALL',2023,2024):
                    q=[r for r in entries if r['instrument'] in symbols and (year=='ALL' or r['signal_time'].year==year)]
                    gs=[r for r in gg if r['instrument'] in symbols and (year=='ALL' or r['current_close'].year==year)]
                    ts=[r for r in trades if r['instrument'] in symbols and (year=='ALL' or r['exit_time'].year==year)]
                    ids={'version':v,'rule':rule,'scope':scope,'year':year};accepted=sum(r['entry_accepted'] for r in q)
                    rejected=sum(not r['rule_pass'] for r in q);busy=sum(r['rule_pass'] and r['position_occupied'] for r in q)
                    funnel.append(ids|{'original_signals':len(q),'rule_forbidden_signals':rejected,
                        'rule_forbidden_when_flat':sum(not r['rule_pass'] and not r['position_occupied'] for r in q),
                        'rule_forbidden_and_busy':sum(not r['rule_pass'] and r['position_occupied'] for r in q),
                        'accepted_entries':accepted,'allowed_skipped_position_busy':busy,'all_busy_signals':sum(r['position_occupied'] for r in q),
                        'partition_check':len(q)==accepted+rejected+busy})
                    gaps.append(ids|{'observed_gaps_gt_15min':sum(r['reason']=='OBSERVED_GAP_GT_15_MIN' for r in gs),
                        'no_previous_bars':sum(r['reason']=='NO_PREVIOUS_OBSERVED_CLOSE' for r in gs),
                        'cross_close_date_gaps':sum(r['cross_date'] for r in gs),'cross_observed_open_date_gaps':sum(r['cross_observed_open_date'] for r in gs),
                        'signals_on_first_bar_after_gap':sum(r['original_signal']!=0 and r['reason']=='OBSERVED_GAP_GT_15_MIN' for r in gs),
                        'signals_without_previous':sum(r['original_signal']!=0 and r['reason']=='NO_PREVIOUS_OBSERVED_CLOSE' for r in gs),
                        'blocked_gap_signals':sum(r['rule_reason']=='FIRST_BAR_AFTER_OBSERVED_GAP' for r in q),
                        'blocked_no_previous_signals':sum(r['rule_reason']=='NO_PREVIOUS_OBSERVED_CLOSE' for r in q)})
                    days=[{b['at'].date() for b in frames[s] if year=='ALL' or b['at'].year==year} for s in symbols]
                    instrument_days=sum(map(len,days));portfolio_days=len(set.union(*days))
                    op=[r for r in o if r['version']==v and r['rule']==rule and r['instrument'] in symbols and (year=='ALL' or r['entry_time'].year==year)]
                    minutes=[r['holding_minutes'] for r in ts]
                    holding.append(ids|{'closed_count':len(ts),'terminal_open_entry_cohort_count':len(op),
                        'holding_minutes_mean':sum(minutes)/len(minutes) if minutes else None,
                        'holding_minutes_median':median(minutes) if minutes else None,'holding_minutes_p90':percentile(minutes,.9) if minutes else None,
                        'bars_held_median':median([r['bars_held'] for r in ts]) if ts else None,
                        'accepted_entries':accepted,'observed_instrument_days':instrument_days,'observed_portfolio_days':portfolio_days,
                        'entries_per_observed_portfolio_day':accepted/portfolio_days if portfolio_days else None,
                        'entries_per_observed_instrument_day':accepted/instrument_days if instrument_days else None,
                        'closed_with_observed_overnight_gap':sum(r['observed_overnight_gaps_exposed']>0 for r in ts),
                        'closed_with_observed_overnight_gap_share':sum(r['observed_overnight_gaps_exposed']>0 for r in ts)/len(ts) if ts else None,
                        'total_observed_overnight_gap_exposures':sum(r['observed_overnight_gaps_exposed'] for r in ts)})
                if rule=='T1':
                    for hour in range(24):
                        q=[r for r in entries if r['instrument'] in symbols and r['moscow_hour']==hour]
                        hours.append({'version':v,'scope':scope,'moscow_hour':hour,'original_signals':len(q),
                            'forbidden':sum(not r['rule_pass'] for r in q),'forbidden_flat':sum(not r['rule_pass'] and not r['position_occupied'] for r in q),
                            'forbidden_busy':sum(not r['rule_pass'] and r['position_occupied'] for r in q)})
            if rule=='CONTROL':continue
            lookup={key(r):r for r in trades};decisions={(r['instrument'],r['signal_time']):r for r in entries};local=[]
            for r in controls:
                match=lookup.get(key(r));dec=decisions[(r['instrument'],r['entry_time'])]
                row={'version':v,'rule':rule,'instrument':r['instrument'],'direction':r['direction'],
                    'control_trade_id':r['trade_id'],'control_entry_time':r['entry_time'],'control_exit_time':r['exit_time'],
                    'control_gross_R':r['gross_R'],'control_winner_ge_2R':r['gross_R']>=2,
                    'match_status':'CLOSED_MATCH' if match else 'LOST_ENTRY','variant_trade_id':match['trade_id'] if match else None,
                    'variant_gross_R':match['gross_R'] if match else None,'decision_reason':dec['decision_reason'],
                    'rule_reason':dec['rule_reason'],'occupied_trade_id':dec['occupied_trade_id'],
                    'outcome_preserved':bool(match and abs(match['gross_R']-r['gross_R'])<=1e-8)}
                local.append(row);lineage.append(row)
            news=[r for r in trades if key(r) not in control_keys];new.extend(news)
            for r in entries:
                ctrl=ce[(r['instrument'],r['signal_time'])]
                if r['entry_accepted']!=ctrl['entry_accepted'] or r['position_occupied']!=ctrl['position_occupied']:
                    changes.append({'version':v,'rule':rule,'instrument':r['instrument'],'signal_time':r['signal_time'],
                        'direction':r['direction'],'control_accepted':ctrl['entry_accepted'],'variant_accepted':r['entry_accepted'],
                        'control_busy':ctrl['position_occupied'],'variant_busy':r['position_occupied'],'variant_rule_pass':r['rule_pass'],
                        'variant_reason':r['decision_reason'],'control_occupied_trade_id':ctrl['occupied_trade_id'],'variant_occupied_trade_id':r['occupied_trade_id']})
            for scope in ('ALL_FOUR',*I.SYMBOLS):
                for year in ('ALL',2023,2024):
                    ss=[r for r in local if (scope=='ALL_FOUR' or r['instrument']==scope) and (year=='ALL' or r['control_exit_time'].year==year)]
                    nn=[r for r in news if (scope=='ALL_FOUR' or r['instrument']==scope) and (year=='ALL' or r['exit_time'].year==year)]
                    ww=[r for r in ss if r['control_winner_ge_2R']];lost=[r for r in ss if r['match_status']=='LOST_ENTRY']
                    winners.append({'version':v,'rule':rule,'scope':scope,'control_exit_year':year,
                        'control_large_winners_ge_2R':len(ww),'large_winners_preserved':sum(r['outcome_preserved'] for r in ww),
                        'large_winners_lost':sum(r['match_status']=='LOST_ENTRY' for r in ww),
                        'lost_large_winner_R':sum(r['control_gross_R'] for r in ww if r['match_status']=='LOST_ENTRY'),
                        'lost_positive_R':sum(r['control_gross_R'] for r in lost if r['control_gross_R']>0),
                        'removed_negative_R_volume':-sum(r['control_gross_R'] for r in lost if r['control_gross_R']<0),
                        'lost_entry_rule_blocked':sum(r['decision_reason'] in ('RULE_BLOCKED','RULE_AND_OCCUPIED') for r in lost),
                        'lost_entry_busy_only':sum(r['decision_reason']=='POSITION_OCCUPIED' for r in lost),
                        'new_closed_entries':len(nn),'new_closed_losses':sum(r['gross_R']<0 for r in nn),
                        'new_closed_gross_R':sum(r['gross_R'] for r in nn),'new_losses_R_volume':-sum(r['gross_R'] for r in nn if r['gross_R']<0)})
    for name,rows,keys in [('signal_funnel',funnel,['version','rule','scope','year']),('t1_blocked_hours',hours,['version','scope','moscow_hour']),
        ('t2_gap_summary',gaps,['version','rule','scope','year']),('holding_frequency',holding,['version','rule','scope','year']),
        ('trade_lineage',lineage,['version','rule','instrument','control_entry_time']),('new_entries',new,['version','rule','instrument','entry_time']),
        ('winner_comparison',winners,['version','rule','scope','control_exit_year']),('chronology_changes',changes,['version','rule','instrument','signal_time'])]:
        c.rows(rows,I.reference(FOLDER+'results/'+name+'.csv'),name,keys)

def run(root,output):
    output.mkdir(parents=True,exist_ok=True)
    assert output.resolve().is_relative_to(I.HERE)
    meta=verify_git();frames,sources=I.load_sources(root);c=I.Comparison()
    t,o,d,e,g,snap=[],[],[],[],[],[]
    for rule in ('CONTROL','T1','T2'):
        for v in I.VERSIONS:
            for s in I.SYMBOLS:
                trades,op,stops,entries,gaps,sn=I.simulate(frames[s],s,v,rule)
                t.extend(trades);d.extend(stops);e.extend(entries);g.extend(gaps);snap.extend(sn)
                if op:o.append(op)
    c.rows(t,I.reference(FOLDER+'results/trades.csv'),'499_trades',['version','rule','instrument','entry_time'])
    c.rows(d,I.reference(FOLDER+'results/stop_decisions.csv'),'499_stops',['version','rule','instrument','bar_close_time'])
    c.rows(e,I.reference(FOLDER+'results/entry_opportunities.csv'),'499_entries',['version','rule','instrument','signal_time'])
    c.rows(g,I.reference(FOLDER+'results/observed_gaps.csv'),'499_gaps',['version','rule','instrument','current_close'])
    c.rows(o,json.loads(I.historical(FOLDER+'results/OPEN_POSITIONS.json')),'499_OPEN',['version','rule','instrument'])
    c.rows(snap,json.loads(I.historical(FOLDER+'results/PERIOD_END_OPEN_POSITIONS.json')),'499_period_OPEN',['version','rule','instrument','month'])
    control=[r for r in t if r['rule']=='CONTROL'];co=[r for r in o if r['rule']=='CONTROL']
    for label,path in [('490','IntradayLab/t3_m15_forever_v1/trades.csv'),('495','IntradayLab/t3_m15_entry_regime_v1/results/trades_CONTROL.csv')]:
        c.rows(control,I.reference(path),label+'_CONTROL',['version','instrument','entry_time'],('C1_R','net_R','c1_price_unit','initial_risk_ticks'))
    for label,path in [('490','IntradayLab/t3_m15_forever_v1/OPEN_POSITIONS.json'),('495','IntradayLab/t3_m15_entry_regime_v1/results/CONTROL_OPEN_POSITIONS.json')]:
        c.rows(co,json.loads(I.historical(path)),label+'_OPEN',['version','instrument'],('exit_C1_and_funding',))
    report_audit(c,t,o,snap,frames);diagnostics_audit(c,t,o,e,g,frames)
    counts=[{'version':v,'rule':rule,'closed':sum(r['version']==v and r['rule']==rule for r in t),
        'terminal_OPEN':sum(r['version']==v and r['rule']==rule for r in o)} for v in I.VERSIONS for rule in ('CONTROL','T1','T2')]
    for v,n in [('BASELINE',741),('OPTIMIZED',701)]:c.value(sum(r['version']==v for r in control),n,'CONTROL_EXPECTED',v,'closed')
    c.value(len(co),2,'CONTROL_EXPECTED',-1,'OPEN')
    for name,rows in [('trades',t),('stop_decisions',d),('entry_opportunities',e),('observed_gaps',g)]:I.write_csv(output/(name+'.csv'),rows)
    I.write_json(output/'OPEN_POSITIONS.json',o);I.write_json(output/'PERIOD_END_OPEN_POSITIONS.json',snap)
    I.write_csv(output/'DISCREPANCIES.csv',c.diffs,['table','row','field','actual','expected'])
    result={'status':'PASS' if not c.diffs else 'FAIL','FIRST_GATE':True,'combination_executed':False,
        'labels':I.LABEL,'2023_2024':'DEVELOPMENT_EXPOSED','independence':'new stdlib parser, recurrences, forward H1 publication, position machine and metrics; no prior engine/metrics/audit imports',
        'historical_Close_fill':'UNVERIFIED_ASSUMPTION','numeric_absolute_tolerance':1e-8,'fields_compared':c.fields,
        'discrepancies':len(c.diffs),'counts':counts,'tables':c.tables,'maximum_numeric_differences':c.maxima,
        'source_manifest':sources,'git_and_freeze':meta,'future_OHLC_parsed':False,
        'implementation_SHA256':{p.name:I.file_sha(p) for p in (I.HERE/'independent.py',I.HERE/'audit_499.py')}}
    I.write_json(output/'AUDIT_RESULT.json',result)
    print(json.dumps({k:result[k] for k in ('status','fields_compared','discrepancies','counts')}))
    assert result['status']=='PASS','FIRST_GATE_FAIL_COMBINATION_FORBIDDEN'
    return result

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--data-root',type=Path,required=True);p.add_argument('--output',type=Path,default=I.HERE/'audit_499')
    a=p.parse_args()
    try:run(a.data_root,a.output)
    except Exception as ex:
        a.output.mkdir(parents=True,exist_ok=True)
        I.write_json(a.output/'BLOCKER.json',{'status':'BLOCKED','error':str(ex),'traceback':traceback.format_exc(),
            'combination_executed':False,'labels':I.LABEL,'2023_2024':'DEVELOPMENT_EXPOSED'})
        raise
