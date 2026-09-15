from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pandas as pd

from TradingSystemLab.multitimeframe.phase72 import QUALIFICATION_RULES, classify, run


SOURCE = Path("TradingSystemLab/results/multitimeframe_research")


def _tree(path: Path) -> dict[str, str]:
    return {str(item.relative_to(path)): hashlib.sha256(item.read_bytes()).hexdigest()
            for item in sorted(path.rglob("*")) if item.is_file()}


def test_classification_is_deterministic_and_uses_declared_gates() -> None:
    evidence = {"trades": QUALIFICATION_RULES["minimum_trades"], "expectancy": .1,
                "net_R": 3.0, "max_drawdown": -2.0, "top5_positive_R_share": .3,
                "yearly_consistency": True, "direction_consistency": True,
                "instrument_consistency": True}
    assert classify(evidence) == classify(dict(reversed(list(evidence.items()))))
    assert classify(evidence)[0] == "ROBUST_TIMEFRAME_CANDIDATE"
    evidence["trades"] -= 1
    assert classify(evidence)[0] == "RESEARCH_ONLY"


def test_registry_is_complete_unranked_and_phase71_is_read_only(tmp_path: Path) -> None:
    before = _tree(SOURCE)
    analysis, registry = tmp_path / "analysis", tmp_path / "registry"
    result = run(SOURCE, analysis, registry)
    assert result["combinations"] == 16
    assert before == _tree(SOURCE)
    rows = pd.read_csv(registry / "candidate_registry.csv")
    assert len(rows) == 16
    assert list(rows.columns) == ["strategy", "instrument", "timeframe", "status", "reason"]
    manifest = json.loads((analysis / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["ranking_performed"] is False
    assert manifest["optimization_performed"] is False
    assert manifest["strategy_execution_performed"] is False
    assert manifest["market_data_accessed"] is False
    assert manifest["input_artifact_sha256"] == before


def test_all_outputs_are_sha256_repeatable(tmp_path: Path) -> None:
    analysis, registry = tmp_path / "analysis", tmp_path / "registry"
    run(SOURCE, analysis, registry)
    first = (_tree(analysis), _tree(registry))
    run(SOURCE, analysis, registry)
    assert first == (_tree(analysis), _tree(registry))
