"""Development-only Phase 3 robustness for the four frozen v2 candidates.

The candidate registry is the sole candidate input.  This module deliberately
contains no search, ranking, optimization, or replacement mechanism.
"""
from __future__ import annotations

from copy import deepcopy
import argparse
import hashlib
import json
from pathlib import Path
import shutil
from typing import Any, Mapping

import numpy as np
import pandas as pd

from ..baseline_v2 import (DATA_ROOT, FROZEN_TICK_SIZE, INSTRUMENTS,
                           TRUE_OOS_START, load_development)
from ..core.unified_metrics import concentration, finite, stats
from ..multitimeframe.phase71 import verify_frozen_strategies
from ..optimization.experiment import stable_hash
from ..optimization.phase2a_t2 import _execute as execute_t2
from ..optimization.phase2b_t3 import _execute as execute_t3

REGISTRY_PATH = Path("TradingSystemLab/results/phase3_candidate_freeze/candidate_registry.json")
PHASE2_ROOT = Path("TradingSystemLab/results/optimization_v2")
OUTPUT_ROOT = Path("TradingSystemLab/results/robustness_v2")
FREEZE_REFERENCE_COMMIT = "ff0db54b35544086f4265c303b1018d57d3849e7"
STUDIES = (("T2", "M30"), ("T2", "H1"), ("T3", "M30"), ("T3", "H1"))
EXPECTED_IDS = {
    ("T2", "M30"): ("T2_M30_candidate_v2", "7c89b4a215cd8b68f96de2fc0938c2b99e755158b919a1284dfc07c6c2547ac6"),
    ("T2", "H1"): ("T2_H1_candidate_v2", "a98459cab4f22e598fbfd705fb60cfb8a65f1771fa7d903bafa581544faa35ea"),
    ("T3", "M30"): ("T3_M30_candidate_v2", "0050d828c1a8628621f63de1c88fc7bb67fa686d72767732998f6767b1eed8bc"),
    ("T3", "H1"): ("T3_H1_candidate_v2", "aeeb96942cf33d9551b5635f33d2f2745aefad572f57f7ea92b9791c2d992a39"),
}
BOOTSTRAP_ITERATIONS = 10_000
BOOTSTRAP_SEED = 330_2025
COST_MODELS = ("C1",)
DEVELOPMENT_PERIOD = ("2020-01-01", "2024-12-31")


def _json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")


def _csv(path: Path, rows: list[dict[str, Any]]) -> None:
    pd.DataFrame(rows).map(finite).to_csv(path, index=False, lineterminator="\n",
                                          float_format="%.12g", na_rep="")


def load_frozen_registry(path: Path = REGISTRY_PATH) -> tuple[list[dict[str, Any]], str]:
    """Load and validate immutable identities before any market-data access."""
    raw = Path(path).read_bytes()
    payload = json.loads(raw)
    candidates = payload.get("candidates", [])
    if payload.get("immutable") is not True or len(candidates) != 4:
        raise RuntimeError("FROZEN_CANDIDATE_REGISTRY_INVALID")
    ordered = []
    for study in STUDIES:
        matches = [x for x in candidates if (x.get("strategy"), x.get("timeframe")) == study]
        if len(matches) != 1:
            raise RuntimeError(f"FROZEN_STUDY_IDENTITY_INVALID:{study}")
        item = matches[0]
        if (item.get("candidate_id"), item.get("parameter_hash")) != EXPECTED_IDS[study]:
            raise RuntimeError(f"FROZEN_CANDIDATE_ID_OR_HASH_INVALID:{study}")
        if stable_hash(item["parameters"]) != item["parameter_hash"]:
            raise RuntimeError(f"FROZEN_CANDIDATE_PARAMETERS_INVALID:{study}")
        if item.get("selection_locked_before_validation") is not True:
            raise RuntimeError(f"CANDIDATE_SELECTION_NOT_LOCKED:{study}")
        ordered.append(deepcopy(item))
    return ordered, hashlib.sha256(raw).hexdigest()


