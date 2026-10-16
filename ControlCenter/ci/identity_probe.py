"""Separate-SID Python/spawn proof using synthetic bytes, disposable VM only."""
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
    from observer.metadata import metadata_native
    state, metadata = metadata_native(str(root),path.name,pin)
    assert state == 'FILE_PRESENT' and metadata['size'] == 2
    print('LOW_SID_OS_READONLY_TASK_AND_REAL_ACCESS_DENIED_METADATA=PASS',flush=True)
    if sys.argv[2] == 'e':
        # CI-only transport proof under the real Exporter token. No H1 reads;
        # all observations and binding remain UNKNOWN/unverified.
        from datetime import datetime, timezone
        from exporter.snapshot import publish
        from cc.providers.source_contract import SCHEMA_ID
        from cc.providers.h1_contract import SPEC, ACTIVE, ACCEPTED_COMMIT
        from cc.providers.h1_readonly import canonical_digest
        value=dict(schema_id=SCHEMA_ID,payload_sha256='0'*64,generated_at=datetime.now(timezone.utc).isoformat(),
                   identity=dict(robot_id='H1',strategy_id='T3/H1/TRAIL1',production_specification_id=SPEC,
                                 active_identity=ACTIVE,installed_code_commit=ACCEPTED_COMMIT,
                                 source_id='CC03-H1-CIONLY0001',account_alias='H1-CIONLY',binding_id='0'*64,account_binding='UNVERIFIED'))
        for group,source in dict(heartbeat='H1_PRODUCTION_HEARTBEAT',reconciliation='H1_PRODUCTION_HEARTBEAT',
                                 kill_switch='H1_KILL_SWITCH_FILE',task='WINDOWS_TASK_PROBE',candles='APPROVED_H1_CALENDAR',
                                 finances='APPROVED_ACCOUNT_FINANCE',execution='APPROVED_EXECUTION_EVENTS').items():
            value[group]=dict(source=source,status='UNAVAILABLE',observed_at=None,value=None)
        value['payload_sha256']=canonical_digest(value)
        completed=publish(value)
        assert completed.exists()
        print('SYNTHETIC_UNKNOWN_TRANSPORT_UNDER_EXPORTER=PASS',flush=True)
    print(json.dumps(dict(identity_python='PASS',expected_sid=sys.argv[1],python=sys.version,
                          executable=sys.executable,cwd=os.getcwd(),spawn=multiprocessing.get_start_method(),
                          ntfs_read_spawn='PASS')),flush=True)


if __name__ == '__main__': main()
