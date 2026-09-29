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

import subprocess
import numpy as np
import pytest

from .audit_unified_comparison import (
    ORDER, concentration, first_differentiating_criterion, max_dd,
    negative_streak, rank_candidates, recovery, rolling_windows, source_matches,
    validate_starting_sha,
)


def test_known_drawdown_and_recovery():
    assert max_dd([2.0, -1.0, -3.0, 1.0]) == -4.0
    assert recovery(8.0, -4.0) == 2.0


def test_complete_rolling_windows_and_lifecycle_boundary():
    baseline = pd.DataFrame({"year": [2023] * 6, "month": range(1, 7), "net_R": range(1, 7)})
    oos = pd.DataFrame({"year": [2025] * 12, "month": range(1, 13), "net_R": [1.0] * 12})
    assert rolling_windows(baseline, 6) == [21.0]
    assert rolling_windows(oos, 12) == [12.0]
    # A missing calendar month invalidates the apparent three-row window.
    assert rolling_windows(baseline.drop(index=2).reset_index(drop=True), 3) == [15.0]
    # Lifecycles are supplied separately, so no 2023 -> 2025 window can exist.
    assert rolling_windows(baseline, 12) == [] and rolling_windows(oos, 6)[-1] == 6.0


def test_concentration_and_negative_streak():
    best, top3, amount = concentration([4, 3, 2, 1, -10])
    assert best == pytest.approx(0.4)
    assert top3 == pytest.approx(0.9)
    assert amount == 9
    assert negative_streak([1, -1, -2, 0, -3, -4, -5, 1]) == 3


def test_lexicographic_hierarchy_and_first_difference():
    base = {field: 1.0 for field in ORDER}
    base.update({"configuration_id": "A", "all_annual_gates_pass": True})
    for index, field in enumerate(ORDER):
        left, right = dict(base), dict(base)
        right["configuration_id"] = "B"
        # Higher is better except streak and concentration.
        right[field] = 0.0 if field not in ("longest_negative_month_streak", "top_3_concentration") else 2.0
        frame = pd.DataFrame([left, right])
        assert rank_candidates(frame).iloc[0].configuration_id == "A"
        assert first_differentiating_criterion(frame.iloc[0], frame.iloc[1]) == field
        # Ensure prior criteria really tie in each synthetic comparison.
        assert all(left[x] == right[x] for x in ORDER[:index])


def test_provenance_unknown_nonancestor_and_changed_source(tmp_path):
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.email", "audit@example.invalid"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.name", "Audit"], cwd=tmp_path, check=True)
    (tmp_path / "one").write_text("one")
    subprocess.run(["git", "add", "one"], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-qm", "one"], cwd=tmp_path, check=True)
    first = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=tmp_path, text=True).strip()
    assert validate_starting_sha(tmp_path, "0" * 40) == (False, False)
    subprocess.run(["git", "checkout", "-q", "--orphan", "unrelated"], cwd=tmp_path, check=True)
    subprocess.run(["git", "rm", "-qf", "one"], cwd=tmp_path, check=True)
    (tmp_path / "two").write_text("two")
    subprocess.run(["git", "add", "two"], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-qm", "two"], cwd=tmp_path, check=True)
    assert validate_starting_sha(tmp_path, first) == (True, False)

    ledger = tmp_path / "ledger.csv"
    ledger.write_text("trade_id\n1\n")
    import hashlib
    digest = hashlib.sha256(ledger.read_bytes()).hexdigest()
    assert source_matches(ledger, digest, 1)
    ledger.write_text("trade_id\n1\n2\n")
    assert not source_matches(ledger, digest, 1)
