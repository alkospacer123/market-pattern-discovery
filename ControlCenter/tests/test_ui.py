"""Minimal operator UI: exactly three screens, no demo trading data in runtime."""
from datetime import datetime, timedelta, timezone
from pathlib import Path
import pytest
from streamlit.testing.v1 import AppTest
from cc.ui import PAGES, CONTROL_EXPLANATION

APP = Path(__file__).resolve().parents[1] / "app.py"


@pytest.fixture
def app():
    return AppTest.from_file(str(APP), default_timeout=15).run()


def page_text(app):
    return "\n".join(str(e.value) for kind in ("markdown", "caption", "info", "warning", "success")
                     for e in getattr(app, kind))


def local(now, *, status="CURRENT"):
    return dict(status=status, received_at=now, observed_at=now, contact_at=now,
                health="HEALTHY", task="Running", reconciliation="PASS",
                positions=0, stops=0, unresolved=0, cycle_count=22877,
                kill_switch="ARMED", generation="62",
                cycles=[{"Попытка": n, "Результат": "PASS", "Цикл": str(22867+n),
                         "Причина": "NONE"} for n in range(1, 11)])


def test_only_three_requested_sections(app):
    assert not app.exception
    assert PAGES == ("Главная", "Журнал", "Управление")
    assert list(app.radio[0].options) == list(PAGES)
    assert app.selectbox(key="h1-source").value == "WINDOWS_OS_ONLY"
    assert app.button(key="cc03-manual-refresh").disabled is False
    assert len(app.button) == 1
    assert "H1" in page_text(app) and "M15" in page_text(app)
    assert "нет актуального H1 CHECK" in page_text(app)
    assert not app.get("plotly_chart")


@pytest.mark.parametrize("section", PAGES)
def test_sections_load_without_background_poll_or_demo(section, app):
    app.radio[0].set_value(section).run()
    assert not app.exception
    assert not app.get("plotly_chart")
    assert len(app.button) == 1
    assert "DEMO-H1" not in page_text(app)
    assert "DEMO-M15" not in page_text(app)


def test_full_operator_report_shown_once_on_main(app):
    now = datetime.now(timezone.utc)
    app.session_state["cc03-local-check"] = local(now)
    app.run()
    assert not app.exception
    content = page_text(app)
    assert "HEALTHY · ARMED" in content
    assert "10/10 PASS" in content
    assert any(m.value == "22877" for m in app.metric)
    assert any(m.label == "Позиции H1" and m.value == "0" for m in app.metric)
    assert "Источник M15 не подключён" in content
    assert len(app.dataframe) == 0
    app.radio[0].set_value("Журнал").run()
    assert len(app.dataframe) == 1
    assert len(app.dataframe[0].value) == 10
    assert set(app.dataframe[0].value["Результат"]) == {"PASS"}
    app.radio[0].set_value("Главная").run()
    assert len(app.dataframe) == 0


def test_stale_report_is_not_green(app):
    now = datetime.now(timezone.utc) - timedelta(hours=2)
    app.session_state["cc03-local-check"] = local(now, status="CURRENT")
    app.run()
    content = page_text(app)
    assert "STALE · H1 CHECK" in content
    assert "HEALTHY · ARMED" not in content
    assert all(m.value != "22877" for m in app.metric)


def test_controls_not_fake_clickable(app):
    app.radio[0].set_value("Управление").run()
    assert not app.exception
    assert CONTROL_EXPLANATION in page_text(app)
    assert len(app.button) == 1
    assert not app.get("plotly_chart")


def test_untrusted_query_cannot_choose_runtime_source(app):
    app.query_params["source"] = "VERIFIED_LIVE"
    app.query_params["path"] = "C:/TradingSystemLab/private.sqlite"
    app.run()
    assert not app.exception
    assert app.selectbox(key="h1-source").value == "WINDOWS_OS_ONLY"
    assert "private.sqlite" not in page_text(app)
