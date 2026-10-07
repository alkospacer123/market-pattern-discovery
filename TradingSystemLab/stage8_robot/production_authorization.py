"""Durable Stage 8.12.4 production authorization authority.

The authorization record is intentionally external to the repository.  It is
bound to the exact production commit, frozen Stage 7 identity, sanitized real
account hash, and the accepted Stage 8.12.2 / Stage 8.12.3 evidence hashes.

Creating this record is a separate operator action.  Importing this module,
possessing the trading credential, or having a valid preflight report never
creates or implies authorization.
"""
from __future__ import annotations

import json
import os
import re
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .specification import ACTIVE_IDENTITY, PRODUCTION_SPECIFICATION_ID

AUTHORIZATION_SCHEMA = "stage8_12_4_production_authorization.v1"
AUTHORIZATION_FILENAME = "stage8-12-4-production-authorization.json"
OPERATOR_AUTHORIZATION_PHRASE = "AUTHORIZE_STAGE8_12_4_FULL_R15_PRODUCTION"
STAGE8_12_2_EVIDENCE_SHA256 = "4F58595E2F62F2A377E5525972B9E88A136B2F9BC51760268D012AF94A70AE9F"
STAGE8_12_3_EVIDENCE_SHA256 = "9584F45186DE38ABAE9209E1F326255C783AF762CD736EA45718D19C93BC61B1"
REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
_HEX40 = re.compile(r"^[0-9a-f]{40}$")
_HEX64 = re.compile(r"^[0-9A-Fa-f]{64}$")


class ProductionAuthorizationError(RuntimeError):
    pass


def _outside_repository(path: Path) -> Path:
    resolved = path.resolve()
    if resolved == REPOSITORY_ROOT or REPOSITORY_ROOT in resolved.parents:
        raise ProductionAuthorizationError("STAGE8_12_4_REPOSITORY_AUTHORIZATION_FORBIDDEN")
    return resolved


def authorization_path(runtime_root: Path | str) -> Path:
    return _outside_repository(Path(runtime_root)) / "safety" / AUTHORIZATION_FILENAME


def _validated_identity(*, accepted_commit: str, account_hash: str) -> tuple[str, str]:
    commit = str(accepted_commit).strip().lower()
    account = str(account_hash).strip().lower()
    if not _HEX40.fullmatch(commit):
        raise ProductionAuthorizationError("STAGE8_12_4_ACCEPTED_COMMIT_INVALID")
    if not _HEX64.fullmatch(account):
        raise ProductionAuthorizationError("STAGE8_12_4_ACCOUNT_HASH_INVALID")
    return commit, account


def _record(*, accepted_commit: str, account_hash: str, observed: datetime) -> dict[str, Any]:
    commit, account = _validated_identity(
        accepted_commit=accepted_commit, account_hash=account_hash
    )
    if observed.tzinfo is None or observed.utcoffset() is None:
        raise ProductionAuthorizationError("STAGE8_12_4_TIMESTAMP_INVALID")
    return {
        "schema_id": AUTHORIZATION_SCHEMA,
        "status": "AUTHORIZED",
        "production_specification_id": PRODUCTION_SPECIFICATION_ID,
        "active_identity": ACTIVE_IDENTITY,
        "accepted_code_commit": commit,
        "sanitized_account_hash": account,
        "stage8_12_2_external_evidence_sha256": STAGE8_12_2_EVIDENCE_SHA256,
        "stage8_12_3_external_evidence_sha256": STAGE8_12_3_EVIDENCE_SHA256,
        "execution_authorized": True,
        "authorized_utc": observed.astimezone(timezone.utc).isoformat(),
    }


def write_authorization(
    runtime_root: Path | str,
    *,
    accepted_commit: str,
    account_hash: str,
    operator_authorization_phrase: str,
    now: datetime | None = None,
) -> dict[str, Any]:
    """Create the exact authorization once; never overwrite or broaden it."""
    if operator_authorization_phrase != OPERATOR_AUTHORIZATION_PHRASE:
        raise ProductionAuthorizationError("STAGE8_12_4_EXPLICIT_OPERATOR_AUTHORIZATION_REQUIRED")
    observed = now or datetime.now(timezone.utc)
    value = _record(
        accepted_commit=accepted_commit,
        account_hash=account_hash,
        observed=observed,
    )
    destination = authorization_path(runtime_root)
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        try:
            existing = json.loads(destination.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError):
            raise ProductionAuthorizationError("STAGE8_12_4_EXISTING_AUTHORIZATION_INVALID") from None
        if existing == value:
            return existing
        raise ProductionAuthorizationError("STAGE8_12_4_AUTHORIZATION_ALREADY_EXISTS")

    descriptor, temporary = tempfile.mkstemp(
        prefix=f".{AUTHORIZATION_FILENAME}.", suffix=".tmp", dir=destination.parent
    )
    try:
        with os.fdopen(descriptor, "x", encoding="utf-8", newline="\n") as stream:
            json.dump(value, stream, sort_keys=True, separators=(",", ":"))
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, destination)
        try:
            directory_fd = os.open(destination.parent, os.O_RDONLY)
            try:
                os.fsync(directory_fd)
            finally:
                os.close(directory_fd)
        except OSError:
            pass
    finally:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass
    return value


def load_authorization(
    runtime_root: Path | str,
    *,
    expected_commit: str,
    expected_account_hash: str,
) -> dict[str, Any]:
    """Load and fail closed unless every durable authority binding is exact."""
    commit, account = _validated_identity(
        accepted_commit=expected_commit, account_hash=expected_account_hash
    )
    path = authorization_path(runtime_root)
    if not path.is_file() or path.is_symlink():
        raise ProductionAuthorizationError("STAGE8_12_4_AUTHORIZATION_MISSING")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        raise ProductionAuthorizationError("STAGE8_12_4_AUTHORIZATION_INVALID") from None
    expected = {
        "schema_id": AUTHORIZATION_SCHEMA,
        "status": "AUTHORIZED",
        "production_specification_id": PRODUCTION_SPECIFICATION_ID,
        "active_identity": ACTIVE_IDENTITY,
        "accepted_code_commit": commit,
        "sanitized_account_hash": account,
        "stage8_12_2_external_evidence_sha256": STAGE8_12_2_EVIDENCE_SHA256,
        "stage8_12_3_external_evidence_sha256": STAGE8_12_3_EVIDENCE_SHA256,
        "execution_authorized": True,
    }
    if not isinstance(value, dict) or any(value.get(k) != v for k, v in expected.items()):
        raise ProductionAuthorizationError("STAGE8_12_4_AUTHORIZATION_BINDING_MISMATCH")
    authorized = value.get("authorized_utc")
    if not isinstance(authorized, str):
        raise ProductionAuthorizationError("STAGE8_12_4_AUTHORIZATION_TIMESTAMP_INVALID")
    try:
        stamp = datetime.fromisoformat(authorized.replace("Z", "+00:00"))
    except ValueError:
        raise ProductionAuthorizationError("STAGE8_12_4_AUTHORIZATION_TIMESTAMP_INVALID") from None
    if stamp.tzinfo is None or stamp.utcoffset() is None:
        raise ProductionAuthorizationError("STAGE8_12_4_AUTHORIZATION_TIMESTAMP_INVALID")
    return value
