"""Opt-in initial M15 deposited-capital proof, only bound FINAM READONLY GET.

Uses same local GUI as Step15 (no passwords in shell); no account values in logs.
Historical trades/transactions must be complete and consistent before PASS.
No live orders, Task, H1 access, runtime state writes or capital assignment.
"""
from __future__ import annotations

import sys
from datetime import datetime, timezone

from .broker_risk_readonly import check_account, M15RiskAuthorityError
from .broker_snapshot import order_views, position_quantities
from .finam_readonly import M15FinamReadOnlyAPI, M15FinamReadOnlyError
from .initial_capital import lifetime_interval, prove_initial_basis
from .step15_broker_probe import _gui_credentials
from .spec import EXECUTION_STATUS


def main() -> int:
    print("M15_STEP15_CAPITAL_NO_ORDER_NO_TASK_NO_H1_ACCESS=YES", flush=True)
    print("M15_STEP15_CAPITAL_ONLY_READONLY_BOUND_GET=YES", flush=True)
    if EXECUTION_STATUS != "NOT_LIVE_AUTHORIZED":
        print("M15_STEP15_CAPITAL_FAIL_CLOSED=LIVE_AUTHORITY_UNEXPECTED")
        return 1
    try:
        m15, h1, token = _gui_credentials()
        if not m15 or not h1 or m15 == h1 or not token:
            raise M15RiskAuthorityError("M15_CAPITAL_ACCOUNTS_NOT_DISTINCT")
        api = M15FinamReadOnlyAPI(secret=token, account_id=m15, timeout=10)
        del token
        api.connect_readonly()
        if not api.readonly_bound:
            raise M15RiskAuthorityError("M15_CAPITAL_BINDING_NOT_PROVEN")
        account = api.account(m15)
        orders = api.orders(m15)
        if position_quantities(account) or any(row.active for row in order_views(orders)):
            raise M15RiskAuthorityError("M15_CAPITAL_ACCOUNT_NOT_FLAT")
        funds = check_account(account, m15)
        start, finish, begin, end = lifetime_interval(account, datetime.now(timezone.utc))
        history = api.trades(m15, start=start, end=finish, limit=1000)
        cashflows = api.transactions(m15, start=start, end=finish, limit=1000)
        proof = prove_initial_basis(
            account=account, funds=funds, trades=history, transactions=cashflows,
            begin=begin, end=end,
        )
        print("M15_STEP15_CAPITAL_LIFETIME_BOUNDED_FINAM_GET=PASS", flush=True)
        print("M15_STEP15_CAPITAL_BROKER_TRADES=0", flush=True)
        print("M15_STEP15_CAPITAL_ONLY_POSITIVE_RUB_DEPOSITS=PASS", flush=True)
        print("M15_STEP15_CAPITAL_DEPOSITS_EQUALS_REALIZED_EQUITY=PASS", flush=True)
        print("M15_STEP15_CAPITAL_INITIAL_R15_BASIS=PASS", flush=True)
        print("M15_STEP15_CAPITAL_FUTURE_CASHFLOW_LEDGER=NOT_PROVEN", flush=True)
        print("M15_STEP15_RISK_LIVE_READY=NO", flush=True)
        print("M15_LIVE_AUTHORIZED=NO", flush=True)
        print("M15_STEP15_CAPITAL_EXIT_CODE=0", flush=True)
        return 0
    except (M15RiskAuthorityError, M15FinamReadOnlyError) as exc:
        code = str(exc)
        if not code.startswith("M15_"):
            code = "M15_CAPITAL_UNKNOWN_FAILURE"
        print("M15_STEP15_CAPITAL_FAIL_CLOSED=" + code, flush=True)
        print("M15_LIVE_AUTHORIZED=NO", flush=True)
        return 1
    except (KeyboardInterrupt, EOFError):
        print("M15_STEP15_CAPITAL_FAIL_CLOSED=OPERATOR_CANCELLED", flush=True)
        return 1
    except Exception:
        print("M15_STEP15_CAPITAL_FAIL_CLOSED=UNEXPECTED", flush=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
