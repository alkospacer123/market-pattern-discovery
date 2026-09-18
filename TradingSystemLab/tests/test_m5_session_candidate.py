from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

from TradingSystemLab.multitimeframe.phase73 import hash_tree
from TradingSystemLab.timeframe_analysis.m5_session_candidate import run


def _inputs(root: Path) -> tuple[Path, Path]:
    validation, optimization = root / "validation", root / "optimization"
    rows = [
        {"trade_id": "a", "instrument": "USDRUBF", "direction": "LONG",
         "entry_time": "2023-01-02T09:55:00+03:00", "exit_time": "2023-01-02T10:05:00+03:00", "net_R": -1.0},
        {"trade_id": "b", "instrument": "CNYRUBF", "direction": "SHORT",
         "entry_time": "2024-07-01T10:00:00+03:00", "exit_time": "2024-07-01T10:30:00+03:00", "net_R": 2.0},
        {"trade_id": "c", "instrument": "CNYRUBF", "direction": "LONG",
         "entry_time": "2024-07-01T16:59:00+03:00", "exit_time": "2024-07-01T18:00:00+03:00", "net_R": 0.5},
        {"trade_id": "d", "instrument": "USDRUBF", "direction": "SHORT",
         "entry_time": "2024-07-01T17:00:00+03:00", "exit_time": "2024-07-01T17:20:00+03:00", "net_R": -0.5},
        {"trade_id": "e", "instrument": "USDRUBF", "direction": "LONG",
         "entry_time": "2024-06-29T12:00:00+03:00", "exit_time": "2024-06-29T12:05:00+03:00", "net_R": 5.0},
    ]
    for key in ("T2", "T3"):
        (validation / key).mkdir(parents=True)
        (optimization / key).mkdir(parents=True)
        pd.DataFrame(rows).to_csv(validation / key / "trades.csv", index=False)
        (optimization / key / "candidate_registry.json").write_text(
            json.dumps({"candidate_id": f"{key}_M5_candidate_v1", "parameters": {"frozen": True}}) + "\n")
    return validation, optimization


def test_session_candidate_is_exact_read_only_and_deterministic(tmp_path: Path) -> None:
    validation, optimization = _inputs(tmp_path)
    source_before = (hash_tree(validation), hash_tree(optimization))
    output = tmp_path / "output"
    manifest = run(validation, optimization, output)
    first = hash_tree(output)
    run(validation, optimization, output)
    assert first == hash_tree(output)
    assert source_before == (hash_tree(validation), hash_tree(optimization))
    assert manifest["status"] == "PHASE_M5_SESSION_CANDIDATE_COMPLETE"
    assert manifest["candidate_research"] is True
    assert all(manifest[key] is False for key in
               ("diagnostic_only", "optimization", "parameter_changes", "strategy_changes",
                "winner_selection", "true_oos_access"))
    metrics = json.loads((output / "T2" / "metrics.json").read_text())
    assert metrics["baseline"]["trades"] == 5
    assert metrics["session_filter_candidate"]["trades"] == 2
    sessions = pd.read_csv(output / "T2" / "session_report.csv")
    assert list(sessions.query("variant == 'BASELINE'").session) == ["Session_A", "Session_B", "Session_C"]
    assert sessions.query("variant == 'SESSION_FILTER'").trades.iloc[0] == 2
    comparison = pd.read_csv(output / "comparison.csv")
    assert {"T2", "T3", "COMBINED"} == set(comparison.scope)
    assert {"performance", "instrument", "direction", "weekday", "session", "holding_time"} == set(comparison.analysis)


def test_true_oos_rejected_before_output(tmp_path: Path) -> None:
    validation, optimization = _inputs(tmp_path)
    path = validation / "T3" / "trades.csv"
    frame = pd.read_csv(path)
    frame.loc[0, "entry_time"] = "2025-01-02T10:00:00+03:00"
    frame.to_csv(path, index=False)
    output = tmp_path / "output"
    with pytest.raises(ValueError, match="TRUE_OOS_TRADE_REJECTED"):
        run(validation, optimization, output)
    assert not output.exists()


def test_baseline_identity_is_frozen(tmp_path: Path) -> None:
    validation, optimization = _inputs(tmp_path)
    registry = optimization / "T2" / "candidate_registry.json"
    registry.write_text(json.dumps({"candidate_id": "changed"}))
    with pytest.raises(ValueError, match="CANDIDATE_IDENTITY_MISMATCH:T2"):
        run(validation, optimization, tmp_path / "output")
