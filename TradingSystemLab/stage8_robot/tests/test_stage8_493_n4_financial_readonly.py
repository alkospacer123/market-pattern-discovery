"""Offline only: synthetic FINAM payloads, no network/SQLite/LIVE credentials."""
import csv
import importlib.util
import json
from pathlib import Path
import sys
import types
from decimal import Decimal
from unittest.mock import patch

import pytest

SOURCE = Path(__file__).resolve().parents[1] / 'diagnostics/stage8_493_n4_financial_readonly.py'
spec = importlib.util.spec_from_file_location('stage8_493_financial_readonly_test', SOURCE)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

ROWS = [dict(research_symbol=n, finam_symbol=f'{n}@RTSX', mic='RTSX',
             binding_status='AUTHENTICATED_REAL_READONLY', trading_status='TRADABLE',
             quantity_granularity='1', price_step=step, tick_value=value)
        for n,step,value in [('USDRUBF','0.01','10'),('CNYRUBF','0.001','1'),
                             ('GLDRUBF','0.1','0.1'),('IMOEXF','0.5','5')]]


def dec(value):
    if not isinstance(value,dict) or set(value)!={'value'}:
        raise ValueError('BAD_DECIMAL')
    return Decimal(value['value'])


def margin(params, side):
    return Decimal(str(params['long_initial_margin' if side=='LONG' else 'short_initial_margin']))


def sample_asset(name):
    step = next(row['price_step'] for row in ROWS if row['research_symbol']==name)
    decimals = len(step.split('.')[1])
    return {'ticker':name,'mic':'RTSX','decimals':decimals,
            'min_step':str(int(Decimal(step)*10**decimals)),'lot_size':{'value':'1000'}}


def sample_params(name, account='fake'):
    return {'symbol':f'{name}@RTSX','account_id':account,'is_tradable':{'value':True},
            'trade_lot_size':'1','long_initial_margin':'1000','short_initial_margin':'1200'}


def sample_account(account='fake'):
    return {'account_id':account,'status':'ACCOUNT_ACTIVE','positions':[],
            'equity':{'value':'100000'},'unrealized_profit':{'value':'0'},
            'portfolio_mc':{'available_cash':{'value':'50000'}}}


def finances(a):
    def p(a): return types.SimpleNamespace(variant='MC',available_cash=dec(a['portfolio_mc']['available_cash']))
    return m.financial_account(a,'fake',lambda a:{} if not a['positions'] else {'CNY':1},
                                lambda _:[],p,dec)


def test_frozen_registry(tmp_path):
    r = tmp_path/'TradingSystemLab/stage8_robot/production_instrument_registry.csv'
    r.parent.mkdir(parents=True)
    with r.open('w',newline='',encoding='utf8') as f:
        w=csv.DictWriter(f, fieldnames=ROWS[0].keys());w.writeheader();w.writerows(ROWS)
    assert set(m.read_registry(tmp_path))==set(m.N4)
    with r.open('a') as f:f.write('EXTRA,EXTRA@RTSX,RTSX,AUTHENTICATED_REAL_READONLY,TRADABLE,1,1,1\n')
    with pytest.raises(m.Blocked,match='MEMBERSHIP'):m.read_registry(tmp_path)


@pytest.mark.parametrize('name',m.N4)
def test_asset_and_margin_four_n4(name):
    row=next(r for r in ROWS if r['research_symbol']==name)
    report=m.asset_economics(name,sample_asset(name),sample_params(name),row,margin,dec)
    assert Decimal(report['price_step_finam'])==Decimal(row['price_step'])
    assert report['initial_margin_per_contract_rub_finam']=={'LONG':'1000','SHORT':'1200'}
    assert report['tick_value_rub_live_broker_verified'] is False


@pytest.mark.parametrize('fault', ['step','lot','symbol','account','tradeability','margin','asset'])
def test_asset_broker_forgery_fail_closed(fault):
    row=ROWS[1]; asset=sample_asset('CNYRUBF');p=sample_params('CNYRUBF')
    if fault=='step': asset['min_step']='2'
    if fault=='lot': p['trade_lot_size']='2'
    if fault=='symbol': p['symbol']='IMOEXF@RTSX'
    if fault=='account': p['account_id']=None
    if fault=='tradeability': p['is_tradable']={'value':False}
    if fault=='margin': p['long_initial_margin']='-1'
    if fault=='asset': asset['ticker']='INVALID'
    with pytest.raises((m.Blocked,AssertionError,ValueError)):
        m.asset_economics('CNYRUBF',asset,p,row,margin,dec)


def test_account_equity_not_mislabeled_realized():
    assert finances(sample_account())['equity_broker_reported_rub']=='100000'
    with pytest.raises(m.Blocked,match='POSITION_NOT_FLAT'):
        finances({**sample_account(),'positions':[{'symbol':'CNY'}]})
    with pytest.raises(m.Blocked,match='ACCOUNT_INVALID'):
        finances(sample_account('wrong'))


