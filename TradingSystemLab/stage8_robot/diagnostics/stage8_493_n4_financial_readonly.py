"""PR #493: isolated FINAM N4 financial GET-only evidence (NOT trade authority).

Run only behind the hash-pinned, previously proven post-isolation gate.
Writes one sanitized JSON file outside production. Neither fees nor realized
production equity can be inferred merely from GET account/asset responses.
"""
from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
from decimal import Decimal
import hashlib
import json
import logging
import os
from pathlib import Path
import re
import subprocess
import sys
from urllib.parse import quote, urlencode

SPEC = 'PROD_STAGE7_46DB784378797C7FB04636892350AFF21006D71A31F2CED9D4B974EDA2DC36B8'
IDENTITY = 'TRAIL1__N4_01__FULL__R15'
LIVE_SHA = '184e8c2b8fa092a606249ff293a4f507160bff29'
N4 = ('USDRUBF', 'CNYRUBF', 'GLDRUBF', 'IMOEXF')


class Blocked(Exception):
    pass


def require(ok, code):
    if not ok:
        raise Blocked(code)


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def read_registry(checkout):
    path = checkout / 'TradingSystemLab/stage8_robot/production_instrument_registry.csv'
    with path.open(encoding='utf-8', newline='') as stream:
        rows = list(csv.DictReader(stream))
    result = {row.get('research_symbol'): row for row in rows}
    require(len(rows) == 4 and set(result) == set(N4), 'FROZEN_REGISTRY_MEMBERSHIP_INVALID')
    for name in N4:
        row = result[name]
        require(row.get('finam_symbol') == name + '@RTSX' and row.get('mic') == 'RTSX'
                and row.get('binding_status') == 'AUTHENTICATED_REAL_READONLY'
                and row.get('trading_status') == 'TRADABLE'
                and row.get('quantity_granularity') == '1', 'FROZEN_REGISTRY_BINDING_INVALID')
    return result


def financial_account(account, account_id, positions, order_views, portfolio_authority, parse_decimal):
    require(isinstance(account, dict) and account.get('account_id') == account_id
            and account.get('status') in {'ACCOUNT_ACTIVE', 'ACCOUNT_STATUS_ACTIVE'}, 'FINAM_ACCOUNT_INVALID')
    require(not positions(account), 'BROKER_POSITION_NOT_FLAT')
    # These three account fields are explicitly distinct: equity != realized equity.
    equity = parse_decimal(account.get('equity'))
    unrealized = parse_decimal(account.get('unrealized_profit'))
    available = portfolio_authority(account)
    require(equity > 0 and available.available_cash >= 0, 'ACCOUNT_FINANCIAL_VALUES_INVALID')
    return {'equity_broker_reported_rub': str(equity),
            'unrealized_pnl_broker_reported_rub': str(unrealized),
            'available_cash_broker_reported_rub': str(available.available_cash),
            'portfolio_variant': available.variant}


def verify_orders(response, order_views):
    require(not any(order.active for order in order_views(response)), 'BROKER_ACTIVE_ORDERS_PRESENT')


def asset_economics(name, asset, params, row, parse_margin, parse_decimal):
    symbol = row['finam_symbol']
    require(isinstance(asset, dict) and asset.get('ticker') == name
            and asset.get('mic') == 'RTSX', 'ASSET_IDENTITY_INVALID')
    require(isinstance(params, dict) and params.get('symbol') == symbol
            and isinstance(params.get('account_id'), str)
            and params.get('is_tradable') == {'value': True}, 'ASSET_PARAMS_ACCOUNT_OR_STATUS_INVALID')
    decimals = asset.get('decimals')
    rawstep = asset.get('min_step')
    require(type(decimals) is int and 0 <= decimals <= 12
            and type(rawstep) is str and re.fullmatch(r'[1-9][0-9]*', rawstep) is not None,
            'FINAM_ASSET_PRICE_STEP_INVALID')
    step = Decimal(rawstep) / (Decimal(10) ** decimals)
    require(step == Decimal(row['price_step']), 'FINAM_STEP_FROZEN_REFERENCE_MISMATCH')
    lot = params.get('trade_lot_size')
    require(type(lot) is str and re.fullmatch(r'[1-9][0-9]*', lot) is not None,
            'FINAM_TRADE_LOT_NOT_PROVEN')
    require(int(lot) == int(row['quantity_granularity']), 'FINAM_TRADE_LOT_MISMATCH')
    contract_size = parse_decimal(asset.get('lot_size'))
    require(contract_size > 0, 'FINAM_CONTRACT_SIZE_INVALID')
    margins = {'LONG': parse_margin(params, 'LONG'), 'SHORT': parse_margin(params, 'SHORT')}
    require(all(v > 0 for v in margins.values()), 'FINAM_DIRECTIONAL_MARGIN_INVALID')
    return {'finam_symbol': symbol, 'price_step_finam': str(step),
            'tick_rub_frozen_moex_reference_not_broker_cash_authority': row['tick_value'],
            'trade_lot_size_finam': int(lot), 'contract_size_finam': str(contract_size),
            'initial_margin_per_contract_rub_finam': {side: str(value) for side, value in margins.items()},
            'account_specific_margin': True, 'tick_value_rub_live_broker_verified': False}


