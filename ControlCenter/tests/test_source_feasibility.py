"""No real source is supplied: provenance cannot be created by rehashing a fixture."""
from copy import deepcopy
from datetime import timedelta
import json
from pathlib import Path
import socket
import sqlite3
import subprocess
import urllib.request

import pytest
from cc.models import RobotId, SourceKind, State
from cc.providers import h1_export as receiver
from cc.providers import readonly_file
from cc.providers.h1_readonly import canonical_digest
from exporter import snapshot as exporter
from test_cc03_source import policy, sources, export, approved


def test_default_collection_fails_before_all_source_capabilities(policy, now, monkeypatch):
    calls = []
    def forbidden(*args, **kwargs):
        calls.append(True)
        raise AssertionError('source capability called')
    for module, name in ((readonly_file, '_read_file'), (readonly_file, 'read_windows'),
                         (exporter, 'read_source'), (exporter, 'read_windows'),
                         (Path, 'open'), (socket, 'create_connection'),
                         (sqlite3, 'connect'), (subprocess, 'Popen'),
                         (urllib.request, 'urlopen')):
        monkeypatch.setattr(module, name, forbidden)
    with pytest.raises(ValueError, match='^CC03_LIVE_SOURCE_COMPATIBILITY_BLOCKED$'):
        exporter.collect(policy, now)
    for leaf in (exporter.HB, exporter.KS, 'stage8-12-production.sqlite3'):
        with pytest.raises(ValueError, match='^CC03_LIVE_SOURCE_COMPATIBILITY_BLOCKED$'):
            readonly_file.read_source(policy['heartbeat_root'], leaf, [1, 2, 3])
    assert not calls


def receive(value, p, now, monkeypatch):
    value['payload_sha256'] = canonical_digest(value)
    raw = json.dumps(value).encode()
    reads = []
    def read(*args):
        reads.append(args)
        return raw
    monkeypatch.setattr(receiver, 'read_latest_windows', read)
    result = receiver.H1ExportProvider(p).snapshot(RobotId.H1, 'READONLY_EXPORT', now)
    assert len(reads) == 1
    return result


def test_existing_fixture_never_becomes_live_authority(h1_export, policy, now, monkeypatch):
    result = receive(h1_export, approved(policy), now, monkeypatch)
    assert result.status.state == State.UNKNOWN
    assert result.status.provenance.source_kind == SourceKind.READONLY_EXPORT
    assert result.status.provenance.account_scope == 'UNBOUND-H1'
    assert result.positions is None and result.portfolio.equity is None
    assert result.readonly_identity is None and not result.signals and not result.orders


@pytest.mark.parametrize('attack', ['source', 'account', 'binding', 'robot', 'release', 'spec',
                                    'future_source', 'unknown_field', 'broker_authority'])
def test_rehashed_provenance_substitution_rejected(policy, sources, now, monkeypatch, attack):
    value = export(policy, sources, now)
    if attack in {'source', 'account', 'binding', 'robot', 'release', 'spec'}:
        name, bad = {
            'source': ('source_id', 'CC03-H1-OTHER001'),
            'account': ('account_alias', 'H1-OTHER001'),
            'binding': ('binding_id', 'c' * 64),
            'robot': ('robot_id', 'M15'),
            'release': ('installed_code_commit', '0' * 40),
            'spec': ('production_specification_id', 'OTHER_SPEC'),
        }[attack]
        value['identity'][name] = bad
    elif attack == 'future_source':
        value['heartbeat']['observed_at'] = (now + timedelta(seconds=1)).isoformat()
    elif attack == 'unknown_field':
        value['positions'] = {'complete': True, 'items': []}
    else:
        value['finances'].update(status='AVAILABLE', observed_at=now.isoformat(),
                                 value={'equity': 100000})
    result = receive(value, approved(policy), now, monkeypatch)
    assert result.status.state == State.UNKNOWN and result.readonly_identity is None
    assert result.status.provenance.account_scope == 'UNBOUND-H1'
    assert result.status.heartbeat_at is None and result.positions is None
    assert result.portfolio.equity is None and not result.signals and not result.orders


def test_receipt_does_not_refresh_original_source_clock(policy, sources, now, monkeypatch):
    value = export(policy, sources, now)
    original = deepcopy(value)
    first = receive(value, approved(policy), now, monkeypatch)
    assert first.status.state == State.HALTED  # SYNTHETIC input only; not live evidence.
    later = now + timedelta(seconds=61)
    second = receive(value, approved(policy), later, monkeypatch)
    assert second.status.state == State.STALE
    assert second.status.provenance.received_at == later
    assert second.status.provenance.observed_at == first.status.provenance.observed_at == now
    assert value == original
    assert second.positions is None and second.portfolio.equity is None


def test_etw_reader_family_includes_venv_redirector_without_producer():
    from ci.file_open_trace import descendant_pids
    def edge(parent, child):
        return dict(provider='Microsoft-Windows-Kernel-Process', id='1',
                    values={'ParentProcessID': str(parent), 'ProcessID': hex(child)})
    records = [edge(20, 30), edge(1, 40), edge(40, 50), edge(1, 10), edge(10, 20)]
    # 1=panel, 10=reader launcher, 20/30=interpreter descendants; 40/50=producer.
    assert descendant_pids(records, [10]) == {10, 20, 30}
