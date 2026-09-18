"""Causal M30 expanding-window validation of the frozen T2/T3 candidates.

This phase has no search surface.  Train replays are descriptive; every test
replay is independently initialized FLAT and owns entries in its half-open
calendar window.  Only explicitly frozen 2023/2024 source names are opened.
"""
from __future__ import annotations

from dataclasses import replace
import hashlib
import json
from pathlib import Path
import shutil
from typing import Any

import pandas as pd

from ..core.backtester import Backtester
from ..core.instrument_specs import get_instrument_spec
from ..core.portfolio import FixedRiskPortfolio
from ..core.unified_metrics import finite, stats
from ..multitimeframe.phase71 import (APPROVED_DATA_ROOT, COST_TICKS_PER_SIDE,
    STRATEGY_FILES, STRATEGY_SHA256, TRUE_OOS_START, verify_frozen_strategies)
from ..multitimeframe.phase73 import hash_tree
from ..optimization.experiment import stable_hash
from ..optimization.phase32 import PARAMETERS, _normalize_backtester
from ..strategies.trend.T2_Trend_Pullback import T2TrendPullback
from ..strategies.trend.T3_MTF_Trend import T3MTFTrend
from ..timeframe_validation.m30_baseline import (INSTRUMENTS, TRADE_COLUMNS,
    causal_four_m30_context, load_m30_development)

OUTPUT = Path("TradingSystemLab/results/walk_forward/M30")
BASELINE = Path("TradingSystemLab/results/timeframe_validation/M30")
OPTIMIZATION = Path("TradingSystemLab/results/timeframe_optimization/M30")
ROBUSTNESS = Path("TradingSystemLab/results/timeframe_analysis/M30_ROBUSTNESS")
STATUS = "PHASE_M30_WALK_FORWARD_COMPLETE"
INITIAL_TRAIN_MONTHS, TEST_MONTHS, STEP_MONTHS = 12, 3, 3
DEVELOPMENT_PERIOD = ["2023-01-01", "2024-12-31"]
EXPECTED = {
    "T2": ("T2_M30_candidate_v1", "T2-M30-0008-2b0494cdd24b", "2b0494cdd24bfbfa8ce7d657d6f83d1408f07b9f565d38d093dec5b4856e3c00"),
    "T3": ("T3_M30_candidate_v1", "T3-M30-0020-816e9e819790", "816e9e819790e1523aa5408bc1437119fae03f840c9e672c74f9974983e429c3"),
}
_FOUR_M30_CONTEXT_CACHE: dict[int, pd.DataFrame] = {}
_T2_INDICATOR_CACHE: dict[tuple[int, str], pd.DataFrame] = {}
PROTECTED = (BASELINE, OPTIMIZATION, ROBUSTNESS,
    Path("TradingSystemLab/results/T3_walk_forward"),
    Path("TradingSystemLab/results/robustness_validation"),
    Path("TradingSystemLab/results/multitimeframe_research"),
    Path("TradingSystemLab/results/timeframe_validation/M1"),
    Path("TradingSystemLab/results/timeframe_validation/M5"),
    Path("TradingSystemLab/results/timeframe_validation/M15"),
    Path("TradingSystemLab/results/timeframe_analysis/M5_ROBUSTNESS"),
    Path("TradingSystemLab/results/timeframe_analysis/M15_ROBUSTNESS"),
    Path("TradingSystemLab/results/walk_forward/M5"),
    Path("TradingSystemLab/results/walk_forward/M15"),
    Path("TradingSystemLab/results/true_oos_validation/M5"),
    Path("TradingSystemLab/results/true_oos_validation/M5_EXPERIMENTAL_EMA50_NORMAL"))


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")


def _csv(path: Path, value: Any) -> None:
    frame = value if isinstance(value, pd.DataFrame) else pd.DataFrame(value)
    frame.map(finite).to_csv(path, index=False, lineterminator="\n", float_format="%.12g", na_rep="")


def reject_true_oos(values: Any) -> None:
    stamps = pd.DatetimeIndex(pd.to_datetime(values, utc=True))
    if len(stamps) and (stamps >= TRUE_OOS_START.tz_convert("UTC")).any():
        raise ValueError("M30_TRUE_OOS_ACCESS_REJECTED")


