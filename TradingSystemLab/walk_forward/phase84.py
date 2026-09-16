"""Phase 8.4 causal M1 expanding-window validation.

The Phase 8.3-approved candidates are immutable inputs.  Every train and test
replay starts from a sliced candle frame, which gives it a FLAT strategy and
portfolio state.  There is deliberately no parameter-search interface here.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import shutil
from typing import Any

import pandas as pd

from ..core.unified_metrics import concentration, finite, stats
from ..multitimeframe.phase71 import APPROVED_DATA_ROOT, TRUE_OOS_START, reject_true_oos
from ..multitimeframe.phase73 import hash_tree
from ..optimization.experiment import stable_hash
from ..optimization.phase82 import OUTPUT as PHASE82_ROOT
from ..robustness.phase83 import OUTPUT as PHASE83_ROOT
from ..timeframe_validation.phase81 import INSTRUMENTS, TRADE_COLUMNS, _execute, load_m1_development

OUTPUT = Path("TradingSystemLab/results/timeframe_validation/M1/walk_forward")
STATUS = "PHASE_8_4_M1_WALK_FORWARD_COMPLETE"
FOLDS = (
    ("WF01", "2023-01-01", "2023-07-01", "2023-07-01", "2023-10-01"),
    ("WF02", "2023-01-01", "2023-10-01", "2023-10-01", "2024-01-01"),
    ("WF03", "2023-01-01", "2024-01-01", "2024-01-01", "2024-07-01"),
    ("WF04", "2023-01-01", "2024-07-01", "2024-07-01", "2025-01-01"),
)
PROTECTED = (Path("TradingSystemLab/results/true_oos_validation"),
             Path("TradingSystemLab/results/portfolio_construction"))


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")


def _csv(path: Path, rows: Any) -> None:
    frame = rows if isinstance(rows, pd.DataFrame) else pd.DataFrame(rows)
    frame.map(finite).to_csv(path, index=False, lineterminator="\n", float_format="%.12g", na_rep="")


def metric(frame: pd.DataFrame) -> dict[str, Any]:
    values = frame.net_R.astype(float) if len(frame) else pd.Series(dtype=float)
    result = stats(values)
    return {"trades": result["trades"], "PF": finite(result["PF_R"]),
            "expectancy_R": finite(result["expectancy"]), "net_R": result["net_R"],
            "max_drawdown_R": result["max_DD_R"],
            "recovery_factor": finite(result["recovery_factor"]),
            "win_rate": finite(result["winrate"])}


def reject_forbidden_timestamps(frame: pd.DataFrame) -> None:
    """Fail closed on any candle or trade at the TRUE OOS boundary."""
    if isinstance(frame.index, pd.DatetimeIndex):
        reject_true_oos(frame.index)
    for column in ("entry_time", "exit_time"):
        if column in frame:
            reject_true_oos(pd.to_datetime(frame[column], utc=True))


def validate_fold_causality() -> None:
    previous_test_end = None
    development_end = pd.Timestamp("2025-01-01", tz="UTC")
    for _, train_start, train_end, test_start, test_end in FOLDS:
        points = [pd.Timestamp(x, tz="UTC") for x in (train_start, train_end, test_start, test_end)]
        # An exclusive 2025-01-01 bound identifies the last development slice;
        # it is not itself an observation or permission to read that timestamp.
        if not (points[0] < points[1] == points[2] < points[3]) or points[3] > development_end:
            raise RuntimeError("INVALID_OR_NONCAUSAL_FOLD")
        if previous_test_end is not None and points[2] != previous_test_end:
            raise RuntimeError("NONCONTIGUOUS_TEST_FOLDS")
        previous_test_end = points[3]


def _verify_inputs(phase83_root: Path, phase82_root: Path) -> tuple[dict, dict[str, dict]]:
    path = phase83_root / "manifest.json"
    if not path.is_file():
        raise RuntimeError("PHASE_8_3_ARTIFACTS_MISSING")
    manifest = json.loads(path.read_text(encoding="utf-8"))
    if (manifest.get("phase") != "8.3" or not manifest.get("true_oos_blocked") or
            manifest.get("optimization") is not False):
        raise RuntimeError("PHASE_8_3_PROVENANCE_INVALID")
    registries = {}
    for key in ("T2", "T3"):
        registry_path = phase82_root / key / "candidate_registry.json"
        if not registry_path.is_file() or _sha(registry_path) != manifest.get("candidate_hashes", {}).get(key):
            raise RuntimeError(f"{key}_PHASE_8_3_CANDIDATE_HASH_MISMATCH")
        registry = json.loads(registry_path.read_text(encoding="utf-8"))
        if (registry.get("candidate_id") != f"{key}_M1_candidate_v1" or
                stable_hash(registry.get("parameters", {})) != manifest.get("parameter_hashes", {}).get(key)):
            raise RuntimeError(f"{key}_FROZEN_PARAMETER_HASH_MISMATCH")
        registries[key] = registry
    return manifest, registries


def _slice(frame: pd.DataFrame, start: str, end: str) -> pd.DataFrame:
    start_time, end_time = pd.Timestamp(start, tz="UTC"), pd.Timestamp(end, tz="UTC")
    result = frame.loc[(frame.index >= start_time) & (frame.index < end_time)].copy()
    reject_forbidden_timestamps(result)
    return result


def _replay(key: str, parameters: dict, alias: str, candles: pd.DataFrame,
            fold: str, split: str) -> pd.DataFrame:
    # _execute creates all state locally; a fresh invocation is the FLAT boundary.
    result = _execute(key, parameters, alias, candles)
    result = result.copy()
    result["trade_id"] = [f"{key}-M1-{fold}-{split}-{alias}-{n:06d}" for n in range(1, len(result) + 1)]
    result["fold"] = fold
    result["split"] = split
    reject_forbidden_timestamps(result)
    return result


def _groups(trades: pd.DataFrame, column: str, values: list[Any]) -> list[dict]:
    return [{column: value, **metric(trades.loc[trades[column].eq(value)])} for value in values]


def _run_candidate(key: str, registry: dict, loaded: dict[str, tuple], target: Path) -> dict:
    target.mkdir(parents=True)
    fold_rows, decay_rows, test_parts = [], [], []
    for fold, train_start, train_end, test_start, test_end in FOLDS:
        split_frames = {}
        for split, start, end in (("train", train_start, train_end), ("test", test_start, test_end)):
            parts = []
            for _, alias in INSTRUMENTS:
                source = loaded[alias][0]
                if source is not None:
                    parts.append(_replay(key, registry["parameters"], alias, _slice(source, start, end), fold, split))
            split_frames[split] = pd.concat(parts, ignore_index=True) if parts else pd.DataFrame(
                columns=TRADE_COLUMNS + ["instrument", "strategy", "timeframe", "net_R", "fold", "split"])
            split_frames[split] = split_frames[split].sort_values(["exit_time", "trade_id"], kind="mergesort").reset_index(drop=True)
            row = {"fold": fold, "split": split, "period_start": start, "period_end_exclusive": end,
                   "initial_state": "FLAT", **metric(split_frames[split])}
            fold_rows.append(row)
        train_metric, test_metric = metric(split_frames["train"]), metric(split_frames["test"])
        decay_rows.append({"fold": fold, "train_expectancy_R": train_metric["expectancy_R"],
                           "test_expectancy_R": test_metric["expectancy_R"],
                           "expectancy_decay_R": (test_metric["expectancy_R"] - train_metric["expectancy_R"]
                                                   if None not in (test_metric["expectancy_R"], train_metric["expectancy_R"]) else None),
                           "train_PF": train_metric["PF"], "test_PF": test_metric["PF"]})
        test_parts.append(split_frames["test"])
    trades = pd.concat(test_parts, ignore_index=True).sort_values(["exit_time", "trade_id"], kind="mergesort").reset_index(drop=True)
    _csv(target / "folds.csv", [{"fold": f, "train_start": a, "train_end_exclusive": b,
                                  "test_start": c, "test_end_exclusive": d} for f, a, b, c, d in FOLDS])
    _csv(target / "trades.csv", trades); _csv(target / "fold_report.csv", fold_rows)
    _csv(target / "train_test_decay.csv", decay_rows)
    years = trades.assign(year=pd.to_datetime(trades.exit_time, utc=True).dt.year)
    _csv(target / "yearly_report.csv", _groups(years, "year", [2023, 2024]))
    _csv(target / "instrument_report.csv", _groups(trades, "instrument", [x[0] for x in INSTRUMENTS]))
    _csv(target / "direction_report.csv", _groups(trades, "direction", ["LONG", "SHORT"]))
    conc = concentration(trades.net_R.astype(float))
    _csv(target / "concentration_report.csv", [conc])
    excursion = [{"statistic": name,
                  "MAE_R": finite(trades.MAE_R.astype(float).quantile(q)) if len(trades) else None,
                  "MFE_R": finite(trades.MFE_R.astype(float).quantile(q)) if len(trades) else None}
                 for name, q in (("minimum", 0), ("p25", .25), ("median", .5), ("p75", .75), ("maximum", 1))]
    _csv(target / "mae_mfe_report.csv", excursion)
    loo = [{"excluded_fold": fold, **metric(trades.loc[~trades.fold.eq(fold)])} for fold, *_ in FOLDS]
    _csv(target / "leave_one_fold_out.csv", loo)
    aggregate = metric(trades)
    stable_folds = sum((row["net_R"] > 0) for row in fold_rows if row["split"] == "test")
    payload = {"candidate_id": registry["candidate_id"], "parameter_hash": registry["parameter_hash"],
               "test_folds_positive": stable_folds, "test_folds_total": len(FOLDS), **aggregate}
    _json(target / "metrics.json", payload)
    (target / "final_report.md").write_text(
        f"# {registry['candidate_id']} M1 walk-forward validation\n\n"
        f"Expanding-window test result: {stable_folds}/{len(FOLDS)} folds had positive net R.\n\n"
        "Every fold and split starts FLAT. Parameters are frozen; optimization=false; ranking=false.\n",
        encoding="utf-8")
    return {"strategy": key, **payload}


def run(data_root: Path = APPROVED_DATA_ROOT, output: Path = OUTPUT,
        phase83_root: Path = PHASE83_ROOT, phase82_root: Path = PHASE82_ROOT) -> dict[str, Any]:
    validate_fold_causality()
    output, phase83_root, phase82_root = Path(output), Path(phase83_root), Path(phase82_root)
    manifest83, registries = _verify_inputs(phase83_root, phase82_root)
    protected_before = {str(path): hash_tree(path) for path in (*PROTECTED, phase83_root, phase82_root)}
    loaded = {alias: load_m1_development(Path(data_root), alias) for _, alias in INSTRUMENTS}
    sources = [{"instrument": instrument, "alias": alias,
                "files": [{"name": p.name, "sha256": _sha(p)} for p in loaded[alias][1]]}
               for instrument, alias in INSTRUMENTS]
    if sources != manifest83.get("source_data_hashes"):
        raise RuntimeError("PHASE_8_3_SOURCE_HASH_MISMATCH")
    if output.exists(): shutil.rmtree(output)
    output.mkdir(parents=True)
    summaries = [_run_candidate(key, registries[key], loaded, output / key) for key in ("T2", "T3")]
    _csv(output / "comparison.csv", summaries)
    protected_after = {str(path): hash_tree(path) for path in (*PROTECTED, phase83_root, phase82_root)}
    if protected_before != protected_after:
        raise RuntimeError("PROTECTED_ARTIFACT_MUTATION")
    fold_defs = [{"fold": f, "train": [a, b], "test": [c, d], "end_semantics": "exclusive"}
                 for f, a, b, c, d in FOLDS]
    manifest = {"phase": "8.4", "status": STATUS, "timeframe": "M1",
        "development_period": ["2023-01-01", "2024-12-31"],
        "candidates": [registries[k]["candidate_id"] for k in ("T2", "T3")],
        "instruments": [x[0] for x in INSTRUMENTS], "fold_definitions": fold_defs,
        "phase8_3_candidate_hashes": manifest83["candidate_hashes"],
        "frozen_parameter_hashes": manifest83["parameter_hashes"], "source_data_hashes": sources,
        "protected_artifact_hashes": protected_after, "flat_initialization_per_fold": True,
        "deterministic": True, "optimization": False, "ranking": False, "true_oos_blocked": True}
    _json(output / "manifest.json", manifest)
    lines = ["# Phase 8.4 M1 Walk-Forward Validation", "", "Independent validation; this table is not a ranking.", "",
             "| Candidate | Trades | PF | Expectancy R | Net R | Max DD R | Positive folds |",
             "|---|---:|---:|---:|---:|---:|---:|"]
    for row in summaries:
        lines.append(f"| {row['candidate_id']} | {row['trades']} | {row['PF']} | {row['expectancy_R']} | {row['net_R']} | {row['max_drawdown_R']} | {row['test_folds_positive']}/4 |")
    lines += ["", "Expanding windows, FLAT fold initialization, frozen parameters, and development data only.", "",
              "optimization=false; ranking=false; true_oos_blocked=true; deterministic=true.", "", STATUS, ""]
    (output / "m1_walk_forward_report.md").write_text("\n".join(lines), encoding="utf-8")
    return {"status": STATUS, "candidates": summaries}
