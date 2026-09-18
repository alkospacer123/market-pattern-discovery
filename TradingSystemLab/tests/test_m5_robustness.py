from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pandas as pd
import pytest

from TradingSystemLab.multitimeframe.phase73 import hash_tree
from TradingSystemLab.tests.test_m5_overextension_session_candidate import _fixture
from TradingSystemLab.timeframe_analysis.m5_robustness import FILES, STATUS, run


def _hashes(path: Path) -> dict[str, str]:
    return {str(item.relative_to(path)): hashlib.sha256(item.read_bytes()).hexdigest()
            for item in sorted(path.rglob("*")) if item.is_file()}


def test_determinism_artifacts_and_sources_are_immutable(tmp_path: Path) -> None:
    validation, optimization, market = _fixture(tmp_path)
    sources = hash_tree(validation), hash_tree(optimization)
    output = tmp_path / "robustness"
    first_manifest = run(validation, optimization, output=output, market_data=market)
    first_hashes = _hashes(output)
    second_manifest = run(validation, optimization, output=output, market_data=market)
    assert first_hashes == _hashes(output)
    assert first_manifest == second_manifest
    assert sources == (hash_tree(validation), hash_tree(optimization))
    assert first_manifest["status"] == STATUS
    assert {item.name for item in output.iterdir()} == {"T2", "T3", "COMBINED", "manifest.json", "robustness_report.md"}
    for scope in ("T2", "T3", "COMBINED"):
        assert {item.name for item in (output / scope).iterdir()} == set(FILES)


def test_true_oos_is_rejected_before_output(tmp_path: Path) -> None:
    validation, optimization, market = _fixture(tmp_path)
    market["CNYRUBF"] = market["CNYRUBF"].set_axis(pd.date_range("2025-01-01", periods=500, freq="5min", tz="UTC"))
    output = tmp_path / "robustness"
    with pytest.raises(ValueError, match="TRUE_OOS"):
        run(validation, optimization, output=output, market_data=market)
    assert not output.exists()


def test_no_strategy_or_parameter_modification(tmp_path: Path) -> None:
    validation, optimization, market = _fixture(tmp_path)
    ledgers_before = hash_tree(validation)
    registries_before = hash_tree(optimization)
    manifest = run(validation, optimization, output=tmp_path / "out", market_data=market)
    assert manifest["diagnostic_only"] is True
    assert manifest["optimization"] is False
    assert manifest["strategy_change"] is False
    assert manifest["parameter_change"] is False
    assert manifest["true_oos_access"] is False
    assert ledgers_before == hash_tree(validation)
    assert registries_before == hash_tree(optimization)
    registry = optimization / "T3/candidate_registry.json"
    registry.write_text(json.dumps({"candidate_id": "changed"}))
    with pytest.raises(ValueError, match="CANDIDATE_IDENTITY_MISMATCH"):
        run(validation, optimization, output=tmp_path / "other", market_data=market)


def test_reports_cover_required_slices_and_calendar(tmp_path: Path) -> None:
    validation, optimization, market = _fixture(tmp_path)
    output = tmp_path / "out"
    run(validation, optimization, output=output, market_data=market)
    interaction = pd.read_csv(output / "COMBINED/interaction_report.csv")
    assert set(interaction.variant) == {"SESSION_CANDIDATE", "EMA50_NEAR", "EMA50_NORMAL", "EMA50_EXTENDED", "SESSION_EMA50_NORMAL", "SESSION_EMA50_EXTENDED"}
    monthly = pd.read_csv(output / "COMBINED/monthly_report.csv")
    assert len(monthly.query("variant == 'BASELINE'")) == 24
    assert set(pd.read_csv(output / "T2/yearly_report.csv").year) == {2023, 2024}
    assert set(pd.read_csv(output / "T2/instrument_report.csv").instrument) == {"USDRUBF", "CNYRUBF"}
