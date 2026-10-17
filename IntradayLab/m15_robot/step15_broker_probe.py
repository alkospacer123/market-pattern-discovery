"""Opt-in interactive, in-memory FINAM READONLY N4 GO/portfolio diagnostic.

Separate M15 account only. Two permitted session-auth POSTs; otherwise GET.
No credentials, account ids, JWT or raw response written to files or logs.
No H1 path, SQLite, windows task, order/SLTP/cancel endpoint, authorization.
"""
from __future__ import annotations

import getpass
import hashlib
import sys

from .broker_risk_readonly import check_account, check_instrument, M15RiskAuthorityError
from .broker_snapshot import order_views, position_quantities
from .finam_readonly import M15FinamReadOnlyAPI, M15FinamReadOnlyError
from .spec import EXECUTION_STATUS, INSTRUMENTS


def main() -> int:
    print("M15_STEP15_NO_ORDER_NO_TASK_NO_H1_ACCESS=YES", flush=True)
    print("M15_STEP15_READONLY_AUTH_POST_ONLY_THEN_GET_ONLY=YES", flush=True)
    if EXECUTION_STATUS != "NOT_LIVE_AUTHORIZED":
        print("M15_STEP15_FAIL_CLOSED=LIVE_AUTHORITY_UNEXPECTED")
        return 1
    try:
        m15 = getpass.getpass("enter separate m15 account id (hidden): ").strip()
        h1 = getpass.getpass("enter h1 account id ONLY for local inequality check (hidden): ").strip()
        if not m15 or not h1 or m15 == h1 or len(m15) > 128 or len(h1) > 128:
            raise M15RiskAuthorityError("M15_STEP15_ACCOUNTS_NOT_DISTINCT")
        secret = getpass.getpass("enter separate m15 READONLY token (hidden): ").strip()
        if not secret:
            raise M15RiskAuthorityError("M15_STEP15_READONLY_TOKEN_REQUIRED")
        api = M15FinamReadOnlyAPI(secret=secret, account_id=m15, timeout=10)
        del secret
        api.connect_readonly()
        if not api.readonly_bound:
            raise M15RiskAuthorityError("M15_STEP15_READONLY_NOT_BOUND")
        account = api.account(m15)
        orders = api.orders(m15)
        positions = position_quantities(account)
        active = [o for o in order_views(orders) if o.active]
        if positions or active:
            raise M15RiskAuthorityError("M15_STEP15_BROKER_NOT_FLAT")
        funds = check_account(account, m15)
        print("M15_STEP15_EXACT_SEPARATE_READONLY_ACCOUNT=PASS", flush=True)
        print("M15_STEP15_POSITIONS_AND_ACTIVE_ORDERS=0", flush=True)
        print("M15_STEP15_PORTFOLIO_SCHEMA=PASS", flush=True)
        print("M15_STEP15_AVAILABLE_CASH_NONNEGATIVE=PASS", flush=True)
        print("M15_STEP15_EQUITY_MINUS_UNREALIZED_PRELIMINARY=PASS", flush=True)
        for instrument in INSTRUMENTS:
            symbol = instrument + "@RTSX"
            asset = api.asset_details(symbol)
            params = api.asset_params(symbol)
            checked = check_instrument(asset, params, symbol, m15)
            print(f"M15_STEP15_{instrument}_ASSET_STEP_LOT_LONG_SHORT_GO=PASS "
                  f"step={checked.price_step} lot={checked.trade_lot_size} "
                  f"go_long_rub={checked.long_initial_margin_rub} "
                  f"go_short_rub={checked.short_initial_margin_rub}", flush=True)
        print("M15_STEP15_N4_BROKER_GO_READONLY=PASS", flush=True)
        print("M15_STEP15_TICK_RUB_VALUE_AUTHORITY=NOT_PROVEN", flush=True)
        print("M15_STEP15_REALIZED_EQUITY_CASHFLOW_RECONCILIATION=NOT_PROVEN", flush=True)
        print("M15_STEP15_RISK_LIVE_READY=NO", flush=True)
        print("M15_LIVE_AUTHORIZED=NO", flush=True)
        print("M15_STEP15_EXIT_CODE=0", flush=True)
        return 0
    except (M15RiskAuthorityError, M15FinamReadOnlyError) as exc:
        # Only our explicit internal codes; never dump bearer token or account data.
        message = str(exc)
        if not message.startswith("M15_"):
            message = "M15_STEP15_READONLY_FAILED"
        print("M15_STEP15_FAIL_CLOSED=" + message, flush=True)
        print("M15_LIVE_AUTHORIZED=NO", flush=True)
        return 1
    except (KeyboardInterrupt, EOFError):
        print("M15_STEP15_FAIL_CLOSED=OPERATOR_CANCELLED", flush=True)
        return 1
    except Exception:
        print("M15_STEP15_FAIL_CLOSED=READONLY_PROBE_UNEXPECTED_ERROR", flush=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
