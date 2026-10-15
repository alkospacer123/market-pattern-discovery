"""Wire, identity, time and trading-authority tests using only invented exports."""
from copy import deepcopy
from dataclasses import replace
from datetime import timedelta
import json
import sqlite3
import pytest
from cc.freshness import display_state
from cc.models import ExecutionState, RobotId, SourceKind, State
from cc.providers import h1_readonly as adapter
from cc.providers.h1_contract import MAX_BYTES, SCHEMA
from cc.providers.h1_readonly import H1ReadonlyProvider, SAFE_ERROR
from cc.providers.synthetic import SyntheticProvider


def read(now):
    return H1ReadonlyProvider().snapshot(RobotId.H1, 'ignored', now)


def stamp(at):
    return at.isoformat().replace('+00:00', 'Z')


def evidence(kind, at):
    return dict(kind=kind, reference='a'*64, observed_at=at, complete=True)


def reconciled(value, at):
    value['reconciliation'].update(observed_at=at, last_success_at=at, status='PASS', unresolved_intents=0)


def healthy(value, at):
    reconciled(value, at)
    value['runtime'].update(state='HEALTHY', heartbeat_at=at, last_successful_cycle_at=at)


def order(at, state='ACK'):
    return dict(instrument='USDRUBF', occurred_at=at, reference='b'*64, state=state,
                quantity=2, filled_quantity=None, fill_price=None, evidence=None)


def financial(value, at):
    reconciled(value, at)
    value['finances'].update(observed_at=at, complete=True, evidence=evidence('FIXTURE_ACCOUNT', at),
                             equity=100000, realized_pnl=100, unrealized_pnl=20, commissions=10,
                             deposits=99890, withdrawals=0, available_margin=80000, used_risk_pct=1.5, contracts=2)


def assert_unknown(result):
    assert result.status.state == State.UNKNOWN
    assert result.status.provenance.source_kind == SourceKind.OFFLINE_FIXTURE
    assert result.status.provenance.observed_at is None
    assert result.positions is None and not result.orders and not result.candles
    assert result.portfolio.equity is None
    assert result.events[0].message == SAFE_ERROR


def test_valid_halted_fixture_is_not_live(h1_export, publish, now):
    publish(h1_export)
    result = read(now)
    assert result.status.state == display_state(result.status, now) == State.HALTED
    assert result.status.heartbeat_at is None
    assert result.status.task_state is None  # documented Disabled is not a current probe
    assert result.status.trading_allowed is False
    assert result.status.provenance.source_kind == SourceKind.OFFLINE_FIXTURE
    assert result.status.provenance.synthetic is True
    assert len(result.instruments) == len(result.candles) == 4
    assert all(bar.freshness == State.UNKNOWN for bar in result.h1_readonly.bars)
    assert result.positions is None and result.status.open_positions is None
    assert not result.h1_readonly.orders_complete and not result.signals
    assert all('Причина не опубликована' in row.condition for row in result.instruments)


@pytest.mark.parametrize('path,value', [
    (('schema_id',),'v2'), (('source_kind',),'VERIFIED_LIVE_READONLY'), (('synthetic',),False),
    (('identity','robot_id'),'M15'), (('identity','strategy_id'),'T3/M15/SESSION'),
    (('identity','active_identity'),'OTHER'), (('identity','production_specification_id'),'OTHER'),
    (('identity','accepted_code_commit'),'2695cd3fce6f2241608d1d43d2b7c693ecaba32d'),
    (('identity','account_scope'),'FIXTURE-M15'), (('identity','account_alias'),'RAW-ACCOUNT'),
    (('identity','account_binding'),'0'*64), (('identity','raw_account_id'),'SECRET'),
    (('runtime','trading_permission'),True), (('runtime','state'),'RUNNING'),
    (('runtime','heartbeat_at'),'2026-10-15T18:00:00'),
    (('runtime','heartbeat_at'),'2026-10-15T21:00:00+03:00'),
    (('runtime','heartbeat_at'),'2026-10-15T18:00:00+25:00'),
    (('runtime','heartbeat_at'),'2026-02-30T18:00:00Z'),
    (('complete',),False), (('complete',),1), (('bars',),'bad'),
    (('reconciliation','unresolved_intents'),True), (('reconciliation','unresolved_intents'),-1),
    (('finances','equity'),'100'), (('finances','equity'),float('nan')),
    (('finances','equity'),float('inf')), (('orders','items'),[order('2026-10-15T18:20:00Z')]*65),
    (('finances','evidence'),evidence('BROKER_ACCOUNT','2026-10-15T18:20:00Z')),
])
def test_strict_schema_and_identity(h1_export, publish, now, path, value):
    target = h1_export
    for part in path[:-1]:
        target = target[part]
    target[path[-1]] = value
    publish(h1_export, seal=not (type(value) is float and str(value) in ('nan','inf')))
    assert_unknown(read(now))


