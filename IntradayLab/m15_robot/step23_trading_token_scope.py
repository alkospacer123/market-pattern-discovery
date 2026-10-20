"""Step #23 preflight: exact one-account FINAM TRADING token scope, auth only.

Uses M15's existing strictly non-order-capable READONLY transport for ONLY
two FINAM session-auth POST endpoints. Deliberately does not call connect_readonly
(which rejects trading tokens). No account GET, order POST, cancel, Task, H1 IO,
SQLite writes, runtime arming, or LIVE release. A successful token scope check
is NOT an authorization to send any order.
"""
from __future__ import annotations

import re
import sys

from .finam_readonly import M15FinamReadOnlyAPI, M15FinamReadOnlyError
from .finam_trading import M15_ORDER_POST_RELEASED
from .spec import EXECUTION_STATUS


class M15TradingScopeError(RuntimeError):
    pass


def verify_m15_trading_token_scope(*, m15_account_id: str, secret: str) -> dict:
    if (EXECUTION_STATUS != "NOT_LIVE_AUTHORIZED"
            or M15_ORDER_POST_RELEASED is not False):
        raise M15TradingScopeError("M15_STEP23_TRADE_SCOPE_STATIC_FREEZE_REQUIRED")
    # Instantiate ONLY the structurally no-order FINAM reader. It can
    # authenticate but cannot execute order submission/cancellation.
    api = M15FinamReadOnlyAPI(
        secret=secret, account_id=m15_account_id, timeout=10,
    )
    auth = api._request("POST", "/v1/sessions", {"secret": secret})
    if (not isinstance(auth, dict)
            or not isinstance(auth.get("token"), str)
            or not auth["token"]):
        raise M15TradingScopeError("M15_STEP23_TRADE_SCOPE_SESSION_TOKEN_INVALID")
    details = api._request(
        "POST", "/v1/sessions/details", {"token": auth["token"]})
    if not isinstance(details, dict) or details.get("readonly") is not False:
        raise M15TradingScopeError("M15_STEP23_TRADE_SCOPE_NOT_TRADING_TOKEN")
    if details.get("account_ids") != [m15_account_id]:
        raise M15TradingScopeError("M15_STEP23_TRADE_SCOPE_ACCOUNT_NOT_EXACT_SINGLE")
    if api.readonly_bound is not False or hasattr(api, "place_order"):
        raise M15TradingScopeError("M15_STEP23_TRADE_SCOPE_READSIDE_ONLY_INVARIANT")
    return {
        "trading_token_exact_single_m15_account": True,
        "auth_post_count": 2,
        "broker_order_post_count": 0,
        "broker_order_cancel_count": 0,
        "live_authorized": False,
        "task_activated": False,
    }


def _gui_credentials() -> tuple[str, str]:
    """Local Windows form; token masked and never written to a shell or file."""
    import tkinter as tk
    root = tk.Tk()
    chosen: tuple[str, str] | None = None
    try:
        root.title("IntradayLab M15 / TRADING token scope check - AUTH ONLY")
        root.geometry("650x205")
        root.resizable(False, False)
        tk.Label(root, text="Session AUTH only. NO orders. Ctrl+V is supported.").pack(padx=12, pady=8)
        tk.Label(root, text="Separate M15 FINAM account ID").pack()
        account = tk.Entry(root, width=78)
        account.pack(padx=12)
        tk.Label(root, text="Separate M15 TRADING API secret (not READONLY; masked)").pack()
        token = tk.Entry(root, width=78, show="*")
        token.pack(padx=12)
        status = tk.Label(root, text="")
        status.pack()

        def accept():
            nonlocal chosen
            m15, key = account.get().strip(), token.get().strip()
            if not m15 or len(m15) > 128 or not key:
                status.config(text="Enter a separate M15 account and trading secret.")
                return
            chosen = (m15, key)
            root.quit()

        def cancel():
            root.quit()

        tk.Button(root, text="Verify token scope (NO orders)", command=accept).pack(pady=8)
        root.protocol("WM_DELETE_WINDOW", cancel)
        root.bind("<Escape>", lambda _: cancel())
        account.focus_set()
        root.lift()
        root.mainloop()
    finally:
        root.destroy()
    if chosen is None:
        raise M15TradingScopeError("M15_STEP23_TRADE_SCOPE_GUI_CANCELLED")
    return chosen


def safe_failure_code(exc: Exception) -> str:
    if not isinstance(exc, (M15TradingScopeError, M15FinamReadOnlyError)):
        return "M15_STEP23_TRADE_SCOPE_UNEXPECTED_ERROR"
    code = str(exc)
    if len(code) <= 108 and re.fullmatch(r"M15_[A-Z][A-Z0-9_]*", code):
        return code
    return "M15_STEP23_TRADE_SCOPE_UNCLASSIFIED_ERROR"


def main() -> int:
    print("m15_step23_trade_token_probe=session_auth_only", flush=True)
    print("m15_step23_no_order_no_task_no_h1_io=yes", flush=True)
    print("m15_live_authorized=no", flush=True)
    try:
        m15, token = _gui_credentials()
        verify_m15_trading_token_scope(m15_account_id=m15, secret=token)
        del token
        print("m15_step23_trading_token_exact_account=pass", flush=True)
        print("m15_step23_trade_order_authorized=no", flush=True)
        print("m15_live_authorized=no", flush=True)
        return 0
    except (KeyboardInterrupt, EOFError):
        print("m15_step23_trade_scope=cancelled", flush=True)
        return 1
    except Exception as exc:
        print("m15_step23_trade_scope_failure=" + safe_failure_code(exc), flush=True)
        print("m15_step23_trading_token_exact_account=fail_closed", flush=True)
        print("m15_live_authorized=no", flush=True)
        return 1


if __name__ == "__main__":
    if sys.argv[1:]:
        print("m15_step23_trade_scope=invalid_args", flush=True)
        sys.exit(1)
    sys.exit(main())
