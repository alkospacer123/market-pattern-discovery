"""Operator-only Stage8 #493 CNY LONG two-contract plan. NO LIVE TRANSPORT.

The one-shot acceptance quantity is NOT the frozen production R15 quantity.
This module cannot send orders and never grants production trading rights.
"""
from __future__ import annotations

import argparse
import json
from decimal import Decimal, InvalidOperation, ROUND_FLOOR
from pathlib import Path

SPEC = 'PROD_STAGE7_46DB784378797C7FB04636892350AFF21006D71A31F2CED9D4B974EDA2DC36B8'
IDENTITY = 'TRAIL1__N4_01__FULL__R15'
LIVE_SHA = '184e8c2b8fa092a606249ff293a4f507160bff29'
SYMBOLS = {
    'USDRUBF': ('USDRUBF@RTSX', '0.01', '10'),
    'CNYRUBF': ('CNYRUBF@RTSX', '0.001', '1'),
    'GLDRUBF': ('GLDRUBF@RTSX', '0.1', '0.1'),
    'IMOEXF': ('IMOEXF@RTSX', '0.5', '5'),
}


class Blocked(ValueError):
    pass


def fail(condition, code):
    if not condition:
        raise Blocked(code)


def money(value, code):
    fail(isinstance(value, str), code)
    try:
        number = Decimal(value)
        fail(number.is_finite() and number > 0, code)
        return number
    except (InvalidOperation, ValueError):
        raise Blocked(code) from None


def on_grid(value, tick):
    return value % tick == 0


