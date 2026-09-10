from dataclasses import replace
from datetime import datetime, timedelta, timezone

import pytest

from market_pattern_discovery.backtest import BacktestEngine, CostModel
from market_pattern_discovery.contracts import deterministic_hash
from market_pattern_discovery.ranking import RankingStatus, StrategyRankingEngine
from market_pattern_discovery.research import (CandidateFamily, EntryDefinition, EntryType,
    ExitDefinition, ExitType, ResearchMemory, RiskDefinition, RiskType, StrategyCandidate,
    StrategyCandidateStatus, TradingCandidate, TradingCandidateStatus, TradingDirection)
from market_pattern_discovery.validation import (DataPartition, DataSplit, ValidationEngine,
    ValidationStatus, ValidationThresholds)

UTC = timezone.utc


def candidate():
    return StrategyCandidate("strategy-validation", "source-validation", "TEST", "SCALPING",
        "M5", ("M15",), TradingDirection.LONG, "fixed causal hypothesis", {"state": "on"},
        CandidateFamily.KNOWN, EntryDefinition(EntryType.CLOSE_ENTRY, {}),
        RiskDefinition(RiskType.FIXED_DISTANCE_STOP, {"distance_units": 2}),
        ExitDefinition(ExitType.TIME_EXIT, {"bars": 1}), StrategyCandidateStatus.READY_FOR_BACKTEST)


def market(*, losing=False):
    execution, context = [], []
    for year in range(2019, 2026):
        base = datetime(year, 6, 1, 9, tzinfo=UTC)
        context.extend([{"time": base - timedelta(minutes=15), "open": 1, "high": 2,
                         "low": 1, "close": 2, "state": "on"},
                        {"time": base, "open": 1, "high": 2, "low": 1, "close": 2,
                         "state": "on"}])
        closes = (10, 10.5, 11, 11.5) if not losing else (10, 9.5, 9, 8.5)
        for index, close in enumerate(closes):
            execution.append({"time": base + timedelta(minutes=5 * index), "open": close,
                "high": close + .25, "low": close - .25, "close": close, "state": "on",
                "signal": index == 0})
    return {"M5": execution, "M15": context}


def baseline(strategy, data):
    development = {tf: [row for row in rows if row["time"].year < 2025]
                   for tf, rows in data.items()}
    return BacktestEngine(CostModel(0, 0)).run(strategy, development, data_version="fixture-v1")


def source():
    return TradingCandidate("source-validation", "effect", "TEST", "SCALPING", "M5",
        ("M15",), TradingDirection.LONG, "fixed causal hypothesis", {"state": "on"},
        "behavior", "target", .1, 20, {"confidence": "reviewed"}, CandidateFamily.KNOWN,
        TradingCandidateStatus.READY_FOR_STRATEGY_SEARCH)


def test_split_is_versioned_disjoint_and_future_unavailable():
    split = DataSplit.calendar_v1()
    assert split.version == "calendar-split-v1"
    assert split.partition_at(datetime(2023, 1, 1, tzinfo=UTC),
                              observed_at=datetime(2024, 1, 1, tzinfo=UTC)) is DataPartition.TRAIN
    assert split.partition_at(datetime(2024, 1, 1, tzinfo=UTC),
                              observed_at=datetime(2024, 1, 1, tzinfo=UTC)) is DataPartition.VALIDATION
    assert split.partition_at(datetime(2025, 1, 1, tzinfo=UTC),
                              observed_at=datetime(2025, 1, 1, tzinfo=UTC)) is DataPartition.TRUE_OOS
    with pytest.raises(ValueError, match="future data"):
        split.partition_at(datetime(2025, 1, 1, tzinfo=UTC),
                           observed_at=datetime(2024, 12, 31, tzinfo=UTC))


