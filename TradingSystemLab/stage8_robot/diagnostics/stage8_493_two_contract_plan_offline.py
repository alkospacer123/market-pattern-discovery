"""Stage8 PR #493 item 1.4: offline, non-authorizing use of prior FINAM N4 private report.

Input is a previously observed, hash-pinned private snapshot. It must NOT be
used as a fresh broker, strategy-signal, commission or trade authorization.
No network, credential, order, SQLite or Windows Task access.
"""
from __future__ import annotations

import argparse
from decimal import Decimal, InvalidOperation, ROUND_FLOOR
import hashlib
import json
from pathlib import Path

SPEC = 'PROD_STAGE7_46DB784378797C7FB04636892350AFF21006D71A31F2CED9D4B974EDA2DC36B8'
IDENTITY = 'TRAIL1__N4_01__FULL__R15'
LIVE = '184e8c2b8fa092a606249ff293a4f507160bff29'
N4 = ('USDRUBF', 'CNYRUBF', 'GLDRUBF', 'IMOEXF')

class Blocked(ValueError):
    pass

def require(ok, reason):
    if not ok:
        raise Blocked(reason)

def dec(value, code, positive=False):
    require(type(value) is str and value != '' and value.strip() == value, code)
    try:
        n = Decimal(value)
    except InvalidOperation:
        raise Blocked(code) from None
    require(n.is_finite() and (not positive or n > 0), code)
    return n

def whole(value, code):
    require(type(value) is int and value >= 0, code)
    return value

def units(value, step):
    return (value/step).to_integral_value(rounding=ROUND_FLOOR)

