"""PR #493 task 1.5 — one-attempt operator approval policy for FINAM adapter.

NOT an executable operator launcher. No token loader, broker/network API,
Windows Task control or production SQLite writes. Approval verification and
fresh physical authority must be independently provided by an operator-only
runner AFTER separate exact-deal permission. Without both: HOLD.
"""
from __future__ import annotations

from datetime import datetime, timezone, timedelta
from decimal import Decimal, InvalidOperation
from hashlib import sha256
import json
from typing import Callable

from .stage8_493_operator_harness import Hold, Journal, Plan
from .stage8_493_finam_readonly_observation import _time

SPEC = "PROD_STAGE7_46DB784378797C7FB04636892350AFF21006D71A31F2CED9D4B974EDA2DC36B8"
IDENTITY = "TRAIL1__N4_01__FULL__R15"
ACTIONS = frozenset({"ENTRY", "SLTP", "CANCEL", "EXIT"})
RECEIPT_FIELDS = frozenset({
    "schema", "production_specification_id", "active_identity",
    "account_hash", "instrument", "symbol", "direction", "quantity",
    "entry_key", "stop_key", "exit_key", "stop_price",
    "entry_reference", "fees_rub", "slippage_ticks",
    "risk_budget_rub", "approved_operations", "approved_from", "approved_until",
})
PHYSICAL_FIELDS = frozenset({
    "account_hash", "task_disabled", "switch_halted",
    "production_process_count", "production_lock_free",
    "write_session_exact_account", "broker_snapshot_age_seconds",
    "test_two_contract_margin_and_cash_current", "operator_budget_current_verified",
    "unresolved_intents_zero", "recovery_approved",
})


