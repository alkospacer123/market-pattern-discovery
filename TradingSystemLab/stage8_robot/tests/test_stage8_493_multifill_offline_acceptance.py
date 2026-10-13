"""Independent offline acceptance matrix. NO FINAM/API/Task connection."""
import json
from pathlib import Path
import importlib.util
import sqlite3
import subprocess
import sys
import pytest

SRC=Path(__file__).resolve().parents[1] / 'diagnostics' / 'stage8_493_multifill_offline_acceptance.py'
spec=importlib.util.spec_from_file_location('stage8_493_sim', SRC)
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

def trace():
    b=dict(spec=m.SPEC, identity=m.IDENTITY, account_id='synthetic-account',
           symbol='CNYRUBF@RTSX',direction='LONG',stop_price='12.740')
    f1=dict(fill_id='synthetic-f1',account_id=b['account_id'],order_id='synthetic-entry',
            symbol=b['symbol'],side='SIDE_BUY',quantity=1,price='12.748')
    f2=dict(fill_id='synthetic-f2',account_id=b['account_id'],order_id='synthetic-entry',
            symbol=b['symbol'],side='SIDE_BUY',quantity=1,price='12.749')
    e=[
        dict(kind='entry_intent',intent_key='synthetic-entry-intent',requested_quantity=2),
        dict(kind='entry_post_ack',intent_key='synthetic-entry-intent',order_id='synthetic-entry'),
        dict(kind='position',quantity=1,fills=[f1]),
        dict(kind='stop_intent',intent_key='synthetic-stop-intent',symbol=b['symbol'],
             side='SIDE_SELL',sl_price='12.740',sl_qty_measure='SLTP_QTY_MEASURE_PERCENT',
             quantity_sl='100',valid_before='VALID_BEFORE_GOOD_TILL_CANCEL'),
        dict(kind='stop_post_ack',intent_key='synthetic-stop-intent',order_id='synthetic-stop'),
        dict(kind='stop_observed',order_id='synthetic-stop',active=True,symbol=b['symbol'],
             side='SIDE_SELL',sl_price='12.740',sl_qty_measure='SLTP_QTY_MEASURE_PERCENT',
             quantity_sl='100',covered_current_quantity=1),
        dict(kind='position',quantity=2,fills=[f1,f2]),
        dict(kind='stop_observed',order_id='synthetic-stop',active=True,symbol=b['symbol'],
             side='SIDE_SELL',sl_price='12.740',sl_qty_measure='SLTP_QTY_MEASURE_PERCENT',
             quantity_sl='100',covered_current_quantity=2),
        dict(kind='terminal_flat',broker_quantity=0,active_orders=0,unresolved_intents=0,
             stop_terminal=True,entry_terminal=True)
    ]
    return dict(schema_id=m.SCHEMA,binding=b,events=e)

def execute(tmp_path,t=None):
    return m.run(trace() if t is None else t,tmp_path)

def test_positive_full_progression_and_no_real_authority(tmp_path):
    r=execute(tmp_path)
    assert r['classification']=='OFFLINE_MULTIFILL_GROWTH_SIMULATION_PASS_NOT_REAL_AUTHORITY'
    assert r['journal_event_count']==9 and r['real_order_endpoint_calls']==0
    assert r['live_production_ready'] is False and r['partial_growth_observed_synthetic'] is True
    assert r['broker_percent_coverage_real']=='NOT_VERIFIED'
    assert m.Journal(m.isolated_db(tmp_path),trace()['binding']).size==9

def test_restart_mid_fills_append_no_second_post(tmp_path):
    t=trace();prefix=dict(t,events=t['events'][:6]);r=execute(tmp_path,prefix)
    assert r['classification']=='INCOMPLETE' and r['journal_event_count']==6
    assert execute(tmp_path,t)['classification']=='OFFLINE_MULTIFILL_GROWTH_SIMULATION_PASS_NOT_REAL_AUTHORITY'
    j=m.Journal(m.isolated_db(tmp_path),t['binding'])
    assert j.state['entry_posts']==1 and j.state['stop_posts']==1
    j.close()

