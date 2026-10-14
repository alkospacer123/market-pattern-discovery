"""Read journals ONLY after independent full replay and scalar verification."""
import csv,gzip,hashlib,io,json,math
from datetime import datetime
from io_utils import clean,write_json,write_csv,read_csv
from source import git,SPEC

def reconcile(models,out):
    marker=json.loads((out/'independent_run_completed.json').read_text())
    assert marker['independent_feature_and_execution_verification_completed']
    checks=0;differences=[];receipts=[];max_error=0.;unrepresented=set()
    def value(actual,expected,context,field):
        nonlocal checks,max_error
        checks+=1;actual=clean(actual)
        if isinstance(actual,(float,int)) and not isinstance(actual,bool):
            delta=abs(actual-float(expected));max_error=max(max_error,delta);ok=delta<=1e-8
        elif actual is None:ok=expected==''
        else:ok=str(actual)==expected
        if not ok:differences.append(dict(context=context,field=field,independent=str(actual),published=expected))
    reason_map=dict(RULE_AND_OCCUPIED='OUTSIDE_T1_AND_OCCUPIED',RULE_BLOCKED='OUTSIDE_T1',SKIPPED_MISSING_ADJACENT_OPEN='MISSING_ADJACENT_OPEN')
    for mode,data in models.items():
        model='T1_'+mode+'_TRAIL_3p5'
        for table in ('trades','entries','stops','OPEN','snapshots'):
            path='IntradayLab/t3_m15_build_comparison_2023_2026_v1/results/journals/'+model+'/'+table+'.csv.gz'
            raw=git('show',SPEC['pr514']+':'+path);unpacked=gzip.decompress(raw)
            rows=list(csv.DictReader(io.StringIO(unpacked.decode())))
            ours=data['signals' if table=='entries' else table]
            key=lambda r:tuple(str(clean(r[k]) or '') for k in (('instrument','signal_time','direction') if table=='entries' else ('instrument','trade_id','bar_close') if table=='stops' else ('instrument','trade_id','month') if table=='snapshots' else ('instrument','trade_id')))
            if table=='stops':rows=[dict(r,bar_close=r['bar_close_time']) for r in rows]
            ours=sorted(ours,key=key);rows=sorted(rows,key=key)
            value(len(ours),str(len(rows)),model+'/'+table,'row_count')
            for i,(a,b) in enumerate(zip(ours,rows)):
                for field,actual in a.items():
                    mapped={'model':'build_id','reason':'decision_reason','initial_stop':'candidate_initial_stop'} if table=='entries' else {'model':'build_id','bar_close':'bar_close_time','ATR':'ATR_at_close','observed_gap':'observed_gap_before_bar','next_stop':'active_stop_next_bar','proposal':'trail_proposal'} if table=='stops' else {'model':'build_id','unrealized_gross_R':'unrealized_gross_R_at_last_close'}
                    target=mapped.get(field,field)
                    if mode=='SIGNAL_CLOSE' and table in ('trades','snapshots'):
                        target={'signal_time':'entry_time','signal_close':'entry_price'}.get(field,target)
                    if table=='entries' and field=='signal_close':continue # Original schema omits it; trades/source feature audit covers it.
                    if table=='entries' and field in ('entry_price','initial_stop') and not a['entry_accepted']:continue # Original candidate diagnostics are not fills.
                    if table=='snapshots' and field=='status':continue # Same OPEN semantics, different descriptive label.
                    if target not in b and ((table=='entries' and field in ('execution_bar_close','next_observed_close') and actual is None) or (table=='snapshots' and field in ('ATR','H1AvailableAt'))):
                        unrepresented.add(model+'/'+table+'/'+field);continue
                    assert target in b,(table,field,target)
                    expected=b[target]
                    if field=='reason':expected=reason_map.get(expected,expected)
                    value(actual,expected,model+'/'+table+'/'+str(i),field)
            receipts.append(dict(model=model,table=table,path=path,ref=SPEC['pr514'],sha256=hashlib.sha256(raw).hexdigest(),uncompressed_sha256=hashlib.sha256(unpacked).hexdigest(),independent_rows=len(ours),published_rows=len(rows)))
    # PR517 is reporting only; compare only selected model rows, never replay other configurations.
    for filename,oursname in (('YEARLY_COMPARISON.csv','yearly_comparison.csv'),('BUILD_SUMMARY.csv','comparison_summary.csv')):
        raw=git('show',SPEC['pr517']+':IntradayLab/t3_m15_full_n4_catalog_v1/'+filename)
        selected=[r for r in csv.DictReader(io.StringIO(raw.decode())) if r['build_id'] in {'T1_'+m+'_TRAIL_3p5' for m in models}]
        ours=read_csv(out/oursname)
        receipts.append(dict(table='PR517/'+filename,ref=SPEC['pr517'],sha256=hashlib.sha256(raw).hexdigest(),selected_rows=len(selected)))
        # Columns differ across catalog schemas; exact mapping is explicit below.
        mapping={'gross_PF':'gross_PF','gross_R':'gross_R','CLOSED':'CLOSED','max_closed_R_DD':'max_DD_R','win_rate':'win_rate','mean_win_R':'mean_win_R','mean_loss_R':'mean_loss_R','expectancy_R':'expectancy_R','max_losing_streak':'max_loss_streak'}
        for a in ours:
            candidates=[r for r in selected if r['build_id']==a['model'] and ('year' not in a or r['year']==a['year'])]
            assert len(candidates)==1,(filename,a['model'],a.get('year'))
            for k,target in mapping.items():
                if target in candidates[0]:value(float(a[k]),candidates[0][target],filename+'/'+a['model'],k)
    write_csv(out/'published_differences.csv',differences,['context','field','independent','published'])
    result=dict(status='PASS' if not differences else 'FAIL',checked_fields=checks,max_abs_error=max_error,differences=len(differences),source_receipts=receipts,read_after_independent_completion=True,unrepresented_original_columns=sorted(unrepresented),schema_normalizations=['Blocked-signal candidate prices in original entries are diagnostics; compare actual accepted fills only','SIGNAL_CLOSE signal_time/signal_close inferred from entry_time/entry_price in original schema','RULE_BLOCKED/RULE_AND_OCCUPIED mapped to explicit OUTSIDE_T1 reasons','OPEN status descriptive text differs; positions and numeric states compared'],scope='Only the two requested build IDs')
    write_json(out/'published_reconciliation.json',result)
    assert not differences,differences[:10]
    return result
