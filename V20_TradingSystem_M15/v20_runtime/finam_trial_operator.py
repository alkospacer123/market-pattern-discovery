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
import json
import hashlib
import logging
import os
from pathlib import Path
import re
import sqlite3
import time

from TradingSystemLab.stage8_robot.finam_api import FinamAPI
from TradingSystemLab.stage8_robot.broker import compact_client_order_id
from TradingSystemLab.stage8_robot.production_broker_state import unique_order_by_client_id
from TradingSystemLab.stage8_robot.trading_safety_gate import (
    emergency_halt, load_kill_switch, write_kill_switch,
)

from .finam_execution import (
    V20FinamBlocked, V20FinamReadAdapter, V20SingleTradeTransport,
    V20TradeJournal, run_v20_single_trial_cycle,
)
from .account_risk import reserve_entry
from .h1_state_journal import ROBOT_STRATEGIES
from .offline_planner import N4


class TechnicalTrialJournal(V20TradeJournal):
    """H1 StateStore/InstanceLock, acceptance ledger separate from LIVE intents."""
    state_file = "v20-technical-acceptance.sqlite3"
    schema = "v20.h1_state_store.technical_acceptance.v1"
    mode = "V20_TECHNICAL_ACCEPTANCE_ONLY"


class ShallowStopRetestJournal(TechnicalTrialJournal):
    """One new Shallow stop proof; NEVER mutate or reuse its earlier POST ledger."""
    state_file = "v20-technical-shallow-retest.sqlite3"
    schema = "v20.h1_state_store.shallow_stop_retest.v1"


