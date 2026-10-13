"""Independent offline fill/exposure oracles; no Intel data or broker requests."""
from dataclasses import replace
from TradingSystemLab.stage8_robot.broker import compact_client_order_id
from datetime import datetime, timezone
from decimal import Decimal as D, localcontext
from fractions import Fraction
import json

import pytest

from TradingSystemLab.stage8_robot.execution_grid import EXECUTION_REVISION, require_on_grid
from TradingSystemLab.stage8_robot.finam_fill_price_readonly import Target, analyze_history
from TradingSystemLab.stage8_robot.production_broker_state import order_views
from TradingSystemLab.stage8_robot.production_runtime import ProductionRuntimeError
from TradingSystemLab.stage8_robot.production_service import ProductionService, ProductionServiceError, Snapshot
from TradingSystemLab.stage8_robot.protective_stop_contract import percent_position_stop_payload
from TradingSystemLab.stage8_robot.tests.test_stop_tick_grid_amendment import runtime, plan, signal, bar

ACCOUNT='synthetic-fill-account'
ORDER='synthetic-entry-order'
START='2026-01-02T07:00:00Z'
END='2026-01-02T07:01:00Z'
NOW=datetime(2026,1,2,7,1,tzinfo=timezone.utc)


def fill(entry, index=1, *, quantity=1, price='100', **changes):
    return dict({'trade_id':f'synthetic-fill-{index}', 'order_id':ORDER, 'account_id':ACCOUNT,
                 'symbol':entry.finam_symbol,'side':'SIDE_BUY' if entry.direction=='LONG' else 'SIDE_SELL',
                 'size':{'value':str(quantity)},'price':{'value':str(price)},'currency':'XXX',
                 'timestamp':f'2026-01-02T07:00:0{index}.123456789Z'},**changes)


def setup(rt, symbol='USDRUBF', side='LONG'):
    entry=plan(rt,signal(symbol,side),cash=D('300') if side=='LONG' else D('360'))
    assert entry.quantity==3
    rt.record_entry_submission(entry.idempotency_key,ACCOUNT,START)
    rt.store.transition_intent(entry.idempotency_key,'ACK',ORDER)
    return entry


def handoff(rt,entry,rows,**changes):
    args=dict(account_id=ACCOUNT,broker_order_id=ORDER,response={'trades':rows},
              start=START,end=END,limit=1000,observed_at=END)
    return rt.handoff_entry_history(entry.idempotency_key,**(args|changes))


@pytest.mark.parametrize('symbol',['USDRUBF','CNYRUBF','GLDRUBF','IMOEXF'])
@pytest.mark.parametrize('side',['LONG','SHORT'])
def test_full_fill_xxx_authority_exact_rub_tick_risk_and_restart(tmp_path,symbol,side):
    path=tmp_path/'production.db';rt=runtime(path);entry=setup(rt,symbol,side)
    stop=rt.confirm_entry_position(entry.idempotency_key,entry.expected_position_quantity)
    assert stop.quantity==3 and stop.stop_price==entry.stop_price
    require_on_grid(stop.stop_price,stop.price_step)
    rt.confirm_protective_stop(stop.idempotency_key,'synthetic-backstop')
    step=entry.price_step
    # Better fill keeps sizing and economic authority separate from the feed label.
    price=D('100')+(-1 if side=='LONG' else 1)*step
    rows=[fill(entry,quantity=3,price=str(price))]
    report=handoff(rt,entry,rows)
    p=rt.open_positions()[symbol]
    oracle=abs(Fraction(price)-Fraction(entry.stop_price))/Fraction(step)*Fraction(p['instrument_authority']['tick_value'])*3
    assert Fraction(p['actual_initial_loss_cash'])==oracle
    assert p['risk_currency']=='RUB' and p['account_trade_currencies']==['XXX']
    assert p['currency_conversion_performed'] is False
    assert p['reference_entry']!=p['verified_fill_entry']
    assert p['fill_authority']=='FINAM_ACCOUNT_TRADE' and p['protective_covered_quantity']==3
    assert rt.store.intent(entry.idempotency_key)['status']=='RECONCILED'
    assert len(rt.store.fills_for_order(ORDER))==1
    before=rt.store.get('production_positions');rt.close();rt=runtime(path)
    assert rt.open_positions()==before
    handoff(rt,entry,rows)
    assert rt.open_positions()==before and len(rt.store.fills_for_order(ORDER))==1
    assert report['weighted_price_exact']==p['fill_price_exact']
    rt.close()


