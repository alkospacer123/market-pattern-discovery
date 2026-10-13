"""Stage 8 #493 FINAM READONLY evidence adapter, disconnected from any API.

Normalizes independently collected REST GET account/orders/trades payloads for
operator review. No FinamAPI, credentials, network, writable port, recovery
execution or real-order authorization. Snapshots have no intrinsic freshness;
caller must verify authenticated source, timestamp and consistency separately.
"""
from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
import hashlib

from TradingSystemLab.stage8_robot.production_broker_state import (
    ProductionBrokerStateError, order_views, position_quantities,
)


class ReadonlyEvidenceBlocked(ValueError):
    pass


def _num(value, *, whole=False, positive=False) -> Decimal:
    if (type(value) is not dict or set(value) != {'value'}
            or type(value['value']) is not str):
        raise ReadonlyEvidenceBlocked('FINAM_DECIMAL_SCHEMA_INVALID')
    try:
        amount = Decimal(value['value'])
    except InvalidOperation:
        raise ReadonlyEvidenceBlocked('FINAM_DECIMAL_VALUE_INVALID') from None
    if (not amount.is_finite()
            or (whole and amount != amount.to_integral_value())
            or (positive and amount <= 0)):
        raise ReadonlyEvidenceBlocked('FINAM_DECIMAL_VALUE_INVALID')
    return amount


def _time(value: str) -> datetime:
    if type(value) is not str or 'T' not in value or not (value.endswith('Z') or
            '+' in value[10:] or '-' in value[10:]):
        raise ReadonlyEvidenceBlocked('FINAM_TIMESTAMP_INVALID')
    try:
        timestamp = datetime.fromisoformat(value.replace('Z', '+00:00'))
    except ValueError:
        raise ReadonlyEvidenceBlocked('FINAM_TIMESTAMP_INVALID') from None
    if timestamp.tzinfo is None or timestamp.utcoffset() is None:
        raise ReadonlyEvidenceBlocked('FINAM_TIMESTAMP_INVALID')
    return timestamp.astimezone(timezone.utc)


def account_orders_snapshot(account: dict, orders: dict, *,
                            account_id: str, symbol: str) -> dict:
    """Convert real broker field shapes; never assert a LIVE broker observation."""
    if (type(account) is not dict or type(account_id) is not str
            or not account_id or account.get('account_id') != account_id
            or type(symbol) is not str or not symbol):
        raise ReadonlyEvidenceBlocked('FINAM_ACCOUNT_IDENTITY_INVALID')
    try:
        positions = position_quantities(account)
        views = order_views(orders)
    except (ProductionBrokerStateError, ValueError) as exc:
        raise ReadonlyEvidenceBlocked('FINAM_ACCOUNT_ORDER_SCHEMA_INVALID') from exc

    if type(orders) is not dict or type(orders.get('orders')) is not list:
        raise ReadonlyEvidenceBlocked('FINAM_ORDERS_NOT_FULL_COLLECTION')
    raw = orders['orders']
    if len(raw) != len(views):
        raise ReadonlyEvidenceBlocked('FINAM_ORDER_COUNT_MISMATCH')
    result = []
    for row, view in zip(raw, views):
        data = {
            'id': view.order_id, 'kind': view.kind.lower(),
            'active': view.active, 'symbol': view.symbol,
            'side': view.side, 'client_order_id': view.client_order_id,
            'comment': view.comment,
        }
        if view.kind == 'REGULAR':
            remaining = _num(row.get('remaining_quantity'), whole=True)
            if remaining < 0:
                raise ReadonlyEvidenceBlocked('FINAM_REMAINING_NEGATIVE')
            data['remaining'] = int(remaining)
        else:
            request = view.request
            if (request.get('sl_qty_measure') != 'SLTP_QTY_MEASURE_PERCENT'
                    or request.get('valid_before') != 'VALID_BEFORE_GOOD_TILL_CANCEL'):
                raise ReadonlyEvidenceBlocked('FINAM_SLTP_CONTRACT_INVALID')
            percent = _num(request.get('quantity_sl'), whole=True)
            price = _num(request.get('sl_price'), positive=True)
            if percent < 1 or percent > 100:
                raise ReadonlyEvidenceBlocked('FINAM_SLTP_PERCENT_INVALID')
            data.update(percent=int(percent), price=str(price))
        result.append(data)
    return {
        'account_hash': hashlib.sha256(account_id.encode('utf-8')).hexdigest(),
        'symbol': symbol, 'position': positions.get(symbol, 0),
        'other_positions': sum(1 for key, value in positions.items()
                               if key != symbol and value != 0),
        'orders': result,
        'authority': 'READONLY_REST_RESPONSE_NORMALIZATION_ONLY',
        'freshness': 'NOT_PROVEN_BY_THIS_ADAPTER',
    }


def linked_history_fills(response: dict, *, account_id: str, order_id: str,
                         symbol: str, side: str, price_step: str,
                         start: str, end: str, limit: int) -> list[dict]:
    """Parse *bounded* GET /trades response, never prove retention/completeness."""
    if (not all(type(x) is str and x for x in
                (account_id, order_id, symbol, price_step, start, end))
            or side not in {'SIDE_BUY', 'SIDE_SELL'}
            or type(limit) is not int or not 0 < limit < 2**31):
        raise ReadonlyEvidenceBlocked('FILL_TARGET_INVALID')
    a, b = _time(start), _time(end)
    if not a < b:
        raise ReadonlyEvidenceBlocked('FILL_INTERVAL_INVALID')
    try:
        step = Decimal(price_step)
    except InvalidOperation:
        raise ReadonlyEvidenceBlocked('FILL_TICK_INVALID') from None
    if not step.is_finite() or step <= 0:
        raise ReadonlyEvidenceBlocked('FILL_TICK_INVALID')
    if (type(response) is not dict or type(response.get('trades')) is not list
            or len(response['trades']) >= limit
            or any(response.get(k) not in (None, '', 0)
                   for k in ('next_cursor', 'next_page_token'))):
        raise ReadonlyEvidenceBlocked('FILL_HISTORY_COMPLETENESS_UNKNOWN')
    matched, unique_ids = [], set()
    for row in response['trades']:
        if type(row) is not dict:
            raise ReadonlyEvidenceBlocked('FILL_ROW_SCHEMA_INVALID')
        if row.get('order_id') != order_id:
            continue
        if (row.get('account_id') != account_id or row.get('symbol') != symbol
                or row.get('side') != side
                or type(row.get('trade_id')) is not str or not row['trade_id']
                or row['trade_id'] in unique_ids
                or row.get('currency') not in {'RUB', 'XXX'}):
            raise ReadonlyEvidenceBlocked('FILL_IDENTITY_INVALID')
        when = _time(row.get('timestamp'))
        if not a <= when < b:
            raise ReadonlyEvidenceBlocked('FILL_TIMESTAMP_OUTSIDE_WINDOW')
        count = _num(row.get('size'), whole=True, positive=True)
        price = _num(row.get('price'), positive=True)
        if count > 2 or price % step != 0:
            raise ReadonlyEvidenceBlocked('FILL_SIZE_OR_TICK_INVALID')
        unique_ids.add(row['trade_id'])
        matched.append({
            'account_hash': hashlib.sha256(account_id.encode('utf-8')).hexdigest(),
            'order_id': order_id, 'symbol': symbol, 'side': side,
            'trade_id': row['trade_id'], 'quantity': int(count),
            'price': str(price),
        })
    if sum(v['quantity'] for v in matched) > 2:
        raise ReadonlyEvidenceBlocked('FILL_QUANTITY_EXCEEDS_TWO')
    return matched
