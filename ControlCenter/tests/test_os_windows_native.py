"""Real Windows API tests. All mutators are confined to UUID-named CI fixtures."""
from datetime import datetime, timezone
import json
import ctypes
import os
from pathlib import Path
import subprocess
import sys
import threading
import time
import uuid
import pytest
from observer import windows_os as observer
from ci.metadata_experiment import MetadataAPI, metadata_native, probe
from cc.providers import windows_file as win
from cc.providers.h1_export import H1ExportProvider
from cc.models import RobotId, State
from test_os_observer import os_policy, envelope, approved

pytestmark=pytest.mark.skipif(os.name!='nt',reason='NOT_VERIFIED: Windows OS APIs and disposable hosted VM required')
HARNESS=Path(__file__).parents[1]/'ci/Os-Fixtures.ps1'


def fixture_operation(operation,folder=None,pid=None):
    assert os.environ.get('GITHUB_ACTIONS')=='true' and os.environ.get('RUNNER_ENVIRONMENT')=='github-hosted'
    args=['powershell.exe','-NoProfile','-NonInteractive','-File',str(HARNESS),'-Operation',operation]
    if folder: args+=['-Folder',folder]
    if pid: args+=['-ProcessId',str(pid)]
    result=subprocess.run(args,capture_output=True,text=True,timeout=20)
    assert result.returncode==0, result.stderr
    return json.loads(result.stdout) if result.stdout.strip() else None


@pytest.fixture(scope='module')
def tasks():
    folder='CC03-CI-'+uuid.uuid4().hex
    try:
        yield fixture_operation('Create',folder),folder
    finally:
        fixture_operation('Remove',folder)


def task_policy(p,fixture):
    return dict(p,**{k:v for k,v in fixture.items() if k!='state'},process_enabled=False)


@pytest.mark.parametrize('name,state',[('Disabled','TASK_DISABLED'),('Ready','TASK_READY'),('Running','TASK_RUNNING')])
def test_native_exact_task_states_are_readonly(os_policy,tasks,name,state):
    fixtures,folder=tasks
    p=task_policy(os_policy,fixtures[name])
    result=observer.os_facts(p)['task']
    assert result['state']==state and result['confidence']=='OS_OBSERVED', result
    after=fixture_operation('Inspect',folder)
    assert after[name]==fixtures[name]


def test_native_missing_and_wrong_task_identity(os_policy,tasks):
    fixtures,folder=tasks
    p=task_policy(os_policy,fixtures['Ready'])
    p['task_xml_sha256']='0'*64
    assert observer.os_facts(p)['task']['reason']=='IDENTITY_MISMATCH'
    p=task_policy(os_policy,fixtures['Ready']);p['task_principal_sid']='S-1-5-18'
    assert observer.os_facts(p)['task']['reason']=='IDENTITY_MISMATCH'
    p['task_name']='\\'+folder+'\\Missing'
    row=observer.os_facts(p)['task']
    assert row['state']=='UNKNOWN' and row['reason']=='NOT_FOUND',row


def test_native_process_exists_disappeared_wrong_identity(os_policy,tasks):
    # Only this test's own Python child is launched/terminated. Never H1.
    child=subprocess.Popen([sys.executable,'-c','import time; time.sleep(60)'])
    try:
        p=dict(os_policy,**fixture_operation('Process',pid=child.pid))
        p.update({k:v for k,v in tasks[0]['Ready'].items() if k!='state'})
        row=observer.os_facts(p)['process']
        assert row['state']=='PROCESS_OBSERVED',row
        for key in ('process_image_sha256','process_command_sha256','process_creation_sha256','process_principal_sid'):
            wrong=dict(p,**{key:('S-1-5-18' if key.endswith('_sid') else '0'*64)})
            assert observer.os_facts(wrong)['process']['state']=='UNKNOWN'
        child.terminate();child.wait(5)
        row=observer.os_facts(p)['process']
        assert row['state']=='PROCESS_ABSENT' and row['reason']=='NOT_FOUND',row
    finally:
        if child.poll() is None:child.terminate();child.wait(5)


