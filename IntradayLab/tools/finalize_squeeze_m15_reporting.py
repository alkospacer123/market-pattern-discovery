#!/usr/bin/env python3
"""Add source/parent coverage and complete funnel reporting; never change trading."""
import argparse,csv,gzip,json,shutil,hashlib
from pathlib import Path
from datetime import datetime,timedelta
from decimal import Decimal as D,localcontext
from collections import Counter
from run_squeeze_m15 import read_inputs,CONFIG,write_csv,encoded,sha
from squeeze_m15_replay import compose,windows,geometry,flat_slot


def read(path):
    with (gzip.open(path,'rt') if path.suffix=='.gz' else path.open()) as f:return list(csv.DictReader(f))


def finalize(root,source,out):
    assert not out.exists();out.mkdir(parents=True)
    for p in source.iterdir():
        if p.name!='SHA256SUMS':shutil.copy2(p,out/p.name)
    data,_=read_inputs(root,json.loads(CONFIG.read_text()))
    cov=[]
    for s,bars in data.items():
        parents=compose(bars,15)
        for m in range(1,13):
            day=datetime(2023,m,1);expected=set()
            while day.year==2023 and day.month==m:
                for a,z in windows(day.date()):
                    t=a-timedelta(minutes=a.minute%15)
                    if t<a:t+=timedelta(minutes=15)
                    while t+timedelta(minutes=15)<=z:
                        expected.add(t);t+=timedelta(minutes=15)
                day+=timedelta(days=1)
            cov.append(dict(instrument=s,period=f'2023-{m:02d}',expected_m15_slots=len(expected),observed_m15_slots=sum(parents.get(t) is not None for t in expected),missing_m15_since_inception=sum(t>=bars[0].timestamp and parents.get(t) is None for t in expected),pre_inception_m15_slots=sum(t<bars[0].timestamp for t in expected)))
    lookup={(r['instrument'],r['period']):r for r in cov}
    monthly=read(source/'monthly_results.csv')
    for r in monthly:
        r.update({k:v for k,v in lookup[r['instrument'],r['period']].items() if k not in ('instrument','period')})
        if r['coverage_status']=='NO_COVERAGE':r['unknown_entry_orders']=0
    write_csv(out/'monthly_results.csv',monthly);write_csv(out/'coverage_m15.csv',cov)
    metrics=read(source/'metrics.csv');signals=read(source/'signals.csv.gz')
    cycles=read(source/'squeeze_cycles.csv.gz');features=read(source/'indicator_features.csv.gz')
    stages=[]
    for r in metrics:
        keys=r['instrument'],r['architecture'],r['scenario']
        ms=[m for m in monthly if (m['instrument'],m['architecture'],m['scenario'],m['cost'])==(*keys,'C1')]
        r['zero_net_trade_months']=sum(m['month_status']=='ZERO_NET' for m in ms)
        r['confirmed_zero_trade_months']=sum(m['month_status']=='NO_TRADES' and m['coverage_status']=='COVERED' for m in ms)
        r['partially_covered_months']=sum(m['coverage_status'] in ('PARTIAL_DATA','PARTIAL_LAUNCH') for m in ms)
        pos=[D(m['closed_net']) for m in ms if m['closed_net'] and D(m['closed_net'])>0]
        r['largest_positive_month_share']=max(pos)/sum(pos) if pos else None
        r['positive_month_scope']='CLOSED_COHORT_SUBSETS_WITH_COVERAGE_LABELS'
        symbol=r['instrument'];valid=compose(data[symbol],15)
        group=[s for s in signals if (s['instrument'],s['architecture'],s['scenario'])==keys]
        safe=[];context=[];geometric=[]
        for s in group:
            w=next(w for w in windows(datetime.fromisoformat(s['signal_at']).date()) if w[0]<=datetime.fromisoformat(s['signal_at'])<w[1])
            target=datetime.fromisoformat(s['planned_execution_at'])
            if not (w[0]<=target<w[1] and target+timedelta(minutes=25)<=flat_slot(w)-timedelta(minutes=5)):continue
            safe.append(s)
            if s['architecture']=='SQUEEZE_H1_M15' and s['mtf_reason']:continue
            context.append(s)
            model={k:D(s[k]) for k in ('atr7','stop','cap','edge')};model['direction_sign']=int(s['direction_sign'])
            with localcontext() as ctx:
                ctx.prec=34
                _,why=geometry(symbol,model,D(s['signal_close']),datetime.fromisoformat(s['available_at']))
            if why is None:geometric.append(s)
        counts=[('ALL_2023_SOURCE_M5',len(data[symbol])),('COMPLETE_USABLE_M15',sum(b is not None for b in valid.values())),('READY_BB7_EMA7_ATR7',sum(f['instrument']==symbol for f in features)),('RAW_SQUEEZE_EPISODES',int(r['raw_squeeze_episodes'])),('CONFIRMED_SQUEEZES',int(r['confirmed_squeeze_episodes'])),('DIRECTIONAL_EXPANSIONS',len(group)),('COMMON_SESSION_SAFE_TARGETS',len(safe)),('ENTRY_CONTEXT_ALLOWED',len(context)),('SIGNAL_CLOSE_GEOMETRY_ALLOWED',len(geometric)),('SUBMITTED_ORDERS',int(r['model_orders'])),('CONDITIONAL_EXACT_OPEN_FILLS',int(r['entries'])),('NONFILL',int(r['nonfills'])),('UNKNOWN_ORDER_OR_PATH',int(r['unknown']))]
        stages += [dict(instrument=keys[0],architecture=keys[1],scenario=keys[2],stage=stage,count=count,scope='PREDECLARED_CAUSAL_FAN_IN_TO_EXECUTION' if stage not in ('NONFILL','UNKNOWN_ORDER_OR_PATH') else 'EXECUTION_OUTCOME_BRANCH') for stage,count in counts]
    write_csv(out/'metrics.csv',metrics);write_csv(out/'funnel_stages.csv',stages)
    unchanged=['signals.csv.gz','squeeze_cycles.csv.gz','indicator_features.csv.gz','trade_ledger.csv.gz','execution_events.csv.gz','derived_parents.csv.gz','sensitivity.csv','direction_results.csv','frequency_report.csv','filter_funnel.csv','m15_h1_comparison.csv','input_provenance.json']
    assert all((source/f).read_bytes()==(out/f).read_bytes() for f in unchanged)
    history={'kind':'REPORT_COMPLETENESS_ONLY_NO_TRADING_OR_RETURN_CHANGE','reason':'Add promised expected/observed M15 coverage, zero-net month counts, positive-month concentration and source-to-execution causal funnel; uncovered unknown-order count represented as zero research orders.','configuration_sha256':sha(CONFIG.read_bytes()),'trading_artifacts_identical':unchanged,'changes':{f:{'before_sha256':sha((source/f).read_bytes()),'after_sha256':sha((out/f).read_bytes())} for f in ('metrics.csv','monthly_results.csv')},'new_artifacts':['coverage_m15.csv','funnel_stages.csv']}
    (out/'reporting_correction_history.json').write_text(encoded(history))
    (out/'SHA256SUMS').write_text(''.join(f'{sha(p.read_bytes())}  {p.name}\n' for p in sorted(out.iterdir()) if p.name!='SHA256SUMS'))
    print('Reporting additions complete; trading/returns byte-identical')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--data-root',type=Path,required=True);p.add_argument('--source',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();finalize(a.data_root,a.source,a.output)
