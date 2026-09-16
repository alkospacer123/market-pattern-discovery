"""Safety and diagnostic contracts for BBW Compliance Audit v1."""
from __future__ import annotations

import hashlib
from pathlib import Path

import pandas as pd
import pytest

from bbw_system.bbw_compliance_cli import main
from bbw_system.compliance.bbw_strategy_audit import ComplianceAuditError, _read_candles, _replay_result


def test_cli_requires_every_input_root() -> None:
    with pytest.raises(SystemExit) as error:
        main([])
    assert error.value.code == 2


def test_true_oos_fails_closed_before_research(tmp_path: Path) -> None:
    path = tmp_path / "H1.csv"
    pd.DataFrame({"timestamp": ["2025-01-02"], "open": [1], "high": [1], "low": [1],
                  "close": [1], "volume": [1]}).to_csv(path, index=False)
    before = hashlib.sha256(path.read_bytes()).hexdigest()
    with pytest.raises(ComplianceAuditError, match="TRUE OOS"):
        _read_candles(path, "H1")
    assert hashlib.sha256(path.read_bytes()).hexdigest() == before


def test_independent_r_replay_matches_static_partial_exit_ledger() -> None:
    m15 = pd.DataFrame({
        "timestamp": pd.to_datetime(["2024-01-01 10:00", "2024-01-01 10:15"]),
        "open": [100, 100], "high": [111, 131], "low": [99, 109], "close": [110, 130], "volume": [1, 1],
    })
    trade = pd.Series({"entry_time": pd.Timestamp("2024-01-01 10:00"), "direction": "LONG",
                       "entry_price": 100, "stop_price": 90, "tp1": 110, "tp2": 120, "tp3": 130})
    assert _replay_result(trade, m15, (0.5, 0.3, 0.2)) == pytest.approx(1.7)
