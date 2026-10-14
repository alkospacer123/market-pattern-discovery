"""Candidate-only regression tests. All prices/fills/broker ACKs are synthetic."""
from dataclasses import replace
from datetime import datetime
from decimal import Decimal, localcontext
import hashlib
from zoneinfo import ZoneInfo

import pandas as pd
import pytest

from TradingSystemLab.stage8_robot.execution_grid import (
    EXECUTION_REVISION, initial_projection, project_stop, require_on_grid,
)
from TradingSystemLab.stage8_robot.production_runtime import ProductionRuntime, ProductionRuntimeError
from TradingSystemLab.stage8_robot.production_service import ProductionService, ProductionServiceError
from TradingSystemLab.stage8_robot.live_execution import AuthorizedFinamProductionTransport, LiveExecutionError
from TradingSystemLab.stage8_robot.protective_stop_contract import (
    percent_position_stop_payload, ProtectiveStopContractError, SyntheticPercentPositionStopAdapter,
)
from TradingSystemLab.stage8_robot.risk import ContractEconomics, size_position
from TradingSystemLab.stage8_robot.strategy_core import CompletedBar, SignalIntent, order_events
from TradingSystemLab.stage8_robot.tests.test_stage8_12_production_runtime import authority, FROZEN_ECONOMICS

D = Decimal
MSK = ZoneInfo('Europe/Moscow')
SYMBOLS = tuple(FROZEN_ECONOMICS)


def runtime(path):
    return ProductionRuntime(path, execution_revision=EXECUTION_REVISION)


def signal(symbol='USDRUBF', side='LONG', ticks='5.1', hour=10):
    a = authority(symbol)
    entry = D('100')
    stop = entry + (-1 if side == 'LONG' else 1) * D(ticks) * a.price_step
    return SignalIntent(f'sig-{symbol}-{side}-{hour}', f'trade-{symbol}-{side}-{hour}', symbol, side,
                        datetime(2026, 1, 2, hour, tzinfo=MSK), entry, stop, abs(entry-stop), stop)


def plan(rt, sig=None, *, equity=D('100000'), cash=D('1000000'), budget=None):
    sig = sig or signal()
    budget = budget or rt.begin_batch(realized_equity=equity, available_cash=cash)
    return rt.plan_entry(sig, authority(sig.instrument), realized_equity=equity, budget=budget)


def confirm(rt, entry, price=D('100')):
    return rt.confirm_entry_position(entry.idempotency_key, entry.expected_position_quantity,
                                     verified_fill_entry=price, fill_authority='OFFLINE_SYNTHETIC_VERIFIED')


def open_protected(rt, sig=None, price=D('100')):
    entry = plan(rt, sig)
    stop = confirm(rt, entry, price)
    rt.confirm_protective_stop(stop.idempotency_key, 'synthetic-'+entry.instrument)
    return entry


def bar(hour, high, low, atr, opened='100', close='100'):
    return CompletedBar(datetime(2026,1,2,hour,tzinfo=MSK), D(opened), D(high), D(low), D(close), D(atr))


@pytest.mark.parametrize('symbol', SYMBOLS)
@pytest.mark.parametrize('side', ['LONG', 'SHORT'])
@pytest.mark.parametrize('ticks', ['5', '5.1', '5.999999999999999999999999'])
def test_n4_projection_sizing_persist_and_initial_protection(tmp_path, symbol, side, ticks):
    rt = runtime(tmp_path/'state.db')
    sig = signal(symbol, side, ticks)
    before = sig
    a = plan(rt, sig)
    assert a.kind == 'ENTRY' and sig == before
    expected = sig.entry + (-1 if side == 'LONG' else 1)*D(5 if ticks == '5' else 6)*authority(symbol).price_step
    assert a.stop_price == expected
    p = rt.store.intent(a.idempotency_key)['payload']
    assert p['raw_initial_stop'] == str(sig.initial_stop)
    assert p['raw_initial_r'] == str(sig.initial_r)
    assert D(p['executable_initial_r']) == abs(sig.entry-expected)
    assert D(p['reference_initial_loss_cash']) <= D('1500')
    assert p['verified_fill_entry'] is None and p['actual_initial_loss_cash'] is None
    assert p['signal_id'] == sig.signal_id and p['trade_id'] == sig.trade_id
    stop = confirm(rt, a)
    payload = percent_position_stop_payload(stop)
    require_on_grid(payload['sl_price']['value'], authority(symbol).price_step)
    rt.close()


