from __future__ import annotations

import ast
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

import pytest

from TradingSystemLab.stage8_robot.production_service import (
    MODE,
    STATE_DATABASE,
    ProductionService,
    Snapshot,
)


COMMIT = "a" * 40
ACCOUNT = "synthetic-production-account"


class ReadOnlyGetFakeAPI:
    def __init__(self):
        self.calls = []

    def create_session(self):
        self.calls.append("create_session")
        return {}

    def session_details(self):
        self.calls.append("session_details")
        return {"readonly": False, "account_ids": [ACCOUNT]}

    def account(self, account_id):
        self.calls.append(("account", account_id))
        return {"status": "ACCOUNT_ACTIVE"}


def service(tmp_path, api=None):
    return ProductionService(
        tmp_path,
        tmp_path / "stage5",
        api or ReadOnlyGetFakeAPI(),
        ACCOUNT,
        COMMIT,
    )


def test_package2_service_has_no_direct_finam_order_endpoint_calls():
    source = Path("TradingSystemLab/stage8_robot/production_service.py").read_text()
    tree = ast.parse(source)
    assert "place_order(" not in source
    assert "place_sltp_order(" not in source
    assert "write_authorization" not in source
    assert "write_kill_switch" not in source
    imports = [
        node.module or ""
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom)
    ]
    assert "TradingSystemLab.stage8_robot.strategy_core" not in imports


def test_package2_uses_exact_production_state_and_30_day_h1_authority():
    source = Path("TradingSystemLab/stage8_robot/production_service.py").read_text()
    assert STATE_DATABASE == "stage8-12-production.sqlite3"
    assert 'H1_LOOKBACK_DAYS = 30' in source
    assert "load_stage5_seed_open_h1" in source
    assert "splice_seed_and_finam_open_h1" in source
    assert "newest_expected_h1_close" in source
    assert "T3ContextBuilder" not in source  # ProductionRuntime owns the frozen builder.
    assert "self.runtime.context_builder.build" in source


def test_absent_authorization_never_constructs_order_transport(tmp_path, monkeypatch):
    import TradingSystemLab.stage8_robot.production_service as module

    class BombTransport:
        def __init__(self, **kwargs):
            raise AssertionError("order transport constructed while unauthorized")

    monkeypatch.setattr(module, "AuthorizedFinamProductionTransport", BombTransport)
    api = ReadOnlyGetFakeAPI()
    svc = service(tmp_path, api)
    try:
        svc.authenticate()
        assert svc.transport is None
        assert api.calls == [
            "create_session",
            "session_details",
            ("account", ACCOUNT),
        ]
    finally:
        svc.close()


def test_unauthorized_or_halted_path_cannot_consume_entry_signal(tmp_path, monkeypatch):
    svc = service(tmp_path)
    try:
        svc.transport = None
        monkeypatch.setattr(
            svc.runtime,
            "build_latest_signal",
            lambda *args, **kwargs: (_ for _ in ()).throw(
                AssertionError("signal consumed before authorization/ARM")
            ),
        )
        snap = Snapshot(
            account={},
            positions={},
            orders=[],
            realized_equity=Decimal("100000"),
            available_cash=Decimal("100000"),
            observed_at=datetime(2026, 10, 7, 12, tzinfo=timezone.utc),
        )
        svc._plan_entry({}, snap)
        assert svc.runtime.store.unresolved_intent_count() == 0
    finally:
        svc.close()


def test_realized_equity_authority_excludes_unrealized_and_explained_cash(tmp_path):
    svc = service(tmp_path)
    try:
        svc.runtime.store.put("explained_external_cash_flows", "1000")
        realized = svc._realized_basis({
            "equity": {"value": "11000"},
            "unrealized_profit": {"value": "500"},
        }, {}, [])
        assert realized == Decimal("9500")
        assert svc.runtime.current_realized_equity() == Decimal("9500")
    finally:
        svc.close()


def test_realized_equity_bootstrap_requires_clean_broker_account(tmp_path):
    svc = service(tmp_path)
    try:
        with pytest.raises(
            RuntimeError,
            match="STAGE8_12_4_REALIZED_EQUITY_BOOTSTRAP_REQUIRES_CLEAN_ACCOUNT",
        ):
            svc._realized_basis({
                "equity": {"value": "10000"},
                "unrealized_profit": {"value": "500"},
            }, {"USDRUBF@RTSX": 1}, [])
        assert svc.runtime.current_realized_equity() is None
        assert svc.runtime.store.get("starting_realized_equity") is None
    finally:
        svc.close()


def test_production_runtime_persists_entry_signal_watermark_contract():
    source = Path("TradingSystemLab/stage8_robot/production_runtime.py").read_text()
    assert '"signal_timestamp": signal.timestamp.isoformat()' in source
    assert 'watermark_key = f"last_managed_h1:{payload[\'instrument\']}"' in source
    assert "ENTRY_SIGNAL_WATERMARK_MISMATCH" in source


def test_windows_production_task_is_separate_and_installed_disabled():
    root = Path("TradingSystemLab/stage8_robot/deploy/windows")
    installer = (root / "install-production-task.ps1").read_text()
    launcher = (root / "run-production.ps1").read_text()
    assert 'TradingSystemLab-Stage8-Production' in installer
    assert 'TradingSystemLab-Stage8-Readonly' in installer
    assert "READONLY_TASK_MUST_REMAIN_DISABLED" in installer
    assert "Disable-ScheduledTask" in installer
    assert "Start-ScheduledTask" not in installer
    assert "Enable-ScheduledTask" not in installer
    assert "write_authorization" not in installer
    assert "write_kill_switch" not in installer
    assert "run-readonly.ps1" not in launcher
    assert "trading-credential-store.ps1" in launcher
    assert '$env:FINAM_MODE = "STAGE8_12_PRODUCTION"' in launcher
    assert "--accepted-commit" in launcher
    assert "--stage5-data-root" in launcher
    assert "ExpectedCommit" in launcher
    assert "STAGE8_12_4_PRODUCTION_COMMIT_MISMATCH" in launcher
    assert "-ExpectedCommit $commit" in installer
    assert "STAGE8_12_4_PRODUCTION_TASK_PRINCIPAL_MISMATCH" in installer
    assert "--once" in launcher
    assert "50f1fd2178c18b7ab3bd969be82ad01f47a34745" in launcher


def test_package2_mode_is_not_legacy_readonly():
    assert MODE == "STAGE8_12_PRODUCTION"
