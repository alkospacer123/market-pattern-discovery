"""Bounded JSONL history reading and explicit crash-safe Windows rotation.

Rotation is an operator maintenance action, never a check/UI/Task side effect.
The active file is renamed atomically into a self-describing immutable archive;
no historical segment is truncated or deleted.
"""
from __future__ import annotations

import argparse
from collections import deque
from datetime import datetime, timezone
from hashlib import sha256
import json
import os
from pathlib import Path
import re
import stat

MAX_ACTIVE = 64 * 1024 * 1024
STEMS = {"live-m15", "v20-control"}
STAMP = "%Y%m%dT%H%M%S.%fZ"


def _safe_file(path):
    try:
        info = path.lstat()
        return stat.S_ISREG(info.st_mode) and not path.is_symlink() and not (
            getattr(info, "st_file_attributes", 0) & 0x400)
    except OSError:
        return False


def _utc(value):
    if not isinstance(value, str) or len(value) > 48:
        raise ValueError("JSONL_BAD_TIMESTAMP")
    try:
        stamp = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as error:
        raise ValueError("JSONL_BAD_TIMESTAMP") from error
    if stamp.utcoffset() is None:
        raise ValueError("JSONL_NAIVE_TIMESTAMP")
    return stamp.astimezone(timezone.utc)


def _compact(stamp):
    return stamp.strftime(STAMP)


def _parse_compact(value):
    return datetime.strptime(value, STAMP).replace(tzinfo=timezone.utc)


def _scan(path, robot=None):
    if not _safe_file(path) or path.stat().st_size > MAX_ACTIVE:
        raise ValueError("JSONL_FILE_INVALID")
    count = 0
    first = last = None
    digest = sha256()
    recent = deque(maxlen=10)
    with path.open("rb") as stream:
        for raw in stream:
            digest.update(raw)
            if not raw.strip():
                continue
            recent.append(raw)
            try:
                row = json.loads(raw)
            except (ValueError, UnicodeError) as error:
                raise ValueError("JSONL_RECORD_INVALID") from error
            if type(row) is not dict or (robot is not None and row.get("robot") != robot):
                raise ValueError("JSONL_IDENTITY_INVALID")
            stamp = _utc(row.get("utc"))
            if last is not None and stamp < last:
                raise ValueError("JSONL_TIME_ORDER")
            first = stamp if first is None else first
            last = stamp
            count += 1
    return dict(count=count, first=first, last=last, sha256=digest.hexdigest(),
                size=path.stat().st_size, recent=list(recent))


def _descriptor(path, stem):
    match = re.fullmatch(
        re.escape(stem) +
        r"-(\d{8}T\d{6}\.\d{6}Z)-(\d{8}T\d{6}\.\d{6}Z)-([0-9]{1,12})-([a-f0-9]{64})\.jsonl",
        path.name)
    if match is None or not _safe_file(path):
        raise ValueError("JSONL_ARCHIVE_NAME_INVALID")
    count = int(match.group(3))
    first, last = _parse_compact(match.group(1)), _parse_compact(match.group(2))
    if count < 1 or first > last:
        raise ValueError("JSONL_ARCHIVE_METADATA_INVALID")
    return dict(path=path, name=path.name, count=count, first=first, last=last,
                sha256=match.group(4), size=path.stat().st_size)


def archives(active, stem, verify=False):
    folder = active.parent / "archive"
    if not folder.exists():
        return []
    if folder.is_symlink() or not folder.is_dir():
        raise ValueError("JSONL_ARCHIVE_DIRECTORY_INVALID")
    rows = [_descriptor(path, stem) for path in folder.iterdir()
            if path.name.startswith(stem + "-") and path.name.endswith(".jsonl")]
    rows.sort(key=lambda row: (row["first"], row["name"]))
    previous = None
    digests = set()
    for row in rows:
        if previous is not None and row["first"] < previous:
            raise ValueError("JSONL_ARCHIVE_TIME_ORDER")
        if row["sha256"] in digests:
            raise ValueError("JSONL_ARCHIVE_DUPLICATE")
        digests.add(row["sha256"])
        previous = row["last"]
        if verify:
            scanned = _scan(row["path"])
            if any(scanned[key] != row[key] for key in ("count", "first", "last", "sha256")):
                raise ValueError("JSONL_ARCHIVE_INTEGRITY")
    return rows