@pytest.mark.parametrize('side,price,expected', [('LONG','99.949','99.94'), ('SHORT','100.051','100.06'),
                                              ('LONG','99.95','99.95'), ('SHORT','100.05','100.05')])
def test_integer_decimal_projection_independent_of_context(side, price, expected):
    with localcontext() as context:
        context.prec = 3
        assert project_stop(side, D(price), D('.01')) == D(expected)
        assert project_stop(side, D('99.95000000000000000000000000001'), D('.01')) == (
            D('99.95') if side == 'LONG' else D('99.96'))


@pytest.mark.parametrize('entry,stop,step,side', [
    ('100.001','99.941','.01','LONG'), ('NaN','99','.01','LONG'), ('100','Infinity','.01','LONG'),
    ('100','99','0','LONG'), ('100','101','.01','LONG'), ('100','99','.01','SHORT'),
    ('100','0','.01','LONG'), ('100','99','.01','BAD'),
])
def test_invalid_prices_and_entry_are_fail_closed(entry,stop,step,side):
    with pytest.raises(ValueError): initial_projection(side,D(entry),D(stop),D(step))


@pytest.mark.parametrize('side', ['LONG','SHORT'])
def test_r15_floor_margin_zero_and_local_reservation(tmp_path, side):
    rt = runtime(tmp_path/'state.db')
    cash = D('250') if side == 'LONG' else D('300')
    budget = rt.begin_batch(realized_equity=D('100000'), available_cash=cash)
    a = plan(rt, signal(side=side), budget=budget)
    assert a.quantity == 2
    assert budget.remaining == cash - 2*authority().initial_margin(side)
    rt.close()
    rt = runtime(tmp_path/'zero.db')
    assert plan(rt, signal(side=side), equity=D('1')).kind == 'SKIP_ZERO_CAPACITY'
    assert rt.store.all_intents() == []
    rt.close()
    sized = size_position(D('100000'), D('100'), D('99.94'), ContractEconomics(D('.01'),D('10'),3,True))
    assert sized.quantity == 24 and sized.quantity*sized.loss_per_contract <= D('1500')


def test_full_nominal_aggregate_six_percent_and_no_pyramiding(tmp_path):
    rt = runtime(tmp_path/'state.db')
    for symbol in SYMBOLS:
        open_protected(rt, signal(symbol))
    assert rt._aggregate_open_initial_risk() == D('6000')
    with pytest.raises(ProductionRuntimeError, match='PYRAMIDING'): plan(rt)
    rt.broker_exit_observed('USDRUBF', realized_equity_after_exit=D('75000'), protective_stop_terminal=True)
    assert plan(rt, signal(hour=11), equity=D('75000')).kind == 'SKIP_RISK_LIMIT'
    rt.close()


