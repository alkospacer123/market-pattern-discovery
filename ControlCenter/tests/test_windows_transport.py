"""Immutable CC-owned transport; legacy H1 compatibility is separately blocked."""
import hashlib
import json
import os
import multiprocessing
from pathlib import Path
import subprocess
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
            for i in range(600):
                temporary=tmp_path/'next.tmp'; temporary.write_bytes(str(i).encode())
                os.replace(temporary,path)
        except BaseException as exc: errors.append(exc)
    thread=threading.Thread(target=produce); thread.start()
    for _ in range(600):
        with pytest.raises(ValueError,match='CC03_LIVE_SOURCE_COMPATIBILITY_BLOCKED'):
            # No H1 directory metadata/handle is needed to reject this reader.
            read_source(tmp_path,path.name,(1,2,3))
    thread.join(10)
    assert not thread.is_alive() and not errors and path.read_bytes()==b'599'


def test_native_one_manual_immutable_read_with_legacy_replacements_zero_h1_opens(
        policy, sources, now, tmp_path, monkeypatch):
    from datetime import datetime, timezone
    from cc.models import RobotId, State
    from cc.providers import h1_export as receiver
    from ci.file_open_trace import file_create_trace, events_for, descendant_pids, process_edges
    from test_cc03_source import approved
    from test_manual_os_native import replace_producer

    # Entirely synthetic source and separate CC output in disposable hosted VM.
    legacy_root = tmp_path / 'legacy'; legacy_root.mkdir()
    cc_root = tmp_path / 'cc-export'; cc_root.mkdir()
    legacy = legacy_root / 'stage8-12-4-production-heartbeat.json'
    legacy.write_bytes(b'initial')
    before = tmp_path / 'before-positive.txt'; before.write_bytes(b'before')
    after = tmp_path / 'after-positive.txt'; after.write_bytes(b'after')
    monkeypatch.setattr(writer, 'EXPORT_ROOT', cc_root)
    monkeypatch.setattr(receiver, 'EXPORT_ROOT', cc_root)
    # Current wall clock is required for receiving a bounded synthetic observation.
    now = datetime.now(timezone.utc)
    sources[writer.HB]['timestamp'] = sources[writer.HB]['last_successful_finam_api_contact'] = now.isoformat()
    completed = writer.publish(export(policy, sources, now))
    expected_raw = completed.read_bytes()
    p = approved(policy, export_root_id=pin(cc_root))
    context = multiprocessing.get_context('spawn')
    stop, started = context.Event(), context.Event()
    receive, send = context.Pipe(False)
    producer = context.Process(target=replace_producer, args=(str(legacy_root), stop, started, send))
    observed_pids = [os.getpid()]
    reader_launchers = []
    original_popen = subprocess.Popen
    def tracked_popen(*args, **kwargs):
        child = original_popen(*args, **kwargs)
        observed_pids.append(child.pid)
        command = args[0]
        if (isinstance(command, list) and len(command) == 4 and command[1:3] == ['-I', '-B']
                and Path(command[3]).name == 'windows_file.py'):
            reader_launchers.append(child.pid)
        return child
    monkeypatch.setattr(subprocess, 'Popen', tracked_popen)
    try:
        with file_create_trace(tmp_path, process_events=True) as trace:
            # Warm the provider before the canary bracket, as in existing OS audit.
            env = os.environ.copy(); env['CC03_OPEN_CONTROL'] = str(before)
            control = subprocess.run(['powershell.exe', '-NoProfile', '-NonInteractive', '-Command',
                '[IO.File]::ReadAllBytes($env:CC03_OPEN_CONTROL).Length'],
                env=env, capture_output=True, text=True, timeout=10)
            assert control.returncode == 0
            before.read_bytes()
            producer.start(); send.close()
            assert started.wait(10) and producer.is_alive()
            probes = []
            def read_once():
                probes.append(True)
                return receiver.H1ExportProvider(p).snapshot(RobotId.H1, 'READONLY_EXPORT', now)
            result, accepted = receiver.manual_export_refresh(now, reader=read_once)
            assert accepted and len(probes) == 1 and result.status.state == State.HALTED
            assert result.positions is None and result.portfolio.equity is None
            assert producer.is_alive()
            after.read_bytes()
            stop.set(); producer.join(15)
            assert not producer.is_alive() and producer.exitcode == 0 and receive.poll(1)
            done = receive.recv()
            assert not done['errors'] and done['replacements'] >= 500, done
        assert events_for(trace, before) and events_for(trace, after), 'CANARY_BRACKET_MISSING'
        assert any(e['pid'] == os.getpid() for e in events_for(trace, before))
        assert any(e['pid'] == os.getpid() for e in events_for(trace, after))
        # Include each fixed child's real interpreter descendants, excluding the
        # independent producer tree. Never accept an arbitrary PID's file event.
        assert len(reader_launchers) == 1
        reader_family = descendant_pids(trace, reader_launchers)
        observer_family = {os.getpid()} | descendant_pids(trace, observed_pids[1:])
        assert producer.pid not in observer_family
        completed_events = events_for(trace, completed)
        assert any(e['pid'] in reader_family for e in completed_events), (
            'CC_READER_NOT_OBSERVED', sorted(reader_family), completed_events, process_edges(trace))
        assert not [e for e in events_for(trace, legacy) if e['pid'] in observer_family], 'H1_OPEN_DETECTED'
        assert completed.read_bytes() == expected_raw and not list(cc_root.glob('*.tmp'))
        evidence = dict(classification='SYNTHETIC_IMMUTABLE_TRANSPORT_ONLY_NO_LIVE_AUTHORITY',
            replacements=done['replacements'], producer_errors=0, legacy_opens=0,
            manual_probes=len(probes), observer_pids=sorted(observer_family), producer_pid=producer.pid,
            reader_launcher_pids=reader_launchers, reader_family=sorted(reader_family),
            completed_open_pids=sorted({e['pid'] for e in completed_events}), process_edges=process_edges(trace),
            before_canary_opens=len(events_for(trace, before)), after_canary_opens=len(events_for(trace, after)),
            live_source='NOT_AUTHORIZED / NO_SAFE_SOURCE')
        (Path(os.environ['RUNNER_TEMP']) / 'cc03-evidence/source-feasibility-noninterference.json').write_text(
            json.dumps(evidence, indent=2))
        print('SOURCE_FEASIBILITY_ZERO_H1_OPENS=' + json.dumps(evidence))
    finally:
        stop.set()
        if producer.pid is not None:
            producer.join(15)
            if producer.is_alive():
                producer.terminate(); producer.join(5)
        receive.close(); send.close()


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