def generate_folds(common_start: pd.Timestamp, coverage_end_exclusive: pd.Timestamp) -> list[dict[str, Any]]:
    """Apply the H1 12/3/3 MonthBegin scheduler; reject partial windows."""
    common_start = pd.Timestamp(common_start)
    coverage_end_exclusive = pd.Timestamp(coverage_end_exclusive)
    reject_true_oos([common_start])
    if coverage_end_exclusive > TRUE_OOS_START:
        raise ValueError("M30_FOLD_TOUCHES_TRUE_OOS")
    threshold = common_start + pd.DateOffset(months=INITIAL_TRAIN_MONTHS)
    test_start = pd.offsets.MonthBegin().rollforward(threshold.normalize())
    folds = []
    while test_start + pd.DateOffset(months=TEST_MONTHS) <= coverage_end_exclusive:
        test_end = test_start + pd.DateOffset(months=TEST_MONTHS)
        folds.append({"fold_id": f"WF{len(folds)+1:02d}", "train_start": common_start,
            "train_end": test_start, "test_start": test_start, "test_end": test_end,
            "initial_state": "FLAT", "status": "COMPLETE"})
        test_start += pd.DateOffset(months=STEP_MONTHS)
    if any(a["test_end"] > b["test_start"] for a, b in zip(folds, folds[1:])):
        raise RuntimeError("M30_OVERLAPPING_FOLDS")
    return folds


class T2WalkForwardAdapter(T2TrendPullback):
    """Boundary gate around the frozen state machine without changing its code."""
    def __init__(self, parameters: Any, entry_start: pd.Timestamp, entry_end: pd.Timestamp):
        super().__init__(parameters)
        self.entry_start, self.entry_end = entry_start, entry_end

    def calculate_indicators(self, candles: pd.DataFrame) -> pd.DataFrame:
        # Calculate on historical data first, then begin iteration with fresh
        # local state at entry_start. Thus history warms indicators only.
        key = (id(candles), stable_hash(self.frozen_parameters()))
        indicators = _T2_INDICATOR_CACHE.get(key)
        if indicators is None:
            indicators = super().calculate_indicators(candles)
            _T2_INDICATOR_CACHE[key] = indicators
        return indicators.loc[indicators.index >= self.entry_start]

    def is_pullback(self, bar: pd.Series, direction: str) -> bool:
        return bool(bar.name < self.entry_end and super().is_pullback(bar, direction))

    def is_confirmation(self, bar: pd.Series, previous: pd.Series, direction: str) -> bool:
        return bool(bar.name < self.entry_end and super().is_confirmation(bar, previous, direction))


def _canonical_sources(rows: list[dict]) -> list[dict]:
    seen = {}
    for row in rows:
        alias = row["alias"]
        files = row.get("files") or [{"name": x["name"], "sha256": x["sha256"]} for x in rows if x["alias"] == alias]
        item = {"instrument": row["instrument"], "alias": alias, "files": files}
        if alias in seen and seen[alias] != item:
            raise RuntimeError("M30_SOURCE_SNAPSHOT_INTERNALLY_INCONSISTENT")
        seen[alias] = item
    return [seen[alias] for _, alias in INSTRUMENTS]


