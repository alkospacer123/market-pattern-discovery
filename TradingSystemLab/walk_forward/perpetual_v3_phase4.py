"""Phase 4 walk-forward evidence for the four immutable v3 perpetual candidates.

This is a direct reuse of :mod:`walk_forward.phase4`; it has no
selection, search, ranking, or candidate-replacement surface.
"""
from __future__ import annotations

from copy import deepcopy
import argparse
import hashlib
import json
import multiprocessing as mp
from pathlib import Path
import shutil
from typing import Any, Mapping

import pandas as pd

from ..perpetual_v3_baseline import DATA_ROOT, FROZEN_TICK_SIZE, INSTRUMENTS, load_development, verify_strategy_identity
from ..core.unified_metrics import finite, stats
from ..optimization.experiment import stable_hash
from ..perpetual_v3_phase2a_t2 import _execute as execute_t2
from ..perpetual_v3_baseline import four_bar_context
from ..core.backtester import Backtester
from ..core.portfolio import FixedRiskPortfolio
from ..optimization.phase32 import _normalize_backtester
from ..strategies.trend.T3_MTF_Trend import T3MTFTrend, T3Parameters
from ..strategies.trend.T2_Trend_Pullback import T2Parameters
from ..robustness.perpetual_v3_phase3 import EXPECTED_IDS, load_frozen_registry
from dataclasses import asdict, replace

OUTPUT_ROOT = Path("TradingSystemLab/results/perpetual_v3/walk_forward")
REGISTRY_PATH = Path("TradingSystemLab/results/perpetual_v3/phase3_candidate_freeze/candidate_registry.json")
ROBUSTNESS_ROOT = Path("TradingSystemLab/results/perpetual_v3/robustness")
FREEZE_REFERENCE_COMMIT = "f123f1468c6b5f1f0719154aba73d4635e6de0ea"
PHASE2_REFERENCE_COMMIT = "272eabd5a4261a18a763356964b82b4b5b5673ea"
ROBUSTNESS_REFERENCE_COMMIT = "d684bfb7f321c2183eab36159c77fa687bd6092b"
STUDIES = (("T2", "M30"), ("T2", "H1"), ("T3", "M30"), ("T3", "H1"))
ROBUSTNESS = {study: "ROBUST_READY" for study in STUDIES}
SCHEDULE = (
    ("WF01", "2023-01-01", "2023-12-31 23:59:59", "2024-01-01", "2024-03-31 23:59:59"),
    ("WF02", "2023-01-01", "2024-03-31 23:59:59", "2024-04-01", "2024-06-30 23:59:59"),
    ("WF03", "2023-01-01", "2024-06-30 23:59:59", "2024-07-01", "2024-09-30 23:59:59"),
    ("WF04", "2023-01-01", "2024-09-30 23:59:59", "2024-10-01", "2024-12-31 23:59:59"),
)


def _json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")


def _csv(path: Path, rows: list[dict[str, Any]], columns: list[str] | None = None) -> None:
    pd.DataFrame(rows, columns=columns).map(finite).to_csv(
        path, index=False, lineterminator="\n", float_format="%.12g", na_rep="")


def _summary(values: pd.Series) -> dict[str, Any]:
    result = stats(values.astype(float))
    return {"trades": result["trades"], "PF": result["PF_R"],
            "expectancy": result["expectancy"], "net_R": result["net_R"],
            "max_drawdown": result["max_DD_R"], "recovery_factor": result["recovery_factor"],
            "win_rate": result["winrate"], "winning_streak": result["max_winning_streak"],
            "losing_streak": result["max_losing_streak"]}


def classify(summary: Mapping[str, Any], positive_share: float, best_fold: float | None,
             instrument_expectancies: list[float | None], complete_folds: int) -> str:
    instrument_gate = all((0.0 if x is None or pd.isna(x) else x) >= 0
                          for x in instrument_expectancies)
    pass_ = (summary["trades"] >= 50 and summary["expectancy"] is not None
             and summary["expectancy"] > 0 and positive_share >= .60
             and (best_fold is None or pd.isna(best_fold) or best_fold <= .70)
             and instrument_gate and complete_folds > 0)
    majority_negative = complete_folds > 0 and positive_share < .50
    fail = ((summary["expectancy"] is not None and summary["expectancy"] < 0)
            or majority_negative)
    return "WALK_FORWARD_PASS" if pass_ else ("WALK_FORWARD_FAIL" if fail else "WALK_FORWARD_BORDERLINE")


