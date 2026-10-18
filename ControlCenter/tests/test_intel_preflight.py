"""Permission-A boundaries; injected facts only, no production probes."""
from copy import deepcopy
import json
from pathlib import Path
import socket
import sqlite3
import subprocess
import pytest
from observer import intel_preflight as preflight
from observer.windows_os import row


@pytest.fixture
def preflight_policy():
    # Synthetic test references only.
    return dict(schema_id='cc03.intel-preflight-policy.v2', readonly_preflight_approved=True,
        observer_sid='S-1-5-21-1-2-3-1001', task_name=preflight.TASK, task_xml_sha256='a'*64,
        task_principal_sid='S-1-5-21-1-2-3-1002', process_binding=dict(process_pid=12345,
        process_creation_sha256='b'*64, process_image_sha256='c'*64, process_command_sha256='d'*64,
        process_principal_sid='S-1-5-21-1-2-3-1002'), cc_panel_sid=None)


def ready(_):
    return dict(observer_standard=True, identities='CCPANEL_NOT_PROVISIONED', directories='NOT_PROVISIONED')


def facts(p):
    return dict(task=row('WINDOWS_TASK_READONLY', 'TASK_RUNNING', 'OK', p['task_xml_sha256']),
                process=row('WINDOWS_PROCESS_READONLY', 'PROCESS_OBSERVED', 'OK', 'd'*64))


def run(p, **kwargs):
    return preflight.execute(p, identity=lambda:(p['observer_sid'],False), facts=kwargs.pop('facts',facts),
                             cc_readiness=kwargs.pop('cc_readiness',ready), **kwargs)


def test_preview_never_accesses_physical_sources(monkeypatch,capsys):
    def forbidden(*a,**kw): pytest.fail('PREVIEW attempted physical I/O')
    for name in ('current_identity','os_facts','readiness','read_windows'):
        monkeypatch.setattr(preflight,name,forbidden)
    for module,name in ((subprocess,'run'),(socket,'create_connection'),(sqlite3,'connect')):
        monkeypatch.setattr(module,name,forbidden)
    assert preflight.main([])==0
    result=json.loads(capsys.readouterr().out)
    assert result['mode']=='PREVIEW' and result['outcome']=='NOT_VERIFIED'
    assert all(v=='UNKNOWN' for v in result['trading'].values())


@pytest.mark.parametrize('key,value',[('task_name','WrongTask'),('task_xml_sha256',None),
    ('readonly_preflight_approved',False),('observer_sid','S-1-5-18'),
    ('cc_panel_sid','S-1-5-21-1-2-3-1002')])
def test_invalid_approval_refused_before_io(preflight_policy,key,value):
    preflight_policy[key]=value
    def forbidden(*a): pytest.fail('invalid policy reached physical source')
    with pytest.raises(ValueError):
        preflight.execute(preflight_policy,identity=forbidden,facts=forbidden,cc_readiness=forbidden)


def test_running_allowed_and_provisioning_independent(preflight_policy):
    r=run(preflight_policy)
    assert r['outcome']=='PASS' and r['task_state']=='TASK_RUNNING_OBSERVED'
    assert r['task_identity']=='TASK_IDENTITY_MATCHED' and r['process']=='PROCESS_IDENTITY_MATCHED'
    assert r['cc_identities']=='CCPANEL_NOT_PROVISIONED' and r['cc_directories']=='NOT_PROVISIONED'
    assert r['cc_acl']=='NOT_VERIFIED' and r['os_source']=='OS_SOURCE_APPROVAL_REQUIRED'
    assert all(v=='UNKNOWN' for v in r['trading'].values())


@pytest.mark.parametrize('state,reason',[('UNKNOWN','IDENTITY_MISMATCH'),('UNKNOWN','ACCESS_DENIED'),
    ('PROCESS_ABSENT','NOT_FOUND'),('UNKNOWN','TIMEOUT')])
def test_wrong_pid_epoch_missing_or_denied_remain_unknown(preflight_policy,state,reason):
    def unavailable(p):
        r=facts(p);r['process']=row('WINDOWS_PROCESS_READONLY',state,reason);return r
    r=run(preflight_policy,facts=unavailable)
    assert r['process']=='PROCESS_UNKNOWN'
    assert r['process_access']==('ACCESS_DENIED' if reason=='ACCESS_DENIED' else 'UNKNOWN')


