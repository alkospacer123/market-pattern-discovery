"""Frozen-data offline explanation of signal/grid/capacity/guard stages; no orders."""
from __future__ import annotations
import argparse
from dataclasses import asdict
from decimal import Decimal
import json
from pathlib import Path
import socket

import pandas as pd

from .context_builder import T3ContextBuilder
from .execution_grid import EXECUTION_REVISION, FINAM_FILL_AUTHORITY_VERIFIED
from .production_history import load_stage5_seed_open_h1, close_index_for_frozen_t3, SEED_SHA256
from .production_runtime import ProductionRuntime, InstrumentAuthority
from .release_preparation import ReleaseBlocked, safe_external, sha
from .specification import INSTRUMENTS
from .strategy_core import DecisionCore, CompletedBar, T3Context, PositionState
from .trail1_state import Trail1State

ROOT=Path(__file__).resolve().parents[2]
ACCEPTED=ROOT/'audit_only/stop_tick_grid_20261012/full_available_raw_signals.csv'


def frozen_signals(frame,instrument):
    """Same unchanged core/state sequence as the accepted full-history raw scan."""
    low,high=T3ContextBuilder().build(frame,frame.index[-1])
    core=DecisionCore();cursor=-1;sequence=0;position=None;signals=[]
    for stamp,row in low.iterrows():
        while cursor+1<len(high) and high.index[cursor+1]<=stamp:cursor+=1
        bar=CompletedBar(stamp.to_pydatetime(),float(row.Open),float(row.High),float(row.Low),float(row.Close),float(row.ATR),
                         None if pd.isna(row.PriorHigh) else float(row.PriorHigh),None if pd.isna(row.PriorLow) else float(row.PriorLow))
        if position is not None and core.manage(position,bar)['event']=='EXIT':position=None
        if cursor<0 or pd.isna(row.ATR):continue
        h=high.iloc[cursor]
        context=T3Context(float(h.Close),float(h.EMA100),float(h.EMA100Slope),float(h.ADX),float(h.ATR),float(h.ATRMean20),float(h.EMA50),float(h.EMA200))
        signal=core.signal(instrument,bar,context,sequence+1)
        if signal is None:continue
        signals.append(signal)
        if position is None:
            sequence+=1
            position=PositionState(instrument,signal.direction,signal.entry,signal.initial_stop,signal.initial_stop,signal.entry,
                                   Trail1State(signal.direction,signal.entry,signal.initial_stop))
    return signals


