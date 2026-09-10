from datetime import datetime, timedelta, timezone

import pytest

from market_pattern_discovery.backtest import BacktestResult
from market_pattern_discovery.orchestration import AutonomousTradingPipeline
from market_pattern_discovery.ranking import StrategyRankingEngine
from market_pattern_discovery.research import ResearchMemory
from market_pattern_discovery.research.hypotheses import Hypothesis
from market_pattern_discovery.research.intelligence import Evidence, Evaluation, PatternEffect
from market_pattern_discovery.validation import ValidationReport, ValidationStatus


def finding(memory):
    hypothesis = Hypothesis("cell", "TEST", "SCALPING", "M5", ("M15",),
        "KNOWN", "known_event_evaluation", {"signal": True},
        "future_signed_return_same_trading_day", "observable baseline")
    evaluation = Evaluation("evaluation", .1, 50, {}, hypothesis.hypothesis_id,
        0, .1, hypothesis.target_definition, hypothesis.method,
        hypothesis.context_timeframes, {}, hypothesis.state_definition,
        hypothesis.baseline_definition, {}, {}, {})
    evidence = Evidence("evaluation", True, "qualified", True, True, True, True)
    effect = PatternEffect("effect", "evaluation", .1, 50)
    memory.record_scientific_finding(evaluation, evidence, effect, hypothesis)


class Backtests:
    def __init__(self, calls, fail=False): self.calls, self.fail = calls, fail
    def run(self, strategy, data, *, data_version):
        self.calls.append(("backtest", strategy.strategy_id))
        if self.fail: raise RuntimeError("backtest failed")
        at = datetime(2024, 1, 1, tzinfo=timezone.utc)
        return BacktestResult("bt-" + strategy.strategy_id, strategy.strategy_id,
            strategy.symbol, strategy.execution_timeframe, strategy.context_timeframes,
            at, at + timedelta(days=1), 4, 3, 1, 3, -1, 2, 3, .5, .75,
            1, 1, -1, 1, timedelta(minutes=5), "fixed:1", "fixed:1",
            data_version, "fake-backtest")


class Validations:
    def __init__(self, calls, fail=False): self.calls, self.fail = calls, fail
    def validate(self, strategy, backtest, data, *, split, data_version):
        self.calls.append(("validation", backtest.backtest_id))
        if self.fail: raise RuntimeError("validation failed")
        return ValidationReport("val-" + backtest.backtest_id, backtest.backtest_id,
            strategy.strategy_id, strategy.symbol, strategy.execution_timeframe, "v1",
            split.training_period, split.validation_period, split.true_oos_period,
            "train", "validation", "oos", (), 1, 1, 1, 50, 4, 3, .5, 1,
            ValidationStatus.ACCEPTED, "passed", "fake-validation", data_version)


class Rankings(StrategyRankingEngine):
    def __init__(self, calls, fail=False): super().__init__(); self.calls, self.fail = calls, fail
    def rank(self, inputs):
        values = tuple(inputs)
        self.calls.append(("ranking", values[0][0].validation_id))
        if self.fail: raise RuntimeError("ranking failed")
        return super().rank(values)


def pipeline(memory, calls, *, backtest_fail=False, validation_fail=False, ranking_fail=False):
    return AutonomousTradingPipeline(memory, lambda strategy: {"scope": strategy.symbol},
        backtest_engine=Backtests(calls, backtest_fail),
        validation_engine=Validations(calls, validation_fail),
        ranking_engine=Rankings(calls, ranking_fail), data_version="fixture-v1")


def test_full_chain_lineage_order_and_restart(tmp_path):
    memory = ResearchMemory(tmp_path); finding(memory); calls = []
    first = pipeline(memory, calls).run()
    assert (first.trading_candidates, first.strategy_candidates, first.backtests,
            first.validations, first.rankings) == (1, 27, 27, 27, 27)
    assert [name for name, _ in calls] == ["backtest"] * 27 + ["validation"] * 27 + ["ranking"]
    ranking = next(iter(memory.strategy_rankings().values()))
    report = memory.validation_reports()[ranking.validation_id]
    backtest = memory.backtest_results()[report.backtest_id]
    strategy = memory.strategy_candidates()[ranking.strategy_id]
    candidate = memory.trading_candidates()[ranking.trading_candidate_id]
    assert backtest.strategy_id == strategy.strategy_id
    assert strategy.source_trading_candidate_id == candidate.candidate_id
    assert candidate.source_pattern_effect_id == ranking.pattern_effect_id == "effect"

    restarted = ResearchMemory(tmp_path)
    second = pipeline(restarted, []).run()
    assert (second.trading_candidates, second.strategy_candidates, second.backtests,
            second.validations, second.rankings) == (0, 0, 0, 0, 0)
    assert len(restarted.strategy_candidates()) == len(set(restarted.strategy_candidates())) == 27


def test_stage_failures_do_not_create_invalid_downstream_objects(tmp_path):
    memory = ResearchMemory(tmp_path / "backtest"); finding(memory)
    pipeline(memory, [], backtest_fail=True).run()
    assert not memory.backtest_results() and not memory.validation_reports()

    memory = ResearchMemory(tmp_path / "validation"); finding(memory)
    pipeline(memory, [], validation_fail=True).run()
    assert len(memory.backtest_results()) == 27 and not memory.validation_reports()

    memory = ResearchMemory(tmp_path / "ranking"); finding(memory)
    pipeline(memory, [], ranking_fail=True).run()
    assert len(memory.validation_reports()) == 27 and not memory.strategy_rankings()
    assert memory.pipeline_failures()


def test_pipeline_does_not_modify_or_select_strategies(tmp_path):
    memory = ResearchMemory(tmp_path); finding(memory)
    pipeline(memory, []).run()
    before = memory.strategy_candidates()
    pipeline(ResearchMemory(tmp_path), []).run()
    assert ResearchMemory(tmp_path).strategy_candidates() == before


@pytest.mark.parametrize(("horizon", "execution", "contexts"), [
    ("SCALPING", "M1", ("M15",)),
    ("SCALPING", "M5", ("M15",)),
    ("INTRADAY", "M5", ("H1", "D1")),
    ("INTRADAY", "M15", ("H1", "D1")),
    ("INTRADAY", "M30", ("H1", "D1")),
    ("MEDIUM_TERM", "H1", ("D1",)),
    ("MEDIUM_TERM", "D1", ("D1",)),
])
def test_pipeline_preserves_multi_horizon_scope(tmp_path, horizon, execution, contexts):
    memory = ResearchMemory(tmp_path)
    hypothesis = Hypothesis("cell", "TEST", horizon, execution, contexts,
        "KNOWN", "known_event_evaluation", {"signal": True},
        "future_signed_return_same_trading_day", "observable baseline")
    evaluation = Evaluation("evaluation", .1, 50, {}, hypothesis.hypothesis_id,
        target=hypothesis.target_definition, method=hypothesis.method,
        context=hypothesis.context_timeframes, uncertainty={},
        state_definition=hypothesis.state_definition, stability={},
        null_comparison={}, multiplicity={})
    memory.record_scientific_finding(evaluation,
        Evidence("evaluation", True, "qualified", True, True, True, True),
        PatternEffect("effect", "evaluation", .1, 50), hypothesis)
    pipeline(memory, []).run()
    strategy = next(iter(memory.strategy_candidates().values()))
    assert (strategy.horizon, strategy.execution_timeframe,
            strategy.context_timeframes) == (horizon, execution, contexts)