def validate_prerequisites(baseline: Path = BASELINE, optimization: Path = OPTIMIZATION,
                           robustness: Path = ROBUSTNESS) -> tuple[dict, dict, dict, dict]:
    manifests = [json.loads((root / "manifest.json").read_text(encoding="utf-8"))
                 for root in (baseline, optimization, robustness)]
    expected = (("M30_BASELINE", "PHASE_M30_BASELINE_COMPLETE"),
                ("M30_OPTIMIZATION", "PHASE_M30_OPTIMIZATION_COMPLETE"),
                ("M30_ROBUSTNESS", "PHASE_M30_ROBUSTNESS_COMPLETE"))
    for manifest, (phase, status) in zip(manifests, expected):
        if (manifest.get("phase"), manifest.get("status"), manifest.get("timeframe"),
                manifest.get("development_period"), manifest.get("true_oos_cutoff"),
                manifest.get("true_oos_blocked")) != (
                phase, status, "M30", DEVELOPMENT_PERIOD, "2025-01-01", True):
            raise RuntimeError(f"{phase}_PROVENANCE_INVALID")
    bm, om, rm = manifests
    snapshots = [_canonical_sources(m["source_files"]) for m in manifests]
    if snapshots[0] != snapshots[1] or snapshots[1] != snapshots[2]:
        raise RuntimeError("M30_PREREQUISITE_SOURCE_SNAPSHOT_MISMATCH")
    committed = json.loads((robustness / "candidate_registry.json").read_text(encoding="utf-8"))
    registries = {}
    for key, identity in EXPECTED.items():
        registry = committed.get(key, {})
        if tuple(registry.get(x) for x in ("candidate_id", "optimization_configuration_id", "parameter_hash")) != identity:
            raise RuntimeError(f"{key}_FROZEN_CANDIDATE_IDENTITY_MISMATCH")
        if (stable_hash(registry.get("parameters", {})) != identity[2]
                or registry.get("parent_candidate_id") != f"{key}_candidate_v1"
                or registry.get("selection_locked_before_validation") is not True):
            raise RuntimeError(f"{key}_FROZEN_PARAMETER_HASH_MISMATCH")
        if registry.get("strategy_hash") != STRATEGY_SHA256[key]:
            raise RuntimeError(f"{key}_FROZEN_PROVENANCE_MISMATCH")
        registries[key] = {**registry, "configuration_id": registry["optimization_configuration_id"]}
    return bm, om, rm, registries


def _normalize(raw: pd.DataFrame, key: str, alias: str, fold: str) -> pd.DataFrame:
    frame = raw.copy() if key == "T2" else _normalize_backtester(raw, key)
    if frame.empty:
        return pd.DataFrame(columns=TRADE_COLUMNS + ["fold_id"])
    frame["instrument"] = "USDRUBF" if alias == "Si" else "CNYRUBF"
    frame["strategy"], frame["timeframe"], frame["fold_id"] = key, "M30", fold
    frame["net_R"] = frame.gross_R.astype(float) - 2 * COST_TICKS_PER_SIDE / frame.initial_risk_ticks.astype(float)
    frame["trade_id"] = [f"{key}-M30-{fold}-{alias}-{i:06d}" for i in range(1, len(frame) + 1)]
    return frame


def execute_window(key: str, registry: dict, alias: str, candles: pd.DataFrame,
                   start: pd.Timestamp, end: pd.Timestamp, fold: str) -> pd.DataFrame:
    """Replay one independent window with causal warm-up and FLAT state."""
    params = replace(PARAMETERS[key], **registry["parameters"])
    spec = get_instrument_spec(alias)
    if key == "T2":
        raw = T2WalkForwardAdapter(params, start, end).run(candles, alias, tick_size=spec.price_precision)
    else:
        context = _FOUR_M30_CONTEXT_CACHE.get(id(candles))
        if context is None:
            context = causal_four_m30_context(candles)
            _FOUR_M30_CONTEXT_CACHE[id(candles)] = context
        raw = Backtester(FixedRiskPortfolio(), tick_size=spec.price_precision).run(
            T3MTFTrend(params), alias, candles, context,
            entry_start=start, entry_end=end).trades
    result = _normalize(raw, key, alias, fold)
    if len(result):
        entries = pd.to_datetime(result.entry_time, utc=True)
        if not ((entries >= start.tz_convert("UTC")) & (entries < end.tz_convert("UTC"))).all():
            raise RuntimeError("M30_FOLD_ENTRY_OWNERSHIP_VIOLATION")
        reject_true_oos(entries); reject_true_oos(result.exit_time)
    return result


def metric(frame: pd.DataFrame) -> dict[str, Any]:
    s = stats(frame.net_R.astype(float) if len(frame) else pd.Series(dtype=float))
    return {"trades": s["trades"], "PF": finite(s["PF_R"]), "expectancy_R": finite(s["expectancy"]),
        "net_R": s["net_R"], "max_drawdown_R": s["max_DD_R"],
        "recovery_factor": finite(s["recovery_factor"]), "win_rate": finite(s["winrate"]),
        "median_R": finite(s["median_R"]), "max_losing_streak": s["max_losing_streak"],
        "max_winning_streak": s["max_winning_streak"]}