def test_multiple_fills_nonterminating_mean_exact_even_low_decimal_precision_and_trail1(tmp_path):
    path=tmp_path/'production.db';rt=runtime(path);entry=setup(rt)
    stop=rt.confirm_entry_position(entry.idempotency_key,3);rt.confirm_protective_stop(stop.idempotency_key,'backstop')
    rows=[fill(entry,1,quantity=2),fill(entry,2,price='100.01')]
    with localcontext() as ctx:
        ctx.prec=5
        handoff(rt,entry,rows)
    p=rt.open_positions()['USDRUBF']
    assert Fraction(p['verified_fill_entry'])==Fraction(30001,300)
    assert Fraction(p['actual_initial_loss_cash'])==190
    assert p['fill_price_exact']=={'numerator':'30001','denominator':'300'}
    rt.close();rt=runtime(path)
    # +1R uses exact actual mean, stored stop uses outward execution projection.
    assert rt.manage_completed_bar('USDRUBF',bar(11,'100.12','100','.023',close='100.10'),observed_position_quantity=3) is None
    assert rt.open_positions()['USDRUBF']['trail1']['triggered']
    rt.close();rt=runtime(path)
    replacement=rt.manage_completed_bar('USDRUBF',bar(12,'100.13','100.08','.026',opened='100.10',close='100.12'),observed_position_quantity=3)
    assert replacement and replacement.stop_price==D('100.05')
    rt.confirm_protective_stop(replacement.idempotency_key,'tighter-backstop')
    assert rt.manage_completed_bar('USDRUBF',bar(13,'100.14','100.08','.028',opened='100.12',close='100.12'),observed_position_quantity=3) is None
    gap=rt.manage_completed_bar('USDRUBF',bar(14,'100.04','99.98','.028',opened='100',close='100.01'),observed_position_quantity=3)
    assert gap.kind=='EMERGENCY_EXIT_REQUIRED' and gap.reference_price==D('100')
    rt.close()


def test_partial_protection_precedes_price_and_growth_preserves_backstop_halts(tmp_path):
    """Unknown extra fills never turn an unverified 1-contract stop into 3-contract protection.

    The durable broker-quantity observation is kept separately for operator
    recovery. Local *reconciled* quantity stays 1 and cannot be managed as 3.
    """
    path=tmp_path/'production.db';rt=runtime(path);entry=setup(rt)
    stop=rt.confirm_entry_position(entry.idempotency_key,1)
    assert stop.quantity==1 and stop.expected_position_quantity==1 and stop.stop_price==entry.stop_price
    assert percent_position_stop_payload(stop)['quantity_sl']=={'value':'100'}
    assert rt.open_positions()['USDRUBF']['verified_fill_entry'] is None
    rt.confirm_protective_stop(stop.idempotency_key,'original-backstop')
    handoff(rt,entry,[fill(entry)])
    assert rt.store.intent(entry.idempotency_key)['status']=='PARTIAL_FILL'
    assert rt._aggregate_open_initial_risk()==D('1500')  # full reserved nominal budget
    rt.close();rt=runtime(path)
    assert rt.confirm_entry_position(entry.idempotency_key,1) is None
    assert rt.confirm_entry_position(entry.idempotency_key,3) is None
    handoff(rt,entry,[fill(entry),fill(entry,2,quantity=2,price='100.01')])
    p=rt.open_positions()['USDRUBF']
    assert p['quantity']==1 and p['protective_covered_quantity']==1
    assert p['filled_quantity']==3  # order-linked fills are not discarded
    hold=rt.store.get(f'entry_growth_hold:{entry.idempotency_key}')
    assert hold['observed_quantity']==3 and hold['prior_quantity']==1
    assert hold['reason']=='ACTIVE_PERCENT_STOP_BROKER_PROOF_MISSING'
    assert p['protective_stop_broker_order_id']=='original-backstop'
    assert len([r for r in rt.store.all_intents() if r['payload']['kind'].startswith('PROTECTIVE')])==1
    assert rt.store.get('execution_halt')['operator_intervention_required'] is True
    with pytest.raises(ProductionRuntimeError,match='HALTED'): plan(rt,signal('CNYRUBF'))
    with pytest.raises(ProductionRuntimeError,match='HALTED'):
        rt.manage_completed_bar('USDRUBF',bar(11,'100.12','100','.023',close='100.10'),observed_position_quantity=3)
    rt.close();rt=runtime(path)
    assert rt.store.get('execution_halt')['status']=='HALTED'
    assert rt.store.get(f'entry_growth_hold:{entry.idempotency_key}')==hold
    assert rt.open_positions()['USDRUBF']['quantity']==1
    assert rt.open_positions()['USDRUBF']['protective_stop_broker_order_id']=='original-backstop'
    assert rt.confirm_entry_position(entry.idempotency_key,3) is None  # sticky operator hold
    rt.close()


