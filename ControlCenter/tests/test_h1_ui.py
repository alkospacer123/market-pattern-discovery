"""H1 local report integration and separately tested one-click concurrency."""
from datetime import datetime, timezone
from pathlib import Path
import pytest
from streamlit.testing.v1 import AppTest
from cc.ui import PAGES

APP = Path(__file__).parents[1] / "app.py"


def text(app):
    return "\n".join(str(e.value) for kind in ("caption", "markdown", "info", "warning", "success")
                     for e in getattr(app, kind))


def test_h1_ui_has_no_unsupported_monitor_tabs():
    app = AppTest.from_file(str(APP), default_timeout=15).run()
    assert not app.exception
    assert PAGES == ("Главная", "Журнал", "Управление")
    assert len(app.radio) == 1
    assert len(app.button) == 1
    assert "UNKNOWN" in text(app)
    app.radio[0].set_value("Управление").run()
    assert "Управление ещё не подключено" in text(app)


def test_h1_navigation_has_zero_extra_manual_requests(monkeypatch):
    from cc.providers.h1_windows_os import manual_os_refresh
    calls = []
    import cc.providers.h1_windows_os as osmodule
    def watched(*args, **kwargs):
        calls.append(True)
        return manual_os_refresh(*args, **kwargs)
    monkeypatch.setattr(osmodule, "manual_os_refresh", watched)
    app = AppTest.from_file(str(APP), default_timeout=15).run()
    app.radio[0].set_value("Журнал").run()
    app.radio[0].set_value("Управление").run()
    app.radio[0].set_value("Главная").run()
    assert not calls


def test_manual_refresh_refuses_concurrent_clicks_without_retry(monkeypatch):
    from datetime import datetime, timezone
    from threading import Event, Thread
    from cc.models import State
    from cc.providers.h1_export import H1ExportProvider, manual_export_refresh, unchecked_export_snapshot
    started, release = Event(), Event()
    calls, results = [], []
    now = datetime(2026, 10, 18, tzinfo=timezone.utc)

    def stalled_provider(self, robot_id, scenario, observed):
        calls.append((robot_id, scenario))
        started.set()
        assert release.wait(10), 'test worker release timed out'
        return unchecked_export_snapshot(observed)

    monkeypatch.setattr(H1ExportProvider, 'snapshot', stalled_provider)
    worker = Thread(target=lambda: results.append(manual_export_refresh(now)), daemon=True)
    worker.start()
    try:
        assert started.wait(5)
        blocked, accepted = manual_export_refresh(now)
        assert not accepted
        assert blocked.status.state == State.UNKNOWN
        assert blocked.status.heartbeat_at is None
        assert len(calls) == 1
    finally:
        release.set()
        worker.join(10)
    assert not worker.is_alive() and len(results) == 1
    assert results[0][1] is True
    assert manual_export_refresh(now)[1] is True
    assert len(calls) == 2


def test_manual_refresh_exception_is_unknown_and_gate_is_released(monkeypatch):
    from datetime import datetime, timezone
    from cc.models import State
    from cc.providers.h1_export import H1ExportProvider, manual_export_refresh
    now = datetime(2026, 10, 18, tzinfo=timezone.utc)

    def denied(self, robot_id, scenario, observed):
        raise PermissionError('SENSITIVE_SOURCE_PATH_CANNOT_BE_SHOWN')
    monkeypatch.setattr(H1ExportProvider, 'snapshot', denied)
    for _ in range(2):
        result, accepted = manual_export_refresh(now)
        assert not accepted and result.status.state == State.UNKNOWN
        assert 'SENSITIVE_SOURCE_PATH' not in repr(result)


def test_export_is_not_read_without_manual_click_and_navigation_does_not_reread(monkeypatch):
    from cc.providers.h1_export import H1ExportProvider
    calls = []
    def count_reads(self, robot_id, scenario, now):
        calls.append((robot_id, scenario))
        from cc.providers.h1_export import unchecked_export_snapshot
        return unchecked_export_snapshot(now)
    monkeypatch.setattr(H1ExportProvider, "snapshot", count_reads)
    app = AppTest.from_file(str(APP), default_timeout=15).run()
    app.selectbox(key="h1-source").select("READONLY_EXPORT").run()
    assert not app.exception and not calls
    app.radio[0].set_value("Журнал").run()
    app.radio[0].set_value("Управление").run()
    assert not calls
    app.button(key="cc03-manual-refresh").click().run()
    assert len(calls) == 1
    app.radio[0].set_value("Главная").run()
    app.radio[0].set_value("Журнал").run()
    assert len(calls) == 1
    app.button(key="cc03-manual-refresh").click().run()
    assert len(calls) == 2
    app.selectbox(key="h1-source").select("SYNTHETIC / DEMO").run()
    app.selectbox(key="h1-source").select("READONLY_EXPORT").run()
    assert len(calls) == 2
