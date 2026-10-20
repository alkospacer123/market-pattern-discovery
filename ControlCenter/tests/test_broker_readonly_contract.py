"""Offline broker candidate shape tests — no authenticated/live authority."""
from copy import deepcopy
from datetime import datetime, timedelta, timezone
import json
import pytest
from broker_readonly.contract import SCHEMA, CandidateRejected, collect_once, validate_candidate

NOW = datetime(2026, 10, 20, 12, 0, tzinfo=timezone.utc)
SOURCE = 'CC03-H1-ONEOFFTEST20261020'
ALIAS = 'H1-LOCALN4'
BIND = 'a' * 64

def example():
    return dict(schema_id=SCHEMA, robot_id='H1', source_id=SOURCE, account_alias=ALIAS,
        binding_id=BIND, observed_at=(NOW-timedelta(seconds=60)).isoformat(),
        retrieved_at=(NOW-timedelta(seconds=30)).isoformat(),
        complete=dict(positions=True, orders=True, fills=True),
        positions=[dict(instrument='USDRUBF', side='LONG', quantity=2,
                        position_ref='b'*64, entry_price='80.12')],
        orders=[dict(order_ref='c'*64, position_ref='b'*64, instrument='USDRUBF',
                     side='SELL', quantity=2, status='ACTIVE', kind='STOP', stop_price='79.95')],
        fills=[dict(fill_ref='d'*64, instrument='USDRUBF', side='BUY', quantity=2,
                    price='80.12', executed_at=(NOW-timedelta(seconds=70)).isoformat())])

def check(x, **kwargs):
    return validate_candidate(json.dumps(x).encode(), expected_source=SOURCE,
        expected_alias=ALIAS, expected_binding=BIND, now=NOW, **kwargs)

def test_synthetic_shape_never_becomes_live():
    r=check(example())
    assert r['positions_claimed']==r['orders_claimed']==r['fills_claimed']==1
    assert r['broker_authenticated'] is False and r['stop_protection_verified'] is False
    assert r['engine_health'] is None and r['finance'] is None
    assert 'b'*64 not in repr(r) and 'c'*64 not in repr(r)

def test_empty_complete_not_verified_flat():
    x=example();x['positions']=[];x['orders']=[];x['fills']=[]
    assert check(x)['account_flat_verified'] is False

@pytest.mark.parametrize('case', ['schema','robot','source','alias','binding','extra','unknown_symbol',
    'position_bool','bad_price','order_link','wrong_stop_side','stale','future','incomplete',
    'bad_fill','duplicate_id','negative_qty'])
def test_bad_candidate_fails_closed(case):
    x=example()
    if case=='schema':x['schema_id']='OTHER'
    elif case=='robot':x['robot_id']='M15'
    elif case=='source':x['source_id']='CC03-H1-WRONGXXXXX'
    elif case=='alias':x['account_alias']='H1-OTHER1'
    elif case=='binding':x['binding_id']='e'*64
    elif case=='extra':x['token']='secret'
    elif case=='unknown_symbol':x['positions'][0]['instrument']='SBER'
    elif case=='position_bool':x['positions'][0]['quantity']=True
    elif case=='bad_price':x['orders'][0]['stop_price']='NaN'
    elif case=='order_link':x['orders'][0]['position_ref']='e'*64
    elif case=='wrong_stop_side':x['orders'][0]['side']='BUY'
    elif case=='stale':x['observed_at']=(NOW-timedelta(minutes=10)).isoformat()
    elif case=='future':x['retrieved_at']=(NOW+timedelta(seconds=1)).isoformat()
    elif case=='incomplete':x['complete']['positions']=False
    elif case=='bad_fill':x['fills'][0]['executed_at']=(NOW+timedelta(hours=1)).isoformat()
    elif case=='duplicate_id':x['orders'].append(deepcopy(x['orders'][0]))
    elif case=='negative_qty':x['positions'][0]['quantity']=-1
    with pytest.raises(CandidateRejected, match='^BROKER_CANDIDATE_REJECTED$'):
        check(x)

@pytest.mark.parametrize('raw', [b'{}', b'[]', b'{"a":1,"a":2}',b'NaN',b'\xff',
    b' '*65537, b'', b'{"secret": "token"}'],
    ids=['empty-object', 'empty-list', 'duplicate-key', 'nan', 'bad-utf8',
         'oversized-input', 'empty-bytes', 'secret-field'])
def test_bad_json_rejected_silently(raw):
    with pytest.raises(CandidateRejected) as err:
        validate_candidate(raw, expected_source=SOURCE, expected_alias=ALIAS,
                           expected_binding=BIND, now=NOW)
    assert 'token' not in str(err.value)

def test_no_external_producer_hook_and_no_mutators():
    with pytest.raises(CandidateRejected):collect_once()
    import ast
    from pathlib import Path
    source=Path(__file__).parents[1]/'broker_readonly/contract.py'
    tree=ast.parse(source.read_text())
    banned={'socket','urllib','requests','httpx','finam','ctypes','sqlite3',
            'subprocess','os','pathlib','importlib','TradingSystemLab','IntradayLab'}
    for n in ast.walk(tree):
        if isinstance(n,ast.Import): assert not any(a.name.split('.')[0] in banned for a in n.names)
        if isinstance(n,ast.ImportFrom): assert (n.module or '').split('.')[0] not in banned
