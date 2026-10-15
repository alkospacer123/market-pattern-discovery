from pathlib import Path
from datetime import timedelta
import sqlite3
import pytest
from streamlit.testing.v1 import AppTest
from cc.ui import PAGES, CONTROLS, CONTROL_EXPLANATION
from cc.models import RobotId
from cc.providers.synthetic import SyntheticProvider

APP=Path(__file__).resolve().parents[1]/'app.py'


@pytest.fixture
def app():
    return AppTest.from_file(str(APP),default_timeout=15).run()


def text(app):
    return '\n'.join(str(element.value) for kind in ('markdown','caption','info','warning','success') for element in getattr(app,kind))


def test_app_loads_two_independent_robots(app):
    assert not app.exception
    content=text(app)
    for required in ('SYNTHETIC / DEMO','T3/H1/TRAIL1','T3/M15/SESSION','HALTED','NOT_DEPLOYED','DEMO-H1','DEMO-M15'):
        assert required in content
    assert [m.value for m in app.metric]==['0','0','UNKNOWN','UNKNOWN']


@pytest.mark.parametrize('page',PAGES)
def test_navigation(page,app):
    app.radio[0].set_value(page).run()
    assert not app.exception
    assert 'SYNTHETIC' in text(app)
    if page in ('Монитор H1','Монитор M15','Графики и сигналы'):
        assert len(app.get('plotly_chart'))==1
        assert len(app.dataframe)>=1


def test_m15_finances_unknown_after_switch(app):
    app.radio[0].set_value('Сделки и статистика').run()
    assert app.metric[0].value=='101 700.00 ₽'
    app.selectbox(key='trades-robot').select('M15').run()
    assert all(m.value=='UNKNOWN' for m in app.metric)
    assert 'NO_RUNTIME_AUTHORITY' in text(app)
    assert 'NOT_DEPLOYED' in text(app)
    assert len(app.dataframe)==0


@pytest.mark.parametrize('scenario',('STALE','UNKNOWN','UNAVAILABLE','MALFORMED','API_ERROR','DATA_GAP','UNRESOLVED','HEALTHY'))
def test_failure_scenarios_do_not_affect_m15(app,scenario):
    app.selectbox(key='scenario-H1').select(scenario).run()
    assert not app.exception
    assert 'NOT_DEPLOYED' in text(app)
    expected='UNKNOWN' if scenario in ('UNKNOWN','UNAVAILABLE','MALFORMED') else scenario
    assert any(f'· {expected} ·' in e.value for kind in ('info','warning','success') for e in getattr(app,kind))


def test_controls_disabled_and_no_handlers(app):
    app.radio[0].set_value('Управление').run()
    assert len(app.button)==10
    assert all(button.disabled for button in app.button)
    assert [b.label for b in app.button]==list(CONTROLS)*2
    assert CONTROL_EXPLANATION in text(app)


def test_chart_instrument_and_period_selection(app):
    app.radio[0].set_value('Монитор H1').run()
    app.selectbox(key='symbol-H1').select('CNYRUBF').run()
    app.selectbox(key='period-H1').select(24).run()
    assert not app.exception
    assert set(app.dataframe[0].value['Инструмент'])=={'CNYRUBF'}


def test_event_filters(app):
    app.radio[0].set_value('Журнал событий').run()
    app.multiselect[0].set_value(['M15']).run()
    frame=app.dataframe[0].value
    assert set(frame['Робот'])=={'M15'}
    assert set(frame['Счёт DEMO'])=={'DEMO-M15'}
    app.multiselect[1].set_value(['ERROR']).run()
    assert len(app.dataframe[0].value)==1
    app.text_input[0].set_value('no-such-event').run()
    assert app.dataframe[0].value.empty
    app.text_input[0].set_value('').run()
    app.date_input[0].set_value(app.date_input[1].value+timedelta(days=1)).run()
    assert any('Начальная дата' in row.value for row in app.warning)


@pytest.mark.parametrize('failed_robot', list(RobotId))
@pytest.mark.parametrize('error_type,message', [
    (RuntimeError, 'SECRET_TRADING_TOKEN_123'),
    (sqlite3.DatabaseError, 'SENSITIVE_ACCOUNT_DATA'),
])
def test_provider_failure_renders_only_safe_unknown(app, monkeypatch, failed_robot, error_type, message):
    app.selectbox(key='scenario-H1').select('HEALTHY').run()
    assert any('T3/H1/TRAIL1 · HEALTHY ·' in row.value for row in app.success)
    original = SyntheticProvider.snapshot

    def failing_snapshot(self, robot_id, scenario, now):
        if robot_id == failed_robot:
            raise error_type(message)
        return original(self, robot_id, scenario, now)

    monkeypatch.setattr(SyntheticProvider, 'snapshot', failing_snapshot)
    app.run()
    assert not app.exception
    strategy = 'T3/H1/TRAIL1' if failed_robot == RobotId.H1 else 'T3/M15/SESSION'
    assert any(f'{strategy} · UNKNOWN ·' in row.value for row in app.warning)
    if failed_robot == RobotId.H1:
        assert not app.success  # previous HEALTHY is not retained
        assert any('T3/M15/SESSION · NOT_DEPLOYED ·' in row.value for row in app.info)
    else:
        assert any('T3/H1/TRAIL1 · HEALTHY ·' in row.value for row in app.success)
    assert message not in text(app)
    app.radio[0].set_value('Журнал событий').run()
    assert not app.exception
    frame = app.dataframe[0].value
    failed_events = frame[frame['Робот'] == failed_robot.value]
    assert list(failed_events['Событие DEMO']) == ['SYNTHETIC: SNAPSHOT_INVALID_OR_UNAVAILABLE']
    assert message not in frame.to_string() and message not in text(app)
