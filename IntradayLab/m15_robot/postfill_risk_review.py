"""M15-only post-fill nominal R15/GO risk REVIEW; no broker/order API.

The original R15 sizing is performed before submitting an entry. This pure
post-fill review detects changes to initial nominal risk after *actual*
AccountTrade VWAP becomes known, including off-tick weighted average.
A flagged overrun NEVER authorizes a new entry, a stop modification, or
an emergency exit: those require separate FINAM-authoritative gates.

No FINAM client, token, Task, trading state, H1 import or live authorization.
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from fractions import Fraction

from .broker_risk_readonly import M15AccountSnapshot
from .cashflow_reconcile_gate import CashflowReconciliation
from .grid_risk import ContractAuthority, SizedOrder, require_on_grid
from .initial_stop_from_fills import M15InitialStopProposal
from .spec import MAX_NOMINAL_INITIAL_RISK, RISK_FRACTION


class M15PostFillRiskError(RuntimeError):
    pass


@dataclass(frozen=True)
class M15PostFillRiskReview:
    matched_broker_quantity: int
    exact_vwap: Fraction
    executable_stop: Decimal
    actual_initial_loss_rub: Fraction
    initial_risk_budget_rub: Fraction
    full_margin_requirement_rub: Decimal
    result: str
    margin_source: str = "PRE_ENTRY_READONLY_M15_SNAPSHOT"
    realized_equity_source: str = "CASHFLOW_RECONCILIATION_OFFLINE"
    commission_verified: bool = False
    stop_broker_acknowledged: bool = False
    order_submission_authorized: bool = False
    new_entries_authorized: bool = False
    live_authorized: bool = False


def review_initial_risk_after_broker_fill(
    *, proposal: M15InitialStopProposal,
    initial_order_sizing: SizedOrder,
    contract: ContractAuthority,
    pre_entry_account: M15AccountSnapshot,
    capital: CashflowReconciliation,
    pre_entry_committed_nominal_risk: Decimal,
) -> M15PostFillRiskReview:
    """Compare actual broker VWAP and sized/filled quantity to frozen R15.

    pre_entry_account is an externally authenticated read-only snapshot
    captured BEFORE the original entry attempt; FINAM available cash AFTER a
    fill must not be used as though no margin had yet been reserved.
    This function cannot verify timing itself; production admission requires
    a separately durable broker-snapshot proof.
    """
    if (not isinstance(proposal, M15InitialStopProposal)
            or not isinstance(initial_order_sizing, SizedOrder)
            or not isinstance(contract, ContractAuthority)
            or not isinstance(pre_entry_account, M15AccountSnapshot)
            or not isinstance(capital, CashflowReconciliation)):
        raise M15PostFillRiskError("M15_POSTFILL_EVIDENCE_REQUIRED")
    if (proposal.live_authorized or proposal.order_submission_authorized
            or proposal.broker_stop_acknowledged or proposal.broker_position_protected
            or proposal.draft.live_authorized or proposal.draft.submitted
            or capital.runtime_r15_authorized or capital.live_authorized
            or proposal.source != "BOUNDED_FINAM_GET_EVIDENCE_OFFLINE"
            or proposal.draft.kind != "PROTECTIVE_STOP_INSTALL"
            or proposal.draft.payload.get("quantity_sl") != {"value": "100"}):
        raise M15PostFillRiskError("M15_POSTFILL_OFFLINE_ONLY")
    contract.validate()
    if (type(proposal.matched_quantity) is not int or proposal.matched_quantity <= 0
            or type(initial_order_sizing.final_quantity) is not int
            or proposal.matched_quantity > initial_order_sizing.final_quantity
            or initial_order_sizing.reason != "OK"):
        raise M15PostFillRiskError("M15_POSTFILL_ORDER_QUANTITY_UNPROVEN")
    if (not isinstance(proposal.weighted_entry_exact, Fraction)
            or proposal.weighted_entry_exact <= 0
            or not isinstance(proposal.stop_price, Decimal)
            or proposal.draft.payload.get("sl_price") !=
                {"value": str(proposal.stop_price)}):
        raise M15PostFillRiskError("M15_POSTFILL_STOP_OR_VWAP_INVALID")
    try:
        stop = require_on_grid(proposal.stop_price, contract.price_step)
    except (ValueError, TypeError, ArithmeticError):
        raise M15PostFillRiskError("M15_POSTFILL_STOP_OFF_TICK") from None
    side = proposal.draft.payload.get("side")
    if side not in {"SIDE_SELL", "SIDE_BUY"}:
        raise M15PostFillRiskError("M15_POSTFILL_CLOSING_SIDE_INVALID")
    is_long = side == "SIDE_SELL"
    vwap, stop_exact = proposal.weighted_entry_exact, Fraction(stop)
    if (is_long and not stop_exact < vwap
            or not is_long and not stop_exact > vwap):
        raise M15PostFillRiskError("M15_POSTFILL_STOP_WRONG_SIDE")
    if (not isinstance(pre_entry_committed_nominal_risk, Decimal)
            or not pre_entry_committed_nominal_risk.is_finite()
            or pre_entry_committed_nominal_risk < 0
            or not isinstance(capital.proposed_realized_equity, Decimal)
            or not capital.proposed_realized_equity.is_finite()
            or capital.proposed_realized_equity <= 0
            or capital.proposed_realized_equity !=
                pre_entry_account.broker_equity_minus_unrealized):
        raise M15PostFillRiskError("M15_POSTFILL_PRE_ENTRY_CAPITAL_UNPROVEN")
    if (not isinstance(pre_entry_account.available_cash, Decimal)
            or not pre_entry_account.available_cash.is_finite()
            or pre_entry_account.available_cash < 0):
        raise M15PostFillRiskError("M15_POSTFILL_PRE_ENTRY_MARGIN_UNPROVEN")
    tick_distance = abs(vwap - stop_exact) / Fraction(contract.price_step)
    per_contract_loss = tick_distance * Fraction(contract.tick_value)
    total_risk = per_contract_loss * proposal.matched_quantity
    equity = Fraction(capital.proposed_realized_equity)
    committed = Fraction(pre_entry_committed_nominal_risk)
    risk_budget = min(equity * Fraction(RISK_FRACTION),
                      max(Fraction(0), equity * Fraction(MAX_NOMINAL_INITIAL_RISK) - committed))
    margin_per_contract = (contract.long_initial_margin if is_long
                           else contract.short_initial_margin)
    required_margin = margin_per_contract * proposal.matched_quantity
    # Even a confirmed post-fill overrun MUST NOT change the position or its
    # protective stop automatically in this code-only review.
    capacity_ok = (total_risk <= risk_budget
                   and required_margin <= pre_entry_account.available_cash
                   and proposal.matched_quantity % contract.trade_lot_size == 0)
    return M15PostFillRiskReview(
        matched_broker_quantity=proposal.matched_quantity,
        exact_vwap=vwap, executable_stop=stop,
        actual_initial_loss_rub=total_risk, initial_risk_budget_rub=risk_budget,
        full_margin_requirement_rub=required_margin,
        result=("WITHIN_NOMINAL_R15_GO_OFFLINE_ONLY" if capacity_ok
                else "POSTFILL_RISK_OR_MARGIN_OVERRUN_REQUIRES_BROKER_REVIEW"),
    )
