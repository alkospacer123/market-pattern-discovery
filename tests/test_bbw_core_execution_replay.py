from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from bbw_system.core_execution.replay import run_execution_replay
from bbw_system.core_execution_cli import main


CANDIDATE = {"range_min_bars": 3, "range_max_bars": 40, "atr_min": 1.0, "atr_max": 3.0,
             "retest_min_bars": 3, "retest_max_bars": 30, "penetration": 0.2}


def _inputs(root: Path) -> dict[str, Path]:
    feature, normalized = root / "features", root / "normalized"
    candidate, baseline = root / "candidate", root / "baseline"
    for directory in (feature, normalized, candidate, baseline):
        directory.mkdir(parents=True)
    times = pd.date_range("2024-01-02", periods=7, freq="h")
    pd.DataFrame({"timestamp": times, "open": [5] * 6 + [9], "high": [10] * 6 + [12],
                  "low": [0] * 6 + [9], "close": [5] * 6 + [11], "volume": 1,
                  "bbw_squeeze": [True] + [False] * 6, "trend_direction": ["LONG"] * 7,
                  "atr14": [5] * 7}).to_csv(feature / "BBW_FEATURES.csv", index=False)
    m15_times = pd.date_range("2024-01-02 07:00", periods=12, freq="15min")
    pd.DataFrame({"timestamp": m15_times, "open": [11, 11, 11, 12, 12, 24, 36, 48, 48, 48, 48, 48],
                  "high": [12, 12, 12, 13, 25, 37, 49, 49, 49, 49, 49, 49],
                  "low": [10, 10, 10, 11, 11, 23, 35, 47, 47, 47, 47, 47],
                  "close": [11, 11, 11, 12, 24, 36, 48, 48, 48, 48, 48, 48],
                  "volume": 1}).to_csv(normalized / "M15.csv", index=False)
    (candidate / "CANDIDATE_CONFIG.json").write_text(json.dumps(CANDIDATE), encoding="utf-8")
    (baseline / "BASELINE_CONFIG.json").write_text(json.dumps({"stop_offset": 4}), encoding="utf-8")
    old = pd.DataFrame({"entry_time": ["2024-01-02 07:45"], "exit_time": ["2024-01-02 08:45"],
                        "result_R": [1.0], "exit_reason": ["TP3"]})
    old.to_csv(candidate / "CANDIDATE_TRADES.csv", index=False)
    old.assign(result_R=-1.0, exit_reason="STOP").to_csv(baseline / "BASELINE_TRADES.csv", index=False)
    return {"feature_root": feature, "normalized_root": normalized, "candidate_root": candidate,
            "baseline_root": baseline}


def test_replay_writes_complete_artifact_set_and_preserves_inputs(tmp_path: Path) -> None:
    roots = _inputs(tmp_path)
    output = tmp_path / "results" / "core_execution" / "v1"
    result = run_execution_replay(symbol="CNYRUBF", output_root=output, **roots)
    expected = {"CORE_TRADES.csv", "CORE_EXECUTION_REPORT.md", "CORE_EXECUTION_SUMMARY.json",
                "CORE_EXECUTION_COMPARISON.csv", "R_DISTRIBUTION.csv", "manifest.json"}
    assert {path.name for path in output.iterdir()} == expected
    assert result["status"] == "CORE_EXECUTION_ANALYSIS_COMPLETE"
    trades = pd.read_csv(output / "CORE_TRADES.csv")
    assert list(trades.exit_reason) == ["TAKE_PROFIT"]
    assert bool(trades.loc[0, "breakeven_activated"])
    comparison = pd.read_csv(output / "CORE_EXECUTION_COMPARISON.csv")
    assert list(comparison.execution) == ["Baseline", "Candidate", "CORE v1"]
    assert "CORE_EXECUTION_ANALYSIS_COMPLETE" in (output / "CORE_EXECUTION_REPORT.md").read_text()


def test_cli_rejects_true_oos_without_creating_outputs(tmp_path: Path, capsys: object) -> None:
    roots = _inputs(tmp_path)
    feature_path = roots["feature_root"] / "BBW_FEATURES.csv"
    frame = pd.read_csv(feature_path)
    frame.loc[len(frame)] = frame.iloc[-1]
    frame.loc[len(frame) - 1, "timestamp"] = "2025-01-01"
    frame.to_csv(feature_path, index=False)
    output = tmp_path / "out"
    argv = ["--symbol", "CNYRUBF", "--output-root", str(output)]
    for name, path in roots.items():
        argv.extend((f"--{name.replace('_', '-')}", str(path)))
    assert main(argv) == 2
    assert not output.exists()
    assert "CORE_EXECUTION_FAILED" in capsys.readouterr().err  # type: ignore[attr-defined]
