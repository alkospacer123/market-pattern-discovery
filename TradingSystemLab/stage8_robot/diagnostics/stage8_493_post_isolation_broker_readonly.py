"""Post-Task-isolation FINAM account/orders: exclusively real READONLY API calls."""
from __future__ import annotations

import argparse
import hashlib
import json
import logging
import os
import subprocess
import sys
import time
from pathlib import Path
from urllib.parse import quote

SPEC = 'PROD_STAGE7_46DB784378797C7FB04636892350AFF21006D71A31F2CED9D4B974EDA2DC36B8'
IDENTITY = 'TRAIL1__N4_01__FULL__R15'
LIVE_SHA = '184e8c2b8fa092a606249ff293a4f507160bff29'

class Blocked(Exception):
    pass

def require(ok: bool, code: str) -> None:
    if not ok:
        raise Blocked(code)

def local_gate(root: Path, account: str) -> None:
    switch = json.loads((root / 'safety/stage8-trading-kill-switch.json').read_text(encoding='utf-8'))
    hb = json.loads((root / 'diagnostics/stage8-12-4-production-heartbeat.json').read_text(encoding='utf-8'))
    require(switch.get('schema_id') == 'stage8_trading_kill_switch.v1' and
            switch.get('production_specification_id') == SPEC and
            switch.get('state') == 'HALTED', 'SWITCH_NOT_HALTED')
    require(hb.get('schema_id') == 'stage8_12_4_production_heartbeat.v1' and
            hb.get('production_specification_id') == SPEC and
            hb.get('active_identity') == IDENTITY and
            hb.get('accepted_code_commit') == LIVE_SHA and
            hb.get('account_hash') == hashlib.sha256(account.encode()).hexdigest(),
            'LAST_HEARTBEAT_IDENTITY_MISMATCH')
    # Intentionally no fresh-heartbeat check: production is stopped at this stage.
    require(all(type(hb.get(k)) is int and hb[k] == 0 for k in
                ('open_position_count','unresolved_intent_count','active_protective_stop_count')),
            'LAST_HEARTBEAT_EXPOSURE_NONZERO')

def probe(root: Path, checkout: Path, secret: str, account: str, delay: int = 2) -> None:
    require(bool(secret) and bool(account), 'READONLY_CREDENTIAL_UNAVAILABLE')
    require(subprocess.check_output(['git','-C',str(checkout),'rev-parse','HEAD'],
            stderr=subprocess.DEVNULL, text=True).strip() == LIVE_SHA,
            'LIVE_CODE_COMMIT_MISMATCH')
    sys.path.insert(0, str(checkout))
    logging.getLogger('TradingSystemLab.stage8_robot.finam_api').setLevel(logging.CRITICAL)
    from TradingSystemLab.stage8_robot.finam_api import FinamAPI
    from TradingSystemLab.stage8_robot.production_broker_state import position_quantities, order_views
    path = '/v1/accounts/' + quote(account, safe='')

    class StrictReadOnly(FinamAPI):
        def __init__(self, secret: str):
            super().__init__(secret)
            self.bound = False
            self.trace: list[str] = []
        def _request(self, method, endpoint, payload=None, auth=True, retries=0):
            if method == 'POST' and endpoint in {'/v1/sessions','/v1/sessions/details'}:
                label = 'SESSION'
            elif self.bound and method == 'GET' and payload is None and endpoint in {path, path+'/orders'}:
                label = 'ACCOUNT' if endpoint == path else 'ORDERS'
            else:
                raise Blocked('FINAM_ENDPOINT_FORBIDDEN')
            self.trace.append(label)
            return super()._request(method, endpoint, payload, auth, retries)

    local_gate(root, account)
    api = StrictReadOnly(secret)
    api.create_session()
    details = api.session_details()
    require(isinstance(details, dict) and details.get('readonly') is True and
            isinstance(details.get('account_ids'), list) and
            details['account_ids'].count(account) == 1, 'FINAM_READONLY_ACCOUNT_BINDING_INVALID')
    api.bound = True
    print('FINAM_SESSION=EXACT_READONLY_ACCOUNT_BOUND')
    for n in (1,2):
        local_gate(root, account)
        a = api.account(account)
        orders_response = api.orders(account)
        require(isinstance(a,dict) and a.get('account_id') == account and
                a.get('status') in {'ACCOUNT_ACTIVE','ACCOUNT_STATUS_ACTIVE'},
                'BROKER_ACCOUNT_INVALID')
        pos = position_quantities(a)
        orders = order_views(orders_response)
        active = sum(int(o.active) for o in orders)
        print(f'SNAPSHOT_{n}_NONZERO_POSITIONS={len(pos)}')
        print(f'SNAPSHOT_{n}_ACTIVE_ORDERS={active}')
        print(f'SNAPSHOT_{n}_ORDERS_SCANNED={len(orders)}')
        require(len(pos) == 0 and active == 0, 'BROKER_NOT_FLAT')
        if n == 1:
            time.sleep(delay)
    require(api.trace == ['SESSION','SESSION','ACCOUNT','ORDERS','ACCOUNT','ORDERS'],
            'BROKER_REQUEST_TRACE_INVALID')
    local_gate(root, account)
    print('POST_ISOLATION_BROKER_FLAT=PASS')
    print('NO_ORDER_OR_CANCEL=YES')

def main() -> int:
    p=argparse.ArgumentParser()
    p.add_argument('--runtime-root', type=Path, required=True)
    p.add_argument('--checkout', type=Path, required=True)
    args=p.parse_args()
    print('=== stage8 #493 broker post isolation READONLY; no heartbeat freshness ===')
    try:
        probe(args.runtime_root, args.checkout,
              os.environ.get('stage8_493_readonly_secret',''),
              os.environ.get('stage8_493_readonly_account',''))
        return 0
    except Exception as exc:
        print('POST_ISOLATION_BROKER=BLOCKED:' + (str(exc) if isinstance(exc,Blocked) else 'UNEXPECTED'))
        return 1

if __name__ == '__main__':
    raise SystemExit(main())
