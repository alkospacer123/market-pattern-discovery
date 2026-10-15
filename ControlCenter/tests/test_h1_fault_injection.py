"""Independent I/O fault harness: mutate real temporary files during receiver reads.

No production data, SQLite connection, broker library or runtime constructor.
"""
import ast
from copy import deepcopy
from datetime import timedelta
import hashlib
import json
import os
from pathlib import Path
import socket
import sqlite3
import subprocess
import urllib.request
import pytest
from cc.models import RobotId, State
from cc.providers import h1_readonly as adapter
from cc.providers import readonly_file as reader
from cc.providers.h1_contract import MAX_BYTES
from cc.providers.h1_readonly import H1ReadonlyProvider, SAFE_ERROR


posix_only = pytest.mark.skipif(os.name == "nt", reason="POSIX descriptor fault injection; native Windows equivalents in test_windows_reader.py")


def get(now):
    return H1ReadonlyProvider().snapshot(RobotId.H1, 'BASELINE', now)


def unknown(now):
    result = get(now)
    assert result.status.state == State.UNKNOWN
    assert result.status.provenance.observed_at is None
    assert result.events[0].message == SAFE_ERROR
    assert result.positions is None and not result.orders
    assert result.portfolio.equity is None
    return result


def test_missing_source_has_no_last_good(h1_export, publish, now):
    path = publish(h1_export)
    assert get(now).status.state == State.HALTED
    path.unlink()
    unknown(now)


@pytest.mark.parametrize('attack', ['file_symlink','directory_symlink','ancestor_symlink','hardlink','fifo','directory'])
@posix_only
def test_unsafe_files_and_ancestors_rejected(h1_export, publish, now, tmp_path, monkeypatch, attack):
    path = publish(h1_export)
    if attack == 'file_symlink':
        target = tmp_path/'elsewhere.json'; path.rename(target); path.symlink_to(target)
    elif attack == 'hardlink':
        os.link(path, tmp_path/'second-name')
    elif attack == 'fifo':
        path.unlink(); os.mkfifo(path)
    elif attack == 'directory':
        path.unlink(); path.mkdir()
    else:
        link = tmp_path/'link'
        actual = tmp_path/'actual'; actual.mkdir()
        path.rename(actual/'h1.snapshot.json')
        link.symlink_to(actual, target_is_directory=True)
        if attack == 'directory_symlink':
            monkeypatch.setattr(adapter,'FIXTURE_ROOT',link)
        else:
            child = actual/'child'; child.mkdir()
            (actual/'h1.snapshot.json').rename(child/'h1.snapshot.json')
            monkeypatch.setattr(adapter,'FIXTURE_ROOT',link/'child')
    unknown(now)


@pytest.mark.parametrize('name', ['../h1.snapshot.json','/etc/passwd','h1.snapshot.json.tmp','other.json','sub/h1.snapshot.json'])
def test_file_allowlist_rejects_traversal(tmp_path, name):
    with pytest.raises(ValueError): reader.read_snapshot(tmp_path,name,MAX_BYTES)


def test_parent_traversal_rejected(tmp_path):
    with pytest.raises(ValueError): reader.read_snapshot(tmp_path/'..'/'other','h1.snapshot.json',MAX_BYTES)


@pytest.mark.parametrize('attack', ['replace','truncate','grow','rewrite','symlink','root_replace','root_symlink'])
@posix_only
def test_partial_write_and_path_races_fail_closed(h1_export, publish, now, tmp_path, monkeypatch, attack):
    path = publish(h1_export)
    real_read = os.read
    fired = False
    def mutate(fd, size):
        nonlocal fired
        data = real_read(fd, size)
        if not fired:
            fired = True
            if attack == 'replace':
                replacement=tmp_path/'replacement'; replacement.write_bytes(path.read_bytes()); replacement.replace(path)
            elif attack == 'truncate': path.write_bytes(b'{')
            elif attack == 'grow':
                with path.open('ab') as stream: stream.write(b' '*(MAX_BYTES+1))
            elif attack == 'rewrite': path.write_bytes(path.read_bytes())
            elif attack == 'symlink':
                target=tmp_path/'target'; path.rename(target); path.symlink_to(target)
            else:
                root=tmp_path/'root'; root.mkdir()
                path.rename(root/'h1.snapshot.json')
                # The provider opened tmp_path; moving that directory changes the path binding.
                renamed=tmp_path.with_name(tmp_path.name+'-retained')
                tmp_path.rename(renamed)
                if attack == 'root_symlink': tmp_path.symlink_to(renamed, target_is_directory=True)
                else:
                    tmp_path.mkdir(); (tmp_path/'h1.snapshot.json').write_bytes(b'{}')
        return data
    monkeypatch.setattr(os,'read',mutate)
    unknown(now)
    assert fired


