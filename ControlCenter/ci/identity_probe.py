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
    with export_gate() as acquired:
        assert acquired, 'STANDARD_TOKEN_GLOBAL_MUTEX_UNAVAILABLE'
    print('LOW_SID_GLOBAL_MANUAL_MUTEX=PASS',flush=True)
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
