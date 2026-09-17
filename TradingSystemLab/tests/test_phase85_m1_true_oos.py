from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pandas as pd
import pytest

from TradingSystemLab.multitimeframe.phase73 import hash_tree
from TradingSystemLab.optimization.experiment import stable_hash
from TradingSystemLab.true_oos.phase85 import OOS_START, run, validate_true_oos_candles


def _fake_trades(key: str, parameters: dict, alias: str, frame: pd.DataFrame) -> pd.DataFrame:
    times = frame.index[::max(1, len(frame) // 20)][:20]
    gross = [0.8 if n % 3 else -0.3 for n in range(len(times))]
    return pd.DataFrame({"trade_id": [f"{key}-M1-OOS-{alias}-{n:06d}" for n in range(1, len(times) + 1)],
        "entry_time": times, "exit_time": times + pd.Timedelta("1min"), "gross_R": gross,
        "initial_risk_ticks": [100.] * len(times), "net_R": [x - .01 for x in gross],
        "MAE_R": [-.2] * len(times), "MFE_R": [.7] * len(times),
        "instrument": ["USDRUBF" if alias == "Si" else "CNYRUBF"] * len(times),
        "direction": ["LONG" if n % 2 else "SHORT" for n in range(len(times))],
        "strategy": [key] * len(times), "timeframe": ["M1"] * len(times)})


@pytest.fixture
def inputs(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    import TradingSystemLab.true_oos.phase85 as phase85
    root82, root83, root84 = (tmp_path / x for x in ("82", "83", "84"))
    root82.mkdir(); root83.mkdir(); root84.mkdir()
    hashes, parameters = {}, {}
    for key in ("T2", "T3"):
        params = {"sentinel": key}; parameters[key] = stable_hash(params)
        registry = {"candidate_id": f"{key}_M1_candidate_v1", "strategy": key,
                    "timeframe": "M1", "parameters": params, "parameter_hash": parameters[key]}
        folder = root82 / key; folder.mkdir()
        path = folder / "candidate_registry.json"
        path.write_text(json.dumps(registry, sort_keys=True), encoding="utf-8")
        hashes[key] = hashlib.sha256(path.read_bytes()).hexdigest()
    (root83 / "manifest.json").write_text(json.dumps(
        {"phase": "8.3", "candidate_hashes": hashes, "parameter_hashes": parameters}), encoding="utf-8")
    (root84 / "manifest.json").write_text(json.dumps({"phase": "8.4",
        "phase8_3_candidate_hashes": hashes, "frozen_parameter_hashes": parameters}), encoding="utf-8")
    index = pd.date_range("2025-01-01 00:01", periods=400, freq="1min", tz="UTC")
    frames = {alias: pd.DataFrame({"Close": range(len(index))}, index=index)
              for _, alias in phase85.INSTRUMENTS}
    monkeypatch.setattr(phase85, "load_m1_true_oos", lambda root, alias: (frames[alias], []))
    monkeypatch.setattr(phase85, "_execute", _fake_trades)
    return root82, root83, root84, tmp_path / "out"


def test_true_oos_barrier_and_development_rejection() -> None:
    validate_true_oos_candles(pd.DataFrame(index=pd.date_range(OOS_START, periods=2, freq="1min")))
    with pytest.raises(ValueError, match="DEVELOPMENT_DATA_IN_TRUE_OOS"):
        validate_true_oos_candles(pd.DataFrame(index=pd.date_range("2024-12-31 23:59", periods=2,
                                                                   freq="1min", tz="UTC")))


def test_determinism_trade_identity_frozen_inputs_and_protection(inputs) -> None:
    root82, root83, root84, output = inputs
    protected = (hash_tree(root82), hash_tree(root83), hash_tree(root84))
    first = run(output=output, phase82_root=root82, phase83_root=root83, phase84_root=root84)
    hashes = {str(p.relative_to(output)): hashlib.sha256(p.read_bytes()).hexdigest()
              for p in output.rglob("*") if p.is_file()}
    second = run(output=output, phase82_root=root82, phase83_root=root83, phase84_root=root84)
    assert first == second
    assert hashes == {str(p.relative_to(output)): hashlib.sha256(p.read_bytes()).hexdigest()
                      for p in output.rglob("*") if p.is_file()}
    assert protected == (hash_tree(root82), hash_tree(root83), hash_tree(root84))
    manifest = json.loads((output / "manifest.json").read_text())
    assert manifest["optimization"] is manifest["ranking"] is manifest["walk_forward"] is False
    assert manifest["true_oos_blocked"] is False
    for key in ("T2", "T3"):
        trades = pd.read_csv(output / key / "trades.csv")
        assert trades.trade_id.is_unique
        assert (pd.to_datetime(trades.entry_time, utc=True) >= OOS_START).all()
        assert json.loads((output / key / "metrics.json").read_text())["candidate_id"] == f"{key}_M1_candidate_v1"


def test_candidate_hash_tampering_fails_closed(inputs) -> None:
    root82, root83, root84, output = inputs
    with (root82 / "T2" / "candidate_registry.json").open("a") as stream:
        stream.write(" ")
    with pytest.raises(RuntimeError, match="FROZEN_CANDIDATE_HASH_MISMATCH"):
        run(output=output, phase82_root=root82, phase83_root=root83, phase84_root=root84)


def test_no_optimizer_interface() -> None:
    import TradingSystemLab.true_oos.phase85 as phase85
    assert not hasattr(phase85, "optimize")
    source = Path(phase85.__file__).read_text(encoding="utf-8")
    assert "parameter_space" not in source and "RANGES" not in source
