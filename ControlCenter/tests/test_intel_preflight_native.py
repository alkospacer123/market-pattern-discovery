"""New physical prerequisites on disposable hosted Tasks/processes only."""
import os
import subprocess
import sys
import pytest
from observer import intel_preflight as preflight
from observer import windows_os as observer
from test_intel_preflight import preflight_policy, ready
from test_os_windows_native import tasks, fixture_operation

pytestmark=pytest.mark.skipif(os.name!='nt',reason='NOT_VERIFIED: disposable hosted Windows required')


def native_run(p,fixture):
    # Real standard-token checks live in ci.identity_probe under both SIDs.
    return preflight.execute(p,identity=lambda:(p['observer_sid'],False),cc_readiness=ready,
        facts=lambda q:observer.os_facts(dict(q,task_name=fixture['task_name'])))


def test_native_preflight_running_exact_binding_before_after(preflight_policy,tasks):
    fixtures,folder=tasks
    p=dict(preflight_policy,**{k:v for k,v in fixtures['Running'].items() if k not in {'state','task_name'}},process_binding=None)
    r=native_run(p,fixtures['Running'])
    assert r['outcome']=='PASS' and r['task_state']=='TASK_RUNNING_OBSERVED',r
    assert r['task_identity']=='TASK_IDENTITY_MATCHED' and r['task_before_after']=='UNCHANGED_OBSERVED'
    assert fixture_operation('Inspect',folder)==fixtures
    p['task_xml_sha256']='0'*64
    assert native_run(p,fixtures['Running'])['outcome']=='BLOCKED'


def test_native_preflight_epoch_and_pid_disappearance(preflight_policy,tasks):
    child=subprocess.Popen([sys.executable,'-c','import time; time.sleep(60)'])
    try:
        p=dict(preflight_policy,**{k:v for k,v in tasks[0]['Ready'].items() if k not in {'state','task_name'}},
               process_binding=fixture_operation('Process',pid=child.pid))
        assert native_run(p,tasks[0]['Ready'])['process']=='PROCESS_IDENTITY_MATCHED'
        original=p['process_binding']['process_creation_sha256']
        p['process_binding']['process_creation_sha256']='0'*64
        assert native_run(p,tasks[0]['Ready'])['process']=='PROCESS_UNKNOWN'
        p['process_binding']['process_creation_sha256']=original
        child.terminate();child.wait(5)
        assert native_run(p,tasks[0]['Ready'])['process']=='PROCESS_UNKNOWN'
    finally:
        if child.poll() is None:child.terminate();child.wait(5)


def test_native_readiness_script_on_missing_disposable_roots(preflight_policy,monkeypatch):
    # Capture only this disposable helper's diagnostics, never a production source.
    original=subprocess.run
    captured=[]
    def capture(*args,**kwargs):
        result=original(*args,**kwargs)
        captured.append((result.returncode,result.stdout,result.stderr))
        return result
    monkeypatch.setattr(subprocess,'run',capture)
    previous=os.environ['CC03_CI_DISPOSABLE_ROOT']
    import uuid
    from pathlib import Path
    try:
        os.environ['CC03_CI_DISPOSABLE_ROOT']=str(Path(previous).parent / ('CC03-'+uuid.uuid4().hex))
        result=preflight.readiness(preflight_policy)
        assert result['identities']=='CCPANEL_NOT_PROVISIONED', captured
        assert result['directories']=='NOT_PROVISIONED', captured
        assert result['observer_standard'] is False # elevated pytest token
    finally:
        os.environ['CC03_CI_DISPOSABLE_ROOT']=previous


def test_native_actual_local_ccpanel_enabled_absent_disabled_wrong_sid_and_admin():
    import json
    from pathlib import Path
    assert os.environ.get('GITHUB_ACTIONS')=='true' and os.environ.get('RUNNER_ENVIRONMENT')=='github-hosted'
    script=Path(__file__).parents[1]/'ci/Test-PanelIdentity.ps1'
    environment=os.environ.copy()
    environment['PSMODULEPATH']=os.pathsep.join([str(Path(os.environ['SYSTEMROOT'])/'System32/WindowsPowerShell/v1.0/Modules'),
        str(Path(os.environ['PROGRAMFILES'])/'WindowsPowerShell/Modules')])
    result=subprocess.run(['powershell.exe','-NoProfile','-NonInteractive','-File',str(script)],
                          capture_output=True,text=True,timeout=45,env=environment)
    assert result.returncode==0, result.stderr
    assert json.loads(result.stdout)==['CCPANEL_NOT_PROVISIONED','CCPANEL_ENABLED','CCPANEL_SID_MISMATCH',
                                      'CCPANEL_DISABLED','CCPANEL_PRIVILEGED','CCPANEL_ENABLED','FILTERED_ADMIN_REJECTED']


def test_native_restricted_execution_policy_is_child_only(preflight_policy):
    import json
    payload=json.dumps(dict(cc_panel_sid=None, roots=[]))
    base=['powershell.exe','-NoLogo','-NoProfile','-NonInteractive']
    def policies():
        result=subprocess.run(base+['-Command','Get-ExecutionPolicy -List | ConvertTo-Json -Compress'],
                              capture_output=True,text=True,timeout=10)
        assert result.returncode==0, result.stderr
        return json.loads(result.stdout)
    before=policies()
    denied=subprocess.run(base+['-ExecutionPolicy','Restricted','-File',str(preflight.READINESS_SCRIPT)],
                          input=payload,capture_output=True,text=True,timeout=10)
    assert denied.returncode!=0 and 'PSSecurityException' in denied.stderr
    observed=preflight.readiness(preflight_policy)
    assert observed['observer_standard'] is False # elevated runner, never standard
    assert observed['identities']=='CCPANEL_NOT_PROVISIONED'
    assert policies()==before # no machine/user policy mutation


def test_native_elevated_runner_token_rejected_before_task(preflight_policy):
    from observer.identity import current_identity
    sid,unsafe=current_identity()
    assert unsafe is True
    p=dict(preflight_policy,observer_sid=sid)
    r=preflight.execute(p,facts=lambda _:pytest.fail('privileged observer queried Task'))
    assert r['outcome']=='BLOCKED' and r['reason']=='OBSERVER_IDENTITY_INVALID'
