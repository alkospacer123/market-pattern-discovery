"""Independent source/authority regression; only synthetic temporary inputs."""
import ast
from copy import deepcopy
from datetime import timedelta
import json
from pathlib import Path
import os
import socket
import sqlite3
import subprocess
import urllib.request
import pytest
from cc.models import RobotId, SourceKind, State
from cc.freshness import display_state
from cc.providers import h1_export as receiver
from cc.providers.h1_contract import SPEC, ACTIVE, ACCEPTED_COMMIT, validate
from cc.providers.h1_readonly import canonical_digest
from cc.providers.source_contract import SCHEMA
from exporter.snapshot import collect, policy_check


@pytest.fixture
def policy():
    return dict(schema_id='cc03.private-source-policy.v1', source_id='CC03-H1-TESTONLY01',
                account_alias='H1-TESTONLY', binding_id='a'*64, expected_account_hash='b'*64,
                installed_code_commit=ACCEPTED_COMMIT, installed_commit_verified=True,
                sources_acl_approved=True, binding_approved=True,
                heartbeat_root=r'C:\TESTONLY\diagnostics', heartbeat_root_id=[1,2,3],
                kill_switch_root=r'C:\TESTONLY\safety', kill_switch_root_id=[1,2,4])


@pytest.fixture
def sources(now):
    at = now.isoformat()
    return {
        'stage8-12-4-production-heartbeat.json': dict(
            schema_id='stage8_12_4_production_heartbeat.v1', production_specification_id=SPEC,
            active_identity=ACTIVE, accepted_code_commit=ACCEPTED_COMMIT, account_hash='b'*64,
            timestamp=at, last_successful_finam_api_contact=at, reconciliation_status='PASS',
            unresolved_intent_count=0, health_status='HEALTHY', cycle_count=1,
            open_position_count=0, active_protective_stop_count=0, position_protection=[]),
        'stage8-trading-kill-switch.json': dict(schema_id='stage8_trading_kill_switch.v1',
            production_specification_id=SPEC, state='HALTED', generation=1,
            updated_utc=(now-timedelta(days=2)).isoformat())}


def export(policy, sources, now):
    calls = []
    def read(root, name, pin):
        calls.append((root,name,pin))
        return json.dumps(sources[name]).encode()
    result = collect(policy, now, read)
    assert len(calls) == 2
    assert calls[0][2] == policy['heartbeat_root_id'] and calls[1][2] == policy['kill_switch_root_id']
    return result


def approved(policy, **kwargs):
    return receiver.ReceiverPolicy(source_id=policy['source_id'], account_alias=policy['account_alias'],
                                   binding_id=policy['binding_id'], snapshot=60, heartbeat=40,
                                   kill_switch=20, reconciliation=40, **kwargs)


def get(value, policy, now, tmp_path, monkeypatch):
    value['payload_sha256'] = canonical_digest(value)
    (tmp_path/'h1.snapshot.json').write_text(json.dumps(value))
    monkeypatch.setattr(receiver,'EXPORT_ROOT',tmp_path)
    return receiver.H1ExportProvider(policy).snapshot(RobotId.H1,'READONLY_EXPORT',now)


def test_partial_export_sanitized_no_inferred_authority(policy, sources, now):
    # Raw IDs in unused source protection records never reach the output.
    sources['stage8-12-4-production-heartbeat.json']['position_protection'] = [{'trade_id':'SECRET_RAW_BROKER_ID'}]
    value = export(policy, sources, now)
    validate(value, SCHEMA)
    raw = json.dumps(value)
    assert 'SECRET_RAW_BROKER_ID' not in raw and 'b'*64 not in raw and 'TESTONLY\\' not in raw
    assert value['identity']['account_binding'] == 'MATCHED_LOCAL_POLICY'
    assert value['kill_switch']['observed_at'] == now.isoformat()
    assert value['kill_switch']['value']['updated_at'] != now.isoformat()
    for name in ('task','candles','finances','execution'):
        assert value[name]['status'] == 'NEEDS_SOURCE_APPROVAL' and value[name]['value'] is None
    assert all(word not in raw for word in ('FILL_CONFIRMED','ACTIVE_SLTP','equity','open_position_count'))


@pytest.mark.parametrize('field,bad', [('account_hash','c'*64),('accepted_code_commit','0'*40),
                                      ('production_specification_id','WRONG'),('active_identity','WRONG'),
                                      ('schema_id','fixture'),('health_status','HALTED'),('unresolved_intent_count',False)])
def test_source_identity_and_types_fail_closed(policy,sources,now,field,bad):
    sources['stage8-12-4-production-heartbeat.json'][field] = bad
    value = export(policy,sources,now)
    assert value['heartbeat']['value'] is None and value['reconciliation']['value'] is None
    assert value['identity']['account_binding'] == 'UNVERIFIED'


