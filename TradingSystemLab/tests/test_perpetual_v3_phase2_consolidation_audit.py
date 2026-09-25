import json
from pathlib import Path
import shutil

import pandas as pd
import pytest

import TradingSystemLab.audit_perpetual_v3_phase2 as subject


def csv_change(root: Path, relative: str, change):
    path = root / relative
    frame = pd.read_csv(path)
    change(frame)
    frame.to_csv(path, index=False)


def json_change(root: Path, relative: str, key: str, value):
    path = root / relative
    body = json.loads(path.read_text())
    body[key] = value
    path.write_text(json.dumps(body, indent=2, sort_keys=True) + "\n")


MUTATIONS = {
    "remove_t2_m30": lambda r: csv_change(r, "T2/M30/parameters.csv", lambda f: f.drop(f.index[-1], inplace=True)),
    "duplicate_t2_h1": lambda r: csv_change(r, "T2/H1/parameters.csv", lambda f: f.loc.__setitem__((f.index[-1], slice(None)), f.iloc[0].to_numpy())),
    "t3_parameter": lambda r: csv_change(r, "T3/M30/parameters.csv", lambda f: f.loc.__setitem__((0, "ema_period"), 999)),
    "t3_multifactor": lambda r: csv_change(r, "T3/H1/parameters.csv", lambda f: (f.loc.__setitem__((0, "ema_period"), 50), f.loc.__setitem__((0, "breakout_period"), 55))),
    "configuration_id": lambda r: csv_change(r, "T3/M30/parameters.csv", lambda f: f.loc.__setitem__((0, "configuration_id"), "tampered")),
    "baseline_flag": lambda r: csv_change(r, "T2/M30/parameters.csv", lambda f: f.__setitem__("is_baseline", False)),
    "expectancy": lambda r: csv_change(r, "T3/H1/results.csv", lambda f: f.loc.__setitem__((0, "expectancy_C1"), f.iloc[0].expectancy_C1 + .1)),
    "classification": lambda r: csv_change(r, "T2/M30/plateau_report.csv", lambda f: f.loc.__setitem__((0, "classification"), "NO_EDGE")),
    "neighbors": lambda r: csv_change(r, "T3/M30/plateau_report.csv", lambda f: f.loc.__setitem__((0, "neighbor_ids"), "tampered")),
    "tolerance": lambda r: csv_change(r, "T2/H1/plateau_report.csv", lambda f: f.loc.__setitem__((0, "stability_tolerance"), 99)),
    "sensitivity": lambda r: csv_change(r, "T3/M30/sensitivity_report.csv", lambda f: f.loc.__setitem__((0, "mean_expectancy_C1"), 99)),
    "remove_region": lambda r: (r / "T2/M30/best_regions.md").write_text((r / "T2/M30/best_regions.md").read_text().replace("- `T2-M30-608dc87d09f1`\n", "")),
    "add_region": lambda r: (r / "T3/H1/best_regions.md").write_text((r / "T3/H1/best_regions.md").read_text() + "- `T3-H1-not-robust`\n"),
    "candidate_selection": lambda r: json_change(r, "T2/manifest.json", "candidate_selection", True),
    "ranking": lambda r: json_change(r, "T3/manifest.json", "ranking", True),
    "true_oos": lambda r: json_change(r, "T3/manifest.json", "true_oos_blocked", False),
    "strategy_hash": lambda r: json_change(r, "T2/M30/manifest.json", "frozen_strategy_hash", "0" * 64),
    "data_commit": lambda r: json_change(r, "T3/H1/manifest.json", "data_commit", "0" * 40),
    "missing_artifact": lambda r: (r / "T2/H1/experiment.json").unlink(),
}


@pytest.mark.parametrize("name", MUTATIONS)
def test_child_tampering_fails_closed(tmp_path, name):
    target = tmp_path / "optimization"
    shutil.copytree(subject.ROOT, target)
    MUTATIONS[name](target)
    with pytest.raises((AssertionError, FileNotFoundError)):
        subject.audit(target, check_protected=False, write_bundle=False)


def test_phase1_trade_tampering_fails_closed(tmp_path):
    optimization = tmp_path / "optimization"
    baseline = tmp_path / "baseline"
    shutil.copytree(subject.ROOT, optimization)
    shutil.copytree(subject.BASELINE_ROOT, baseline)
    csv_change(baseline, "T2/M30/USDRUBF/trades.csv",
               lambda frame: frame.loc.__setitem__((0, "net_R"), frame.iloc[0].net_R + 1))
    with pytest.raises(AssertionError):
        subject.audit(optimization, baseline_root=baseline, check_protected=False, write_bundle=False)


ROOT_MUTATIONS = {
    "remove_inventory": lambda r: csv_change(r, "robust_plateau_inventory.csv", lambda f: f.drop(f.index[-1], inplace=True)),
    "add_inventory": lambda r: csv_change(r, "robust_plateau_inventory.csv", lambda f: f.loc.__setitem__(len(f), f.iloc[0])),
    "changed_parameter": lambda r: csv_change(r, "robust_plateau_inventory.csv", lambda f: f.loc.__setitem__((0, "changed_parameter"), "tampered")),
    "performance_order": lambda r: csv_change(r, "robust_plateau_inventory.csv", lambda f: f.sort_values("PF_C1", ascending=False, inplace=True)),
    "rank_column": lambda r: csv_change(r, "robust_plateau_inventory.csv", lambda f: f.__setitem__("rank", range(len(f)))),
}


@pytest.mark.parametrize("name", ROOT_MUTATIONS)
def test_root_inventory_tampering_fails_closed(tmp_path, name):
    target = tmp_path / "optimization"
    shutil.copytree(subject.ROOT, target)
    ROOT_MUTATIONS[name](target)
    with pytest.raises(AssertionError):
        subject.audit(target, check_protected=False, write_bundle=False)
