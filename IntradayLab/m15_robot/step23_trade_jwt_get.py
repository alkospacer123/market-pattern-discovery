"""Step #23: broker GET evidence in the SAME scoped M15 trading JWT.

No trading-client construction, broker order POST/cancel/SLTP, permanent
authorization, Task mutation, H1 account IO or persistent state writes.
This is a one-off FINAM pre-POST read-side acceptance check ONLY.
"""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import sys

from .finam_readonly import M15FinamReadOnlyAPI
from .broker_risk_readonly import check_account, check_instrument
from .broker_snapshot import order_views, position_quantities
from .exchange_contract import contract_from_moex_and_finam
from .finam_trading import M15_ORDER_POST_RELEASED
from .spec import EXECUTION_STATUS, INSTRUMENTS
from .step23_readonly_preflight import inspect_m15_halted_runtime
from .step23_trading_token_scope import _gui_credentials, safe_failure_code


class M15TradingJwtGetError(RuntimeError):
    pass


def verify_m15_trade_jwt_broker_get(
    *, api: M15FinamReadOnlyAPI, m15_account_id: str,
    runtime_root: Path,
) -> dict:
    if (EXECUTION_STATUS != "NOT_LIVE_AUTHORIZED"
            or M15_ORDER_POST_RELEASED is not False):
        raise M15TradingJwtGetError("M15_STEP23_LIVE_FREEZE_UNEXPECTED")
    if (type(api) is not M15FinamReadOnlyAPI
            or api.readonly_bound is not False
            or api.trading_get_only_bound is not True
            or not isinstance(m15_account_id, str)
            or api.account_id != m15_account_id):
        raise M15TradingJwtGetError("M15_STEP23_TRADING_JWT_NOT_EXACT_BOUND")
    runtime = inspect_m15_halted_runtime(runtime_root)
    if (not runtime["m15_runtime_halted"]
            or runtime["production_switch_present"]
            or runtime["production_heartbeat_present"]):
        raise M15TradingJwtGetError("M15_STEP23_PRODUCTION_STATE_REVIEW_REQUIRED")
    account = api.account(m15_account_id)
    orders_response = api.orders(m15_account_id)
    if position_quantities(account) or any(x.active for x in order_views(orders_response)):
        raise M15TradingJwtGetError("M15_STEP23_TRADING_JWT_BROKER_NOT_FLAT")
    funds = check_account(account, m15_account_id)
    if funds.available_cash <= 0:
        raise M15TradingJwtGetError("M15_STEP23_TRADING_JWT_NO_FREE_GO")
    could_cover_one = False
    for instrument in INSTRUMENTS:
        symbol = instrument + "@RTSX"
        authority = check_instrument(
            api.asset_details(symbol), api.asset_params(symbol),
            symbol, m15_account_id)
        verified = contract_from_moex_and_finam(authority)
        if funds.available_cash >= min(
                verified.long_initial_margin,
                verified.short_initial_margin) * verified.trade_lot_size:
            could_cover_one = True
    if not could_cover_one:
        raise M15TradingJwtGetError("M15_STEP23_TRADING_JWT_NO_AFFORDABLE_N4_GO")
    return {
        "exact_trading_jwt_get": True,
        "account_flat": True,
        "active_order_count": 0,
        "n4_go_and_tick": True,
        "initial_capital_from_previous_readonly_proof": "NOT_RECHECKED",
        "causal_next_open_signal": "NOT_EVALUATED",
        "broker_sltp": "NOT_EVALUATED",
        "live_authorized": False,
        "order_post_permitted": False,
    }


def main() -> int:
    print("m15_step23_same_trading_jwt_get_only=yes", flush=True)
    print("m15_step23_no_order_no_task_no_h1_access=yes", flush=True)
    print("m15_live_authorized=no", flush=True)
    phase = "local_gui"
    try:
        m15, token = _gui_credentials()
        phase = "trading_jwt_bind"
        api = M15FinamReadOnlyAPI(secret=token, account_id=m15)
        del token
        api.connect_trading_get_only()
        phase = "broker_get"
        result = verify_m15_trade_jwt_broker_get(
            api=api, m15_account_id=m15,
            runtime_root=Path("c:/intradaylab/runtime/m15"))
        print("m15_step23_same_jwt_account_orders=pass", flush=True)
        print("m15_step23_same_jwt_n4_go=pass", flush=True)
        print("m15_step23_trade_order_authorized=no", flush=True)
        print("m15_live_authorized=no", flush=True)
        return 0
    except (KeyboardInterrupt, EOFError):
        print("m15_step23_same_jwt=cancelled", flush=True)
        return 1
    except Exception as exc:
        print("m15_step23_same_jwt_phase=" + phase, flush=True)
        # Local-only constant-code exceptions, no FINAM response or secrets.
        print("m15_step23_same_jwt_failure="
              + safe_failure_code(exc), flush=True)
        print("m15_step23_same_jwt_get=fail_closed", flush=True)
        print("m15_live_authorized=no", flush=True)
        return 1


if __name__ == "__main__":
    if sys.argv[1:]:
        print("m15_step23_same_jwt=invalid_mode", flush=True)
        sys.exit(1)
    sys.exit(main())