@pytest.mark.parametrize('reason',['IDENTITY_MISMATCH','ACCESS_DENIED','TIMEOUT'])
def test_task_failure_blocks_process_query(preflight_policy,reason):
    calls=[]
    def unavailable(p):
        calls.append(p.copy());return dict(task=row('WINDOWS_TASK_READONLY',reason=reason))
    r=run(preflight_policy,facts=unavailable)
    assert r['outcome']=='BLOCKED' and len(calls)==1 and not calls[0]['process_enabled']
    assert r['task_identity']=='UNKNOWN' and r['task_state']=='UNKNOWN'
    if reason=='ACCESS_DENIED':assert r['task_access']=='ACCESS_DENIED'


@pytest.mark.parametrize('drift',['state','identity','denied'])
def test_before_after_drift_blocks(preflight_policy,drift):
    calls=[]
    def changing(p):
        calls.append(deepcopy(p));r=facts(p)
        if len(calls)==3:
            r['task']=row('WINDOWS_TASK_READONLY','TASK_READY' if drift=='state' else 'UNKNOWN',
                'OK' if drift=='state' else ('ACCESS_DENIED' if drift=='denied' else 'IDENTITY_MISMATCH'),
                p['task_xml_sha256'] if drift=='state' else None)
        return r
    r=run(preflight_policy,facts=changing)
    assert r['outcome']=='BLOCKED' and r['task_before_after']=='UNKNOWN'
    assert [p['process_enabled'] for p in calls]==[False,True,False]
    assert {p['task_name'] for p in calls}=={preflight.TASK}


def test_unbound_process_is_never_discovered(preflight_policy):
    preflight_policy['process_binding']=None
    calls=[]
    def observed(p):calls.append(p.copy());return facts(p)
    r=run(preflight_policy,facts=observed)
    assert r['outcome']=='PASS' and r['process']=='PROCESS_UNKNOWN'
    assert len(calls)==2 and all(not p['process_enabled'] for p in calls)


def test_filtered_admin_or_wrong_identity_blocks(preflight_policy):
    r=run(preflight_policy,cc_readiness=lambda _:dict(ready(None),observer_standard=False))
    assert r['outcome']=='BLOCKED' and r['own_identity']=='UNKNOWN'
    r=preflight.execute(preflight_policy,identity=lambda:('S-1-5-18',False),
                       facts=lambda _:pytest.fail('wrong identity probed'))
    assert r['outcome']=='BLOCKED'


def test_sanitized_report_does_not_echo_policy_facts_or_exception(preflight_policy,capsys,monkeypatch):
    def contaminated(p):
        r=facts(p);r['process']=row('WINDOWS_PROCESS_READONLY',reason='SECRET_TOKEN_PRIVATE_PATH')
        r['task']['private']='SECRET_TOKEN_PRIVATE_PATH';return r
    encoded=json.dumps(run(preflight_policy,facts=contaminated))
    assert 'SECRET' not in encoded and preflight_policy['observer_sid'] not in encoded
    assert preflight_policy['task_xml_sha256'] not in encoded and '12345' not in encoded
    # On POSIX the platform gate itself must sanitize the report.
    monkeypatch.setattr(preflight,'read_windows',lambda *a,**k:(_ for _ in ()).throw(ValueError('SECRET')))
    assert preflight.main(['--execute'])==1
    assert 'SECRET' not in capsys.readouterr().out


def test_no_mutation_export_or_robot_file_interface():
    root=Path(preflight.__file__).parent
    source=Path(preflight.__file__).read_text()
    for text in (source,(root/'Read-PreflightReadiness.ps1').read_text(),(root/'Read-OsFacts.ps1').read_text()):
        for forbidden in ('Start-ScheduledTask','Stop-ScheduledTask','RegisterTask','DeleteTask',
            'SetSecurityDescriptor','Set-Acl','Get-Content','sqlite3','finam','Get-Process',
            'Start-Process','Invoke-WebRequest','write_text','write_bytes'):
            assert forbidden not in text
    assert 'publish(' not in source and 'metadata_native' not in source
    template=json.loads((root.parent/'deployment/preflight-policy.example.json').read_text())
    assert template['readonly_preflight_approved'] is False and template['process_binding'] is None
    with pytest.raises(ValueError):preflight.policy_check(template)


