#!/usr/bin/env python3
"""Rebuild compact read-only comparisons from immutable experiment outputs."""
import csv
import gzip
import json
from collections import Counter,defaultdict
from decimal import Decimal as D
from pathlib import Path
from stage2_architecture_analysis import LAB
from independent_corrective_review import write_csv

DEST=LAB/'results/stage2_architecture_review'
FOLDERS=[LAB/'results/stage2_complete_architectures_v1',LAB/'results/stage2_vwap_payable_cap_v1']

def table(path):
    opener=path.open if path.exists() else lambda **kw:gzip.open(str(path)+'.gz','rt',**kw)
    with opener(newline='') as f:return list(csv.DictReader(f))


def run():
    records=[];months=[];freq=Counter();days=Counter();exit_counts=Counter();r_bins=Counter();pairs=[]
    for folder in FOLDERS:
        data=json.loads((folder/'results.json').read_text())['runs']
        by={(r['architecture'],r['scenario'],r['run']):r for r in data}
        for f in table(folder/'daily_frequency.csv'):
            k=f['architecture'],f['scenario'],f['run'];days[k]+=1;freq[k]+=int(f['model_entries'])
        for r in data:
            if r['scenario']!='C1_T10':continue
            k=r['architecture'],r['scenario'],r['run'];other=by[r['architecture'],'C1_T15_DELAY',r['run']]
            fields=['architecture','run','strategy','instrument','trades','closed_accounted_trades','unresolved',
                'closed_only_gross','closed_only_c1','closed_only_net_c1','net_PF_closed_diagnostic',
                'net_expectancy_closed_diagnostic','mean_net_R_closed_diagnostic','mean_win','mean_loss_magnitude',
                'closed_only_drawdown_price_units','closed_subset_positive_months','closed_subset_negative_months',
                'months_with_closed_trades','complete_calendar_months','complete_positive_calendar_months',
                'complete_negative_calendar_months','no_coverage_months','incomplete_covered_months',
                'known_negative_calendar_month_streak_lower_bound','Net','full_PF','Net_null_reason']
            row={x:r.get(x) for x in fields}
            row.update(entries_per_approved_calendar_day=D(freq[k])/days[k],approved_calendar_days=days[k],
                delay_closed=other['closed_accounted_trades'],delay_unknown=other['unresolved'],
                delay_net=other['closed_only_net_c1'],delay_PF=other['net_PF_closed_diagnostic'],
                C2_net=r['C2_closed_net_stress'],C2_PF=r['C2_PF_closed_stress'])
            records.append(row)
        monthly_fields=['architecture','run','strategy','instrument','period','direction','trades','closed_accounted_trades',
            'unresolved','coverage_status','metric_status','full_period_accounted','Net','full_PF','Net_null_reason',
            'closed_only_net_c1','net_PF_closed_diagnostic','net_expectancy_closed_diagnostic','closed_subset_outcome',
            'calendar_month_outcome','mean_net_R_closed_diagnostic','closed_only_drawdown_price_units',
            'stop_count','take_count','BE_count','trailing_count']
        months += [{k:r[k] for k in monthly_fields} for r in table(folder/'metrics.csv') if r['scenario']=='C1_T10' and r['group']=='MONTH']
        for r in table(folder/'trade_ledger.csv'):
            k=r['architecture'],r['scenario'],r['run'];exit_counts[k+(r['exit_reason'],)]+=1
            if r['net_R']=='':bucket='UNKNOWN'
            else:
                v=D(r['net_R']);bucket='<=-1R' if v<=-1 else '(-1,0)R' if v<0 else '0R' if v==0 else '(0,0.5)R' if v<D('.5') else '[0.5,1)R' if v<1 else '[1,2)R' if v<2 else '[2,3)R' if v<3 else '>=3R'
            r_bins[k+(bucket,)]+=1
        pairs+=table(folder/'paired_contribution.csv')
    grouped=defaultdict(list)
    for r in pairs:grouped[r['run'],r['reference_architecture'],r['candidate_architecture']].append(r)
    pair_summary=[]
    for k,rs in sorted(grouped.items()):
        valid=[r for r in rs if r['paired_net_delta']!='']
        rec={'run':k[0],'reference_architecture':k[1],'candidate_architecture':k[2],
            'matched_entries':len(rs),'exact_entry_both_known':len(valid),'excluded_unknown_or_changed_entry':len(rs)-len(valid),
            'paired_net_delta':sum((D(r['paired_net_delta']) for r in valid),D(0))}
        for field in ['baseline_winner_became_loser','baseline_loser_became_winner','profit_reduced','loss_reduced']:
            rec[field]=sum(r[field]=='True' for r in valid)
        pair_summary.append(rec)
    DEST.mkdir(exist_ok=True,parents=True)
    for name,rows in [('architecture_comparison.csv',records),('monthly_results.csv',months),('paired_summary.csv',pair_summary),
        ('exit_counts.csv',[{'architecture':k[0],'scenario':k[1],'run':k[2],'exit_reason':k[3],'count':v} for k,v in sorted(exit_counts.items())]),
        ('R_distribution.csv',[{'architecture':k[0],'scenario':k[1],'run':k[2],'net_R_bucket':k[3],'count':v,
            'R_basis':'Each architecture initial risk; not equal capital risk; unknown excluded from numeric bins'} for k,v in sorted(r_bins.items())])]:write_csv(DEST/name,rows)
    # Reporting-only correction: independent seed simulation ends at its first
    # unknown continuation. Raw frozen rows retain the pre-gap scalar exposure
    # fields; these do not establish remaining quantity after an unknown Stop.
    # Publish an authoritative null view without altering prices, P&L or replay.
    unknowns=[r for r in table(LAB/'results/stage2_exit_only_ablation_v1/trade_ledger.csv') if r['status']=='UNRESOLVED']
    corrected=[{'run':r['run'],'signal_id':r['signal_id'],'status':'UNRESOLVED',
        'entry':r['entry'],'c1_entry_known':r['c1_entry'],'exit':None,
        'gross_price_pnl':None,'c1_exit':None,'c1_total':None,'net_model_c1':None,
        'exit_filled_model_units':None,'residual_model_units':None,
        'possible_residual_model_units':None,'residual_upper_bound_abstract_units':1,
        'model_flat_confirmed':False,
        'reason':'UNKNOWN_COUNTERFACTUAL_PATH; inherited pre-gap scalar fields are not post-gap exposure evidence'} for r in unknowns]
    write_csv(DEST/'exit_only_unknown_accounting_correction.csv',corrected)
    (DEST/'reporting_notes.json').write_text(json.dumps({
        'exit_only_unknown_accounting':'Authoritative correction CSV nulls post-gap exit/residual quantity; raw frozen seed outputs retained. No change to decisions, P&L or unknown count.',
        'indicator_clock':'Raw indicator_available_at is diagnostic nominal minimum t+10. Actual causal strategy clocks are available_at, ready_at and amendment decided_at, including T15.'},sort_keys=True,indent=2)+'\n')
    print('48 primary comparisons; 1728 monthly direction rows; diagnostic R/exit/paired tables; 2 unknown seed accounting corrections')

if __name__=='__main__':run()
