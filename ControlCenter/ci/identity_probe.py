"""Single standard ccpanel Python/spawn proof, disposable Windows VM only."""
import ctypes
import json
import multiprocessing
import os
from pathlib import Path
import sys
import subprocess
import csv
from cc.providers.windows_file import read_windows, WinAPI


def main():
    assert os.name == 'nt' and os.environ.get('RUNNER_ENVIRONMENT') == 'github-hosted'
    actual=next(csv.reader([subprocess.check_output(['whoami','/user','/fo','csv','/nh'],text=True).strip()]))[1]
    assert actual == sys.argv[1] and not ctypes.windll.shell32.IsUserAnAdmin()
    print('PYTHON_ACTUAL_SID='+actual,flush=True)
    import importlib
    managed = Path(os.environ['CC03_CI_DISPOSABLE_ROOT'])
    base = managed/'runtime/python312'
    assert Path(sys.executable) == managed/'venv/Scripts/python.exe'
    assert Path(sys.base_prefix) == base and Path(sys._base_executable) == base/'python.exe'
    assert Path(sys.prefix) == managed/'venv'
    assert 'include-system-site-packages = false' in (managed/'venv/pyvenv.cfg').read_text()
    for name in ('venv','ensurepip','ssl','streamlit','plotly','pip'):
        origin = Path(importlib.import_module(name).__file__)
        assert origin.is_relative_to(base) or origin.is_relative_to(managed/'venv')
    for denied in (managed/'protected-outside-cc/h1.sqlite3',
                   managed/'protected-outside-cc/unrelated-user-profile/python.exe'):
        try: denied.read_bytes()
        except PermissionError: pass
        else: raise AssertionError('OUTSIDE_RUNTIME_READ_ALLOWED')
    print('LOW_SID_MANAGED_PYTHON_BASE_VENV_MODULES_H1_PROFILE_DENIAL=PASS',flush=True)
    print(json.dumps(dict(executable=sys.executable,base_executable=sys._base_executable,
                         base_prefix=sys.base_prefix,prefix=sys.prefix)),flush=True)

    from ctypes import wintypes as w
    u=ctypes.WinDLL('user32',use_last_error=True)
    u.GetProcessWindowStation.restype=w.HANDLE
    u.GetThreadDesktop.argtypes=[w.DWORD]; u.GetThreadDesktop.restype=w.HANDLE
    u.GetUserObjectInformationW.argtypes=[w.HANDLE,ctypes.c_int,w.LPVOID,w.DWORD,ctypes.POINTER(w.DWORD)]
    def object_name(handle):
        buffer=ctypes.create_unicode_buffer(512); needed=w.DWORD()
        if not u.GetUserObjectInformationW(handle,2,buffer,ctypes.sizeof(buffer),ctypes.byref(needed)):
            raise ValueError('CURRENT_DESKTOP_NAME_UNAVAILABLE')
        return buffer.value
    print('IDENTITY_WINDOWSTATION='+object_name(u.GetProcessWindowStation()),flush=True)
    print('IDENTITY_DESKTOP='+object_name(u.GetThreadDesktop(ctypes.windll.kernel32.GetCurrentThreadId())),flush=True)
    # whoami is performed by the PS bootstrap; Python verifies access and spawn.
    root = Path(os.environ['TEMP'])
    path = root/'probe.json'; path.write_bytes(b'{}')
    api=WinAPI(); handle=api.open(str(root), True)
    try: pin=api.info(handle,str(root),True)[:3]
    finally: api.close(handle)
    assert read_windows(root,path.name,131072,pin) == b'{}'
    # These are CC03-CI UUID Tasks created by the guarded test harness, never H1.
    from observer.identity import current_identity
    from observer.windows_os import os_facts
    sid, elevated = current_identity()
    assert sid == actual and not elevated
    fixtures = json.loads((Path(os.environ['CC03_CI_DISPOSABLE_ROOT'])/'Os-Fixtures.json').read_text())
    for name, expected in [('Ready','TASK_READY'),('Denied','UNKNOWN')]:
        fixture = fixtures[name]
        facts = os_facts(dict(fixture, process_enabled=False))
        assert facts['task']['state'] == expected, facts
        if name == 'Denied': assert facts['task']['reason'] == 'ACCESS_DENIED', facts
    print('LOW_SID_OS_READONLY_TASK_AND_REAL_ACCESS_DENIED=PASS; METADATA_DISABLED',flush=True)
    # No private source policy read is possible under the actual panel token.
    try:
        (Path(os.environ['CC03_CI_DISPOSABLE_ROOT'])/'data/private/source-policy.json').read_bytes()
    except PermissionError:
        pass
    else:
        raise AssertionError('PANEL_PRIVATE_POLICY_READ_ALLOWED')
    from cc.manual_gate import export_gate
    child_gate = 'from cc.manual_gate import export_gate\nwith export_gate() as acquired: print("ACQUIRED" if acquired else "BLOCKED")'
    with export_gate() as acquired:
        assert acquired, 'STANDARD_TOKEN_LOCAL_PIPE_GATE_UNAVAILABLE'
        child = subprocess.run([sys.executable, '-c', child_gate], capture_output=True, text=True, timeout=10)
        assert child.returncode == 0 and child.stdout.strip() == 'BLOCKED', (child.stdout, child.stderr)
    child = subprocess.run([sys.executable, '-c', child_gate], capture_output=True, text=True, timeout=10)
    assert child.returncode == 0 and child.stdout.strip() == 'ACQUIRED', (child.stdout, child.stderr)
    print('LOW_SID_LOCAL_PIPE_GATE_ACQUIRE_CONTEND_RELEASE=PASS',flush=True)
    # Native protected C policy -> one unmodified standard-ccpanel helper ->
    # session-only conversion. Only CI maps the production Task name to UUIDs.
    from datetime import datetime, timezone, timedelta
    from cc.providers import h1_windows_os as manual
    from cc.providers.h1_export import age_export_snapshot
    location=json.loads((Path(os.environ['CC03_CI_DISPOSABLE_ROOT'])/'manual-policy-location.json').read_text())
    manual.POLICY_ROOT=Path(location['root'])
    real_facts=manual.os_facts
    for name in ('Ready','Denied'):
        manual.POLICY_NAME=name+'-manual-os-policy.json'
        p=manual.installed_policy()  # real secure spawned reader, every ancestor/leaf checked
        assert p['observer_sid']==sid and p['process_binding'] is None
        calls=[]
        def disposable_facts(q):
            calls.append(q)
            assert q['require_ccpanel'] is True and q['observer_sid']==sid
            return real_facts(dict(q,task_name=fixtures[name]['task_name']))
        manual.os_facts=disposable_facts
        result,accepted=manual.manual_os_refresh(datetime.now(timezone.utc))
        assert accepted and len(calls)==1, (accepted,result)
        assert result.status.state=='UNKNOWN' and result.status.heartbeat_at is None
        assert result.status.trading_allowed is None and result.positions is None
        if name=='Ready':
            assert result.status.task_state=='TASK_READY',result
            expired=age_export_snapshot(result,result.readonly_expires_at+timedelta(seconds=1))
            assert expired.status.task_state is None and expired.windows_observations[0].freshness=='STALE'
        else:
            assert result.status.task_state is None and result.windows_observations[0].reason=='ACCESS_DENIED',result
        assert all(r.state=='UNKNOWN' for r in result.windows_observations[1:])
    manual.os_facts=real_facts
    # Zero export writes: panel retains only its session-local immutable result.
    assert not list((Path(os.environ['CC03_CI_DISPOSABLE_ROOT'])/'data/export').glob('h1-*.json'))
    print('LOW_SID_MANUAL_C_PROTECTED_POLICY_ONE_HELPER_READY_DENIED_TTL_NO_EXPORT=PASS',flush=True)
    from ci.streamlit_click import main as streamlit_click
    streamlit_click(sid)
    # Permission-A preflight runs under the actual standard ccpanel token. The policy
    # remains fixed to H1; this CI-only adapter selects only UUID fixtures.
    from observer import intel_preflight as preflight
    import uuid
    for name in ('Running', 'Denied'):
        fixture = fixtures[name]
        policy = dict(schema_id='cc03.intel-preflight-policy.v2', readonly_preflight_approved=True,
            observer_sid=sid, task_name=preflight.TASK, task_xml_sha256=fixture['task_xml_sha256'],
            task_principal_sid=fixture['task_principal_sid'], process_binding=None,
            cc_panel_sid=sid)
        report = preflight.execute(policy,
            facts=lambda q: os_facts(dict(q, task_name=fixture['task_name'])))
        if name == 'Running':
            assert report['outcome'] == 'PASS' and report['task_state'] == 'TASK_RUNNING_OBSERVED', report
            assert report['task_before_after'] == 'UNCHANGED_OBSERVED', report
        else:
            assert report['outcome'] == 'BLOCKED' and report['task_access'] == 'ACCESS_DENIED', report
        assert report['cc_identities'] == 'CCPANEL_ENABLED', report
        assert all(v == 'UNKNOWN' for v in report['trading'].values()), report
    previous_root = os.environ['CC03_CI_DISPOSABLE_ROOT']
    try:
        os.environ['CC03_CI_DISPOSABLE_ROOT'] = str(Path(previous_root).parent / ('CC03-' + uuid.uuid4().hex))
        missing = preflight.readiness(policy)
        assert missing['observer_standard'] and missing['directories'] == 'NOT_PROVISIONED', missing
    finally:
        os.environ['CC03_CI_DISPOSABLE_ROOT'] = previous_root
    preview = subprocess.run([sys.executable, '-m', 'observer.intel_preflight'], capture_output=True, text=True, timeout=10)
    assert preview.returncode == 0 and json.loads(preview.stdout)['mode'] == 'PREVIEW'
    unapproved = subprocess.run([sys.executable, '-m', 'observer.intel_preflight', '--execute'],
                               capture_output=True, text=True, timeout=10)
    assert unapproved.returncode == 1 and json.loads(unapproved.stdout)['outcome'] == 'NOT_VERIFIED'
    print('LOW_SID_INTEL_PREFLIGHT_RUNNING_DENIED_MISSING_ROOTS_PREVIEW_UNAPPROVED=PASS', flush=True)
    print(json.dumps(dict(identity_python='PASS',expected_sid=sys.argv[1],python=sys.version,
                          executable=sys.executable,cwd=os.getcwd(),spawn=multiprocessing.get_start_method(),
                          ntfs_read_spawn='PASS')),flush=True)


if __name__ == '__main__': main()
