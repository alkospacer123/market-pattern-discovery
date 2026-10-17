"""Isolated account/runtime guards. Structural NO-ORDER boundary at this stage."""
from __future__ import annotations

import hashlib
from pathlib import Path

from .spec import EXECUTION_STATUS, ROBOT_ID


class M15NotAuthorized(RuntimeError):
    pass


def account_fingerprint(account_id: str) -> str:
    if not isinstance(account_id, str) or not account_id.strip() or account_id != account_id.strip():
        raise ValueError("M15_ACCOUNT_ID_REQUIRED")
    return hashlib.sha256(account_id.encode("utf-8")).hexdigest()


def validate_independent_binding(
    *, m15_account_id: str, h1_account_sha256: str, m15_runtime_root: Path,
    h1_runtime_root: Path, repository_root: Path,
) -> str:
    """Require proof of a distinct account and disjoint external runtime root."""
    fp = account_fingerprint(m15_account_id)
    if not isinstance(h1_account_sha256, str) or len(h1_account_sha256) != 64:
        raise ValueError("H1_ACCOUNT_FINGERPRINT_REQUIRED")
    try:
        int(h1_account_sha256, 16)
    except ValueError:
        raise ValueError("H1_ACCOUNT_FINGERPRINT_INVALID") from None
    if fp == h1_account_sha256.lower():
        raise ValueError("H1_ACCOUNT_REUSE_PROHIBITED")
    if not all(isinstance(x, Path) and x.is_absolute() for x in
               (m15_runtime_root, h1_runtime_root, repository_root)):
        raise ValueError("RUNTIME_ABSOLUTE_PATH_REQUIRED")
    m15 = m15_runtime_root.resolve()
    h1 = h1_runtime_root.resolve()
    repo = repository_root.resolve()
    if m15 == h1 or m15 in h1.parents or h1 in m15.parents:
        raise ValueError("M15_H1_RUNTIME_OVERLAP")
    if m15 == repo or repo in m15.parents or m15 in repo.parents:
        raise ValueError("M15_RUNTIME_INSIDE_REPOSITORY")
    if "tradingsystemlab" in tuple(part.lower() for part in m15.parts):
        raise ValueError("M15_RUNTIME_H1_TREE_FORBIDDEN")
    return fp


def prohibit_real_order(*args, **kwargs):
    """No FINAM transport, task change, credential, POST or re-arm exists here."""
    raise M15NotAuthorized(f"{ROBOT_ID}:{EXECUTION_STATUS}:REAL_ORDER_PROHIBITED")