def test_execute_has_no_robot_file_network_sqlite_or_export_side_effect(preflight_policy,monkeypatch):
    import builtins
    import os
    def forbidden(*a,**kw):pytest.fail('unauthorized external capability')
    for module,name in ((builtins,'open'),(os,'open'),(socket,'create_connection'),
                         (sqlite3,'connect'),(subprocess,'run')):
        monkeypatch.setattr(module,name,forbidden)
    assert run(preflight_policy)['outcome']=='PASS'


def test_v1_null_exporter_migrates_without_mutation(preflight_policy):
    legacy = dict(preflight_policy, schema_id='cc03.intel-preflight-policy.v1', cc_exporter_sid=None)
    before = deepcopy(legacy)
    assert preflight.policy_check(legacy) == preflight_policy
    assert legacy == before
    assert run(legacy)['outcome'] == 'PASS'


@pytest.mark.parametrize('change', ['exporter', 'extra', 'missing_observer', 'v2_exporter'])
def test_ambiguous_or_privileged_migration_refused(preflight_policy, change):
    p = dict(preflight_policy, schema_id='cc03.intel-preflight-policy.v1', cc_exporter_sid=None)
    if change == 'exporter': p['cc_exporter_sid'] = 'S-1-5-21-1-2-3-2000'
    if change == 'extra': p['allow_admin'] = True
    if change == 'missing_observer': del p['observer_sid']
    if change == 'v2_exporter': p['schema_id'] = preflight_policy['schema_id']
    with pytest.raises(ValueError): preflight.policy_check(p)


@pytest.mark.parametrize('state,installation', [('CCPANEL_ENABLED','NOT_VERIFIED'),
    ('CCPANEL_NOT_PROVISIONED','NOT_PROVISIONED'), ('CCPANEL_DISABLED','BLOCKED'),
    ('CCPANEL_SID_MISMATCH','BLOCKED'), ('CCPANEL_PRIVILEGED','BLOCKED'), ('UNKNOWN','NOT_VERIFIED')])
def test_panel_readiness_never_approves_b_or_blocks_independent_a(preflight_policy,state,installation):
    r=run(preflight_policy,cc_readiness=lambda _:dict(ready(None), identities=state,
                                                   directories='EXISTING_ROOTS_OBSERVED'))
    assert r['outcome']=='PASS' and r['cc_installation']==installation
    assert r['cc_acl']=='NOT_VERIFIED' and r['os_source']=='OS_SOURCE_APPROVAL_REQUIRED'
    assert all(v=='UNKNOWN' for v in r['trading'].values())


def test_readiness_pins_process_scoped_policy_and_cc_only_payload(monkeypatch, preflight_policy):
    calls=[]
    def child(argv, **kwargs):
        calls.append((argv,kwargs))
        return subprocess.CompletedProcess(argv,0,json.dumps(ready(None)),'')
    monkeypatch.setattr(subprocess,'run',child)
    monkeypatch.setattr(subprocess,'CREATE_NO_WINDOW',0,raising=False)
    assert preflight.readiness(preflight_policy)==ready(None)
    assert len(calls)==1
    argv,kwargs=calls[0]
    assert argv[1:]==['-NoLogo','-NoProfile','-NonInteractive','-ExecutionPolicy','Bypass',
                      '-File',str(preflight.READINESS_SCRIPT)]
    assert argv[0].lower().endswith('powershell.exe')
    assert kwargs['timeout']==6 and kwargs['creationflags']==0
    payload=json.loads(kwargs['input'])
    assert set(payload)=={'cc_panel_sid','roots'} and len(payload['roots'])==6
    assert not any('TradingSystemLab' in root or 'IntradayLab' in root for root in payload['roots'])
    assert 'PSExecutionPolicyPreference' not in kwargs['env']


def test_readiness_denial_fails_closed(monkeypatch,preflight_policy):
    monkeypatch.setattr(subprocess,'run',lambda *a,**k:subprocess.CompletedProcess(a,1,'{}','PSSecurityException'))
    monkeypatch.setattr(subprocess,'CREATE_NO_WINDOW',0,raising=False)
    assert preflight.readiness(preflight_policy)==dict(observer_standard=False, identities='UNKNOWN', directories='UNKNOWN')
