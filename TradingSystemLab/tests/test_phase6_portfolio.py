from pathlib import Path
import hashlib
import json

import pandas as pd
import pytest

from TradingSystemLab.portfolio.portfolio import EXPECTED_IDS, load_inputs, run

SOURCE = Path("TradingSystemLab/results/true_oos_validation")


def digest_tree(root: Path) -> dict[str, str]:
    return {p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(root.rglob("*")) if p.is_file()}


def test_phase5_provenance_and_true_oos_barrier():
    frames, manifest = load_inputs(SOURCE)
    assert set(frames) == {"T2", "T3"}
    assert [frames[k].candidate_id.iloc[0] for k in ("T2", "T3")] == list(EXPECTED_IDS.values())
    assert manifest["true_oos_barrier"] == {"enabled": True, "start": "2025-01-01", "development_rows_read": 0}
    assert all((frame.entry_time >= pd.Timestamp("2025-01-01", tz="UTC")).all() for frame in frames.values())


def test_hard_fails_on_changed_trade_identity(tmp_path):
    copied = tmp_path / "phase5"
    import shutil
    shutil.copytree(SOURCE, copied)
    trades = copied / "T2/trades.csv"
    trades.write_text(trades.read_text().replace("CNY-000001", "changed", 1))
    with pytest.raises(RuntimeError, match="SOURCE_SHA256_MISMATCH"):
        load_inputs(copied)


def test_predefined_portfolios_are_deterministic_and_inputs_unchanged(tmp_path):
    before = digest_tree(SOURCE)
    first, second = tmp_path / "first", tmp_path / "second"
    one, two = run(SOURCE, first), run(SOURCE, second)
    assert digest_tree(first) == digest_tree(second)
    assert digest_tree(SOURCE) == before
    assert one["weights"] == two["weights"]
    assert one["weights"]["C"] == {"T2": .5, "T3": .5}
    assert set(one["weights"]) == {"A", "B", "C", "D"}
    assert abs(sum(one["weights"]["D"].values()) - 1) < 1e-12
    assert one["optimization"] is False and one["walk_forward"] is False and one["ranking"] is False
    expected = {"manifest.json", "portfolio_summary.md", "portfolio_metrics.csv", "equity_curve.csv",
                "monthly_report.csv", "quarterly_report.csv", "yearly_report.csv", "strategy_contribution.csv",
                "correlation_report.csv", "overlap_report.csv", "concentration_report.csv",
                "drawdown_report.csv", "bootstrap_report.csv"}
    assert {p.name for p in first.iterdir()} == expected
    metrics = pd.read_csv(first / "portfolio_metrics.csv")
    assert set(metrics.portfolio_id) == {"A", "B", "C", "D"}
    assert (metrics.expectancy > 0).all() and (metrics.net_R > 0).all()
    assert json.loads((first / "manifest.json").read_text())["artifact_sha256"]