def prove_shallow_prior_post_and_flat(*, journal: ShallowStopRetestJournal,
                                      reader: V20FinamReadAdapter,
                                      source_sha: str, symbol: str) -> str:
    """GET-only owner-bounded retry gate using unchanged H1 broker observers.

    H1 InstanceLock is already held by the retest journal. The old database is
    opened SQLite URI mode=ro and NOT rewritten or reset. A previous confirmed
    broker POST (not a PRE-POST expiry) is mandatory. Real FINAM must be FLAT.
    """
    if (not isinstance(journal, ShallowStopRetestJournal)
            or journal.robot_id != "v20-shallow" or symbol != "CNYRUBF"):
        raise V20FinamBlocked("SHALLOW_RETEST_ROBOT_OR_SYMBOL_INVALID")
    from TradingSystemLab.stage8_robot.trading_safety_gate import load_kill_switch
    switch, err = load_kill_switch(journal.instance_root)
    if err or not switch or switch.get("state") != "HALTED":
        raise V20FinamBlocked("SHALLOW_RETEST_REQUIRES_HALTED")
    old = journal.instance_root / "state" / TechnicalTrialJournal.state_file
    first_permit = journal.instance_root / "safety" / "v20-single-trial-approval.json"
    if (not old.is_file() or old.is_symlink()
            or not first_permit.is_file() or first_permit.is_symlink()
            or first_permit.parent.is_symlink()):
        raise V20FinamBlocked("SHALLOW_RETEST_PRIOR_PROOF_MISSING")
    try:
        permission = json.loads(first_permit.read_text(encoding="utf-8"))
        with sqlite3.connect(old.as_uri() + "?mode=ro", uri=True) as db:
            def get_state(key):
                item = db.execute("SELECT value FROM state WHERE key=?", (key,)).fetchone()
                return json.loads(item[0]) if item else None
            identity = get_state("database_identity")
            rows = db.execute(
                "SELECT idempotency_key,payload,status,broker_order_id FROM intents"
            ).fetchall()
            old_fills = db.execute("SELECT COUNT(*) FROM fills").fetchone()[0]
            if len(rows) != 1:
                raise V20FinamBlocked("SHALLOW_RETEST_PRIOR_INTENTS_NOT_SINGLE")
            entry_key, text_payload, status, broker_id = rows[0]
            entry = json.loads(text_payload)
            if (not isinstance(permission, dict)
                    or permission.get("schema") != "v20.08.2.single_trial.v1"
                    or permission.get("scope") != "ONE_SPECIFIC_APPROVED_TRIAL"
                    or permission.get("source_commit") != source_sha
                    or permission.get("robot_id") != journal.robot_id
                    or permission.get("account_sha256") != journal.account_hash
                    or permission.get("entry_key") != entry_key
                    or permission.get("instrument") != "CNYRUBF"
                    or permission.get("direction") != "LONG"
                    or permission.get("max_quantity") != 1
                    or permission.get("trial_kind") !=
                        "TECHNICAL_ACCEPTANCE_NOT_STRATEGY_SIGNAL"
                    or identity != {
                        **journal.identity,
                        "schema_id": TechnicalTrialJournal.schema,
                    }
                    or not isinstance(entry_key, str)
                    or not isinstance(broker_id, str) or not broker_id
                    or status != "ACK"
                    or entry.get("kind") != "ENTRY"
                    or entry.get("robot_id") != journal.robot_id
                    or entry.get("account_sha256") != journal.account_hash
                    or entry.get("symbol") != "CNYRUBF"
                    or entry.get("direction") != "LONG"
                    or entry.get("quantity") != 1
                    or get_state("trial_authority_consumed") != entry_key
                    or get_state("entry_submission:" + entry_key) is None
                    or get_state("execution_halt") != "BROKER_ORDER_MISMATCH"
                    or get_state("protected_fill:" + entry_key) is not None
                    or old_fills):
                raise V20FinamBlocked("SHALLOW_RETEST_PRIOR_BROKER_POST_INVALID")
    except (sqlite3.Error, OSError, UnicodeError, ValueError, TypeError) as exc:
        raise V20FinamBlocked("SHALLOW_RETEST_PRIOR_READONLY_INVALID") from exc
    reader.authenticate()
    observed = reader.snapshot(now=datetime.now(timezone.utc))
    if not observed.clean:
        raise V20FinamBlocked("SHALLOW_RETEST_ACCOUNT_NOT_FLAT")
    original = unique_order_by_client_id(
        list(observed.orders), compact_client_order_id(entry_key),
    )
    if (original is not None
            and (original.order_id != broker_id or original.kind != "REGULAR"
                 or original.symbol != "CNYRUBF@RTSX"
                 or original.side != "SIDE_BUY")):
        raise V20FinamBlocked("SHALLOW_RETEST_PRIOR_BROKER_ID_MISMATCH")
    # Only NEW isolated SQLite is annotated; the old journal/permit is intact.
    journal.store.put("shallow_previous_client_order_id",
                      compact_client_order_id(entry_key))
    journal.store.put("shallow_retest_prior_proof", {
        "previous_broker_order_sha256": hashlib.sha256(broker_id.encode()).hexdigest(),
        "original_technical_sqlite": TechnicalTrialJournal.state_file,
        "account_sha256": journal.account_hash,
        "broker_flat_readonly": True,
    })
    return "PASS_PRIOR_REAL_POST_PRESERVED_BROKER_FLAT"

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



def advance_authorization(approved_path: Path, *, robot: str, account_hash: str,
                          symbol: str, source_sha: str) -> dict:
    """Read owner's preapproved ONE-trial scope; never infer consent from token."""
    if not approved_path.is_file() or approved_path.is_symlink() or approved_path.parent.is_symlink():
        raise V20FinamBlocked("TRIAL_ADVANCE_APPROVAL_MISSING")
    try:
        granted = json.loads(approved_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, ValueError):
        raise V20FinamBlocked("TRIAL_ADVANCE_APPROVAL_INVALID") from None
    expected = {
        "schema": "v20.08.2.first_signal_approval.v1",
        "scope": "ONE_FIRST_REAL_FROZEN_TRIAL_ONLY",
        "robot_id": robot,
        "account_sha256": account_hash,
        "source_commit": source_sha,
        "instrument": symbol,
        "max_risk_fraction": "0.015",
        "explicit_owner_approval": True,
    }
    if not isinstance(granted, dict) or any(granted.get(k) != v for k,v in expected.items()):
        raise V20FinamBlocked("TRIAL_ADVANCE_APPROVAL_SCOPE_INVALID")
    return granted