@pytest.mark.parametrize('side', ['LONG','SHORT'])
def test_stored_candidate_next_event_tighten_duplicate_rounding_and_gap(tmp_path, side):
    rt = runtime(tmp_path/'state.db')
    entry = open_protected(rt, signal(side=side))
    observed = entry.expected_position_quantity
    first = bar(11,'100.12','100','.023',close='100.10') if side == 'LONG' else bar(11,'100','99.88','.023',close='99.90')
    assert rt.manage_completed_bar('USDRUBF', first, observed_position_quantity=observed) is None
    p = rt.open_positions()['USDRUBF']
    stored = D(p['trail1']['stored_candidate'])
    assert stored == (D('100.05') if side == 'LONG' else D('99.95'))
    assert p['trail1']['triggered'] and not p['trail1']['activated']
    rt.close(); rt = runtime(tmp_path/'state.db')
    second = bar(12,'100.12','100.06','.023',opened='100.10',close='100.10') if side == 'LONG' else bar(12,'99.94','99.88','.023',opened='99.90',close='99.90')
    update = rt.manage_completed_bar('USDRUBF', second, observed_position_quantity=observed)
    assert update.kind == 'PROTECTIVE_STOP_REPLACE' and update.stop_price == stored
    rt.confirm_protective_stop(update.idempotency_key,'stop-1')
    third = replace(second, timestamp=datetime(2026,1,2,13,tzinfo=MSK), atr=D('.022'))
    assert rt.manage_completed_bar('USDRUBF', third, observed_position_quantity=observed) is None
    assert len([x for x in rt.store.all_intents() if x['payload']['kind']=='PROTECTIVE_STOP_REPLACE']) == 1
    # A later looser candidate cannot loosen the executable stop.
    fourth = replace(third, timestamp=datetime(2026,1,2,14,tzinfo=MSK), atr=D('.04'))
    assert rt.manage_completed_bar('USDRUBF', fourth, observed_position_quantity=observed) is None
    gap = bar(15,'100.05','99.8','.02',opened='99.90',close='99.90') if side=='LONG' else bar(15,'100.2','99.95','.02',opened='100.10',close='100.10')
    exit_action = rt.manage_completed_bar('USDRUBF', gap, observed_position_quantity=observed)
    assert exit_action.kind == 'EMERGENCY_EXIT_REQUIRED'
    assert exit_action.reference_price == D('99.90' if side=='LONG' else '100.10')
    assert rt.open_positions()['USDRUBF']['trail1']['gap_through_activated_trail']
    assert [x['type'] for x in order_events([{'timestamp':1,'type':'ENTRY','identity':'a'},{'timestamp':1,'type':'EXIT','identity':'b'}])] == ['EXIT','ENTRY']
    rt.close()


def test_no_retroactive_exit_and_protection_before_retirement(tmp_path):
    rt = runtime(tmp_path/'state.db'); entry = plan(rt)
    stop = confirm(rt,entry); adapter = SyntheticPercentPositionStopAdapter()
    oid = adapter.submit(stop,observed_position_quantity=entry.quantity)
    rt.confirm_protective_stop(stop.idempotency_key,oid)
    # Current low is below this bar's new candidate but above pre-event stop.
    assert rt.manage_completed_bar('USDRUBF',bar(11,'100.12','99.98','.02'),observed_position_quantity=entry.quantity) is None
    update = rt.manage_completed_bar('USDRUBF',bar(12,'100.13','100.07','.02',opened='100.10',close='100.10'),observed_position_quantity=entry.quantity)
    new_oid = adapter.submit(update,observed_position_quantity=entry.quantity)
    assert len(adapter.active_stops('USDRUBF',entry.trade_id)) == 2
    rt.confirm_protective_stop(update.idempotency_key,new_oid)
    assert adapter.trigger('USDRUBF',entry.trade_id,observed_position_quantity=entry.quantity,price=D('99')) == 0
    assert adapter.trigger('USDRUBF',entry.trade_id,observed_position_quantity=0,price=D('99')) == 0
    rt.close()


def test_fill_reference_separate_actual_risk_not_guaranteed(tmp_path):
    rt = runtime(tmp_path/'state.db'); entry = plan(rt)
    confirm(rt,entry,D('100.025'))
    p = rt.open_positions()['USDRUBF']
    assert p['reference_entry'] == '100' and p['verified_fill_entry'] == '100.025'
    assert D(p['actual_initial_r']) == D('.085')
    assert D(p['actual_initial_loss_cash']) > D('1500')
    assert D(p['reference_initial_loss_cash']) <= D('1500')
    with pytest.raises(ProductionRuntimeError,match='FILL_AUTHORITY_CHANGED'):
        confirm(rt,entry,D('100.026'))
    rt.close()


