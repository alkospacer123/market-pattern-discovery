"""Synthetic only, no account, trading token or network."""
import importlib.util
import json
from pathlib import Path
import pytest

src=Path(__file__).resolve().parents[1] / 'diagnostics' / 'stage8_493_two_contract_plan_offline.py'
spec=importlib.util.spec_from_file_location('stage8_493_two_contract_plan_offline',src)
m=importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

def report():
    d={'USDRUBF':('0.01','10'),'CNYRUBF':('0.001','1'),
       'GLDRUBF':('0.1','0.1'),'IMOEXF':('0.5','5')}
    return {'schema_id':'stage8_493_n4_financial_readonly.v1',
            'production_specification_id':m.SPEC, 'active_identity':m.IDENTITY,
            'live_commit':m.LIVE, 'classification':'BROKER_N4_ACCOUNT_ASSET_PARAMS_READONLY_PASS_NO_TRADE_AUTHORITY',
            'session_readonly':True,'positions_and_orders_zero_twice':True,
            'finam_trading_order_calls':0, 'real_order_authorization':False,
            'account_sha256':'a'*64,
            'account_financials':{'equity_broker_reported_rub':'49969.56',
               'unrealized_pnl_broker_reported_rub':'0','available_cash_broker_reported_rub':'49969.56',
               'portfolio_variant':'MC'},
            'N4':{name:{'finam_symbol':name+'@RTSX',
              'price_step_finam':tick,'tick_rub_frozen_moex_reference_not_broker_cash_authority':rub,
              'trade_lot_size_finam':1,'initial_margin_per_contract_rub_finam':{'LONG':'15000','SHORT':'15000'},
              'account_specific_margin':True,'tick_value_rub_live_broker_verified':False}
              for name,(tick,rub) in d.items()}}

def cand(**kw):
    data={'instrument':'CNYRUBF','direction':'LONG','entry':'12.750',
          'stop':'12.450','round_trip_fees_rub':'5',
          'adverse_slippage_ticks':5,'operator_budget_rub':'615'}
    data.update(kw)
    return data

def test_report_eight_instruments_and_no_trade_permission():
    out=m.inspect_report(report())
    assert len(out['margin_and_risk_reference'])==8
    assert out['nominal_r15_cash_rub_prior_snapshot']=='749.54340'
    assert out['real_orders']==0 and out['live_authorized'] is False
    assert 'account_sha256' not in json.dumps(out)
    assert 'a'*64 not in json.dumps(out)
    assert all(x['possible_exact_two_by_frozen_sizing'] for x in out['margin_and_risk_reference'])

def test_exact_two_plan_with_fee_slippage_and_budget():
    out=m.inspect_report(report(),[cand()])['candidate_reference_checks'][0]
    assert out['r15_quantity_reference']==2
    assert out['frozen_quantity_reference']==2
    assert out['nominal_stop_loss_two_rub']=='600'
    assert out['scenario_loss_two_plus_fees_rub']=='615'
    assert out['operator_budget_scenario_pass'] is True
    assert out['live_trade_authorized'] is False

def test_stop_too_narrow_causes_more_than_two_not_pass():
    out=m.inspect_report(report(),[cand(stop='12.700')])['candidate_reference_checks'][0]
    assert out['frozen_quantity_reference']>2
    assert out['exact_two_reference'] is False

def test_budget_below_scenario_fails():
    out=m.inspect_report(report(),[cand(operator_budget_rub='614.99')])['candidate_reference_checks'][0]
    assert out['exact_two_reference'] is True
    assert out['operator_budget_scenario_pass'] is False

@pytest.mark.parametrize('field,value',[
  ('real_order_authorization',True),('session_readonly',False),('positions_and_orders_zero_twice',False),
  ('live_commit','0'*40),('account_sha256','NOT_ALLOWED'),
  ('finam_trading_order_calls',1),
])
def test_invalid_report_blocks(field,value):
    r=report();r[field]=value
    with pytest.raises(m.Blocked):m.inspect_report(r)

@pytest.mark.parametrize('key,value',[
  ('stop','12.751'),('stop','12.4501'),('entry','NaN'),
  ('adverse_slippage_ticks',True),('round_trip_fees_rub','-1'),
])
def test_bad_plan_blocks(key,value):
    with pytest.raises(m.Blocked):m.inspect_report(report(),[cand(**{key:value})])

def test_margin_capacity_below_two_blocks():
    r=report()
    r['N4']['CNYRUBF']['initial_margin_per_contract_rub_finam']={'LONG':'30000','SHORT':'30000'}
    out=m.inspect_report(r,[cand()])
    assert out['candidate_reference_checks'][0]['frozen_quantity_reference']==1
    assert out['candidate_reference_checks'][0]['exact_two_reference'] is False

def test_no_network_or_sqlite_or_place_order_source():
    text=src.read_text('utf-8').lower()
    for term in ('finamapi','place_order','cancel_order','sqlite3','urlopen','get-scheduledtask'):
        assert term not in text