def verdict(folds: int, aggregate: dict, positive_share: float, top1: float | None,
            instruments: list[dict]) -> str:
    if folds < 3:
        return "INSUFFICIENT_HISTORY"
    instrument_pass = all(row["trades"] < 20 or (row["expectancy_R"] or 0) > 0 for row in instruments)
    passed = (aggregate["trades"] >= 50 and (aggregate["expectancy_R"] or 0) > 0 and
        (aggregate["PF"] or 0) > 1.2 and aggregate["net_R"] > 0 and positive_share >= .60 and
        (top1 is None or top1 < .70) and instrument_pass)
    if passed:
        return "WALK_FORWARD_PASS"
    if (aggregate["expectancy_R"] or 0) > 0 and (aggregate["PF"] or 0) > 1 and aggregate["net_R"] > 0:
        return "WALK_FORWARD_BORDERLINE"
    return "WALK_FORWARD_FAIL"


def _run_candidate(key: str, registry: dict, loaded: dict, folds: list[dict], target: Path) -> dict:
    target.mkdir(parents=True); (target / "folds").mkdir()
    fold_rows, decay_rows, parts = [], [], []
    for fold in folds:
        windows = {}
        for split, start, end in (("train", fold["train_start"], fold["train_end"]),
                                  ("test", fold["test_start"], fold["test_end"])):
            pieces = [execute_window(key, registry, alias, loaded[alias][0], start, end,
                                     fold["fold_id"] + "-" + split) for _, alias in INSTRUMENTS]
            windows[split] = pd.concat(pieces, ignore_index=True).sort_values(
                ["entry_time", "instrument", "trade_id"], kind="mergesort").reset_index(drop=True)
        test = windows["test"].copy(); test["fold_id"] = fold["fold_id"]
        _csv(target / "folds" / f"{fold['fold_id']}_trades.csv", test)
        parts.append(test); tm, sm = metric(windows["train"]), metric(test)
        fold_rows.append({"fold_id": fold["fold_id"], **{n: fold[n].isoformat() for n in
            ("train_start", "train_end", "test_start", "test_end")}, "initial_state": "FLAT", **sm,
            "LONG_trades": int(test.direction.eq("LONG").sum()), "SHORT_trades": int(test.direction.eq("SHORT").sum()),
            "USDRUBF_trades": int(test.instrument.eq("USDRUBF").sum()), "CNYRUBF_trades": int(test.instrument.eq("CNYRUBF").sum()),
            "positive_fold": sm["net_R"] > 0})
        decay_rows.append({"fold_id": fold["fold_id"], "train_expectancy_R": tm["expectancy_R"],
            "test_expectancy_R": sm["expectancy_R"], "expectancy_decay_R": (None if None in
            (tm["expectancy_R"], sm["expectancy_R"]) else sm["expectancy_R"] - tm["expectancy_R"]),
            "train_PF": tm["PF"], "test_PF": sm["PF"], "parameters_frozen": True})
    stitched = pd.concat(parts, ignore_index=True).sort_values(
        ["entry_time", "instrument", "trade_id"], kind="mergesort").reset_index(drop=True)
    if stitched.trade_id.duplicated().any() or stitched[["instrument", "entry_time"]].duplicated().any():
        raise RuntimeError("M30_DUPLICATE_FORWARD_ENTRY")
    _csv(target / "fold_metrics.csv", fold_rows); _csv(target / "train_test_decay.csv", decay_rows)
    _csv(target / "stitched_forward_trades.csv", stitched)
    aggregate = metric(stitched)
    positive_total = float(stitched.loc[stitched.net_R > 0, "net_R"].sum())
    concentration_rows = []
    for row in fold_rows:
        part = stitched.loc[stitched.fold_id.eq(row["fold_id"])]
        positive = float(part.loc[part.net_R > 0, "net_R"].sum())
        concentration_rows.append({"fold_id": row["fold_id"], "fold_net_R": row["net_R"],
            "fold_positive_R": positive, "share_of_total_positive_R": positive / positive_total if positive_total else None,
            "share_of_total_net_R": row["net_R"] / aggregate["net_R"] if aggregate["net_R"] else None})
    shares = sorted((x["share_of_total_positive_R"] for x in concentration_rows
                     if x["share_of_total_positive_R"] is not None), reverse=True)
    top1, top2 = (shares[0] if shares else None), (sum(shares[:2]) if shares else None)
    _csv(target / "fold_concentration.csv", concentration_rows)
    instruments = [{"instrument": name, **metric(stitched.loc[stitched.instrument.eq(name)])}
                   for name, _ in INSTRUMENTS]
    directions = [{"direction": name, **metric(stitched.loc[stitched.direction.eq(name)])}
                  for name in ("LONG", "SHORT")]
    _csv(target / "instrument_report.csv", instruments); _csv(target / "direction_report.csv", directions)
    excursions = []
    for name, sample in (("all", stitched), ("winners", stitched.loc[stitched.net_R > 0]),
                         ("losers", stitched.loc[stitched.net_R <= 0])):
        excursions.append({"group": name, "trades": len(sample),
            **{f"{column}_{stat}": (finite(getattr(sample[column].astype(float), stat)()) if len(sample) else None)
               for column in ("MAE_R", "MFE_R") for stat in ("mean", "median")}})
    _csv(target / "mae_mfe_report.csv", excursions)
    positive = sum(row["positive_fold"] for row in fold_rows); positive_share = positive / len(folds)
    decision = verdict(len(folds), aggregate, positive_share, top1, instruments)
    payload = {"candidate_id": registry["candidate_id"], "configuration_id": registry["configuration_id"],
        "parameter_hash": registry["parameter_hash"], **aggregate, "positive_folds": positive,
        "total_folds": len(folds), "positive_fold_share": positive_share,
        "top_1_fold_positive_R_share": top1, "top_2_fold_positive_R_share": top2, "verdict": decision}
    _json(target / "aggregate_metrics.json", payload)
    (target / "final_report.md").write_text(
        f"# {registry['candidate_id']} M30 Walk Forward\n\n"
        f"**{decision}** — {aggregate['trades']} stitched trades; PF {aggregate['PF']}; "
        f"expectancy {aggregate['expectancy_R']} R; net {aggregate['net_R']} R; positive folds {positive}/{len(folds)}.\n\n"
        "Frozen parameters, independent FLAT folds, causal warm-up, H1 C1 costs only; no ranking or selection.\n",
        encoding="utf-8")
    _json(target / "folds.json", [{k: (v.isoformat() if isinstance(v, pd.Timestamp) else v)
                                    for k, v in fold.items()} for fold in folds])
    return {"strategy": key, **payload}