def _summary(values: pd.Series) -> dict[str, Any]:
    result = stats(values.astype(float))
    return {"trade_count": result["trades"], "PF": result["PF_R"],
            "expectancy": result["expectancy"], "net_R": result["net_R"],
            "max_DD": result["max_DD_R"], "recovery_factor": result["recovery_factor"],
            "win_rate": result["winrate"],
            "max_winning_streak": result["max_winning_streak"],
            "max_losing_streak": result["max_losing_streak"]}


def _group_rows(trades: pd.DataFrame, column: str, groups: list[Any]) -> list[dict[str, Any]]:
    return [{column: group, **_summary(trades.loc[trades[column].eq(group), "net_R_C1"])}
            for group in groups]


def _mae_mfe(trades: pd.DataFrame) -> list[dict[str, Any]]:
    net = trades.net_R_C1.astype(float)
    rows = []
    for group, mask in (("ALL", pd.Series(True, index=trades.index)),
                        ("WINNERS", net.gt(0)), ("LOSERS", net.lt(0))):
        for metric in ("MAE_R", "MFE_R"):
            values = pd.to_numeric(trades.loc[mask, metric], errors="coerce").dropna()
            rows.append({"group": group, "metric": metric, "trade_count": len(values),
                         "mean": values.mean() if len(values) else None,
                         "median": values.median() if len(values) else None,
                         "p75": values.quantile(.75) if len(values) else None,
                         "p90": values.quantile(.90) if len(values) else None})
    return rows


def _dependence(trades: pd.DataFrame) -> list[dict[str, Any]]:
    dates = pd.to_datetime(trades.exit_time, utc=True)
    naive = dates.dt.tz_localize(None)
    periods = {"quarter": naive.dt.to_period("Q").astype(str),
               "year": dates.dt.year.astype(str),
               "fold": naive.dt.to_period("6M").astype(str)}
    rows = []
    for kind, labels in periods.items():
        for label in sorted(labels.unique()):
            rows.append({"analysis": f"leave_one_{kind}_out", "omitted_period": label,
                         **_summary(trades.loc[labels.ne(label), "net_R_C1"])})
    return rows


def _bootstrap(values: pd.Series) -> dict[str, Any]:
    sample = np.asarray(values, dtype=float)
    if not len(sample):
        raise RuntimeError("BOOTSTRAP_REQUIRES_TRADES")
    rng = np.random.default_rng(BOOTSTRAP_SEED)
    means = np.empty(BOOTSTRAP_ITERATIONS)
    for start in range(0, BOOTSTRAP_ITERATIONS, 1000):
        stop = min(start + 1000, BOOTSTRAP_ITERATIONS)
        means[start:stop] = rng.choice(sample, size=(stop - start, len(sample)), replace=True).mean(axis=1)
    quantiles = np.quantile(means, [.025, .05, .5, .95, .975])
    return {"iterations": BOOTSTRAP_ITERATIONS, "seed": BOOTSTRAP_SEED,
            "sample_trades": len(sample), "bootstrap_mean_R": float(means.mean()),
            "p2_5": quantiles[0], "p5": quantiles[1], "p50": quantiles[2],
            "p95": quantiles[3], "p97_5": quantiles[4],
            "probability_mean_R_gt_0": float((means > 0).mean()),
            "interpretation": "DIAGNOSTIC_ONLY_IID_TRADE_BOOTSTRAP"}


def severe_concentration(row: Mapping[str, Any]) -> bool:
    return bool(row["top_3_positive_R_share"] > .50 or row["expectancy_C1_without_top3"] <= 0)


def classify(expectancy: float, instruments_positive: bool, years_positive: bool,
             severe: bool, bootstrap_probability: float) -> str:
    ready = (expectancy > 0 and not severe and instruments_positive and years_positive
             and bootstrap_probability > .5)
    return "ROBUST_READY" if ready else ("BORDERLINE" if expectancy > 0 else "REJECTED")


