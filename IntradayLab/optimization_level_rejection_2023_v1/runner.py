"""Exhaustive frozen Level Rejection 72 x 3 evaluations; unchanged shared engine."""
import argparse
from datetime import date
from decimal import Decimal as D
import json
from pathlib import Path
from IntradayLab.core.backtester import Backtester
from IntradayLab.core.calendar import MarketRules
from IntradayLab.core.data_loader import load_market_data
from IntradayLab.core.reports import write_data_quality_reports,csv_write,dump,data_quality_coverage
from IntradayLab.strategies.level_rejection_m5_optimization_v1 import LevelRejectionM5Optimization
from .contract import verify_freeze,grid,protected_check,output_guard,bounded_reads,digest,STUDY,RESULTS
from .aggregation import summaries,select
from .reporting import report
from .baseline_replay import run as baseline_replay


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
    candidates=[];monthly=[];directional=[];funnels=[];index=[]
    code_sha=digest(STUDY.parents[0]/'strategies/level_rejection_m5_optimization_v1.py')
    for config in grid(policy):
        ident=config['configuration_id'];p={k:v for k,v in config.items() if k!='configuration_id'}
        for symbol in policy['instruments']:
            target=output/'evaluations'/ident/symbol
            result=Backtester(rules,data_gap_policy='DATA_GAP_SKIP_V2',daily_trade_deadline_clock='17:00',
                cost_ticks_per_side=1,allow_entry_bar_take=False,session_flat_before_end_bars=1).run(
                    LevelRejectionM5Optimization(p),symbol,data[symbol],start=date(2023,1,1),end_exclusive=date(2024,1,1))
            result.validate();local=dict(policy,instruments=[symbol])
            write_data_quality_reports(target,result,data,local,rules)
            csv_write(target/'days.csv',result.days)
            csv_write(target/'rejected_nonfill.csv',[s for s in result.signals if s['status'] in ('REJECTED','NONFILL')])
            dump(target/'configuration.json',dict(configuration_id=ident,parameters=p,instrument=symbol,
                execution=policy['execution'],strategy_sha256=code_sha,source_sha=policy['source_ref'],
                source_blob=policy['inputs'][symbol]['blob'],freeze_commit=freeze))
            cov=data_quality_coverage(data,local,rules,result)
            m,months,directions,funnel=summaries(config,symbol,result,cov,policy,freeze,code_sha)
            m.update(signals=funnel['signals'],attempted_entries=sum(bool(s.get('pending_created')) for s in result.signals),
                raw_rejections=sum(bool(s.get('raw_rejection')) for s in result.signals),
                dedup_30min=sum(s['base_reason']=='DEDUP_30MIN' for s in result.signals),
                calendar_trading_days=len(cov),observed_trading_days=sum(c['valid_bars']>0 for c in cov),
                months_without_closed=12-m['entry_months'],
                closed_per_calendar_trading_day=D(m['CLOSED'])/len(cov),
                closed_per_observed_trading_day=D(m['CLOSED'])/sum(c['valid_bars']>0 for c in cov),
                closed_per_active_entry_day=D(m['CLOSED'])/m['entry_days'] if m['entry_days'] else 'NOT_AVAILABLE')
            candidates.append(m);monthly.extend(months);directional.extend(directions);funnels.append(funnel)
            index.append(dict(configuration_id=ident,instrument=symbol,detail_directory=str(target.relative_to(output)),
                signals=len(result.signals),CLOSED=len(result.trades),SKIP=len(result.data_gap_skips),EXCLUDED=len(result.data_quality_exclusions)))
        print(f'{ident}: completed {len(candidates)}/216',flush=True)
    assert len(candidates)==216
    neighbors,selection=select(candidates,policy)
    for name,rows in [('all_candidates',candidates),('monthly_results',monthly),('direction_results',directional),
        ('execution_funnel',funnels),('parameter_neighborhood',neighbors),('detailed_artifact_index',index)]:
        csv_write(output/(name+'.csv'),rows)
    dump(output/'selection_report.json',selection)
    baseline_replay(data_root,output,policy,freeze,loaded=(data,receipts,reads))
    (output/'Optimization_Report.md').write_text(report(policy,freeze,candidates,monthly,selection))
    return selection


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--data-root',type=Path,required=True);p.add_argument('--output',type=Path,default=RESULTS)
    a=p.parse_args();print(json.dumps(run(a.data_root,a.output),sort_keys=True))
