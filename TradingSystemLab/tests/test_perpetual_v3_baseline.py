import hashlib, json
from pathlib import Path
import pandas as pd

from TradingSystemLab.perpetual_v3_baseline import *


def test_frozen_contract():
    assert INSTRUMENTS == ("USDRUBF", "CNYRUBF", "GLDRUBF", "IMOEXF")
    assert TIMEFRAMES == ("M30", "H1") and STRATEGIES == ("T2", "T3")
    assert len(RUNS) == 16 and len(set(RUNS)) == 16
    assert BASELINE_PARAMETERS["T2"]["max_initial_stop_atr"] == 3.0
    assert BASELINE_PARAMETERS["T3"]["ema_period"] == 100
    assert COST_MODEL == {"name": "C1", "ticks_per_side": 1, "round_trip_ticks": 2, "additional_slippage_ticks": 0}
    assert FROZEN_TICK_SIZE == .001
    verify_strategy_identity()


def test_development_filter_and_natural_starts():
    for instrument in INSTRUMENTS:
        frame, _ = load_development(DATA_ROOT, instrument, "H1")
        assert frame.index.tz is not None and str(frame.index.tz) == "Europe/Moscow"
        assert frame.index.max() < TRUE_OOS_START
        assert frame.index.is_monotonic_increasing and not frame.index.has_duplicates
        if instrument in ("GLDRUBF", "IMOEXF"):
            assert frame.index.min() > DEVELOPMENT_START


def test_context_is_complete_separate_and_day_bounded():
    index = pd.DatetimeIndex(["2024-01-01 10:00", "2024-01-01 11:00", "2024-01-01 12:00",
        "2024-01-02 10:00", "2024-01-02 11:00", "2024-01-02 12:00", "2024-01-02 13:00", "2024-01-02 14:00"], tz="Europe/Moscow")
    frame = pd.DataFrame({"Open": range(8), "High": range(1,9), "Low": range(8), "Close": range(1,9)}, index=index)
    context = four_bar_context(frame)
    assert context is not frame and len(context) == 1
    assert context.index[0] == index[6]


def test_generated_tree_has_no_selection_or_ranking():
    root = OUTPUT_ROOT
    matrix = pd.read_csv(root / "summary/baseline_matrix.csv")
    assert len(matrix) == 16
    assert not ({"rank", "score", "winner", "best", "recommended_candidate"} & set(matrix.columns))
    manifest = json.loads((root / "summary/manifest.json").read_text())
    assert manifest["true_oos_status"] == "BLOCKED_NOT_READ_NOT_EXECUTED"
    assert not manifest["optimization"] and not manifest["ranking"] and not manifest["selection"]


def test_deterministic_artifact_tree(tmp_path):
    # The production validation runs twice; this test byte-hashes the committed tree.
    files = sorted(p for p in OUTPUT_ROOT.rglob("*") if p.is_file())
    first = [(p.relative_to(OUTPUT_ROOT).as_posix(), hashlib.sha256(p.read_bytes()).hexdigest()) for p in files]
    second = [(p.relative_to(OUTPUT_ROOT).as_posix(), hashlib.sha256(p.read_bytes()).hexdigest()) for p in files]
    assert first == second and len(first) == 16 * 8 + 6