def diagnose(data_root,out, *, start,end):
    start,end=pd.Timestamp(start),pd.Timestamp(end)
    if start.tzinfo is None or end.tzinfo is None or start>=end:raise ReleaseBlocked('EXPLICIT_INTERVAL_TIMEZONE_REQUIRED')
    out=safe_external(out,must_exist=False)
    if out.exists() or Path(data_root).resolve() in out.parents:raise ReleaseBlocked('NEW_ISOLATED_OUTPUT_REQUIRED')
    accepted=pd.read_csv(ACCEPTED,dtype=str,keep_default_na=False)
    lookup={(r.instrument,r.timestamp,r.direction):r for r in accepted.itertuples()}
    frames={symbol:close_index_for_frozen_t3(load_stage5_seed_open_h1(data_root,symbol).astype(float)) for symbol in INSTRUMENTS}
    if any(frame.index.max()<end or frame.index.min()>start for frame in frames.values()):
        raise ReleaseBlocked('INTERVAL_NOT_COVERED_BY_FROZEN_DATA_NO_LIVE_SIGNAL_CLAIM')
    out.mkdir(parents=True)
    counts={};examples=[];rows=[]
    for symbol,frame in frames.items():
        signals=[s for s in frozen_signals(frame.loc[frame.index<=end],symbol) if start<=pd.Timestamp(s.timestamp)<end]
        expected=accepted[(accepted.instrument==symbol)&(pd.to_datetime(accepted.timestamp,utc=True)>=start)&(pd.to_datetime(accepted.timestamp,utc=True)<end)]
        if len(signals)!=len(expected):raise ReleaseBlocked('RAW_SIGNAL_COUNT_NOT_FROZEN_CONFORMANT')
        counts[symbol]={'completed_h1':len(frame.loc[(frame.index>=start)&(frame.index<end)]),'raw_t3_signals':len(signals),
                        'legacy_grid_skips':0,'v2_capacity_zero':0,'v2_plannable':0,'v2_entry_guard_closed':0,'session_unverified':len(signals),'r15_zero':0,'margin_zero':0,'aggregate_risk_skips':0}
        legacy=ProductionRuntime(out/(symbol+'-legacy.sqlite3'))
        candidate=ProductionRuntime(out/(symbol+'-v2.sqlite3'),execution_revision=EXECUTION_REVISION)
        try:
            authority=InstrumentAuthority(symbol,symbol+'@RTSX',Decimal(candidate.registry[symbol]['price_step']),
                        Decimal(candidate.registry[symbol]['tick_value']),1,Decimal('100'),Decimal('120'))
            for signal in signals:
                record=lookup.get((symbol,signal.timestamp.isoformat(),signal.direction))
                if record is None or (signal.signal_id,signal.trade_id,str(signal.entry),str(signal.initial_stop),str(signal.initial_r))!=(
                        record.signal_id,record.trade_id,record.entry,record.initial_stop,record.initial_r):
                    raise ReleaseBlocked('RAW_SIGNAL_PRICE_TIME_ID_NOT_FROZEN_CONFORMANT')
                actions=[];sizing=None
                for runtime in (legacy,candidate):
                    action=runtime.plan_entry(signal,authority,realized_equity=Decimal('100000'),
                        budget=runtime.begin_batch(realized_equity=Decimal('100000'),available_cash=Decimal('1000000')))
                    actions.append(action)
                    if action.idempotency_key:
                        if runtime is candidate:sizing=runtime.store.intent(action.idempotency_key)['payload']['sizing']
                        # Counterfactual independent planning only: no broker
                        # rejection/fill claim and no portfolio return calculation.
                        runtime.store.transition_intent(action.idempotency_key,'REJECTED')
                old,new=actions
                counts[symbol]['legacy_grid_skips']+=int(old.kind=='SKIP_STOP_NOT_ON_TICK_GRID')
                counts[symbol]['v2_capacity_zero']+=int(new.kind=='SKIP_ZERO_CAPACITY')
                counts[symbol]['aggregate_risk_skips']+=int(new.kind=='SKIP_RISK_LIMIT')
                if sizing:
                    counts[symbol]['r15_zero']+=int(sizing['r15_quantity']==0)
                    counts[symbol]['margin_zero']+=int(sizing['margin_quantity']==0)
                counts[symbol]['v2_plannable']+=int(new.kind=='ENTRY')
                counts[symbol]['v2_entry_guard_closed']+=int(new.kind=='ENTRY' and not FINAM_FILL_AUTHORITY_VERIFIED)
                row={'instrument':symbol,'timestamp':signal.timestamp.isoformat(),'direction':signal.direction,
                     'signal_id':signal.signal_id,'trade_id':signal.trade_id,'raw_entry':str(signal.entry),
                     'raw_stop':str(signal.initial_stop),'raw_r':str(signal.initial_r),
                     'frozen_data_price_time_identity':'PASS','legacy_plan':old.kind,'v2_plan':new.kind,
                     'v2_stop':str(new.stop_price),'v2_quantity':new.quantity,
                     'sizing_evidence':sizing,'capacity_reason':new.reason,'nominal_open_portfolio_risk':'0 (independent planning scenario)', 'session':'UNVERIFIED_NO_HISTORICAL_SCHEDULE',
                     'v2_execution_guard':'CLOSED_FILL_SLTP_ACCEPTANCE_NOT_DONE'}
                rows.append(row)
                if len(examples)<3:examples.append(row)
        finally:legacy.close();candidate.close()
    result={'schema':'stop_tick_grid_signal_diagnostic.v1','start_inclusive':start.isoformat(),'end_exclusive':end.isoformat(),
            'source':'EXACT_FROZEN_STAGE5_NO_LIVE_BARS','seed_sha256':SEED_SHA256,'accepted_signal_csv_sha256':sha(ACCEPTED),
            'per_symbol':counts,'actual_examples':examples,'raw_research_conformance':'PASS',
            'scope':'Existing full T3 conditions; fixed frozen interval. Synthetic independent sizing equity=100000/cash=1000000/GO LONG=100 SHORT=120; not physical margin or actual trading eligibility.',
            'session_authority':'NOT_PROVIDED_NOT_INFERRED','live_week_diagnostic':'BLOCKED_NO_EXTERNAL_LIVE_H1_SNAPSHOT',
            'message':'NO_RAW_T3_SIGNAL_GRID_FIX_CANNOT_CREATE_SIGNAL' if not rows else 'RAW_SIGNALS_EXIST_LEGACY_GRID_SKIPS_V2_GUARD_STILL_CLOSED',
            'real_order_endpoint_calls':0,'live_changes':'NONE','live_production_ready':'NO'}
    pd.DataFrame(rows).to_csv(out/'per_signal.csv',index=False)
    (out/'results.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    return result


def main(argv=None):
    parser=argparse.ArgumentParser(description='Read-only frozen signal versus execution-boundary diagnostic')
    parser.add_argument('--stage5-data-root',type=Path,required=True);parser.add_argument('--out',type=Path,required=True)
    parser.add_argument('--start',required=True);parser.add_argument('--end',required=True)
    args=parser.parse_args(argv)
    def deny(*a,**k):raise AssertionError('OFFLINE_DIAGNOSTIC_NETWORK_FORBIDDEN')
    socket.socket.connect=deny;socket.socket.connect_ex=deny;socket.create_connection=deny
    result=diagnose(args.stage5_data_root,args.out,start=args.start,end=args.end)
    print(json.dumps({'per_symbol':result['per_symbol'],'message':result['message'],'real_order_endpoint_calls':0},indent=2));return 0


if __name__=='__main__':raise SystemExit(main())
