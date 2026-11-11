"""Roadmap #23: install the ORIGINAL H1-style durable M15 intent journal.

This is a physical installation, not a simulated run: only after the existing
HALTED + exact M15 READONLY financial preflight sees FLAT account,
zero active orders, reconciled cashflow and N4 GO. Creates the isolated M15 SQLite once. Does NOT
send or cancel orders, arm a task, create production permission/heartbeat, or
read H1 files. M15 and H1 account identifiers remain local and never printed.
"""
from __future__ import annotations

import hashlib
from pathlib import Path
from datetime import datetime, timezone
import sys

from .finam_readonly import M15FinamReadOnlyAPI, M15FinamReadOnlyError
from .finam_trading import M15_ORDER_POST_RELEASED
from .live_execution import M15OutboundJournal
from .spec import EXECUTION_STATUS
from .step23_readonly_preflight import (
    verify_m15_step23_financial_preflight, safe_preflight_failure_code,
)

ROOT = Path("c:/intradaylab/runtime/m15")
REPO = Path(__file__).resolve().parents[2]
# A pure disjoint PATH REFERENCE: nothing is read from or written to H1.
H1_PATH_SENTINEL = Path("c:/h1-independent-account-reference-unused")
DB_NAME = "m15-production-outbound-intents.sqlite3"


class M15InstallError(RuntimeError):
    pass


def install_m15_journal_once(*, api: M15FinamReadOnlyAPI,
                             m15_account_id: str, h1_account_id: str,
                             runtime_root: Path = ROOT,
                             repository_root: Path = REPO) -> dict:
    """Creates exactly the M15 production journal; no trade authorization."""
    if EXECUTION_STATUS != "NOT_LIVE_AUTHORIZED" or M15_ORDER_POST_RELEASED is not False:
        raise M15InstallError("M15_INSTALL_LIVE_FREEZE_REQUIRED")
    if (not isinstance(m15_account_id, str) or not m15_account_id
            or not isinstance(h1_account_id, str) or not h1_account_id
            or m15_account_id == h1_account_id
            or len(m15_account_id) > 128 or len(h1_account_id) > 128):
        raise M15InstallError("M15_INSTALL_DISTINCT_ACCOUNT_REQUIRED")
    if (not isinstance(runtime_root, Path) or not runtime_root.is_absolute()
            or not isinstance(repository_root, Path)
            or not repository_root.is_absolute()
            or runtime_root.is_symlink()
            or runtime_root.resolve() != ROOT.resolve()
            or type(api) is not M15FinamReadOnlyAPI
            or api.account_id != m15_account_id
            or api.readonly_bound is not True):
        raise M15InstallError("M15_INSTALL_RUNTIME_OR_SESSION_INVALID")
    # H1-style installation needs proven broker/account/risk facts, NOT an
    # order-capable API token. The READONLY client has no order endpoint.
    # A separate trading JWT is rechecked at actual execution, not persisted.
    verify_m15_step23_financial_preflight(
        api=api, m15_account_id=m15_account_id,
        h1_account_id=h1_account_id, runtime_root=runtime_root,
        observed_at=datetime.now(timezone.utc))
    db_path = runtime_root / "state" / DB_NAME
    if (db_path.is_symlink() or db_path.parent.is_symlink()
            or db_path.exists()
            or any((runtime_root / "state" / (DB_NAME + suffix)).exists()
                   for suffix in ("-wal", "-shm", "-journal"))
            or (runtime_root / "safety" / "m15-execution-authorization.json").exists()
            or (runtime_root / "safety" / "m15-trading-kill-switch.json").exists()
            or (runtime_root / "diagnostics" / "m15-production-heartbeat.json").exists()):
        raise M15InstallError("M15_INSTALL_STATE_ALREADY_PRESENT")
    journal = M15OutboundJournal(
        runtime_root=runtime_root, repository_root=repository_root,
        h1_runtime_root=H1_PATH_SENTINEL,
        m15_account_id=m15_account_id,
        h1_account_sha256=hashlib.sha256(
            h1_account_id.encode("utf-8")).hexdigest())
    try:
        if (journal.db.execute("PRAGMA integrity_check").fetchone() != ("ok",)
                or journal.db.execute(
                    "SELECT COUNT(*) FROM outbound").fetchone() != (0,)
                or journal.db.execute(
                    "SELECT COUNT(*) FROM broker_flat").fetchone() != (0,)
                or journal.execution_authorized is not False):
            raise M15InstallError("M15_INSTALL_JOURNAL_NOT_EMPTY_OR_VALID")
    finally:
        journal.close()
    if not db_path.is_file() or db_path.is_symlink():
        raise M15InstallError("M15_INSTALL_SQLITE_NOT_CREATED")
    return {
        "m15_persistent_intent_sqlite": True,
        "schema_empty_and_integrity_pass": True,
        "h1_file_io": False,
        "order_post_count": 0,
        "production_authorized": False,
    }


