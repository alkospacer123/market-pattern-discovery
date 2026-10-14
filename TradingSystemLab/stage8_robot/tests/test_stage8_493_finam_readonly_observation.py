"""No-network synthetic FINAM account/order/trade response contract tests."""
from __future__ import annotations

import hashlib
from copy import deepcopy
from pathlib import Path
import pytest

from TradingSystemLab.stage8_robot.diagnostics.stage8_493_finam_readonly_observation import (
    ReadonlyEvidenceBlocked, account_orders_snapshot, linked_history_fills
)

ACC='synthetic-only-account'
SYMBOL='CNYRUBF@RTSX'


def dec(value):
    return {'value': str(value)}


def fixture():
    account={'account_id':ACC,'positions':[{'symbol':SYMBOL,'quantity':dec('2')}]}
    orders={'orders':[
        {'order_id':'entry-id','status':'ORDER_STATUS_FILLED',
         'remaining_quantity':dec('0'),'order':{
             'symbol':SYMBOL,'client_order_id':'cid-entry','side':'SIDE_BUY',
             'quantity':dec('2')}},
        {'order_id':'stop-id','status':'ORDER_STATUS_NEW',
         'sltp_order':{'symbol':SYMBOL,'client_order_id':'cid-stop',
                       'comment':'acceptance-stop-1','side':'SIDE_SELL',
                       'sl_qty_measure':'SLTP_QTY_MEASURE_PERCENT',
                       'quantity_sl':dec('100'),'sl_price':dec('12.740'),
                       'valid_before':'VALID_BEFORE_GOOD_TILL_CANCEL'}},
    ]}
    return account,orders


def rows():
    return {'trades':[
        {'account_id':ACC,'order_id':'entry-id','symbol':SYMBOL,'side':'SIDE_BUY',
         'trade_id':'a','size':dec('1'),'price':dec('12.748'),'currency':'XXX',
         'timestamp':'2026-10-06T09:00:00Z'},
        {'account_id':ACC,'order_id':'entry-id','symbol':SYMBOL,'side':'SIDE_BUY',
         'trade_id':'b','size':dec('1'),'price':dec('12.749'),'currency':'RUB',
         'timestamp':'2026-10-06T09:00:01Z'}
    ]}


PARAMS=dict(account_id=ACC,order_id='entry-id',symbol=SYMBOL,side='SIDE_BUY',
            price_step='0.001',start='2026-10-06T08:00:00Z',
            end='2026-10-06T11:00:00Z',limit=50)


def test_native_finam_readonly_normalization():
    account,orders=fixture()
    row=account_orders_snapshot(account,orders,account_id=ACC,symbol=SYMBOL)
    assert row['position']==2 and row['other_positions']==0
    assert row['account_hash']==hashlib.sha256(ACC.encode()).hexdigest()
    assert row['orders'][0]['remaining']==0
    assert row['orders'][0]['active'] is False
    assert row['orders'][1]['active'] is True
    assert row['orders'][1]['percent']==100 and row['orders'][1]['price']=='12.740'
    assert row['freshness']=='NOT_PROVEN_BY_THIS_ADAPTER'


def test_two_order_linked_fills_only_scope():
    fills=linked_history_fills(rows(),**PARAMS)
    assert len(fills)==2 and sum(f['quantity'] for f in fills)==2
    assert [f['price'] for f in fills]==['12.748','12.749']
    assert all(f['account_hash']==hashlib.sha256(ACC.encode()).hexdigest() for f in fills)


@pytest.mark.parametrize('change',[
    lambda a,o: a.__setitem__('account_id','other'),
    lambda a,o: a['positions'].append(dict(a['positions'][0])),
    lambda a,o: o['orders'][0].__setitem__('status','ORDER_STATUS_UNSPECIFIED'),
    lambda a,o: o['orders'][0].pop('remaining_quantity'),
    lambda a,o: o['orders'][0].__setitem__('remaining_quantity',dec('-1')),
    lambda a,o: o['orders'][1]['sltp_order'].__setitem__('quantity_sl',dec('NaN')),
    lambda a,o: o['orders'][1]['sltp_order'].__setitem__('valid_before','VALID_BEFORE_DAY'),
    lambda a,o: o['orders'].append(dict(o['orders'][0])),
])
def test_wrong_broker_state_fails_closed(change):
    a,o=fixture();change(a,o)
    with pytest.raises(ReadonlyEvidenceBlocked):
        account_orders_snapshot(a,o,account_id=ACC,symbol=SYMBOL)


def test_other_symbol_position_never_hidden():
    a,o=fixture()
    a['positions'].append({'symbol':'USDRUBF@RTSX','quantity':dec('-1')})
    row=account_orders_snapshot(a,o,account_id=ACC,symbol=SYMBOL)
    assert row['other_positions']==1


@pytest.mark.parametrize('change',[
    lambda r:r.__setitem__('next_cursor','other-page'),
    lambda r:r['trades'].append(dict(r['trades'][0])),
    lambda r:r['trades'][1].__setitem__('account_id','foreign-account'),
    lambda r:r['trades'][1].__setitem__('side','SIDE_SELL'),
    lambda r:r['trades'][1].__setitem__('price',dec('12.7495')),
    lambda r:r['trades'][1].__setitem__('timestamp','2027-01-01T00:00:00Z'),
    lambda r:r['trades'][0].__setitem__('size',dec('2')),
    lambda r:r['trades'][0].__setitem__('currency','USD'),
])
def test_history_bad_scope_identity_size_or_completeness_blocks(change):
    response=rows();change(response)
    with pytest.raises(ReadonlyEvidenceBlocked):
        linked_history_fills(response,**PARAMS)


def test_history_limit_must_leave_headroom():
    with pytest.raises(ReadonlyEvidenceBlocked):
        linked_history_fills(rows(),**dict(PARAMS,limit=2))


def test_no_trading_or_network_imports():
    source=(Path(__file__).resolve().parents[1]/'diagnostics'/
            'stage8_493_finam_readonly_observation.py').read_text('utf-8')
    for forbidden in ('import FinamAPI','place_order(', 'cancel_order(',
                      'place_sltp_order(', 'create_session(', 'dpapi', 'requests.get('):
        assert forbidden not in source