class OperatorOneAttemptWriteGate:
    """Callable accepted by FinamOperatorPort after external physical wiring.

    Strictly bounded approval and fresh host/broker checks must be supplied by
    independent verified operator functions; no claims that synthetic test
    callbacks establish those authorities. Gate intent is durable and
    recorded BEFORE any POST/DELETE. One action/ID cannot replay after restart.
    """

    def __init__(self, *, plan: Plan, journal: Journal, receipt: dict,
                 verify_operator_approval: Callable[[dict], bool] | None = None,
                 verify_physical_authority: Callable[[], dict] | None = None,
                 now: Callable[[], datetime] | None = None):
        plan.check()
        self.plan = plan
        self.journal = journal
        self.receipt = receipt
        self.verify_operator_approval = verify_operator_approval
        self.verify_physical_authority = verify_physical_authority
        self.now = now or (lambda: datetime.now(timezone.utc))
        if (type(receipt) is not dict or set(receipt) != RECEIPT_FIELDS
                or receipt.get("schema") != "stage8_493_operator_one_attempt_approval.v1"
                or receipt.get("production_specification_id") != SPEC
                or receipt.get("active_identity") != IDENTITY
                or receipt.get("account_hash") != plan.account_hash
                or receipt.get("instrument") != plan.instrument
                or receipt.get("symbol") != plan.symbol
                or receipt.get("direction") != plan.direction
                or receipt.get("instrument") != "CNYRUBF"
                or receipt.get("direction") != "LONG"
                or receipt.get("quantity") != 2
                or receipt.get("entry_key") != plan.entry_key
                or receipt.get("stop_key") != plan.stop_key
                or receipt.get("stop_price") != plan.stop_price
                or type(receipt.get("exit_key")) is not str or not receipt["exit_key"]
                or type(receipt.get("entry_reference")) is not str
                or type(receipt.get("fees_rub")) is not str
                or type(receipt.get("risk_budget_rub")) is not str
                or type(receipt.get("slippage_ticks")) is not int
                or type(receipt.get("approved_operations")) is not list
                or set(receipt["approved_operations"]) != ACTIONS
                or len(receipt["approved_operations"]) != len(ACTIONS)
                or not isinstance(receipt.get("approved_from"), str)
                or not isinstance(receipt.get("approved_until"), str)):
            raise Hold("OPERATOR_WRITE_APPROVAL_BINDING_INVALID")
        # Acceptance-only monetary cap. This gate must NOT compare quantity 2
        # to the robot's natural FULL/R15 quantity; production is unchanged.
        try:
            entry = Decimal(receipt["entry_reference"])
            stop_price = Decimal(receipt["stop_price"])
            fees = Decimal(receipt["fees_rub"])
            budget = Decimal(receipt["risk_budget_rub"])
        except (InvalidOperation, ValueError):
            raise Hold("OPERATOR_TEST_MONEY_INVALID") from None
        tick = Decimal("0.001")
        if (not all(x.is_finite() for x in (entry, stop_price, fees, budget))
                or entry <= 0 or stop_price <= 0 or stop_price >= entry
                or entry % tick != 0 or stop_price % tick != 0
                or fees < 0 or budget != Decimal("1000")
                or receipt["slippage_ticks"] < 0):
            raise Hold("OPERATOR_TEST_PRICE_OR_BUDGET_INVALID")
        # CNYRUBF frozen reference tick value = 1 RUB; the operator must
        # independently verify executable broker ticks, fees and slippage.
        scenario = 2 * (entry - stop_price) / tick + 2 * receipt["slippage_ticks"] + fees
        if scenario > budget:
            raise Hold("OPERATOR_TEST_1000_RUB_SCENARIO_EXCEEDED")
        start = _time(receipt["approved_from"])
        stop = _time(receipt["approved_until"])
        if not start < stop or stop-start > timedelta(minutes=30):
            raise Hold("OPERATOR_APPROVAL_WINDOW_INVALID")
        # No account number, keys or raw financial values in this journal.
        self.receipt_sha256 = sha256(json.dumps(receipt, sort_keys=True,
                                              separators=(",", ":")).encode()).hexdigest()

    def __call__(self, action: str, candidate: Plan, key: str) -> None:
        if candidate != self.plan or action not in ACTIONS or type(key) is not str or not key:
            raise Hold("OPERATOR_WRITE_ACTION_BINDING_INVALID")
        if action == "ENTRY" and key != self.plan.entry_key:
            raise Hold("OPERATOR_WRITE_ENTRY_KEY_INVALID")
        if action == "SLTP" and key != self.plan.stop_key:
            raise Hold("OPERATOR_WRITE_STOP_KEY_INVALID")
        if action == "EXIT" and key != self.receipt["exit_key"]:
            raise Hold("OPERATOR_WRITE_EXIT_KEY_INVALID")
        when = self.now()
        if (not isinstance(when, datetime) or when.tzinfo is None
                or when.utcoffset() is None):
            raise Hold("OPERATOR_WRITE_CLOCK_INVALID")
        now = when.astimezone(timezone.utc)
        if not _time(self.receipt["approved_from"]) <= now <= _time(self.receipt["approved_until"]):
            raise Hold("OPERATOR_WRITE_APPROVAL_EXPIRED")
        if self.verify_operator_approval is None or self.verify_physical_authority is None:
            raise Hold("OPERATOR_INDEPENDENT_APPROVAL_AND_PHYSICAL_GATE_REQUIRED")
        # The execution runner must verify actual operator approval (not a
        # boolean from this receipt) and exact matching proposal digest.
        if self.verify_operator_approval(self.receipt) is not True:
            raise Hold("OPERATOR_APPROVAL_NOT_INDEPENDENTLY_VERIFIED")
        physical = self.verify_physical_authority()
        if type(physical) is not dict or set(physical) != PHYSICAL_FIELDS:
            raise Hold("OPERATOR_PHYSICAL_PRECHECK_INVALID")
        if (physical["account_hash"] != self.plan.account_hash
                or physical["task_disabled"] is not True
                or physical["switch_halted"] is not True
                or type(physical["production_process_count"]) is not int
                or physical["production_process_count"] != 0
                or physical["production_lock_free"] is not True
                or physical["write_session_exact_account"] is not True
                or type(physical["broker_snapshot_age_seconds"]) is not int
                or not 0 <= physical["broker_snapshot_age_seconds"] <= 10
                or physical["test_two_contract_margin_and_cash_current"] is not True
                or physical["operator_budget_current_verified"] is not True
                or physical["unresolved_intents_zero"] is not True
                or physical["recovery_approved"] is not True):
            raise Hold("OPERATOR_PHYSICAL_PRECHECK_NOT_PASS")
        existing = [x for x in self.journal.records if x.get("event") == "operator_write_intent"]
        if any(x.get("action") == action or x.get("key_sha256") ==
               sha256(key.encode()).hexdigest() for x in existing):
            raise Hold("OPERATOR_WRITE_INTENT_ALREADY_CONSUMED")
        if action != "ENTRY" and not any(x.get("action") == "ENTRY" for x in existing):
            raise Hold("OPERATOR_ENTRY_INTENT_NOT_PRESENT")
        if action == "SLTP" and any(x.get("action") in {"EXIT", "CANCEL"} for x in existing):
            raise Hold("OPERATOR_STOP_AFTER_RECOVERY_NOT_AUTHORIZED")
        if action == "EXIT" and not any(x.get("action") == "SLTP" for x in existing):
            raise Hold("OPERATOR_PROTECTIVE_INTENT_NOT_PRESENT")
        self.journal.add("operator_write_intent", action=action,
                         key_sha256=sha256(key.encode()).hexdigest(),
                         receipt_sha256=self.receipt_sha256)