@pytest.mark.parametrize('field,bad', [('installed_code_commit','0'*40),('account_alias','FIXTURE-H1'),
    ('installed_commit_verified',False),('sources_acl_approved',False),('heartbeat_root_id',[]),
    ('binding_approved','true')])
def test_private_policy_rejected(policy,field,bad):
    policy[field] = bad
    with pytest.raises(ValueError): policy_check(policy)


def test_halted_requires_independent_fresh_approved_observation(policy,sources,now,tmp_path,monkeypatch):
    sources['stage8-12-4-production-heartbeat.json']['timestamp'] = (now-timedelta(days=1)).isoformat()
    sources['stage8-12-4-production-heartbeat.json']['last_successful_finam_api_contact'] = (now-timedelta(days=1)).isoformat()
    value = export(policy,sources,now)
    result = get(value,approved(policy),now,tmp_path,monkeypatch)
    assert result.status.state == State.HALTED and display_state(result.status,now) == State.HALTED
    assert result.positions is None and result.portfolio.equity is None and result.status.open_positions is None
    assert result.status.task_state is None and result.status.trading_allowed is False
    assert get(value,approved(policy),now+timedelta(seconds=21),tmp_path,monkeypatch).status.state == State.STALE
    assert get(value,receiver.ReceiverPolicy(),now,tmp_path,monkeypatch).status.state == State.UNKNOWN


@pytest.mark.parametrize('binding', ['source_id','account_alias','binding_id','account_binding'])
def test_checksum_cannot_supply_source_or_account_trust(policy,sources,now,tmp_path,monkeypatch,binding):
    value = export(policy,sources,now)
    replacement = {'source_id':'CC03-H1-DIFFERENT','account_alias':'H1-DIFFERENT','binding_id':'c'*64,'account_binding':'UNVERIFIED'}
    value['identity'][binding] = replacement[binding]
    result = get(value,approved(policy),now,tmp_path,monkeypatch)
    assert result.status.state == State.UNKNOWN and result.readonly_identity is None
    assert result.status.provenance.account_scope == 'UNBOUND-H1'


def test_unknown_cadence_and_calendar_never_inferred(policy,sources,now,tmp_path,monkeypatch):
    value = export(policy,sources,now)
    no_ttl = receiver.ReceiverPolicy(source_id=policy['source_id'],account_alias=policy['account_alias'],binding_id=policy['binding_id'])
    result = get(value,no_ttl,now,tmp_path,monkeypatch)
    assert result.status.state == State.UNKNOWN
    assert all(row.state == State.UNKNOWN for row in result.readonly_observations)
    assert all(row.state == State.UNKNOWN for row in result.instruments)


def test_unresolved_unhealthy_and_no_task_no_healthy(policy,sources,now,tmp_path,monkeypatch):
    sources['stage8-trading-kill-switch.json']['state']='ARMED'
    value=export(policy,sources,now)
    assert get(value,approved(policy),now,tmp_path,monkeypatch).status.state == State.UNKNOWN
    sources['stage8-12-4-production-heartbeat.json']['health_status']='UNHEALTHY'
    value=export(policy,sources,now)
    assert get(value,approved(policy),now,tmp_path,monkeypatch).status.state == State.UNHEALTHY
    sources['stage8-12-4-production-heartbeat.json']['unresolved_intent_count']=1
    value=export(policy,sources,now)
    assert get(value,approved(policy),now,tmp_path,monkeypatch).status.state == State.UNRESOLVED


def test_corrupt_oversize_and_secret_error_missing_exporter(policy,sources,now,tmp_path,monkeypatch):
    monkeypatch.setattr(receiver,'EXPORT_ROOT',tmp_path)
    provider=receiver.H1ExportProvider(approved(policy))
    for raw in (b'{',b' '*131073,b'{"token":"SECRET_TOKEN"}'):
        (tmp_path/'h1.snapshot.json').write_bytes(raw)
        result=provider.snapshot(RobotId.H1,'',now)
        assert result.status.state==State.UNKNOWN and 'SECRET_TOKEN' not in repr(result)
    (tmp_path/'h1.snapshot.json').unlink()
    assert provider.snapshot(RobotId.H1,'',now).status.state==State.UNKNOWN


