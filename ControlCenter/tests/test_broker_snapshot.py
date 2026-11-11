"""CC-03 broker immutable capture: isolated tests, no broker or production IO."""
from contextlib import contextmanager
from copy import deepcopy
from datetime import datetime, timezone, timedelta
import json
from pathlib import Path
import os
import subprocess

import pytest
from cc.providers import h1_broker_snapshot as broker

NOW = datetime(2026, 10, 20, 13, 52, 0, tzinfo=timezone.utc)


def approved():
    return dict(schema_id='cc03.broker-readonly-policy.v1', source_approved=True,
                export_root_id=[123, 0, 456], principal_sid_sha256='a'*64,
                credential_blob_sha256='b'*64, probe_sha256=broker.PROBE,
                received_ttl_seconds=180)


def capture():
    return dict(schema_id=broker.SCHEMA, robot_id='H1', source_id=broker.SOURCE,
                production_id=broker.SPEC, probe_sha256=broker.PROBE,
                principal_sid_sha256='a'*64, credential_blob_sha256='b'*64,
                received_at_utc='2026-10-20T13:51:25Z',
                broker_original_snapshot_timestamp=None,
                readonly_session_verified=True, account_response_identity_verified=True,
                position_contracts={'USDRUBF': 0, 'CNYRUBF': 0, 'GLDRUBF': 0, 'IMOEXF': 0},
                other_nonzero_position_symbols=0, order_rows=0, active_order_rows=0,
                active_sltp_order_rows=0, positions_complete=False, orders_complete=False,
                h1_account_ownership_verified=False, stop_coverage_verified=False)


def encoded(value):
    return json.dumps(value, separators=(',', ':')).encode('utf-8')


def test_observed_zero_is_not_verified_flat_or_protected():
    observed = broker.validate(encoded(capture()), broker._policy(approved()), NOW)
    assert observed['status'] == 'CURRENT'
    assert observed['quantities']['USDRUBF'] == 0
    assert observed['order_rows'] == observed['active_sltp'] == 0
    assert observed['original_source_timestamp'] is None
    assert observed['h1_account_ownership'] == 'UNVERIFIED'
    assert observed['stop_coverage'] == 'UNVERIFIED'
    assert observed['completeness'] == 'NOT_PROVEN_BY_API_RESPONSE'
    assert broker.age(observed, observed['expires_at'] + timedelta(seconds=1))['status'] == 'STALE'
    assert broker.age(observed, NOW - timedelta(hours=1))['status'] == 'STALE'


@pytest.mark.parametrize('case', [
    'source', 'production', 'probe', 'sid', 'credential', 'future', 'negative_count',
    'count_inversion', 'bool_quantity', 'unknown_symbol', 'h1_claim', 'stop_claim',
    'positions_complete', 'orders_complete', 'source_timestamp', 'readonly_false',
    'account_false', 'extra', 'wrong_robot'])
def test_forged_or_incomplete_capture_rejected(case):
    x = capture()
    if case == 'source': x['source_id'] = 'CC03-H1-MISMATCH'
    elif case == 'production': x['production_id'] = 'OTHER'
    elif case == 'probe': x['probe_sha256'] = 'f'*64
    elif case == 'sid': x['principal_sid_sha256'] = 'f'*64
    elif case == 'credential': x['credential_blob_sha256'] = 'f'*64
    elif case == 'future': x['received_at_utc'] = '2026-10-20T15:00:00Z'
    elif case == 'negative_count': x['order_rows'] = -1
    elif case == 'count_inversion': x['active_sltp_order_rows'] = 1
    elif case == 'bool_quantity': x['position_contracts']['USDRUBF'] = True
    elif case == 'unknown_symbol': x['position_contracts']['SBER'] = 1
    elif case == 'h1_claim': x['h1_account_ownership_verified'] = True
    elif case == 'stop_claim': x['stop_coverage_verified'] = True
    elif case == 'positions_complete': x['positions_complete'] = True
    elif case == 'orders_complete': x['orders_complete'] = True
    elif case == 'source_timestamp': x['broker_original_snapshot_timestamp'] = x['received_at_utc']
    elif case == 'readonly_false': x['readonly_session_verified'] = False
    elif case == 'account_false': x['account_response_identity_verified'] = False
    elif case == 'extra': x['token'] = 'secret'
    elif case == 'wrong_robot': x['robot_id'] = 'M15'
    with pytest.raises(ValueError):
        broker.validate(encoded(x), approved(), NOW)


