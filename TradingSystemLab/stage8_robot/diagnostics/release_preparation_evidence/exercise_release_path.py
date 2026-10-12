"""Offline synthetic legacy -> exact committed readonly runner oracle.
Usage: python exercise_release_path.py <new-external-output> <exact-Stage5-root> --preview
Only external IO is substituted. Git/blob/manifest/runtime bindings remain real.
No LIVE snapshot, credentials or socket connections are used.
"""
import json,sqlite3,socket,sys
from pathlib import Path
from decimal import Decimal as D
from datetime import datetime,timezone
root=Path(__file__).resolve().parents[4];sys.path[:0]=[str(root),str(root/'src')]
def deny(*a,**k):raise AssertionError('OFFLINE_NETWORK_FORBIDDEN')
socket.socket.connect=deny;socket.socket.connect_ex=deny;socket.create_connection=deny
from TradingSystemLab.stage8_robot import release_preparation as r,release_candidate_runner as runner
from TradingSystemLab.stage8_robot.production_service import ProductionService
from TradingSystemLab.stage8_robot.production_history import load_stage5_seed_open_h1,continuation_payload_from_frame
from TradingSystemLab.stage8_robot.tests.test_stop_tick_grid_amendment import signal
from TradingSystemLab.stage8_robot.tests.test_stage8_12_production_runtime import authority
workspace=Path(sys.argv[1]);workspace.mkdir()
data=Path(sys.argv[2]);account='synthetic-release-contract';commit=r.checkout_commit()
source=workspace/'legacy-fixture';svc=ProductionService(source,data,object(),account,commit);rt=svc.runtime
rt.set_realized_equity(D('100000'));rt.store.put('starting_realized_equity','100000')
rt.store.put('production_positions',{});rt.store.put('production_service_cycle_count',9258)
sig=signal(ticks='5');action=rt.plan_entry(sig,authority(),realized_equity=D('100000'),budget=rt.begin_batch(realized_equity=D('100000'),available_cash=D('1000000')))
rt.store.transition_intent(action.idempotency_key,'CLOSED','synthetic-history-order')
rt.store.persist_fill({'fill_id':'synthetic-history-fill','broker_order_id':'synthetic-history-order','trade_id':sig.trade_id,'quantity':action.quantity,'price':'100','timestamp':sig.timestamp.isoformat()})
for symbol in r.INSTRUMENTS:
 seed=load_stage5_seed_open_h1(data,symbol);latest=seed.index.max()
 rt.store.put(f'production_h1_continuation:{symbol}',continuation_payload_from_frame(seed.iloc[0:0],symbol))
 rt.store.put(f'production_expected_h1:{symbol}',latest.isoformat())
 rt.store.put(f'last_evaluated_h1:{symbol}',(latest+__import__('pandas').Timedelta('1h')).isoformat())
 rt.store.put(f'last_managed_h1:{symbol}',(latest+__import__('pandas').Timedelta('1h')).isoformat())
 rt.store.put(f'signal_sequence:{symbol}',42);rt.store.put(f'pending_signal:{symbol}',None)
snapshot=workspace/'external-legacy-snapshot.sqlite3';db=sqlite3.connect(snapshot);rt.store.db.backup(db);db.close();svc.close()
broker={'observed_at':'2026-09-16T01:00:00+00:00','account':{'account_id':account,'status':'ACCOUNT_ACTIVE','positions':[],'equity':{'value':'100000'},'unrealized_profit':{'value':'0'},'type':'FORTS','portfolio_forts':{'available_cash':{'value':'1000000'},'money_reserved':{'value':'0'}}},'orders':{'orders':[]}}
brokerpath=workspace/'broker-synthetic.json';brokerpath.write_text(json.dumps(broker,sort_keys=True)+'\n')
assert r.main(['--snapshot',str(snapshot),'--snapshot-sha256',r.sha(snapshot),'--out',str(workspace/'prepared'), '--stage5-data-root',str(data),'--broker-snapshot',str(brokerpath),'--broker-snapshot-sha256',r.sha(brokerpath),'--account-hash',r.digest(account),'--source-commit',commit,'--candidate-commit',commit])==0
manifest=workspace/'prepared/release-manifest.json';value=json.loads(manifest.read_text())
if '--preview' in sys.argv:
 calls=[]
 class OfflineAPI:
  def __init__(self,*a):pass
  def connect_readonly(self):calls.append('FAKE_READONLY_SESSION')
  def account(self,*a):calls.append('FAKE_GET_ACCOUNT');return broker['account']
  def orders(self,*a):calls.append('FAKE_GET_ORDERS');return broker['orders']
  def place_order(self,*a):raise AssertionError('ORDER_ENDPOINT_FORBIDDEN')
  place_sltp_order=place_order;cancel_order=place_order
 # Substitute only external IO. Actual git/blob/manifest/runtime validation is untouched.
 runner.CandidateReadonlyAPI=OfflineAPI
 import os
 os.environ.update(FINAM_MODE='STAGE8_12_PRODUCTION',FINAM_API_SECRET='synthetic-no-token',FINAM_REAL_ACCOUNT_ID=account)
 assert runner.main(['--runtime-root',value['runtime_root'],'--stage5-data-root',str(data),'--accepted-commit',commit,'--release-manifest',str(manifest),'--release-manifest-sha256',r.sha(manifest)])==0
 assert calls==['FAKE_READONLY_SESSION','FAKE_GET_ACCOUNT','FAKE_GET_ORDERS']
 value['exact_committed_runner_dispatch']='PASS';value['api_calls']=calls
value['fixture_provenance']='SYNTHETIC_LEGACY_SERVICE_DATABASE_WITH_EXACT_FROZEN_STAGE5_SEEDS_NOT_INTEL_SNAPSHOT'
value['source_sha256_after']=r.sha(snapshot);assert value['source_sha256_after']==value['snapshot_sha256']
(workspace/'exercise-result.json').write_text(json.dumps(value,indent=2,sort_keys=True)+'\n')
print(json.dumps({'fixture_provenance':value['fixture_provenance'],'source_unchanged':True,'causal_values_preserved':value['causal_state_preserved'],'rollback_exact':value['rollback_exact'],'candidate_commit':commit,'real_order_endpoint_calls':0,'live_changes':'NONE','exact_committed_runner_dispatch':value.get('exact_committed_runner_dispatch','PENDING_COMMIT')},sort_keys=True))
