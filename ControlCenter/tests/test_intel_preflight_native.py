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
        assert result['identities']=='CC_IDENTITIES_NOT_PROVISIONED', captured
        assert result['directories']=='NOT_PROVISIONED', captured
        assert result['observer_standard'] is False # elevated pytest token
    finally:
        os.environ['CC03_CI_DISPOSABLE_ROOT']=previous