@pytest.mark.parametrize('group', list(SCHEMA['properties']))
def test_every_envelope_field_required(group, h1_export, publish, now):
    del h1_export[group]
    publish(h1_export, seal=False)
    assert_unknown(read(now))


@pytest.mark.parametrize('payload', [b'', b'{', b'{"partial":', b'[]', b'null', b'\xff',
                                     b'{"x":1,"x":2}', b' '* (MAX_BYTES+1)])
def test_corrupt_empty_partial_oversize(payload, publish, h1_export, now):
    path = publish(h1_export)
    path.write_bytes(payload)
    assert_unknown(read(now))


def test_checksum_catches_valid_but_torn_publication(h1_export, publish, now):
    publish(h1_export)
    h1_export['runtime']['state'] = 'HEALTHY'
    publish(h1_export, seal=False)
    assert_unknown(read(now))


def test_schema_document_matches_runtime():
    from pathlib import Path
    assert json.loads((Path(__file__).parents[1]/'docs/H1_READONLY_SNAPSHOT_SCHEMA.json').read_text()) == SCHEMA


def test_stale_cannot_become_new_healthy_on_browser_refresh(h1_export, publish, now):
    healthy(h1_export, stamp(now))
    publish(h1_export)
    first = read(now)
    assert display_state(first.status, now) == State.HEALTHY
    stale = read(now+timedelta(seconds=181))
    assert stale.status.state == display_state(stale.status, now+timedelta(seconds=181)) == State.STALE
    assert stale.status.provenance.observed_at == first.status.provenance.observed_at
    assert stale.status.provenance.received_at > first.status.provenance.received_at
    assert stale.positions is None and not stale.orders and not stale.candles
    assert not stale.signals and stale.portfolio.equity is None


@pytest.mark.parametrize('field', ['generated_at','observed_at'])
def test_future_envelope(field, h1_export, publish, now):
    h1_export[field] = stamp(now+timedelta(seconds=3))
    publish(h1_export)
    assert_unknown(read(now))


@pytest.mark.parametrize('field', ['heartbeat_at','last_successful_cycle_at'])
def test_old_runtime_field_does_not_get_freshened(field, h1_export, publish, now):
    healthy(h1_export, stamp(now))
    h1_export['runtime'][field] = stamp(now-timedelta(seconds=91))
    publish(h1_export)
    assert read(now).status.state == State.STALE


def test_halted_does_not_treat_stopped_heartbeat_as_fault(h1_export, publish, now):
    h1_export['runtime']['heartbeat_at'] = stamp(now-timedelta(days=1))
    publish(h1_export)
    assert read(now).status.state == State.HALTED
    assert read(now+timedelta(seconds=181)).status.state == State.STALE


def test_per_group_times_and_ttls(h1_export, publish, now):
    financial(h1_export, stamp(now-timedelta(seconds=250)))
    healthy(h1_export, stamp(now))  # fresh reconciliation/heartbeat; older complete finance
    publish(h1_export)
    result = read(now)
    assert result.status.state == State.HEALTHY
    assert result.portfolio.equity == 100000
    states = {row.name:row for row in result.h1_readonly.observations}
    assert states['finances'].observed_at == now-timedelta(seconds=250)
    assert states['finances'].state == State.HEALTHY
    assert states['bar/USDRUBF'].state == State.UNKNOWN
    h1_export['finances']['observed_at'] = stamp(now-timedelta(seconds=301))
    h1_export['finances']['evidence']['observed_at'] = h1_export['finances']['observed_at']
    publish(h1_export)
    assert read(now).portfolio.equity is None
    assert read(now).status.state == State.HEALTHY


@pytest.mark.parametrize('mutation', ['partial','open_label','open_candle','bad_ohlc','missing_n4','duplicate','wrong_instrument'])
def test_candle_integrity(h1_export, publish, now, mutation):
    bar = h1_export['bars'][0]
    if mutation == 'partial': bar['completed'] = False
    elif mutation == 'open_label': bar['time_label'] = 'OPEN'
    elif mutation == 'open_candle': bar['close_at'] = stamp(now+timedelta(hours=1))
    elif mutation == 'bad_ohlc': bar['ohlc']['high'] = 1
    elif mutation == 'missing_n4': h1_export['bars'].pop()
    elif mutation == 'duplicate': h1_export['bars'][1] = deepcopy(bar)
    else: bar['instrument'] = 'DEMO-M15-A'
    publish(h1_export)
    assert_unknown(read(now))