def test_exact_duplicate_dedup_conflict_rollback_and_trade_id_cross_order_conflict(tmp_path):
    rt=runtime(tmp_path/'production.db');entry=setup(rt);rt.confirm_entry_position(entry.idempotency_key,3)
    rows=[fill(entry,1),fill(entry,2,quantity=2)]
    handoff(rt,entry,rows+[rows[0]])
    assert len(rt.store.fills_for_order(ORDER))==2
    before=rt.open_positions();history=rt.store.get(f'entry_fill_history:{entry.idempotency_key}')
    with pytest.raises(RuntimeError,match='CONFLICTING_DURABLE_FILL'):
        handoff(rt,entry,[fill(entry,1,price='100.01'),rows[1]])
    assert rt.open_positions()==before and rt.store.get(f'entry_fill_history:{entry.idempotency_key}')==history
    with pytest.raises(RuntimeError,match='CONFLICTING_DUPLICATE_FILL'):
        handoff(rt,entry,rows+[fill(entry,1,price='100.01')])
    saved=rt.store.fills_for_order(ORDER)[0]
    with pytest.raises(RuntimeError,match='CONFLICTING_DURABLE_FILL'):
        rt.store.persist_fill(saved|{'broker_order_id':'other-order'},strict=True)
    rt.close()


@pytest.mark.parametrize('changes',[
    {'account_id':'other'},{'order_id':'other'},{'symbol':'CNYRUBF@RTSX'},{'side':'SIDE_SELL'},
    {'trade_id':''},{'currency':'USD'},{'currency':''},{'price':{'value':'100.001'}},
    {'price':{'value':'NaN'}},{'size':{'value':'0'}},{'size':{'value':'1.5'}},
    {'size':{'value':'4'}},{'timestamp':'2026-01-02T06:59:59Z'},
    {'timestamp':END},
])
def test_bad_fill_identity_time_units_grid_or_quantity_never_claims_price(tmp_path,changes):
    rt=runtime(tmp_path/'production.db');entry=setup(rt);stop=rt.confirm_entry_position(entry.idempotency_key,3)
    rt.confirm_protective_stop(stop.idempotency_key,'safe-backstop')
    try:
        handoff(rt,entry,[fill(entry,quantity=3,**changes)])
    except (RuntimeError,ValueError):
        pass
    p=rt.open_positions()['USDRUBF']
    assert p['verified_fill_entry'] is None and p['actual_initial_loss_cash'] is None
    assert p['protective_stop_broker_order_id']=='safe-backstop'
    assert rt.store.intent(entry.idempotency_key)['status']!='RECONCILED'
    rt.close()


def test_missing_stale_saturated_history_no_price_substitution(tmp_path):
    rt=runtime(tmp_path/'production.db');entry=setup(rt);stop=rt.confirm_entry_position(entry.idempotency_key,3)
    rt.confirm_protective_stop(stop.idempotency_key,'safe-backstop')
    for changes in ({'start':'2026-01-02T07:00:01Z'}, {'observed_at':'2026-01-02T07:02:00Z'}, {'limit':1},
                    {'response':{'trades':[fill(entry,quantity=3)],'next_page_token':'more'}}):
        with pytest.raises(RuntimeError): handoff(rt,entry,[fill(entry,quantity=3)],**changes)
    handoff(rt,entry,[])
    assert rt.open_positions()['USDRUBF']['actual_initial_loss_cash'] is None
    handoff(rt,entry,[fill(entry,quantity=3)])
    with pytest.raises(RuntimeError,match='MISSING_FROM_HISTORY'): handoff(rt,entry,[])
    with pytest.raises(RuntimeError,match='STALE_FILL_HISTORY'):
        handoff(rt,entry,[fill(entry,quantity=3)],end='2026-01-02T07:00:59Z',observed_at='2026-01-02T07:00:59Z')
    assert rt.open_positions()['USDRUBF']['protective_stop_broker_order_id']=='safe-backstop'
    rt.close()