def test_missing_fill_preserves_initial_protection_blocks_management_and_new_entry(tmp_path):
    rt = runtime(tmp_path/'state.db'); entry = plan(rt)
    with pytest.raises(ProductionRuntimeError,match='FILL_AUTHORITY_UNVERIFIED'):
        rt.confirm_entry_position(entry.idempotency_key,entry.quantity,verified_fill_entry=D('100'),fill_authority='FINAM_ASSUMED')
    stop = rt.confirm_entry_position(entry.idempotency_key,entry.quantity)
    rt.confirm_protective_stop(stop.idempotency_key,'backstop')
    assert rt.open_positions()['USDRUBF']['actual_initial_loss_cash'] is None
    with pytest.raises(ProductionRuntimeError,match='UNRESOLVED_INTENT_BLOCKS_BAR'):
        rt.manage_completed_bar('USDRUBF',bar(11,'101','100','1'),observed_position_quantity=entry.quantity)
    with pytest.raises(ProductionRuntimeError,match='ACTUAL_FILL_AUTHORITY_BLOCKS_NEW'): plan(rt,signal('CNYRUBF'))
    rt.close(); rt = runtime(tmp_path/'state.db')
    assert rt.confirm_entry_position(entry.idempotency_key,entry.quantity) is None
    assert len(rt.store.all_intents()) == 2
    rt.close()


@pytest.mark.parametrize('status',['INTENT_PERSISTED','SUBMITTED','UNCERTAIN','ACK'])
def test_restart_before_post_uncertain_and_ack_no_duplicate(tmp_path,status):
    rt = runtime(tmp_path/'state.db'); entry=plan(rt)
    rt.store.transition_intent(entry.idempotency_key,status)
    rt.close(); rt=runtime(tmp_path/'state.db')
    assert rt.confirm_entry_position(entry.idempotency_key,0) is None
    with pytest.raises(ProductionRuntimeError,match='UNRESOLVED_INTENT'): plan(rt)
    stop=confirm(rt,entry)
    rt.close(); rt=runtime(tmp_path/'state.db')
    assert confirm(rt,entry)==stop
    rt.store.transition_intent(stop.idempotency_key,'UNCERTAIN')
    rt.close(); rt=runtime(tmp_path/'state.db')
    assert confirm(rt,entry)==stop
    rt.confirm_protective_stop(stop.idempotency_key,'stop-0')
    rt.confirm_protective_stop(stop.idempotency_key,'stop-0')
    assert confirm(rt,entry) is None
    assert len(rt.store.all_intents())==2
    rt.close()


@pytest.mark.parametrize('boundary',['entry_consume','position_before_stop','stop_before_position','replacement_after_watermark'])
def test_crash_transactions_rollback_critical_boundaries(tmp_path,monkeypatch,boundary):
    rt=runtime(tmp_path/'state.db')
    if boundary=='entry_consume':
        original=rt._consume_pending_signal
        def fail(sig): original(sig); raise RuntimeError('CRASH')
        monkeypatch.setattr(rt,'_consume_pending_signal',fail)
        with pytest.raises(RuntimeError,match='CRASH'): plan(rt)
        assert rt.store.all_intents()==[]
    elif boundary=='position_before_stop':
        entry=plan(rt); original=rt.store.persist_intent
        def fail(key,payload):
            if payload['kind']=='PROTECTIVE_STOP_INSTALL': raise RuntimeError('CRASH')
            return original(key,payload)
        monkeypatch.setattr(rt.store,'persist_intent',fail)
        with pytest.raises(RuntimeError,match='CRASH'): confirm(rt,entry)
        assert rt.open_positions()=={}
        assert rt.store.intent(entry.idempotency_key)['status']=='INTENT_PERSISTED'
    elif boundary=='stop_before_position':
        entry=plan(rt); stop=confirm(rt,entry)
        monkeypatch.setattr(rt,'_save_positions',lambda positions: (_ for _ in ()).throw(RuntimeError('CRASH')))
        with pytest.raises(RuntimeError,match='CRASH'): rt.confirm_protective_stop(stop.idempotency_key,'stop-0')
        assert rt.store.intent(stop.idempotency_key)['status']=='INTENT_PERSISTED'
        assert rt.open_positions()['USDRUBF']['protective_stop_state']=='PENDING'
    else:
        entry=open_protected(rt)
        rt.manage_completed_bar('USDRUBF',bar(11,'100.12','100','.023'),observed_position_quantity=entry.quantity)
        before=rt.open_positions(); original=rt.store.persist_intent
        def fail(key,payload):
            if payload['kind']=='PROTECTIVE_STOP_REPLACE': raise RuntimeError('CRASH')
            return original(key,payload)
        monkeypatch.setattr(rt.store,'persist_intent',fail)
        with pytest.raises(RuntimeError,match='CRASH'):
            rt.manage_completed_bar('USDRUBF',bar(12,'100.12','100.06','.023',opened='100.10',close='100.10'),observed_position_quantity=entry.quantity)
        assert rt.open_positions()==before
        assert rt.store.get('last_managed_h1:USDRUBF')==datetime(2026,1,2,11,tzinfo=MSK).isoformat()
    rt.close(); restored=runtime(tmp_path/'state.db'); restored.close()


