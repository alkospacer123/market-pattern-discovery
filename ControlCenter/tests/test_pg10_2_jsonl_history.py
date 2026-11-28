"""PG10.2 M06: lossless JSONL rotation, archive integrity and bounded reads."""
from datetime import datetime, timedelta, timezone
import json
import os
from pathlib import Path
import threading

import pytest

from deployment.v20_jsonl_history import (
    MAX_ACTIVE, archives, read_events, rotate,
)
from deployment.v20_live_export import events_from_log


ROBOT = "v20-shallow"
START = datetime(2026, 11, 28, 10, 0, tzinfo=timezone.utc)


def row(index, state="NO_FROZEN_SIGNAL"):
    return json.dumps({"utc": (START + timedelta(seconds=index)).isoformat(),
                       "robot": ROBOT, "state": state, "sequence": index}) + "\n"


def fixture(path, count=12):
    path.parent.mkdir(parents=True, exist_ok=True)
    original = "".join(row(i) for i in range(count)).encode()
    path.write_bytes(original)
    return original


def test_rotation_preserves_history_counters_order_and_recent_classification(tmp_path):
    active = tmp_path / "logs" / "live-m15.jsonl"
    original = fixture(active)
    result = rotate(active, robot=ROBOT)
    assert result["archive"].read_bytes() == original
    assert active.read_bytes() == b""
    assert len(archives(active, "live-m15", verify=True)) == 1
    with active.open("a", encoding="utf-8") as stream:
        stream.write(row(12, "R070_PROTECT3_REPLACED_NEEDS_NEXT_BROKER_CHECK"))
        stream.write(row(13))
    events = events_from_log(active, ROBOT, 12, START + timedelta(seconds=11))
    assert [event["cycle"] for event in events] == [13, 14]
    assert events[0]["result"] == "PENDING"
    assert events[1]["result"] == "PASS"
    assert result["archive"].read_bytes() == original


def test_crash_after_atomic_rename_loses_no_archive_and_writer_recovers(tmp_path, monkeypatch):
    active = tmp_path / "logs" / "live-m15.jsonl"
    original = fixture(active)
    original_open = Path.open

    def crash_create(self, mode="r", *args, **kwargs):
        if self == active and mode == "xb":
            raise KeyboardInterrupt("synthetic power loss after rename")
        return original_open(self, mode, *args, **kwargs)

    monkeypatch.setattr(Path, "open", crash_create)
    with pytest.raises(KeyboardInterrupt):
        rotate(active, robot=ROBOT)
    monkeypatch.setattr(Path, "open", original_open)
    assert not active.exists()
    archived = archives(active, "live-m15", verify=True)
    assert len(archived) == 1 and archived[0]["path"].read_bytes() == original
    active.write_text(row(12), encoding="utf-8")
    events = read_events(active, "live-m15", ROBOT, 12, START + timedelta(seconds=11))
    assert len(events) == 1 and events[0]["cycle"] == 13


def test_concurrent_writer_is_excluded_or_appends_to_next_segment_without_loss(tmp_path):
    active = tmp_path / "logs" / "live-m15.jsonl"
    original = fixture(active, count=200)
    attempts = []
    stop = threading.Event()

    def writer():
        index = 200
        while not stop.is_set():
            try:
                with active.open("a", encoding="utf-8") as stream:
                    stream.write(row(index))
                attempts.append(index)
                index += 1
            except OSError:
                attempts.append("denied")
                break

    thread = threading.Thread(target=writer)
    thread.start()
    while not attempts:
        pass
    result = rotate(active, robot=ROBOT)
    stop.set()
    thread.join(timeout=5)
    assert not thread.is_alive()
    if not active.exists():
        active.write_bytes(b"")
    archived_rows = result["archive"].read_text(encoding="utf-8").splitlines()
    active_rows = active.read_text(encoding="utf-8").splitlines()
    combined = [json.loads(line)["sequence"] for line in archived_rows + active_rows]
    assert len(combined) == len(set(combined))
    assert combined == list(range(200)) + sorted(x for x in combined if x >= 200)
    assert set(range(200)).issubset(combined)
    assert "denied" in attempts or len(attempts) > 1


def test_concurrent_read_and_append_either_returns_valid_events_or_fails_closed(tmp_path):
    active = tmp_path / "logs" / "live-m15.jsonl"
    fixture(active)
    with active.open("a", encoding="utf-8") as stream:
        stream.write(row(12))
        try:
            events = read_events(active, "live-m15", ROBOT, 12,
                                 START + timedelta(seconds=11))
        except ValueError as error:
            assert "JSONL" in str(error)
        else:
            assert events[-1]["cycle"] == 13


def test_empty_oversize_unknown_and_corrupt_archives_fail_without_deletion(tmp_path):
    active = tmp_path / "logs" / "live-m15.jsonl"
    fixture(active, count=0)
    with pytest.raises(ValueError, match="EMPTY"):
        rotate(active, robot=ROBOT)
    assert active.exists()
    active.write_bytes(b"x")
    with active.open("r+b") as stream:
        stream.truncate(MAX_ACTIVE + 1)
    with pytest.raises(ValueError, match="FILE_INVALID"):
        rotate(active, robot=ROBOT)
    assert active.stat().st_size == MAX_ACTIVE + 1

    active = tmp_path / "other" / "live-m15.jsonl"
    original = fixture(active)
    result = rotate(active, robot=ROBOT)
    unknown = result["archive"].with_name("live-m15-unknown.jsonl")
    unknown.write_bytes(original)
    with pytest.raises(ValueError, match="NAME_INVALID"):
        archives(active, "live-m15")
    unknown.unlink()
    result["archive"].write_bytes(original + row(12).encode())
    with pytest.raises(ValueError, match="INTEGRITY"):
        archives(active, "live-m15", verify=True)
    assert result["archive"].exists() and unknown.exists() is False


def test_archive_change_during_snapshot_is_not_published(tmp_path, monkeypatch):
    active = tmp_path / "logs" / "live-m15.jsonl"
    fixture(active)
    import deployment.v20_jsonl_history as history
    original = history.archives
    calls = []

    def changing(*args, **kwargs):
        calls.append(1)
        rows = original(*args, **kwargs)
        if len(calls) == 2:
            return [dict(rows[0], name="changed")] if rows else [
                dict(name="changed", size=1)]
        return rows

    monkeypatch.setattr(history, "archives", changing)
    with pytest.raises(ValueError, match="ROTATION_DURING_READ"):
        read_events(active, "live-m15", ROBOT, 12, START + timedelta(seconds=11))