@posix_only
def test_no_secure_platform_primitive_fails_closed(h1_export, publish, now, monkeypatch):
    publish(h1_export)
    monkeypatch.setattr(os,'supports_dir_fd',set())
    unknown(now)


def test_bounded_read_rejects_fake_small_stat(h1_export, publish, now, monkeypatch):
    path = publish(h1_export)
    initial = path.stat()
    path.write_bytes(b' '*(MAX_BYTES+100))
    monkeypatch.setattr(os,'fstat',lambda fd: initial)
    unknown(now)


@posix_only
def test_read_uses_no_write_capability_or_external_systems(h1_export, publish, now, monkeypatch):
    path = publish(h1_export)
    before = path.stat(), hashlib.sha256(path.read_bytes()).hexdigest()
    original = os.open
    flags = []
    def readonly_open(name, mode, *args, **kwargs):
        assert mode & (os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC|os.O_APPEND) == 0
        flags.append(mode)
        return original(name, mode, *args, **kwargs)
    # os.supports_dir_fd contains callable identities, preserve the secure capability selector.
    monkeypatch.setattr(os,'supports_dir_fd',os.supports_dir_fd|{readonly_open})
    monkeypatch.setattr(os,'open',readonly_open)
    def prohibited(*args,**kwargs): raise AssertionError('external operation attempted')
    for module,name in ((sqlite3,'connect'),(subprocess,'Popen'),(os,'system'),
                         (socket,'create_connection'),(urllib.request,'urlopen')):
        monkeypatch.setattr(module,name,prohibited)
    assert get(now).status.state == State.HALTED
    assert flags and all(mode & os.O_NOFOLLOW for mode in flags)
    after = path.stat(), hashlib.sha256(path.read_bytes()).hexdigest()
    assert before[1] == after[1]
    assert (before[0].st_size,before[0].st_mtime_ns,before[0].st_ctime_ns) == (after[0].st_size,after[0].st_mtime_ns,after[0].st_ctime_ns)


def test_no_runtime_write_call_paths():
    root=Path(__file__).parents[1]/'cc'
    forbidden={'write','writev','pwrite','fdopen','write_text','write_bytes','touch','unlink','remove',
               'mkdir','makedirs','rename','link','symlink','chmod','chown','truncate',
               'ftruncate','connect','execute','executescript','commit','system','popen','Popen'}
    allowed_os={'open','close','read','stat','fstat'}
    for path in root.rglob('*.py'):
        tree=ast.parse(path.read_text(encoding='utf-8'))
        for node in ast.walk(tree):
            if isinstance(node,ast.Call) and isinstance(node.func,ast.Attribute):
                display_write = (path.name == 'ui.py' and isinstance(node.func.value,ast.Name)
                                 and node.func.value.id == 'st' and node.func.attr == 'write')
                assert display_write or node.func.attr not in forbidden, (path,node.func.attr)
                if isinstance(node.func.value,ast.Name) and node.func.value.id=='os':
                    assert path.name=='readonly_file.py' and node.func.attr in allowed_os


def test_nested_unknown_fields_rejected_without_leak(h1_export, publish, now):
    # Independently walk every object from the actual wire sample, not the schema.
    targets=[]
    def walk(value,route=()):
        if isinstance(value,dict):
            targets.append(route)
            for key,child in value.items(): walk(child,route+(key,))
        elif isinstance(value,list):
            for key,child in enumerate(value): walk(child,route+(key,))
    walk(h1_export)
    for route in targets:
        value=deepcopy(h1_export); target=value
        for key in route: target=target[key]
        target['SECRET_UNKNOWN_FIELD']='SECRET_ACCOUNT_TOKEN'
        publish(value)
        result=unknown(now)
        assert 'SECRET_ACCOUNT_TOKEN' not in repr(result)


def test_receipt_time_does_not_resurrect_stale_healthy(h1_export, publish, now):
    # Independent clock jump; do not call the provider's freshness helper.
    v=h1_export
    v['runtime'].update(state='HEALTHY',heartbeat_at=v['observed_at'],last_successful_cycle_at=v['observed_at'])
    v['reconciliation'].update(observed_at=v['observed_at'],last_success_at=v['observed_at'],status='PASS',unresolved_intents=0)
    publish(v)
    assert get(now).status.state==State.HEALTHY
    later=get(now+timedelta(days=1))
    assert later.status.state==State.STALE
    assert later.status.provenance.observed_at==now
    assert later.status.provenance.received_at==now+timedelta(days=1)