def inspect_report(report, candidate_plans=()):
    require(type(report) is dict and report.get('schema_id') == 'stage8_493_n4_financial_readonly.v1'
            and report.get('production_specification_id') == SPEC
            and report.get('active_identity') == IDENTITY and report.get('live_commit') == LIVE
            and report.get('classification') == 'BROKER_N4_ACCOUNT_ASSET_PARAMS_READONLY_PASS_NO_TRADE_AUTHORITY'
            and report.get('session_readonly') is True
            and report.get('positions_and_orders_zero_twice') is True
            and report.get('finam_trading_order_calls') == 0
            and report.get('real_order_authorization') is False,
            'PRIOR_READONLY_REPORT_AUTHORITY_INVALID')
    acct = report.get('account_sha256')
    require(type(acct) is str and len(acct) == 64
            and all(c in '0123456789abcdef' for c in acct), 'ACCOUNT_SHA_INVALID')
    money = report.get('account_financials')
    require(type(money) is dict and money.get('portfolio_variant') in ('MC', 'FORTS'),
            'ACCOUNT_FINANCIALS_INVALID')
    broker_equity = dec(money.get('equity_broker_reported_rub'), 'EQUITY_INVALID', True)
    unrealized = dec(money.get('unrealized_pnl_broker_reported_rub'), 'UNREALIZED_INVALID')
    cash = dec(money.get('available_cash_broker_reported_rub'), 'CASH_INVALID')
    require(cash >= 0 and broker_equity-unrealized > 0, 'FINANCIAL_BALANCE_INVALID')
    # Only the PREVIOUSLY checked zero subtraction supports this reference.
    # This report never read LIVE SQLite: NO production-equity authority.
    reference_capital = broker_equity-unrealized
    risk = reference_capital * Decimal('0.015')
    assets = report.get('N4')
    require(type(assets) is dict and set(assets) == set(N4), 'N4_MEMBERSHIP_INVALID')
    rows = []
    for name in N4:
        item = assets[name]
        require(type(item) is dict and item.get('finam_symbol') == name+'@RTSX'
                and item.get('account_specific_margin') is True
                and item.get('tick_value_rub_live_broker_verified') is False
                and item.get('trade_lot_size_finam') == 1, 'N4_CONTRACT_INVALID')
        tick = dec(item.get('price_step_finam'), 'TICK_INVALID', True)
        rub = dec(item.get('tick_rub_frozen_moex_reference_not_broker_cash_authority'), 'RUB_TICK_INVALID', True)
        margins = item.get('initial_margin_per_contract_rub_finam')
        require(type(margins) is dict and set(margins) == {'LONG','SHORT'}, 'N4_MARGIN_INVALID')
        for side in ('LONG', 'SHORT'):
            go = dec(margins[side], 'N4_MARGIN_INVALID', True)
            capacity = int(units(cash, go))
            # Exact 2: floor(R15 / (stop_ticks*tick_rub))>=2 AND
            # (floor(cash/GO)==2 OR floor(R15 / loss_per_contract)==2).
            min_ticks = max(1, int(units(risk / Decimal(3), rub)) + 1) if capacity >= 3 else 1
            max_ticks = int(units(risk / Decimal(2), rub))
            eligible = capacity >= 2 and 1 <= min_ticks <= max_ticks
            rows.append({'instrument':name, 'direction':side,
                         'margin_capacity_lots_snapshot_only':capacity,
                         'two_contract_margin_available_snapshot_only':capacity>=2,
                         'possible_exact_two_by_frozen_sizing':eligible,
                         'minimum_stop_distance_ticks_for_exact_two':min_ticks if eligible else None,
                         'maximum_stop_distance_ticks_for_exact_two':max_ticks if eligible else None,
                         'reference_stop_distance_min':str(min_ticks*tick) if eligible else None,
                         'reference_stop_distance_max':str(max_ticks*tick) if eligible else None,
                         'tick_price_units':str(tick),
                         'tick_rub_moex_reference_only':str(rub),
                         'margin_per_contract_rub_snapshot_only':str(go)})
    index = {(r['instrument'],r['direction']):r for r in rows}
    results=[]
    for p in candidate_plans:
        require(type(p) is dict and set(p) == {'instrument','direction','entry','stop',
              'round_trip_fees_rub','adverse_slippage_ticks','operator_budget_rub'},
              'CANDIDATE_PLAN_SCHEMA_INVALID')
        key = (p['instrument'],p['direction'])
        require(key in index, 'CANDIDATE_OUTSIDE_FROZEN_N4')
        row=index[key]
        entry = dec(p['entry'], 'ENTRY_INVALID', True)
        stop = dec(p['stop'], 'STOP_INVALID', True)
        tick = Decimal(row['tick_price_units']); rub = Decimal(row['tick_rub_moex_reference_only'])
        require(entry % tick == 0 and stop % tick == 0 and
                (stop < entry if p['direction']=='LONG' else stop > entry),
                'ENTRY_STOP_GRID_OR_DIRECTION_INVALID')
        stop_ticks = abs(entry-stop)/tick
        loss = stop_ticks*rub
        r15lots = int(units(risk,loss))
        result_qty = min(r15lots,row['margin_capacity_lots_snapshot_only'])
        fees = dec(p['round_trip_fees_rub'], 'FEES_INVALID') if p['round_trip_fees_rub'] is not None else None
        budget = dec(p['operator_budget_rub'], 'BUDGET_INVALID',True) if p['operator_budget_rub'] is not None else None
        slippage = whole(p['adverse_slippage_ticks'], 'SLIPPAGE_INVALID') if p['adverse_slippage_ticks'] is not None else None
        if fees is not None:
            require(fees>=0,'FEES_INVALID')
        total = None if fees is None or slippage is None else 2*(loss+slippage*rub)+fees
        results.append({'instrument':key[0], 'direction':key[1],
                        'r15_quantity_reference':r15lots, 'margin_quantity_snapshot':row['margin_capacity_lots_snapshot_only'],
                        'frozen_quantity_reference':result_qty,
                        'nominal_stop_loss_two_rub':str(2*loss),
                        'scenario_loss_two_plus_fees_rub':str(total) if total is not None else None,
                        'exact_two_reference':result_qty==2,
                        'operator_budget_scenario_pass':total is not None and budget is not None and total <= budget,
                        'live_trade_authorized':False})
    return {'classification':'HISTORICAL_FINAM_N4_TWO_CONTRACT_REFERENCE_ONLY',
            'nominal_r15_cash_rub_prior_snapshot':str(risk),
            'margin_and_risk_reference':rows,'candidate_reference_checks':results,
            'no_current_entry_or_stop_in_broker_report':True,
            'current_realized_equity_sqlite_authority':'NOT_REVALIDATED',
            'current_broker_margin_authority':'STALE_REPORT_NOT_CURRENT',
            'commissions_and_slippage':'NOT_PROVEN_BY_BROKER_REPORT',
            'current_moex_rub_tick_authority':'REFERENCE_ONLY',
            'real_orders':0,'live_authorized':False}

def main(argv=None):
    p=argparse.ArgumentParser(description='Offline FINAM N4 reference; NO BROKER CALLS')
    p.add_argument('--report',type=Path,required=True)
    p.add_argument('--report-sha256',required=True)
    p.add_argument('--candidate-plans',type=Path)
    args=p.parse_args(argv)
    try:
        require(len(args.report_sha256)==64 and all(c in '0123456789abcdefABCDEF' for c in args.report_sha256), 'REPORT_SHA_INVALID')
        path=args.report.resolve(strict=True)
        require('tslaudit' in [x.lower() for x in path.parts] and path.is_file(), 'PRIVATE_REPORT_OUTSIDE_LIVE_REQUIRED')
        raw=path.read_bytes()
        require(hashlib.sha256(raw).hexdigest()==args.report_sha256.lower(), 'PRIVATE_REPORT_HASH_MISMATCH')
        report=json.loads(raw)
        candidates=[] if args.candidate_plans is None else json.loads(args.candidate_plans.read_text('utf-8'))
        require(type(candidates) is list, 'CANDIDATES_LIST_REQUIRED')
        output=inspect_report(report,candidates)
        print(json.dumps(output,sort_keys=True,ensure_ascii=False))
        return 0
    except (OSError,ValueError,TypeError,KeyError):
        print('classification=blocked_historical_n4_reference_not_usable')
        print('real_orders=0')
        return 1

if __name__=='__main__':
    raise SystemExit(main())
