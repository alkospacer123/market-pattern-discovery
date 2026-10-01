"""Byte-exact authority hashing with narrowly scoped text EOL canonicalization."""
from __future__ import annotations

import hashlib
from pathlib import Path


CANONICAL_TEXT_SUFFIXES = frozenset({".py", ".json", ".csv", ".md"})


def canonical_authority_sha256(path: Path) -> str:
    """Hash authority files, treating CRLF as LF only for known UTF-8 text.

    Unsupported suffixes retain raw-byte hashing.  Known text must be valid UTF-8
    and may contain LF or CRLF, but never an unpaired carriage return.
    """
    raw = path.read_bytes()
    if path.suffix.lower() not in CANONICAL_TEXT_SUFFIXES:
        return hashlib.sha256(raw).hexdigest()
    raw.decode("utf-8")  # Authentication fails rather than guessing an encoding.
    without_crlf = raw.replace(b"\r\n", b"\n")
    if b"\r" in without_crlf:
        raise ValueError(f"AUTHORITY_TEXT_LONE_CR:{path}")
    return hashlib.sha256(without_crlf).hexdigest()
