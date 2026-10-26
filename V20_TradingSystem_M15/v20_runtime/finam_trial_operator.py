"""One supervised V20-08.2 approved FINAM trial, not the autonomous LIVE Task.

H1 FINAM API, H1 StateStore/lock, V20 single-trial transport and frozen
NEXT_OPEN are reused unchanged. Execution is impossible without an exact
on-disk account/order-specific permit and an explicitly ARMED own kill switch.
Never schedule this module automatically; operator must supervise the process.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation
import hashlib
import os
from pathlib import Path
import re
import time

from TradingSystemLab.stage8_robot.finam_api import FinamAPI
from TradingSystemLab.stage8_robot.trading_safety_gate import (
    emergency_halt, load_kill_switch,
)

from .finam_execution import (
    V20FinamBlocked, V20FinamReadAdapter, V20SingleTradeTransport,
    V20TradeJournal, run_v20_single_trial_cycle,
)
from .h1_state_journal import ROBOT_STRATEGIES
from .offline_planner import N4


def _inputs(robot: str, symbol: str, fee: str, source_sha: str) -> tuple[str, str, Decimal]:
    if robot not in ROBOT_STRATEGIES or symbol not in N4:
        raise V20FinamBlocked("TRIAL_OPERATOR_SCOPE_INVALID")
    if not re.fullmatch(r"[a-f0-9]{40}", source_sha):
        raise V20FinamBlocked("TRIAL_OPERATOR_COMMIT_INVALID")
    try:
        cost = Decimal(fee)
    except (InvalidOperation, TypeError, ValueError):
        raise V20FinamBlocked("TRIAL_OPERATOR_FULL_COST_INVALID") from None
    if not cost.is_finite() or cost <= 0:
        raise V20FinamBlocked("TRIAL_OPERATOR_FULL_COST_REQUIRED")
    return robot, symbol, cost


TERMINAL = {
    "BROKER_FLAT_NO_ACTIVE_STOP",
    "STOP_EXIT_BROKER_FLAT_UNDER_ACCEPTANCE",
}
NO_NEW_ENTRY = {"NO_FROZEN_SIGNAL", "BROKER_OBSERVED_NO_TRIAL_ENTRY"}


def supervised_cycle(
    sender: V20SingleTradeTransport, *, symbol: str, cost: Decimal,
    mode: str, sleep=time.sleep, now_utc=None,
) -> str:
    """Only approved one-entry cycle; follow means no new entries, even ARMED.

    Existing H1/V20 ledger prevents a duplicate after process restart.
    Existing FINAM stop remains on broker while a third-session exit is due.
    """
    if mode not in ("trial", "follow"):
        raise V20FinamBlocked("TRIAL_OPERATOR_MODE_INVALID")
    clock = now_utc if now_utc is not None else lambda: datetime.now(timezone.utc)
    allow_entry = mode == "trial"
    iterations = 0
    while True:
        now = clock()
        if now.tzinfo is None or now.utcoffset() is None:
            raise V20FinamBlocked("TRIAL_OPERATOR_CLOCK_INVALID")
        observed = run_v20_single_trial_cycle(
            sender, now=now, trial_symbol=symbol,
            from_utc=now-timedelta(days=20), cost_per_contract=cost,
            allow_new_entry=allow_entry,
        )
        state = observed["state"]
        print("v20_08_2_cycle=" + state, flush=True)
        if state in TERMINAL:
            return state
        if state in NO_NEW_ENTRY and allow_entry:
            return state
        if state == "BROKER_OBSERVED_NO_TRIAL_ENTRY":
            return state
        # Once the first attempt has been considered, follow only; any
        # subsequent attempt to submit a new entry is forbidden.
        allow_entry = False
        iterations += 1
        if iterations >= 200000:
            raise V20FinamBlocked("TRIAL_OPERATOR_SUPERVISION_CEILING")
        sleep(5)


def run(*, root: Path, robot: str, symbol: str, fee: str,
        source_sha: str, mode: str) -> str:
    robot, symbol, cost = _inputs(robot, symbol, fee, source_sha)
    if mode not in ("trial", "follow"):
        raise V20FinamBlocked("TRIAL_OPERATOR_MODE_INVALID")
    if not root.is_absolute() or root.name.casefold() != "v20lab":
        raise V20FinamBlocked("TRIAL_OPERATOR_ROOT_INVALID")
    account = os.environ.get("V20_FINAM_ACCOUNT", "")
    secret = os.environ.get("V20_FINAM_TOKEN", "")
    scope = os.environ.get("V20_FINAM_ACCOUNT_SHA256", "")
    if (not re.fullmatch(r"[A-Za-z0-9_.-]{1,128}", account)
            or not secret or not re.fullmatch(r"[a-f0-9]{64}", scope)
            or hashlib.sha256(account.encode()).hexdigest() != scope):
        raise V20FinamBlocked("TRIAL_OPERATOR_ACCOUNT_SCOPE_INVALID")
    api = FinamAPI(secret)
    reader = V20FinamReadAdapter(
        api=api, robot_id=robot, account_id=account,
        expected_account_hash=scope,
    )
    # Journal/InstanceLock is shared between submit, follow and recovery.
    with V20TradeJournal(root, robot, account) as journal:
        permit = journal.instance_root / "safety" / "v20-single-trial-approval.json"
        sender = V20SingleTradeTransport(
            journal=journal, reader=reader, accepted_commit=source_sha,
            trial_permit_path=permit,
        )
        try:
            # Before actual broker requests, require the exact scoped permit.
            # Reuse transport's _permit in both entry and follow modes.
            import json
            if not permit.is_file() or permit.is_symlink():
                raise V20FinamBlocked("TRIAL_OPERATOR_PERMIT_MISSING")
            try:
                owner_record = json.loads(permit.read_text(encoding="utf-8"))
            except (OSError, UnicodeError, ValueError):
                raise V20FinamBlocked("TRIAL_OPERATOR_PERMIT_INVALID") from None
            if (not isinstance(owner_record, dict)
                    or owner_record.get("instrument") != symbol
                    or owner_record.get("source_commit") != source_sha
                    or owner_record.get("robot_id") != robot
                    or owner_record.get("account_sha256") != scope
                    or owner_record.get("explicit_owner_approval") is not True):
                raise V20FinamBlocked("TRIAL_OPERATOR_PERMIT_SCOPE_INVALID")
            key = owner_record.get("entry_key")
            if not isinstance(key, str) or not key.startswith("v20:" + robot + ":"):
                raise V20FinamBlocked("TRIAL_OPERATOR_ENTRY_KEY_INVALID")
            sender._permit(key=key, kind="ENTRY" if mode == "trial" else "PROTECTIVE_STOP")
            switch, err = load_kill_switch(journal.instance_root)
            if mode == "trial" and (err or switch["state"] != "ARMED"):
                raise V20FinamBlocked("TRIAL_OPERATOR_SWITCH_NOT_ARMED")
            if mode == "follow" and not journal.store.all_intents():
                raise V20FinamBlocked("TRIAL_OPERATOR_NO_ENTRY_TO_FOLLOW")
            reader.authenticate()
            return supervised_cycle(
                sender, symbol=symbol, cost=cost, mode=mode,
            )
        finally:
            # HALTED inhibits NEW entries only; active FINAM SLTP/exit
            # operations continue through existing H1 risk-reducing methods.
            emergency_halt(journal.instance_root)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", required=True)
    parser.add_argument("--robot", choices=tuple(ROBOT_STRATEGIES), required=True)
    parser.add_argument("--symbol", choices=tuple(sorted(N4)), required=True)
    parser.add_argument("--full-roundtrip-cost", required=True)
    parser.add_argument("--source-sha", required=True)
    parser.add_argument("--mode", choices=("trial", "follow"), required=True)
    args = parser.parse_args()
    try:
        result = run(
            root=Path(args.root), robot=args.robot, symbol=args.symbol,
            fee=args.full_roundtrip_cost, source_sha=args.source_sha,
            mode=args.mode,
        )
    except (Exception, KeyboardInterrupt) as exc:
        code = str(exc)
        safe = code if re.fullmatch(r"[A-Z0-9_]{4,110}", code) else "OPERATOR_REQUIRES_RECONCILIATION"
        print("v20_08_2_operator=HOLD_" + safe, flush=True)
        print("v20_08_2_new_entry=BLOCKED", flush=True)
        return 2
    print("v20_08_2_operator=" + result, flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
