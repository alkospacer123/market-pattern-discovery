import hashlib
import json
from pathlib import Path
import shutil

import pandas as pd
import pytest

import TradingSystemLab.audit_perpetual_v3_phase2 as subject


def test_full_artifact_only_consolidation_and_contract():
    result = subject.audit(write_bundle=False)
    assert result == {"status": subject.STATUS, "audit": "PASS", "studies": 4,
                      "configurations": 82, "robust_plateau_configurations": 25,
                      "failures": []}
    assert len(subject.bounded_design("T2")) == 19
    assert len(subject.bounded_design("T3")) == 22
    assert subject.BASELINES["T2"]["max_initial_stop_atr"] == 3.0
    assert subject.BASELINES["T3"]["ema_period"] == 100
    manifest = json.loads((subject.ROOT / "manifest.json").read_text())
    assert manifest["true_oos_blocked"] is True
    assert not manifest["ranking"] and not manifest["candidate_selection"]


def test_root_bundle_is_deterministic(tmp_path):
    target = tmp_path / "optimization"
    shutil.copytree(subject.ROOT, target)
    subject.audit(target, check_protected=False)
    names = ("manifest.json", "robust_plateau_inventory.csv",
             "Phase_2_Optimization_Report.md", "Phase_2_Optimization_Audit_Report.md")
    first = {name: hashlib.sha256((target / name).read_bytes()).hexdigest() for name in names}
    subject.audit(target, check_protected=False)
    second = {name: hashlib.sha256((target / name).read_bytes()).hexdigest() for name in names}
    assert first == second


def test_independent_metric_calculation_reconciles_phase1():
    expected = {("T2", "M30"): 366, ("T2", "H1"): 176,
                ("T3", "M30"): 398, ("T3", "H1"): 184}
    for study, trades in expected.items():
        metrics = subject.phase1_metrics(*study)
        assert metrics["trades"] == trades
        assert metrics["net_R_C1"] == pytest.approx(metrics["expectancy_C1"] * trades)


def test_inventory_is_canonical_and_contains_only_reconstructed_plateaus():
    inventory = pd.read_csv(subject.ROOT / "robust_plateau_inventory.csv")
    assert len(inventory) == 25
    assert inventory.groupby(["strategy", "timeframe"], sort=False).size().tolist() == [3, 4, 9, 9]
    assert not {"rank", "score", "winner", "selected"} & set(inventory.columns)
