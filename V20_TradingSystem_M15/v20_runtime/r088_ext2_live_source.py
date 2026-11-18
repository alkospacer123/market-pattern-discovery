"""R088 explicit account-bound EXT2 history wiring (not auto-installed).

Reuse the already accepted R070 rolling H1 StateStore/ZIP and the *second*
FINAM M15 GET that the frozen pre-intent gate performs. The source calendar
and per-account release authority are SHA-pinned separately. No FINAM request,
LIVE SQLite mutation, order, task control or token handling here.
"""
from __future__ import annotations

from datetime import date, datetime
from hashlib import sha256
import json
from pathlib import Path
import re

from .ext2_history_bridge import EXT2HistoryBlocked
from .h1_state_journal import _require_v20_root
from .r070_m15_candidate_state import (
    R070CandidateCheckpointState, make_r070_checkpoint_refresh,
)

COVERED = ("CNYRUBF", "GLDRUBF", "USDRUBF")
APPLIES = ("v20-shallow", "v20-obv")
_AUTH_SCHEMA = "v20.r088.ext2.account_release.v1"
_CALENDAR_SCHEMA = "v20.r088.moex_main_session_calendar.v1"


def _need(yes: bool, message: str) -> None:
    if not yes:
        raise EXT2HistoryBlocked(message)


def _read_exact_json(path: Path) -> dict:
    _need(path.is_file() and not path.is_symlink() and not path.parent.is_symlink(),
          "R088_EXT2_AUTH_OR_CALENDAR_MISSING_OR_LINK")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise EXT2HistoryBlocked("R088_EXT2_AUTH_OR_CALENDAR_UNREADABLE") from exc
    _need(isinstance(data, dict), "R088_EXT2_AUTH_OR_CALENDAR_NOT_OBJECT")
    return data


def _approved_days(*, root: Path, release: dict) -> tuple[date, ...]:
    file = root / "r070-candidate" / "r088-moex-calendar.json"
    raw = file.read_bytes() if (file.is_file() and not file.is_symlink()
                                and not file.parent.is_symlink()) else b""
    _need(raw and sha256(raw).hexdigest() == release["calendar_sha256"],
          "R088_EXT2_CALENDAR_SOURCE_SHA_UNVERIFIED")
    cal = _read_exact_json(file)
    _need(set(cal) == {"schema", "market", "source_url", "verified_open_days", "operator_verified"}
          and cal["schema"] == _CALENDAR_SCHEMA
          and cal["market"] == "MOEX_FORTS_MAIN_M15_1000_1745"
          and cal["source_url"] == "https://www.moex.com/n96571"
          and cal["operator_verified"] is True
          and isinstance(cal["verified_open_days"], list)
          and len(cal["verified_open_days"]) >= 3,
          "R088_EXT2_CALENDAR_NOT_INDEPENDENTLY_APPROVED")
    try:
        values = tuple(date.fromisoformat(text) for text in cal["verified_open_days"])
    except (TypeError, ValueError) as exc:
        raise EXT2HistoryBlocked("R088_EXT2_CALENDAR_DATES_INVALID") from exc
    _need(values == tuple(sorted(set(values))) and
          all(isinstance(value, date) for value in values),
          "R088_EXT2_CALENDAR_NOT_SORTED_UNIQUE")
    return values


def configure_r088_ext2_live_source(
    *, sender, root: Path, robot: str, account_id: str, source_commit: str,
) -> bool:
    """Bind explicitly approved source to the live sender; no implicit fallback.

    The existing R070 gate still performs exactly one fresh second FINAM GET,
    verifies its M15 Open, each checked OHLCV overlap, D ATR, and audit cursor.
    Missing USD/GLD history blocks release rather than silently disabling EXT2.
    All durable M15 writes stay under /r070-candidate, NEVER real trade SQLite.
    """
    if robot == "v20-inside":
        return False
    _need(robot in APPLIES and isinstance(account_id, str)
          and re.fullmatch(r"[A-Za-z0-9_.-]{1,128}", account_id) is not None
          and isinstance(source_commit, str)
          and re.fullmatch("[a-f0-9]{40}", source_commit) is not None,
          "R088_EXT2_RELEASE_IDENTITY_INVALID")
    root = _require_v20_root(root)
    if (getattr(sender, "source", None) != source_commit
            or getattr(sender, "r070_verified_history_provider", None) is not None
            or getattr(sender, "r070_verified_history_refresh", None) is not None):
        raise EXT2HistoryBlocked("R088_EXT2_TRANSPORT_SOURCE_UNTRUSTED")
    journal = getattr(sender, "journal", None)
    account_sha = sha256(account_id.encode("utf-8")).hexdigest()
    _need(getattr(journal, "robot_id", None) == robot
          and getattr(journal, "account_hash", None) == account_sha
          and getattr(journal, "live_runtime", False) is True
          and getattr(getattr(sender, "reader", None), "account_hash", None) == account_sha,
          "R088_EXT2_LIVE_JOURNAL_ACCOUNT_MISMATCH")
    path = root / "robots" / robot.removeprefix("v20-") / "safety" / "r088-ext2-release.json"
    release = _read_exact_json(path)
    _need(set(release) == {
        "schema", "source_commit", "robot_id", "account_sha256", "owner_approved",
        "symbols", "calendar_sha256"}
          and release.get("schema") == _AUTH_SCHEMA
          and release.get("source_commit") == source_commit
          and release.get("robot_id") == robot
          and release.get("account_sha256") == account_sha
          and release.get("owner_approved") is True
          and release.get("symbols") == list(COVERED)
          and isinstance(release.get("calendar_sha256"), str)
          and re.fullmatch(r"[a-f0-9]{64}", release["calendar_sha256"]),
          "R088_EXT2_RELEASE_NOT_ACCOUNT_APPROVED")
    days = _approved_days(root=root, release=release)
    # No uninitialized symbol may be used with a frozen new entry.
    with R070CandidateCheckpointState(
            v20_root=root, robot_id=robot, account_id=account_id) as state:
        for symbol in COVERED:
            cursor = state.verified_cursor(symbol)
            _need(isinstance(cursor, dict),
                  "R088_EXT2_NOT_ALL_N4_HISTORY_BOOTSTRAPPED")
            try:
                stamp = datetime.fromisoformat(cursor["last_open_msk"])
            except (KeyError, TypeError, ValueError) as exc:
                raise EXT2HistoryBlocked("R088_EXT2_CURSOR_INVALID") from exc
            _need(stamp.tzinfo is None, "R088_EXT2_CURSOR_INVALID")
    def refresh(*, robot: str, symbol: str, signal_open_msk: datetime,
                finam_recent, observed_at_msk: datetime):
        # Short exclusive lock only while advancing the isolated H1 store.
        with R070CandidateCheckpointState(
                v20_root=root, robot_id=robot, account_id=account_id) as state:
            provider = make_r070_checkpoint_refresh(
                candidate_state=state, independently_verified_open_days=days)
            return provider(
                robot=robot, symbol=symbol, signal_open_msk=signal_open_msk,
                finam_recent=finam_recent, observed_at_msk=observed_at_msk)
    sender.r070_verified_history_refresh = refresh
    return True