def create_exact_permit_on_signal(*, authorized_path: Path, permit_path: Path,
                                  robot: str, account_hash: str, symbol: str,
                                  source_sha: str, technical_acceptance: bool = False):
    """Real signal OR one clearly labeled technical trial -> H1 idempotency permit.

    Approves only the first frozen signal on the owner's selected instrument.
    One use, never overwrite an existing permit, no journal mutation or POST.
    """
    advance_authorization(
        authorized_path, robot=robot, account_hash=account_hash,
        symbol=symbol, source_sha=source_sha,
    )
    def on_signal(key, signal, proposal, authority):
        if (signal.symbol != symbol or proposal.symbol != symbol
                or signal.strategy != ROBOT_STRATEGIES[robot]
                or authority.account_id is None
                or hashlib.sha256(authority.account_id.encode()).hexdigest() != account_hash
                or proposal.direction not in ("LONG", "SHORT")
                or proposal.quantity <= 0):
            raise V20FinamBlocked("TRIAL_SIGNAL_SCOPE_INVALID")
        bound = authority.realized_equity * Decimal("0.015")
        risk = reserve_entry(
            authority=authority, entry_key=key, symbol=symbol,
            direction=proposal.direction, entry=proposal.reference_entry,
            atr14=signal.atr14, planned_max_quantity=proposal.quantity,
            current_reservations=(),
        )
        if risk.quantity < 1 or risk.reserved_risk > bound:
            raise V20FinamBlocked("TRIAL_SIGNAL_RISK_EXCEEDS_OWNER_LIMIT")
        if technical_acceptance and (proposal.direction != "LONG" or risk.quantity != 1):
            raise V20FinamBlocked("TECHNICAL_TRIAL_REQUIRES_ONE_LONG_CONTRACT")
        record = {
            "schema": "v20.08.2.single_trial.v1",
            "scope": "ONE_SPECIFIC_APPROVED_TRIAL",
            "source_commit": source_sha,
            "robot_id": robot,
            "account_sha256": account_hash,
            "entry_key": key,
            "authorized_operations": (
                ["ENTRY", "PROTECTIVE_STOP"] if technical_acceptance
                else ["ENTRY", "PROTECTIVE_STOP", "FROZEN_EXIT"]
            ),
            "explicit_owner_approval": True,
            "instrument": symbol,
            "direction": proposal.direction,
            "max_quantity": risk.quantity,
            "max_risk_rub": str(bound),
            "trial_kind": ("TECHNICAL_ACCEPTANCE_NOT_STRATEGY_SIGNAL"
                           if technical_acceptance else "FROZEN_NEXT_OPEN_SIGNAL"),
        }
        if permit_path.exists() or permit_path.is_symlink() or permit_path.parent.is_symlink():
            raise V20FinamBlocked("TRIAL_EXACT_PERMIT_ALREADY_EXISTS")
        # Exclusive creation prevents a second signal/process from altering the
        # owner's first authorized trade even if two workers race.
        with permit_path.open("x", encoding="utf-8", newline="\n") as fh:
            json.dump(record, fh, sort_keys=True, separators=(",", ":"))
            fh.write("\n")
            fh.flush()
            os.fsync(fh.fileno())
        print("v20_08_2_exact_permit=" + (
            "ONE_TECHNICAL_TRIAL_APPROVED" if technical_acceptance
            else "ONE_REAL_FROZEN_SIGNAL_APPROVED"), flush=True)
    return on_signal