@pytest.mark.parametrize('boundary',['persist_fill','save_positions','history'])
def test_atomic_fill_handoff_crash_rolls_back_every_fact_and_state(tmp_path,monkeypatch,boundary):
    path=tmp_path/'production.db';rt=runtime(path);entry=setup(rt);rt.confirm_entry_position(entry.idempotency_key,3)
    before=rt.open_positions();original_fill=rt.store.persist_fill;original_put=rt.store.put
    def bomb_fill(*args,**kwargs):
        original_fill(*args,**kwargs);raise RuntimeError('offline crash')
    def bomb_save(*args,**kwargs): raise RuntimeError('offline crash')
    def bomb_history(key,value):
        original_put(key,value)
        if key.startswith('entry_fill_history:'): raise RuntimeError('offline crash')
    if boundary=='persist_fill':monkeypatch.setattr(rt.store,'persist_fill',bomb_fill)
    elif boundary=='save_positions':monkeypatch.setattr(rt,'_save_positions',bomb_save)
    else:monkeypatch.setattr(rt.store,'put',bomb_history)
    with pytest.raises(RuntimeError,match='offline crash'): handoff(rt,entry,[fill(entry,quantity=3)])
    assert rt.store.fills_for_order(ORDER)==[] and rt.open_positions()==before
    assert rt.store.get(f'entry_fill_history:{entry.idempotency_key}') is None
    rt.close();rt=runtime(path);handoff(rt,entry,[fill(entry,quantity=3)])
    assert len(rt.store.fills_for_order(ORDER))==1
    rt.close()


@pytest.mark.parametrize('change',['price','cash','v1'])
def test_restart_tamper_and_previous_proposed_revision_fail_closed(tmp_path,change):
    path=tmp_path/'production.db';rt=runtime(path);entry=setup(rt);rt.confirm_entry_position(entry.idempotency_key,3)
    handoff(rt,entry,[fill(entry,quantity=3)])
    if change=='price':
        saved=rt.store.fills_for_order(ORDER)[0]|{'price':'100.01'}
        with rt.store.transaction():rt.store.db.execute('UPDATE fills SET payload=?',(json.dumps(saved),))
    elif change=='cash':
        pos=rt.store.get('production_positions');pos['USDRUBF']['actual_initial_loss_cash_exact']['numerator']='1'
        rt.store.put('production_positions',pos)
    else:
        identity=rt.store.get('database_identity')|{'execution_revision':'STOP_TICK_GRID_V1_PROPOSED','schema_id':'stage8_12_production_runtime.stop_tick_grid.v1'}
        rt.store.put('database_identity',identity)
    rt.close();before=path.read_bytes()
    with pytest.raises(ProductionRuntimeError): runtime(path)
    assert path.read_bytes()==before


@pytest.mark.parametrize('price',['101','99.90'])
def test_market_gap_excess_risk_and_fill_across_stop_halt_without_compensation(tmp_path,price):
    rt=runtime(tmp_path/'production.db');entry=setup(rt);stop=rt.confirm_entry_position(entry.idempotency_key,3)
    rt.confirm_protective_stop(stop.idempotency_key,'backstop')
    handoff(rt,entry,[fill(entry,quantity=3,price=price)])
    assert rt.open_positions()['USDRUBF']['verified_fill_entry'] is not None
    assert rt.store.get('execution_halt')['status']=='HALTED'
    assert len(rt.store.all_intents())==2
    assert rt.open_positions()['USDRUBF']['protective_stop_broker_order_id']=='backstop'
    rt.close()


class SyntheticHistoryAPI:
    def __init__(self):self.rows=[];self.calls=[];self.fail=False
    def trades(self,account_id,**query):
        self.calls.append(('GET_TRADES',account_id,query))
        if self.fail:raise RuntimeError('synthetic unavailable history')
        return {'trades':self.rows}


class SyntheticTransport:
    def __init__(self,events):self.calls=[];self.events=events
    def submit_protective_stop(self,action,*,observed_position_quantity):
        self.events.append('PROTECT_BEFORE_HISTORY');self.calls.append(action)
        assert action.quantity==abs(observed_position_quantity)
        return {'order_id':'synthetic-protective-order'}
    def submit_entry(self,*args,**kwargs):raise AssertionError('ENTRY POST forbidden')
    def cancel_protective_stop_after_flat(self,*args,**kwargs):raise AssertionError('backstop cancellation forbidden')


