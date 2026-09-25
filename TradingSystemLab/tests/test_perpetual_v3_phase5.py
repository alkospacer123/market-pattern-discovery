import json
from pathlib import Path

import pandas as pd
import pytest

from TradingSystemLab.true_oos.perpetual_v3_phase5 import (
    BOOTSTRAP_ITERATIONS, BOOTSTRAP_SEED, EXPECTED_IDENTITIES, FROZEN_TICK_SIZE,
    INSTRUMENTS, STUDIES, TRUE_OOS_START, classify, four_bar_context,
    load_frozen_registry, load_true_oos,
)

REGISTRY = Path("TradingSystemLab/results/perpetual_v3/phase3_candidate_freeze/candidate_registry.json")


def test_frozen_contract():
    assert STUDIES == (("T2", "M30"), ("T2", "H1"), ("T3", "M30"), ("T3", "H1"))
    assert INSTRUMENTS == ("USDRUBF", "CNYRUBF", "GLDRUBF", "IMOEXF")
    assert TRUE_OOS_START == pd.Timestamp("2025-01-01", tz="Europe/Moscow")
    assert (BOOTSTRAP_ITERATIONS, BOOTSTRAP_SEED, FROZEN_TICK_SIZE) == (10_000, 5_102_025, .001)

@pytest.mark.parametrize("mutation", ["candidate_id", "parameter_hash", "parameters"])
def test_registry_mutations_fail_closed(tmp_path, mutation):
    data = json.loads(REGISTRY.read_text())
    data["candidates"][0][mutation] = "mutated" if mutation != "parameters" else {"ema_fast": 999}
    path = tmp_path / "registry.json"; path.write_text(json.dumps(data))
    with pytest.raises(RuntimeError): load_frozen_registry(path)


def test_context_is_cold_complete_local_day_blocks():
    idx = pd.date_range("2025-01-01 10:30", periods=5, freq="30min", tz="Europe/Moscow")
    frame = pd.DataFrame({"Open":range(5), "High":range(1,6), "Low":range(5), "Close":range(1,6)}, index=idx)
    context = four_bar_context(frame)
    assert len(context) == 1 and context.index[0] == idx[3] and context.index.min() >= TRUE_OOS_START


def test_exact_classification_boundaries_and_gates():
    good = {"total_trades":50, "expectancy":.1}
    assert classify(good, .95, 5, 3, True, True, .1) == "PASS"
    assert classify({**good,"total_trades":49}, .95, 5, 3, True, True, .1) == "BORDERLINE"
    assert classify({**good,"expectancy":0}, .99, 5, 5, True, True, .1) == "FAIL"
    assert classify(good, .50, 5, 5, True, True, .1) == "FAIL"
    for args in ((.94,5,5,True,True,.1),(.99,5,2,True,True,.1),(.99,5,5,False,True,.1),(.99,5,5,True,False,.1),(.99,5,5,True,True,0)):
        assert classify(good, *args) == "BORDERLINE"


def test_manifests_enforce_lifecycle_and_provenance():
    root = Path("TradingSystemLab/results/perpetual_v3/true_oos")
    summary = json.loads((root/"summary/manifest.json").read_text())
    assert summary["development_rows_admitted"] == 0 and summary["cold_start"] and summary["start_state"] == "FLAT"
    assert summary["C1_only"] and not summary["optimization"] and not summary["ranking"] and not summary["candidate_replacement"]
    assert summary["bootstrap"] == {"diagnostic_only":True,"iterations":10_000,"seed":5_102_025}
    for strategy, timeframe in STUDIES:
        study = json.loads((root/strategy/timeframe/"manifest.json").read_text())
        assert study["walk_forward_reference_commit"] == "d5aa616186c2750d5f0b0b9c60eddbf5d096c98f"
        assert study["candidate_id"] == EXPECTED_IDENTITIES[(strategy,timeframe)][0]
        assert study["development_rows_admitted"] == 0 and not study["development_state_reused"]


def test_trade_ids_and_oos_boundary():
    root = Path("TradingSystemLab/results/perpetual_v3/true_oos")
    for strategy, timeframe in STUDIES:
        trades = pd.read_csv(root/strategy/timeframe/"trades.csv")
        assert trades.trade_id.is_unique
        assert pd.to_datetime(trades.entry_time, utc=True).ge(TRUE_OOS_START.tz_convert("UTC")).all()
        assert pd.to_datetime(trades.exit_time, utc=True).ge(TRUE_OOS_START.tz_convert("UTC")).all()
