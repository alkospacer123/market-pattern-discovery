"""R070 candidate-only M15 reboot checkpoint. No FINAM access or LIVE writes.

One atomic ZIP file; externally pinned SHA, historic source pins and a
fresh independently certified FINAM M15 overlap are all mandatory for
resumption. Checkpoint bytes alone do NOT prove exchange market history.
"""
from __future__ import annotations

from datetime import date, datetime
from hashlib import sha256
from io import BytesIO
import json
import os
from pathlib import Path
import tempfile
from zipfile import ZIP_DEFLATED, ZipFile, BadZipFile

import pandas as pd

from .ext2_history_bridge import (
    EXT2HistoryBlocked, R060_SEED_SHA256, _strict_m15,
    advance_verified_m15, canonical_m15_csv_bytes, m15_history_sha256,
)

SCHEMA = "v20.r070.m15_candidate_checkpoint.v1"
PINNED_TERMINAL_SHA256 = {
    "USDRUBF": "dde2e7f5dbc0461d2fc8fcbb451fac713488411cce7199f2c3eb7dd336a84f5c",
    "CNYRUBF": "f6ae045a074fea9be3f7c9b5ca47dfc7dedae4481f61e8a71fc60d16b502d4f2",
    "GLDRUBF": "b1c4546aa7c00d3cfbe2b5a8fa88b57c1c46699003aac87a5413fbf8d1fc1a97",
    "IMOEXF": "01ea8d223e44f53709a46ac9b103b9e02dffb87a16e380e3453da07fdec1173c",
}


def _candidate_path(path: str | Path) -> Path:
    p = Path(path).absolute()
    if (p.suffix.lower() != ".zip" or not p.parent.is_dir()
            or p.is_symlink() or p.parent.is_symlink()):
        raise EXT2HistoryBlocked("R070_CHECKPOINT_PATH_INVALID")
    return p


def _check_sha(value: str, code: str) -> str:
    if (not isinstance(value, str) or len(value) != 64
            or any(c not in "0123456789abcdef" for c in value.lower())):
        raise EXT2HistoryBlocked(code)
    return value.lower()


def save_r070_m15_checkpoint(
    *, path: str | Path, symbol: str, verified_history: pd.DataFrame,
    expected_history_sha256: str, previous_checkpoint_sha256: str | None = None,
) -> str:
    """Persist only a caller-proven M15 frame, never an unverified broker GET.

    The caller must originally validate R060 and FINAM source *file bytes*
    with their official pinned loaders and certified session calendar.
    Overwrite requires the exact previous checkpoint SHA (one writer assumed).
    Return SHA of the entire committed ZIP for separate durable pinning.
    """
    if symbol not in R060_SEED_SHA256 or symbol not in PINNED_TERMINAL_SHA256:
        raise EXT2HistoryBlocked("R070_CHECKPOINT_SYMBOL_INVALID")
    p = _candidate_path(path)
    existing = p.exists()
    if existing:
        if (previous_checkpoint_sha256 is None or
                sha256(p.read_bytes()).hexdigest() !=
                _check_sha(previous_checkpoint_sha256, "R070_CHECKPOINT_PREVIOUS_SHA_INVALID")):
            raise EXT2HistoryBlocked("R070_CHECKPOINT_OVERWRITE_UNVERIFIED")
    elif previous_checkpoint_sha256 is not None:
        raise EXT2HistoryBlocked("R070_CHECKPOINT_PREVIOUS_MISSING")
    history = _strict_m15(verified_history)
    expected = _check_sha(expected_history_sha256, "R070_HISTORY_DIGEST_REQUIRED")
    if m15_history_sha256(history) != expected:
        raise EXT2HistoryBlocked("R070_HISTORY_DIGEST_MISMATCH")
    raw = canonical_m15_csv_bytes(history)
    manifest = {
        "schema": SCHEMA, "symbol": symbol, "history_sha256": expected,
        "rows": len(history),
        "latest_m15_open_msk": history.Datetime.iloc[-1].isoformat(),
        "source_r060_csv_sha256": R060_SEED_SHA256[symbol],
        "source_finam_terminal_csv_sha256": PINNED_TERMINAL_SHA256[symbol],
        "csv_sha256": sha256(raw).hexdigest(),
    }
    descriptor, temp = tempfile.mkstemp(prefix=".r070-m15-", suffix=".zip", dir=p.parent)
    try:
        with os.fdopen(descriptor, "wb") as dest:
            with ZipFile(dest, "w", compression=ZIP_DEFLATED) as z:
                z.writestr("manifest.json", json.dumps(manifest, sort_keys=True, separators=(",", ":")))
                z.writestr("history.csv", raw)
            dest.flush()
            os.fsync(dest.fileno())
        # No second writer is permitted; the caller must retain the digest
        # outside this archive. Replace only after ZIP is fully closed.
        digest = sha256(Path(temp).read_bytes()).hexdigest()
        os.replace(temp, p)
        return digest
    finally:
        if os.path.exists(temp):
            os.unlink(temp)