def svc_setup(tmp_path):
    api=SyntheticHistoryAPI();svc=ProductionService(tmp_path,tmp_path/'data',api,ACCOUNT,'a'*40,
                                                   execution_revision=EXECUTION_REVISION,clock=lambda:NOW)
    entry=setup(svc.runtime);svc.transport=SyntheticTransport(api.calls)
    return svc,api,entry


def snapshot(entry,quantity,stop=None,status='PARTIALLY_FILLED'):
    request={'symbol':entry.finam_symbol,'side':'SIDE_BUY','quantity':{'value':'3'},
             'client_order_id':compact_client_order_id(entry.idempotency_key)}
    orders=[{'order_id':ORDER,'status':status,'order':request}]
    if stop:
        payload=percent_position_stop_payload(stop);payload.pop('schema_id')
        payload['client_order_id']=compact_client_order_id(stop.idempotency_key)
        orders.append({'order_id':'synthetic-protective-order','status':'NEW','sltp_order':payload})
    return Snapshot({'account_id':ACCOUNT},{entry.finam_symbol:quantity} if quantity else {},order_views({'orders':orders}),D('100000'),D('1000000'),NOW)


def test_service_partial_protects_before_unavailable_history_restart_no_duplicate(tmp_path):
    svc,api,entry=svc_setup(tmp_path);api.fail=True;snap=snapshot(entry,1)
    svc._assert_exact_broker_ownership(snap)
    with pytest.raises(ProductionServiceError,match='HALTED'): svc._reconcile_intents(snap)
    assert api.calls[0]=='PROTECT_BEFORE_HISTORY'
    assert len(svc.transport.calls)==1
    stop=svc.transport.calls[0];svc.close()
    svc=ProductionService(tmp_path,tmp_path/'data',api,ACCOUNT,'a'*40,execution_revision=EXECUTION_REVISION,clock=lambda:NOW)
    svc.transport=SyntheticTransport(api.calls);api.fail=False;api.rows=[fill(entry)]
    svc._reconcile_intents(snapshot(entry,1,stop))
    assert svc.transport.calls==[]
    assert svc._protection(snapshot(entry,1,stop))[0]['covered_quantity']==1
    assert svc.runtime.open_positions()['USDRUBF']['fill_authority']=='FINAM_ACCOUNT_TRADE'
    assert svc.runtime.store.get('execution_halt')['status']=='HALTED' # no implicit resume
    svc.close()


def test_growth_before_initial_post_uses_fresh_current_quantity_then_growth_halts(tmp_path):
    """Fresh, order-linked active 100% STOP permits a synthetic 2->3 observation.

    This is *not* physical FINAM dynamic coverage proof, and cannot lift the
    separate real-entry gate. Missing broker STOP evidence is tested below.
    """
    svc,api,entry=svc_setup(tmp_path)
    initial=svc.runtime.confirm_entry_position(entry.idempotency_key,1)
    svc.runtime.confirm_entry_position(entry.idempotency_key,2)
    api.rows=[fill(entry,quantity=2)]
    svc._reconcile_intents(snapshot(entry,2))
    assert len(svc.transport.calls)==1 and svc.transport.calls[0].quantity==2
    actual=svc.transport.calls[0]
    svc._reconcile_intents(snapshot(entry,2,actual))
    assert svc._protection(snapshot(entry,2,actual))[0]['covered_quantity']==2
    api.rows=[fill(entry,quantity=2),fill(entry,2)]
    svc._reconcile_intents(snapshot(entry,3,actual,status='FILLED'))
    coverage=svc._protection(snapshot(entry,3,actual,status='FILLED'))
    assert coverage[0]['covered_quantity']==3
    assert coverage[0]['active_stop_order_ids']==['synthetic-protective-order']
    assert len(svc.transport.calls)==1
    p=svc.runtime.open_positions()['USDRUBF']
    assert p['quantity']==3 and p['protective_covered_quantity']==3
    assert p['protective_stop_broker_order_id']=='synthetic-protective-order'
    proof=svc.runtime.store.get(f'entry_growth_stop_observed:{entry.idempotency_key}')
    assert proof['from_quantity']==2 and proof['to_quantity']==3
    assert proof['quantity_measure']=='SLTP_QTY_MEASURE_PERCENT'
    assert proof['quantity_percent']=='100'
    assert proof['evidence']=='CURRENT_ACCOUNT_ORDERS_SNAPSHOT'
    assert proof['real_finam_dynamic_coverage_proven'] is False
    assert svc.runtime.store.get('execution_halt') is None
    svc.close()
    # Restart must not silently drop the broker-matched STOP or coverage proof.
    svc=ProductionService(tmp_path,tmp_path/'data',api,ACCOUNT,'a'*40,
                          execution_revision=EXECUTION_REVISION,clock=lambda:NOW)
    svc.transport=SyntheticTransport(api.calls)
    assert svc.runtime.store.get(f'entry_growth_stop_observed:{entry.idempotency_key}')==proof
    assert svc._protection(snapshot(entry,3,actual,status='FILLED'))[0]['covered_quantity']==3
    assert len(svc.transport.calls)==0
    svc.close()


