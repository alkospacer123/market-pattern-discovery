"""Validate externally captured broker facts without upgrading their authority.

An accepted shape is NOT an authenticated FINAM observation. Only an independently
approved one-shot producer and source-binding/NTFS acceptance can grant that.
No network, IO, tokens, DPAPI, subprocess or H1 imports exist in this module.
"""
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
import json
import re

SCHEMA = 'cc03.h1-broker-capture.candidate.v1'
N4 = frozenset({'USDRUBF', 'CNYRUBF', 'GLDRUBF', 'IMOEXF'})
MAX_BYTES = 65536
MAX_ROWS = 256
HEX = re.compile(r'[0-9a-f]{64}\Z')
ALIAS = re.compile(r'H1-[A-Z0-9]{4,24}\Z')
SOURCE = re.compile(r'CC03-H1-[A-Z0-9]{8,32}\Z')
PRICE = re.compile(r'(?:0|[1-9][0-9]{0,11})(?:\.[0-9]{1,8})?\Z')


class CandidateRejected(ValueError):
    """Fixed public error; source data/error text is never included."""
    def __init__(self):
        super().__init__('BROKER_CANDIDATE_REJECTED')


def require(ok):
    if not ok:
        raise CandidateRejected()


def unique_pairs(pairs):
    value = {}
    for key, item in pairs:
        require(key not in value)
        value[key] = item
    return value


def timestamp(value):
    require(type(value) is str and len(value) <= 40)
    try:
        at = datetime.fromisoformat(value.replace('Z', '+00:00'))
    except (ValueError, OverflowError):
        raise CandidateRejected() from None
    require(at.tzinfo is not None and at.utcoffset() is not None)
    return at.astimezone(timezone.utc)


def money(value):
    require(type(value) is str and PRICE.fullmatch(value) is not None)
    try:
        result = Decimal(value)
    except InvalidOperation:
        raise CandidateRejected() from None
    require(result.is_finite() and result > 0)
    return value


def hex_id(value):
    require(type(value) is str and HEX.fullmatch(value) is not None)
    return value


def string(value, pattern):
    require(type(value) is str and pattern.fullmatch(value) is not None)
    return value


def keys(row, required):
    require(type(row) is dict and set(row) == set(required))


def rows(value):
    require(type(value) is list and len(value) <= MAX_ROWS)
    return value


def validate_candidate(raw, *, expected_source, expected_alias, expected_binding, now):
    """Return bounded OFFLINE evidence facts; never a runtime or broker authority.

    The three expected bindings must be obtained independently of *raw*. This
    prevents accidental cross-account mapping; it does not authenticate raw.
    Missing/completeness=false rows are not evidence of zero/flat/protection.
    """
    require(type(raw) is bytes and 0 < len(raw) <= MAX_BYTES)
    require(isinstance(now, datetime) and now.tzinfo is not None and now.utcoffset() is not None)
    string(expected_source, SOURCE)
    string(expected_alias, ALIAS)
    hex_id(expected_binding)
    try:
        data = json.loads(raw.decode('utf-8'), object_pairs_hook=unique_pairs,
                          parse_constant=lambda _: (_ for _ in ()).throw(CandidateRejected()))
    except (ValueError, UnicodeError, TypeError, RecursionError):
        raise CandidateRejected() from None
    keys(data, ('schema_id', 'robot_id', 'source_id', 'account_alias', 'binding_id',
                'observed_at', 'retrieved_at', 'complete', 'positions', 'orders', 'fills'))
    require(data['schema_id'] == SCHEMA and data['robot_id'] == 'H1'
            and data['source_id'] == expected_source
            and data['account_alias'] == expected_alias
            and data['binding_id'] == expected_binding)
    at, retrieved = timestamp(data['observed_at']), timestamp(data['retrieved_at'])
    clock = now.astimezone(timezone.utc)
    require(at <= retrieved <= clock and (clock - at).total_seconds() <= 300)
    completeness = data['complete']
    keys(completeness, ('positions', 'orders', 'fills'))
    require(all(type(v) is bool for v in completeness.values()))
    positions, orders, fills = rows(data['positions']), rows(data['orders']), rows(data['fills'])
    require(all(completeness.values()) or not any((positions, orders, fills)))
    observed_symbols = set()
    observed_positions = set()
    for row in positions:
        keys(row, ('instrument', 'side', 'quantity', 'position_ref', 'entry_price'))
        require(type(row['instrument']) is str and row['instrument'] in N4
                and row['instrument'] not in observed_symbols)
        observed_symbols.add(row['instrument'])
        require(row['side'] in ('LONG', 'SHORT') and type(row['quantity']) is int
                and 0 < row['quantity'] <= 1000000)
        observed_positions.add(hex_id(row['position_ref']))
        if row['entry_price'] is not None:
            money(row['entry_price'])
    require(len(observed_positions) == len(positions))
    observed_orders = set()
    for row in orders:
        keys(row, ('order_ref', 'position_ref', 'instrument', 'side',
                   'quantity', 'status', 'kind', 'stop_price'))
        oid = hex_id(row['order_ref'])
        require(oid not in observed_orders)
        observed_orders.add(oid)
        require(hex_id(row['position_ref']) in observed_positions)
        require(type(row['instrument']) is str and row['instrument'] in observed_symbols
                and row['instrument'] == next(p['instrument'] for p in positions
                                             if p['position_ref'] == row['position_ref']))
        require(row['side'] in ('BUY', 'SELL') and row['kind'] == 'STOP'
                and row['status'] == 'ACTIVE' and type(row['quantity']) is int
                and 0 < row['quantity'] <= 1000000)
        position = next(p for p in positions if p['position_ref'] == row['position_ref'])
        require(row['side'] == ('SELL' if position['side'] == 'LONG' else 'BUY')
                and row['quantity'] <= position['quantity'])
        money(row['stop_price'])
    observed_fills = set()
    for row in fills:
        keys(row, ('fill_ref', 'instrument', 'side', 'quantity', 'price', 'executed_at'))
        fid = hex_id(row['fill_ref'])
        require(fid not in observed_fills)
        observed_fills.add(fid)
        require(type(row['instrument']) is str and row['instrument'] in N4
                and row['side'] in ('BUY', 'SELL')
                and type(row['quantity']) is int and 0 < row['quantity'] <= 1000000)
        money(row['price'])
        require(timestamp(row['executed_at']) <= retrieved)
    # A declared empty positions list is still NOT a verified flat broker account.
    return {'classification': 'OFFLINE_CANDIDATE_NOT_AUTHENTICATED',
            'observed_at': at.isoformat(), 'retrieved_at': retrieved.isoformat(),
            'positions_claimed': len(positions), 'orders_claimed': len(orders),
            'fills_claimed': len(fills), 'completeness_claimed': dict(completeness),
            'broker_authenticated': False, 'h1_ownership_verified': False,
            'stop_protection_verified': False, 'account_flat_verified': False,
            'engine_health': None, 'engine_signals': None, 'finance': None}


def collect_once(*args, **kwargs):
    """No approved producer is wired; cannot query FINAM or emit a live snapshot."""
    raise CandidateRejected()
