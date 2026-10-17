"""Streamlit acceptance of the actual receiving adapter and independent M15."""
from datetime import datetime, timezone
from pathlib import Path
import sqlite3
import pytest
from streamlit.testing.v1 import AppTest
from cc.models import State
from cc.providers import h1_readonly as adapter
from cc.ui import PAGES

APP=Path(__file__).parents[1]/'app.py'


def content(app):
    return '\n'.join(str(e.value) for kind in ('caption','markdown','info','warning','success') for e in getattr(app,kind))


def shift(value, delta):
    if isinstance(value,dict):
        for key,child in value.items():
            if key.endswith('_at') and child is not None:
                value[key]=(datetime.fromisoformat(child.replace('Z','+00:00'))+delta).isoformat()
            else: shift(child,delta)
    elif isinstance(value,list):
        for child in value: shift(child,delta)


@pytest.fixture
def fixture_app(h1_export, publish, now):
    shift(h1_export,datetime.now(timezone.utc).replace(microsecond=0)-now)
    path=publish(h1_export)
    app=AppTest.from_file(str(APP),default_timeout=15).run()
    app.selectbox(key='h1-source').select('OFFLINE_FIXTURE').run()
    return app,path,h1_export


@pytest.mark.parametrize('page',PAGES)
def test_fixture_navigation_and_disabled_controls(page, fixture_app):
    app,path,value=fixture_app
    app.radio[0].set_value(page).run()
    assert not app.exception
    assert 'OFFLINE_FIXTURE' in content(app)
    if page=='Управление':
        controls=[b for b in app.button if b.key!='cc03-manual-refresh']
        assert len(controls)==10 and all(row.disabled for row in controls)
    if page=='Монитор H1':
        assert 'Причина не опубликована' in content(app)
        assert 'accepted code 3a18c8c' in content(app)
        assert len(app.get('plotly_chart'))==1
        assert 'OFFLINE_FIXTURE OHLC' in app.get('plotly_chart')[0].proto.spec
        frames=[frame.value for frame in app.dataframe]
        bars=next(f for f in frames if 'Закрытие H1 (CLOSE)' in f.columns)
        assert set(bars['Актуальность'])=={'UNKNOWN'}
    if page=='Монитор M15':
        assert 'NOT_DEPLOYED' in content(app) and 'DEMO-M15' in content(app)
    if page=='Сделки и статистика':
        assert all(metric.value=='UNKNOWN' for metric in app.metric)
        assert 'Equity не является чистой' in content(app)


def test_h1_source_loss_m15_survives(fixture_app):
    app,path,value=fixture_app
    assert 'T3/H1/TRAIL1 · HALTED · OFFLINE_FIXTURE' in content(app)
    path.unlink()
    app.run()
    assert not app.exception
    assert 'T3/H1/TRAIL1 · UNKNOWN · OFFLINE_FIXTURE' in content(app)
    assert 'T3/M15/SESSION · NOT_DEPLOYED · SYNTHETIC / DEMO' in content(app)
    app.radio[0].set_value('Монитор M15').run()
    assert not app.exception and len(app.get('plotly_chart'))==1


@pytest.mark.parametrize('error_type',[RuntimeError,sqlite3.DatabaseError])
def test_old_healthy_removed_no_secret_in_ui_or_journal(fixture_app, publish, monkeypatch, caplog, error_type):
    app,path,value=fixture_app
    at=value['observed_at']
    value['runtime'].update(state='HEALTHY',heartbeat_at=at,last_successful_cycle_at=at)
    value['reconciliation'].update(observed_at=at,last_success_at=at,status='PASS',unresolved_intents=0)
    publish(value); app.run()
    assert any('T3/H1/TRAIL1 · HEALTHY · OFFLINE_FIXTURE' in row.value for row in app.success)
    secret='SECRET_FINAM_TOKEN_RAW_ACCOUNT'
    def fail(*args): raise error_type(secret)
    monkeypatch.setattr(adapter,'read_snapshot',fail)
    app.run()
    assert not app.exception and not app.success
    assert 'T3/H1/TRAIL1 · UNKNOWN · OFFLINE_FIXTURE' in content(app)
    assert 'T3/M15/SESSION · NOT_DEPLOYED' in content(app)
    assert secret not in content(app)+caplog.text
    app.radio[0].set_value('Журнал событий').run()
    table=app.dataframe[0].value
    assert secret not in table.to_string()+content(app)
    assert adapter.SAFE_ERROR in table.to_string()


def test_no_query_parameter_or_user_path_can_enable_live(fixture_app, monkeypatch):
    app,path,value=fixture_app
    app.query_params['source']='VERIFIED_LIVE_READONLY'
    app.query_params['path']='C:/tradingsystemlab/production/state.sqlite3'
    monkeypatch.setenv('CONTROL_CENTER_H1_PATH','/etc/passwd')
    app.run()
    assert not app.exception
    assert list(app.selectbox(key='h1-source').options)==['SYNTHETIC / DEMO','OFFLINE_FIXTURE','READONLY_EXPORT']
    assert 'FIXTURE-H1' in content(app)
    assert 'accepted code' not in content(app)  # overview only
    app.radio[0].set_value('Монитор H1').run()
    assert 'accepted code' in content(app)
    assert 'C:/tradingsystemlab' not in content(app)
    assert not app.text_input


def test_switching_back_to_demo_preserves_scenarios(fixture_app):
    app,path,value=fixture_app
    app.selectbox(key='h1-source').select('SYNTHETIC / DEMO').run()
    app.selectbox(key='scenario-H1').select('HEALTHY').run()
    assert 'T3/H1/TRAIL1 · HEALTHY · SYNTHETIC / DEMO' in content(app)
    assert 'T3/M15/SESSION · NOT_DEPLOYED' in content(app)
    assert [metric.value for metric in app.metric]==['0','0','UNKNOWN','UNKNOWN']


def test_export_is_not_read_without_manual_click_and_navigation_does_not_reread(monkeypatch):
    from cc.providers.h1_export import H1ExportProvider
    calls=[]
    def count_reads(self, robot_id, scenario, now):
        calls.append((robot_id, scenario))
        from cc.providers.h1_export import unchecked_export_snapshot
        return unchecked_export_snapshot(now)
    monkeypatch.setattr(H1ExportProvider, 'snapshot', count_reads)
    app=AppTest.from_file(str(APP), default_timeout=15).run()
    app.selectbox(key='h1-source').select('READONLY_EXPORT').run()
    assert not app.exception and not calls
    assert 'MANUAL_REFRESH_REQUIRED' in content(app) or 'Проверка H1 не запускалась' in content(app)
    app.radio[0].set_value('Монитор H1').run()
    app.radio[0].set_value('Монитор M15').run()
    assert not calls
    app.button(key='cc03-manual-refresh').click().run()
    assert len(calls)==1
    app.radio[0].set_value('Главная панель').run()
    app.radio[0].set_value('Монитор H1').run()
    assert len(calls)==1
    app.button(key='cc03-manual-refresh').click().run()
    assert len(calls)==2
    app.selectbox(key='h1-source').select('SYNTHETIC / DEMO').run()
    app.selectbox(key='h1-source').select('READONLY_EXPORT').run()
    assert len(calls)==2 and 'Проверка H1 не запускалась' in content(app)