def test_validation_lineage_determinism_walk_forward_and_fixed_robustness():
    strategy, data = candidate(), market()
    original = deterministic_hash(strategy)
    result = baseline(strategy, data)
    engine = ValidationEngine(CostModel(0, 0), thresholds=ValidationThresholds(minimum_trades=2))
    first = engine.validate(strategy, result, data, split=DataSplit.calendar_v1(),
                            data_version="fixture-v1")
    second = engine.validate(strategy, result, data, split=DataSplit.calendar_v1(),
                             data_version="fixture-v1")
    assert first == second
    assert first.backtest_id == result.backtest_id
    assert first.strategy_id == strategy.strategy_id
    assert len(first.walk_forward_result_references) == 6  # train and test for all three windows
    assert first.parameter_sensitivity_score == 1
    assert deterministic_hash(strategy) == original
    assert ValidationEngine.SENSITIVITY_MULTIPLIERS == (.9, 1.1)
    assert not hasattr(engine, "optimize") and not hasattr(engine, "select_best")


def test_all_deterministic_acceptance_outcomes():
    strategy, good = candidate(), market()
    base = baseline(strategy, good)
    split = DataSplit.calendar_v1()
    accepted = ValidationEngine(CostModel(0, 0), thresholds=ValidationThresholds(minimum_trades=2))
    assert accepted.validate(strategy, base, good, split=split,
                             data_version="fixture-v1").status is ValidationStatus.ACCEPTED
    rejected_data = market(losing=True)
    rejected_base = baseline(strategy, rejected_data)
    assert accepted.validate(strategy, rejected_base, rejected_data, split=split,
                             data_version="fixture-v1").status is ValidationStatus.REJECTED
    insufficient = ValidationEngine(CostModel(0, 0),
                                    thresholds=ValidationThresholds(minimum_trades=99))
    assert insufficient.validate(strategy, base, good, split=split,
                                 data_version="fixture-v1").status is ValidationStatus.INSUFFICIENT_DATA


def test_insufficient_execution_candles_create_a_report_not_an_exception():
    strategy, data = candidate(), market()
    result = baseline(strategy, data)
    sparse = {"M5": data["M5"][:1], "M15": data["M15"]}
    report = ValidationEngine(CostModel(0, 0)).validate(
        strategy, result, sparse, split=DataSplit.calendar_v1(), data_version="fixture-v1")
    assert report.status is ValidationStatus.INSUFFICIENT_DATA
    assert report.backtest_id == result.backtest_id
    assert report.sample_size == len(sparse["M5"]) + len(sparse["M15"])
    assert report.missing_requirements
    assert "execution candles" in report.reason


@pytest.mark.parametrize("timeframe", ["H1", "D1"])
def test_missing_declared_context_is_deterministic_insufficient_data(timeframe):
    base_strategy, data = candidate(), market()
    strategy = replace(base_strategy, context_timeframes=(timeframe,))
    complete = {**data, timeframe: data["M15"]}
    result = baseline(strategy, complete)
    engine = ValidationEngine(CostModel(0, 0))
    first = engine.validate(strategy, result, data, split=DataSplit.calendar_v1(),
                            data_version="fixture-v1")
    second = engine.validate(strategy, result, data, split=DataSplit.calendar_v1(),
                             data_version="fixture-v1")
    assert first == second
    assert first.status is ValidationStatus.INSUFFICIENT_DATA
    assert f"context timeframe {timeframe}" in first.missing_requirements


def test_validation_requires_backtest_result_and_matching_contract():
    strategy, data = candidate(), market()
    engine = ValidationEngine(CostModel(0, 0))
    with pytest.raises(TypeError, match="BacktestResult"):
        engine.validate(strategy, object(), data, split=DataSplit.calendar_v1(),
                        data_version="fixture-v1")
    with pytest.raises(ValueError, match="data version"):
        engine.validate(strategy, baseline(strategy, data), data,
                        split=DataSplit.calendar_v1(), data_version="different")