def test_gap_is_distinct_from_calendar_unknown(h1_export, publish, now):
    h1_export['bars'][0]['gaps'] = True
    publish(h1_export)
    assert read(now).instruments[0].state == State.DATA_GAP
    assert read(now).instruments[1].state == State.UNKNOWN


def test_only_published_signal_no_inference(h1_export, publish, now):
    h1_export['signals'].update(observed_at=stamp(now), complete=False, items=[dict(
        instrument='USDRUBF',bar_close_at='2026-10-15T18:00:00Z',emitted=True,
        direction='NO_SIGNAL',rejection_reason=None,risk_result='UNKNOWN')])
    publish(h1_export)
    result = read(now)
    assert len(result.signals) == 1 and result.signals[0].direction == 'NO_SIGNAL'
    assert 'Причина не опубликована' in result.signals[0].reason
    assert all(row.instrument == 'USDRUBF' for row in result.signals)
    h1_export['signals']['items'][0]['bar_close_at'] = '2026-10-15T17:00:00Z'
    publish(h1_export)
    assert_unknown(read(now))


@pytest.mark.parametrize('execution', list(ExecutionState))
def test_execution_levels_and_evidence(h1_export, publish, now, execution):
    reconciled(h1_export, stamp(now))
    row = order(stamp(now), execution)
    if execution == ExecutionState.FILL_CONFIRMED:
        row.update(filled_quantity=2, fill_price=101, evidence=evidence('FIXTURE_TRADE_HISTORY',stamp(now)))
    h1_export['orders'].update(observed_at=stamp(now),complete=True,items=[row])
    publish(h1_export)
    result = read(now)
    assert result.orders[0].state == execution
    assert (result.orders[0].fill_price is not None) == (execution == ExecutionState.FILL_CONFIRMED)
    if execution == ExecutionState.FILL_CONFIRMED:
        row['evidence'] = None
        publish(h1_export)
        assert read(now).orders[0].state == ExecutionState.UNRESOLVED
        assert read(now).orders[0].fill_price is None


def test_ack_cannot_smuggle_fill(h1_export, publish, now):
    row = order(stamp(now)); row['fill_price'] = 101
    h1_export['orders'].update(observed_at=stamp(now),complete=True,items=[row])
    publish(h1_export)
    assert_unknown(read(now))


def test_position_price_and_stop_need_separate_broker_evidence(h1_export, publish, now):
    reconciled(h1_export, stamp(now))
    h1_export['positions'].update(observed_at=stamp(now),complete=True,items=[dict(
        instrument='USDRUBF',side='LONG',quantity=2,entry_price=101,price_evidence=None)])
    row = dict(instrument='USDRUBF',side='LONG',quantity=2,expected_quantity=2,observed_quantity=2,
               broker_status='ACTIVE',checked_at=stamp(now),planned_price=99,evidence=None)
    h1_export['stops'].update(observed_at=stamp(now),complete=True,items=[row])
    publish(h1_export)
    result = read(now)
    assert result.positions[0].entry_price is None and result.positions[0].stop_price is None
    assert not result.h1_readonly.stops[0].protected
    assert result.h1_readonly.stops[0].broker_status == 'UNKNOWN'
    assert result.h1_readonly.stops[0].observed_quantity is None
    row['evidence'] = evidence('FIXTURE_BROKER_SLTP',stamp(now))
    publish(h1_export)
    assert read(now).h1_readonly.stops[0].protected
    for key, val in [('side','SHORT'),('quantity',1),('expected_quantity',1),('observed_quantity',1),('broker_status','INACTIVE')]:
        changed = deepcopy(h1_export)
        changed['stops']['items'][0][key] = val
        publish(changed)
        assert not read(now).h1_readonly.stops[0].protected