def full_parameters(strategy: str, frozen: Mapping[str, Any]) -> dict[str, Any]:
    """Resolve the immutable optimization delta against canonical defaults."""
    defaults = T2Parameters() if strategy == "T2" else T3Parameters()
    return asdict(replace(defaults, **frozen))


def _verify_before_data(registry_path: Path) -> tuple[list[dict[str, Any]], str]:
    verify_strategy_identity()
    candidates, sha = load_frozen_registry(registry_path)
    robust = json.loads((ROBUSTNESS_ROOT / "validation_manifest.json").read_text())
    if robust.get("status") != "V3_PERPETUAL_PHASE_3_ROBUSTNESS_COMPLETE" or robust.get("classifications") != {
            f"{s}/{t}": ROBUSTNESS[(s, t)] for s, t in STUDIES}:
        raise RuntimeError("PHASE_3_ROBUSTNESS_PROVENANCE_INVALID")
    if [(x["strategy"], x["timeframe"]) for x in candidates] != list(STUDIES):
        raise RuntimeError("FROZEN_CANDIDATE_ORDER_INVALID")
    return candidates, sha


def _execute(strategy: str, parameters: Mapping[str, Any], frames: Mapping[str, pd.DataFrame],
             start: str, end: str) -> pd.DataFrame:
    # Each invocation creates fresh strategy, context and portfolio instances.
    sliced = {symbol: frames[symbol].loc[start:end].copy() for symbol in INSTRUMENTS}
    if strategy == "T2":
        trades = execute_t2(parameters, sliced)
    else:
        pieces = []
        for symbol in INSTRUMENTS:
            execution = sliced[symbol]
            raw = Backtester(FixedRiskPortfolio(), cost_ticks_per_side=1,
                             tick_size=FROZEN_TICK_SIZE).run(
                T3MTFTrend(replace(T3Parameters(), **parameters)), symbol,
                execution, four_bar_context(execution)).trades
            piece = _normalize_backtester(raw, "T3")
            if len(piece):
                piece["net_R_C1"] = piece["gross_R"] - piece["cost_R"]
                pieces.append(piece)
        trades = pd.concat(pieces, ignore_index=True) if pieces else pd.DataFrame()
    if len(trades):
        lo, hi = pd.Timestamp(start, tz="UTC"), pd.Timestamp(end, tz="UTC")
        entry = pd.to_datetime(trades.entry_time, utc=True)
        exit_ = pd.to_datetime(trades.exit_time, utc=True)
        trades = trades.loc[entry.ge(lo) & exit_.le(hi)].copy()
        trades = trades.sort_values(["exit_time", "symbol", "trade_id"], kind="mergesort").reset_index(drop=True)
    return trades


_WORKER_INPUT: tuple[str, Mapping[str, Any], Mapping[str, pd.DataFrame]] | None = None


def _interval_worker(interval: tuple[str, str]) -> pd.DataFrame:
    if _WORKER_INPUT is None:
        raise RuntimeError("INTERVAL_WORKER_NOT_INITIALIZED")
    strategy, parameters, frames = _WORKER_INPUT
    return _execute(strategy, parameters, frames, *interval)