def _gui() -> tuple[str, str, str]:
    """Only locally entered identifiers / masked READONLY key; never persisted."""
    import tkinter as tk
    root = tk.Tk()
    chosen = None
    try:
        root.title("IntradayLab M15 #23 - install isolated journal (NO TRADING)")
        root.geometry("710x255")
        root.resizable(False, False)
        tk.Label(root, text="Separate M15 journal installation. NO orders, Task or H1 file access.").pack(pady=8)
        tk.Label(root, text="M15 FINAM account").pack()
        m15 = tk.Entry(root, width=80)
        m15.pack()
        tk.Label(root, text="H1 FINAM account (local inequality check only)").pack()
        h1 = tk.Entry(root, width=80)
        h1.pack()
        tk.Label(root, text="M15 READONLY API secret (masked; no trading key needed)").pack()
        secret = tk.Entry(root, width=80, show="*")
        secret.pack()
        message = tk.Label(root, text="")
        message.pack()

        def submit():
            nonlocal chosen
            a, b, c = m15.get().strip(), h1.get().strip(), secret.get().strip()
            if not a or not b or not c:
                message.config(text="Fill the three fields; no values are logged.")
                return
            chosen = (a, b, c)
            root.quit()

        tk.Button(root, text="INSTALL M15 SQLITE (NO TRADING)", command=submit).pack(pady=8)
        root.protocol("WM_DELETE_WINDOW", root.quit)
        root.mainloop()
    finally:
        root.destroy()
    if chosen is None:
        raise M15InstallError("M15_INSTALL_OPERATOR_CANCELLED")
    return chosen


def _error_code(exc: Exception) -> str:
    if isinstance(exc, M15InstallError):
        code = str(exc)
        return code if code.startswith("M15_INSTALL_") and code.isascii() and code.replace("_","").isalnum() and len(code)<100 else "M15_INSTALL_FAILED"
    # Preserve only fixed local diagnostic codes: no account, secret or
    # broker payload can escape into PowerShell on a failed install.
    return safe_preflight_failure_code(exc)


def main() -> int:
    print("m15_step23_installer=separate_m15_durable_journal_only", flush=True)
    print("m15_no_order_no_task_no_h1_access=yes", flush=True)
    print("m15_live_authorized=no", flush=True)
    try:
        m15, h1, secret = _gui()
        api = M15FinamReadOnlyAPI(secret=secret, account_id=m15)
        del secret
        api.connect_readonly()
        install_m15_journal_once(
            api=api, m15_account_id=m15, h1_account_id=h1)
        print("m15_broker_readonly_capital_flat_n4_go=pass", flush=True)
        print("m15_production_intent_sqlite_installed=pass", flush=True)
        print("m15_order_post_authorized=no", flush=True)
        print("m15_live_authorized=no", flush=True)
        return 0
    except (EOFError, KeyboardInterrupt):
        print("m15_step23_install=cancelled", flush=True)
        return 1
    except Exception as exc:
        print("m15_step23_install_failure=" + _error_code(exc), flush=True)
        print("m15_live_authorized=no", flush=True)
        return 1


if __name__ == "__main__":
    if sys.argv[1:]:
        print("m15_step23_install=invalid_args", flush=True)
        sys.exit(1)
    sys.exit(main())
