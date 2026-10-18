"""Native concurrency + open-audit and handle-free metadata experiment, hosted only."""
import ctypes
from ctypes import wintypes as w
from datetime import datetime, timezone
import json
import multiprocessing
import os
from pathlib import Path
import subprocess
import sys
import time
import pytest
from observer import windows_os as observer
from cc.providers import h1_windows_os as manual
from ci.file_open_trace import file_create_trace, events_for
from test_manual_os import manual_policy, wire
from test_os_observer import os_policy
from test_os_windows_native import tasks, fixture_operation

pytestmark=pytest.mark.skipif(os.name!='nt',reason='NOT_VERIFIED: Windows native hosted VM required')


def replace_producer(root,stop,started,send):
    path=Path(root)/'stage8-12-4-production-heartbeat.json'
    i=0
    try:
        while not stop.is_set() or i<500:
            temporary=Path(root)/'next.tmp';temporary.write_bytes(str(i).encode())
            os.replace(temporary,path)
            i+=1;started.set();time.sleep(.003)
        send.send(dict(replacements=i,errors=[]))
    except BaseException as exc:send.send(dict(replacements=i,errors=[repr(exc)]))
    finally:send.close()


def test_native_manual_diagnostic_and_path_attributes_with_replace_zero_legacy_opens(
        manual_policy,tasks,tmp_path,monkeypatch):
    child=subprocess.Popen([sys.executable,'-c','import time;time.sleep(60)'])
    context=multiprocessing.get_context('spawn')
    stop=context.Event();started=context.Event();receive,send=context.Pipe(False)
    producer=context.Process(target=replace_producer,args=(str(tmp_path),stop,started,send))
    legacy=tmp_path/'stage8-12-4-production-heartbeat.json'
    legacy.write_bytes(b'initial')
    # Positive controls prove that the trace observes both parent and PS native
    # file opens. The diagnostic never receives the legacy path, even for metadata.
    parent_control=tmp_path/'parent-positive.txt';parent_control.write_bytes(b'control')
    ps_control=tmp_path/'ps-positive.txt';ps_control.write_bytes(b'control')
    try:
        binding=fixture_operation('Process',pid=child.pid)
        p=dict(manual_policy,process_binding=binding,**{k:v for k,v in tasks[0]['Ready'].items()
                                                    if k not in {'state','task_name'}})
        # Tests adapt only the exact Task name and standard identity check on the
        # elevated fixture token. Real unmodified ccpanel helper runs in rehearsal.
        def probe(q):
            fixture=dict(q,task_name=tasks[0]['Ready']['task_name'])
            del fixture['require_ccpanel']
            return observer.os_facts(fixture)
        wire(monkeypatch,p,probe)
        observed_pids=[os.getpid()]
        powershell_pids=[]
        original_popen=subprocess.Popen
        def tracked_popen(*a,**k):
            process=original_popen(*a,**k)
            observed_pids.append(process.pid)
            if str(a[0][0]).lower().endswith('powershell.exe'):powershell_pids.append(process.pid)
            return process
        monkeypatch.setattr(subprocess,'Popen',tracked_popen)
        with file_create_trace(tmp_path) as trace:
            # Fixture-generated path, passed by environment rather than shell interpolation.
            env=os.environ.copy();env['CC03_OPEN_CONTROL']=str(ps_control)
            result=subprocess.run(['powershell.exe','-NoProfile','-NonInteractive','-Command',
                '[IO.File]::ReadAllBytes($env:CC03_OPEN_CONTROL).Length'],env=env,capture_output=True,text=True,timeout=10)
            assert result.returncode==0, result.stderr
            # Fixed positive-control PS startup precedes the Python canary, so
            # provider enablement/manifest warmup cannot conceal the first read.
            parent_control.read_bytes()
            # Record native child PID separately through a fixed test-only child.
            # A source-opening regression is also rejected by the kernel audit,
            # even if sharing happens to allow all 500 replacements.
            producer.start();send.close()
            assert started.wait(10) and producer.is_alive()
            snapshot,accepted=manual.manual_os_refresh(datetime.now(timezone.utc))
            assert accepted and snapshot.status.task_state=='TASK_READY',snapshot
            assert snapshot.windows_observations[1].state=='PROCESS_OBSERVED'
            assert producer.is_alive()
            parent_control.read_bytes()
        assert any(e['pid']==os.getpid() for e in events_for(trace,parent_control)), 'PARENT_OPEN_POSITIVE_CONTROL_NOT_CAPTURED'
        assert any(e['pid'] in powershell_pids for e in events_for(trace,ps_control)), 'POWERSHELL_OPEN_POSITIVE_CONTROL_NOT_CAPTURED'
        assert len(powershell_pids)==2, 'EXPECTED_ONE_CONTROL_AND_ONE_DIAGNOSTIC'
        # Attribute events by native PID, excluding only the independent producer.
        # Includes BOTH panel Python and every fixed-helper PowerShell child.
        assert not [e for e in events_for(trace,legacy) if e['pid'] in observed_pids], 'LEGACY_FILE_OPEN_DETECTED'
        # Separate rejected path-attributes experiment AFTER the runtime audit.
        # Run 39111630879 proved that GetFileAttributesExW can emit kernel Create
        # events despite not exposing a caller-owned handle. Never call it a
        # zero-open path or include it in the source/observer trace acceptance.
        kernel=ctypes.WinDLL('kernel32',use_last_error=True)
        kernel.GetFileAttributesExW.argtypes=[w.LPCWSTR,ctypes.c_int,w.LPVOID]
        kernel.GetFileAttributesExW.restype=w.BOOL
        class Attributes(ctypes.Structure):
            _fields_=[('attributes',w.DWORD),('created',w.FILETIME),('accessed',w.FILETIME),
                      ('modified',w.FILETIME),('size_high',w.DWORD),('size_low',w.DWORD)]
        for _ in range(500):
            data=Attributes()
            assert kernel.GetFileAttributesExW(str(legacy),0,ctypes.byref(data)),ctypes.get_last_error()
        stop.set();producer.join(15)
        assert not producer.is_alive() and producer.exitcode==0 and receive.poll(1)
        done=receive.recv()
        assert not done['errors'] and done['replacements']>=500,done
        evidence=dict(replacements=done['replacements'],producer_errors=len(done['errors']),legacy_opens=0,
            observer_pids=observed_pids,producer_pid=producer.pid,
            parent_positive_opens=len(events_for(trace,parent_control)),
            powershell_positive_opens=len(events_for(trace,ps_control)),
            path_attribute_calls_outside_runtime_audit=500,path_attributes='NOT_ACCEPTED_KERNEL_OPENS_OBSERVED',
            metadata_runtime='DISABLED',task_process='OS_ONLY')
        (Path(os.environ['RUNNER_TEMP'])/'cc03-evidence/manual-os-noninterference.json').write_text(json.dumps(evidence,indent=2))
        print('MANUAL_OS_NATIVE_ZERO_LEGACY_OPENS='+json.dumps(evidence))
    finally:
        stop.set()
        if producer.pid is not None:
            producer.join(15)
            if producer.is_alive():producer.terminate();producer.join(5)
        receive.close();send.close()
        child.terminate();child.wait(5)


def test_native_manual_rejects_real_elevated_identity_before_helper(manual_policy,monkeypatch):
    from observer.identity import current_identity
    sid,unsafe=current_identity()
    assert unsafe
    manual_policy['observer_sid']=sid
    monkeypatch.setattr(manual,'installed_policy',lambda:manual.policy_check(manual_policy))
    monkeypatch.setattr(manual,'os_facts',lambda p:pytest.fail('elevated token invoked helper'))
    assert not manual.manual_os_refresh(datetime.now(timezone.utc))[1]
