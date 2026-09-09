import pytest
from market_pattern_discovery.orchestration.multihorizon import MultiHorizonResearchRunner
from market_pattern_discovery.research import ResearchMemory


def test_runner_requires_explicit_finite_cycles(tmp_path):
    runner = MultiHorizonResearchRunner(tmp_path, tmp_path / "memory")
    with pytest.raises(ValueError, match="unlimited"):
        runner.run(0)


def test_runner_restart_skips_persisted_cells(monkeypatch, tmp_path):
    runner = MultiHorizonResearchRunner(tmp_path, tmp_path / "memory", seed=1)
    monkeypatch.setattr(runner, "_prepare", lambda cell: (object(), object(),
        __import__("pandas").DataFrame({"close_change": [None, 1, -1]})))
    assert runner.run(2)[-1].recorded == 1
    restarted = MultiHorizonResearchRunner(tmp_path, tmp_path / "memory", seed=1)
    monkeypatch.setattr(restarted, "_prepare", runner._prepare)
    assert restarted.run(1)[0].recorded == 1
    memory = ResearchMemory(tmp_path / "memory")
    assert len(memory.research_attempts()) == 3
    assert len({row["attempt_id"] for row in memory.research_attempts()}) == 3
