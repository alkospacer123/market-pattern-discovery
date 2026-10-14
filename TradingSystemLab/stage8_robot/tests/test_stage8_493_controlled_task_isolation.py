"""No-task/no-broker offline regressions for controlled #493 isolation."""
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace
import sys
import pytest

ROOT=Path(__file__).resolve().parent
P=ROOT/'stage8_493_post_isolation_broker_readonly.py'
spec=importlib.util.spec_from_file_location('post',P)
post=importlib.util.module_from_spec(spec)
spec.loader.exec_module(post)


def test_only_readonly_account_and_orders_transport_allowed():
    text=P.read_text()
    assert "method == 'POST' and endpoint in {'/v1/sessions','/v1/sessions/details'}" in text
    assert "method == 'GET' and payload is None and endpoint in {path, path+'/orders'}" in text
    assert "raise Blocked('FINAM_ENDPOINT_FORBIDDEN')" in text
    assert 'FINAM_REAL_ACCOUNT_ID' not in text
    assert 'FINAM_API_SECRET' not in text
    assert 'place_order' not in text
    assert 'cancel_order' not in text


def sample_root(tmp_path):
    safe=tmp_path/'safety';safe.mkdir()
    diag=tmp_path/'diagnostics';diag.mkdir()
    (safe/'stage8-trading-kill-switch.json').write_text(json.dumps(dict(schema_id='stage8_trading_kill_switch.v1',production_specification_id=post.SPEC,state='HALTED')))
    import hashlib
    (diag/'stage8-12-4-production-heartbeat.json').write_text(json.dumps(dict(schema_id='stage8_12_4_production_heartbeat.v1',production_specification_id=post.SPEC,active_identity=post.IDENTITY,accepted_code_commit=post.LIVE_SHA,account_hash=hashlib.sha256(b'account-a').hexdigest(),open_position_count=0,unresolved_intent_count=0,active_protective_stop_count=0,timestamp='2020-01-01T00:00:00Z')))
    return tmp_path


def test_stale_heartbeat_is_not_used_to_block_stopped_service(tmp_path):
    post.local_gate(sample_root(tmp_path),'account-a')

@pytest.mark.parametrize('key,value',[
    ('state','ARMED'),('production_specification_id','wrong'),('schema_id','wrong')])
def test_switch_required(tmp_path,key,value):
    root=sample_root(tmp_path)
    p=root/'safety/stage8-trading-kill-switch.json'
    d=json.loads(p.read_text());d[key]=value;p.write_text(json.dumps(d))
    with pytest.raises(post.Blocked):post.local_gate(root,'account-a')

@pytest.mark.parametrize('key,value',[
    ('active_identity','incorrect'),('accepted_code_commit','0'*40),
    ('account_hash','x'),('unresolved_intent_count',2),('open_position_count',1),
    ('active_protective_stop_count',1)])
def test_heartbeat_frozen_identity_and_last_zero_state(tmp_path,key,value):
    root=sample_root(tmp_path)
    p=root/'diagnostics/stage8-12-4-production-heartbeat.json'
    d=json.loads(p.read_text());d[key]=value;p.write_text(json.dumps(d))
    with pytest.raises(post.Blocked):post.local_gate(root,'account-a')


def test_known_identity_wrong_account_rejected(tmp_path):
    with pytest.raises(post.Blocked):post.local_gate(sample_root(tmp_path),'account-b')


def test_task_mutator_only_has_safe_bounded_control_actions():
    code=(ROOT/'stage8-493-controlled-task-isolation.ps1').read_text().lower()
    assert 'disable-scheduledtask -taskname $task_name' in code
    assert 'stop-scheduledtask -taskname $task_name' in code
    assert code.index('disable-scheduledtask -taskname $task_name') < code.index('stop-scheduledtask -taskname $task_name')
    for forbidden in ('stop-process','start-scheduledtask','enable-scheduledtask','set-scheduledtask',
                      'remove-scheduledtask','get-tradingcredential','finam_api_secret','delete from intents',
                      'place_order','cancel_order','set-content'):
        assert forbidden not in code
    assert 'if (-not $execute)' in code
    assert 'fresh_pre_isolation_gate_blocked' in code
    assert 'task_definition_backup_sha256=' in code
    assert 'blocked_operator_recovery_required' in code
    assert 'no_real_orders' in code
    assert 'real_order_authorized=no' in code


def test_post_isolation_only_reads_and_never_changes_task():
    code=(ROOT/'stage8-493-post-isolation-readonly.ps1').read_text().lower()
    for forbidden in ('disable-scheduledtask','stop-scheduledtask','enable-scheduledtask',
                      'stop-process','set-scheduledtask','get-tradingcredential',
                      'invoke-restmethod','place_order','cancel_order'):
        assert forbidden not in code
    for signal in ('production_process_orphan_present','production_lock_handle_not_quiescent',
                   'finam_post_stop_blocked','sqlite_post_stop_before_after=pass','classifi'+'cation=post_isolation_readonly_pass_no_trade_authority'):
        assert signal in code


def test_scripts_powershell_lowercase_commands():
    import re
    for p in ROOT.glob('*.ps1'):
        code=p.read_text()
        assert not re.search(r'(?m)^\s*[A-Z]+-[A-Za-z]',code)
