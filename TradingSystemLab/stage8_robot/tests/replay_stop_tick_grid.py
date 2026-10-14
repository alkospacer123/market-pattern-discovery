"""Bounded candidate replay. Never writes frozen artifacts or uses broker/network.

python .../replay_stop_tick_grid.py --data-root <frozen worktree> --out <NEW DIR>
Synthetic realized equity/margin and reference-price fills are expressly offline.
"""
from __future__ import annotations
import argparse
from dataclasses import replace
from decimal import Decimal
from fractions import Fraction
import json
from pathlib import Path
import socket
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT/'src'))
sys.path.insert(0, str(ROOT/'audit_only/stop_tick_grid_20261012'))

def deny(*args, **kwargs): raise AssertionError('OFFLINE_REPLAY_NETWORK_FORBIDDEN')
socket.socket.connect = deny
socket.socket.connect_ex = deny
socket.create_connection = deny

import pandas as pd
from audit import authenticate_exact_sources, authority, HASHES, S5, S6, economics
from TradingSystemLab.core.data_loader import DataLoader
from TradingSystemLab.stage8_robot.production_replay import replay_production
from TradingSystemLab.stage8_robot.authority_replay import replay_authority
from TradingSystemLab.stage8_robot.historical_conformance import reconcile
from TradingSystemLab.stage8_robot.context_builder import T3ContextBuilder
from TradingSystemLab.stage8_robot.strategy_core import CompletedBar, SignalIntent
from TradingSystemLab.stage8_robot.production_runtime import ProductionRuntime
from TradingSystemLab.stage8_robot.execution_grid import EXECUTION_REVISION, require_on_grid
from TradingSystemLab.stage8_robot.protective_stop_contract import percent_position_stop_payload


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--data-root',type=Path,required=True)
    parser.add_argument('--out',type=Path,required=True)
    args=parser.parse_args()
    if args.out.exists(): raise ValueError('OUTPUT_MUST_BE_NEW_NO_FROZEN_ARTIFACT_REWRITE')
    args.out.mkdir(parents=True)
    auth=authenticate_exact_sources(args.data_root)
    registry=pd.read_csv(S5/'canonical_lifecycle_registry.csv',keep_default_na=False)
    registry=registry[(registry.generation=='v3_perpetual')&(registry.strategy=='T3')&(registry.timeframe=='H1')&registry.instrument.isin(HASHES)]
    frames={s:DataLoader.close_index(DataLoader(forbid_true_oos=False).load_csv(args.data_root/'forever'/s/f'{s}_H1.csv')) for s in HASHES}
    # Two exact RAW replays use unchanged core/authority; no amended expectations.
    raw,independent=[],[]
    prepared={}
    for r in registry.to_dict('records'):
        f=frames[r['instrument']].loc[r['start_timestamp']:r['end_timestamp']].copy()
        meta={k:r[k] for k in ('instrument','lifecycle','fold_id')}
        raw.extend(replay_production(f,r['instrument'],meta))
        independent.extend(replay_authority(f,r['instrument'],meta))
        low,_=T3ContextBuilder().build(f,f.index[-1])
        prepared[(r['instrument'],r['lifecycle'],r['fold_id'])]=low
    expected=pd.read_csv(S6/'trail1_authoritative_trades.csv',keep_default_na=False)
    raw_results={'production':reconcile(expected,pd.DataFrame(raw),args.out/'raw_production.csv'),
                 'independent_authority':reconcile(expected,pd.DataFrame(independent),args.out/'raw_authority.csv')}
    assert all(x['status']=='PASS' for x in raw_results.values())
    accepted=ROOT/'audit_only/stop_tick_grid_20261012'
    entries=pd.read_csv(accepted/'lifecycle_admitted_entries.csv',keep_default_na=False,dtype=str)
    rows=[]; projection_checks=0; stops=0; replacements=0; exits=0; bars=0; changed_exit_times=0
    # Project ALL 1422 accepted full-history signals through actual candidate
    # plan_entry, including durable sizing evidence. Reject intent terminally in
    # this order-incapable flat proof; no historical portfolio authority invented.
    rt=ProductionRuntime(args.out/'all-signals.sqlite3',execution_revision=EXECUTION_REVISION)
    for r in pd.read_csv(accepted/'full_available_raw_signals.csv',dtype=str,keep_default_na=False).to_dict('records'):
        sig=SignalIntent(r['signal_id'],r['trade_id'],r['instrument'],r['direction'],pd.Timestamp(r['timestamp']).to_pydatetime(),
                         Decimal(r['entry']),Decimal(r['initial_stop']),Decimal(r['initial_r']),Decimal(r['initial_stop']))
        budget=rt.begin_batch(realized_equity=Decimal('100000'),available_cash=Decimal('1000000'))
        action=rt.plan_entry(sig,authority(sig.instrument),realized_equity=Decimal('100000'),budget=budget)
        assert action.kind in {'ENTRY','SKIP_ZERO_CAPACITY'}
        if action.kind=='ENTRY':
            p=rt.store.intent(action.idempotency_key)['payload']
            # Independent rational oracle: no production projection/sizing
            # function supplies these expectations.
            raw_ticks=Fraction(sig.initial_stop)/Fraction(authority(sig.instrument).price_step)
            tick_index=raw_ticks.numerator//raw_ticks.denominator
            if sig.direction=='SHORT' and raw_ticks.denominator!=1: tick_index+=1
            oracle_stop=tick_index*Fraction(authority(sig.instrument).price_step)
            oracle_loss=abs(Fraction(sig.entry)-oracle_stop)/Fraction(authority(sig.instrument).price_step)*Fraction(authority(sig.instrument).tick_value)
            oracle_r15=int(Fraction(1500)//oracle_loss)
            oracle_margin=1000000//(100 if sig.direction=='LONG' else 120)
            assert Fraction(action.stop_price)==oracle_stop
            assert p['r15_quantity']==oracle_r15
            assert action.quantity==min(oracle_r15,oracle_margin)
            assert action.quantity*oracle_loss<=1500
            require_on_grid(action.stop_price,authority(sig.instrument).price_step)
            assert Decimal(p['reference_initial_loss_cash'])<=Decimal('1500')
            assert Decimal(p['margin_reservation'])<=Decimal('1000000')
            assert p['raw_initial_stop']==r['initial_stop'] and p['raw_initial_r']==r['initial_r']
            rt.store.transition_intent(action.idempotency_key,'REJECTED')
        projection_checks+=1
    rt.close()
    for i,r in enumerate(entries.to_dict('records')):
        low=prepared[(r['instrument'],r['lifecycle'],r['fold_id'])]
        rt=ProductionRuntime(args.out/f'trade-{i:04}.sqlite3',execution_revision=EXECUTION_REVISION)
        sig=SignalIntent(r['signal_id'],r['trade_id'],r['instrument'],r['direction'],pd.Timestamp(r['timestamp']).to_pydatetime(),
                         Decimal(r['entry']),Decimal(r['initial_stop']),Decimal(r['initial_r']),Decimal(r['initial_stop']))
        a=rt.plan_entry(sig,authority(sig.instrument),realized_equity=Decimal('100000'),budget=rt.begin_batch(realized_equity=Decimal('100000'),available_cash=Decimal('1000000')))
        assert a.kind=='ENTRY'
        initial=rt.confirm_entry_position(a.idempotency_key,a.expected_position_quantity,verified_fill_entry=Decimal(r['entry']),fill_authority='OFFLINE_SYNTHETIC_VERIFIED')
        percent_position_stop_payload(initial); rt.confirm_protective_stop(initial.idempotency_key,f'synthetic-{i}-0'); stops+=1
        p=rt.open_positions()[sig.instrument]; exec_stop=p['executable_initial_stop']; exec_r=p['executable_initial_r']
        rt.close(); rt=ProductionRuntime(args.out/f'trade-{i:04}.sqlite3',execution_revision=EXECUTION_REVISION)
        exit_time=''; exit_price=''
        for stamp,b in low.loc[low.index>pd.Timestamp(r['timestamp'])].iterrows():
            event=CompletedBar(stamp.to_pydatetime(),float(b.Open),float(b.High),float(b.Low),float(b.Close),float(b.ATR))
            action=rt.manage_completed_bar(sig.instrument,event,observed_position_quantity=a.expected_position_quantity); bars+=1
            p=rt.open_positions()[sig.instrument]
            require_on_grid(p['current_stop'],authority(sig.instrument).price_step)
            if p['trail1']['stored_candidate'] is not None: require_on_grid(p['trail1']['stored_candidate'],authority(sig.instrument).price_step)
            if action is None: continue
            if action.kind=='PROTECTIVE_STOP_REPLACE':
                percent_position_stop_payload(action); replacements+=1; stops+=1
                rt.confirm_protective_stop(action.idempotency_key,f'synthetic-{i}-{replacements}')
            else:
                assert action.kind=='EMERGENCY_EXIT_REQUIRED'
                exit_time=stamp.isoformat(); exit_price=str(action.reference_price); exits+=1
                break
        if exit_time!=r['exit_timestamp']: changed_exit_times+=1
        rows.append({'instrument':sig.instrument,'lifecycle':r['lifecycle'],'fold_id':r['fold_id'],'trade_id':sig.trade_id,
                     'reference_entry':r['entry'],'raw_stop':r['initial_stop'],'executable_stop':exec_stop,
                     'raw_r':r['initial_r'],'executable_r':exec_r,'raw_exit_time':r['exit_timestamp'],
                     'executable_exit_time':exit_time,'executable_offline_stop_fill':exit_price,
                     'fill_authority':'OFFLINE_REFERENCE_PRICE_ONLY','status':'PASS'})
        rt.close()
    pd.DataFrame(rows).to_csv(args.out/'execution_comparison.csv',index=False)
    result={'authentication':auth,'raw_replays':raw_results,'all_raw_signal_projection_checks':projection_checks,
            'independent_rational_projection_sizing_checks':projection_checks,
            'frozen_entry_paths':len(rows),'completed_executable_paths':exits,'terminal_open_paths':len(rows)-exits,
            'management_bars':bars,'protective_prices_checked':stops,'replacement_count':replacements,
            'changed_exit_timestamps':changed_exit_times,
            'classifications':{'RAW_RESEARCH_CONFORMANCE':'PASS','EXECUTABLE_STOP_CONFORMANCE':'PASS',
                               'R15_MARGIN_CONFORMANCE':'PASS','PROTECTIVE_STOP_CONFORMANCE':'PASS',
                               'ACTUAL_FILL_AUTHORITY':'BLOCKED','PRODUCTION_READY':'NO'},
            'scope':'Fixed frozen entry paths; synthetic equity=100000, cash=1000000, LONG margin=100, SHORT=120; no adjusted PnL or OOS claim; actual FINAM fills/spec histories unavailable',
            'real_order_endpoint_calls':0}
    (args.out/'results.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ('authentication','scope')},indent=2))

if __name__=='__main__': main()
