#!/usr/bin/env python3
"""2023 technical feasibility only: no execution paths, trade ledger or P&L."""
import argparse
from collections import Counter
from datetime import date,timedelta
from decimal import Decimal as D
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from IntradayLab.core.calendar import MarketRules
from IntradayLab.core.data_loader import load_market_data
from IntradayLab.core.models import Context
from IntradayLab.core.execution import entry_admission
from IntradayLab.strategies.high_low_cluster_m5 import HighLowClusterM5,FIVE
from IntradayLab.tools.audit_high_low_cluster_baseline import episodes
from IntradayLab.tools.audit_canonical_baseline import check_rows
from IntradayLab.tools.high_low_cluster_contract import LAB,config_path,bounded_reads,protected_check


def preflight(root):
    cfg=json.loads(config_path(4).read_text());rules=MarketRules(cfg);scope=protected_check(root,cfg)
    with bounded_reads(root,cfg) as reads:raw,receipts=load_market_data(root,cfg,rules)
    output={};checked=0
    for n in (4,7,10):
        config=json.loads(config_path(n).read_text());by={}
        for symbol in cfg['instruments']:
            rows=raw[symbol];st=HighLowClusterM5(config['parameters']);actual=[];admission=Counter();day=date(2023,1,1)
            while day.year==2023:
                st.begin_day(symbol,day)
                for a,z in rules.windows(day) if day>=min(rows).date() else []:
                    at=a
                    while at<z:
                        ctx=Context(symbol,at,at+FIVE,(a,z),rules.tick(symbol,at),{})
                        for event in st.on_bar(rows.get(at),ctx):
                            e=dict(event,instrument=symbol,date=str(day),recorded_at=at+FIVE)
                            if e['base_reason']=='SIGNAL':
                                e.update(window_start=a,window_end=z)
                                b=rows.get(e['signal_at']);step=rules.tick(symbol,e['signal_at'])
                                if b is None or not b.open.is_finite() or b.open<=0 or b.open%step:admission['UNKNOWN_OPEN']+=1
                                else:admission[entry_admission(b.open,e['direction'],e['stop'],step,e['entry_constraints']) or 'GEOMETRY_FEASIBLE']+=1
                            actual.append(e)
                        at+=FIVE
                st.end_day();day+=timedelta(days=1)
            observations={at:(b.open,b.high,b.low,b.close,b.volume) for at,b in rows.items()}
            expected=episodes(symbol,observations,n)
            keys=sorted({k for e in expected for k in e if k not in ('extrema','extreme_times')})
            checked+=check_rows(actual,expected,keys,'PREFLIGHT')
            require_ids=len({e['episode_id'] for e in actual})==len(actual)
            if not require_ids:raise AssertionError('DUPLICATES')
            by[symbol]=dict(rows_2023=len(rows),detected=len(actual),signals=sum(e['base_reason']=='SIGNAL' for e in actual),admission_geometry_only=dict(sorted(admission.items())),zero_width_count=sum(e['cluster_width_ticks']==0 for e in actual),historical_grid_and_raw_oracle='PASS')
        output[f'B{n}']=by
    doc=dict(status='PASS',historical_PnL_viewed=False,trade_paths_evaluated=False,backtester_used=False,all_three_checked_before_pnl=True,
        checked_signal_fields=checked,models=output,source_receipts=receipts,actual_read_guard=reads,protected_files=scope,
        accepted_risk_ticks_implication=[3,5],C1_initial_risk_R_range=['0.40','0.6666666666666666666666666667'],
        source_ref=cfg['source_ref'],bytes_2024_plus_read=0,bytes_2025_plus_read=0)
    (LAB/'config/high_low_cluster_b4_b7_b10_pre_pnl_validation.json').write_text(json.dumps(doc,indent=2,sort_keys=True,default=str)+'\n')
    return doc


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--data-root',type=Path,required=True);r=preflight(p.parse_args().data_root);print(json.dumps(dict(status=r['status'],checked_signal_fields=r['checked_signal_fields'],historical_PnL_viewed=False)))