def test_growth_without_fresh_broker_stop_halts_and_preserves_backstop(tmp_path):
    """Same 2->3 exposure cannot be accepted from local ACK or stale coverage."""
    svc,api,entry=svc_setup(tmp_path)
    svc.runtime.confirm_entry_position(entry.idempotency_key,2)
    api.rows=[fill(entry,quantity=2)]
    svc._reconcile_intents(snapshot(entry,2))
    assert len(svc.transport.calls)==1
    stop=svc.transport.calls[0]
    svc._reconcile_intents(snapshot(entry,2,stop))
    api.rows=[fill(entry,quantity=2),fill(entry,2)]
    with pytest.raises(ProductionServiceError,match='GROWTH_OPERATOR_HOLD'):
        svc._reconcile_intents(snapshot(entry,3,status='FILLED'))  # no active SLTP order
    held=svc.runtime.store.get(f'entry_growth_hold:{entry.idempotency_key}')
    assert held['observed_quantity']==3 and held['prior_quantity']==2
    assert svc.runtime.store.get('execution_halt')['status']=='HALTED'
    assert svc.runtime.open_positions()['USDRUBF']['quantity']==2
    assert svc.runtime.open_positions()['USDRUBF']['protective_stop_broker_order_id']=='synthetic-protective-order'
    assert len(svc.transport.calls)==1  # no duplicate STOP or guessed emergency market order
    svc.close()


def test_terminal_partial_and_flat_with_open_entry_preserve_backstop(tmp_path):
    svc,api,entry=svc_setup(tmp_path);api.rows=[fill(entry)]
    svc._reconcile_intents(snapshot(entry,1));stop=svc.transport.calls[0]
    svc._reconcile_intents(snapshot(entry,1,stop,status='CANCELLED'))
    assert svc.runtime.store.intent(entry.idempotency_key)['status']=='RECONCILED'
    assert svc._protection(snapshot(entry,1,stop,status='CANCELLED'))[0]['covered_quantity']==1
    svc.close()
    svc,api,entry=svc_setup(tmp_path/'second');api.rows=[fill(entry)]
    svc._reconcile_intents(snapshot(entry,1));stop=svc.transport.calls[0]
    svc._reconcile_intents(snapshot(entry,1,stop))
    flat=snapshot(entry,0,stop)
    with pytest.raises(ProductionServiceError,match='HALTED'):svc._flat_cleanup_and_exit(flat)
    assert svc.runtime.open_positions()['USDRUBF']['protective_stop_broker_order_id']=='synthetic-protective-order'
    svc.close()


@pytest.mark.parametrize('status',['SUBMITTED','UNCERTAIN','ACK'])
def test_uncertain_entry_and_stop_never_reposted_after_restart(tmp_path,status):
    svc,api,entry=svc_setup(tmp_path);svc.runtime.store.transition_intent(entry.idempotency_key,status,ORDER)
    with pytest.raises(ProductionServiceError,match='HALTED'):svc._reconcile_intents(replace(snapshot(entry,0),orders=[]))
    assert svc.transport.calls==[]
    stop=svc.runtime.confirm_entry_position(entry.idempotency_key,1)
    svc.runtime.store.transition_intent(stop.idempotency_key,status,'unknown-stop')
    svc.close();svc=ProductionService(tmp_path,tmp_path/'data',api,ACCOUNT,'a'*40,execution_revision=EXECUTION_REVISION,clock=lambda:NOW)
    svc.transport=SyntheticTransport(api.calls);api.rows=[fill(entry)]
    with pytest.raises(ProductionServiceError,match='UNCERTAIN_STOP'):svc._reconcile_intents(snapshot(entry,1))
    assert svc.transport.calls==[]
    svc.close()


