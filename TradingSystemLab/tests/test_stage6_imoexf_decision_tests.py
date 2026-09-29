import importlib.util
import shutil
from pathlib import Path

import pandas as pd
import pytest

HERE = Path(__file__).resolve().parents[1] / "results/post_v3_analysis/stage6_imoexf_decision_tests"
SPEC = importlib.util.spec_from_file_location("imoexf_decision", HERE / "run_imoexf_decision_tests.py")
mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(mod)


def registry(starts=None):
    starts = starts or {"CNYRUBF": "2024-01-01", "GLDRUBF": "2024-03-01", "IMOEXF": "2024-05-01"}
    return pd.DataFrame([{"lifecycle": life, "instrument": symbol, "start_timestamp": start,
                          "end_timestamp": "2024-11-30 23:59:59"}
                         for life in mod.LIFECYCLES for symbol, start in starts.items()])


def event_frame():
    rows = []
    values = [1.0, -0.5, 0.0, 2.0, -1.0, 0.5, 1.5]
    n = 0
    for life in mod.LIFECYCLES:
        for symbol in mod.SYMBOLS:
            for month, value in zip(range(5, 12), values):
                n += 1
                rows.append({"generation": "v3_perpetual", "lifecycle": life, "fold_id": "",
                             "strategy": "T3", "timeframe": "H1", "instrument": symbol,
                             "direction": "LONG", "entry_time": f"2024-{month:02d}-02T10:00:00Z",
                             "entry_price": 100.0, "exit_time": f"2024-{month:02d}-03T10:00:00Z",
                             "net_R_C1": value, "cost_R": 0.01, "trade_id": f"T{n}"})
    return pd.DataFrame(rows)


def canonical_frame(events):
    frame = events[events.instrument == "IMOEXF"].copy()
    # Keep paths identical so the reconciliation artifact is valid but empty.
    return frame


def test_monthly_pf_edge_contract():
    assert mod.profit_factor(pd.Series([], dtype=float)) is None
    assert mod.profit_factor(pd.Series([1.0])) is None
    assert mod.profit_factor(pd.Series([2.0, -1.0])) == 2.0
    assert mod.profit_factor(pd.Series([2.0, 1.0])) is None
    assert mod.profit_factor(pd.Series([-2.0, -1.0])) == 0.0


def test_availability_zero_month_and_complete_rolling_window():
    reg = registry({"IMOEXF": "2024-05-01"})
    events = event_frame()
    events = events[(events.lifecycle == "baseline") & (events.instrument == "IMOEXF")]
    # Remove June: it remains an available zero-trade month.
    events = events[pd.to_datetime(events.exit_time, utc=True).dt.month != 6]
    monthly = mod.monthly_frame(events, "net_R_C1", symbols=("IMOEXF",), registry=reg)
    assert monthly.month.iloc[0] == 5                 # no pre-availability rows
    assert monthly.loc[monthly.month == 6, "trades"].item() == 0
    assert monthly.loc[monthly.month == 6, "net_R"].item() == 0
    assert monthly.rolling_6_month_net_R.iloc[:5].isna().all()
    assert monthly.rolling_6_month_net_R.iloc[5] == pytest.approx(monthly.net_R.iloc[:6].sum())


def test_basket_component_availability_is_reconstructed():
    events = event_frame()
    events = events[(events.lifecycle == "baseline") & events.instrument.isin(mod.SYMBOLS[:2])]
    monthly = mod.monthly_frame(events, "net_R_C1", symbols=mod.SYMBOLS[:2], registry=registry())
    assert monthly.month.iloc[0] == 1
    assert monthly.available_instruments.iloc[0] == "CNYRUBF"
    assert monthly.loc[monthly.month == 3, "available_instruments"].item() == "CNYRUBF+GLDRUBF"


@pytest.fixture()
def built(tmp_path):
    events = event_frame(); canonical = canonical_frame(events)
    mod.build_outputs(events, canonical, tmp_path, registry())
    return tmp_path, events, canonical


def audit(built):
    path, events, canonical = built
    return mod.independent_audit(path, events, canonical, registry())


def mutate_csv(path, mask, column, value):
    frame = pd.read_csv(path)
    frame.loc[mask(frame), column] = value
    frame.to_csv(path, index=False, lineterminator="\n")


def test_cost_sensitivity_keeps_trade_paths_and_headlines(built):
    path, events, _ = built
    costs = pd.read_csv(path / "cost_sensitivity_summary.csv")
    assert all(costs.groupby(["lifecycle", "basket_or_symbol"]).trades.nunique() == 1)
    base = costs[costs.cost_multiplier == 1.0]
    for row in base.itertuples():
        expected = events[(events.lifecycle == row.lifecycle) & events.instrument.isin(mod.BASKETS[row.basket_or_symbol])]
        assert row.trades == len(expected)
        assert row.net_R == pytest.approx(expected.net_R_C1.sum())


@pytest.mark.parametrize("kind", ["pf", "availability", "rolling"])
def test_monthly_semantic_mutations_are_detected(built, kind):
    path, _, _ = built
    target = path / "trail1_monthly_detail.csv"
    frame = pd.read_csv(target)
    if kind == "pf":
        index = frame[frame.trades == 1].index[0]
        frame.loc[index, "PF"] = 0
    elif kind == "availability":
        row = frame[(frame.lifecycle == "baseline") & (frame.basket_or_symbol == "IMOEXF")].iloc[0].copy()
        row["year"], row["month"], row["net_R"], row["trades"] = 2024, 4, 0, 0
        frame = pd.concat([frame, row.to_frame().T], ignore_index=True)
    else:
        index = frame[(frame.lifecycle == "baseline") & (frame.basket_or_symbol == "IMOEXF")].index[0]
        frame.loc[index, "rolling_6_month_net_R"] = frame.loc[index, "net_R"]
    frame.to_csv(target, index=False, lineterminator="\n")
    result = audit(built)
    assert result["status"] == "POST_V3_STAGE6_IMOEXF_DECISION_TESTS_CORRECTION_AUDIT_FAILED"
    assert result["checks"]["monthly_detail_rebuilt"] == "FAIL"


def test_production_decision_sha_is_frozen():
    assert mod.sha(mod.STAGE6 / "production_assembly_decision.csv") == mod.DECISION_SHA


def test_headline_frozen_trail1_artifact_values():
    summary = pd.read_csv(HERE / "audit_results/trail1_basket_summary.csv")
    expected = {
        "baseline": (90, 44.6404790228, 117, 57.6710272512),
        "walk_forward": (35, 25.6051934123, 49, 32.9682622741),
        "historical_true_oos": (90, 51.8803560467, 140, 65.067298267),
    }
    for life, (t2, r2, t3, r3) in expected.items():
        rows = summary[summary.lifecycle == life].set_index("basket_or_symbol")
        assert (rows.loc["CNYRUBF+GLDRUBF", "trades"], rows.loc["CNYRUBF+GLDRUBF+IMOEXF", "trades"]) == (t2, t3)
        assert rows.loc["CNYRUBF+GLDRUBF", "net_R"] == pytest.approx(r2)
        assert rows.loc["CNYRUBF+GLDRUBF+IMOEXF", "net_R"] == pytest.approx(r3)