def test_duplicate_and_nonfinite_rejected():
    with pytest.raises(ValueError):
        broker.validate(b'{"schema_id":"x","schema_id":"y"}', approved(), NOW)
    with pytest.raises(ValueError):
        broker.validate(encoded(capture()).replace(b'0', b'NaN', 1), approved(), NOW)


@pytest.mark.parametrize('bad', [
    {'source_approved': False}, {'export_root_id': None}, {'received_ttl_seconds': 0},
    {'principal_sid_sha256': 'x'}, {'probe_sha256': 'f'*64},
])
def test_unapproved_policy_fails_closed(bad):
    policy = approved(); policy.update(bad)
    with pytest.raises(ValueError):
        broker._policy(policy)


def test_manual_one_click_only_reads_pinned_policy_and_completed_cc_file(monkeypatch):
    observed = []

    @contextmanager
    def gate():
        observed.append('gate')
        yield True

    def policy_read(root, name, size, **kwargs):
        observed.append(('policy', name, size, kwargs))
        return encoded(approved())

    def snapshot_read(root, size, pin):
        observed.append(('snapshot', str(root), size, pin))
        return encoded(capture())

    monkeypatch.setattr(broker, 'export_gate', gate)
    monkeypatch.setattr(broker, 'read_windows', policy_read)
    monkeypatch.setattr(broker, 'read_latest_windows', snapshot_read)
    result = broker.manual_broker_refresh(NOW)
    assert result['status'] == 'CURRENT'
    assert observed[0] == 'gate'
    assert observed[1] == ('policy', broker.POLICY, 4096, {'admin_policy': True})
    assert observed[2][1].lower().endswith('/broker-readonly') or observed[2][1].lower().endswith('\\broker-readonly')
    assert observed[2][3] == [123, 0, 456] and len(observed) == 3


def test_fail_closed_no_snapshot_if_policy_unapproved(monkeypatch):
    calls = []
    @contextmanager
    def gate():
        yield True
    monkeypatch.setattr(broker, 'export_gate', gate)
    monkeypatch.setattr(broker, 'read_windows', lambda *a, **k: encoded(dict(approved(), source_approved=False)))
    monkeypatch.setattr(broker, 'read_latest_windows', lambda *a, **k: calls.append(True))
    assert broker.manual_broker_refresh(NOW)['status'] == 'UNKNOWN'
    assert not calls


def test_operator_publisher_invokes_only_pinned_existing_readonly_probe():
    path = Path(__file__).parents[1] / 'broker_readonly/publish-from-one-shot.ps1'
    code = path.read_text(encoding='utf-8').lower()
    assert "33668f23c7ffb774e198b4f7ef55c85d73a6d407cd84b2a3cb1ea5bd6a97fc7c" in code
    assert "cc03-finam-one-shot.ps1" in code and "'finam-real-readonly.dpapi'" in code
    assert "readonly_session" in code and "h1_engine_account_ownership" in code
    assert "no_h1_json_sqlite_task_order_cancel_or_write" in code
    assert "cc03_broker_publish=preview_no_network_no_file_write" in code
    assert code.count('powershell.exe -noprofile') == 1
    assert code.count("throw 'probe_output_invalid'") == 1
    assert "^([a-z0-9_]+)=([a-za-z0-9_.:-]+)$" in code
    for forbidden in ('invoke-restmethod', 'start-scheduledtask', 'stop-scheduledtask',
                      'invoke-expression', 'set-acl', 'set-content', 'add-content',
                      '-method delete', 'cancel-order', 'place-order', 'sqlite3.connect'):
        assert forbidden not in code
    if os.name == 'nt':
        ps_path = str(path).replace("'", "''")
        parser = ("$tokens=$null;$errors=$null;"
                  "[void][management.automation.language.parser]::parsefile('"
                  + ps_path +
                  "',[ref]$tokens,[ref]$errors);if(@($errors).count -gt 0){exit 1}")
        p = subprocess.run(['powershell.exe', '-noprofile', '-noninteractive', '-command', parser],
                           capture_output=True, text=True, timeout=20)
        assert p.returncode == 0, 'PUBLISHER_SYNTAX_INVALID: ' + p.stdout + p.stderr
        p = subprocess.run(['powershell.exe', '-noprofile', '-noninteractive', '-file', str(path)],
                           capture_output=True, text=True, timeout=20)
        assert p.returncode == 0 and 'preview_no_network_no_file_write' in p.stdout