def test_validation_memory_is_append_only_and_restart_safe(tmp_path):
    strategy, data = candidate(), market()
    result = baseline(strategy, data)
    report = ValidationEngine(CostModel(0, 0)).validate(
        strategy, result, data, split=DataSplit.calendar_v1(), data_version="fixture-v1")
    memory_a = ResearchMemory(tmp_path)
    memory_a.add_trading_candidate(source())
    memory_a.add_strategy_candidate(strategy)
    memory_a.add_backtest_result(result)
    assert memory_a.add_validation_report(report)
    memory_b = ResearchMemory(tmp_path)
    assert not memory_b.add_validation_report(report)
    assert memory_b.validation_reports()[report.validation_id] == report
    collision = replace(report, reason="different payload")
    with pytest.raises(ValueError, match="collision"):
        memory_b.add_validation_report(collision)


def test_strategy_ranking_components_acceptance_positions_and_no_leakage():
    strategy, data, trading = candidate(), market(), source()
    original = deterministic_hash(strategy)
    report = ValidationEngine(CostModel(0, 0),
        thresholds=ValidationThresholds(minimum_trades=2)).validate(
            strategy, baseline(strategy, data), data, split=DataSplit.calendar_v1(),
            data_version="fixture-v1")
    engine = StrategyRankingEngine()
    first = engine.rank(((report, strategy, trading),))
    second = engine.rank(((report, strategy, trading),))
    assert first == second
    ranking = first[0]
    assert ranking.status is RankingStatus.RANKED and ranking.position == 1
    assert all(0 <= value <= 20 for value in (ranking.scientific_score,
        ranking.statistical_score, ranking.backtest_score, ranking.validation_score,
        ranking.risk_score))
    assert ranking.composite_score == round(sum((ranking.scientific_score,
        ranking.statistical_score, ranking.backtest_score, ranking.validation_score,
        ranking.risk_score)), 8)
    assert ranking.trading_candidate_id == strategy.source_trading_candidate_id
    assert ranking.pattern_effect_id == trading.source_pattern_effect_id
    assert deterministic_hash(strategy) == original
    assert not hasattr(engine, "optimize") and not hasattr(engine, "create_trades")

    trading_b = replace(trading, candidate_id="source-validation-b")
    strategy_b = replace(strategy, strategy_id="strategy-validation-b",
                         source_trading_candidate_id=trading_b.candidate_id)
    report_b = replace(report, validation_id="accepted-validation-b",
                       strategy_id=strategy_b.strategy_id)
    positioned = engine.rank(((report_b, strategy_b, trading_b),
                              (report, strategy, trading)))
    assert [(row.strategy_id, row.position) for row in positioned] == [
        ("strategy-validation", 1), ("strategy-validation-b", 2)]

    rejected_report = replace(report, validation_id="rejected-validation",
                              status=ValidationStatus.REJECTED)
    insufficient_report = replace(report, validation_id="insufficient-validation",
                                  status=ValidationStatus.INSUFFICIENT_DATA)
    audited = engine.rank(((rejected_report, strategy, trading),
                           (insufficient_report, strategy, trading)))
    assert {row.status for row in audited} == {RankingStatus.INSUFFICIENT_DATA,
                                               RankingStatus.REJECTED}
    assert all(row.position is None and row.composite_score == 0 for row in audited)


def test_strategy_ranking_memory_restart_and_collision(tmp_path):
    strategy, data, trading = candidate(), market(), source()
    result = baseline(strategy, data)
    report = ValidationEngine(CostModel(0, 0),
        thresholds=ValidationThresholds(minimum_trades=2)).validate(
            strategy, result, data, split=DataSplit.calendar_v1(), data_version="fixture-v1")
    ranking = StrategyRankingEngine().rank(((report, strategy, trading),))[0]
    memory_a = ResearchMemory(tmp_path)
    memory_a.add_trading_candidate(trading)
    memory_a.add_strategy_candidate(strategy)
    memory_a.add_backtest_result(result)
    memory_a.add_validation_report(report)
    assert memory_a.add_strategy_ranking(ranking)
    memory_b = ResearchMemory(tmp_path)
    assert not memory_b.add_strategy_ranking(ranking)
    assert memory_b.strategy_rankings()[ranking.ranking_id] == ranking
    with pytest.raises(ValueError, match="collision"):
        memory_b.add_strategy_ranking(replace(ranking, composite_score=1.0))