def arm_one_approved_trial(instance_root: Path) -> None:
    """Temporary ARMED entry gate, confined to one approved 08.2 supervised trial.

    The enclosing run() always returns this gate to HALTED in its finally.
    No Windows Tasks, unrelated V20 instances or H1 runtime are modified.
    """
    switch, err = load_kill_switch(instance_root)
    if err or switch is None or switch.get("state") != "HALTED":
        raise V20FinamBlocked("TRIAL_OPERATOR_PREARM_SWITCH_NOT_HALTED")
    write_kill_switch(instance_root, "ARMED", allow_arm=True)
    switch, err = load_kill_switch(instance_root)
    if err or switch is None or switch.get("state") != "ARMED":
        raise V20FinamBlocked("TRIAL_OPERATOR_ARM_RESULT_UNVERIFIED")


def recover_unsubmitted_technical(
    *, journal: TechnicalTrialJournal, reader: V20FinamReadAdapter,
    sender: V20SingleTradeTransport, permit: Path, robot: str, symbol: str,
) -> str:
    """One V20-08.2 PRE-POST repair, never submit or authorize an order.

    Account/orders are read twice from FINAM while H1 InstanceLock is held.
    Recovery is refused if a durable POST checkpoint, any fill, another
    intent or any broker exposure exists. Old evidence stays inside H1 SQLite.
    """
    if (not isinstance(journal, TechnicalTrialJournal)
            or journal.state_file != "v20-technical-acceptance.sqlite3"):
        raise V20FinamBlocked("TECHNICAL_RECOVERY_LEDGER_SCOPE_INVALID")
    switch, error = load_kill_switch(journal.instance_root)
    if error or not switch or switch["state"] != "HALTED":
        raise V20FinamBlocked("TECHNICAL_RECOVERY_REQUIRES_HALTED")
    reader.authenticate()
    first = reader.snapshot(now=datetime.now(timezone.utc))
    second = reader.snapshot(now=datetime.now(timezone.utc))
    if not first.clean or not second.clean or first.positions != second.positions:
        raise V20FinamBlocked("TECHNICAL_RECOVERY_BROKER_NOT_FLAT")
    entries = journal.store.all_intents()
    audit = journal.store.get("technical_unposted_aborts", [])
    if not isinstance(audit, list):
        raise V20FinamBlocked("TECHNICAL_RECOVERY_AUDIT_INVALID")
    if not permit.is_file() or permit.is_symlink() or permit.parent.is_symlink():
        raise V20FinamBlocked("TECHNICAL_RECOVERY_PERMIT_MISSING")
    try:
        permission = json.loads(permit.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, ValueError):
        raise V20FinamBlocked("TECHNICAL_RECOVERY_PERMIT_INVALID") from None
    if (not isinstance(permission, dict)
            or permission.get("trial_kind") !=
            "TECHNICAL_ACCEPTANCE_NOT_STRATEGY_SIGNAL"
            or permission.get("robot_id") != robot
            or permission.get("account_sha256") != journal.account_hash
            or permission.get("instrument") != symbol
            or permission.get("direction") != "LONG"
            or permission.get("max_quantity") != 1):
        raise V20FinamBlocked("TECHNICAL_RECOVERY_PERMIT_SCOPE_INVALID")
    key = permission.get("entry_key")
    if not isinstance(key, str) or not key.startswith("v20:" + robot + ":"):
        raise V20FinamBlocked("TECHNICAL_RECOVERY_ENTRY_KEY_INVALID")
    if entries:
        if len(entries) != 1 or entries[0]["idempotency_key"] != key:
            raise V20FinamBlocked("TECHNICAL_RECOVERY_OTHER_INTENTS")
        row = entries[0]
        marker = journal.store.get("technical_acceptance:" + key)
        reservations = journal.store.get("risk_reservations", {})
        sessions = journal.store.get("session_entries", {})
        if (row["status"] != "INTENT_PERSISTED"
                or row["broker_order_id"] is not None
                or row["payload"].get("kind") != "ENTRY"
                or row["payload"].get("account_sha256") != journal.account_hash
                or row["payload"].get("robot_id") != robot
                or row["payload"].get("symbol") != symbol
                or row["payload"].get("direction") != "LONG"
                or row["payload"].get("quantity") != 1
                or not isinstance(marker, dict)
                or marker.get("kind") != "TECHNICAL_ACCEPTANCE_NOT_FROZEN_SIGNAL"
                or marker.get("account_sha256") != journal.account_hash
                or not isinstance(reservations, dict)
                or set(reservations) != {key}
                or not isinstance(sessions, dict)
                or sum(len(v) for v in sessions.values()) != 1
                or not any(v == [key] for v in sessions.values())
                or journal.store.get("entry_submission:" + key) is not None
                or journal.store.get("trial_authority_consumed") is not None
                or journal.store.get("execution_halt") is not None
                or journal.store.all_fills()):
            raise V20FinamBlocked("TECHNICAL_RECOVERY_POST_OR_STATE_UNCERTAIN")
        sender._permit(key=key, kind="ENTRY")
        with journal.store.transaction():
            # Atomically preserve the original prepared attempt in H1 state.
            # No previous irreversible FINAM POST is admissible here.
            journal.store.put("technical_unposted_aborts", audit + [{
                "entry_key": key, "original_intent": row,
                "original_marker": marker,
                "at_utc": datetime.now(timezone.utc).isoformat(),
                "result": "PREPOST_ABORT_BROKER_TWICE_FLAT_NO_POST_CHECKPOINT",
            }])
            cur = journal.store.db.execute(
                "DELETE FROM intents WHERE idempotency_key=? "
                "AND status='INTENT_PERSISTED' AND broker_order_id IS NULL",
                (key,),
            )
            if cur.rowcount != 1:
                raise V20FinamBlocked("TECHNICAL_RECOVERY_INTENT_CHANGED")
            journal.store.put("risk_reservations", {})
            journal.store.put("session_entries", {})
            journal.store.db.execute(
                "DELETE FROM state WHERE key=?", ("technical_acceptance:" + key,),
            )
    else:
        # Crash between atomic local cleanup and permit unlink: finish only
        # if prior abort evidence proves exactly which permit was cleared.
        if (not audit or audit[-1].get("entry_key") != key
                or journal.store.get("trial_authority_consumed") is not None
                or journal.store.all_fills()):
            raise V20FinamBlocked("TECHNICAL_RECOVERY_EMPTY_WITHOUT_PROOF")
    permit.unlink()
    return "PASS_PREPOST_ONLY_FINAM_TWICE_FLAT_NEW_ENTRY_STILL_OFF"


