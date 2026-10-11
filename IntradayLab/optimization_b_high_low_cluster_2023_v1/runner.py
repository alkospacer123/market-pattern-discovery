"""Exhaustive frozen 315 configurations /585 evaluations via existing Backtester/V2."""
import argparse
from datetime import date
import json
from pathlib import Path

from IntradayLab.core.backtester import Backtester
from IntradayLab.core.calendar import MarketRules
from IntradayLab.core.data_loader import load_market_data
from IntradayLab.core.reports import write_data_quality_reports,csv_write,dump
from IntradayLab.strategies.high_low_cluster_m5_optimization_b_v1 import HighLowClusterM5OptimizationB
from .contract import verify_freeze,grid,eligible,protected_check,output_guard,bounded_reads,digest,STUDY,RESULTS
from .aggregation import summaries,select,report


GEOMETRY_KEYS=('episode_id','level_type','boundary_touches','cluster_bars','cluster_min','cluster_max',
    'cluster_width_ticks','cluster_level','round_distance_ticks','signal_close','entry_distance_ticks','open_vs_close_ticks')

def enrich(result):
    from decimal import Decimal as D
    by={s['signal_id']:s for s in result.signals}
    for s in result.signals:
        op=s.get('entry_open')
        s['entry_distance_ticks']=s['direction']*(op-s['cluster_level'])/s['entry_tick'] if op is not None else None
        s['open_vs_close_ticks']=s['direction']*(op-s['signal_close'])/s['entry_tick'] if op is not None else None
    for t in result.trades+result.data_quality_exclusions:
        for k in GEOMETRY_KEYS:t[k]=by[t['signal_id']][k]
        t['holding_lower_minutes']=D(str((t['exit_interval_start']-t['entry_at']).total_seconds()/60)) if t['status']=='CLOSED' else None
        t['holding_upper_minutes']=D(str((t['exit_interval_end']-t['entry_at']).total_seconds()/60)) if t['status']=='CLOSED' else None


def diagnostics(target,result,spec):
    from .aggregation import economics
    for field,values in [('cluster_width_ticks',range(1,spec['maximum_width_ticks']+1)),
                         ('boundary_touches',range(2,spec['cluster_bars']+1)),
                         ('level_type',('ROUND_NEAR','ORDINARY_FAR'))]:
        rows=[]
        for v in values:
            ss=[s for s in result.signals if str(s[field])==str(v)]
            ts=[t for t in result.trades if str(t[field])==str(v)]
            rows.append(dict(diagnostic_field=field,value=v,detected=len(ss),
                signals=sum(s['base_reason']=='SIGNAL' for s in ss),
                accepted=sum(s['model_filled'] for s in ss),
                EXCLUDED=sum(str(t[field])==str(v) for t in result.data_quality_exclusions),
                **economics(ts),scope='DESCRIPTIVE_ONLY; no hindsight filter'))
        csv_write(target/(field+'_diagnostics.csv'),rows)

def run(data_root,output):
    policy,freeze,commitments=verify_freeze()
    output_guard(output);protected_check(policy)
    rules=MarketRules(policy)
    with bounded_reads(data_root,policy) as reads:
        data,receipts=load_market_data(data_root,policy,rules)
    output.mkdir(parents=True)
    dump(output/'input_provenance.json',dict(source_sha=policy['source_ref'],
        verified_prefixes=receipts,actual_python_read_receipts=reads,
        candle_rows_read=sum(r['candle_rows_read'] for r in reads),
        candle_bytes_read=sum(r['bytes_read'] for r in reads),bytes_2024_plus_read=0,rows_2024_plus_read=0))
    dump(output/'freeze_manifest.json',dict(freeze_commit=freeze,**commitments))
    candidates=[];monthly=[];directional=[];funnels=[]
    code_sha=digest(STUDY.parents[0]/'strategies/high_low_cluster_m5_optimization_b_v1.py')
    for config in grid(policy):
        ident=config['configuration_id']
        parameters={k:v for k,v in config.items() if k!='configuration_id'}
        for symbol in policy['instruments']:
            if not eligible(config,symbol):continue
            target=output/'evaluations'/ident/symbol
            strategy=HighLowClusterM5OptimizationB(parameters)
            result=Backtester(rules,entry_mode=policy['execution']['entry_mode'],
                data_gap_policy=policy['execution']['data_gap_policy'],cost_ticks_per_side=1,
                allow_entry_bar_take=False,session_flat_before_end_bars=1).run(
                    strategy,symbol,data[symbol],
                    start=date(2023,1,1),end_exclusive=date(2024,1,1))
            enrich(result)
            write_data_quality_reports(target,result,{symbol:data[symbol]},dict(policy,instruments=[symbol]),rules)
            csv_write(target/'episodes.csv',strategy.episode_records)
            diagnostics(target,result,config)
            csv_write(target/'rejected_nonfill.csv',[s for s in result.signals if s['status'] in ('REJECTED','NONFILL')])
            dump(target/'configuration.json',dict(configuration_id=ident,parameters=parameters,instrument=symbol,
                execution=policy['execution'],strategy_sha256=code_sha,source_sha=policy['source_ref'],
                source_blob=policy['inputs'][symbol]['blob'],freeze_commit=freeze))
            # Keep the common coverage report and exact economics as independent evidence.
            import csv
            cov=[]
            with (target/'coverage_report.csv').open() as stream:
                for row in csv.DictReader(stream):
                    for k in ('valid_bars','missing_bars','invalid_bars','accepted_entries','data_gap_skips','data_quality_excluded'):
                        row[k]=int(row[k])
                    cov.append(row)
            m,months,directions,funnel=summaries(config,symbol,result,cov,policy,freeze,code_sha)
            candidates.append(m);monthly.extend(months);directional.extend(directions);funnels.append(funnel)
        print(f'{ident}: completed {len(candidates)}/585',flush=True)
    assert len(candidates)==585
    neighborhood,selection=select(candidates,policy)
    for name,rows in [('all_candidates',candidates),('monthly_results',monthly),('direction_results',directional),
                      ('execution_funnel',funnels),('parameter_neighborhood',neighborhood)]:
        csv_write(output/(name+'.csv'),rows)
    dump(output/'selection_report.json',selection)
    (output/'Optimization_Report.md').write_text(report(policy,freeze,candidates,monthly,selection))
    return selection


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--data-root',type=Path,required=True);p.add_argument('--output',type=Path,default=RESULTS)
    a=p.parse_args();print(json.dumps(run(a.data_root,a.output),sort_keys=True))
