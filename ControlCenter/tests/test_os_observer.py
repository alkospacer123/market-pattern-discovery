"""OS envelope/receiver isolation. No live source is ever used by these tests."""
import ast
from copy import deepcopy
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import subprocess
import pytest
from cc.models import RobotId, State
from cc.providers import h1_export as receiver
from cc.providers.h1_readonly import canonical_digest
from cc.providers.os_contract import SCHEMA, check_semantics
from cc.providers.h1_contract import validate, timestamp
from observer import windows_os as observer


@pytest.fixture
def os_policy():
    return dict(schema_id='cc03.os-policy.v1', os_policy_approved=True,
        source_id='CC03-H1-OSCIDISPOSABLE', account_alias='H1-OSCIDISPOSABLE', binding_id='a'*64,
        observer_sid='S-1-5-21-1-2-3-1001', task_name=observer.TASK, task_xml_sha256='b'*64,
        task_principal_sid='S-1-5-21-1-2-3-1002', process_enabled=True, process_pid=12345,
        process_creation_sha256='e'*64, process_image_sha256='c'*64, process_command_sha256='d'*64,
        process_principal_sid='S-1-5-21-1-2-3-1002', metadata_enabled=False, export_root_id=[1,2,5])


def envelope(policy):
    return observer.collect(policy,
        facts=lambda p: dict(task=observer.row('WINDOWS_TASK_READONLY', 'TASK_RUNNING', 'OK', 'b'*64),
                            process=observer.row('WINDOWS_PROCESS_READONLY', 'PROCESS_OBSERVED', 'OK', 'd'*64)))


def received(value, policy, now, monkeypatch):
    value['payload_sha256'] = canonical_digest(value)
    monkeypatch.setattr(receiver, 'read_latest_windows', lambda *args: json.dumps(value).encode())
    return receiver.H1ExportProvider(policy).snapshot(RobotId.H1, '', now)


def approved(p, **kwargs):
    return receiver.ReceiverPolicy(source_id=p['source_id'], account_alias=p['account_alias'],
        binding_id=p['binding_id'], snapshot=30, os_observations=15, **kwargs)


def test_os_observations_never_grant_robot_or_account_authority(os_policy, monkeypatch):
    value = envelope(os_policy)
    now = datetime.now(timezone.utc)
    validate(value, SCHEMA); check_semantics(value, timestamp)
    s = received(value, approved(os_policy), now, monkeypatch)
    assert s.status.state == State.UNKNOWN and s.status.heartbeat_at is None
    assert s.status.task_state == 'TASK_RUNNING' and s.status.trading_allowed is None
    assert s.positions is None and s.trades is None and s.portfolio.equity is None
    assert not s.signals and not s.orders and not s.candles
    assert s.windows_observations[1].state == 'PROCESS_OBSERVED'
    assert all(r.authority == 'WINDOWS_OS_ONLY' for r in s.windows_observations[:2])
    assert all(r.state == 'UNKNOWN' and r.reason == 'DISABLED' for r in s.windows_observations[2:])
    assert 'VERIFIED_LIVE' not in repr(s) and 'account UNVERIFIED' in s.readonly_identity


@pytest.mark.parametrize('field', ['source_id','account_alias','binding_id'])
def test_wrong_source_or_account_cannot_publish_verified_os(os_policy, monkeypatch, field):
    value = envelope(os_policy)
    value['identity'][field] = {'source_id':'CC03-H1-WRONGSOURCE','account_alias':'H1-WRONG','binding_id':'f'*64}[field]
    s = received(value, approved(os_policy), datetime.now(timezone.utc), monkeypatch)
    assert not s.windows_observations and s.status.state == State.UNKNOWN


def test_stale_or_unknown_ttl_hides_positive_os_facts(os_policy, monkeypatch):
    value = envelope(os_policy)
    for policy, offset in [(approved(os_policy), 16), (approved(os_policy), 31),
        (receiver.ReceiverPolicy(source_id=os_policy['source_id'], account_alias=os_policy['account_alias'], binding_id='a'*64), 0)]:
        s = received(value, policy, datetime.now(timezone.utc)+timedelta(seconds=offset), monkeypatch)
        assert s.status.task_state is None
        assert all(r.state == 'UNKNOWN' and r.value is None and r.authority == 'UNKNOWN' for r in s.windows_observations)


@pytest.mark.parametrize('change', ['future','confidence','unknown_value','extra','broker_authority','metadata_fact'])
def test_forged_or_incoherent_os_facts_rejected(os_policy, monkeypatch, change):
    value = envelope(os_policy)
    if change == 'future': value['task']['observed_at'] = (datetime.now(timezone.utc)+timedelta(days=1)).isoformat()
    elif change == 'confidence': value['task']['confidence'] = 'UNKNOWN'
    elif change == 'unknown_value': value['task']['state'] = 'UNKNOWN'
    elif change == 'extra': value['task']['broker_connected'] = True
    elif change=='broker_authority': value['identity']['authority'] = 'BROKER_CONNECTED'
    else: value['heartbeat_metadata'].update(state='FILE_ABSENT',reason='NOT_FOUND',confidence='OS_OBSERVED')
    assert not received(value, approved(os_policy), datetime.now(timezone.utc), monkeypatch).windows_observations


@pytest.mark.parametrize('key,bad', [('os_policy_approved',False),('task_name','python.exe'),
    ('observer_sid','S-1-5-18'),('task_principal_sid','S-1-5-21-1-2-3-1001'),
    ('process_pid',True),('process_pid',0),('export_root_id',[]),('process_enabled','true'),('metadata_enabled',True)])
def test_policy_fail_closed_before_native_calls(os_policy,key,bad):
    os_policy[key]=bad
    with pytest.raises(ValueError): observer.policy_check(os_policy)


