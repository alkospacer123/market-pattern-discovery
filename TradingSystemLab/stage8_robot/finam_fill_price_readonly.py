"""Proposed GET-only FINAM fill-contract diagnostic; never reconciles LIVE state.

Only session authentication, GET account and bounded GET trades are permitted.
An immutable COPY of a historical Stage 8.11 ACK ledger supplies order identity.
No orders URL, SQLite write, production runtime, or trading profile is enabled.
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal, localcontext
from fractions import Fraction
import hashlib
import json
import logging
import os
from pathlib import Path
import re
import sqlite3
from urllib.parse import parse_qs, quote, urlencode, urlsplit

from .broker import compact_client_order_id
from .controlled_real_acceptance import _timestamp
from .execution_grid import require_on_grid
from .finam_api import FinamAPI, FinamError, FinamNotFound
from .margin import parse_rest_decimal_value_object
from .production_broker_state import position_quantities
from .production_runtime import _load_registry
from .state import _validate_acceptance_schema, stage8_11_identity

OFFICIAL_SOURCE_SHA = '52c95c8672542c2f89fbee2a4016774e73a0caa4'
SCHEMA = 'finam_fill_price_readonly_diagnostic.v1'


class FillDiagnosticBlocked(RuntimeError):
    pass


def digest(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def file_digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def contracts(value) -> int:
    number = parse_rest_decimal_value_object(value)
    if number != number.to_integral_value() or number <= 0:
        raise FillDiagnosticBlocked('FILL_QUANTITY_INVALID')
    return int(number)


@dataclass(frozen=True)
class Target:
    account_id: str
    intent_key: str
    order_id: str
    symbol: str
    side: str
    quantity: int
    price_step: Decimal

    def identity(self) -> dict:
        return {'account_sha256': digest(self.account_id), 'intent_key': self.intent_key,
                'order_id_sha256': digest(self.order_id), 'symbol': self.symbol,
                'side': self.side, 'requested_quantity': self.quantity}


def load_ack_copy(path: Path, expected_sha256: str, account_id: str, intent_key: str) -> Target:
    """Read a stable, standalone copy without WAL/shm creation or ledger adoption."""
    path = path.resolve()
    if (not path.is_file() or path.name.lower() in {'stage8-11-acceptance.sqlite3', 'stage8-12-production.sqlite3'}
            or any(Path(str(path)+suffix).exists() for suffix in ('-wal', '-shm'))
            or file_digest(path) != expected_sha256.lower()):
        raise FillDiagnosticBlocked('IMMUTABLE_LEDGER_COPY_REQUIRED')
    if not re.fullmatch(r'stage8\.11\.attempt[2-7]:(USDRUBF|CNYRUBF|GLDRUBF|IMOEXF):entry', intent_key):
        raise FillDiagnosticBlocked('HISTORICAL_ENTRY_KEY_REQUIRED')
    db = sqlite3.connect(path.as_uri()+'?mode=ro&immutable=1', uri=True)
    try:
        _validate_acceptance_schema(db)
        row = db.execute("SELECT value FROM state WHERE key='database_identity'").fetchone()
        if row is None or json.loads(row[0]) != stage8_11_identity(account_id):
            raise FillDiagnosticBlocked('ACK_ACCOUNT_IDENTITY_MISMATCH')
        if db.execute('PRAGMA integrity_check').fetchone() != ('ok',):
            raise FillDiagnosticBlocked('ACK_COPY_INTEGRITY_INVALID')
        row = db.execute('SELECT payload,status,broker_order_id FROM intents WHERE idempotency_key=?',(intent_key,)).fetchone()
        if row is None or row[1] not in {'ACK','PARTIAL_FILL','FILL','RECONCILED','CLOSED'} or not isinstance(row[2],str) or not row[2]:
            raise FillDiagnosticBlocked('DURABLE_ACK_ORDER_ID_REQUIRED')
        payload = json.loads(row[0])
        instrument = intent_key.split(':')[1]
        registry = _load_registry()[instrument]
        if (payload.get('client_order_id') != compact_client_order_id(intent_key)
                or payload.get('symbol') != registry['finam_symbol']
                or payload.get('side') not in {'SIDE_BUY','SIDE_SELL'}
                or payload.get('type') != 'ORDER_TYPE_MARKET' or contracts(payload.get('quantity')) != 1):
            raise FillDiagnosticBlocked('ACK_REQUEST_IDENTITY_INVALID')
        target = Target(account_id,intent_key,row[2],payload['symbol'],payload['side'],1,Decimal(registry['price_step']))
    finally:
        db.close()
    if file_digest(path) != expected_sha256.lower():
        raise FillDiagnosticBlocked('ACK_COPY_CHANGED')
    return target


class ReadonlyFillAPI(FinamAPI):
    """Hard request allowlist, including rejection of inherited order methods."""
    def __init__(self, secret: str, account_id: str, **kwargs):
        super().__init__(secret, **kwargs)
        self.account_id = account_id
        self.account_path = '/v1/accounts/'+quote(account_id,safe='')
        self.bound = False
        self.request_shapes: list[dict] = []

    def _request(self, method, path, payload=None, auth=True, retries=0):
        label = None
        if method == 'POST' and path in {'/v1/sessions','/v1/sessions/details'}:
            label = 'SESSION_AUTHENTICATION'
        elif method == 'GET' and self.bound and path == self.account_path and payload is None:
            label = 'ACCOUNT_READ'
        elif (method == 'GET' and self.bound and path.startswith(self.account_path+'/trades?')
              and urlsplit(path).path == self.account_path+'/trades' and not urlsplit(path).fragment and payload is None):
            params = parse_qs(urlsplit(path).query, strict_parsing=True)
            if set(params)=={'limit','interval.start_time','interval.end_time'} and all(len(v)==1 for v in params.values()):
                start,end = params['interval.start_time'][0],params['interval.end_time'][0]
                if _timestamp(start) < _timestamp(end) and 0 < int(params['limit'][0]) < 2**31:
                    label = 'TRADES_HISTORY_READ'
        if label is None:
            raise FillDiagnosticBlocked('READONLY_REQUEST_FORBIDDEN')
        self.request_shapes.append({'method':method,'resource':label})
        return super()._request(method,path,payload,auth,retries)

    def connect_readonly(self):
        self.create_session()
        details = self.session_details()
        if (not isinstance(details,dict) or details.get('readonly') is not True
                or not isinstance(details.get('account_ids'),list)
                or details['account_ids'].count(self.account_id)!=1):
            raise FillDiagnosticBlocked('EXACT_READONLY_ACCOUNT_BINDING_REQUIRED')
        self.bound = True

    def read_account(self):
        return self._request('GET',self.account_path).body

    def read_history(self, start: str, end: str, limit: int):
        query = urlencode({'limit':limit,'interval.start_time':start,'interval.end_time':end})
        response = self._request('GET',self.account_path+'/trades?'+query)
        if response.status != 200:
            raise FillDiagnosticBlocked('HISTORY_HTTP_STATUS_INVALID')
        return response.body


def analyze_history(response: dict, target: Target, start: str, end: str, limit: int) -> dict:
    """Schema-level identity/coverage proof; no LIVE fill handoff is produced."""
    lower,upper = _timestamp(start),_timestamp(end)
    if lower >= upper or type(limit) is not int or not 0 < limit < 2**31:
        raise FillDiagnosticBlocked('HISTORY_INTERVAL_OR_LIMIT_INVALID')
    if not isinstance(response,dict) or not isinstance(response.get('trades'),list):
        raise FillDiagnosticBlocked('HISTORY_SCHEMA_INVALID')
    rows=response['trades']
    if len(rows)>=limit or any(response.get(k) not in (None,'',0) for k in ('next_cursor','next_page_token')):
        raise FillDiagnosticBlocked('HISTORY_COMPLETENESS_UNPROVEN')
    matched={}
    row_fields=set()
    for row in rows:
        if not isinstance(row,dict): raise FillDiagnosticBlocked('HISTORY_ROW_INVALID')
        row_fields.update(row)
        if row.get('order_id')!=target.order_id: continue
        if (row.get('account_id')!=target.account_id or row.get('symbol')!=target.symbol
                or row.get('side')!=target.side):
            raise FillDiagnosticBlocked('MATCHING_ORDER_FILL_IDENTITY_INVALID')
        # Feed currency is a label, not authority for tick money or conversion.
        currency=row.get('currency')
        if currency not in {'RUB','XXX'}:
            raise FillDiagnosticBlocked('FILL_MONETARY_SEMANTICS_UNPROVEN')
        trade_id=row.get('trade_id')
        if not isinstance(trade_id,str) or not trade_id: raise FillDiagnosticBlocked('FILL_ID_REQUIRED')
        timestamp=_timestamp(row.get('timestamp'))
        if not lower <= timestamp < upper: raise FillDiagnosticBlocked('FILL_OUTSIDE_REQUESTED_INTERVAL')
        price=parse_rest_decimal_value_object(row.get('price'),positive=True)
        require_on_grid(price,target.price_step)
        quantity=contracts(row.get('size'))
        price_text=format(price,'f')
        if '.' in price_text: price_text=price_text.rstrip('0').rstrip('.')
        fact={'trade_id_sha256':digest(trade_id),'quantity':quantity,'price':price_text,
              'utc_seconds':timestamp[0],'nanoseconds':timestamp[1],'account_trade_currency':currency}
        if trade_id in matched and matched[trade_id]!=fact: raise FillDiagnosticBlocked('CONFLICTING_DUPLICATE_FILL')
        matched[trade_id]=fact
    facts=sorted(matched.values(),key=lambda r:r['trade_id_sha256'])
    quantity=sum(r['quantity'] for r in facts)
    if quantity>target.quantity: raise FillDiagnosticBlocked('MATCHING_FILLS_EXCEED_REQUEST_QUANTITY')
    notional=sum((Fraction(r['price'])*r['quantity'] for r in facts),Fraction(0))
    mean=notional/quantity if quantity else None
    display=None
    if mean is not None:
        with localcontext() as context:
            context.prec=34
            display=str(Decimal(mean.numerator)/Decimal(mean.denominator))
    canonical=json.dumps(facts,sort_keys=True,separators=(',',':'))
    return {'history_top_level_fields':sorted(response),'history_row_fields':sorted(row_fields),
            'response_row_count':len(rows),'matched_unique_fills':facts,'matched_quantity':quantity,
            'fill_set_sha256':digest(canonical),
            'quantity_observation':'FULL_REQUEST_MATCHED' if quantity==target.quantity else 'PARTIAL_REQUEST_MATCHED' if quantity else 'NO_MATCHING_FILLS',
            'weighted_price_exact':None if mean is None else {'numerator':str(mean.numerator),'denominator':str(mean.denominator)},
            'weighted_price_decimal_display_only':display,
            'account_trade_currencies':sorted({fact['account_trade_currency'] for fact in facts}),
            'currency_conversion_performed':False,
            'authority_scope':'READONLY_DIAGNOSTIC_ONLY_NO_RUNTIME_HANDOFF'}


def collect(api: ReadonlyFillAPI, target: Target, start: str, end: str, limit: int, *, ledger_sha: str,
            previous: dict | None=None) -> dict:
    if _timestamp(start)>=_timestamp(end) or _timestamp(end)>_timestamp(datetime.now(timezone.utc).isoformat()):
        raise FillDiagnosticBlocked('CLOSED_HISTORICAL_INTERVAL_REQUIRED')
    api.connect_readonly()
    account=api.read_account()
    if not isinstance(account,dict) or account.get('account_id')!=target.account_id:
        raise FillDiagnosticBlocked('ACCOUNT_RESPONSE_IDENTITY_INVALID')
    positions=position_quantities(account)
    query={'start':start,'end_exclusive':end,'limit':limit}
    result={'schema_id':SCHEMA,'official_contract_sha':OFFICIAL_SOURCE_SHA,'target':target.identity(),
            'ledger_copy_sha256':ledger_sha,'query':query,'observed_at':datetime.now(timezone.utc).isoformat(),
            'current_position_quantity':positions.get(target.symbol,0),
            'current_position_is_not_historical_fill_authority':True,
            'real_order_endpoint_calls':0,'live_changes':'NONE','live_production_ready':'NO'}
    try:
        response=api.read_history(start,end,limit)
        result['history']=analyze_history(response,target,start,end,limit)
        result['history_http_status']=200
    except FinamError as exc:
        match=re.search(r'HTTP_(\d{3})',str(exc))
        result.update(history_http_status=int(match[1]) if match else 404 if isinstance(exc,FinamNotFound) else None,
                      history_blocker='HISTORY_READ_UNAVAILABLE',history_error_category=type(exc).__name__)
    except (ValueError,RuntimeError) as exc:
        code=str(exc)
        result.update(history_blocker=code if re.fullmatch(r'[A-Z0-9_]{1,128}',code) else 'HISTORY_CONTRACT_UNPROVEN',
                      history_error_category=type(exc).__name__)
    result['restart_observation']='NOT_TESTED'
    if previous is not None:
        if (previous.get('schema_id')!=SCHEMA or previous.get('target')!=result['target']
                or previous.get('query')!=query or previous.get('ledger_copy_sha256')!=ledger_sha):
            raise FillDiagnosticBlocked('PREVIOUS_DIAGNOSTIC_IDENTITY_MISMATCH')
        old=previous.get('history',{}); new=result.get('history',{})
        result['restart_observation']=('SAME_FULL_FILL_SET_OBSERVED' if old.get('quantity_observation')==new.get('quantity_observation')=='FULL_REQUEST_MATCHED'
            and old.get('fill_set_sha256')==new.get('fill_set_sha256') else 'BLOCKED_CHANGED_OR_INCOMPLETE_HISTORY')
    result['request_shapes']=api.request_shapes
    result['acceptance_status']='DIAGNOSTIC_OBSERVATION_ONLY_NOT_LIVE_ACCEPTANCE'
    return result


def main(argv=None) -> int:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--ledger-copy',type=Path,required=True)
    parser.add_argument('--ledger-sha256',required=True)
    parser.add_argument('--intent-key',required=True)
    parser.add_argument('--start-time',required=True)
    parser.add_argument('--end-time',required=True)
    parser.add_argument('--limit',type=int,default=50)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--previous-report',type=Path)
    parser.add_argument('--previous-sha256')
    args=parser.parse_args(argv)
    # Suppress transport path logging (contains the private account identifier).
    logging.getLogger('TradingSystemLab.stage8_robot.finam_api').setLevel(logging.CRITICAL)
    try:
        if args.output.exists() or args.output.suffix.lower()!='.json' or not args.output.parent.is_dir():
            raise FillDiagnosticBlocked('OUTPUT_MUST_BE_NEW_JSON_IN_EXISTING_SCRATCH_DIRECTORY')
        secret=os.environ.get('FINAM_FILL_READONLY_SECRET','')
        account=os.environ.get('FINAM_FILL_READONLY_ACCOUNT','')
        if not secret or not account: raise FillDiagnosticBlocked('READONLY_CREDENTIALS_REQUIRED')
        target=load_ack_copy(args.ledger_copy,args.ledger_sha256,account,args.intent_key)
        previous=None
        if args.previous_report:
            if not args.previous_sha256 or file_digest(args.previous_report)!=args.previous_sha256.lower():
                raise FillDiagnosticBlocked('PREVIOUS_REPORT_HASH_REQUIRED')
            previous=json.loads(args.previous_report.read_text(encoding='utf-8'))
        report=collect(ReadonlyFillAPI(secret,account),target,args.start_time,args.end_time,args.limit,
                       ledger_sha=args.ledger_sha256.lower(),previous=previous)
        if file_digest(args.ledger_copy)!=args.ledger_sha256.lower(): raise FillDiagnosticBlocked('ACK_COPY_CHANGED')
        # Only this new standalone report is written. No production path is opened.
        with args.output.open('x',encoding='utf-8') as stream: stream.write(json.dumps(report,indent=2,sort_keys=True)+'\n')
        print('FINAM_FILL_READONLY_REPORT_CREATED; LIVE_CHANGES=NONE; REAL_ORDER_ENDPOINT_CALLS=0')
        return 0
    except Exception as exc:
        print('FINAM_FILL_READONLY_DIAGNOSTIC_BLOCKED:'+type(exc).__name__)
        return 1


if __name__=='__main__': raise SystemExit(main())
