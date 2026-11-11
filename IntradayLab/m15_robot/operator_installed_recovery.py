"""The installed M15 durable journal's H1-style broker reconciliation cycle.

Unlike offline temp/preview checks, reads and recovers the physically installed
separate M15 SQLite under its existing Windows single-instance lock. Uses only
the authenticated M15 READONLY API. No new order, no H1 filesystem access,
no Task changes and NEVER a production/live-authorizing heartbeat.
"""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
from pathlib import Path
import re
import sys

from .execution_cycle import run_m15_readonly_recovery_once
from .finam_readonly import M15FinamReadOnlyAPI
from .finam_trading import M15_ORDER_POST_RELEASED
from .live_execution import M15OutboundJournal
from .spec import EXECUTION_STATUS
from .step23_install import ROOT, REPO, DB_NAME, H1_PATH_SENTINEL
from .step23_readonly_preflight import inspect_m15_halted_runtime
from .step15_broker_probe import _gui_credentials


class M15InstalledRecoveryError(RuntimeError):
    pass


def run_installed_recovery_once(
    *, api: M15FinamReadOnlyAPI, m15_account_id: str,
    h1_account_id: str, runtime_root: Path = ROOT,
    repository_root: Path = REPO,
) -> dict:
    if (EXECUTION_STATUS != "NOT_LIVE_AUTHORIZED"
            or M15_ORDER_POST_RELEASED is not False):
        raise M15InstalledRecoveryError("M15_INSTALLED_LIVE_FREEZE_REQUIRED")
    if (type(api) is not M15FinamReadOnlyAPI
            or api.readonly_bound is not True
            or api.account_id != m15_account_id
            or not isinstance(m15_account_id, str) or not m15_account_id
            or not isinstance(h1_account_id, str) or not h1_account_id
            or m15_account_id == h1_account_id
            or not isinstance(runtime_root, Path)
            or not runtime_root.is_absolute()
            or runtime_root.resolve() != ROOT.resolve()
            or not isinstance(repository_root, Path)
            or not repository_root.is_absolute()):
        raise M15InstalledRecoveryError("M15_INSTALLED_IDENTITY_INVALID")
    db = runtime_root / "state" / DB_NAME
    if (db.is_symlink() or db.parent.is_symlink() or not db.is_file()):
        raise M15InstalledRecoveryError("M15_INSTALLED_EXISTING_SQLITE_REQUIRED")
    halted = inspect_m15_halted_runtime(runtime_root)
    if (not halted["m15_runtime_halted"]
            or halted["production_switch_present"]
            or halted["production_heartbeat_present"]):
        raise M15InstalledRecoveryError("M15_INSTALLED_RUNTIME_NOT_HALTED")
    # The journal constructor checks the already persisted identity and
    # schema. It cannot silently reset/migrate existing real intents.
    journal = M15OutboundJournal(
        runtime_root=runtime_root, repository_root=repository_root,
        h1_runtime_root=H1_PATH_SENTINEL,
        m15_account_id=m15_account_id,
        h1_account_sha256=hashlib.sha256(
            h1_account_id.encode("utf-8")).hexdigest())
    try:
        report = run_m15_readonly_recovery_once(
            runtime_root=runtime_root, journal=journal, api=api,
            m15_account_id=m15_account_id,
            observed_at=datetime.now(timezone.utc),
        )
    finally:
        journal.close()
    if (report["status"] != "HALTED_READONLY_RECOVERY"
            or report["order_post_permitted"] is not False
            or report["live_authorized"] is not False):
        raise M15InstalledRecoveryError("M15_INSTALLED_RECOVERY_NOT_READONLY")
    return {
        "existing_journal_reconciled": True,
        "broker_positions": report["broker_position_count"],
        "durable_intents": report["intent_count"],
        "events": len(report["events"]),
        "readonly_heartbeat_written": True,
        "order_post_authorized": False,
        "live_authorized": False,
    }


def _safe(exc: Exception) -> str:
    if isinstance(exc, M15InstalledRecoveryError):
        code = str(exc)
        if len(code) < 100 and re.fullmatch(r"M15_[A-Z0-9_]+", code):
            return code
    return "M15_INSTALLED_RECOVERY_FAIL_CLOSED"


def main() -> int:
    print("m15_installed_journal_broker_recovery=readonly", flush=True)
    print("m15_no_order_no_task_no_h1_io=yes", flush=True)
    print("m15_live_authorized=no", flush=True)
    try:
        m15, h1, secret = _gui_credentials()
        api = M15FinamReadOnlyAPI(secret=secret, account_id=m15)
        del secret
        api.connect_readonly()
        result = run_installed_recovery_once(
            api=api, m15_account_id=m15, h1_account_id=h1)
        print("m15_existing_sqlite_finam_reconciliation=pass", flush=True)
        print("m15_readonly_worker_cycle=pass", flush=True)
        print("m15_production_heartbeat=not_created", flush=True)
        print("m15_live_authorized=no", flush=True)
        return 0
    except (KeyboardInterrupt, EOFError):
        print("m15_installed_worker=cancelled", flush=True)
        return 1
    except Exception as exc:
        print("m15_installed_worker_failure=" + _safe(exc), flush=True)
        print("m15_live_authorized=no", flush=True)
        return 1


if __name__ == "__main__":
    if sys.argv[1:]:
        print("m15_installed_worker=invalid_arguments", flush=True)
        sys.exit(1)
    sys.exit(main())