@pytest.mark.parametrize('defect', ['incomplete','missing_cashflows','no_evidence','wrong_evidence','fault','stale_reconciliation'])
def test_incomplete_financial_authority_suppresses_all_numbers(h1_export, publish, now, defect):
    financial(h1_export, stamp(now))
    if defect == 'incomplete': h1_export['finances']['complete'] = False
    elif defect == 'missing_cashflows': h1_export['finances']['withdrawals'] = None
    elif defect == 'no_evidence': h1_export['finances']['evidence'] = None
    elif defect == 'wrong_evidence': h1_export['finances']['evidence']['kind'] = 'FIXTURE_TRADE_HISTORY'
    elif defect == 'fault': h1_export['reconciliation']['status'] = 'FAULT'
    else: h1_export['reconciliation']['last_success_at'] = stamp(now-timedelta(seconds=91))
    publish(h1_export)
    result = read(now)
    assert result.portfolio.equity is None and result.portfolio.realized_pnl is None
    assert result.risk.used_pct is None and result.h1_readonly.deposits is None


def test_financial_values_not_recomputed_from_equity_or_orders(h1_export, publish, now):
    financial(h1_export, stamp(now))
    publish(h1_export)
    result = read(now)
    assert result.portfolio.equity == 100000
    assert result.portfolio.realized_pnl == 100
    assert result.portfolio.profit_factor is None and result.trades is None


def test_missing_rows_do_not_prove_flat(h1_export, publish, now):
    publish(h1_export)
    assert read(now).status.open_positions is None and read(now).positions is None
    reconciled(h1_export, stamp(now))
    h1_export['positions'].update(complete=True,observed_at=stamp(now))
    h1_export['orders'].update(complete=True,observed_at=stamp(now))
    publish(h1_export)
    assert read(now).positions == () and read(now).status.open_positions == 0
    assert read(now).h1_readonly.orders_complete


def test_reconciliation_fault_is_not_healthy(h1_export, publish, now):
    healthy(h1_export, stamp(now))
    h1_export['reconciliation']['status'] = 'FAULT'
    publish(h1_export)
    assert read(now).status.state == State.UNHEALTHY


@pytest.mark.parametrize('error', [RuntimeError, sqlite3.DatabaseError])
def test_safe_exception_boundary_no_leak_or_old_healthy(h1_export, publish, now, monkeypatch, caplog, error):
    healthy(h1_export, stamp(now)); publish(h1_export)
    assert read(now).status.state == State.HEALTHY
    secret = 'SECRET_TOKEN_RAW_ACCOUNT_PATH'
    def fail(*args): raise error(secret)
    monkeypatch.setattr(adapter,'read_snapshot',fail)
    result = read(now)
    assert_unknown(result)
    assert secret not in repr(result) + caplog.text
    m15 = SyntheticProvider().snapshot(RobotId.M15,'BASELINE',now)
    assert m15.status.state == State.NOT_DEPLOYED and m15.portfolio.equity is None


@pytest.mark.parametrize('signal', [KeyboardInterrupt, SystemExit])
def test_process_signals_propagate(monkeypatch, now, signal):
    def fail(*args): raise signal()
    monkeypatch.setattr(adapter,'read_snapshot',fail)
    with pytest.raises(signal): read(now)


def test_no_model_promotion_to_verified_live(h1_export, publish, now):
    publish(h1_export)
    p = read(now).status.provenance
    with pytest.raises(ValueError, match='CC03'): replace(p,source_kind=SourceKind.VERIFIED_LIVE_READONLY,synthetic=False)


@pytest.mark.parametrize('ahead', [0.001,1])
def test_even_small_future_time_rejected(ahead,h1_export,publish,now):
    h1_export['generated_at']=stamp(now+timedelta(seconds=ahead))
    publish(h1_export)
    assert_unknown(read(now))


def test_unavailable_source_masks_numbers_even_with_complete_groups(h1_export,publish,now):
    financial(h1_export,stamp(now))
    h1_export['runtime']['source_status']='UNAVAILABLE'
    publish(h1_export)
    result=read(now)
    assert result.status.state==State.UNKNOWN
    assert result.portfolio.equity is None and result.positions is None
    assert not result.candles and not result.orders and not result.signals


def test_reconciliation_fault_cannot_confirm_empty_order_list(h1_export,publish,now):
    healthy(h1_export,stamp(now))
    h1_export['reconciliation']['status']='FAULT'
    h1_export['orders'].update(observed_at=stamp(now),complete=True)
    publish(h1_export)
    assert not read(now).h1_readonly.orders_complete


def test_stale_ohlc_still_requires_valid_structure(h1_export,publish,now):
    h1_export['bars'][0]['ohlc']['high']=1
    publish(h1_export)
    assert_unknown(read(now+timedelta(days=1)))


def test_exact_maximum_file_size_allowed(h1_export,publish,now):
    path=publish(h1_export)
    data=path.read_bytes()
    path.write_bytes(data+b' '*(MAX_BYTES-len(data)))
    assert read(now).status.state==State.HALTED
