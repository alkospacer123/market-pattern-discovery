"""R088: bind the already certified CNY M15 source to isolated R070 H1 SQLite.

Only the two physically checked Shallow/OBV accounts. NO API / LIVE journal /
Task / credential writes, orders, cancellations, or strategy changes.
Original 2026-11-18 FINAM report and existing checkpoint are authoritative.
"""
from __future__ import annotations

from datetime import datetime
from hashlib import sha256
import json
from pathlib import Path
import re

from .ext2_history_bridge import EXT2HistoryBlocked, m15_history_sha256
from .h1_state_journal import _require_v20_root
from .r070_m15_candidate_state import R070CandidateCheckpointState
from .r070_m15_checkpoint import load_r070_m15_checkpoint

ROBOT_IDS = frozenset(("v20-shallow", "v20-obv"))
SYMBOL = "CNYRUBF"
REPORT_DATE = "20261118"
ARCHIVE = "r070-cnyrubf-20261115-verified-offline.zip"
LAST_ARCHIVE_OPEN = datetime(2026, 11, 15, 17, 45)
MINIMUM_LIVE_PROOF = datetime(2026, 11, 18, 15, 30)
HISTORY_SHA256 = "6fcd14c5d473652d014e47577597d22512b97319ef73996aad04cbc38b9ff79c"


def _need(ok: bool, code: str) -> None:
    if not ok:
        raise EXT2HistoryBlocked(code)


def _check_physical_report(
    *, report_path: Path, archive_path: Path, robot: str, account_id: str,
) -> str:
    """Check all receipt identity, source and no-order fields before bootstrap."""
    for p in (report_path, archive_path):
        _need(p.is_file() and not p.is_symlink() and not p.parent.is_symlink(),
              "R088_CNY_PHYSICAL_RECEIPT_OR_ARCHIVE_NOT_TRUSTED")
    _need(isinstance(account_id, str) and re.fullmatch(r"[A-Za-z0-9_.-]{1,128}", account_id)
          is not None, "R088_CNY_ACCOUNT_INVALID")
    try:
        raw = report_path.read_bytes()
        report = json.loads(raw)
        at = datetime.fromisoformat(report["observed_at_utc"])
        witnessed = datetime.fromisoformat(report["last_completed_open_msk"])
    except (OSError, KeyError, ValueError, TypeError, UnicodeError) as exc:
        raise EXT2HistoryBlocked("R088_CNY_PHYSICAL_RECEIPT_INVALID") from exc
    account_sha = sha256(account_id.encode("utf-8")).hexdigest()
    expected_keys = {
        "schema": "r070.cny.finam_readonly_physical.v1",
        "status": "PASS_CNYRUBF_FRESH_M15_READONLY_NO_LIVE",
        "robot": robot,
        "account_sha256": account_sha,
        "checkpoint_history_sha256": HISTORY_SHA256,
        "source_r060_zip_sha256": "80291246ba4692485545f58fd28c7563199bf7be28033fc16eb296efee377e31",
        "source_terminal_csv_sha256": "f6ae045a074fea9be3f7c9b5ca47dfc7dedae4481f61e8a71fc60d16b502d4f2",
        "readonly_http_method": "FINAM GET /bars only plus session authentication",
    }
    _need(isinstance(report, dict)
          and all(report.get(key) == value for key, value in expected_keys.items())
          and report.get("overlap_verified", 0) >= 32
          and report.get("m15_missing") == 0
          and report.get("account_bound_sqlite") is False
          and report.get("live_authorized") is False
          and report.get("orders_sent") == 0
          and report.get("orders_cancelled") == 0
          and report.get("report_contains_token_or_account_id") is False
          and at.tzinfo is not None
          and at.date().isoformat() == "2026-11-18"
          and witnessed >= MINIMUM_LIVE_PROOF
          and bool(re.fullmatch(r"[a-f0-9]{64}", str(report.get("checkpoint_file_sha256", "")))),
          "R088_CNY_PHYSICAL_PROOF_OR_ACCOUNT_MISMATCH")
    check = sha256(archive_path.read_bytes()).hexdigest()
    _need(check == report["checkpoint_file_sha256"], "R088_CNY_PHYSICAL_ARCHIVE_SHA_MISMATCH")
    return check


def bootstrap_r088_verified_cny(
    *, root: Path, robot: str, account_id: str,
) -> dict:
    """One-time SHA-pinned, account-bound isolated bootstrap; restart is idempotent.

    A physical historical source report is NOT a LIVE authorization. The
    separately verified fresh FINAM M15 witness is still required per signal.
    """
    _need(robot in ROBOT_IDS, "R088_CNY_ROBOT_NOT_PHYSICALLY_APPROVED")
    root = _require_v20_root(root)
    evidence = root / "r070-candidate" / "m15"
    report_path = evidence / ("r070-cny-physical-" + robot + "-" + REPORT_DATE + ".json")
    archive_path = evidence / ARCHIVE
    digest = _check_physical_report(
        report_path=report_path, archive_path=archive_path,
        robot=robot, account_id=account_id)
    history, history_sha = load_r070_m15_checkpoint(
        path=archive_path, symbol=SYMBOL,
        expected_checkpoint_sha256=digest,
        minimum_last_m15_open_msk=LAST_ARCHIVE_OPEN)
    _need(history_sha == HISTORY_SHA256
          and m15_history_sha256(history) == history_sha
          and history.Datetime.iloc[-1].to_pydatetime() == LAST_ARCHIVE_OPEN,
          "R088_CNY_ARCHIVE_CONTENT_NOT_VERIFIED")
    with R070CandidateCheckpointState(
            v20_root=root, robot_id=robot, account_id=account_id) as state:
        existing = state.verified_cursor(SYMBOL)
        if existing is None:
            row = state.bootstrap(
                symbol=SYMBOL, verified_history=history,
                expected_history_sha256=history_sha)
            status = "PASS_ACCOUNT_BOUND_CNY_BOOTSTRAPPED"
        else:
            # Never reset a rolled-forward cursor, but verify its pinned ZIP.
            saved_at = datetime.fromisoformat(existing["last_open_msk"])
            _need(saved_at >= LAST_ARCHIVE_OPEN, "R088_CNY_CHECKPOINT_CURSOR_BACKWARDS")
            if saved_at == LAST_ARCHIVE_OPEN:
                state.provide_ext2_history(
                    robot=robot, symbol=SYMBOL, signal_open_msk=LAST_ARCHIVE_OPEN)
                _need(existing["history_sha256"] == history_sha,
                      "R088_CNY_ALREADY_BOUND_DIFFERENT_SEED")
            else:
                from .r070_m15_checkpoint import load_r070_m15_checkpoint
                last, sha = load_r070_m15_checkpoint(
                    path=state.archive_dir / existing["filename"], symbol=SYMBOL,
                    expected_checkpoint_sha256=existing["checkpoint_sha256"],
                    minimum_last_m15_open_msk=saved_at)
                _need(sha == existing["history_sha256"] and len(last) >= len(history),
                      "R088_CNY_ROLLED_FORWARD_SOURCE_UNVERIFIED")
            row = existing
            status = "PASS_ACCOUNT_BOUND_CNY_ALREADY_PRESENT"
    return {
        "status": status, "robot": robot,
        "account_sha256": sha256(account_id.encode("utf-8")).hexdigest(),
        "source_history_sha256": history_sha,
        "cursor_msk": row["last_open_msk"], "generation": row["generation"],
        "live_installed": False, "orders_sent": 0, "finam_requests": 0,
    }
