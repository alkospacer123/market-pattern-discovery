"""Bounded descriptor-relative read. No writes, DB, shell, network or secrets.

POSIX uses directory descriptors; Windows uses pinned no-reparse NTFS handles.
Windows native/ACL physical acceptance remains NOT_VERIFIED until run on Windows.
"""
import os
from pathlib import Path
import stat
from .windows_file import read_windows


def fingerprint(info):
    return (info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns, info.st_ctime_ns)


def _directory(root):
    # Open every ancestor without following symlinks, including the configured root.
    if not root.is_absolute() or any(part in ("..", ".") for part in root.parts):
        raise ValueError("PATH_INVALID")
    if not hasattr(os, "O_NOFOLLOW") or os.open not in os.supports_dir_fd:
        raise ValueError("SECURE_READ_UNAVAILABLE")
    flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
    descriptor = os.open(root.anchor, flags)
    try:
        for part in root.parts[1:]:
            child = os.open(part, flags, dir_fd=descriptor)
            os.close(descriptor)
            descriptor = child
        return descriptor
    except BaseException:
        os.close(descriptor)
        raise


def read_snapshot(root: Path, filename: str, maximum: int) -> bytes:
    if filename != "h1.snapshot.json":
        raise ValueError("FILE_NOT_ALLOWED")
    return _read_file(root, filename, maximum)


def read_source(root, filename, expected_root):
    if os.name != "nt" or filename not in {"stage8-12-4-production-heartbeat.json", "stage8-trading-kill-switch.json"}:
        raise ValueError("SOURCE_NOT_ALLOWED")
    if len(expected_root) != 3 or any(type(x) is not int or x < 0 for x in expected_root):
        raise ValueError("ROOT_PIN_REQUIRED")
    return read_windows(root, filename, 128 * 1024, expected_root)


def _read_file(root, filename, maximum):
    if type(maximum) is not int or not 0 < maximum <= 128 * 1024:
        raise ValueError("SIZE_LIMIT_INVALID")
    if os.name == "nt":
        return read_windows(root, filename, maximum)
    directory = _directory(root)
    try:
        descriptor = os.open(filename, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=directory)
        try:
            before = os.fstat(descriptor)
            if not stat.S_ISREG(before.st_mode) or before.st_nlink != 1 or not 0 < before.st_size <= maximum:
                raise ValueError("FILE_INVALID")
            chunks, size = [], 0
            while size <= maximum:
                chunk = os.read(descriptor, min(16384, maximum + 1 - size))
                if not chunk:
                    break
                chunks.append(chunk)
                size += len(chunk)
            after = os.fstat(descriptor)
            current = os.stat(filename, dir_fd=directory, follow_symlinks=False)
            check_directory = _directory(root)
            try:
                if (fingerprint(before) != fingerprint(after) or fingerprint(after) != fingerprint(current)
                        or size != before.st_size or size > maximum
                        or (os.fstat(directory).st_dev, os.fstat(directory).st_ino)
                        != (os.fstat(check_directory).st_dev, os.fstat(check_directory).st_ino)):
                    raise ValueError("FILE_CHANGED")
            finally:
                os.close(check_directory)
            return b"".join(chunks)
        finally:
            os.close(descriptor)
    finally:
        os.close(directory)
