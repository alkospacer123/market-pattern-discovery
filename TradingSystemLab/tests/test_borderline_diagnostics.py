import json
from pathlib import Path

import pandas as pd

from TradingSystemLab.walk_forward import borderline_diagnostics as diagnostics


def test_phase41_artifact_contract_and_safety_flags(tmp_path):
    output = tmp_path / "diagnostics"
    manifest = diagnostics.run(output=output)
    assert manifest["status"] == "PHASE_4_1_BORDERLINE_DIAGNOSTICS_COMPLETE"
    assert manifest["optimization"] is False and manifest["ranking"] is False
    assert manifest["true_oos_blocked"] is True
    expected = {"final_report.md", "fold_analysis.csv", "leave_one_fold_out.csv",
        "instrument_report.csv", "direction_report.csv", "quarter_report.csv",
        "concentration_report.csv", "mae_mfe_report.csv", "train_test_decay.csv",
        "bootstrap_report.csv", "metrics.json"}
    assert expected == {p.name for p in (output / "T2").iterdir()}


def test_diagnostics_are_byte_deterministic(tmp_path):
    output = tmp_path / "diagnostics"
    diagnostics.run(output=output)
    first = diagnostics.artifact_sha256(output)
    diagnostics.run(output=output)
    assert diagnostics.artifact_sha256(output) == first


def test_required_analyses_and_classifications(tmp_path):
    output = tmp_path / "diagnostics"
    diagnostics.run(output=output)
    for key in diagnostics.KEYS:
        metrics = json.loads((output / key / "metrics.json").read_text())
        assert metrics["classification"] == "SAMPLE_LIMITED"
        assert metrics["leave_one_fold_out_edge_survives_all"] is True
        assert len(pd.read_csv(output / key / "fold_analysis.csv")) == 4
        assert len(pd.read_csv(output / key / "leave_one_fold_out.csv")) == 4
        bootstrap = pd.read_csv(output / key / "bootstrap_report.csv").iloc[0]
        assert bootstrap.iterations == 10_000 and bootstrap.diagnostic_only