def pin(path):
    api=MetadataAPI();handle=api.open(str(path),True)
    try:return api.info(handle,str(path),True)[:3]
    finally:api.close(handle)


def test_native_metadata_experiment_fields_identity_absence_and_wrong_root(tmp_path):
    path=tmp_path/'stage8-12-4-production-heartbeat.json'
    path.write_bytes(b'DO NOT READ CONTENT')
    expected=pin(tmp_path)
    state,value=metadata_native(str(tmp_path),path.name,expected)
    assert state=='FILE_PRESENT' and value['size']==19
    assert value['modified_at'] and len(value['identity'])==64
    nextfile=tmp_path/'next.tmp';nextfile.write_bytes(b'changed');os.replace(nextfile,path)
    assert metadata_native(str(tmp_path),path.name,expected)[1]['identity']!=value['identity']
    assert probe(str(tmp_path),path.name,[0,0,0])[1]=='IDENTITY_MISMATCH'
    path.unlink()
    assert probe(str(tmp_path),path.name,expected)[:2]==('FILE_ABSENT','NOT_FOUND')


def test_native_metadata_experiment_conflict_requires_runtime_block(tmp_path):
    path=tmp_path/'stage8-12-4-production-heartbeat.json';path.write_bytes(b'initial')
    api=MetadataAPI();held=api.open(str(path),False)
    expected=pin(tmp_path)
    errors=[];done=[];start=threading.Event()
    def producer():
        start.wait()
        try:
            for i in range(500):
                temporary=tmp_path/'next.tmp';temporary.write_bytes(str(i).encode());os.replace(temporary,path)
                done.append(i)
        except BaseException as exc:errors.append(exc)
    thread=threading.Thread(target=producer);thread.start();start.set()
    observations=0;changed=0
    try:
        for _ in range(150):
            try:
                state,value=metadata_native(str(tmp_path),path.name,expected)
                assert state=='FILE_PRESENT';observations+=1
            except ValueError as exc:
                # Replacement during an observation must produce UNKNOWN, never old truth.
                assert str(exc) in ('CHANGED','FILE_TYPE_OR_PATH_INVALID');changed+=1
        thread.join(15)
        assert not thread.is_alive() and errors and isinstance(errors[0], PermissionError)
        assert len(done)<500 and observations>0
        # This is a regression of NOT_PASSED metadata noninterference. It is not
        # acceptance of metadata as a source, and is never used in the runtime.
        # The original zero-access handle remains OPEN across every replace.
        original=win.FileInfo()
        assert api.k.GetFileInformationByHandle(held,ctypes.byref(original)) and original.size_low==7
    finally:
        thread.join(15);api.close(held)
    # After all experimental handles close, the same producer operation succeeds.
    for i in range(500):
        temporary=tmp_path/'next.tmp';temporary.write_bytes(str(i).encode());os.replace(temporary,path)
    assert path.read_bytes()==b'499'
    print('METADATA_NONINTERFERENCE=NOT_PASSED / BLOCKED: zero-access handle reproduced producer conflict; after close 500/500 replacements recovered; runtime source disabled')


def test_native_probe_timeout_is_bounded(os_policy,tasks):
    p=task_policy(os_policy,tasks[0]['Ready'])
    started=time.monotonic();facts=observer.os_facts(p,timeout=.001)
    assert time.monotonic()-started<3
    assert all(r['reason']=='TIMEOUT' and r['state']=='UNKNOWN' for r in facts.values())