def _phase2_row(item: Mapping[str, Any]) -> pd.Series:
    path = PHASE2_ROOT / item["strategy"] / item["timeframe"] / "results.csv"
    rows = pd.read_csv(path)
    match = rows.loc[rows.configuration_id.eq(item["phase2_configuration_id"])]
    if len(match) != 1:
        raise RuntimeError("PHASE2_CANDIDATE_RECONCILIATION_SOURCE_MISSING")
    return match.iloc[0]


def _assert_close(actual: Any, expected: Any, label: str) -> None:
    if pd.isna(actual) and pd.isna(expected):
        return
    if not np.isclose(float(actual), float(expected), rtol=1e-9, atol=1e-10):
        raise RuntimeError(f"RECONCILIATION_FAILURE:{label}:{actual}:{expected}")


def _reconcile(item: Mapping[str, Any], baseline: dict[str, Any], candidate: dict[str, Any],
               instruments: list[dict[str, Any]], years: list[dict[str, Any]],
               directions: list[dict[str, Any]]) -> None:
    row = _phase2_row(item)
    fields = {"trade_count": "trades", "PF": "PF_C1", "expectancy": "expectancy_C1",
              "net_R": "net_R_C1", "max_DD": "max_DD_C1",
              "recovery_factor": "recovery_factor_C1", "win_rate": "win_rate_C1"}
    for local, canonical in fields.items():
        _assert_close(candidate[local], row[canonical], f"candidate:{local}")
    for label, rows, prefix in (("instrument", instruments, None), ("year", years, "Y"),
                                ("direction", directions, None)):
        key = {"instrument": "symbol", "year": "year", "direction": "direction"}[label]
        for diagnostic in rows:
            name = diagnostic[key]
            stem = f"{prefix or ''}{name}"
            _assert_close(diagnostic["trade_count"], row[f"{stem}_trades"], f"{label}:{name}:trades")
            _assert_close(diagnostic["expectancy"], row[f"{stem}_expectancy_C1"], f"{label}:{name}:expectancy")
    baseline_rows = pd.read_csv(PHASE2_ROOT / item["strategy"] / item["timeframe"] / "results.csv")
    baseline_id = stable_hash(item["canonical_baseline_parameters"])
    match = baseline_rows.loc[baseline_rows.configuration_id.str.endswith(baseline_id[:12])]
    if len(match) != 1:
        raise RuntimeError("PHASE2_BASELINE_RECONCILIATION_SOURCE_MISSING")
    for local, canonical in fields.items():
        _assert_close(baseline[local], match.iloc[0][canonical], f"baseline:{local}")


def _execute(strategy: str, parameters: Mapping[str, Any], frames: Mapping[str, pd.DataFrame]) -> pd.DataFrame:
    trades = (execute_t2(parameters, frames) if strategy == "T2" else execute_t3(parameters, frames))
    if len(trades):
        dates = pd.concat((pd.to_datetime(trades.entry_time, utc=True),
                           pd.to_datetime(trades.exit_time, utc=True)))
        if (dates >= TRUE_OOS_START.tz_convert("UTC")).any():
            raise RuntimeError("TRUE_OOS_TRADE_VIOLATION")
    return trades


