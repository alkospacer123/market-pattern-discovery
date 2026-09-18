from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

from TradingSystemLab.multitimeframe.phase73 import hash_tree
from TradingSystemLab.timeframe_diagnostics.m5_full import run


def _inputs(root: Path) -> tuple[Path, Path]:
    validation, optimization = root / "validation", root / "optimization"
    rows = [
        {"trade_id": "a", "instrument": "USDRUBF", "direction": "LONG",
         "entry_time": "2023-01-02T09:00:00+03:00", "exit_time": "2023-01-02T09:10:00+03:00",
         "net_R": -1.0, "MAE_R": 1.0, "MFE_R": .2},
        {"trade_id": "b", "instrument": "CNYRUBF", "direction": "SHORT",
         "entry_time": "2024-07-01T10:00:00+03:00", "exit_time": "2024-07-01T10:30:00+03:00",
         "net_R": 2.0, "MAE_R": .1, "MFE_R": 2.5},
        {"trade_id": "c", "instrument": "CNYRUBF", "direction": "LONG",
         "entry_time": "2024-07-01T17:00:00+03:00", "exit_time": "2024-07-01T18:01:00+03:00",
         "net_R": .5, "MAE_R": .3, "MFE_R": .8},
    ]
    for strategy, identity in (("T2", "T2_M5_candidate_v1"), ("T3", "T3_M5_candidate_v1")):
        (validation / strategy).mkdir(parents=True)
        (optimization / strategy).mkdir(parents=True)
        data = pd.DataFrame(rows)
        if strategy == "T2":
            data["setup_age_bars"] = 1
        data.to_csv(validation / strategy / "trades.csv", index=False)
        (optimization / strategy / "candidate_registry.json").write_text(
            json.dumps({"candidate_id": identity}) + "\n", encoding="utf-8")
    return validation, optimization


def test_full_reports_are_read_only_complete_and_deterministic(tmp_path: Path) -> None:
    validation, optimization = _inputs(tmp_path)
    source_before = (hash_tree(validation), hash_tree(optimization))
    output = tmp_path / "output"
    manifest = run(validation, optimization, output)
    first = hash_tree(output)
    run(validation, optimization, output)
    assert first == hash_tree(output)
    assert source_before == (hash_tree(validation), hash_tree(optimization))
    assert manifest["status"] == "PHASE_M5_FULL_DIAGNOSTIC_COMPLETE"
    assert all(manifest[key] is False for key in
               ("optimization_performed", "parameter_changes", "strategy_changes", "ranking",
                "candidate_selection", "true_oos_access"))
    required = {"time_report.csv", "session_report.csv", "weekday_report.csv", "month_report.csv",
                "quarter_report.csv", "instrument_report.csv", "direction_report.csv",
                "instrument_session_report.csv", "trade_distribution_report.csv", "mae_mfe_report.csv",
                "holding_time_report.csv", "drawdown_report.csv", "regime_report.csv", "diagnostic_report.md"}
    assert {p.name for p in (output / "T2").iterdir()} == required
    sessions = pd.read_csv(output / "T2" / "session_report.csv")
    assert list(sessions.trades) == [1, 1, 1]  # exact half-open boundaries
    assert set(pd.read_csv(output / "T2" / "time_report.csv").time_dimension) == {"hour", "year"}
    regime = pd.read_csv(output / "T3" / "regime_report.csv")
    assert "DATA_UNAVAILABLE" in set(regime.status)


def test_true_oos_is_rejected_before_output(tmp_path: Path) -> None:
    validation, optimization = _inputs(tmp_path)
    path = validation / "T2" / "trades.csv"
    frame = pd.read_csv(path)
    frame.loc[0, "entry_time"] = "2025-01-01T00:00:00+03:00"
    frame.to_csv(path, index=False)
    with pytest.raises(ValueError, match="TRUE_OOS_TRADE_REJECTED"):
        run(validation, optimization, tmp_path / "output")
    assert not (tmp_path / "output").exists()
