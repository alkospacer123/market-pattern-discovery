from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

import pandas as pd
import pytest

from TradingSystemLab.stage8_robot.stage8_12_4_service_preflight import (
    ServicePreflightBlocked,
    _context_evidence,
    _external_report,
)
from TradingSystemLab.stage8_robot.stage8_12_intel_preflight import PreflightReadAPI


def _ready_history() -> pd.DataFrame:
    start = pd.Timestamp("2026-01-01T10:00:00", tz="Europe/Moscow")
    index = pd.date_range(start, periods=1200, freq="h")
    base = pd.Series(range(len(index)), index=index, dtype=float) / 100.0 + 100.0
    return pd.DataFrame(
        {
            "Open": base,
            "High": base + 1.0,
            "Low": base - 1.0,
            "Close": base + 0.25,
        },
        index=index,
    )


def test_service_preflight_facade_exposes_no_order_methods():
    class API:
        def create_session(self): ...
        def session_details(self): ...
        def account(self, account_id): ...
        def orders(self, account_id): ...
        def assets_all_active(self): ...
        def asset(self, symbol, account_id): ...
        def asset_params(self, symbol, account_id): ...
        def schedule(self, symbol): ...
        def bars(self, symbol, start, end): ...
        def place_order(self, *args): raise AssertionError
        def place_sltp_order(self, *args): raise AssertionError
        def cancel_order(self, *args): raise AssertionError

    facade = PreflightReadAPI(API())
    assert not hasattr(facade, "place_order")
    assert not hasattr(facade, "place_sltp_order")
    assert not hasattr(facade, "cancel_order")
    assert not hasattr(facade, "submit_order")


def test_context_evidence_proves_full_frozen_t3_indicator_readiness():
    history = _ready_history()
    now = history.index[-1].to_pydatetime()
    evidence = _context_evidence(history, now)
    assert evidence["closed_h1_rows"] == len(history)
    assert evidence["execution_indicators_ready"] is True
    assert evidence["context_indicators_ready"] is True
    assert evidence["latest_h1_close_moscow"] == history.index[-1].isoformat()
    assert evidence["latest_context_close_moscow"] <= history.index[-1].isoformat()


def test_context_evidence_fails_when_ema200_context_is_not_ready():
    history = _ready_history().iloc[:100]
    with pytest.raises(
        ServicePreflightBlocked, match="STAGE8_12_4_T3_CONTEXT_INDICATORS_NOT_READY"
    ):
        _context_evidence(history, history.index[-1].to_pydatetime())


def test_service_preflight_report_must_remain_outside_repository():
    with pytest.raises(
        ServicePreflightBlocked,
        match="STAGE8_12_4_SERVICE_REPORT_REPOSITORY_FORBIDDEN",
    ):
        _external_report(
            Path("TradingSystemLab/stage8_robot/service-preflight.json")
        )
