"""Separate original-value legacy replay, then explicit V2 control comparison."""
import csv
from datetime import date
import json
from IntradayLab.core.backtester import Backtester
from IntradayLab.core.calendar import MarketRules
from IntradayLab.core.data_loader import load_market_data
from IntradayLab.core.reports import csv_write,dump
from IntradayLab.strategies.level_rejection import LevelRejection
from .contract import ROOT,bounded_reads,digest


def read(path):
    with path.open() as f:return list(csv.DictReader(f))


def run(data_root,output,policy,freeze,loaded=None):
    cfg=json.loads((ROOT/'IntradayLab/config/level_rejection_2023_m5_v1.json').read_text())
    cfg=dict(cfg,instruments=policy['instruments'],inputs=policy['inputs'])
    rules=MarketRules(cfg)
    if loaded is None:
        with bounded_reads(data_root,policy) as reads:data,receipts=load_market_data(data_root,cfg,rules)
    else:
        data,receipts,reads=loaded
    archived=ROOT/'IntradayLab/results/level_rejection_2023_m5_v1'
    control=policy['historical_control_id'];details={};comparisons=[]
    keys=('direction','signal_at','entry_at','entry_price','entry_tick','stop','take','risk',
        'exit_reason','exit_at','exit_interval_start','exit_interval_end','resolved_at','exit_price','exit_tick',
        'gross','gross_R','cost_c1','cost_R','net_c1','net_R_c1','planned_C1','d_full','d_legacy',
        'planned_net_to_net_R','realized_net_to_net_R')
    for symbol in policy['instruments']:
        ss,tt,dd=Backtester(rules,daily_trade_deadline_clock='17:00').run(LevelRejection(cfg['parameters']),
            symbol,data[symbol],start=date(2023,1,1),end_exclusive=date(2024,1,1))
        folder=output/'baseline_replay'/symbol
        folder.mkdir(parents=True)
        for name,rows in [('signals',ss),('trades',tt),('days',dd)]:csv_write(folder/(name+'.csv'),rows)
        checks=0
        for name in ('signals','trades','days'):
            old=[r for r in read(archived/(name+'.csv')) if r['instrument']==symbol]
            current=read(folder/(name+'.csv'))
            if len(old)!=len(current):raise AssertionError('LEGACY_REPLAY_ROW_COUNT '+symbol+' '+name)
            for x,y in zip(old,current):
                for k,v in x.items():
                    if v!=y.get(k,''):raise AssertionError('LEGACY_REPLAY_FIELD '+symbol+' '+name+' '+k+' '+str((v,y.get(k))))
                    checks+=1
        old={t['signal_id']:t for t in read(folder/'trades.csv') if t['status']=='CLOSED'}
        v2folder=output/'evaluations'/control/symbol
        new={t['signal_id']:t for t in read(v2folder/'trades.csv')}
        common=sorted(set(old)&set(new));shared_checks=0
        for ident in sorted(set(old)|set(new)):
            x,y=old.get(ident),new.get(ident)
            if x and y:
                for k in keys:
                    if x.get(k,'')!=y.get(k,''):raise AssertionError('COMMON_CLOSED_DIFFERENCE '+symbol+' '+ident+' '+k)
                    shared_checks+=1
            comparisons.append(dict(instrument=symbol,signal_id=ident,comparison='IDENTICAL_COMMON_CLOSED' if x and y else 'LEGACY_ONLY_CLOSED' if x else 'V2_ONLY_CLOSED',
                baseline_status=x['status'] if x else '',v2_status=y['status'] if y else '',
                baseline_net_R=x['net_R_c1'] if x else '',v2_net_R=y['net_R_c1'] if y else '',
                explanation='' if x and y else 'DATA_GAP_SKIP_V2 explicitly changes missing-entry day blocking; separate cohort, no imputed closure'))
        skips=read(v2folder/'data_gap_skips.csv');excluded=read(v2folder/'data_quality_exclusions.csv')
        details[symbol]=dict(legacy_CLOSED=len(old),legacy_UNKNOWN=sum(t['status']=='UNKNOWN' for t in tt),
            v2_CLOSED=len(new),v2_SKIP=len(skips),v2_EXCLUDED=len(excluded),common_CLOSED=len(common),
            legacy_only_ids=sorted(set(old)-set(new)),v2_only_ids=sorted(set(new)-set(old)),
            original_saved_fields_exact=checks,common_closed_economic_fields_exact=shared_checks)
        if len(old)!=policy['instrument_admission'][symbol]['CLOSED']:raise AssertionError('ORIGINAL_BASELINE_SAMPLE')
    csv_write(output/'baseline_comparison.csv',comparisons)
    summary=dict(status='PASS',original_strategy_config_and_results_unchanged=True,freeze_commit=freeze,instruments=details,
        policy_difference='LEGACY_UNKNOWN -> DATA_GAP_SKIP_V2; missing execution Open SKIP does not block day; filled exposure EXCLUDED still blocks remainder day',
        input_provenance=receipts,actual_python_read_receipts=reads,bytes_2024_plus_read=0)
    dump(output/'baseline_replay.json',summary)
    return summary
