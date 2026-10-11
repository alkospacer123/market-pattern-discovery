"""Technical C preflight: observations/signals/immediate Opens, no historical exit/P&L."""
from collections import Counter
from datetime import date, timedelta
import hashlib
import json
from pathlib import Path
from IntradayLab.core.calendar import MarketRules
from IntradayLab.core.data_loader import load_market_data
from IntradayLab.core.execution import entry_admission
from IntradayLab.core.models import Context
from IntradayLab.core.reports import dump
from IntradayLab.strategies.return_retest_rejection_m5 import ReturnRetestRejectionM5, FIVE
from IntradayLab.tools.audit_return_retest_baseline import read_source, constructions, compare_ledger, encode
from IntradayLab.tools.return_retest_contract import CONFIG, bounded_reads, protected_check


def preflight(data_root,output):
    cfg=json.loads(CONFIG.read_text());rules=MarketRules(cfg);protected=protected_check(data_root,cfg)
    with bounded_reads(data_root,cfg) as production_reads:
        data,receipts=load_market_data(data_root,cfg,rules)
    with bounded_reads(data_root,cfg) as independent_reads:
        raw=read_source(data_root,cfg)
    findings={};checked=0
    for symbol in cfg['instruments']:
        st=ReturnRetestRejectionM5(cfg['parameters']);events=[]
        day=date(2023,1,1);first=min(data[symbol]).date()
        while day.year==2023:
            st.begin_day(symbol,day)
            if day>=first:
                for a,z in rules.windows(day):
                    at=a
                    while at<z:
                        ctx=Context(symbol,at,at+FIVE,(a,z),rules.tick(symbol,at),{})
                        events.extend(dict(e,instrument=symbol) for e in st.on_bar(data[symbol].get(at),ctx));at+=FIVE
                st.end_day()
            day+=timedelta(days=1)
        candidates,independent_events=constructions(symbol,raw[symbol],cfg)
        serialized=[{k:json.dumps(v,default=encode,sort_keys=True) if isinstance(v,(list,dict)) else str(v) for k,v in e.items()} for e in events]
        checked+=compare_ledger(serialized,candidates,symbol+' PREFLIGHT',ignore=('window_end',))
        counts=Counter(e['event'] for e in st.construction_events);oracle=Counter(e['event'] for e in independent_events)
        if counts!=oracle:raise AssertionError('INDEPENDENT_APPROACH_COUNTS '+symbol)
        opens=Counter()
        for e in events:
            if e['base_reason']!='SIGNAL':continue
            at=e['signal_at'];bar=data[symbol].get(at);grid=rules.tick(symbol,at)
            if bar is None:opens['MISSING_ENTRY_OPEN']+=1
            elif not bar.open.is_finite() or bar.open<=0 or bar.open%grid:opens['INVALID_ENTRY_OPEN']+=1
            else:
                reason=entry_admission(bar.open,e['direction'],e['stop'],grid,e['entry_constraints'])
                opens[reason or 'GEOMETRY_ADMISSIBLE_BEFORE_POSITION_SESSION_CHECKS']+=1
        findings[symbol]=dict(approach_event_counts=dict(sorted(counts.items())),candidates=len(events),
            qualified_directional_signals=sum(e['base_reason']=='SIGNAL' for e in events),
            close_or_ambiguity_refusals=dict(sorted(Counter(e['base_reason'] for e in events if e['base_reason']!='SIGNAL').items())),
            immediate_open_only_geometry=dict(sorted(opens.items())))
    result=dict(status='PASS',research_phase='BASELINE_TECHNICAL_PREFLIGHT',historical_pnl_calculated=False,
        historical_position_paths_simulated=False,parameters_changed=False,independent_signal_fields=checked,
        findings=findings,input_provenance=receipts,actual_source_reads=production_reads+independent_reads,
        bytes_2024_plus_read=0,protected_scope=protected)
    dump(output,result);return result


if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--data-root',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();r=preflight(a.data_root,a.output);print(json.dumps(dict(status=r['status'],pnl_calculated=False,findings=r['findings']),sort_keys=True))
