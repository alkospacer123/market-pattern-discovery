import hashlib
from pathlib import Path

import pandas as pd
import pytest

from TradingSystemLab.results.post_v3_analysis.stage5_structural_validation import (
    stage5_be1_c1_correction as correction,
)


def test_single_c1_synthetic_loss_is_not_double_charged():
    result = correction.corrected_net_r("LONG", 100.0, 98.0, 2.0)
    assert result == pytest.approx(-1.001)
    assert result != pytest.approx(-1.002)


def test_single_c1_synthetic_profit():
    assert correction.corrected_net_r("LONG", 100.0, 104.0, 2.0) == pytest.approx(1.999)
    assert correction.corrected_net_r("SHORT", 100.0, 96.0, 2.0) == pytest.approx(1.999)


def test_real_canonical_t3_trade_price_regression():
    path = correction.ANATOMY / "normalized_trades_v2_baseline.csv"
    row = pd.read_csv(path).query("strategy == 'T3'").iloc[0]
    risk = 0.002 / float(row.cost_R)
    expected = ((float(row.entry_price) - float(row.exit_price)) / risk - 0.002 / risk)
    actual = correction.corrected_net_r(
        row.direction, float(row.entry_price), float(row.exit_price), risk)
    assert actual == pytest.approx(expected, abs=1e-9)
    assert float(row.canonical_C1_R) == pytest.approx(actual - float(row.cost_R), abs=1e-9)


def test_be1_certified_path_projection_is_immutable():
    path = correction.OUTPUT / "be1_trade_events.csv"
    frame = pd.read_csv(path, dtype=str, keep_default_na=False)
    columns = ["entry_time", "entry_price", "exit_time", "exit_price", "be_triggered",
               "be_activation_time", "exit_reason"]
    digest = hashlib.sha256(frame[columns].to_csv(index=False, lineterminator="\n").encode()).hexdigest()
    assert digest == "9002ab9d757c16ad8a2010278dde5f1a1967a4b7855ca4c4db6424a308b0e1f0"


def test_compact_overlay_is_deterministic_and_has_required_cardinality(tmp_path: Path):
    first = correction.build(tmp_path)
    second = correction.build(tmp_path)
    assert first == second
    assert len(pd.read_csv(tmp_path / "be1_c1_corrected_study_summary.csv")) == 24
    assert len(pd.read_csv(tmp_path / "be1_c1_corrected_lifecycle_report.csv")) == 6
    assert len(pd.read_csv(tmp_path / "t3_c1_pre_post_comparison.csv")) == 12
