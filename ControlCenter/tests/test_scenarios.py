from dataclasses import asdict, replace
from datetime import timedelta
import json
import sqlite3
import pytest
from cc.analytics import monthly
from cc.charts import candle_chart
from cc.freshness import display_state
from cc.models import ExecutionState, RobotId, State
from cc.providers.synthetic import SCENARIOS, SyntheticProvider, read_safely


@pytest.mark.parametrize('robot', list(RobotId))
@pytest.mark.parametrize('scenario', list(SCENARIOS))
def test_deterministic_safe_scenarios(robot, scenario, now):
    a=read_safely(SyntheticProvider(),robot,scenario,now)
    b=read_safely(SyntheticProvider(),robot,scenario,now)
    assert a == b
    assert json.dumps(asdict(a),default=str,sort_keys=True) == json.dumps(asdict(b),default=str,sort_keys=True)
    assert a.status.trading_allowed is False
    assert a.status.provenance.synthetic
    assert a.status.provenance.account_scope == f'DEMO-{robot}'
    if robot == RobotId.M15:
        assert a.status.state == State.NOT_DEPLOYED
        assert a.status.heartbeat_at is None and a.portfolio.equity is None
        assert a.positions is None and a.trades is None


@pytest.mark.parametrize('scenario,state', [('BASELINE',State.HALTED),('HEALTHY',State.HEALTHY),
    ('STALE',State.STALE),('DATA_GAP',State.DATA_GAP),('API_ERROR',State.API_ERROR),
    ('UNRESOLVED',State.UNRESOLVED),('UNAVAILABLE',State.UNKNOWN),('UNKNOWN',State.UNKNOWN),('MALFORMED',State.UNKNOWN)])
def test_h1_display_states(scenario,state,now):
    snapshot=read_safely(SyntheticProvider(),RobotId.H1,scenario,now)
    assert display_state(snapshot.status,now) == state


def test_refresh_advances_only_local_demo(h1,now):
    later = SyntheticProvider().snapshot(RobotId.H1,'BASELINE',now+timedelta(seconds=2))
    assert later.status.provenance.observed_at == now+timedelta(seconds=2)
    assert later.status.state == State.HALTED
    assert h1.status.provenance.observed_at == now


def test_gap_and_open_position(now):
    gap=SyntheticProvider().snapshot(RobotId.H1,'DATA_GAP',now)
    rows=[c for c in gap.candles if c.instrument=='USDRUBF']
    assert len(rows)==71
    assert max(b.close_at-a.close_at for a,b in zip(rows,rows[1:]))==timedelta(hours=2)
    opened=SyntheticProvider().snapshot(RobotId.H1,'OPEN_POSITION',now)
    assert opened.status.open_positions==1
    assert opened.positions[0].stop_evidence=='SYNTHETIC_STOP_PROOF'
    assert len(candle_chart(opened,'USDRUBF',72).layout.shapes)==1


def test_independent_error_recovery(h1,m15,now):
    class Broken:
        def snapshot(self,*args): raise OSError('sensitive payload must not escape')
    failed=read_safely(Broken(),RobotId.H1,'BASELINE',now)
    assert display_state(failed.status,now)==State.UNKNOWN
    assert failed.portfolio.equity is None and failed.positions is None
    assert 'sensitive' not in str(failed)
    assert m15==SyntheticProvider().snapshot(RobotId.M15,'BASELINE',now)
    class WrongAccount:
        def snapshot(self,*args):return m15
    assert display_state(read_safely(WrongAccount(),RobotId.H1,'BASELINE',now).status,now)==State.UNKNOWN


def test_statistics_reconcile_separately(h1,m15):
    assert sum(t.net_pnl for t in h1.trades)==h1.portfolio.realized_pnl==1700
    assert sum(t.commission for t in h1.trades)==h1.portfolio.commissions==50
    assert h1.portfolio.equity==101700
    assert h1.portfolio.profit_factor==pytest.approx(2300/600)
    assert h1.portfolio.maximum_drawdown_pct==pytest.approx(400/100800*100)
    assert sum(r['Net PnL DEMO, ₽'] for r in monthly(h1.trades))==1700
    assert all(r['Счёт DEMO']=='DEMO-H1' for r in monthly(h1.trades))
    assert monthly(m15.trades)==[]


