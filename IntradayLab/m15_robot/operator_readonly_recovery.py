"""One physical FINAM READONLY smoke test of the M15 outbound recovery cycle.

No LIVE, Task, H1 access, trading client, order POST/DELETE or persistent
production intent mutation. Fresh temporary journal only; FINAM broker
position/order GETs must be FLAT and clean. This does NOT simulate a fill.
"""
from __future__ import annotations

from datetime import datetime, timezone
import getpass
import hashlib
from pathlib import Path
import sys
from tempfile import TemporaryDirectory

from .execution_cycle import run_m15_readonly_recovery_once
from .finam_readonly import M15FinamReadOnlyAPI
from .live_execution import M15OutboundJournal
from .spec import EXECUTION_STATUS


class M15PhysicalSmokeError(RuntimeError):
    pass


def run_physical_readonly_smoke(
    *, m15_account_id: str, h1_account_id: str, readonly_secret: str,
) -> dict:
    """Two independent GET-based polls across SQLite close/reopen.

    Use user-supplied account IDs only for local inequality check. The H1
    sentinel is deliberately not a production H1 path; there is no H1 IO.
    The temp SQLite, lock and heartbeat are erased on return.
    """
    if EXECUTION_STATUS != "NOT_LIVE_AUTHORIZED":
        raise M15PhysicalSmokeError("M15_PHYSICAL_STATIC_LIVE_FREEZE_REQUIRED")
    if (not isinstance(m15_account_id, str) or not m15_account_id
            or not isinstance(h1_account_id, str) or not h1_account_id
            or m15_account_id == h1_account_id
            or len(m15_account_id) > 128 or len(h1_account_id) > 128
            or not isinstance(readonly_secret, str) or not readonly_secret):
        raise M15PhysicalSmokeError("M15_PHYSICAL_DISTINCT_ACCOUNT_OR_TOKEN_REQUIRED")
    api = M15FinamReadOnlyAPI(secret=readonly_secret, account_id=m15_account_id)
    api.connect_readonly()
    if api.readonly_bound is not True:
        raise M15PhysicalSmokeError("M15_PHYSICAL_READONLY_NOT_BOUND")
    root = Path(__file__).resolve().parents[2]
    with TemporaryDirectory(prefix="intraday_m15_readonly_") as tempdir:
        folder = Path(tempdir).resolve()
        kw = dict(
            runtime_root=folder / "m15-runtime",
            h1_runtime_root=folder / "foreign-h1-sentinel-never-used",
            repository_root=root,
            m15_account_id=m15_account_id,
            h1_account_sha256=hashlib.sha256(h1_account_id.encode()).hexdigest(),
        )
        journal = M15OutboundJournal(**kw)
        try:
            one = run_m15_readonly_recovery_once(
                runtime_root=kw["runtime_root"], journal=journal,
                api=api, m15_account_id=m15_account_id,
                observed_at=datetime.now(timezone.utc),
            )
        finally:
            journal.close()
        journal = M15OutboundJournal(**kw)
        try:
            two = run_m15_readonly_recovery_once(
                runtime_root=kw["runtime_root"], journal=journal,
                api=api, m15_account_id=m15_account_id,
                observed_at=datetime.now(timezone.utc),
            )
        finally:
            journal.close()
        if (one != two or one.get("status") != "HALTED_READONLY_RECOVERY"
                or one.get("intent_count") != 0
                or one.get("broker_position_count") != 0
                or one.get("events") != []
                or one.get("order_post_permitted") is not False
                or one.get("live_authorized") is not False):
            raise M15PhysicalSmokeError("M15_PHYSICAL_BROKER_NOT_CLEAN_OR_RESTART_DIVERGED")
        # All credentials, account IDs and transient journal contents stay
        # in memory or are erased with this TemporaryDirectory.
        return {
            "status": "PASS_EMPTY_ACCOUNT_READONLY_RESTART",
            "broker_get_cycles": 2,
            "broker_positions": 0,
            "journal_intents": 0,
            "order_post_permitted": False,
            "live_authorized": False,
        }


def main(*, gui: bool = False) -> int:
    print("m15_physical_readonly_only=yes", flush=True)
    print("m15_live_authorized=no", flush=True)
    try:
        if gui:
            from .step15_broker_probe import _gui_credentials
            m15, h1, token = _gui_credentials()
        else:
            m15 = getpass.getpass("m15 account id (hidden): ").strip()
            h1 = getpass.getpass("h1 account id for comparison only (hidden): ").strip()
            token = getpass.getpass("m15 readonly token (hidden): ").strip()
        result = run_physical_readonly_smoke(
            m15_account_id=m15, h1_account_id=h1,
            readonly_secret=token)
        del token
        print("m15_physical_readonly_smoke=pass", flush=True)
        print("m15_broker_get_cycles=2", flush=True)
        print("m15_sqlite_restart=pass", flush=True)
        print("m15_broker_flat_and_no_active_orders=pass", flush=True)
        print("m15_live_authorized=no", flush=True)
        return 0
    except (KeyboardInterrupt, EOFError):
        print("m15_physical_readonly_smoke=operator_cancelled", flush=True)
        return 1
    except Exception:
        # No raw exception: library/HTTP exceptions may contain credentials
        # or account identifiers. This signal is diagnostic, not authority.
        print("m15_physical_readonly_smoke=fail_closed", flush=True)
        print("m15_live_authorized=no", flush=True)
        return 1


if __name__ == "__main__":
    if sys.argv[1:] not in ([], ["--gui"]):
        print("m15_physical_readonly_smoke=invalid_mode")
        sys.exit(1)
    sys.exit(main(gui=sys.argv[1:] == ["--gui"]))