def test_reconcile_entry_during_and_after_trail_replacement_keeps_exact_mean(tmp_path):
    svc,api,entry=svc_setup(tmp_path);api.rows=[fill(entry,quantity=2),fill(entry,2,price='100.01')]
    svc._reconcile_intents(snapshot(entry,3,status='FILLED'));initial=svc.transport.calls[0]
    svc._reconcile_intents(snapshot(entry,3,initial,status='FILLED'))
    svc.runtime.manage_completed_bar('USDRUBF',bar(11,'100.12','100','.023',close='100.10'),observed_position_quantity=3)
    replacement=svc.runtime.manage_completed_bar('USDRUBF',bar(12,'100.13','100.08','.026',opened='100.10',close='100.12'),observed_position_quantity=3)
    assert svc.runtime.open_positions()['USDRUBF']['protective_stop_state']=='PENDING_REPLACE'
    row=svc.runtime.store.intent(entry.idempotency_key)
    snap=snapshot(entry,3,initial,status='FILLED')
    svc._reconcile_candidate_entry(row,entry,snap.orders[0],snap)
    assert svc.runtime.store.get('execution_halt') is None
    assert Fraction(svc.runtime.open_positions()['USDRUBF']['trail1']['entry_price'])==Fraction(30001,300)
    svc.runtime.confirm_protective_stop(replacement.idempotency_key,'replacement-backstop')
    handoff(svc.runtime,entry,api.rows)
    assert svc.runtime.store.get('execution_halt') is None
    svc.close()


def test_position_changes_after_reconcile_cannot_claim_protection(tmp_path):
    svc,api,entry=svc_setup(tmp_path);api.rows=[fill(entry)]
    svc._reconcile_intents(snapshot(entry,1));stop=svc.transport.calls[0]
    svc._reconcile_intents(snapshot(entry,1,stop))
    with pytest.raises(ProductionServiceError,match='POSITION_RECONCILIATION_MISMATCH'):
        svc._protection(snapshot(entry,2,stop))
    assert svc.runtime.store.get('execution_halt')['status']=='HALTED'
    assert len(svc.transport.calls)==1
    svc.close()


def test_submission_boundary_idempotent_and_atomic_before_post(tmp_path,monkeypatch):
    rt=runtime(tmp_path/'production.db');entry=plan(rt,cash=D('300'))
    original=rt.store.transition_intent
    def bomb(*args,**kwargs):original(*args,**kwargs);raise RuntimeError('crash before post')
    with monkeypatch.context() as mp:
        mp.setattr(rt.store,'transition_intent',bomb)
        with pytest.raises(RuntimeError,match='crash'):rt.record_entry_submission(entry.idempotency_key,ACCOUNT,START)
    assert rt.store.get(f'entry_submission:{entry.idempotency_key}') is None
    assert rt.store.intent(entry.idempotency_key)['status']=='INTENT_PERSISTED'
    rt.record_entry_submission(entry.idempotency_key,ACCOUNT,START)
    rt.store.transition_intent(entry.idempotency_key,'ACK',ORDER)
    rt.record_entry_submission(entry.idempotency_key,ACCOUNT,START)
    assert rt.store.intent(entry.idempotency_key)['status']=='ACK'
    with pytest.raises(RuntimeError,match='ALREADY_COMMITTED'):
        rt.record_entry_submission(entry.idempotency_key,ACCOUNT,END)
    rt.close()


def test_restart_rejects_sql_columns_that_conflict_with_fill_payload(tmp_path):
    path=tmp_path/'production.db';rt=runtime(path);entry=setup(rt);rt.confirm_entry_position(entry.idempotency_key,3)
    handoff(rt,entry,[fill(entry,quantity=3)])
    with rt.store.transaction():rt.store.db.execute("UPDATE fills SET price='100.01'")
    rt.close()
    with pytest.raises(ProductionRuntimeError,match='EXECUTION_POSITION_STATE_INVALID') as failure:runtime(path)
    assert 'DURABLE_FILL_COLUMNS_CONFLICT' in str(failure.value.__cause__)