def run(data_root: Path = APPROVED_DATA_ROOT, output: Path = OUTPUT,
        baseline: Path = BASELINE, optimization: Path = OPTIMIZATION,
        robustness: Path = ROBUSTNESS) -> dict[str, Any]:
    verify_frozen_strategies()
    baseline, optimization, robustness, output = map(Path, (baseline, optimization, robustness, output))
    bm, om, rm, registries = validate_prerequisites(baseline, optimization, robustness)
    protected = tuple(Path(x) for x in PROTECTED[:-3]) + PROTECTED[-3:]
    # Replace default prerequisite paths when tests supply isolated snapshots.
    protected = tuple(x for x in protected if x not in (BASELINE, OPTIMIZATION, ROBUSTNESS)) + (baseline, optimization, robustness)
    before = {str(path): hash_tree(path) for path in protected}
    loaded = {alias: load_m30_development(Path(data_root), alias) for _, alias in INSTRUMENTS}
    actual_sources = [{"instrument": instrument, "alias": alias,
        "files": [{"name": p.name, "sha256": _sha(p)} for p in loaded[alias][1]]}
        for instrument, alias in INSTRUMENTS]
    expected_sources = _canonical_sources(bm["source_files"])
    if actual_sources != expected_sources:
        raise RuntimeError("M30_SOURCE_SNAPSHOT_MISMATCH")
    common_start = max(loaded[alias][0].index.min() for _, alias in INSTRUMENTS)
    common_last = min(loaded[alias][0].index.max() for _, alias in INSTRUMENTS)
    # The frozen snapshot explicitly covers the full development period. Its
    # exclusive scheduling boundary is therefore midnight 2025-01-01; no row
    # at that timestamp is read or admitted.
    coverage_end = TRUE_OOS_START
    folds = generate_folds(common_start, coverage_end)
    if len(folds) != 3:
        raise RuntimeError("M30_EXPECTED_THREE_COMPLETE_FOLDS")
    if output.exists(): shutil.rmtree(output)
    output.mkdir(parents=True)
    summaries = [_run_candidate(key, registries[key], loaded, folds, output / key) for key in ("T2", "T3")]
    _csv(output / "comparison.csv", summaries)
    after = {str(path): hash_tree(path) for path in protected}
    if before != after:
        raise RuntimeError("M30_PROTECTED_ARTIFACT_MUTATION")
    schedule = [{k: (v.isoformat() if isinstance(v, pd.Timestamp) else v) for k, v in fold.items()} for fold in folds]
    source_tree_hashes = {"baseline": _sha(baseline / "manifest.json"),
        "optimization": _sha(optimization / "manifest.json"), "robustness": _sha(robustness / "manifest.json")}
    flags = {"optimization": False, "parameter_change": False, "strategy_change": False,
        "filter_search": False, "ranking": False, "candidate_selection": False, "portfolio": False,
        "true_oos_access": False, "true_oos_used_for_training": False, "true_oos_used_for_selection": False}
    manifest = {"phase": "M30_WALK_FORWARD", "status": STATUS, "timeframe": "M30",
        "candidate_ids": {k: registries[k]["candidate_id"] for k in registries},
        "parent_candidate_ids": {k: registries[k]["parent_candidate_id"] for k in registries},
        "configuration_ids": {k: registries[k]["configuration_id"] for k in registries},
        "candidate_registry_hash": _sha(robustness / "candidate_registry.json"),
        "parameter_hashes": {k: registries[k]["parameter_hash"] for k in registries},
        "strategy_hashes": STRATEGY_SHA256, "prerequisite_manifest_hashes": source_tree_hashes,
        "source_data_hashes": actual_sources, "development_period": DEVELOPMENT_PERIOD,
        "complete_fold_count": len(folds), "common_coverage": {"first_close": common_start.isoformat(), "last_close": common_last.isoformat(),
                            "end_exclusive": coverage_end.isoformat()}, "fold_schedule": schedule,
        "initial_train_months": 12, "test_months": 3, "step_months": 3,
        "cost_model": bm["cost_model"], "deterministic": True,
        "parameters_frozen": True, "flat_start_each_fold": True, "causal_warmup_only": True,
        "flat_initialization_per_fold": True, "causal_four_m30_context": True,
        "true_oos_cutoff": "2025-01-01", "true_oos_blocked": True,
        "protected_artifact_hashes": after, **flags}
    _json(output / "manifest.json", manifest)
    lines = ["# M30 Causal Walk Forward Validation", "", "Frozen candidates validated independently; this is not a ranking.", "",
        "| Candidate | Trades | PF | Expectancy R | Net R | Max DD R | Positive folds | Verdict |",
        "|---|---:|---:|---:|---:|---:|---:|---|"]
    for row in summaries:
        lines.append(f"| {row['candidate_id']} | {row['trades']} | {row['PF']} | {row['expectancy_R']} | {row['net_R']} | {row['max_drawdown_R']} | {row['positive_folds']}/{row['total_folds']} | {row['verdict']} |")
    lines += ["", "Every fold starts FLAT. Historical data is causal warm-up/context only. H1 C1 is the sole cost model; TRUE OOS remains locked.", "", STATUS, ""]
    (output / "walk_forward_report.md").write_text("\n".join(lines), encoding="utf-8")
    return {"status": STATUS, "candidates": summaries, "fold_schedule": schedule}