def load_r070_m15_checkpoint(
    *, path: str | Path, symbol: str, expected_checkpoint_sha256: str,
    minimum_last_m15_open_msk: datetime,
) -> tuple[pd.DataFrame, str]:
    """Read one exact SHA-pinned snapshot; never trust its stored calendar.

    The caller must subsequently call resume_r070_m15_checkpoint() using a
    NEW broker GET and an independently proved exchange-session calendar.
    A local snapshot by itself never grants an EXT2 trade permission.
    """
    if symbol not in R060_SEED_SHA256 or symbol not in PINNED_TERMINAL_SHA256:
        raise EXT2HistoryBlocked("R070_CHECKPOINT_SYMBOL_INVALID")
    p = _candidate_path(path)
    if not p.is_file():
        raise EXT2HistoryBlocked("R070_CHECKPOINT_MISSING")
    check = _check_sha(expected_checkpoint_sha256, "R070_CHECKPOINT_SHA_REQUIRED")
    file_bytes = p.read_bytes()
    if sha256(file_bytes).hexdigest() != check:
        raise EXT2HistoryBlocked("R070_CHECKPOINT_SHA_MISMATCH")
    if (not isinstance(minimum_last_m15_open_msk, datetime)
            or minimum_last_m15_open_msk.tzinfo is not None):
        raise EXT2HistoryBlocked("R070_CHECKPOINT_DURABLE_CURSOR_REQUIRED")
    try:
        with ZipFile(BytesIO(file_bytes), "r") as z:
            if z.namelist() != ["manifest.json", "history.csv"]:
                raise ValueError("unexpected archive members")
            meta = json.loads(z.read("manifest.json"))
            data = z.read("history.csv")
        expected_keys = {
            "schema", "symbol", "history_sha256", "rows",
            "latest_m15_open_msk", "source_r060_csv_sha256",
            "source_finam_terminal_csv_sha256", "csv_sha256",
        }
        if (not isinstance(meta, dict) or set(meta) != expected_keys
                or meta["schema"] != SCHEMA or meta["symbol"] != symbol
                or meta["source_r060_csv_sha256"] != R060_SEED_SHA256[symbol]
                or meta["source_finam_terminal_csv_sha256"] != PINNED_TERMINAL_SHA256[symbol]
                or sha256(data).hexdigest() != meta["csv_sha256"]):
            raise ValueError("checkpoint manifest does not match pinned source")
        frame = pd.read_csv(
            BytesIO(data), parse_dates=["Datetime"],
            float_precision="round_trip",
        )
        history = _strict_m15(frame)
        last = history.Datetime.iloc[-1].to_pydatetime()
        if (len(history) != meta["rows"]
                or history.Datetime.iloc[-1].isoformat() != meta["latest_m15_open_msk"]
                or last < minimum_last_m15_open_msk
                or m15_history_sha256(history) != meta["history_sha256"]):
            raise ValueError("checkpoint row count, cursor or digest invalid")
        return history, meta["history_sha256"]
    except (BadZipFile, ValueError, TypeError, KeyError, OverflowError,
            UnicodeError, pd.errors.ParserError) as exc:
        raise EXT2HistoryBlocked("R070_CHECKPOINT_CONTENT_INVALID") from exc


def resume_r070_m15_checkpoint(
    *, path: str | Path, symbol: str, expected_checkpoint_sha256: str,
    minimum_last_m15_open_msk: datetime, finam_recent: pd.DataFrame,
    signal_open_msk: datetime, observed_at_msk: datetime,
    independently_verified_open_days: tuple[date, ...],
) -> tuple[pd.DataFrame, str]:
    """After restart, prove fresh overlap and every recent exchange session.

    This makes NO FINAM requests: the candidate caller must supply a new
    observed, completed FINAM M15 window. Missing source or gap blocks entry.
    The result is an in-memory frame only; save explicitly after confirmation.
    """
    cached, digest = load_r070_m15_checkpoint(
        path=path, symbol=symbol,
        expected_checkpoint_sha256=expected_checkpoint_sha256,
        minimum_last_m15_open_msk=minimum_last_m15_open_msk,
    )
    return advance_verified_m15(
        verified_prefix=cached, prefix_sha256=digest,
        finam_recent=finam_recent, signal_open_msk=signal_open_msk,
        observed_at_msk=observed_at_msk,
        verified_open_days=independently_verified_open_days,
    )
