"""Regression contract for the locked standalone H4 TRUE OOS stage."""
from __future__ import annotations

import copy
import inspect
from pathlib import Path

import pandas as pd
import pytest

from TradingSystemLab.optimization.experiment import stable_hash
from TradingSystemLab.true_oos import h4


def _h1(start: str = "2025-01-01 10:00", periods: int = 240) -> pd.DataFrame:
    index = pd.date_range(start, periods=periods, freq="1h", tz="Europe/Moscow")
    close = pd.Series(range(periods), index=index, dtype=float) / 100 + 10
    return pd.DataFrame({"Open": close, "High": close + .1, "Low": close - .1,
                         "Close": close + .02, "Volume": 1.0}, index=index)


def test_standalone_method_and_frozen_identity():
    source = Path(h4.__file__).read_text(encoding="utf-8")
    assert "true_oos.m30" not in source and "true_oos.m15" not in source and "true_oos.m5" not in source
    assert '"methodological_source": "H1_PHASE_5"' in source
    registry = h4.load_frozen_registry()
    assert {key: row["candidate_id"] for key, row in registry.items()} == h4.EVALUATED_CANDIDATES
    assert {key: row["configuration_id"] for key, row in registry.items()} == {
        key: value[1] for key, value in h4.EXPECTED_REGISTRY.items()}
    assert all(stable_hash(row["parameters"]) == row["parameter_hash"] for row in registry.values())
    with pytest.raises(TypeError, match="frozen"):
        registry["T2"]["parameters"]["ema_fast"] = 1


def test_boundary_file_discovery_and_content_barriers(tmp_path):
    assert all("_H1_2025_" in p.name or "_H1_2026_" in p.name
               for p in h4.discover_true_oos_files(Path("/workspace/market-pattern-data"), "Si"))
    with pytest.raises(RuntimeError, match="PRE_BOUNDARY"):
        h4.validate_true_oos_candles(_h1("2024-12-31 23:00", 2))
    bad = pd.concat([_h1("2024-12-31 23:00", 1), _h1(periods=2)])
    with pytest.raises(RuntimeError, match="PRE_BOUNDARY"):
        h4.validate_true_oos_candles(bad)


def test_h1_to_h4_and_d1_are_causal():
    raw = _h1(periods=240)
    execution, context = h4.causal_h4(raw), h4.causal_d1(raw)
    assert execution.index.is_monotonic_increasing and context.index.is_monotonic_increasing
    assert execution.index.isin(raw.index).all() and context.index.isin(raw.index).all()
    assert execution.index.min() >= raw.index.min() and context.index.min() >= raw.index.min()


def test_adapter_only_overrides_admission():
    assert {name for name in h4._OOST2.__dict__ if not name.startswith("__")} == {"_validate"}


def test_execution_only_and_phase5_constants():
    h4._assert_execution_only()
    assert h4.BOOTSTRAP_SEED == 5102025 and h4.BOOTSTRAP_ITERATIONS == 10_000
    assert "parameters" not in inspect.signature(h4.run).parameters
    assert not hasattr(h4, "optimize") and not hasattr(h4, "rank") and not hasattr(h4, "select")
    assert h4.PRE_OOS_VERDICTS == {"T2": "WALK_FORWARD_BORDERLINE", "T3": "WALK_FORWARD_BORDERLINE"}
    assert h4.WALK_FORWARD_COMMIT == "81a44b82a9bbcaa18ddb42f8b0cb9f9237c03022"


def test_exact_phase5_classification():
    base = {"trades": 50, "expectancy_R": .1}
    quarters = [{"trades": 1, "expectancy_R": .1}] * 3 + [{"trades": 1, "expectancy_R": -.1}] * 2
    slices = [{"trades": 1, "expectancy_R": 0}]
    boot, conc = {"probability_mean_R_gt_0": .95}, {"net_R_without_top5": .01}
    assert h4.classify(base, quarters, slices, slices, boot, conc) == "PASS"
    assert h4.classify({**base, "expectancy_R": 0}, quarters, slices, slices, boot, conc) == "FAIL"
    assert h4.classify(base, quarters, slices, slices, {"probability_mean_R_gt_0": .5}, conc) == "FAIL"
    assert h4.classify(base, quarters, slices, slices, {"probability_mean_R_gt_0": .94}, conc) == "BORDERLINE"
    assert h4.classify(base, quarters + [{"trades": 0, "expectancy_R": None}], slices, slices, boot, conc) == "PASS"
    assert h4.classify(base, quarters, [{"trades": 1, "expectancy_R": -.1}], slices, boot, conc) == "BORDERLINE"
    assert h4.classify(base, quarters, slices, [{"trades": 1, "expectancy_R": -.1}], boot, conc) == "BORDERLINE"
    assert h4.classify(base, quarters, slices, slices, boot, {"net_R_without_top5": 0}) == "BORDERLINE"


def test_mutations_fail_closed():
    registry = h4.load_frozen_registry()["T2"]
    changed = copy.deepcopy(registry); changed["parameters"] = dict(registry["parameters"])
    changed["parameters"]["ema_fast"] += 1
    with pytest.raises(RuntimeError, match="PARAMETER_HASH"):
        h4.execute_candidate("T2", changed, {"Si": _h1(), "CNY": _h1()})