def validate_plan(plan: dict) -> dict:
    """Values are OPERATOR-ASSERTED, never mistaken for fresh FINAM observations."""
    fail(type(plan) is dict and set(plan) == {
        'schema_id', 'production_specification_id', 'active_identity',
        'production_commit', 'instrument', 'finam_symbol', 'direction',
        'requested_contracts', 'entry_reference_price', 'stop_price',
        'realized_equity_rub', 'available_cash_rub', 'margin_per_contract_rub',
        'maximum_operator_loss_and_cost_rub', 'estimated_total_cost_rub',
        'account_has_zero_positions_and_orders', 'production_task_isolated',
        'kill_switch_halted', 'explicit_operator_trade_authorization',
    }, 'OPERATOR_PLAN_SCHEMA_INVALID')
    fail(plan['schema_id'] == 'stage8_493_sltp_operator_plan.v1'
         and plan['production_specification_id'] == SPEC
         and plan['active_identity'] == IDENTITY
         and plan['production_commit'] == LIVE_SHA, 'FROZEN_PRODUCTION_BINDING_INVALID')
    instrument = plan['instrument']
    fail(type(instrument) is str and instrument == 'CNYRUBF', 'TEST_ONLY_CNYRUBF_APPROVED')
    symbol, tick_text, rub_tick_text = SYMBOLS[instrument]
    fail(plan['finam_symbol'] == symbol, 'FINAM_SYMBOL_NOT_FROZEN')
    fail(plan['direction'] == 'LONG', 'TEST_ONLY_LONG_APPROVED')
    fail(type(plan['requested_contracts']) is int and plan['requested_contracts'] == 2,
         'MULTIFILL_TEST_MUST_BE_EXACTLY_TWO_CONTRACTS')
    # No authority to treat an asserted state as a physical broker/Task proof.
    fail(plan['account_has_zero_positions_and_orders'] is True
         and plan['production_task_isolated'] is True
         and plan['kill_switch_halted'] is True
         and plan['explicit_operator_trade_authorization'] is True,
         'OPERATOR_ASSERTED_PRECONDITIONS_MISSING')
    equity = money(plan['realized_equity_rub'], 'REALIZED_EQUITY_INVALID')
    available = money(plan['available_cash_rub'], 'AVAILABLE_CASH_INVALID')
    margin = money(plan['margin_per_contract_rub'], 'MARGIN_INVALID')
    budget = money(plan['maximum_operator_loss_and_cost_rub'], 'OPERATOR_CASH_LIMIT_INVALID')
    fail(budget == Decimal('1000'), 'ONE_SHOT_TEST_BUDGET_MUST_BE_1000_RUB')
    costs = money(plan['estimated_total_cost_rub'], 'COST_ESTIMATE_INVALID')
    entry = money(plan['entry_reference_price'], 'ENTRY_INVALID')
    stop = money(plan['stop_price'], 'STOP_INVALID')
    tick = Decimal(tick_text)
    tick_rub = Decimal(rub_tick_text)
    fail(on_grid(entry,tick) and on_grid(stop,tick), 'ENTRY_OR_STOP_OFF_FROZEN_TICK_GRID')
    if plan['direction'] == 'LONG':
        fail(stop < entry, 'LONG_STOP_NOT_BELOW_ENTRY')
    else:
        fail(stop > entry, 'SHORT_STOP_NOT_ABOVE_ENTRY')
    qty = plan['requested_contracts']
    loss_per_contract = abs(entry-stop) / tick * tick_rub
    loss = loss_per_contract * qty
    nominal_r15 = equity * Decimal('0.015')
    fail(loss > 0, 'TWO_CONTRACT_STOP_LOSS_INVALID')
    fail(margin * qty <= available, 'TWO_CONTRACTS_EXCEED_MARGIN_CASH')
    fail(loss + costs <= budget, 'OPERATOR_MAX_CASH_LOSS_AND_COST_EXCEEDED')
    # Preserve a diagnostic mirror of the frozen robot sizing. The separate
    # one-shot acceptance has an explicit TWO-contract exception: its quantity
    # is constrained by current margin/cash and the 1000 RUB scenario budget,
    # never by equality to the natural FULL/R15 robot quantity.
    r15_quantity = int((nominal_r15 / loss_per_contract).to_integral_value(rounding=ROUND_FLOOR))
    margin_quantity = int((available / margin).to_integral_value(rounding=ROUND_FLOOR))
    frozen_quantity = min(r15_quantity, margin_quantity)
    # No assertion above establishes fresh account authority, fills or Task isolation.
    # 6% aggregate cap is respected by requiring broker-observed flatness; assertion is NOT proof.
    return {'classification':'OFFLINE_PLAN_VALID_NOT_REAL_ORDER_AUTHORITY',
            'instrument':instrument,'contracts':qty,'stop_tick':tick_text,
            'maximum_reference_initial_loss_rub':str(loss),
            'r15_cash_cap_rub_reference_only':str(nominal_r15),
            'test_quantity_independent_of_robot_sizing':True,
            'approved_test_budget_rub':str(budget),
            'r15_reference_quantity':r15_quantity,
            'margin_reference_quantity':margin_quantity,
            'frozen_reference_final_quantity':frozen_quantity,
            'estimated_total_loss_and_cost_rub':str(loss+costs),
            'broker_freshness':'NOT_VERIFIED','task_isolation':'NOT_VERIFIED',
            'order_endpoint_calls':0,'live_production_ready':False,
            'partial_fill_growth_proven':False}


def main():
    parser = argparse.ArgumentParser(description='Offline operator SLTP plan gate: order-incapable')
    parser.add_argument('--plan', type=Path, required=True)
    parser.add_argument('--execute', action='store_true')
    args = parser.parse_args()
    if args.execute:
        print('CLASSIFICATION=BLOCKED_NO_REAL_ORDER_TRANSPORT')
        return 1
    try:
        plan = json.loads(args.plan.read_text(encoding='utf-8'))
        result = validate_plan(plan)
    except (Blocked, OSError, ValueError, TypeError):
        print('CLASSIFICATION=BLOCKED_OFFLINE_OPERATOR_PLAN_INVALID')
        return 1
    print(json.dumps(result,sort_keys=True))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
