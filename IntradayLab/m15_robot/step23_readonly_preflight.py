"""M15 roadmap #23: fresh FINAM GET-only capital/GO preflight, not trading.

One already-established M15 READONLY session, local masked credential form,
exact M15 account and existing HALTED sentinel. Never creates production
switch/heartbeat, modifies Task, sends a broker order or claims READY_TO_TRADE.
"""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import json
import sys

from .broker_risk_readonly import check_account, check_instrument
from .broker_snapshot import order_views, position_quantities
from .cashflow_reconcile_gate import CashflowWindow, propose_realized_capital
from .exchange_contract import contract_from_moex_and_finam
from .finam_readonly import M15FinamReadOnlyAPI
from .initial_capital import lifetime_interval
from .spec import EXECUTION_STATUS, INSTRUMENTS, RISK_FRACTION
from .finam_trading import M15_ORDER_POST_RELEASED


class M15Step23PreflightError(RuntimeError):
    pass


def inspect_m15_halted_runtime(runtime_root: Path) -> dict:
    """Observe the existing M15-only operator HALTED file, no writes or H1 IO.

    Production ARMED switch and heartbeat are NOT synthesized from this
    offline check: those require their own authenticated real worker.
    """
    if not isinstance(runtime_root, Path) or not runtime_root.is_absolute():
        raise M15Step23PreflightError("M15_STEP23_RUNTIME_PATH_INVALID")
    root = runtime_root.resolve()
    if (runtime_root.is_symlink() or "tradingsystemlab" in
            (x.lower() for x in root.parts)):
        raise M15Step23PreflightError("M15_STEP23_RUNTIME_OUTSIDE_M15")
    old = root / "state" / "kill-switch.json"
    if old.is_symlink() or old.parent.is_symlink() or not old.is_file():
        raise M15Step23PreflightError("M15_STEP23_HALTED_FILE_MISSING")
    if old.stat().st_size > 8192:
        raise M15Step23PreflightError("M15_STEP23_HALTED_FILE_INVALID")
    try:
        switch = json.loads(old.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, ValueError):
        raise M15Step23PreflightError("M15_STEP23_HALTED_FILE_INVALID") from None
    if (not isinstance(switch, dict)
            or str(switch.get("state", "")).lower() != "halted"):
        raise M15Step23PreflightError("M15_STEP23_NOT_HALTED")
    # Both are required for future broker ENTRY authority. Their absence is
    # recorded as a real implementation blocker, NEVER fabricated as healthy.
    production = (
        root / "safety" / "m15-trading-kill-switch.json",
        root / "diagnostics" / "m15-production-heartbeat.json",
    )
    if any(x.is_symlink() or x.parent.is_symlink() for x in production):
        raise M15Step23PreflightError("M15_STEP23_PRODUCTION_SYMLINK_INVALID")
    return {
        "m15_runtime_halted": True,
        "production_switch_present": production[0].is_file(),
        "production_heartbeat_present": production[1].is_file(),
        "live_authorized": False,
    }