def test_legacy_and_corrupt_fingerprint_no_silent_migration(tmp_path):
    path=tmp_path/'legacy.db'; old=ProductionRuntime(path)
    old_entry=plan(old,signal(ticks='5'))
    old.confirm_entry_position(old_entry.idempotency_key,old_entry.quantity)
    old.close()
    digest=hashlib.sha256(path.read_bytes()).hexdigest()
    with pytest.raises(ProductionRuntimeError,match='REVISION_MISMATCH'): runtime(path)
    assert hashlib.sha256(path.read_bytes()).hexdigest()==digest
    rt=runtime(tmp_path/'amended.db'); entry=plan(rt)
    p=rt.store.intent(entry.idempotency_key)['payload']; p['specification_fingerprint']='bad'
    import json
    with rt.store.transaction(): rt.store.db.execute('UPDATE intents SET payload=?',(json.dumps(p),))
    rt.close()
    with pytest.raises(ProductionRuntimeError,match='DURABLE_EVIDENCE_INVALID'): runtime(tmp_path/'amended.db')


def test_candidate_real_submission_blocked_without_calls(tmp_path):
    service=ProductionService(tmp_path/'service',tmp_path/'data',object(),'offline-account','a'*40,
                              execution_revision=EXECUTION_REVISION)
    entry=plan(service.runtime)
    class NoOrders:
        def submit_entry(self,*args,**kwargs): raise AssertionError('ORDER_METHOD_CALLED')
    service.transport=NoOrders()
    with pytest.raises(ProductionServiceError,match='ACTUAL_FILL_AUTHORITY_BLOCKED'):
        service._submit(entry,None)
    assert service.runtime.store.intent(entry.idempotency_key)['status']=='INTENT_PERSISTED'
    adapter=object.__new__(AuthorizedFinamProductionTransport)
    with pytest.raises(LiveExecutionError,match='ACTUAL_FILL_AUTHORITY_BLOCKED'): adapter.submit_entry(entry,now=None)
    service.close()


def test_protective_payload_rejects_off_grid_candidate(tmp_path):
    rt=runtime(tmp_path/'state.db'); entry=plan(rt); stop=confirm(rt,entry)
    with pytest.raises(ProtectiveStopContractError,match='NOT_ON_TICK_GRID'):
        percent_position_stop_payload(replace(stop,stop_price=D('99.941')))
    rt.close()


@pytest.mark.parametrize('status',['INTENT_PERSISTED','SUBMITTED','UNCERTAIN','ACK'])
def test_replacement_restart_reuses_one_durable_intent(tmp_path,status):
    rt=runtime(tmp_path/'state.db'); entry=open_protected(rt)
    rt.manage_completed_bar('USDRUBF',bar(11,'100.12','100','.023'),observed_position_quantity=entry.quantity)
    update=rt.manage_completed_bar('USDRUBF',bar(12,'100.12','100.06','.023',opened='100.10',close='100.10'),observed_position_quantity=entry.quantity)
    rt.store.transition_intent(update.idempotency_key,status)
    rt.close(); rt=runtime(tmp_path/'state.db')
    with pytest.raises(ProductionRuntimeError,match='UNRESOLVED_INTENT'):
        rt.manage_completed_bar('USDRUBF',bar(13,'100.12','100.06','.023',opened='100.10',close='100.10'),observed_position_quantity=entry.quantity)
    rt.confirm_protective_stop(update.idempotency_key,'synthetic-replacement')
    rt.close(); rt=runtime(tmp_path/'state.db')
    rt.confirm_protective_stop(update.idempotency_key,'synthetic-replacement')
    assert rt.open_positions()['USDRUBF']['protective_stop_revision']==1
    assert len(rt.store.all_intents())==3
    assert rt.manage_completed_bar('USDRUBF',bar(13,'100.12','100.06','.022',opened='100.10',close='100.10'),observed_position_quantity=entry.quantity) is None
    rt.close()


