from datetime import datetime, timedelta, timezone

import pandas as pd
import pytest

from market_pattern_discovery.backtest.phase6b import metrics
from market_pattern_discovery.contracts import CandleContract, ManifestContract, canonical_json, deterministic_hash
from market_pattern_discovery.experiments import ExecutionContext, ExperimentRunner, ExperimentSpec
from market_pattern_discovery.orchestration import CycleManifest, CycleRunner
from market_pattern_discovery.research import ResearchMemory


def _summary(path, strategy="RL-01"):
    pd.DataFrame([{"strategy_id": strategy, "instrument": "CNYRUBF",
        "exit_configuration": "TIME_15", "friction_scenario": "BASE",
        "profit_factor_ATR": 1.2, "expectancy_ATR": .1, "recovery_factor_ATR": .5}]).to_csv(
            path / "strategy_summary.csv", index=False)


def test_contract_validation_and_hashing_are_deterministic():
    now = datetime(2026, 1, 1, tzinfo=timezone.utc)
    candle = CandleContract("CNYRUBF", "M1", now, now + timedelta(minutes=1), 10, 11, 9, 10.5, 3)
    assert deterministic_hash({"b": 2, "a": candle}) == deterministic_hash({"a": candle, "b": 2})
    assert canonical_json({"b": 2, "a": 1}) == '{"a":1,"b":2}'
    assert ManifestContract("run", "3.5", {"x": 1}).manifest_id
    with pytest.raises(ValueError):
        CandleContract("CNYRUBF", "M1", now, now, 10, 11, 9, 10, 0)


def test_experiment_calls_v3_once_and_persists_adapter(tmp_path):
    calls = []
    memory = ResearchMemory(tmp_path / "memory")

    def v3(data_root, output):
        calls.append((data_root, output))
        _summary(output)
        return {"status": "PASS", "source_modified": False}

    spec = ExperimentSpec("baseline", tmp_path / "data", tmp_path / "output", 4)
    result = ExperimentRunner(memory, v3).run(spec)
    assert len(calls) == 1 and len(result.candidates) == 1
    assert memory.experiments()[0]["experiment_id"] == spec.experiment_id
    assert set(memory.candidates()) == {result.candidates[0].candidate_id}


def test_legacy_two_argument_v3_adapter_is_unchanged(tmp_path):
    calls = []

    def v3(data_root, output):
        calls.append((data_root, output))
        return {"status": "PASS"}

    spec = ExperimentSpec("legacy", tmp_path / "data", tmp_path / "output")
    ExperimentRunner(pipeline=v3).run(spec)
    assert calls == [(spec.data_root, spec.output_directory)]


@pytest.mark.parametrize(("instrument", "canonical"), [
    ("CNY", "CNYRUBF"), ("Si", "USDRUBF"),
])
@pytest.mark.parametrize("timeframe", ["M1", "M5"])
def test_scoped_execution_context_reaches_v3(tmp_path, instrument, canonical, timeframe):
    calls = []

    def v3(data_root, output, context):
        calls.append(context)
        return {"status": "PASS", "timeframe": context.timeframe}

    spec = ExperimentSpec(f"{instrument}-{timeframe}", tmp_path / "data", tmp_path / "output",
                          metadata={"instrument": instrument, "timeframe": timeframe})
    result = ExperimentRunner(pipeline=v3).run(spec)
    assert calls == [ExecutionContext(instrument, timeframe)]
    assert calls[0].instruments == (canonical,)
    assert result.timeframe == timeframe


@pytest.mark.parametrize("timeframe", ["M1", "M5"])
def test_experiment_manifest_timeframe_is_persisted_on_candidate(tmp_path, timeframe):
    memory = ResearchMemory(tmp_path / "memory")

    def v3(_, output):
        _summary(output)
        return {"status": "PASS", "timeframe": timeframe}

    result = ExperimentRunner(memory, v3).run(
        ExperimentSpec(f"{timeframe}-experiment", tmp_path / "data", tmp_path / "output")
    )

    assert result.timeframe == timeframe
    assert result.candidates[0].timeframe == timeframe
    assert next(iter(memory.candidates().values())).timeframe == timeframe


def test_cycle_order_failure_isolation_and_candidate_collection(tmp_path):
    def v3(_, output):
        if output.name == "bad":
            raise RuntimeError("expected failure")
        _summary(output, output.name)
        return {"status": "PASS"}

    specs = (ExperimentSpec("z", tmp_path, tmp_path / "good", 2),
             ExperimentSpec("a", tmp_path, tmp_path / "bad", 2))
    manifest = CycleManifest(2, specs)
    report = CycleRunner(ExperimentRunner(pipeline=v3)).run(manifest)
    assert [spec.name for spec in manifest.experiments] == ["a", "z"]
    assert len(report.results) == 1 and len(report.failures) == 1 and len(report.candidates) == 1
    assert manifest.cycle_id == CycleManifest(2, tuple(reversed(specs))).cycle_id


def test_v3_metrics_equivalence_is_unchanged():
    ledger = pd.DataFrame([
        {"strategy_id": "S", "instrument": "I", "exit_configuration": "TIME_15",
         "friction_scenario": "BASE", "pnl_atr": .5, "pnl_R": float("nan"),
         "net_pnl_price": 2., "gross_pnl_price": 3., "bars_held": 4},
        {"strategy_id": "S", "instrument": "I", "exit_configuration": "TIME_15",
         "friction_scenario": "BASE", "pnl_atr": -.25, "pnl_R": float("nan"),
         "net_pnl_price": -1., "gross_pnl_price": -1., "bars_held": 2},
    ])
    before = metrics(ledger)
    # V3.5 contracts only serialize V3's computed values; they never invoke metric logic.
    payload = ManifestContract("v3-result", "3.5", {"metrics": before.to_dict("records")})
    after = metrics(ledger)
    pd.testing.assert_frame_equal(before, after)
    assert payload.payload["metrics"][0]["profit_factor_ATR"] == before.profit_factor_ATR.iloc[0]
