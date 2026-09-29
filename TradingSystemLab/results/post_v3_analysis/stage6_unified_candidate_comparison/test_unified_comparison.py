import json
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent


def test_exact_frozen_universe_and_normalized_evidence():
    baskets = pd.read_csv(HERE / "basket_registry.csv")
    configs = pd.read_csv(HERE / "configuration_registry.csv")
    sources = pd.read_csv(HERE / "variant_source_registry.csv")
    assert baskets.basket_size.value_counts().to_dict() == {2: 6, 3: 4, 4: 1}
    assert len(configs) == 55 and configs.variant.nunique() == 5
    assert len(sources) == 5 and set(sources.source_status) == {"AUTHENTICATED"}
    assert not (HERE / "portfolio_scaled_trades.csv").exists()


def test_complete_outputs_and_audit_pass():
    expected = {"monthly_metrics.csv", "instrument_monthly_metrics.csv", "unified_leaders.csv",
                "legacy_A_F_unified_bridge.csv", "audit_manifest.json", "independent_audit_result.json"}
    assert expected <= {p.name for p in HERE.iterdir()}
    result = json.loads((HERE / "independent_audit_result.json").read_text())
    assert result["status"] == "PASS" and all(result["checks"].values())


def test_equal_sleeves_and_all_months():
    configs = pd.read_csv(HERE / "configuration_registry.csv")
    assert ((configs.sleeve_weight * configs.basket_size - 1).abs() < 1e-10).all()
    monthly = pd.read_csv(HERE / "monthly_metrics.csv")
    assert monthly.configuration_id.nunique() == 55
    assert monthly.groupby("configuration_id").size().min() >= 12
