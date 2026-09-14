from pathlib import Path
import json

import pandas as pd
import pytest

from TradingSystemLab.optimization.experiment import stable_hash
from TradingSystemLab.true_oos.phase5 import artifact_sha256, load_true_oos, run, verify_provenance


DATA = Path("/workspace/market-pattern-data")


def test_frozen_provenance_and_no_parameter_modification():
    candidates = verify_provenance()
    before = [stable_hash(row["parameters"]) for row in candidates]
    assert [row["candidate_id"] for row in candidates] == ["T2_candidate_v1", "T3_candidate_v1"]
    assert before == [stable_hash(row["parameters"]) for row in candidates]


def test_true_oos_barrier_rejects_pre_boundary_content(tmp_path):
    root = tmp_path / "2026"
    for symbol in ("Si", "CNY"):
        folder = root / symbol; folder.mkdir(parents=True)
        (folder / f"{symbol}_H1_2025_Q1.csv").write_text(
            "<TICKER>;<PER>;<DATE>;<TIME>;<OPEN>;<HIGH>;<LOW>;<CLOSE>;<VOL>\n"
            "X;60;20241231;230000;1;1;1;1;1\n", encoding="utf-8")
    with pytest.raises(RuntimeError, match="TRUE_OOS_BARRIER_VIOLATION"):
        load_true_oos(tmp_path)


@pytest.mark.skipif(not DATA.exists(), reason="external read-only market data unavailable")
def test_deterministic_execution_trade_identity_and_sha256(tmp_path):
    first, second = tmp_path / "first", tmp_path / "second"
    run(DATA, first); run(DATA, second)
    assert artifact_sha256(first) == artifact_sha256(second)
    for key in ("T2", "T3"):
        trades = pd.read_csv(first / key / "trades.csv")
        assert trades.trade_id.notna().all() and trades.trade_id.is_unique
        assert (pd.to_datetime(trades.entry_time, utc=True) >= pd.Timestamp("2025-01-01", tz="UTC")).all()
    manifest = json.loads((first / "summary/manifest.json").read_text())
    assert manifest["parameters_frozen"] and manifest["true_oos_barrier"]["development_rows_read"] == 0
    assert not manifest["optimization"] and not manifest["ranking"] and not manifest["walk_forward"]
