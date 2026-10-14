"""Synthetic independent checks for an order-incapable two-contract operator launcher."""
import importlib.util
from pathlib import Path
import pytest

SRC = Path(__file__).resolve().parents[1] / 'diagnostics' / 'stage8_493_sltp_operator_launcher.py'
spec = importlib.util.spec_from_file_location('launcher', SRC)
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)


def plan():
    return dict(schema_id='stage8_493_sltp_operator_plan.v1',
        production_specification_id=m.SPEC, active_identity=m.IDENTITY,
        production_commit=m.LIVE_SHA, instrument='CNYRUBF',finam_symbol='CNYRUBF@RTSX',
        direction='LONG', requested_contracts=2,entry_reference_price='12.750',
        stop_price='12.740', realized_equity_rub='10000', available_cash_rub='2000',
        margin_per_contract_rub='1000', maximum_operator_loss_and_cost_rub='1000',
        estimated_total_cost_rub='10',account_has_zero_positions_and_orders=True,
        production_task_isolated=True,kill_switch_halted=True,
        explicit_operator_trade_authorization=True)


def test_valid_plan_still_not_physically_authorized():
    r=m.validate_plan(plan())
    assert r['contracts']==2 and r['maximum_reference_initial_loss_rub']=='20'
    assert r['r15_reference_quantity']==15
    assert r['margin_reference_quantity']==r['frozen_reference_final_quantity']==2
    assert r['order_endpoint_calls']==0 and r['live_production_ready'] is False
    assert r['partial_fill_growth_proven'] is False


@pytest.mark.parametrize('change', [
    {'requested_contracts':1}, {'requested_contracts':3}, {'requested_contracts':True},
    {'production_commit':'0'*40}, {'instrument':'NG'},
    {'finam_symbol':'UNKNOWN'}, {'stop_price':'12.751'},
    {'stop_price':'12.7401'}, {'entry_reference_price':'NaN'},
    {'available_cash_rub':'100'},
    {'maximum_operator_loss_and_cost_rub':'20'},
    {'estimated_total_cost_rub':'0'},
    {'explicit_operator_trade_authorization':False},
    {'production_task_isolated':False}, {'kill_switch_halted':False},
    {'account_has_zero_positions_and_orders':False},
])
def test_block_invalid_or_insufficient_conditions(change):
    p=plan(); p.update(change)
    with pytest.raises(m.Blocked):m.validate_plan(p)


def test_only_approved_cny_long_with_protective_stop():
    p=plan();p.update(direction='SHORT',stop_price='12.760')
    with pytest.raises(m.Blocked):m.validate_plan(p)
    p=plan();p.update(stop_price='12.760')
    with pytest.raises(m.Blocked):m.validate_plan(p)
    p=plan();p.update(instrument='USDRUBF',finam_symbol='USDRUBF@RTSX')
    with pytest.raises(m.Blocked):m.validate_plan(p)


def test_unknown_fields_and_numeric_float_inputs_block():
    p=plan(); p['unexpected']='unsafe'
    with pytest.raises(m.Blocked):m.validate_plan(p)
    p=plan(); p['realized_equity_rub']=10000.0
    with pytest.raises(m.Blocked):m.validate_plan(p)


def test_no_broker_imports_or_writable_client():
    src=SRC.read_text(encoding='utf-8').lower()
    assert all(x not in src for x in ('import finamapi','create_session(','.place_order(','.cancel_order(','.place_sltp_order('))
    assert 'blocked_no_real_order_transport' in src


def test_r15_rather_than_margin_can_be_exact_two():
    p=plan()
    p.update(realized_equity_rub='1500', available_cash_rub='10000')
    r=m.validate_plan(p)
    assert r['r15_reference_quantity']==2
    assert r['margin_reference_quantity']==10
    assert r['frozen_reference_final_quantity']==2


def test_frozen_sizing_crosscheck_real_risk_margin_modules():
    from decimal import Decimal as D
    from TradingSystemLab.stage8_robot.risk import ContractEconomics, size_position
    from TradingSystemLab.stage8_robot.margin import cap_r15_by_margin
    for p in [plan(), dict(plan(), realized_equity_rub='1500', available_cash_rub='10000')]:
        r=m.validate_plan(p)
        e,s=D(p['entry_reference_price']),D(p['stop_price'])
        equity=D(p['realized_equity_rub'])
        contract=ContractEconomics(D('0.001'),D('1'),1,True)
        risk=size_position(equity,e,s,contract)
        margin=cap_r15_by_margin(
            realized_equity=equity,entry=e,stop=s,price_step=contract.price_step,
            tick_value=contract.tick_value,r15_quantity=risk.quantity,
            available_cash=D(p['available_cash_rub']),direction=p['direction'],
            initial_margin=D(p['margin_per_contract_rub']),trade_lot_size=1)
        assert r['r15_reference_quantity']==risk.quantity
        assert r['margin_reference_quantity']==margin.margin_quantity
        assert r['frozen_reference_final_quantity']==margin.final_quantity


def test_two_lot_exception_is_independent_of_natural_r15_and_margin_quantity():
    p=plan(); p.update(realized_equity_rub='100',available_cash_rub='10000')
    r=m.validate_plan(p)
    assert r['contracts']==2
    assert r['r15_reference_quantity']==0
    assert r['margin_reference_quantity']==10
    assert r['frozen_reference_final_quantity']==0
    assert r['test_quantity_independent_of_robot_sizing'] is True
    assert r['approved_test_budget_rub']=='1000'
    p=plan();p.update(available_cash_rub='11000',margin_per_contract_rub='1000')
    assert m.validate_plan(p)['frozen_reference_final_quantity']>2


def test_budget_and_margin_are_independent_hard_blocks():
    p=plan();p['maximum_operator_loss_and_cost_rub']='1001'
    with pytest.raises(m.Blocked):m.validate_plan(p)
    p=plan();p['stop_price']='12.200'
    with pytest.raises(m.Blocked):m.validate_plan(p)
    p=plan();p['margin_per_contract_rub']='1001'
    with pytest.raises(m.Blocked):m.validate_plan(p)