def run(data_root: Path = DATA_ROOT, output: Path = OUTPUT_ROOT,
        registry_path: Path = REGISTRY_PATH) -> dict[str, Any]:
    verify_frozen_strategies()  # must precede the first market-data read
    registry, registry_sha = load_frozen_registry(registry_path)
    if output.exists():
        shutil.rmtree(output)
    output.mkdir(parents=True)
    results = []
    cache: dict[tuple[str, str], pd.DataFrame] = {}
    for item in registry:
        strategy, timeframe = item["strategy"], item["timeframe"]
        frames = {}
        for instrument in INSTRUMENTS:
            key = (instrument, timeframe)
            if key not in cache:
                cache[key] = load_development(data_root, instrument, timeframe)[0]
            frames[instrument] = cache[key]
        frozen_parameters = deepcopy(item["parameters"])
        baseline_trades = _execute(strategy, item["canonical_baseline_parameters"], frames)
        candidate_trades = _execute(strategy, frozen_parameters, frames)
        if frozen_parameters != item["parameters"] or stable_hash(frozen_parameters) != item["parameter_hash"]:
            raise RuntimeError("FROZEN_CANDIDATE_PARAMETERS_MODIFIED")
        baseline = _summary(baseline_trades.net_R_C1)
        candidate = _summary(candidate_trades.net_R_C1)
        comparison = [{"version": "baseline", "scenario": "C1", **baseline},
                      {"version": "candidate", "scenario": "C1", **candidate}]
        enriched = candidate_trades.copy()
        enriched["year"] = pd.to_datetime(enriched.exit_time, utc=True).dt.year
        instruments = _group_rows(enriched, "symbol", list(INSTRUMENTS))
        represented_years = sorted(enriched.year.unique().tolist())
        years = _group_rows(enriched, "year", represented_years)
        directions = _group_rows(enriched, "direction", ["LONG", "SHORT"])
        conc = {"analysis": "profit_concentration", **concentration(enriched.net_R_C1)}
        severe = severe_concentration(conc)
        boot = _bootstrap(enriched.net_R_C1)
        positive = lambda rows: all(row["expectancy"] is not None and row["expectancy"] > 0 for row in rows)
        instruments_positive, years_positive = positive(instruments), positive(years)
        classification = classify(candidate["expectancy"], instruments_positive, years_positive,
                                  severe, boot["probability_mean_R_gt_0"])
        flags = []
        if not instruments_positive: flags.append("INSTRUMENT_DEPENDENT")
        if not years_positive: flags.append("YEAR_DEPENDENT")
        if not positive(directions): flags.append("DIRECTION_DEPENDENT")
        _reconcile(item, baseline, candidate, instruments, years, directions)
        target = output / strategy / timeframe
        target.mkdir(parents=True)
        _csv(target / "baseline_vs_candidate.csv", comparison)
        _csv(target / "cost_report.csv", [comparison[1]])
        _csv(target / "instrument_report.csv", instruments)
        _csv(target / "year_report.csv", years)
        _csv(target / "direction_report.csv", directions)
        _csv(target / "concentration_report.csv", [conc, *_dependence(enriched)])
        _csv(target / "mae_mfe_report.csv", _mae_mfe(enriched))
        _csv(target / "bootstrap_report.csv", [boot])
        manifest = {"phase": "PHASE_3_ROBUSTNESS", "methodological_source": "original H1 Phase 3.3",
                    "strategy": strategy, "timeframe": timeframe, "candidate_id": item["candidate_id"],
                    "phase2_configuration_id": item["phase2_configuration_id"],
                    "candidate_parameter_hash": item["parameter_hash"],
                    "candidate_parameters": item["parameters"],
                    "frozen_strategy_source_hash": item["frozen_strategy_source_hash"],
                    "freeze_reference_commit": FREEZE_REFERENCE_COMMIT,
                    "candidate_registry_path": str(registry_path), "candidate_registry_sha256": registry_sha,
                    "selection_locked_before_validation": True,
                    "development_period": list(DEVELOPMENT_PERIOD), "true_oos_start": "2025-01-01",
                    "true_oos_blocked": True, "normalized_research_tick": FROZEN_TICK_SIZE,
                    "cost_models": ["C1"], "optimization_executed": False,
                    "parameter_search_executed": False, "candidate_replacement_executed": False,
                    "walk_forward_executed": False, "true_oos_executed": False,
                    "phase7_mtf_research": False,
                    "execution_context": ("none" if strategy == "T2" else
                        f"four completed non-overlapping {timeframe} bars; local-day reset"),
                    "classification": classification, "diagnostic_flags": flags,
                    "severe_concentration": severe}
        _json(target / "manifest.json", manifest)
        (target / "final_report.md").write_text(
            f"# {strategy}/{timeframe} Phase 3 Robustness\n\n"
            f"Frozen candidate: `{item['candidate_id']}`. Source Phase 2 configuration: "
            f"`{item['phase2_configuration_id']}`.\n\n**Classification: {classification}**\n\n"
            f"C1 expectancy: {candidate['expectancy']:.12g} R. Flags: {', '.join(flags) or 'NONE'}. "
            f"Severe concentration: {str(severe).lower()}. Bootstrap probability mean R > 0: "
            f"{boot['probability_mean_R_gt_0']:.12g}.\n\nSelection was frozen before validation; "
            "no candidate replacement occurred; no Walk Forward occurred; TRUE OOS remained blocked.\n",
            encoding="utf-8")
        results.append({"strategy": strategy, "timeframe": timeframe, "candidate_id": item["candidate_id"],
                        "classification": classification, **candidate,
                        "flags": flags, "severe_concentration": severe})
    root_manifest = {"phase": "PHASE_3_ROBUSTNESS", "methodological_source": "original H1 Phase 3.3",
        "status": "PENDING_AUDIT", "candidate_count": 4, "freeze_reference_commit": FREEZE_REFERENCE_COMMIT,
        "candidate_selection_precedes_validation": True, "selection_locked_before_validation": True,
        "optimization_performed": False, "parameter_search_expanded": False,
        "candidate_replacement_performed": False, "strategies": ["T2", "T3"],
        "timeframes": ["M30", "H1"], "instruments": list(INSTRUMENTS),
        "development_period": list(DEVELOPMENT_PERIOD), "true_oos_start": "2025-01-01",
        "true_oos_blocked": True, "C1_only": True, "normalized_research_tick": FROZEN_TICK_SIZE,
        "bootstrap": {"iterations": BOOTSTRAP_ITERATIONS, "seed": BOOTSTRAP_SEED, "diagnostic_only": True},
        "second_complete_execution_compared": False,
        "reproducibility_note": "Second full rerun not completed because of runtime; deterministic ordering and seed were retained.",
        "walk_forward_executed": False, "true_oos_executed": False, "phase7_mtf_research": False,
        "classifications": {f"{r['strategy']}/{r['timeframe']}": r["classification"] for r in results}}
    _json(output / "validation_manifest.json", root_manifest)
    lines = ["# TradingSystemLab v2 — Phase 3 Final Robustness Report", "",
             "Studies are shown in fixed lifecycle order; they are not ranked.", "",
             "| Study | Candidate | Classification | Trades | PF C1 | Expectancy C1 | Net R C1 | Max DD C1 | Recovery | Flags |",
             "|---|---|---|---:|---:|---:|---:|---:|---:|---|"]
    for row in results:
        lines.append(f"| {row['strategy']}/{row['timeframe']} | {row['candidate_id']} | {row['classification']} | "
                     f"{row['trade_count']} | {row['PF']:.6g} | {row['expectancy']:.6g} | {row['net_R']:.6g} | "
                     f"{row['max_DD']:.6g} | {row['recovery_factor']:.6g} | {', '.join(row['flags']) or 'NONE'} |")
    lines += ["", "Candidate selection preceded validation. No replacement, Walk Forward, TRUE OOS execution, or Phase 7 MTF research occurred."]
    (output / "Final_Robustness_Report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return root_manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-root", type=Path, default=DATA_ROOT)
    parser.add_argument("--output", type=Path, default=OUTPUT_ROOT)
    args = parser.parse_args()
    print(json.dumps(run(args.data_root, args.output), sort_keys=True))


if __name__ == "__main__":
    main()