TERMINAL = {
    "BROKER_FLAT_NO_ACTIVE_STOP",
    "STOP_EXIT_BROKER_FLAT_UNDER_ACCEPTANCE",
    "MANUAL_EXIT_BROKER_FLAT_UNDER_ACCEPTANCE",
}
NO_NEW_ENTRY = {"NO_FROZEN_SIGNAL", "BROKER_OBSERVED_NO_TRIAL_ENTRY"}


def supervised_cycle(
    sender: V20SingleTradeTransport, *, symbol: str, cost: Decimal,
    mode: str, sleep=time.sleep, now_utc=None, permit_on_signal=None,
    wait_for_signal: bool = False,
) -> str:
    """Only approved one-entry cycle; follow means no new entries, even ARMED.

    Existing H1/V20 ledger prevents a duplicate after process restart.
    Existing FINAM stop remains on broker while a third-session exit is due.
    """
    if mode not in ("trial", "follow", "technical", "technical_follow",
                    "technical_retest"):
        raise V20FinamBlocked("TRIAL_OPERATOR_MODE_INVALID")
    clock = now_utc if now_utc is not None else lambda: datetime.now(timezone.utc)
    allow_entry = mode in ("trial", "technical", "technical_retest")
    technical = mode in ("technical", "technical_follow", "technical_retest")
    iterations = 0
    while True:
        now = clock()
        if now.tzinfo is None or now.utcoffset() is None:
            raise V20FinamBlocked("TRIAL_OPERATOR_CLOCK_INVALID")
        if wait_for_signal and allow_entry:
            # This is an ARMED, owner-authorized first-trial *executor*,
            # not a Shadow monitor. Only ask for a real NEXT_OPEN once at
            # approximately second 8 of each 15-minute interval.
            elapsed = (now.minute % 15)*60 + now.second + now.microsecond/1_000_000
            if elapsed < 8:
                sleep(8-elapsed)
                continue
            if elapsed > 25:
                sleep(900-elapsed+8)
                continue
        try:
            observed = run_v20_single_trial_cycle(
                sender, now=now, trial_symbol=symbol,
                from_utc=now-timedelta(days=20), cost_per_contract=cost,
                allow_new_entry=allow_entry,
                permit_on_signal=permit_on_signal if allow_entry else None,
                technical_acceptance=technical,
            )
        except V20FinamBlocked as exc:
            # No current FINAM Open / no adjacent completed bar / 60s expired
            # means NO ORDER this interval. Everything else fails closed.
            if not (wait_for_signal and allow_entry and str(exc) in {
                "M15_NEXT_OPEN_WITNESS_MISSING",
                "M15_FINAL_COMPLETED_BAR_MISSING",
                "M15_IMMEDIATE_NEXT_OPEN_MISSED",
            }):
                raise
            observed = {"state": "NO_FROZEN_SIGNAL", "orders": 0}
        state = observed["state"]
        print("v20_08_2_cycle=" + state, flush=True)
        if state in TERMINAL:
            return state
        if state in NO_NEW_ENTRY and allow_entry:
            if not wait_for_signal:
                return state
            # Retain the first-entry authorization, but never invent a signal
            # or consume an exact permit on an empty M15 boundary.
            later = clock()
            elapsed = (later.minute % 15)*60 + later.second + later.microsecond/1_000_000
            sleep(max(1,900-elapsed+8))
            continue
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
        source_sha: str, mode: str, arm_for_trial: bool = False) -> str:
    robot, symbol, cost = _inputs(robot, symbol, fee, source_sha)
    if mode not in ("trial", "follow", "technical", "technical_follow",
                    "technical_recover", "technical_retest"):
        raise V20FinamBlocked("TRIAL_OPERATOR_MODE_INVALID")
    retest = mode == "technical_retest"
    technical = mode in ("technical", "technical_follow", "technical_recover",
                         "technical_retest")
    opening = mode in ("trial", "technical", "technical_retest")
    if not root.is_absolute() or root.name.casefold() != "v20lab":
        raise V20FinamBlocked("TRIAL_OPERATOR_ROOT_INVALID")
    account = os.environ.get("V20_FINAM_ACCOUNT", "")
    secret = os.environ.get("V20_FINAM_TOKEN", "")
    scope = os.environ.get("V20_FINAM_ACCOUNT_SHA256", "")
    if (not re.fullmatch(r"[A-Za-z0-9_.-]{1,128}", account)
            or not secret or not re.fullmatch(r"[a-f0-9]{64}", scope)
            or hashlib.sha256(account.encode()).hexdigest() != scope):
        raise V20FinamBlocked("TRIAL_OPERATOR_ACCOUNT_SCOPE_INVALID")
    # Original H1 transport auto-renews HTTP 401 once. Its warning embeds
    # the private account path; do not expose it in operator console/logs.
    logging.getLogger("TradingSystemLab.stage8_robot.finam_api").setLevel(logging.ERROR)
    api = FinamAPI(secret)
    reader = V20FinamReadAdapter(
        api=api, robot_id=robot, account_id=account,
        expected_account_hash=scope,
    )
    # Journal/InstanceLock is shared between submit, follow and recovery.
    journal_type = (ShallowStopRetestJournal if retest else
                    TechnicalTrialJournal if technical else V20TradeJournal)
    with journal_type(root, robot, account) as journal:
        permit = journal.instance_root / "safety" / (
            "v20-shallow-stop-retest-approval.json" if retest
            else "v20-single-trial-approval.json"
        )
        sender = V20SingleTradeTransport(
            journal=journal, reader=reader, accepted_commit=source_sha,
            trial_permit_path=permit,
        )
        try:
            if retest:
                if not arm_for_trial:
                    raise V20FinamBlocked("SHALLOW_RETEST_EXPLICIT_FLAG_REQUIRED")
                witness = prove_shallow_prior_post_and_flat(
                    journal=journal, reader=reader, source_sha=source_sha,
                    symbol=symbol,
                )
                print("v20_08_2_shallow_retest_gate=" + witness, flush=True)
            if mode == "technical_recover":
                if arm_for_trial:
                    raise V20FinamBlocked("TECHNICAL_RECOVERY_MUST_NOT_ARM")
                return recover_unsubmitted_technical(
                    journal=journal, reader=reader, sender=sender,
                    permit=permit, robot=robot, symbol=symbol,
                )
            # Exact source permit may already exist (after restart).
            # Otherwise the owner explicitly authorized ONE first genuine
            # frozen signal. It will be atomically narrowed to an exact H1
            # single-trial key only after broker data and R15 sizing arrive.
            permit_on_signal = None
            if permit.is_file() and not permit.is_symlink():
                try:
                    owner_record = json.loads(permit.read_text(encoding="utf-8"))
                except (OSError, UnicodeError, ValueError):
                    raise V20FinamBlocked("TRIAL_OPERATOR_PERMIT_INVALID") from None
                if (not isinstance(owner_record, dict)
                        or owner_record.get("instrument") != symbol
                        or owner_record.get("source_commit") != source_sha
                        or owner_record.get("robot_id") != robot
                        or owner_record.get("account_sha256") != scope
                        or owner_record.get("explicit_owner_approval") is not True
                        or owner_record.get("trial_kind") != (
                            "TECHNICAL_ACCEPTANCE_NOT_STRATEGY_SIGNAL" if technical
                            else "FROZEN_NEXT_OPEN_SIGNAL")):
                    raise V20FinamBlocked("TRIAL_OPERATOR_PERMIT_SCOPE_INVALID")
                key = owner_record.get("entry_key")
                if not isinstance(key, str) or not key.startswith("v20:" + robot + ":"):
                    raise V20FinamBlocked("TRIAL_OPERATOR_ENTRY_KEY_INVALID")
                sender._permit(key=key, kind="ENTRY" if opening else "PROTECTIVE_STOP")
            elif opening:
                grant_path = journal.instance_root / "safety" / "v20-first-signal-approval.json"
                if not grant_path.is_file() or grant_path.is_symlink():
                    raise V20FinamBlocked("TRIAL_OPERATOR_PERMIT_MISSING")
                permit_on_signal = create_exact_permit_on_signal(
                    authorized_path=grant_path, permit_path=permit, robot=robot,
                    account_hash=scope, symbol=symbol, source_sha=source_sha,
                    technical_acceptance=technical,
                )
            else:
                raise V20FinamBlocked("TRIAL_OPERATOR_PERMIT_MISSING")
            if opening:
                if arm_for_trial is not True:
                    raise V20FinamBlocked("TRIAL_OPERATOR_EXPLICIT_ARM_FLAG_REQUIRED")
                if journal.store.all_intents():
                    raise V20FinamBlocked("TRIAL_OPERATOR_ENTRY_ALREADY_PREPARED")
                arm_one_approved_trial(journal.instance_root)
            elif journal.store.all_intents() == []:
                raise V20FinamBlocked("TRIAL_OPERATOR_NO_ENTRY_TO_FOLLOW")
            reader.authenticate()
            return supervised_cycle(
                sender, symbol=symbol, cost=cost, mode=mode,
                permit_on_signal=permit_on_signal,
                wait_for_signal=(mode == "trial" and permit_on_signal is not None),
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
    parser.add_argument("--mode", choices=("trial", "follow", "technical",
                                           "technical_follow", "technical_recover",
                                           "technical_retest"), required=True)
    parser.add_argument("--arm-for-trial", action="store_true", default=False)
    args = parser.parse_args()
    try:
        result = run(
            root=Path(args.root), robot=args.robot, symbol=args.symbol,
            fee=args.full_roundtrip_cost, source_sha=args.source_sha,
            mode=args.mode, arm_for_trial=args.arm_for_trial,
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
