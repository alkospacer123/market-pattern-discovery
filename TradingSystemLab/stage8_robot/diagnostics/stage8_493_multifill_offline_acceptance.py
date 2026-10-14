"""Operator acceptance rehearsal for Stage 8 #493: OFFLINE ONLY.

Strict synthetic events, durable scratch journal, no FinamAPI, no production StateStore,
no trading credentials, no network, no Task changes. SIMULATION NEVER GRANTS TRADE AUTHORITY.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from decimal import Decimal, InvalidOperation
import sqlite3
import sys

SCHEMA = 'stage8_493_offline_multifill_acceptance.v1'
SPEC = 'PROD_STAGE7_46DB784378797C7FB04636892350AFF21006D71A31F2CED9D4B974EDA2DC36B8'
IDENTITY = 'TRAIL1__N4_01__FULL__R15'
MAX_QTY = 2
TICKS = {'USDRUBF@RTSX':'0.01', 'CNYRUBF@RTSX':'0.001', 'GLDRUBF@RTSX':'0.1', 'IMOEXF@RTSX':'0.5'}
DATABASE_NAME = 'stage8_493_synthetic_multifill.sqlite3'

class Blocked(RuntimeError):
    pass

def check(ok: bool, code: str) -> None:
    if not ok:
        raise Blocked(code)

def canonical(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=True, allow_nan=False)

def digest(value: object) -> str:
    return hashlib.sha256(canonical(value).encode('ascii')).hexdigest()

def strict_obj(obj: dict, fields: set[str], code: str) -> None:
    check(type(obj) is dict and set(obj) == fields, code)

def isolated_db(scratch_root: Path) -> Path:
    check(scratch_root.is_absolute() and scratch_root.exists() and scratch_root.is_dir(), 'SCRATCH_ROOT_INVALID')
    resolved = scratch_root.resolve(strict=True)
    check(resolved == scratch_root and not scratch_root.is_symlink(), 'SCRATCH_ALIAS_NOT_ALLOWED')
    parts = {x.lower() for x in scratch_root.parts}
    check('runtime' not in parts and 'production' not in parts and 'state' not in parts,
          'LIVE_RUNTIME_OR_PRODUCTION_PATH_FORBIDDEN')
    database = scratch_root / DATABASE_NAME
    check(not database.is_symlink(), 'DATABASE_SYMLINK_FORBIDDEN')
    return database


def fresh_state() -> dict:
    return dict(entry_key=None, entry_order=None, entry_posts=0, stop_key=None,
                stop_order=None, stop_posts=0, stop_active=False, quantity=0,
                fills=[], partial_observed=False, growth_observed=False,
                stop_at_one=False, stop_at_two=False, terminal=False,
                halted=False, outcome='INCOMPLETE')


def positive_on_grid(price: object, symbol: str) -> bool:
    if type(price) is not str or symbol not in TICKS:
        return False
    try:
        value=Decimal(price)
        tick=Decimal(TICKS[symbol])
        return value.is_finite() and value > 0 and value % tick == 0
    except (InvalidOperation, ValueError):
        return False


def validate_fills(fills: list, account_id: str, order_id: str, symbol: str,
                   direction: str, quantity: int) -> None:
    check(type(fills) is list and 0 < len(fills) <= MAX_QTY, 'SYNTHETIC_FILL_LIST_INVALID')
    side = 'SIDE_BUY' if direction == 'LONG' else 'SIDE_SELL'
    seen = set()
    total = 0
    for f in fills:
        strict_obj(f, {'fill_id','account_id','order_id','symbol','side','quantity','price'}, 'SYNTHETIC_FILL_SCHEMA_INVALID')
        check(type(f['fill_id']) is str and f['fill_id'] and f['fill_id'] not in seen, 'DUPLICATE_FILL_ID')
        check(f['account_id'] == account_id and f['order_id'] == order_id and f['symbol'] == symbol
              and f['side'] == side, 'SYNTHETIC_FILL_IDENTITY_INVALID')
        check(type(f['quantity']) is int and 1 <= f['quantity'] <= MAX_QTY, 'SYNTHETIC_FILL_QTY_INVALID')
        check(positive_on_grid(f['price'], symbol), 'SYNTHETIC_FILL_PRICE_INVALID')
        # Every real price and its monetary identity must later be independently authenticated.
        # This check only binds a synthetic trace to an immutable expected fill identity.
        total += f['quantity']; seen.add(f['fill_id'])
    check(total == quantity and quantity <= MAX_QTY, 'SYNTHETIC_FILL_QUANTITY_MISMATCH')


def advance(st: dict, event: dict, *, account_id: str, symbol: str,
            direction: str, stop_price: str) -> dict:
    """Pure replay. A failure is fail closed and never makes an API request."""
    check(not st['terminal'] and not st['halted'], 'TERMINAL_OR_HALTED_REPLAY_FORBIDDEN')
    check(type(event) is dict and type(event.get('kind')) is str, 'EVENT_SCHEMA_INVALID')
    e = dict(st); kind = event['kind']
    if kind == 'entry_intent':
        strict_obj(event, {'kind','intent_key','requested_quantity'}, 'ENTRY_INTENT_SCHEMA_INVALID')
        check(e['entry_key'] is None and type(event['intent_key']) is str and bool(event['intent_key'])
              and type(event['requested_quantity']) is int and event['requested_quantity'] == MAX_QTY,
              'ENTRY_INTENT_INVALID')
        e['entry_key'] = event['intent_key']
    elif kind == 'entry_post_ack':
        strict_obj(event, {'kind','intent_key','order_id'}, 'ENTRY_ACK_SCHEMA_INVALID')
        check(e['entry_key'] and not e['entry_order'] and e['entry_posts'] == 0
              and event['intent_key'] == e['entry_key'] and type(event['order_id']) is str and event['order_id'],
              'ENTRY_POST_UNAUTHORIZED_OR_DUPLICATE')
        e.update(entry_order=event['order_id'], entry_posts=1)
    elif kind == 'position':
        strict_obj(event, {'kind','quantity','fills'}, 'POSITION_SCHEMA_INVALID')
        qty = event['quantity']
        check(e['entry_order'] and type(qty) is int and 1 <= qty <= MAX_QTY,
              'POSITION_MISSING_ENTRY_OR_QTY_INVALID')
        validate_fills(event['fills'], account_id, e['entry_order'], symbol, direction, qty)
        old = {r['fill_id']: r for r in e['fills']}
        now = {r['fill_id']: r for r in event['fills']}
        check(all(now.get(k) == v for k,v in old.items()), 'RETAINED_FILL_CHANGED_OR_DISAPPEARED')
        check(qty >= e['quantity'], 'POSITION_DECREASE_REQUIRES_SEPARATE_RECOVERY')
        if e['quantity'] == 0:
            check(qty == 1, 'IMMEDIATE_TWO_CONTRACT_FILL_NOT_GROWTH_PROOF')
            e['partial_observed'] = True
        elif e['quantity'] == 1 and qty == 2:
            check(e['stop_active'] and e['stop_at_one'], 'EXPOSURE_GREW_BEFORE_STOP_ACTIVE')
            e['growth_observed'] = True
            e['stop_at_two'] = False  # Must re-observe the same dynamic 100% stop at qty 2.
        elif qty != e['quantity']:
            raise Blocked('UNEXPECTED_FILL_GROWTH')
        e.update(quantity=qty, fills=list(event['fills']))
    elif kind == 'stop_intent':
        strict_obj(event, {'kind','intent_key','sl_price','symbol','side',
                           'sl_qty_measure','quantity_sl','valid_before'}, 'STOP_INTENT_SCHEMA_INVALID')
        expected_side = 'SIDE_SELL' if direction == 'LONG' else 'SIDE_BUY'
        check(e['quantity'] == 1 and not e['stop_key'] and event['symbol'] == symbol
              and event['side'] == expected_side and event['sl_price'] == stop_price
              and positive_on_grid(event['sl_price'],symbol)
              and event['sl_qty_measure'] == 'SLTP_QTY_MEASURE_PERCENT'
              and event['quantity_sl'] == '100'
              and event['valid_before'] == 'VALID_BEFORE_GOOD_TILL_CANCEL'
              and type(event['intent_key']) is str and bool(event['intent_key']),
              'PROTECTIVE_STOP_100_PERCENT_CONTRACT_INVALID')
        e['stop_key'] = event['intent_key']
    elif kind == 'stop_post_ack':
        strict_obj(event, {'kind','intent_key','order_id'}, 'STOP_ACK_SCHEMA_INVALID')
        check(e['stop_key'] and not e['stop_order'] and e['stop_posts'] == 0
              and event['intent_key'] == e['stop_key'] and type(event['order_id']) is str and event['order_id'],
              'STOP_POST_UNAUTHORIZED_OR_DUPLICATE')
        e.update(stop_order=event['order_id'], stop_posts=1)
    elif kind == 'stop_observed':
        strict_obj(event, {'kind','order_id','active','symbol','side','sl_qty_measure',
                           'quantity_sl','sl_price','covered_current_quantity'}, 'STOP_OBSERVATION_SCHEMA_INVALID')
        check(e['stop_order'] == event['order_id'] and e['quantity'] in (1,2) and
              type(event['covered_current_quantity']) is int and
              event['covered_current_quantity'] == e['quantity'] and event['active'] is True and
              event['symbol'] == symbol and
              event['side'] == ('SIDE_SELL' if direction == 'LONG' else 'SIDE_BUY') and
              event['sl_qty_measure'] == 'SLTP_QTY_MEASURE_PERCENT' and
              event['quantity_sl'] == '100' and event['sl_price'] == stop_price,
              'BROKER_100_PERCENT_PROTECTION_NOT_PROVEN')
        e['stop_active'] = True
        if e['quantity'] == 1: e['stop_at_one'] = True
        if e['quantity'] == 2 and e['growth_observed']: e['stop_at_two'] = True
    elif kind == 'uncertain':
        strict_obj(event, {'kind','reason'}, 'UNCERTAIN_SCHEMA_INVALID')
        check(event['reason'] in {'ENTRY_ACK_UNKNOWN','STOP_ACK_UNKNOWN','BROKER_HISTORY_UNAVAILABLE',
                                   'FILL_PRICE_UNVERIFIED','ORDER_STATUS_UNKNOWN'}, 'UNCERTAIN_REASON_INVALID')
        e.update(halted=True, outcome='OPERATOR_INTERVENTION_REQUIRED')
    elif kind == 'terminal_flat':
        strict_obj(event, {'kind','broker_quantity','active_orders','stop_terminal',
                           'entry_terminal','unresolved_intents'}, 'FLAT_SCHEMA_INVALID')
        check(e['quantity'] == 2 and e['growth_observed'] and e['stop_at_one'] and e['stop_at_two']
              and event['broker_quantity'] == 0 and event['active_orders'] == 0
              and event['unresolved_intents'] == 0 and event['stop_terminal'] is True
              and event['entry_terminal'] is True, 'FINAL_BROKER_FLAT_OR_MULTIFILL_PROOF_MISSING')
        e.update(quantity=0,stop_active=False,terminal=True,
                 outcome='OFFLINE_MULTIFILL_GROWTH_SIMULATION_PASS_NOT_REAL_AUTHORITY')
    else:
        raise Blocked('EVENT_KIND_NOT_ALLOWED')
    return e

class Journal:
    def __init__(self, database: Path, identity: dict):
        check(database.name == DATABASE_NAME and database.parent.is_dir(), 'SCRATCH_DATABASE_PATH_INVALID')
        check(type(identity) is dict and identity.get('spec') == SPEC and identity.get('identity') == IDENTITY,
              'FROZEN_IDENTITY_INVALID')
        self.identity = identity
        self.db = sqlite3.connect(database.as_uri() + '?mode=rwc', uri=True)
        self.db.execute('PRAGMA busy_timeout=1000')
        self.db.execute('CREATE TABLE IF NOT EXISTS identity (key TEXT PRIMARY KEY,value TEXT NOT NULL)')
        self.db.execute('CREATE TABLE IF NOT EXISTS events(seq INTEGER PRIMARY KEY, payload TEXT NOT NULL, sha256 TEXT NOT NULL)')
        self.db.commit()
        row=self.db.execute("SELECT value FROM identity WHERE key='binding'").fetchone()
        if row is None:
            self.db.execute("INSERT INTO identity(key,value) VALUES('binding',?)",(canonical(identity),))
            self.db.commit()
        else:
            check(row[0] == canonical(identity), 'JOURNAL_IDENTITY_MISMATCH')
        self.state=fresh_state()
        rows=self.db.execute('SELECT seq,payload,sha256 FROM events ORDER BY seq').fetchall()
        for i,(seq,payload,sha) in enumerate(rows,1):
            check(seq == i and hashlib.sha256(payload.encode()).hexdigest() == sha,
                  'JOURNAL_EVENT_TAMPERED')
            self.state=advance(self.state,json.loads(payload),account_id=identity['account_id'],
                               symbol=identity['symbol'],direction=identity['direction'],
                               stop_price=identity['stop_price'])
        self.size=len(rows)

    def record(self, seq:int, event:dict, *, simulate_crash:bool=False)->dict:
        check(type(seq) is int and seq >= 1, 'EVENT_SEQ_INVALID')
        payload=canonical(event)
        sha=hashlib.sha256(payload.encode()).hexdigest()
        if seq <= self.size:
            row=self.db.execute('SELECT sha256 FROM events WHERE seq=?',(seq,)).fetchone()
            check(row and row[0] == sha, 'EVENT_REPLAY_CONFLICT')
            return dict(self.state)
        check(seq == self.size+1, 'EVENT_SEQ_GAP')
        next_state=advance(self.state,event,account_id=self.identity['account_id'],
                           symbol=self.identity['symbol'],direction=self.identity['direction'],
                           stop_price=self.identity['stop_price'])
        try:
            self.db.execute('BEGIN IMMEDIATE')
            self.db.execute('INSERT INTO events(seq,payload,sha256) VALUES(?,?,?)',(seq,payload,sha))
            if simulate_crash:
                raise Blocked('SYNTHETIC_BEFORE_COMMIT_CRASH')
            self.db.commit()
        except BaseException:
            self.db.rollback()
            raise
        self.size=seq; self.state=next_state
        return dict(self.state)

    def close(self):
        self.db.close()

def run(trace:dict,scratch_root:Path)->dict:
    strict_obj(trace, {'schema_id','binding','events'}, 'TRACE_SCHEMA_INVALID')
    check(trace['schema_id'] == SCHEMA and type(trace['events']) is list, 'TRACE_INVALID')
    bind=trace['binding']
    strict_obj(bind,{'spec','identity','account_id','symbol','direction','stop_price'}, 'TRACE_BINDING_INVALID')
    check(bind['spec'] == SPEC and bind['identity'] == IDENTITY
          and type(bind['account_id']) is str and bind['account_id'].startswith('synthetic-')
          and bind['symbol'] in TICKS
          and bind['direction'] in ('LONG','SHORT')
          and positive_on_grid(bind['stop_price'],bind['symbol']), 'TRACE_IDENTITY_INVALID')
    db=Journal(isolated_db(scratch_root),bind)
    try:
        for i,e in enumerate(trace['events'],1):
            db.record(i,e)
        st=db.state
        return {'schema_id':SCHEMA,'classification':st['outcome'],
                'offline_only':True,'real_order_endpoint_calls':0,
                'partial_growth_observed_synthetic':st['growth_observed'],
                'broker_percent_coverage_real':'NOT_VERIFIED',
                'real_account_fill_history':'NOT_VERIFIED',
                'broker_flat_physical':'NOT_VERIFIED',
                'live_production_ready':False,
                'journal_event_count':db.size}
    finally:
        db.close()

def main(argv=None)->int:
    p=argparse.ArgumentParser(description='strict synthetic durable SLTP multi-fill acceptance replay')
    p.add_argument('--trace',type=Path,required=True)
    p.add_argument('--scratch-root',type=Path,required=True)
    p.add_argument('--execute',action='store_true')
    args=p.parse_args(argv)
    if args.execute:
        print('CLASSIFICATION=BLOCKED_NO_REAL_ORDER_TRANSPORT')
        return 1
    try:
        result=run(json.loads(args.trace.read_text(encoding='utf-8')),args.scratch_root)
    except (Blocked,sqlite3.Error,OSError,ValueError,TypeError,KeyError):
        print('CLASSIFICATION=BLOCKED_SYNTHETIC_ACCEPTANCE')
        return 1
    print(canonical(result))
    return 0 if result['classification'] == 'OFFLINE_MULTIFILL_GROWTH_SIMULATION_PASS_NOT_REAL_AUTHORITY' else 1

if __name__=='__main__':
    sys.exit(main())