def _reports(trades: pd.DataFrame, target: Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    net = trades.net_R_C1.astype(float) if len(trades) else pd.Series(dtype=float)
    instruments = [{"symbol": x, **_summary(net[trades.symbol.eq(x)])} for x in INSTRUMENTS]
    _csv(target / "instrument_report.csv", instruments)
    _csv(target / "direction_report.csv", [{"direction": x, **_summary(net[trades.direction.eq(x)])}
                                             for x in ("LONG", "SHORT")])
    years = pd.to_datetime(trades.exit_time, utc=True).dt.year if len(trades) else pd.Series(dtype=int)
    _csv(target / "year_report.csv", [{"year": 2024, **_summary(net[years.eq(2024)])}])
    positive = net[net > 0].sort_values(ascending=False); total_positive = positive.sum()
    fold_net = trades.assign(_net=net).groupby("fold", sort=True)._net.sum() if len(trades) else pd.Series(dtype=float)
    total = net.sum()
    concentration = {f"top_{n}_trade_share": (float(positive.head(n).sum() / total_positive)
                     if total_positive > 0 else None) for n in (1, 3, 10)}
    concentration["best_fold_contribution"] = (float(fold_net.max() / total)
                                                if len(fold_net) and total > 0 else None)
    _csv(target / "concentration.csv", [concentration])
    _csv(target / "leave_one_fold_out.csv", [
        {"omitted_fold": fold, **_summary(net[trades.fold.ne(fold)])} for fold, *_ in SCHEDULE])
    rows = []
    for group, mask in (("ALL", pd.Series(True, index=trades.index)),
                        ("WINNERS", net.gt(0)), ("LOSERS", net.lt(0))):
        for metric in ("MAE_R", "MFE_R"):
            values = pd.to_numeric(trades.loc[mask, metric], errors="coerce").dropna()
            rows.append({"group": group, "metric": metric, "trades": len(values),
                         "mean": values.mean() if len(values) else None,
                         "median": values.median() if len(values) else None,
                         "p75": values.quantile(.75) if len(values) else None,
                         "p90": values.quantile(.90) if len(values) else None})
    _csv(target / "mae_mfe.csv", rows)
    return instruments, concentration


def run(data_root: Path = DATA_ROOT, output: Path = OUTPUT_ROOT,
        registry_path: Path = REGISTRY_PATH) -> dict[str, Any]:
    candidates, registry_sha = _verify_before_data(registry_path)
    cache: dict[tuple[str, str], pd.DataFrame] = {}; coverage: dict[str, Any] = {}
    for timeframe in ("M30", "H1"):
        coverage[timeframe] = {}
        for symbol in INSTRUMENTS:
            frame, source = load_development(data_root, symbol, timeframe)
            cache[(symbol, timeframe)] = frame
            fold_status = {}
            for fold, _, _, test_start, test_end in SCHEDULE:
                test = frame.loc[test_start:test_end]
                fold_status[fold] = "COMPLETE" if len(test) else "INCOMPLETE"
            coverage[timeframe][symbol] = {
                "source_file": str(source), "first_admitted_close": frame.index.min().isoformat(),
                "last_admitted_close": frame.index.max().isoformat(), "rows": len(frame),
                "actual_history_limitation": ("source begins after Development start" if
                    frame.index.min() > pd.Timestamp("2023-01-07", tz=frame.index.tz) else None),
                "fold_coverage_status": fold_status}
    if any(status != "COMPLETE" for tf in coverage.values() for item in tf.values()
           for status in item["fold_coverage_status"].values()):
        raise RuntimeError("TEST_QUARTER_COVERAGE_INCOMPLETE")
    output = Path(output)
    if output.exists(): shutil.rmtree(output)
    output.mkdir(parents=True); (output / "summary").mkdir()
    _json(output / "DATA_COVERAGE_REPORT.json", {"status": "SUFFICIENT", "true_oos_read": False,
          "timeframes": coverage})
    verdicts: dict[str, str] = {}; comparison = []
    for item in candidates:
        strategy, timeframe = item["strategy"], item["timeframe"]
        frames = {s: cache[(s, timeframe)] for s in INSTRUMENTS}
        target = output / strategy / timeframe; target.mkdir(parents=True)
        fold_rows = []; decay = []; pieces = []
        frozen = deepcopy(item["parameters"])
        intervals = [(x[1], x[2]) for x in SCHEDULE] + [(x[3], x[4]) for x in SCHEDULE]
        global _WORKER_INPUT
        _WORKER_INPUT = (strategy, frozen, frames)
        with mp.get_context("fork").Pool(processes=8) as pool:
            executions = pool.map(_interval_worker, intervals)
        _WORKER_INPUT = None
        for index, (fold, train_start, train_end, test_start, test_end) in enumerate(SCHEDULE):
            train, test = executions[index], executions[index + len(SCHEDULE)]
            test["fold"] = fold; test["fold_start_state"] = "FLAT"; pieces.append(test)
            train_summary, test_summary = _summary(train.net_R_C1), _summary(test.net_R_C1)
            fold_rows.append({"fold": fold, "train_start": train_start, "train_end": train_end,
                "test_start": test_start, "test_end": test_end, "status": "COMPLETE",
                "included_in_pass": True, "reason": "", **test_summary})
            difference = lambda a, b: None if a is None or b is None else b - a
            decay.append({"fold": fold, "train_expectancy": train_summary["expectancy"],
                "test_expectancy": test_summary["expectancy"],
                "expectancy_decay": difference(train_summary["expectancy"], test_summary["expectancy"]),
                "train_PF": train_summary["PF"], "test_PF": test_summary["PF"],
                "PF_change": difference(train_summary["PF"], test_summary["PF"]),
                "train_win_rate": train_summary["win_rate"], "test_win_rate": test_summary["win_rate"],
                "win_rate_change": difference(train_summary["win_rate"], test_summary["win_rate"])})
        if stable_hash(frozen) != item["parameter_hash"]: raise RuntimeError("FROZEN_PARAMETERS_MODIFIED")
        trades = pd.concat(pieces, ignore_index=True).sort_values(
            ["exit_time", "symbol", "trade_id"], kind="mergesort").reset_index(drop=True)
        _csv(target / "folds.csv", fold_rows); _csv(target / "trades.csv", trades.to_dict("records"))
        _csv(target / "train_test_decay.csv", decay)
        instruments, concentration = _reports(trades, target)
        aggregate = _summary(trades.net_R_C1); complete = len(fold_rows)
        positive_share = sum(row["expectancy"] is not None and row["expectancy"] > 0
                             for row in fold_rows) / complete
        best_fold = concentration["best_fold_contribution"]
        instrument_gate = all((x["expectancy"] if x["expectancy"] is not None else 0) >= 0 for x in instruments)
        verdict = classify(aggregate, positive_share, best_fold,
                           [x["expectancy"] for x in instruments], complete)
        key = f"{strategy}/{timeframe}"; verdicts[key] = verdict
        metrics = {"candidate_id": item["candidate_id"], "strategy": strategy, "timeframe": timeframe,
            "phase2_configuration_id": item["phase2_configuration_id"],
            "frozen_parameter_hash": item["parameter_hash"], "full_execution_parameters": full_parameters(strategy, frozen),
            "strategy_source_hash": item["frozen_strategy_source_hash"], "aggregate": {"C1": aggregate},
            "complete_folds": complete, "positive_complete_fold_share": positive_share,
            "best_fold_contribution": best_fold, "instrument_gate": instrument_gate,
            "verdict": verdict, "parameters_frozen": True, "optimization": False,
            "ranking": False, "candidate_replacement": False, "true_oos_blocked": True,
            "execution_context": ("none" if strategy == "T2" else
                f"four completed non-overlapping {timeframe} bars; local-day reset")}
        _json(target / "metrics.json", metrics)
        study_manifest = {
            "generation": "v3_perpetual", "lifecycle_phase": "Walk Forward",
            "methodological_source": "original H1 Phase 4",
            "phase3_canonical_merge": ROBUSTNESS_REFERENCE_COMMIT,
            "candidate_freeze_merge": FREEZE_REFERENCE_COMMIT,
            "phase2_consolidation_merge": PHASE2_REFERENCE_COMMIT,
            "candidate_id": item["candidate_id"],
            "phase2_configuration_id": item["phase2_configuration_id"],
            "candidate_parameter_hash": item["parameter_hash"],
            "full_execution_parameters": full_parameters(strategy, frozen),
            "strategy_source_hash": item["frozen_strategy_source_hash"],
            "instrument_universe": list(INSTRUMENTS), "timeframe": timeframe,
            "development_interval": ["2023-01-01", "2024-12-31"],
            "fold_schedule_definition": [{"fold": x[0], "train_start": x[1],
                "train_end": x[2], "forward_start": x[3], "forward_end": x[4]}
                for x in SCHEDULE],
            "cost_model": "C1", "cost_ticks_per_side": 1, "round_trip_ticks": 2,
            "normalized_tick": FROZEN_TICK_SIZE, "additional_slippage": 0,
            "t3_execution_context": metrics["execution_context"],
            "true_oos_status": "BLOCKED_NOT_READ_NOT_EXECUTED",
            "optimization": False, "candidate_replacement": False,
            "true_oos_execution": False, "classification": verdict,
        }
        _json(target / "manifest.json", study_manifest)
        (target / "final_report.md").write_text(
            f"# {item['candidate_id']} Walk Forward\n\n- Study: {strategy}/{timeframe}\n"
            f"- Frozen Phase 2 configuration: `{item['phase2_configuration_id']}`\n- Verdict: **{verdict}**\n"
            f"- Complete folds: {complete}/4\n- Stitched C1 trades: {aggregate['trades']}\n"
            f"- C1 expectancy: {aggregate['expectancy']}\n- Positive complete-fold share: {positive_share}\n"
            f"- Best-fold contribution: {best_fold}\n- Instrument gate: {instrument_gate}\n\n"
            "Every fold started FLAT. Parameters remained frozen. No optimization, ranking, or replacement "
            "occurred. TRUE OOS remained blocked.\n", encoding="utf-8")
        comparison.append({"candidate_id": item["candidate_id"], "strategy": strategy,
            "timeframe": timeframe, "robustness_classification": ROBUSTNESS[(strategy, timeframe)],
            "walk_forward_verdict": verdict, **aggregate,
            "positive_complete_fold_share": positive_share, "best_fold_contribution": best_fold})
    _csv(output / "summary/comparison.csv", comparison)
    status = "V3_PERPETUAL_PHASE_4_WALK_FORWARD_COMPLETE"
    manifest = {"phase": "PHASE_4_WALK_FORWARD", "methodological_source": "original H1 Phase 4",
        "status": "PENDING_AUDIT", "robustness_reference_commit": ROBUSTNESS_REFERENCE_COMMIT,
        "freeze_reference_commit": FREEZE_REFERENCE_COMMIT, "candidate_registry_path": str(registry_path),
        "candidate_registry_sha256": registry_sha, "candidate_ids": [x["candidate_id"] for x in candidates],
        "candidate_count": 4, "parameters_frozen": True, "strategies": ["T2", "T3"],
        "timeframes": ["M30", "H1"], "instruments": list(INSTRUMENTS),
        "development_coverage": ["2023-01-01", "2024-12-31"],
        "fold_schedule": [{"fold": x[0], "train_start": x[1], "train_end": x[2],
                           "test_start": x[3], "test_end": x[4]} for x in SCHEDULE],
        "normalized_research_tick": FROZEN_TICK_SIZE, "C1_only": True, "optimization": False,
        "ranking": False, "candidate_replacement": False, "robustness_reexecution": False,
        "true_oos_start": "2025-01-01", "true_oos_status": "BLOCKED_NOT_READ_NOT_EXECUTED", "true_oos_blocked": True, "true_oos_read": False, "true_oos_executed": False,
        "phase7_mtf_research": False, "deterministic": True, "verdicts": verdicts,
        "second_complete_execution_compared": False,
        "procedural_status_after_audit": status}
    _json(output / "summary/manifest.json", manifest)
    _json(output / "validation_manifest.json", manifest)
    lines = ["# TradingSystemLab v3 perpetual — Phase 4 Walk Forward", "",
        "Studies are in canonical lifecycle order and are not ranked.", ""]
    for row in comparison:
        lines.append(f"- `{row['candidate_id']}` — Robustness: {row['robustness_classification']}; Walk Forward: **{row['walk_forward_verdict']}**")
    lines += ["", "Development = 2023–2024; four expanding quarterly tests in 2024; C1 only.",
        "Parameters frozen; optimization false; ranking false; candidate replacement false.",
        "TRUE OOS >=2025 remains blocked. All four identities remain in their recorded lifecycle.",
        "Phase 5 TRUE OOS was NOT executed.", "", "PENDING_AUDIT"]
    (output / "summary/Final_Walk_Forward_Report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    (output / "Final_Walk_Forward_Report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return manifest


def artifact_sha256(root: Path) -> dict[str, str]:
    return {p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(root.rglob("*")) if p.is_file()}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-root", type=Path, default=DATA_ROOT)
    parser.add_argument("--output", type=Path, default=OUTPUT_ROOT)
    args = parser.parse_args(); print(json.dumps(run(args.data_root, args.output), sort_keys=True))


if __name__ == "__main__": main()