def test_native_runtime_task_process_observer_does_not_interfere_with_producer(os_policy,tasks,tmp_path):
    child=subprocess.Popen([sys.executable,'-c','import time; time.sleep(60)'])
    errors=[];done=[]
    path=tmp_path/'stage8-12-4-production-heartbeat.json';path.write_bytes(b'initial')
    def producer():
        try:
            for i in range(500):
                temporary=tmp_path/'next.tmp';temporary.write_bytes(str(i).encode());os.replace(temporary,path)
                done.append(i);time.sleep(.003)
        except BaseException as exc:errors.append(exc)
    thread=None
    try:
        p=dict(os_policy,**fixture_operation('Process',pid=child.pid))
        p.update({k:v for k,v in tasks[0]['Ready'].items() if k!='state'})
        thread=threading.Thread(target=producer);thread.start()
        value=observer.collect(os_policy,facts=lambda _:observer.os_facts(p))
        assert len(done)>0 # producer and actual OS API collection overlapped
        assert value['task']['state']=='TASK_READY' and value['process']['state']=='PROCESS_OBSERVED'
        for name in ('heartbeat_metadata','kill_switch_metadata'):
            assert value[name]['state']=='UNKNOWN' and value[name]['reason']=='DISABLED'
        thread.join(15)
        assert not thread.is_alive() and not errors and len(done)==500
        assert path.read_bytes()==b'499'
        print('ACTIVE_OS_OBSERVER_NONINTERFERENCE=PASS: Task/process probes, metadata disabled, 500/500 unchanged os.replace operations')
    finally:
        if thread is not None:thread.join(15)
        child.terminate();child.wait(5)


def test_native_os_snapshot_transport_and_no_root_substitution(os_policy,tmp_path,monkeypatch):
    from exporter import snapshot as writer
    monkeypatch.setattr(writer,'EXPORT_ROOT',tmp_path)
    expected=pin(tmp_path);value=envelope(os_policy)
    leaf=writer.publish(value,expected_root=expected)
    assert json.loads(win.read_latest_windows(tmp_path,131072,expected))==value
    handle=win.WinAPI().open(str(leaf),False)
    try:
        writer.publish(value,expected_root=expected)
    finally:win.WinAPI().close(handle)
    with pytest.raises(ValueError,match='EXPORT_ROOT_IDENTITY_MISMATCH'):
        writer.publish(value,expected_root=[0,0,0])


def test_native_bounded_stop_preserves_open_sole_snapshot_and_outside_data(os_policy,tmp_path,monkeypatch):
    from exporter import snapshot as writer
    root=tmp_path/'export';root.mkdir();outside=tmp_path/'outside';outside.write_bytes(b'keep')
    monkeypatch.setattr(writer,'EXPORT_ROOT',root)
    expected=pin(root);value=envelope(os_policy);leaf=writer.publish(value,expected_root=expected)
    api=win.WinAPI();held=api.open(str(leaf),False)
    before=leaf.read_bytes()
    try:
        monkeypatch.setattr(writer,'MAX_EXPORT_BYTES',len(before))
        with pytest.raises(ValueError,match='EXPORT_BYTE_LIMIT'):writer.publish(value,expected_root=expected)
        assert leaf.read_bytes()==before and outside.read_bytes()==b'keep'
        assert list(root.iterdir())==[leaf]
    finally:api.close(held)


def test_native_panel_restart_does_not_change_disposable_task_or_process(os_policy,tasks,monkeypatch):
    from streamlit.testing.v1 import AppTest
    from cc.providers import h1_export as receiver
    fixtures,folder=tasks
    # Native OS acquisition occurs outside the panel; UI receives only an envelope.
    p=task_policy(os_policy,fixtures['Ready'])
    p['task_name']=observer.TASK # collect's fixed production allowlist is preserved
    value=observer.collect(p,facts=lambda _:observer.os_facts(task_policy(os_policy,fixtures['Ready'])))
    monkeypatch.setattr(receiver,'read_latest_windows',lambda *a:json.dumps(value).encode())
    monkeypatch.setattr(receiver,'installed_policy',lambda:approved(os_policy))
    before=fixture_operation('Inspect',folder)
    for _ in range(2):
        app=AppTest.from_file(str(Path(__file__).parents[1]/'app.py'),default_timeout=15).run()
        app.selectbox(key='h1-source').select('READONLY_EXPORT').run()
        assert not app.exception
        app.radio[0].set_value('Монитор H1').run()
        assert any('TASK_RUNNING / PROCESS_OBSERVED' in str(c.value) for c in app.caption)
    assert fixture_operation('Inspect',folder)==before