def read_events(active, stem, robot, count_at_check, last_at_check):
    if stem not in STEMS or not _safe_file(active):
        raise ValueError("JSONL_SOURCE_INVALID")
    before = archives(active, stem)
    before_identity = [(row["name"], row["size"]) for row in before]
    base = sum(row["count"] for row in before)
    archived_last = before[-1]["last"] if before else None
    scanned = _scan(active, robot=robot)
    after = archives(active, stem)
    if before_identity != [(row["name"], row["size"]) for row in after]:
        raise ValueError("JSONL_ROTATION_DURING_READ")
    if scanned["first"] is not None and archived_last is not None and scanned["first"] < archived_last:
        raise ValueError("JSONL_ACTIVE_ARCHIVE_OVERLAP")
    total = base + scanned["count"]
    if total < count_at_check or scanned["count"] < 1:
        raise ValueError("JSONL_LOG_ROLLBACK")
    if scanned["last"] < last_at_check:
        raise ValueError("JSONL_LOG_TIME_ROLLBACK")
    recent = scanned["recent"]
    events = []
    for raw in recent:
        row = json.loads(raw)
        stamp = _utc(row["utc"])
        state = row.get("state")
        if type(state) is not str or not re.fullmatch(r"[A-Z][A-Z0-9_]{0,47}", state):
            raise ValueError("JSONL_CYCLE_CODE_INVALID")
        events.append(dict(at=stamp.isoformat(), cycle=0, result=state, code=state))
    first_cycle = total - len(events) + 1
    for index, event in enumerate(events):
        event["cycle"] = first_cycle + index
    return events


def _windows_share_handle(path):
    if os.name != "nt":
        raise ValueError("JSONL_ROTATION_WINDOWS_ONLY")
    import ctypes
    from ctypes import wintypes
    create = ctypes.windll.kernel32.CreateFileW
    create.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD,
                       wintypes.LPVOID, wintypes.DWORD, wintypes.DWORD, wintypes.HANDLE]
    create.restype = wintypes.HANDLE
    handle = create(str(path), 0x80000000, 0x1 | 0x4, None, 3, 0x02000000, None)
    invalid = wintypes.HANDLE(-1).value
    if handle == invalid:
        raise OSError("JSONL_ROTATION_EXCLUSIVE_WRITER_DENIAL_FAILED")
    return handle


def rotate(active, robot=None):
    """Explicit atomic rename; readers may remain open, writers are excluded."""
    active = Path(active)
    stem = active.name.removesuffix(".jsonl")
    if stem not in STEMS or active.suffix != ".jsonl" or not _safe_file(active):
        raise ValueError("JSONL_ROTATION_SOURCE_INVALID")
    archive = active.parent / "archive"
    archive.mkdir(exist_ok=True)
    if archive.is_symlink() or not archive.is_dir():
        raise ValueError("JSONL_ARCHIVE_DIRECTORY_INVALID")
    handle = _windows_share_handle(active)
    renamed = False
    try:
        scanned = _scan(active, robot=robot)
        if scanned["count"] < 1:
            raise ValueError("JSONL_ROTATION_EMPTY")
        name = (f"{stem}-{_compact(scanned['first'])}-{_compact(scanned['last'])}-"
                f"{scanned['count']}-{scanned['sha256']}.jsonl")
        destination = archive / name
        if destination.exists():
            raise ValueError("JSONL_ROTATION_DESTINATION_EXISTS")
        os.rename(active, destination)
        renamed = True
        try:
            with active.open("xb") as stream:
                stream.flush()
                os.fsync(stream.fileno())
        except FileExistsError:
            # A worker may create the next active segment immediately after rename.
            pass
        return dict(archive=destination, count=scanned["count"],
                    sha256=scanned["sha256"], active=active)
    finally:
        import ctypes
        if not ctypes.windll.kernel32.CloseHandle(handle):
            raise OSError("JSONL_ROTATION_HANDLE_CLOSE_FAILED")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", type=Path)
    parser.add_argument("--robot", choices=("v20-shallow", "v20-obv", "v20-inside"))
    parser.add_argument("--verify-archives", action="store_true")
    args = parser.parse_args(argv)
    stem = args.path.name.removesuffix(".jsonl")
    if stem not in STEMS or args.path.suffix != ".jsonl":
        raise SystemExit("JSONL_SOURCE_NOT_ALLOWED")
    if args.verify_archives:
        rows = archives(args.path, stem, verify=True)
        print("JSONL_ARCHIVE_VERIFY=PASS segments=" + str(len(rows)))
        return 0
    result = rotate(args.path, robot=args.robot)
    print("JSONL_ROTATION=PASS count=" + str(result["count"]) +
          " sha256=" + result["sha256"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
