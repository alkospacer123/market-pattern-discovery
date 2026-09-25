import json
from pathlib import Path
import shutil

import pandas as pd
import pytest

from TradingSystemLab.audit_perpetual_v3_phase2a_t2 import ROOT, audit


def csv_mutation(root: Path, relative: str, mutate):
    path = root / relative
    frame = pd.read_csv(path)
    mutate(frame)
    frame.to_csv(path, index=False)


def json_mutation(root: Path, relative: str, key: str, value):
    path = root / relative
    body = json.loads(path.read_text())
    body[key] = value
    path.write_text(json.dumps(body, indent=2, sort_keys=True) + "\n")


MUTATIONS = {
    "missing_configuration": lambda root: csv_mutation(root, "M30/parameters.csv", lambda frame: frame.drop(frame.index[-1], inplace=True)),
    "duplicate_configuration": lambda root: csv_mutation(root, "M30/parameters.csv", lambda frame: frame.loc.__setitem__((frame.index[-1], slice(None)), frame.iloc[0].to_numpy())),
    "baseline_flag": lambda root: csv_mutation(root, "M30/parameters.csv", lambda frame: frame.__setitem__("is_baseline", False)),
    "parameter_outside_space": lambda root: csv_mutation(root, "M30/parameters.csv", lambda frame: frame.loc.__setitem__((0, "ema_fast"), 999)),
    "multi_factor": lambda root: csv_mutation(root, "M30/parameters.csv", lambda frame: (frame.__setitem__("ema_fast", frame.ema_fast.mask(frame.index == 0, 30)), frame.__setitem__("ema_slow", frame.ema_slow.mask(frame.index == 0, 250)))),
    "result_expectancy": lambda root: csv_mutation(root, "M30/results.csv", lambda frame: frame.__setitem__("expectancy_C1", frame.expectancy_C1.mask(frame.index == 0, frame.expectancy_C1.iloc[0] + .1))),
    "classification": lambda root: csv_mutation(root, "M30/plateau_report.csv", lambda frame: frame.__setitem__("classification", frame.classification.mask(frame.index == 0, "NO_EDGE"))),
    "neighbor_list": lambda root: csv_mutation(root, "M30/plateau_report.csv", lambda frame: frame.__setitem__("neighbor_ids", frame.neighbor_ids.mask(frame.index == 0, "tampered"))),
    "stability_tolerance": lambda root: csv_mutation(root, "M30/plateau_report.csv", lambda frame: frame.__setitem__("stability_tolerance", frame.stability_tolerance.mask(frame.index == 0, 999))),
    "true_oos_unblocked": lambda root: json_mutation(root, "manifest.json", "true_oos_blocked", False),
    "ranking": lambda root: json_mutation(root, "manifest.json", "ranking", True),
    "candidate_selection": lambda root: json_mutation(root, "manifest.json", "candidate_selection", True),
}


@pytest.mark.parametrize("name", MUTATIONS)
def test_audit_fails_closed_on_tampering(tmp_path, name):
    target = tmp_path / "T2"
    shutil.copytree(ROOT, target)
    MUTATIONS[name](target)
    with pytest.raises(AssertionError):
        audit(target, check_protected=False, write_report=False)
