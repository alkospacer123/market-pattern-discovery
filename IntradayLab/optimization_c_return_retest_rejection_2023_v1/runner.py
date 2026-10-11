"""Run all 288 frozen C configurations through the unchanged shared Backtester."""
import argparse
from collections import Counter
from datetime import date
from decimal import Decimal as D
import json
from pathlib import Path
from IntradayLab.core.backtester import Backtester
from IntradayLab.core.calendar import MarketRules
from IntradayLab.core.data_loader import load_market_data
from IntradayLab.core.reports import write_data_quality_reports,csv_write,dump,data_quality_coverage
from IntradayLab.strategies.return_retest_rejection_m5_optimization_c_v1 import ReturnRetestRejectionM5OptimizationC
from .contract import verify_freeze,grid,protected_check,output_guard,bounded_reads,digest,STUDY,RESULTS
from .aggregation import summaries,select,economics
from .reporting import report


def diagnostics(result,events,spec):
    rows=[]
    for event in ('FIRST','RETREAT','SECOND','THIRD','RESET'):
        cohort=[e for e in events if e['event']==event]
        rows.append(dict(configuration_id=spec['configuration_id'],kind='EVENT',field=event,count=len(cohort),
            reset_reasons=dict(sorted(Counter(e.get('reason') for e in cohort if e.get('reason')).items()))))
    for field,values in (
        ('approach_count',[len(s['approach_starts']) for s in result.signals]),
        ('local_extreme_lookback',[len(e['previous_starts']) for e in events if e['event']=='FIRST']),
        ('zone_distance_ticks',[abs((v-s['level'])/s['signal_tick']) for s in result.signals for v in s['approach_extrema']]),
        ('retreat_depth_ticks',[v for s in result.signals for v in s['retreat_depth_ticks']]),
        ('approach_separation_bars',[v for s in result.signals for v in s['approach_separation_bars']]),
        ('construction_bars',[s['construction_bars'] for s in result.signals]),
        ('risk_ticks',[t['risk']/t['entry_tick'] for t in result.trades+result.data_quality_exclusions])):
        for value,count in sorted(Counter(map(str,values)).items()):
            rows.append(dict(configuration_id=spec['configuration_id'],kind='GEOMETRY',field=field,value=value,count=count))
    return rows


def run(data_root,output):
    policy,freeze,commitments=verify_freeze();output_guard(output);protected_check(policy)
    rules=MarketRules(policy)
    with bounded_reads(data_root,policy) as reads:
        data,receipts=load_market_data(data_root,policy,rules)
    output.mkdir(parents=True)
    dump(output/'input_provenance.json',dict(source_sha=policy['source_ref'],verified_prefixes=receipts,
        actual_python_read_receipts=reads,candle_rows_read=sum(r['candle_rows_read'] for r in reads),
        candle_bytes_read=sum(r['bytes_read'] for r in reads),bytes_2024_plus_read=0,rows_2024_plus_read=0))
    dump(output/'freeze_manifest.json',dict(freeze_commit=freeze,**commitments))
    candidates=[];monthly=[];directional=[];funnels=[];diag=[];index=[]
    code_sha=digest(STUDY.parents[0]/'strategies/return_retest_rejection_m5_optimization_c_v1.py')
    for config in grid(policy):
        ident=config['configuration_id'];symbol='USDRUBF';p={k:v for k,v in config.items() if k!='configuration_id'}
        target=output/'evaluations'/ident/symbol
        strategy=ReturnRetestRejectionM5OptimizationC(p)
        result=Backtester(rules,entry_mode='ENTRY_NEXT_OPEN',data_gap_policy='DATA_GAP_SKIP_V2',
            cost_ticks_per_side=1,allow_entry_bar_take=False,session_flat_before_end_bars=1).run(
                strategy,symbol,data[symbol],start=date(2023,1,1),end_exclusive=date(2024,1,1))
        result.validate()
        write_data_quality_reports(target,result,data,policy,rules)
        csv_write(target/'construction_events.csv',strategy.construction_events)
        csv_write(target/'days.csv',result.days)
        csv_write(target/'rejected_nonfill.csv',[s for s in result.signals if s['status'] in ('REJECTED','NONFILL')])
        ds=diagnostics(result,strategy.construction_events,config);diag.extend(ds);csv_write(target/'construction_diagnostics.csv',ds)
        dump(target/'configuration.json',dict(configuration_id=ident,parameters=p,instrument=symbol,
            execution=policy['execution'],strategy_sha256=code_sha,source_sha=policy['source_ref'],
            source_blob=policy['inputs'][symbol]['blob'],freeze_commit=freeze))
        cov=data_quality_coverage(data,policy,rules,result)
        m,months,directions,funnel=summaries(config,symbol,result,cov,policy,freeze,code_sha)
        candidates.append(m);monthly.extend(months);directional.extend(directions);funnels.append(funnel)
        index.append(dict(configuration_id=ident,instrument=symbol,detail_directory=str(target.relative_to(output)),
            signals=len(result.signals),construction_events=len(strategy.construction_events),CLOSED=len(result.trades),
            SKIP=len(result.data_gap_skips),EXCLUDED=len(result.data_quality_exclusions)))
        print(f'{ident}: completed {len(candidates)}/288',flush=True)
    assert len(candidates)==288
    neighbors,selection=select(candidates,policy)
    for name,rows in [('all_candidates',candidates),('monthly_results',monthly),('direction_results',directional),
        ('execution_funnel',funnels),('parameter_neighborhood',neighbors),('construction_diagnostics',diag),('detailed_artifact_index',index)]:
        csv_write(output/(name+'.csv'),rows)
    dump(output/'selection_report.json',selection)
    (output/'Optimization_Report.md').write_text(report(policy,freeze,candidates,monthly,selection))
    return selection


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--data-root',type=Path,required=True);p.add_argument('--output',type=Path,default=RESULTS)
    a=p.parse_args();print(json.dumps(run(a.data_root,a.output),sort_keys=True))