def test_exact_duplicate_replay_idempotent(tmp_path):
    t=trace();execute(tmp_path,t)
    j=m.Journal(m.isolated_db(tmp_path),t['binding']);sz=j.size
    j.record(2,t['events'][1]);assert j.size==sz
    j.close()

def test_conflicting_duplicate_replay_blocks(tmp_path):
    t=trace();execute(tmp_path,t)
    j=m.Journal(m.isolated_db(tmp_path),t['binding']);e=dict(t['events'][1],order_id='foreign')
    with pytest.raises(m.Blocked,match='EVENT_REPLAY_CONFLICT'):j.record(2,e)
    j.close()

def test_crash_before_commit_replays_without_duplicate_post(tmp_path):
    t=trace();j=m.Journal(m.isolated_db(tmp_path),t['binding'])
    j.record(1,t['events'][0]);
    with pytest.raises(m.Blocked,match='SYNTHETIC_BEFORE_COMMIT_CRASH'):j.record(2,t['events'][1],simulate_crash=True)
    assert j.size==1;j.close()
    j=m.Journal(m.isolated_db(tmp_path),t['binding'])
    assert j.size==1
    j.record(2,t['events'][1]);assert j.state['entry_posts']==1
    j.close()

@pytest.mark.parametrize('mutator',[
    lambda t:t['events'].pop(0), # no entry intent
    lambda t:t['events'].insert(2,dict(t['events'][1])), # duplicate synthetic POST
    lambda t:t['events'].__setitem__(2,dict(t['events'][2],quantity=2,fills=t['events'][6]['fills'])),
    lambda t:t['events'].pop(5), # no stop at 1
    lambda t:t['events'].pop(7), # no stop after growth
    lambda t:t['events'][3].update(quantity_sl='50'),
    lambda t:t['events'][3].update(sl_qty_measure='SLTP_QTY_MEASURE_UNITS'),
    lambda t:t['events'][3].update(side='SIDE_BUY'),
    lambda t:t['events'][3].update(sl_price='12.739'),
    lambda t:t['events'][5].update(covered_current_quantity=2),
    lambda t:t['events'][7].update(active=False),
    lambda t:t['events'][7].update(order_id='foreign'),
    lambda t:t['events'][8].update(active_orders=1),
    lambda t:t['events'][8].update(unresolved_intents=1),
    lambda t:t['events'][8].update(stop_terminal=False),
    lambda t:t['events'][8].update(entry_terminal=False),
    lambda t:t['events'][8].update(broker_quantity=1),
    lambda t:t['events'][6]['fills'][0].update(quantity=2),
    lambda t:t['events'][6]['fills'][1].update(fill_id='synthetic-f1'),
    lambda t:t['events'][6]['fills'][1].update(order_id='foreign'),
    lambda t:t['events'][6]['fills'][1].update(side='SIDE_SELL'),
    lambda t:t['events'][6]['fills'][1].update(account_id='foreign'),
    lambda t:t['events'][6]['fills'].__setitem__(0,dict(t['events'][6]['fills'][0],price='12.760')),
    lambda t:t['events'][6]['fills'].pop(0),
    lambda t:t['events'][6].update(quantity=3),
    lambda t:t['events'][6]['fills'][1].update(price='12.7495'),
    lambda t:t['events'][6]['fills'][1].update(price='NaN'),
    lambda t:t['events'][6]['fills'][1].update(price='-1'),
])
def test_fail_closed_on_invalid_broker_progression(tmp_path,mutator):
    t=trace();mutator(t)
    with pytest.raises(m.Blocked):execute(tmp_path,t)

@pytest.mark.parametrize('reason',['ENTRY_ACK_UNKNOWN','STOP_ACK_UNKNOWN','BROKER_HISTORY_UNAVAILABLE','FILL_PRICE_UNVERIFIED','ORDER_STATUS_UNKNOWN'])
def test_uncertainty_blocks_further_actions(tmp_path,reason):
    t=trace();t['events'].insert(3,{'kind':'uncertain','reason':reason})
    with pytest.raises(m.Blocked,match='TERMINAL_OR_HALTED_REPLAY_FORBIDDEN'):
        execute(tmp_path,t)

