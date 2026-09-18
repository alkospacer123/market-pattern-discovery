from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from TradingSystemLab.multitimeframe.phase73 import hash_tree
from TradingSystemLab.timeframe_diagnostics.m5 import run


def _inputs(root: Path) -> tuple[Path, Path]:
    validation, optimization = root / "validation", root / "optimization"
    rows = [
        {"trade_id": "a", "instrument": "USDRUBF", "direction": "LONG",
         "entry_time": "2024-01-01T09:00:00+03:00", "exit_time": "2024-01-01T09:10:00+03:00", "net_R": -1},
        {"trade_id": "b", "instrument": "CNYRUBF", "direction": "SHORT",
         "entry_time": "2024-01-01T17:00:00+03:00", "exit_time": "2024-01-01T17:20:00+03:00", "net_R": 2},
    ]
    for strategy in ("T2", "T3"):
        (validation / strategy).mkdir(parents=True)
        (optimization / strategy).mkdir(parents=True)
        pd.DataFrame(rows).to_csv(validation / strategy / "trades.csv", index=False)
        (optimization / strategy / "candidate_registry.json").write_text("{}\n")
    return validation, optimization


def test_reports_are_complete_causal_and_deterministic(tmp_path: Path) -> None:
    validation, optimization = _inputs(tmp_path)
    output = tmp_path / "output"
    assert run(validation, optimization, output)["status"] == "PHASE_M5_DIAGNOSTIC_COMPLETE"
    first = hash_tree(output)
    run(validation, optimization, output)
    assert first == hash_tree(output)
    required = {"hour_report.csv", "session_report.csv", "weekday_report.csv",
                "direction_report.csv", "instrument_session_report.csv",
                "drawdown_period_report.csv", "trade_distribution_report.csv", "diagnostic_report.md"}
    assert {p.name for p in (output / "T2").iterdir()} == required
    sessions = pd.read_csv(output / "T2" / "session_report.csv")
    assert sessions.query("scope == 'COMBINED' and session == 'Session_B'").trades.iloc[0] == 1
    manifest = json.loads((output / "manifest.json").read_text())
    assert manifest["optimization_performed"] is False
    assert manifest["true_oos_accessed"] is False


def test_true_oos_trade_is_rejected(tmp_path: Path) -> None:
    validation, optimization = _inputs(tmp_path)
    path = validation / "T2" / "trades.csv"
    frame = pd.read_csv(path)
    frame.loc[0, "entry_time"] = "2025-01-01T00:00:00Z"
    frame.to_csv(path, index=False)
    try:
        run(validation, optimization, tmp_path / "output")
    except ValueError as error:
        assert str(error) == "TRUE_OOS_TRADE_REJECTED"
    else:
        raise AssertionError("TRUE OOS was not rejected")