def test_chart_period_and_no_fabricated_t3(h1):
    chart=candle_chart(h1,'USDRUBF',24)
    assert len(chart.data[0].x)==24
    assert len(chart.data[2].x)==0  # entry outside selected period
    assert chart.data[1].name=='DEMO-линия (не T3)'
    assert len(candle_chart(h1,'UNKNOWN',24).layout.annotations)==1


@pytest.mark.parametrize('failed_robot', list(RobotId))
@pytest.mark.parametrize('error_type,message', [
    (RuntimeError, 'SECRET_TRADING_TOKEN_123'),
    (sqlite3.DatabaseError, 'SENSITIVE_ACCOUNT_DATA'),
])
def test_provider_failure_is_sanitized_and_isolated(failed_robot, error_type, message, now, capsys, caplog):
    class IntermittentProvider:
        failed = False

        def snapshot(self, robot_id, scenario, observed_at):
            if self.failed and robot_id == failed_robot:
                raise error_type(message)
            return SyntheticProvider().snapshot(robot_id, scenario, observed_at)

    provider = IntermittentProvider()
    scenarios = {RobotId.H1: 'HEALTHY', RobotId.M15: 'BASELINE'}
    before = {robot: read_safely(provider, robot, scenarios[robot], now) for robot in RobotId}
    before_json = json.dumps(asdict(before[failed_robot]), default=str, sort_keys=True)
    assert display_state(before[RobotId.H1].status, now) == State.HEALTHY
    provider.failed = True
    after = {robot: read_safely(provider, robot, scenarios[robot], now) for robot in RobotId}
    failed = after[failed_robot]
    peer = RobotId.M15 if failed_robot == RobotId.H1 else RobotId.H1
    assert after[peer] == before[peer]
    assert json.dumps(asdict(before[failed_robot]), default=str, sort_keys=True) == before_json
    assert failed is not before[failed_robot]
    assert display_state(failed.status, now) == State.UNKNOWN
    assert failed.status.state == (State.HALTED if failed_robot == RobotId.H1 else State.NOT_DEPLOYED)
    assert failed.status.provenance.observed_at is None
    assert failed.status.heartbeat_at is None and failed.status.last_bar_at is None
    assert failed.status.open_positions is None and failed.status.trading_allowed is False
    assert not any((failed.instruments, failed.candles, failed.signals, failed.orders))
    assert failed.positions is None and failed.trades is None
    assert all(value is None for key, value in asdict(failed.portfolio).items() if key != 'provenance')
    assert all(getattr(failed.risk, field) is None for field in ('per_position_pct', 'maximum_total_pct', 'used_pct', 'contracts'))
    code = 'SYNTHETIC: SNAPSHOT_INVALID_OR_UNAVAILABLE'
    assert failed.risk.reason == code
    assert len(failed.events) == 1 and failed.events[0].message == code
    output = json.dumps(asdict(failed), default=str, sort_keys=True)
    captured = capsys.readouterr()
    for text in (output, captured.out, captured.err, caplog.text):
        assert message not in text
        assert error_type.__name__ not in text
    provider.failed = False
    assert read_safely(provider, failed_robot, scenarios[failed_robot], now) == before[failed_robot]


@pytest.mark.parametrize('robot', list(RobotId))
@pytest.mark.parametrize('error_type', [KeyboardInterrupt, SystemExit])
def test_process_control_exceptions_propagate(robot, error_type, now):
    interrupt = error_type('SYNTHETIC_PROCESS_CONTROL')

    class InterruptedProvider:
        def snapshot(self, *args):
            raise interrupt

    with pytest.raises(error_type) as caught:
        read_safely(InterruptedProvider(), robot, 'BASELINE', now)
    assert caught.value is interrupt