@pytest.mark.parametrize('change',[
    {'spec':'wrong'},{'identity':'other'},{'symbol':'unknown'},
    {'direction':'invalid'},{'account_id':''},
])
def test_trace_binding_rejected(tmp_path,change):
    t=trace();t['binding'].update(change)
    with pytest.raises(m.Blocked):execute(tmp_path,t)

def test_different_identity_same_database_fails(tmp_path):
    t=trace();execute(tmp_path,t)
    b=dict(t['binding'],account_id='new-account')
    with pytest.raises(m.Blocked,match='JOURNAL_IDENTITY_MISMATCH'):
        m.Journal(m.isolated_db(tmp_path),b)

def test_tampered_journal_blocks_on_restart(tmp_path):
    t=trace();execute(tmp_path,t)
    with sqlite3.connect(m.isolated_db(tmp_path)) as db:
        db.execute("update events set payload='{}' where seq=5")
    with pytest.raises(m.Blocked,match='JOURNAL_EVENT_TAMPERED'):
        m.Journal(m.isolated_db(tmp_path),t['binding'])

def test_scratch_rejects_live_runtime_path(tmp_path):
    live=tmp_path/'runtime';live.mkdir()
    with pytest.raises(m.Blocked,match='LIVE_RUNTIME_OR_PRODUCTION_PATH_FORBIDDEN'):
        m.isolated_db(live)

def test_run_cli_execute_is_always_refused(tmp_path):
    p=tmp_path/'trace.json';p.write_text(json.dumps(trace()))
    proc=subprocess.run([sys.executable,str(SRC),'--trace',str(p),'--scratch-root',str(tmp_path),'--execute'],capture_output=True,text=True)
    assert proc.returncode==1 and 'BLOCKED_NO_REAL_ORDER_TRANSPORT' in proc.stdout
    assert not (tmp_path/m.DATABASE_NAME).exists()

def test_source_contains_no_real_broker_or_task_execution():
    s=SRC.read_text().lower()
    for forbidden in ['import finamapi','import requests','from urllib.request','place_order(','place_sltp_order(',
                      'cancel_order(','stop-scheduledtask','enable-scheduledtask','subprocess.run(']:
        assert forbidden not in s
    assert 'offline_only' in s and 'blocked_no_real_order_transport' in s


def test_immediate_two_contract_fill_cannot_fake_growth(tmp_path):
    t=trace()
    t['events'][2]['quantity']=2
    t['events'][2]['fills']=t['events'][6]['fills']
    with pytest.raises(m.Blocked,match='IMMEDIATE_TWO_CONTRACT_FILL_NOT_GROWTH_PROOF'):
        execute(tmp_path,t)


def test_growth_before_first_stop_ack_is_forbidden(tmp_path):
    t=trace()
    growth=t['events'].pop(6)
    t['events'].insert(5,growth)
    with pytest.raises(m.Blocked,match='EXPOSURE_GREW_BEFORE_STOP_ACTIVE'):
        execute(tmp_path,t)


def test_symmetric_short_synthetic_coverage(tmp_path):
    t=trace();b=t['binding'];b['direction']='SHORT';b['stop_price']='12.760'
    for event in t['events']:
        if event['kind']=='position':
            for fill in event['fills']:fill['side']='SIDE_SELL'
        if event['kind'] in ('stop_intent','stop_observed'):
            event['side']='SIDE_BUY';event['sl_price']='12.760'
    assert execute(tmp_path,t)['classification']=='OFFLINE_MULTIFILL_GROWTH_SIMULATION_PASS_NOT_REAL_AUTHORITY'


def test_only_synthetic_account_can_enter_replay(tmp_path):
    t=trace();t['binding']['account_id']='real_account_id'
    with pytest.raises(m.Blocked,match='TRACE_IDENTITY_INVALID'):
        execute(tmp_path,t)