def test_exporter_no_network_db_process_or_h1_writes(policy,sources,now,monkeypatch):
    def forbidden(*args,**kwargs): raise AssertionError('external call')
    for module,name in ((socket,'create_connection'),(sqlite3,'connect'),(subprocess,'Popen'),
                        (urllib.request,'urlopen'),(os,'open'),(os,'system')):
        monkeypatch.setattr(module,name,forbidden)
    value=export(policy,sources,now)
    assert value['heartbeat']['status']=='AVAILABLE'
    root=Path(__file__).parents[1]
    for path in (root/'exporter').rglob('*.py'):
        tree=ast.parse(path.read_text())
        for node in ast.walk(tree):
            if isinstance(node,ast.ImportFrom):
                assert not (node.module or '').startswith(('TradingSystemLab','IntradayLab','finam','sqlite3'))
            if isinstance(node,ast.Import):
                assert not any(n.name.startswith(('TradingSystemLab','IntradayLab','finam','sqlite3','subprocess','socket')) for n in node.names)


def test_exporter_absence_ui_m15_controls(monkeypatch,tmp_path):
    from streamlit.testing.v1 import AppTest
    monkeypatch.setattr(receiver,'EXPORT_ROOT',tmp_path)
    app=AppTest.from_file(str(Path(__file__).parents[1]/'app.py'),default_timeout=15).run()
    app.selectbox(key='h1-source').select('READONLY_EXPORT').run()
    assert not app.exception
    content='\n'.join(str(x.value) for k in ('caption','info','warning','markdown') for x in getattr(app,k))
    assert 'H1 сохраняет HALTED' not in content and 'READONLY_EXPORT' in content
    app.radio[0].set_value('Монитор M15').run()
    text='\n'.join(str(x.value) for k in ('caption','info','warning','markdown') for x in getattr(app,k))
    assert 'NOT_DEPLOYED' in text and 'DEMO-M15' in text
    app.radio[0].set_value('Управление').run()
    assert not app.exception and len(app.button)==10 and all(x.disabled for x in app.button)


def test_publication_is_atomic_and_only_in_own_directory(policy,sources,now,tmp_path,monkeypatch):
    import types
    from exporter import snapshot as writer
    value=export(policy,sources,now)
    destination=tmp_path/'h1.snapshot.json'
    destination.write_bytes(b'old')
    replace_calls=[]
    def replace(source,target):
        assert destination.read_bytes()==b'old'
        assert Path(source).parent==tmp_path and Path(target)==destination
        validate(json.loads(Path(source).read_bytes()),SCHEMA)
        replace_calls.append((source,target)); os.replace(source,target)
    class API:
        def volume(self,path): pass
        def open(self,path,directory): return path
        def info(self,handle,path,directory): return (1,2,3)
        def close(self,handle): pass
    monkeypatch.setattr(writer,'EXPORT_ROOT',tmp_path)
    monkeypatch.setattr(writer,'WinAPI',API)
    monkeypatch.setattr(writer,'components',lambda root,name: ([root],str(Path(root)/name)))
    monkeypatch.setattr(writer,'os',types.SimpleNamespace(name='nt',fdopen=os.fdopen,fsync=os.fsync,
                        replace=replace,path=os.path,unlink=os.unlink))
    writer.publish(value)
    assert len(replace_calls)==1 and json.loads(destination.read_bytes())==value
    assert list(tmp_path.iterdir())==[destination]
    value['payload_sha256']='0'*64
    with pytest.raises(ValueError): writer.publish(value)


def test_deployment_scripts_preview_and_no_production_mutators():
    root=Path(__file__).parents[1]/'deployment'
    scripts=list(root.glob('*.ps1'))
    assert len(scripts)==8  # shared validator plus seven operator entrypoints
    for path in scripts:
        source=path.read_text()
        if path.name!='Common.ps1':
            assert '[switch]$Execute' in source and 'if (-not $Execute)' in source and 'PREVIEW:' in source
        assert not any(verb in source for verb in ('Start-ScheduledTask','Stop-ScheduledTask','Enable-ScheduledTask',
            'Disable-ScheduledTask','Set-ScheduledTask','Register-ScheduledTask','Set-Acl','Invoke-WebRequest',
            'FINAM_FILL_AUTHORITY_VERIFIED','Stop-Process','git pull'))
    assert "'C:\\TSLControlCenterApp'" in (root/'Common.ps1').read_text()
    assert '--no-index' in (root/'Install.ps1').read_text()
    assert 'Assert-CurrentIdentity $PanelSid' in (root/'Start-Panel.ps1').read_text()
    assert 'Assert-CurrentIdentity $ExporterSid' in (root/'Start-Exporter.ps1').read_text()


def test_packaged_source_schema_matches_runtime():
    published=json.loads((Path(__file__).parents[1]/'docs'/'CC03_READONLY_EXPORT_SCHEMA.json').read_text())
    published.pop('$schema'); published.pop('title')
    assert published==SCHEMA
