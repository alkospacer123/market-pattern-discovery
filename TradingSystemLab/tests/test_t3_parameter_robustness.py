from dataclasses import asdict
from pathlib import Path

import pandas as pd
import pytest

from TradingSystemLab.core.data_loader import DataLoader
from TradingSystemLab.run_t3_parameter_robustness import (
    OAT, configuration_id, interaction_sets, oat_sets, research_plan,
)
from TradingSystemLab.run_robust import TICK_SIZE
from TradingSystemLab.strategies.trend.T3_MTF_Trend import T3Parameters


def test_frozen_parameters_and_single_parameter_overrides():
    base = asdict(T3Parameters())
    assert base == {"ema_period": 100, "slope_lookback": 5, "adx_period": 14,
                    "adx_threshold": 20.0, "atr_period": 14, "atr_average_period": 20,
                    "breakout_period": 20, "stop_atr": 2.0, "trail_atr": 3.0}
    for name, configs in oat_sets().items():
        changed = OAT[name][0]
        for config in configs:
            assert all(getattr(config, key) == value for key, value in base.items() if key != changed)


def test_declared_counts_order_ids_and_no_cartesian_search():
    oat = oat_sets(); interactions = interaction_sets(); plan = research_plan()
    assert sum(map(len, oat.values())) == 28
    assert len(interactions["entry_risk"]) == 27
    assert len(interactions["regime"]) == 9
    assert len(plan) == 47
    ids = [configuration_id(p) for p in plan]
    assert len(ids) == len(set(ids))
    assert plan == research_plan()
    # A full six-dimensional grid would contain thousands, not this declared local map.
    assert len(plan) < 100


def test_correct_tick_units():
    assert TICK_SIZE == {"Si": 0.001, "CNY": 0.001}


@pytest.mark.parametrize("year", [2025, 2026])
def test_loader_rejects_all_true_oos(year, tmp_path):
    path = tmp_path / "bars.csv"
    path.write_text(f"Date,Time,Open,High,Low,Close\n{year}0101,100000,1,2,0,1\n")
    with pytest.raises(ValueError, match="TRUE OOS"):
        DataLoader(timezone="UTC").load_csv(path)


def test_parameter_artifacts_are_text_only():
    root = Path(__file__).parents[1] / "results" / "T3_parameter_robustness"
    forbidden = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".pdf", ".zip", ".parquet"}
    assert not [p for p in root.rglob("*") if p.suffix.lower() in forbidden]
    for path in root.rglob("*"):
        if path.is_file(): path.read_text(encoding="utf-8")


def test_committed_parity_and_manifest_when_generated():
    root = Path(__file__).parents[1] / "results" / "T3_parameter_robustness"
    if not (root / "manifest.json").exists(): pytest.skip("runner artifacts not generated")
    import json
    manifest = json.loads((root / "manifest.json").read_text())
    assert manifest["parity"]["C0"] == manifest["parity"]["C1"] == "PASS"
    assert manifest["dataset_end"] == "2024-12-31"
    assert manifest["interaction_set_count"] == 36