def verify_m15_step23_financial_preflight(
    *, api: M15FinamReadOnlyAPI, m15_account_id: str,
    h1_account_id: str, runtime_root: Path, observed_at: datetime,
) -> dict:
    """Check fresh exact-account CASHFLOW/GO for all N4; do not size a trade.

    Real NEXT_OPEN, signal ATR, transaction commitment, LIVE trading JWT,
    protection and FLAT are NOT proven by this preflight. This is an
    independent financial condition check before further engineering.
    """
    if (EXECUTION_STATUS != "NOT_LIVE_AUTHORIZED"
            or M15_ORDER_POST_RELEASED is not False):
        raise M15Step23PreflightError("M15_STEP23_STATIC_ORDER_FREEZE_CHANGED")
    if (not isinstance(observed_at, datetime)
            or observed_at.tzinfo is None or observed_at.utcoffset() is None
            or type(api) is not M15FinamReadOnlyAPI
            or api.readonly_bound is not True
            or not isinstance(m15_account_id, str) or not m15_account_id
            or not isinstance(h1_account_id, str) or not h1_account_id
            or m15_account_id == h1_account_id
            or api.account_id != m15_account_id):
        raise M15Step23PreflightError("M15_STEP23_SEPARATE_READONLY_ACCOUNT_REQUIRED")
    runtime = inspect_m15_halted_runtime(runtime_root)
    # A physical observer must not accidentally run against newly activated
    # production evidence (or attempt to validate it from a read-only token).
    if runtime["production_switch_present"] or runtime["production_heartbeat_present"]:
        raise M15Step23PreflightError("M15_STEP23_PRODUCTION_RUNTIME_REVIEW_REQUIRED")
    account = api.account(m15_account_id)
    orders = api.orders(m15_account_id)
    if position_quantities(account) or any(x.active for x in order_views(orders)):
        raise M15Step23PreflightError("M15_STEP23_FINAM_ACCOUNT_NOT_FLAT")
    broker = check_account(account, m15_account_id)
    start, finish, begin, end = lifetime_interval(account, observed_at)
    transactions = api.transactions(
        m15_account_id, start=start, end=finish, limit=1000)
    capital = propose_realized_capital(
        account=account, expected_account_id=m15_account_id,
        windows=[CashflowWindow(begin, end, transactions, 1000)],
        now=observed_at,
    )
    if (capital.transaction_count < 1 or capital.runtime_r15_authorized
            or capital.live_authorized
            or capital.proposed_realized_equity !=
            broker.broker_equity_minus_unrealized
            or capital.proposed_realized_equity * RISK_FRACTION <= 0):
        raise M15Step23PreflightError("M15_STEP23_REALIZED_R15_NOT_PROVEN")
    if broker.available_cash <= 0:
        raise M15Step23PreflightError("M15_STEP23_NO_AVAILABLE_GO")
    one_contract_possible = False
    for instrument in INSTRUMENTS:
        symbol = instrument + "@RTSX"
        asset = api.asset_details(symbol)
        params = api.asset_params(symbol)
        authority = check_instrument(
            asset, params, symbol, m15_account_id)
        contract = contract_from_moex_and_finam(authority)
        contract.validate()
        if broker.available_cash >= min(
                contract.long_initial_margin,
                contract.short_initial_margin) * contract.trade_lot_size:
            one_contract_possible = True
    if not one_contract_possible:
        raise M15Step23PreflightError("M15_STEP23_NO_AFFORDABLE_N4_GO")
    return {
        "status": "PASS_FINANCIAL_GET_ONLY",
        "account_readonly_exact": True,
        "broker_flat": True,
        "realized_cashflow_reconciled": True,
        "n4_broker_go_tick_proven": True,
        "m15_runtime_halted": True,
        "production_switch_present": False,
        "production_heartbeat_present": False,
        "signal_next_open_atr_trade_size": "NOT_EVALUATED",
        "broker_sltp_100_percent": "NOT_EVALUATED",
        "entry_order_permitted": False,
        "live_authorized": False,
    }


def main() -> int:
    print("m15_step23_readonly_no_order_no_task_no_h1_access=yes",flush=True)
    try:
        from .step15_broker_probe import _gui_credentials
        m15, h1, token = _gui_credentials()
        api = M15FinamReadOnlyAPI(secret=token, account_id=m15)
        del token
        api.connect_readonly()
        result = verify_m15_step23_financial_preflight(
            api=api, m15_account_id=m15, h1_account_id=h1,
            runtime_root=Path("c:/intradaylab/runtime/m15"),
            observed_at=datetime.now(timezone.utc),
        )
        print("m15_step23_financial_preflight=pass",flush=True)
        print("m15_step23_account_readonly=pass",flush=True)
        print("m15_step23_broker_flat=pass",flush=True)
        print("m15_step23_current_cashflow_r15=pass",flush=True)
        print("m15_step23_n4_go_tick=pass",flush=True)
        print("m15_step23_production_heartbeat=missing",flush=True)
        print("m15_step23_real_order_authorized=no",flush=True)
        print("m15_live_authorized=no",flush=True)
        return 0
    except (KeyboardInterrupt, EOFError):
        print("m15_step23_readonly=cancelled",flush=True)
        return 1
    except Exception:
        # Never report broker messages, account ID, funds, token or raw REST.
        print("m15_step23_financial_preflight=fail_closed",flush=True)
        print("m15_live_authorized=no",flush=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
