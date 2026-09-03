from __future__ import annotations

import builtins
import importlib
import json
from pathlib import Path
import sys

import numpy as np
import pandas as pd
import pytest

from market_pattern_discovery.analysis.phase4b import (activity_summary, categorical_summary,
    coverage_summary, finite_summary, marginal_drift, quality_summary, target_validity, write_reports,
    REPORT_NAMES)
from market_pattern_discovery.features.feature_set import load_manifest, manifest_signature
from market_pattern_discovery.research.protocol import AccessMode, load_protocol, request_access
from market_pattern_discovery.research.registry import register_experiment
from market_pattern_discovery.targets.behavior_target_set import load_behavior_target_set
from market_pattern_discovery.validation.phase4b import _static_scan


def frame() -> pd.DataFrame:
    opened = pd.to_datetime(["2026-01-05 09:00+03:00", "2026-01-05 10:00+03:00",
                             "2026-02-02 09:00+03:00"])
    return pd.DataFrame({"open_time": opened, "close_time": opened + pd.Timedelta(minutes=1),
                         "trading_date": [x.date() for x in opened], "x": [1.0, np.nan, 4.0]})


def test_coverage_month_hour_weekday_partitions():
    data = frame(); coverage = coverage_summary(data); activity = activity_summary(data)
    assert coverage["rows"] == 3 and coverage["trading_dates"] == 2
    assert coverage["months"]["2026-01"]["rows"] == 2
    assert activity["hour"]["9"]["rows"] == 2
    assert activity["weekday"]["0"]["contributing_dates"] == 2


def test_quantiles_nan_constant_binary_and_infinity():
    summary = finite_summary(pd.Series([1, 2, np.nan, np.inf, 4]))
    assert summary["finite_count"] == 3 and summary["nan_count"] == 1
    assert summary["infinite_count"] == 1 and summary["median"] == 2
    constant = quality_summary(pd.Series([3, 3, 3])); binary = quality_summary(pd.Series([0, 1, 0]))
    assert constant["flags"]["near_constant"] and binary["flags"]["binary_or_categorical_like"]


def test_marginal_drift_is_deterministic():
    data = frame(); first = marginal_drift(data, ["x"]); second = marginal_drift(data, ["x"])
    assert first == second and first["x"]["median_shift"] == 3


def test_target_validity_and_categorical_prevalence():
    data = pd.DataFrame({"target_future_valid_1": [True, False, False],
                         "target_future_invalid_reason_1": [None, "gap", "day_end"],
                         "label_x": [1, 0, np.nan]})
    validity = target_validity(data, list(data)); prevalence = categorical_summary(data.label_x)
    assert validity["1"]["valid_count"] == 1 and validity["1"]["invalid_reasons"]["gap"] == 1
    assert prevalence["undefined_count"] == 1


def test_report_schema(tmp_path: Path):
    reports = {name: {} for name in REPORT_NAMES}; reports["summary"] = {"status": "PASS"}
    sizes = write_reports(reports, tmp_path)
    assert set(sizes) == {f"{x}.json" for x in REPORT_NAMES} | {"summary.json"}
    assert all(isinstance(json.loads(path.read_text()), dict) for path in tmp_path.glob("*.json"))


def test_import_and_memory_fallback_without_resource(monkeypatch):
    module_name = "market_pattern_discovery.analysis.phase4b"
    original_import = builtins.__import__

    def import_without_resource(name, *args, **kwargs):
        if name == "resource":
            raise ModuleNotFoundError("No module named 'resource'")
        return original_import(name, *args, **kwargs)

    monkeypatch.delitem(sys.modules, module_name)
    monkeypatch.setattr(builtins, "__import__", import_without_resource)

    phase4b = importlib.import_module(module_name)

    assert phase4b.memory_mb() == 0.0


def test_contract_signatures_and_static_safety():
    feature = load_manifest(); behavior = load_behavior_target_set()
    assert manifest_signature(feature) == feature["signature_sha256"]
    assert behavior["feature_set_signature"] == feature["signature_sha256"]
    assert _static_scan() == []


def test_descriptive_access_and_synthetic_sealed_year_rejection():
    protocol = load_protocol()
    request_access(AccessMode.DESCRIPTIVE_DEVELOPMENT,
                   ("2026-06-01T00:00:00Z", "2026-06-02T00:00:00Z"), protocol=protocol)
    with pytest.raises(PermissionError):
        request_access(AccessMode.DESCRIPTIVE_DEVELOPMENT,
                       ("2027-01-01T00:00:00Z", "2027-01-02T00:00:00Z"), protocol=protocol)


def test_descriptive_registry_zero_candidates_and_hypotheses(tmp_path: Path):
    feature = load_manifest(); behavior = load_behavior_target_set()
    spec = {"research_track":"unknown_discovery", "research_stage":"descriptive", "experiment_type":"descriptive",
        "description":"NO FEATURE→OUTCOME RELATIONSHIP ANALYSIS.", "instrument_scope":"cross_instrument",
        "timeframe_scope":"M1 and M5", "discovery_period":"approved 2026 development coverage",
        "confirmation_period":"descriptive coverage only", "feature_set_version":"1.0",
        "feature_set_signature":feature["signature_sha256"], "behavior_target_set_version":"1.0",
        "behavior_target_signature":behavior["signature_sha256"], "code_commit":"synthetic", "method":"marginal summaries",
        "method_version":"1.0", "input_feature_subset":"all frozen", "output_behavior_subset":"all retained",
        "hyperparameters":{"seed":20260401}, "intended_effect_metric":"none", "statistical_test":"none",
        "number_of_hypotheses_tested":0, "multiple_testing_family":"none", "status":"registered",
        "candidate_ids_created":[], "notes":"descriptive only"}
    result = register_experiment(spec, tmp_path)
    assert result["candidate_ids_created"] == [] and result["number_of_hypotheses_tested"] == 0


@pytest.mark.parametrize("bad", ["feature_importance", "mutual_info", "take_profit"])
def test_forbidden_construct_rejection(monkeypatch, tmp_path: Path, bad: str):
    implementation = tmp_path / "phase4b.py"; implementation.write_text(bad)
    text = implementation.read_text()
    assert bad in text