def test_stale_pending_signal_is_not_automatically_rearmed(tmp_path):
    rt=runtime(tmp_path/'state.db')
    rt.store.put('pending_signal:USDRUBF',{'timestamp':datetime(2026,1,2,10,tzinfo=MSK).isoformat()})
    class Builder:
        def build(self,*args): return pd.DataFrame({'Close':[100]},index=pd.DatetimeIndex([datetime(2026,1,2,11,tzinfo=MSK)])),None
    rt.context_builder=Builder()
    with pytest.raises(ProductionRuntimeError,match='STALE_PENDING_SIGNAL'): rt.build_latest_signal('USDRUBF',None,None)
    assert rt.store.all_intents()==[]
    rt.close()


@pytest.mark.parametrize('change',[
    {'price_step':D('NaN')}, {'tick_value':D('Infinity')}, {'long_initial_margin':D('NaN')},
    {'short_initial_margin':D('0')}, {'trade_lot_size':True},
])
def test_invalid_authenticated_specification_never_creates_intent(tmp_path,change):
    rt=runtime(tmp_path/'state.db'); budget=rt.begin_batch(realized_equity=D('100000'),available_cash=D('1000000'))
    with pytest.raises(ProductionRuntimeError):
        rt.plan_entry(signal(),replace(authority(),**change),realized_equity=D('100000'),budget=budget)
    assert rt.store.all_intents()==[] and budget.remaining==D('1000000')
    rt.close()


def test_unconsumed_entry_signal_and_fill_beyond_stop_fail_closed(tmp_path):
    service=ProductionService(tmp_path/'service',tmp_path/'data',object(),'offline','a'*40,execution_revision=EXECUTION_REVISION)
    service.transport=object()
    assert service._plan_entry({},None) is False
    assert service.runtime.store.get('signal_sequence:USDRUBF') is None
    a=plan(service.runtime)
    with pytest.raises(ProductionRuntimeError,match='FILL_BEYOND_INITIAL_STOP'):
        confirm(service.runtime,a,D('99.90'))
    assert service.runtime.open_positions()=={} and len(service.runtime.store.all_intents())==1
    service.close()


def test_incompatible_sqlite_schema_is_not_recreated(tmp_path):
    import sqlite3
    path=tmp_path/'state.db'; rt=runtime(path); rt.close()
    with sqlite3.connect(path) as db: db.execute('DROP TABLE fills')
    digest=hashlib.sha256(path.read_bytes()).hexdigest()
    with pytest.raises(ProductionRuntimeError,match='STATE_REVISION_MISMATCH'): runtime(path)
    assert hashlib.sha256(path.read_bytes()).hexdigest()==digest


def test_lost_reconciled_position_is_not_rebuilt_as_new_revision(tmp_path):
    rt=runtime(tmp_path/'state.db'); a=open_protected(rt)
    rt.store.put('production_positions',{})
    with pytest.raises(ProductionRuntimeError,match='RECONCILED_POSITION_MISSING'): confirm(rt,a)
    assert rt.open_positions()=={} and len(rt.store.all_intents())==2
    rt.close()


def test_older_h1_history_cannot_create_a_new_signal_after_restart(tmp_path):
    rt=runtime(tmp_path/'state.db')
    rt.store.put('last_evaluated_h1:USDRUBF',datetime(2026,1,2,11,tzinfo=MSK).isoformat())
    rt.close(); rt=runtime(tmp_path/'state.db')
    class Builder:
        def build(self,*args):
            return pd.DataFrame({'Close':[100]},index=pd.DatetimeIndex([datetime(2026,1,2,10,tzinfo=MSK)])),None
    rt.context_builder=Builder()
    with pytest.raises(ProductionRuntimeError,match='STALE_OR_NON_MONOTONIC_SIGNAL_H1'): rt.build_latest_signal('USDRUBF',None,None)
    assert rt.store.get('signal_sequence:USDRUBF') is None and rt.store.all_intents()==[]
    rt.close()