def test_probe_timeout_not_absence_and_no_error_path_leak(os_policy,monkeypatch):
    def timeout(*args,**kwargs): raise subprocess.TimeoutExpired('PRIVATE_PATH_TOKEN',.01)
    monkeypatch.setattr(subprocess,'CREATE_NO_WINDOW',0,raising=False)
    monkeypatch.setattr(subprocess,'run',timeout)
    facts=observer.os_facts(os_policy)
    assert all(v['state']=='UNKNOWN' and v['reason']=='TIMEOUT' for v in facts.values())
    assert 'PRIVATE_PATH_TOKEN' not in repr(facts)


def test_missing_h1_and_panel_rerun_leave_m15_and_controls_independent(monkeypatch,tmp_path):
    from streamlit.testing.v1 import AppTest
    monkeypatch.setattr(receiver,'read_latest_windows',lambda *a: (_ for _ in ()).throw(ValueError('PRIVATE')))
    app=AppTest.from_file(str(Path(__file__).parents[1]/'app.py'),default_timeout=15).run()
    app.selectbox(key='h1-source').select('READONLY_EXPORT').run()
    for _ in range(2): app.run()
    app.radio[0].set_value('Монитор M15').run()
    assert not app.exception
    assert any('NOT_DEPLOYED' in str(x.value) for x in app.info)
    app.radio[0].set_value('Управление').run()
    controls = [b for b in app.button if b.key != 'cc03-manual-refresh']
    assert len(controls) == 10 and all(b.disabled for b in controls)


def test_observer_is_outside_ui_dependency_graph_and_has_no_trading_capabilities():
    root=Path(__file__).parents[1]
    for path in (root/'observer').glob('*.py'):
        tree=ast.parse(path.read_text(encoding='utf-8'))
        imports=[n.module or '' for n in ast.walk(tree) if isinstance(n,ast.ImportFrom)]
        imports += [a.name for n in ast.walk(tree) if isinstance(n,ast.Import) for a in n.names]
        assert not any(i.startswith(('TradingSystemLab','IntradayLab','finam','sqlite3','socket','urllib')) for i in imports)
    for path in [root/'app.py',*(root/'cc').rglob('*.py')]:
        source=path.read_text(encoding='utf-8')
        if path.name != 'h1_windows_os.py':
            assert 'import observer' not in source and 'from observer' not in source
        else:
            imports={n.module for n in ast.walk(ast.parse(source)) if isinstance(n,ast.ImportFrom)
                     and n.module and n.module.startswith('observer')}
            assert imports == {'observer.identity', 'observer.windows_os'}
    script=(root/'observer/Read-OsFacts.ps1').read_text(encoding='utf-8')
    for verb in ('Start-ScheduledTask','Stop-ScheduledTask','RegisterTask','DeleteTask','SetSecurityDescriptor',
                 'Get-Content','Start-Process','Invoke-Expression'):
        assert verb not in script


def test_metadata_blocked_before_any_source_path_or_handle(os_policy,monkeypatch):
    import os
    monkeypatch.setattr(os,'open',lambda *a,**k:pytest.fail('production file open'))
    os_policy['metadata_enabled']=True
    with pytest.raises(ValueError,match='CC03_METADATA_COMPATIBILITY_BLOCKED'):
        observer.collect(os_policy,facts=lambda p:pytest.fail('must fail before probing'))
    source=Path(observer.__file__).read_text(encoding='utf-8')
    assert 'from .metadata' not in source and 'metadata_native' not in source


def test_os_schema_matches_packaged_document():
    schema=json.loads((Path(__file__).parents[1]/'docs/CC03_WINDOWS_OS_SCHEMA.json').read_text())
    schema.pop('$schema');schema.pop('title')
    assert schema==SCHEMA


def test_fixed_os_helper_uses_process_scoped_execution_policy(os_policy, monkeypatch):
    calls=[]
    def child(argv, **kwargs):
        calls.append((argv,kwargs))
        return subprocess.CompletedProcess(argv,1,'{}','denied')
    monkeypatch.setattr(subprocess,'run',child)
    monkeypatch.setattr(subprocess,'CREATE_NO_WINDOW',0,raising=False)
    assert all(r['state']=='UNKNOWN' for r in observer.os_facts(os_policy).values())
    argv,kwargs=calls[0]
    assert len(calls)==1 and argv[1:]==['-NoLogo','-NoProfile','-NonInteractive',
        '-ExecutionPolicy','Bypass','-File',str(observer.SCRIPT)]
    assert kwargs['timeout']==6 and 'PSExecutionPolicyPreference' not in kwargs['env']


def test_cached_os_facts_expire_without_reread_or_timestamp_rewrite(os_policy, monkeypatch):
    value=envelope(os_policy)
    now=datetime.now(timezone.utc)
    snapshot=received(value, approved(os_policy), now, monkeypatch)
    assert snapshot.windows_observations[0].freshness=='CURRENT'
    def forbidden(*a,**k):pytest.fail('cache aging performed source I/O')
    monkeypatch.setattr(receiver,'installed_policy',forbidden)
    monkeypatch.setattr(receiver,'read_latest_windows',forbidden)
    aged=receiver.age_export_snapshot(snapshot,now+timedelta(seconds=16))
    assert aged.status.provenance==snapshot.status.provenance
    assert aged.status.task_state is None and aged.status.state==State.STALE
    assert all(r.state=='UNKNOWN' and r.freshness=='STALE' and r.authority=='UNKNOWN' and r.value is None
               for r in aged.windows_observations)
    assert snapshot.windows_observations[0].freshness=='CURRENT' # immutable original
