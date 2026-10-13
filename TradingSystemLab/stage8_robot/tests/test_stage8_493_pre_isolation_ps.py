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
    assert "git rev-parse '@'" in data and 'git rev-parse @)' not in data
    assert "$env:pythondontwritebytecode = '1'" in data
    assert "setenvironmentvariable('pythondontwritebytecode', $previous_bytecode, 'process')" in data
    cmds=['get-filehash','test-path','get-scheduledtask','get-ciminstance','write-output','get-content']
    assert all(x in data for x in cmds)
    assert not re.search(r'(?m)^\s*[A-Z]+-[A-Za-z]',data)


def test_python_parent_child_chain_is_explicitly_bounded_and_revalidated():
    data = SCRIPT.read_text(encoding='utf-8').lower()
    for evidence in (
        'function get-verified-process-chain',
        '$matching.count -lt 1 -or $matching.count -gt 2',
        '$roots.count -ne 1',
        '$children.count -ne 1',
        'production_process_not_single_chain',
        "parent[0].name -ine 'powershell.exe'",
        "parent_cmd.indexof('run-production.ps1'",
        "parent_cmd.indexof($checkout",
        "parent_cmd.indexof($live_sha",
        'production_process_single_bound_chain=pass',
        '$post_chain = get-verified-process-chain',
        "post_chain.signature -cne $observed.signature",
        'stop_task_authorized_by_this_script=no',
    ):
        assert evidence in data
    assert 'production_process_not_uniquely_identified' not in data
    assert 'stop-scheduledtask' not in data
