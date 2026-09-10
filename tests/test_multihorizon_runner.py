import pytest
from market_pattern_discovery.orchestration.multihorizon import MultiHorizonResearchRunner
from market_pattern_discovery.research import ResearchMemory


def test_runner_requires_explicit_finite_cycles(tmp_path):
    runner = MultiHorizonResearchRunner(tmp_path, tmp_path / "memory")
    with pytest.raises(ValueError, match="unlimited"):
        runner.run(0)


def test_runner_hands_persisted_research_to_trading_pipeline(monkeypatch, tmp_path):
    runner = MultiHorizonResearchRunner(tmp_path, tmp_path / "memory")
    calls = []
    monkeypatch.setattr(runner.scheduler, "plan", lambda completed, budget: ())
    monkeypatch.setattr(runner.trading_pipeline, "run", lambda: calls.append("run"))

    runner.run(3)

    assert calls == ["run"]


def test_strategy_market_data_uses_close_availability_and_exact_scope(monkeypatch, tmp_path):
    from datetime import datetime, timezone
    from types import SimpleNamespace
    import pandas as pd

    runner = MultiHorizonResearchRunner(tmp_path, tmp_path / "memory")
    opened = pd.Timestamp(datetime(2026, 1, 1, 10, tzinfo=timezone.utc))
    loaded = []

    def load(symbol, timeframe_id):
        loaded.append((symbol, timeframe_id))
        return pd.DataFrame({"timestamp": [opened], "timeframe": [timeframe_id]})

    monkeypatch.setattr(runner.loader, "load", load)
    strategy = SimpleNamespace(symbol="CNY", execution_timeframe="M5",
                               context_timeframes=("H1", "D1"))
    data = runner._strategy_market_data(strategy)

    assert tuple(data) == ("M5", "H1", "D1")
    assert data["M5"].timestamp.iloc[0] == opened + pd.Timedelta(minutes=5)
    assert data["H1"].timestamp.iloc[0] == opened + pd.Timedelta(hours=1)
    assert data["D1"].timestamp.iloc[0] == opened + pd.Timedelta(days=1)
    assert loaded == [("CNY", "M5"), ("CNY", "H1"), ("CNY", "D1")]


def test_runner_restart_skips_persisted_cells(monkeypatch, tmp_path):
    runner = MultiHorizonResearchRunner(tmp_path, tmp_path / "memory", seed=1)
    import pandas as pd
    market = pd.DataFrame({"close": range(1, 31), "high": range(2, 32)})
    features = pd.DataFrame({
        "return_1": [0.1] * 30, "range": [1.] * 30,
        "range_median_7": [1.] * 30, "prior_high_20": [0.] * 30,
        "context_direction": [0.1] * 30,
        "future_signed_return": [0.01, -0.01] * 15,
    })
    context = lambda cell: pd.DataFrame({f"context_{tf}_close": range(30)
                                         for tf in cell.context_timeframes})
    monkeypatch.setattr(runner, "_prepare", lambda cell: (market, context(cell), features))
    assert runner.run(2)[-1].recorded == 1
    restarted = MultiHorizonResearchRunner(tmp_path, tmp_path / "memory", seed=1)
    monkeypatch.setattr(restarted, "_prepare", runner._prepare)
    assert restarted.run(1)[0].recorded == 1
    memory = ResearchMemory(tmp_path / "memory")
    assert len(memory.research_attempts()) == 3
    assert len({row["attempt_id"] for row in memory.research_attempts()}) == 3
    assert len(memory.scientific_findings()) == 3
    for finding, knowledge in zip(memory.scientific_findings(), memory.knowledge_records()):
        evaluation_id = finding["evaluation"]["evaluation_id"]
        assert finding["evidence"]["evaluation_id"] == evaluation_id
        if finding["pattern_effect"]:
            assert finding["pattern_effect"]["evaluation_id"] == evaluation_id
        assert knowledge["evidence_reference"] == evaluation_id


def test_unresolved_finding_is_persisted_without_manufactured_effect(monkeypatch, tmp_path):
    import pandas as pd
    runner = MultiHorizonResearchRunner(tmp_path, tmp_path / "memory", seed=1)
    market = pd.DataFrame({"close": [1, 2, 3], "high": [2, 3, 4]})
    features = pd.DataFrame({"return_1": [0., 1., 1.], "range": [1.] * 3,
        "range_median_7": [1.] * 3, "prior_high_20": [0.] * 3,
        "context_direction": [1.] * 3, "future_signed_return": [1., -1., None]})
    monkeypatch.setattr(runner, "_prepare", lambda cell: (market,
        pd.DataFrame({f"context_{tf}_close": range(3) for tf in cell.context_timeframes}),
        features))
    assert runner.run(1)[0].recorded == 1
    memory = ResearchMemory(tmp_path / "memory")
    assert memory.knowledge_records()[0]["conclusion"] == "unresolved"
    assert memory.scientific_findings()[0]["pattern_effect"] is None
