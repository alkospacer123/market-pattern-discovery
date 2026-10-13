from pathlib import Path
import re

SCRIPT = Path(__file__).resolve().parents[1] / 'diagnostics' / 'stage8-493-pre-isolation-readonly.ps1'

def test_pre_isolation_shell_no_task_mutation_or_broker_writes():
    data=SCRIPT.read_text()
    assert 'stage8_493_isolation_sqlite_readonly.py' in data
    assert 'stage8-493-finam-broker-flat-readonly.ps1' in data
    assert 'SQLITE_PRE_BROKER_AUDIT_BLOCKED' in data and 'SQLITE_POST_BROKER_AUDIT_BLOCKED' in data
    assert 'STOP_TASK_AUTHORIZED_BY_THIS_SCRIPT=NO' in data
    for forbidden in ('stop-scheduledtask','disable-scheduledtask','set-scheduledtask','stop-process',
                      'place_order','place_sltp_order','cancel_order','invoke-restmethod',
                      'set-content','get-tradingcredential','start-scheduledtask'):
        assert forbidden not in data.lower()
    assert 'push-location -literalpath $checkout' in data and 'pop-location' in data
    assert 'git -c ' not in data
    assert 'git rev-parse @' in data
    cmds=['get-filehash','test-path','get-scheduledtask','get-ciminstance','write-output','get-content']
    assert all(x in data for x in cmds)
    assert not re.search(r'(?m)^\s*[A-Z]+-[A-Za-z]',data)