def test_bounded_query_uses_existing_transport_only_get_and_encodes_fields():
    from TradingSystemLab.stage8_robot.finam_api import FinamAPI
    from urllib.parse import urlsplit,parse_qs
    class Body:body={'trades':[]}
    api=FinamAPI('synthetic-no-network-secret');calls=[]
    api._request=lambda method,path:(calls.append((method,path)) or Body())
    assert api.trades(ACCOUNT,start=START,end=END,limit=37)=={'trades':[]}
    assert calls[0][0]=='GET'
    assert urlsplit(calls[0][1]).path.endswith('/trades')
    assert parse_qs(urlsplit(calls[0][1]).query)=={'limit':['37'],'interval.start_time':[START],'interval.end_time':[END]}
    with pytest.raises(ValueError):api.trades(ACCOUNT,start=START,end=START)
    assert len(calls)==1


def test_intel_observation_is_user_supplied_not_independent_byte_audit():
    # This is a synthetic regression for the reported shape, not the Intel report bytes.
    row={'trade_id':'synthetic-intel-shape','order_id':ORDER,'account_id':ACCOUNT,'symbol':'CNYRUBF@RTSX',
         'side':'SIDE_BUY','size':{'value':'1'},'price':{'value':'12.748'},'currency':'XXX',
         'timestamp':'2026-01-02T07:00:01Z'}
    report=analyze_history({'trades':[row]},Target(ACCOUNT,'synthetic',ORDER,'CNYRUBF@RTSX','SIDE_BUY',1,D('.001')),START,END,1000)
    assert report['weighted_price_exact']=={'numerator':'3187','denominator':'250'}
    assert report['account_trade_currencies']==['XXX'] and report['currency_conversion_performed'] is False


def test_protective_coverage_cannot_be_silently_promoted_in_durable_state(tmp_path):
    path=tmp_path/'production.db';rt=runtime(path);entry=setup(rt)
    stop=rt.confirm_entry_position(entry.idempotency_key,1);rt.confirm_protective_stop(stop.idempotency_key,'backstop')
    pos=rt.store.get('production_positions');pos['USDRUBF']['protective_covered_quantity']=3
    rt.store.put('production_positions',pos);rt.close()
    with pytest.raises(ProductionRuntimeError,match='EXECUTION_POSITION_STATE_INVALID'):runtime(path)


def test_unknown_instrument_money_semantics_fail_closed_without_currency_conversion(tmp_path):
    rt=runtime(tmp_path/'production.db');rt.registry['CNYRUBF']['currency']='XXX'
    with pytest.raises(ProductionRuntimeError,match='INSTRUMENT_AUTHORITY_NOT_FROZEN'):plan(rt,signal('CNYRUBF'))
    assert rt.store.all_intents()==[]
    rt.close()


def test_position_account_authority_must_match_before_orders_read(tmp_path):
    svc,api,entry=svc_setup(tmp_path)
    api.account=lambda _: {'account_id':'foreign','status':'ACCOUNT_ACTIVE','positions':[]}
    with pytest.raises(ProductionServiceError,match='POSITION_ACCOUNT_IDENTITY_UNVERIFIED'):svc.snapshot(NOW)
    assert svc.runtime.store.get('execution_halt')['status']=='HALTED'
    svc.close()


def test_halt_reconciles_protection_but_never_posts_pending_ordinary_trail(tmp_path):
    svc,api,entry=svc_setup(tmp_path);api.rows=[fill(entry,quantity=3)]
    svc._reconcile_intents(snapshot(entry,3,status='FILLED'));initial=svc.transport.calls[0]
    svc._reconcile_intents(snapshot(entry,3,initial,status='FILLED'))
    svc.runtime.manage_completed_bar('USDRUBF',bar(11,'100.12','100','.023',close='100.10'),observed_position_quantity=3)
    replacement=svc.runtime.manage_completed_bar('USDRUBF',bar(12,'100.13','100.08','.026',opened='100.10',close='100.12'),observed_position_quantity=3)
    svc.runtime.halt('SYNTHETIC_UNPROVEN_AUTHORITY')
    svc._submit(replacement,snapshot(entry,3,initial,status='FILLED'))
    assert len(svc.transport.calls)==1
    assert svc.runtime.store.intent(replacement.idempotency_key)['status']=='INTENT_PERSISTED'
    assert svc.runtime.open_positions()['USDRUBF']['protective_stop_broker_order_id']=='synthetic-protective-order'
    svc.close()
