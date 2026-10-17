"""Actual independent processes contend, including owner termination."""
from datetime import datetime, timezone
import os
from pathlib import Path
import subprocess
import sys
import pytest
from cc.manual_gate import export_gate
from cc.providers import h1_export

CHILD = '''from cc.manual_gate import export_gate
import sys
with export_gate() as acquired:
    print('ACQUIRED' if acquired else 'BLOCKED', flush=True)
    sys.stdin.readline()
'''


@pytest.mark.parametrize('terminate', [False, True])
def test_cross_process_manual_read_gate_and_owner_exit(terminate, monkeypatch):
    child=subprocess.Popen([sys.executable,'-u','-c',CHILD],stdin=subprocess.PIPE,stdout=subprocess.PIPE,
                           stderr=subprocess.PIPE,text=True,cwd=Path(__file__).parents[1])
    try:
        assert child.stdout.readline().strip()=='ACQUIRED'
        def forbidden(*a,**k): pytest.fail('contending click invoked provider')
        monkeypatch.setattr(h1_export.H1ExportProvider,'snapshot',forbidden)
        snapshot,accepted=h1_export.manual_export_refresh(datetime.now(timezone.utc))
        assert not accepted and snapshot.status.state=='UNKNOWN'
        if terminate: child.terminate()
        else: child.stdin.write('\n'); child.stdin.flush()
        child.wait(10)
        with export_gate() as acquired: assert acquired
    finally:
        if child.poll() is None: child.kill(); child.wait(10)
        child.stdin.close();child.stdout.close();child.stderr.close()


def test_gate_failure_never_calls_provider(monkeypatch):
    from contextlib import contextmanager
    @contextmanager
    def denied():
        raise PermissionError('PRIVATE')
        yield
    monkeypatch.setattr(h1_export,'export_gate',denied)
    monkeypatch.setattr(h1_export.H1ExportProvider,'snapshot',lambda *a:pytest.fail('provider called'))
    snapshot,accepted=h1_export.manual_export_refresh(datetime.now(timezone.utc))
    assert not accepted and snapshot.status.state=='UNKNOWN' and 'PRIVATE' not in repr(snapshot)