def test_safe_external_create_only_and_symlink(tmp_path):
    root=tmp_path/'runtime';root.mkdir()
    live=tmp_path/'checkout';live.mkdir()
    audit=tmp_path/'tslaudit';audit.mkdir()
    assert m.safe_output(audit/'new.json',root,live).name=='new.json'
    with pytest.raises(m.Blocked):m.safe_output(root/'bad.json',root,live)
    (audit/'existing.json').write_text('anything')
    with pytest.raises(m.Blocked):m.safe_output(audit/'existing.json',root,live)
    alias=tmp_path/'alias';alias.symlink_to(audit,target_is_directory=True)
    with pytest.raises(m.Blocked):m.safe_output(alias/'new.json',root,live)


def test_no_trade_code_or_endpoints_in_source():
    source=SOURCE.read_text()
    for forbidden in ('place_order(', 'place_sltp_order(', 'cancel_order(',
                      'subprocess.run(', 'sqlite3.connect(', 'Get-TradingCredential'):
        assert forbidden not in source
    assert "FINAM_TRADING_OR_NONALLOWLIST_REQUEST_FORBIDDEN" in source
    assert 'session_readonly' in source
    assert "'real_order_authorization':False" in source


def test_integration_synthetic_get_only_hard_allowlist(tmp_path,monkeypatch,capsys):
    checkout=tmp_path/'checkout';checkout.mkdir()
    root=tmp_path/'runtime';root.mkdir()
    audit=tmp_path/'tslaudit';audit.mkdir()
    r=checkout/'TradingSystemLab/stage8_robot/production_instrument_registry.csv'
    r.parent.mkdir(parents=True)
    with r.open('w',newline='',encoding='utf8') as f:
        w=csv.DictWriter(f, fieldnames=ROWS[0].keys());w.writeheader();w.writerows(ROWS)
    clients=[]
    class FakeFinam:
        def __init__(self,secret):clients.append(self)
        def create_session(self):self._request('POST','/v1/sessions',{'secret':'unused'},auth=False)
        def session_details(self):
            self._request('POST','/v1/sessions/details',{'token':'unused'},auth=False)
            return {'readonly':True,'account_ids':['fake']}
        def account(self,account):return self._request('GET','/v1/accounts/'+account).body
        def orders(self,account):return self._request('GET','/v1/accounts/'+account+'/orders').body
        def _request(self,method,path,payload=None,auth=True,retries=0):
            if path.endswith('/orders'):return types.SimpleNamespace(body={'orders':[]})
            if path.startswith('/v1/accounts/'):
                return types.SimpleNamespace(body=sample_account())
            if path.endswith('/params?account_id=fake'):
                n=path.split('/')[3].split('%')[0]
                return types.SimpleNamespace(body=sample_params(n))
            if path.startswith('/v1/assets/'):
                n=path.split('/')[3].split('%')[0]
                return types.SimpleNamespace(body=sample_asset(n))
            return types.SimpleNamespace(body={})
    def portfolio(a):return types.SimpleNamespace(variant='MC',available_cash=dec(a['portfolio_mc']['available_cash']))
    mods={'TradingSystemLab':types.ModuleType('TradingSystemLab'),
          'TradingSystemLab.stage8_robot':types.ModuleType('TradingSystemLab.stage8_robot'),
          'TradingSystemLab.stage8_robot.finam_api':types.SimpleNamespace(FinamAPI=FakeFinam),
          'TradingSystemLab.stage8_robot.margin':types.SimpleNamespace(portfolio_authority=portfolio,directional_initial_margin=margin,parse_rest_decimal_value_object=dec),
          'TradingSystemLab.stage8_robot.production_broker_state':types.SimpleNamespace(position_quantities=lambda a:{},order_views=lambda o:[]),
          'stage8_493_post_isolation_broker_readonly':types.SimpleNamespace(local_gate=lambda root,account:None)}
    output=audit/'fresh.json'
    with patch.dict(sys.modules,mods),patch.object(m.subprocess,'check_output',return_value=m.LIVE_SHA+'\n'):
        m.collect(root,checkout,'fake_secret','fake',output)
    data=json.loads(output.read_text())
    assert data['classification']=='BROKER_N4_ACCOUNT_ASSET_PARAMS_READONLY_PASS_NO_TRADE_AUTHORITY'
    assert data['positions_and_orders_zero_twice']
    assert data['fees_and_round_trip_commissions']=='NOT_VERIFIED_REQUIRES_CLIENT_TARIFF'
    assert data['real_order_authorization'] is False
    assert set(data['N4'])==set(m.N4)
    assert data['request_labels'].count('ACCOUNT')==2
    for method,path in [('POST','/v1/accounts/fake/orders'),('POST','/v1/accounts/fake/sltp-orders'),
                        ('DELETE','/v1/accounts/fake/orders/one'),('GET','/v1/accounts/other'),
                        ('GET','/v1/accounts/fake/trades')]:
        with pytest.raises(m.Blocked,match='FORBIDDEN'):clients[0]._request(method,path)
