"""Immutable CC-owned transport; legacy H1 compatibility is separately blocked."""
import hashlib
import json
import os
from pathlib import Path
import threading
import pytest
from cc.providers import windows_file as win
from cc.providers.h1_readonly import canonical_digest
from exporter import snapshot as writer
from test_cc03_source import policy, sources, export

pytestmark = pytest.mark.skipif(os.name != 'nt', reason='NOT_VERIFIED: real Windows transport required')


def pin(root):
    api = win.WinAPI(); handle = api.open(str(root), True)
    try: return api.info(handle, str(root), True)[:3]
    finally: api.close(handle)


def test_completed_publications_do_not_replace_open_snapshot(policy, sources, now, tmp_path, monkeypatch):
    monkeypatch.setattr(writer, 'EXPORT_ROOT', tmp_path)
    value = export(policy, sources, now)
    first = writer.publish(value)
    api = win.WinAPI(); handle = api.open(str(first), False)
    errors, published = [], []
    def produce():
        try:
            for _ in range(24): published.append(writer.publish(value))
        except BaseException as exc: errors.append(exc)
    thread = threading.Thread(target=produce)
    thread.start()
    try:
        # Read and publish overlap with an existing leaf held continuously.
        for _ in range(24):
            raw = win._read_native(str(tmp_path), 'LATEST-COMPLETED', 131072, win.WinAPI(), pin(tmp_path))
            assert json.loads(raw) == value
        thread.join(10)
        assert not thread.is_alive() and not errors and len(published) == 24
        assert api.read(handle, 131072) == first.read_bytes()
    finally:
        thread.join(10); api.close(handle)
    assert len(set(published + [first])) == 25
    assert json.loads(win.read_latest_windows(tmp_path, 131072, pin(tmp_path))) == value
    assert not list(tmp_path.glob('*.tmp'))


def test_partial_and_corrupt_latest_fail_closed(policy, sources, now, tmp_path, monkeypatch):
    monkeypatch.setattr(writer, 'EXPORT_ROOT', tmp_path)
    value = export(policy, sources, now)
    first = writer.publish(value)
    (tmp_path / '.cc03-incomplete.tmp').write_bytes(b'{')
    assert json.loads(win.read_latest_windows(tmp_path, 131072, pin(tmp_path))) == value
    # Correct-looking completed name with wrong bytes never falls back to old.
    latest = tmp_path / ('h1-' + '9'*20 + '-' + 'a'*32 + '-' + '0'*64 + '.json')
    latest.write_bytes(b'{}')
    with pytest.raises(ValueError): win.read_latest_windows(tmp_path, 131072, pin(tmp_path))
    assert first.exists()


@pytest.mark.parametrize('attack', ['hardlink','symlink','directory','oversize','root_pin'])
def test_completed_transport_rejects_substitution(attack, tmp_path):
    name = 'h1-' + '1'*20 + '-' + 'a'*32 + '-' + hashlib.sha256(b'{}').hexdigest() + '.json'
    path = tmp_path / name
    path.write_bytes(b'{}')
    expected = pin(tmp_path)
    if attack == 'hardlink': os.link(path, tmp_path/'alias')
    elif attack == 'symlink':
        path.unlink(); target=tmp_path/'target'; target.write_bytes(b'{}'); path.symlink_to(target)
    elif attack == 'directory': path.unlink(); path.mkdir()
    elif attack == 'oversize': path.write_bytes(b' '*131073)
    else: expected = (0,0,0)
    with pytest.raises(ValueError): win.read_latest_windows(tmp_path, 131072, expected)


def test_reader_rejects_changed_completed_file(tmp_path):
    name = 'h1-' + '1'*20 + '-' + 'a'*32 + '-' + hashlib.sha256(b'{}').hexdigest() + '.json'
    path = tmp_path/name; path.write_bytes(b'{}')
    class Changed(win.WinAPI):
        def info(self, handle, pathname, directory):
            info = super().info(handle, pathname, directory)
            if not directory and getattr(self, 'read_done', False): return (*info[:3], info[3]+1, *info[4:])
            return info
        def read(self, handle, maximum):
            data=super().read(handle,maximum); self.read_done=True; return data
    with pytest.raises(ValueError, match='FILE_CHANGED'):
        win._read_native(str(tmp_path),'LATEST-COMPLETED',131072,Changed(),pin(tmp_path))


def test_unbounded_discovery_rejected(tmp_path, monkeypatch):
    for i in range(4): (tmp_path/str(i)).touch()
    monkeypatch.setattr(win, 'MAX_ENTRIES', 3)
    with pytest.raises(ValueError, match='EXPORT_DIRECTORY_FULL'):
        win._read_native(str(tmp_path),'LATEST-COMPLETED',131072,win.WinAPI(),pin(tmp_path))


def test_blocked_legacy_observer_does_not_interfere_with_unchanged_producer(tmp_path):
    from cc.providers.readonly_file import read_source
    path=tmp_path/'stage8-12-4-production-heartbeat.json'; path.write_bytes(b'{}')
    errors=[]
    def produce():
        try:
            for i in range(200):
                temporary=tmp_path/'next.tmp'; temporary.write_bytes(str(i).encode())
                os.replace(temporary,path)
        except BaseException as exc: errors.append(exc)
    thread=threading.Thread(target=produce); thread.start()
    for _ in range(200):
        with pytest.raises(ValueError,match='CC03_LIVE_SOURCE_COMPATIBILITY_BLOCKED'):
            read_source(tmp_path,path.name,pin(tmp_path))
    thread.join(10)
    assert not thread.is_alive() and not errors and path.read_bytes()==b'199'


def test_publisher_capacity_rejects_before_writing(policy,sources,now,tmp_path,monkeypatch):
    monkeypatch.setattr(writer,'EXPORT_ROOT',tmp_path)
    monkeypatch.setattr(writer,'MAX_ENTRIES',2)
    (tmp_path/'one').touch(); (tmp_path/'two').touch()
    before=set(tmp_path.iterdir())
    with pytest.raises(ValueError,match='EXPORT_DIRECTORY_FULL'):
        writer.publish(export(policy,sources,now))
    assert set(tmp_path.iterdir()) == before


def test_real_directory_substitution_between_requests_rejected(policy,sources,now,tmp_path,monkeypatch):
    root=tmp_path/'export'; root.mkdir()
    monkeypatch.setattr(writer,'EXPORT_ROOT',root)
    completed=writer.publish(export(policy,sources,now))
    expected=pin(root)
    original=tmp_path/'original'; root.rename(original)
    root.mkdir()
    # Even byte-identical completed content at the same pathname is a new root.
    (root/completed.name).write_bytes((original/completed.name).read_bytes())
    with pytest.raises(ValueError): win.read_latest_windows(root,131072,expected)
