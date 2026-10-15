from dataclasses import FrozenInstanceError, replace
from datetime import datetime, timedelta
import pytest
from cc.models import (Candle, ExecutionState, OrderEvent, RobotSnapshot, State)
from cc.freshness import display_state, freshness, metric, stamp


def test_missing_is_not_zero(h1, now):
    status = replace(h1.status, open_positions=None, error_count=None, last_bar_at=None)
    assert status.open_positions is None
    assert stamp(status.last_bar_at) == "UNKNOWN"
    assert metric(None) == "UNKNOWN"
    assert metric(0) == "0.00"
    assert display_state(status, now) == State.HALTED


@pytest.mark.parametrize('field,value', [('observed_at',datetime(2026,1,1)), ('received_at',None),
                                         ('synthetic',False), ('schema_version',2), ('account_scope','DEMO-M15'),
                                         ('source','real'), ('observed_at','2026-10-15')])
def test_invalid_provenance_rejected(h1, field, value):
    with pytest.raises(ValueError):
        replace(h1.status.provenance, **{field:value})


@pytest.mark.parametrize('field,value', [('open_positions',-1), ('error_count',True), ('trading_allowed',True),
                                         ('state','HEALTHY'), ('heartbeat_at',datetime(2026,1,1))])
def test_invalid_robot_status_rejected(h1, field, value):
    with pytest.raises(ValueError):
        replace(h1.status, **{field:value})


@pytest.mark.parametrize('value', [float('nan'),float('inf'),-1.,None,'100'])
def test_invalid_candle(h1, value):
    with pytest.raises(ValueError):
        replace(h1.candles[0], close=value)


def test_no_future_naive_or_incoherent_candle(h1):
    with pytest.raises(ValueError):
        replace(h1.candles[0], high=h1.candles[0].low-1)
    with pytest.raises(ValueError):
        replace(h1.candles[0], close_at=None)
    with pytest.raises(FrozenInstanceError):
        h1.candles[0].close = 100


@pytest.mark.parametrize('state', list(ExecutionState))
def test_order_fact_levels(h1, now, state):
    kwargs = dict(filled_quantity=1, fill_price=100., fill_evidence="SYNTHETIC_PROOF") if state == ExecutionState.FILL_CONFIRMED else {}
    event = OrderEvent(h1.status.provenance, 'USDRUBF', now, 'DEMO-order', state, 2, **kwargs)
    assert (event.fill_price is not None) == (state == ExecutionState.FILL_CONFIRMED)


@pytest.mark.parametrize('state', [s for s in ExecutionState if s != ExecutionState.FILL_CONFIRMED])
def test_ack_and_position_are_not_fill(h1, state):
    with pytest.raises(ValueError, match='ACK_IS_NOT_FILL'):
        replace(h1.orders[0], state=state, fill_price=100.)


def test_fill_requires_all_evidence(h1):
    fill = next(o for o in h1.orders if o.state == ExecutionState.FILL_CONFIRMED)
    for field in ('fill_evidence','filled_quantity','fill_price'):
        with pytest.raises(ValueError):
            replace(fill, **{field:None})
    with pytest.raises(ValueError):
        replace(fill, filled_quantity=3)


def test_account_isolation(h1, m15):
    for field in ('instruments','candles','signals','events'):
        with pytest.raises(ValueError, match='CROSS_ACCOUNT'):
            replace(h1, **{field:getattr(m15,field)})
    with pytest.raises(ValueError, match='CROSS_ACCOUNT'):
        replace(m15, portfolio=h1.portfolio)
    with pytest.raises(ValueError):
        replace(h1, positions=[])


def test_m15_has_no_runtime_or_r15(m15):
    for field, value in [('state',State.HEALTHY),('heartbeat_at',m15.status.provenance.received_at),
                         ('production_identity','guessed'),('open_positions',0)]:
        with pytest.raises(ValueError, match='NO_RUNTIME'):
            replace(m15.status, **{field:value})
    with pytest.raises(ValueError, match='NO_M15_FINANCIAL_AUTHORITY'):
        replace(m15, portfolio=replace(m15.portfolio, equity=100.))
    with pytest.raises(ValueError, match='NO_M15_FINANCIAL_AUTHORITY'):
        replace(m15, risk=replace(m15.risk, per_position_pct=1.5))


def test_freshness_and_clock_skew(h1, now):
    p = h1.status.provenance
    assert freshness(p,now+timedelta(seconds=10)) == State.HEALTHY
    assert freshness(p,now+timedelta(seconds=11)) == State.STALE
    assert freshness(replace(p,observed_at=None),now) == State.UNKNOWN
    assert freshness(p,now-timedelta(seconds=3)) == State.UNKNOWN
    healthy = replace(h1.status, state=State.HEALTHY, heartbeat_at=now)
    assert display_state(healthy, now+timedelta(seconds=11)) == State.STALE
    assert display_state(replace(healthy,heartbeat_at=None),now) == State.UNKNOWN
    assert display_state(replace(healthy,heartbeat_at=now-timedelta(seconds=30)),now) == State.STALE


def test_timezone_utc_msk_date_rollover(h1):
    value = h1.status.provenance.received_at.replace(hour=23,minute=59)
    assert '23:59:00 UTC' in stamp(value)
    assert '02:59:00 MSK' in stamp(value)
    with pytest.raises(ValueError):
        stamp(value.replace(tzinfo=None))


def test_snapshot_cannot_refresh_old_child_provenance(h1, now):
    stale=replace(h1.risk,provenance=replace(h1.risk.provenance,observed_at=now-timedelta(minutes=5)))
    with pytest.raises(ValueError,match='NON_ATOMIC_PROVENANCE'):
        replace(h1,risk=stale)


def test_instrument_stop_requires_evidence(h1):
    with pytest.raises(ValueError,match='STOP_EVIDENCE_REQUIRED'):
        replace(h1.instruments[0],stop_price=100.)