def safe_output(path, runtime, checkout):
    require(not path.exists() and path.suffix.lower() == '.json'
            and path.parent.is_dir() and not path.is_symlink(), 'CREATE_ONLY_OUTPUT_REQUIRED')
    # Fail on any symlink/reparse ancestor, including Windows junction metadata.
    here = path.parent
    while True:
        st = here.lstat()
        require(not here.is_symlink() and not (getattr(st, 'st_file_attributes', 0) & 0x400),
                'OUTPUT_REPARSE_ANCESTOR_FORBIDDEN')
        if here == here.parent:
            break
        here = here.parent
    out = path.absolute()
    for forbidden in (runtime, checkout):
        try:
            out.relative_to(forbidden.absolute())
        except ValueError:
            continue
        raise Blocked('OUTPUT_INSIDE_LIVE_OR_CHECKOUT_FORBIDDEN')
    # Strongly isolate output under an already-existing operator audit directory.
    require('tslaudit' in [part.lower() for part in out.parts], 'EXTERNAL_AUDIT_OUTPUT_REQUIRED')
    return out


def collect(root, checkout, secret, account, output):
    require(bool(secret) and bool(account), 'EXACT_READONLY_CREDENTIAL_REQUIRED')
    require(subprocess.check_output(['git', '-C', str(checkout), 'rev-parse', 'HEAD'],
                                   text=True, stderr=subprocess.DEVNULL).strip() == LIVE_SHA,
            'LIVE_CHECKOUT_SHA_MISMATCH')
    output = safe_output(output, root, checkout)
    registry = read_registry(checkout)
    sys.path.insert(0, str(checkout))
    from TradingSystemLab.stage8_robot.finam_api import FinamAPI
    from TradingSystemLab.stage8_robot.margin import (portfolio_authority,
        directional_initial_margin, parse_rest_decimal_value_object)
    from TradingSystemLab.stage8_robot.production_broker_state import position_quantities, order_views
    from stage8_493_post_isolation_broker_readonly import local_gate
    logging.getLogger('TradingSystemLab.stage8_robot.finam_api').setLevel(logging.CRITICAL)
    apath = '/v1/accounts/' + quote(account, safe='')
    aquery = urlencode({'account_id': account})
    asset_paths = {name: ('/v1/assets/' + quote(registry[name]['finam_symbol'], safe='') + '?' + aquery)
                   for name in N4}
    params_paths = {name: ('/v1/assets/' + quote(registry[name]['finam_symbol'], safe='')
                           + '/params?' + aquery) for name in N4}
    allow = {apath: 'ACCOUNT', apath + '/orders': 'ORDERS'}
    for name in N4:
        allow[asset_paths[name]] = 'ASSET_' + name
        allow[params_paths[name]] = 'PARAMS_' + name

    class StrictFinam(FinamAPI):
        def __init__(self):
            super().__init__(secret)
            self.bound = False
            self.trace = []
        def _request(self, method, path, payload=None, auth=True, retries=0):
            if method == 'POST' and path in {'/v1/sessions', '/v1/sessions/details'}:
                label = 'SESSION_AUTH'
            elif method == 'GET' and self.bound and payload is None and path in allow:
                label = allow[path]
            else:
                raise Blocked('FINAM_TRADING_OR_NONALLOWLIST_REQUEST_FORBIDDEN')
            self.trace.append(label)
            return super()._request(method, path, payload, auth, retries)

    def isolation():
        local_gate(root, account)

    isolation()
    api = StrictFinam()
    api.create_session()
    details = api.session_details()
    require(isinstance(details, dict) and details.get('readonly') is True
            and isinstance(details.get('account_ids'), list)
            and details['account_ids'].count(account) == 1, 'SESSION_NOT_EXACT_READONLY_ACCOUNT')
    api.bound = True
    expected = ['SESSION_AUTH', 'SESSION_AUTH']
    before = utc_now()
    isolation()
    a1 = api.account(account)
    o1 = api.orders(account)
    verify_orders(o1, order_views)
    f1 = financial_account(a1, account, position_quantities, order_views,
                           portfolio_authority, parse_rest_decimal_value_object)
    expected += ['ACCOUNT', 'ORDERS']
    instruments = {}
    for name in N4:
        isolation()
        asset = api._request('GET', asset_paths[name]).body
        params = api._request('GET', params_paths[name]).body
        require(params.get('account_id') == account, 'ASSET_PARAMS_ACCOUNT_MISMATCH')
        instruments[name] = asset_economics(name, asset, params, registry[name],
                                             directional_initial_margin, parse_rest_decimal_value_object)
        expected += ['ASSET_' + name, 'PARAMS_' + name]
    isolation()
    a2 = api.account(account)
    o2 = api.orders(account)
    verify_orders(o2, order_views)
    f2 = financial_account(a2, account, position_quantities, order_views,
                           portfolio_authority, parse_rest_decimal_value_object)
    expected += ['ACCOUNT', 'ORDERS']
    isolation()
    require(api.trace == expected, 'READONLY_REQUEST_SEQUENCE_INVALID')
    require(f1 == f2, 'BROKER_FINANCIAL_SNAPSHOTS_CHANGED')
    report = {'schema_id':'stage8_493_n4_financial_readonly.v1',
              'classification':'BROKER_N4_ACCOUNT_ASSET_PARAMS_READONLY_PASS_NO_TRADE_AUTHORITY',
              'observed_start_utc':before, 'observed_end_utc':utc_now(),
              'account_sha256':hashlib.sha256(account.encode()).hexdigest(),
              'live_commit':LIVE_SHA, 'production_specification_id':SPEC, 'active_identity':IDENTITY,
              'account_financials':f2, 'N4':instruments,
              'session_readonly':True, 'positions_and_orders_zero_twice':True,
              'realized_equity_r15_broker_only_unproven':True,
              'external_cash_flows_runtime_reconciliation':'NOT_READ_OR_VERIFIED',
              'exact_two_contract_R15_eligibility':'NOT_VERIFIED',
              'fees_and_round_trip_commissions':'NOT_VERIFIED_REQUIRES_CLIENT_TARIFF',
              'slippage_gap_cash_limit':'NOT_SPECIFIED',
              'real_sltp_multifill_dynamic_coverage':'NOT_TESTED',
              'finam_trading_order_calls':0, 'no_live_mutation':True,
              'real_order_authorization':False, 'v2_production_ready':False,
              'request_labels':expected}
    # Exclusive creation with report deliberately kept only in external operator scratch.
    with output.open('x', encoding='utf-8') as stream:
        json.dump(report, stream, ensure_ascii=False, indent=2, sort_keys=True)
        stream.write('\n')
    print('CLASSIFICATION=BROKER_N4_ACCOUNT_ASSET_PARAMS_READONLY_PASS_NO_TRADE_AUTHORITY')
    print('REPORT_SHA256=' + hashlib.sha256(output.read_bytes()).hexdigest().upper())
    print('FEES_R15_AND_REAL_MULTIFILL=NOT_VERIFIED')
    print('REAL_ORDER_AUTHORIZED=NO')


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--runtime-root', type=Path, required=True)
    p.add_argument('--checkout', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    args = p.parse_args()
    try:
        collect(args.runtime_root.absolute(), args.checkout.absolute(),
                os.environ.get('stage8_493_readonly_secret', ''),
                os.environ.get('stage8_493_readonly_account', ''), args.output)
        return 0
    except Exception as exc:
        print('CLASSIFICATION=BLOCKED:' + (str(exc) if isinstance(exc, Blocked) else 'READONLY_FINANCIAL_OBSERVATION_FAILED'))
        print('REAL_ORDER_AUTHORIZED=NO')
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
