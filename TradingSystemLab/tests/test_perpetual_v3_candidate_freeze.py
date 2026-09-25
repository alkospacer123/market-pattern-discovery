import ast
import json
from pathlib import Path

from TradingSystemLab.perpetual_v3_candidate_freeze import PREDECLARED_CANDIDATES, generate

ROOT = Path(__file__).resolve().parents[2]


def test_generation_is_byte_deterministic(tmp_path):
    first, second = tmp_path / "first", tmp_path / "second"
    generate(ROOT, first)
    generate(ROOT, second)
    for name in ("candidate_registry.json", "manifest.json", "Candidate_Freeze_Report.md"):
        assert (first / name).read_bytes() == (second / name).read_bytes()


def test_exact_immutable_registry(tmp_path):
    output = generate(ROOT, tmp_path)
    registry = json.loads((output / "candidate_registry.json").read_text())
    assert registry["immutable"] is True
    assert len(registry["candidates"]) == 4
    assert [tuple(record[key] for key in ("candidate_id", "strategy", "timeframe", "phase2_configuration_id")) for record in registry["candidates"]] == list(PREDECLARED_CANDIDATES)


def test_predeclarations_are_literal_and_no_selection_or_execution_primitives():
    path = ROOT / "TradingSystemLab/perpetual_v3_candidate_freeze.py"
    source = path.read_text()
    tree = ast.parse(source)
    declaration = next(node for node in tree.body if isinstance(node, ast.Assign) and any(isinstance(target, ast.Name) and target.id == "PREDECLARED_CANDIDATES" for target in node.targets))
    assert ast.literal_eval(declaration.value) == PREDECLARED_CANDIDATES
    calls = {node.func.id if isinstance(node.func, ast.Name) else node.func.attr for node in ast.walk(tree) if isinstance(node, ast.Call) and isinstance(node.func, (ast.Name, ast.Attribute))}
    assert calls.isdisjoint({"sorted", "sort", "nlargest", "nsmallest", "idxmax", "idxmin", "argmax", "argmin", "rank", "score"})
    assert not any(token in source for token in ("Backtester", "load_development", "T2TrendPullback", "T3MTFTrend", "four_bar_context"))
