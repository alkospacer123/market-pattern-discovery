"""Independent Stage 6.7 audit, reconstructed from the frozen Stage 6.6 registry."""
from __future__ import annotations
import hashlib, json
from pathlib import Path
import pandas as pd

HERE=Path(__file__).resolve().parent; SOURCE=HERE.parent/'stage6_unified_candidate_comparison'/'portfolio_trade_scaling_registry.csv'
LIFES=('baseline','walk_forward','historical_true_oos')

def stream_hash(frame, members, weight, risk):
    f=frame[frame.instrument.isin(members)].copy(); output=[]
    for life in LIFES:
        equity=100.; active={}; events=[]
        for x in f[f.lifecycle==life].to_dict('records'):
            events.append((pd.Timestamp(x['entry_time']),0,x['source_trade_id'],x))
            events.append((pd.Timestamp(x['exit_time']),1,x['source_trade_id'],x))
        for _,kind,tid,x in sorted(events,key=lambda z:(z[0],z[1],z[2])):
            if not kind: active[tid]=(equity,equity*risk*weight,x)
            else:
                sized,cash,row=active.pop(tid); pnl=cash*float(row['strategy_R']); equity+=pnl
                output.append((tid,life,row['instrument'],row['entry_time'],row['exit_time'],float(row['strategy_R']),weight,sized,cash,pnl,equity))
    # Producer's canonical serialization uses stable lexical lifecycle ordering.
    output.sort(key=lambda x:(x[1],x[4],x[2],x[0]))
    text=''.join('|'.join(f'{v:.12f}' if isinstance(v,float) else str(v) for v in row)+'\n' for row in output)
    return hashlib.sha256(text.encode()).hexdigest(),len(output)

def audit(path=HERE):
    master=pd.read_csv(path/'master_220_equity_cases.csv'); rm=pd.read_csv(path/'master_110_load_cases_R.csv'); hs=pd.read_csv(path/'equity_execution_hashes.csv')
    src=pd.read_csv(SOURCE,keep_default_na=False); failures=[]
    checks={'configuration_count':master.configuration_id.nunique()==55,'R_case_count':len(rm)==110,'equity_case_count':len(master)==220,'execution_hash_count':len(hs)==220,'risk_cases_unique':master.case_id.nunique()==220}
    for row in master.itertuples():
        members=row.instruments.split('+'); w=1/row.basket_size if row.load_mode=='NORMALIZED' else 1.; risk=row.base_risk_pct/100
        got,n=stream_hash(src[src.variant==row.variant],members,w,risk); expected=hs.loc[hs.case_id==row.case_id].iloc[0]
        if got!=expected.canonical_event_sha256 or n!=expected.event_count: failures.append(row.case_id)
    # Independent R identities and Stage 6.6 reconciliation.
    s66=pd.read_csv(HERE.parent/'stage6_unified_candidate_comparison'/'yearly_metrics.csv')
    merged=rm[rm.load_mode=='NORMALIZED'].merge(s66[['configuration_id','period_label','net_R']].pivot(index='configuration_id',columns='period_label',values='net_R').reset_index(),on='configuration_id')
    maps={'R_2023':'BASELINE_2023','R_2024':'BASELINE_2024','WF24_R':'WF24','R_2025':'OOS2025','R_2026_YTD':'OOS2026_YTD'}
    checks['stage6_6_normalized_reconciliation']=all((merged[a]-merged[b]).abs().max()<1e-8 for a,b in maps.items())
    both=rm.pivot(index='configuration_id',columns='load_mode')
    checks['full_scaling_reconciliation']=all(((both[(c,'FULL')]-both[(c,'NORMALIZED')]*both[('basket_size','FULL')]).abs().max()<1e-7) for c in maps)
    checks['all_execution_hashes_match']=not failures
    checks['annual_and_stability_fields_present']=all(x in master for x in ['return_2023_pct','return_2024_pct','return_2025_pct','positive_quarter_share','positive_month_share','max_realized_equity_DD_pct','production_eligible','pareto_frontier','reference_rank'])
    checks['instrument_gate_recomputed']=master.production_eligible.equals(master.all_portfolio_years_positive & master.all_instrument_years_positive & master.provenance_pass & master.deterministic_reconstruction_pass)
    status='PASS' if all(checks.values()) else 'FAIL'
    result={'status':status,'independent_reconstruction':True,'checks':checks,'execution_hash_mismatches':failures,'counts':{'configurations':55,'R_cases':len(rm),'equity_cases':len(master)}}
    (path/'independent_audit_result.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    if status!='PASS': raise AssertionError(result)
    return result
if __name__=='__main__': audit()
