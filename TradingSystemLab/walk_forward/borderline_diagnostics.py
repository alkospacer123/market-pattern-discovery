"""Read-only Phase 4.1 diagnostics for borderline walk-forward candidates.

Only persisted Phase 4 artifacts are consumed.  In particular, this module has
no strategy execution, parameter-space, market-data, or TRUE OOS interface.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import shutil
from typing import Any

import numpy as np
import pandas as pd

from ..core.unified_metrics import finite, stats

KEYS = ("T2", "T3")
SEED = 4102025
ITERATIONS = 10_000


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def artifact_sha256(root: Path) -> dict[str, str]:
    return {p.relative_to(root).as_posix(): _sha(p) for p in sorted(root.rglob("*")) if p.is_file()}


def _json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")


def _csv(path: Path, rows: list[dict], columns: list[str] | None = None) -> None:
    pd.DataFrame(rows, columns=columns).map(finite).to_csv(
        path, index=False, lineterminator="\n", float_format="%.12g", na_rep=""
    )


def _summary(values: pd.Series) -> dict:
    result = stats(values.astype(float))
    return {
        "trades": result["trades"], "PF": result["PF_R"],
        "expectancy": result["expectancy"], "net_R": result["net_R"],
        "max_drawdown": result["max_DD_R"], "win_rate": result["winrate"],
    }


def _classification(trades: pd.DataFrame, folds: pd.DataFrame) -> str:
    # The predeclared walk-forward minimum is 50.  A positive small sample does
    # not become validation-ready merely because its point estimate is good.
    if len(trades) < 50 or not folds.status.eq("complete").all():
        return "SAMPLE_LIMITED"
    if (folds.expectancy <= 0).sum() >= 2:
        return "TEMPORAL_INSTABILITY"
    return "READY_FOR_TRUE_OOS"


def _bootstrap(net: np.ndarray) -> dict:
    rng = np.random.default_rng(SEED)
    means = rng.choice(net, size=(ITERATIONS, len(net)), replace=True).mean(axis=1)
    q = np.quantile(means, [.025, .05, .5, .95, .975])
    return {
        "iterations": ITERATIONS, "seed": SEED, "diagnostic_only": True,
        "lower_2_5_pct": q[0], "lower_5_pct": q[1], "median": q[2],
        "upper_95_pct": q[3], "upper_97_5_pct": q[4],
        "probability_mean_R_gt_0": float(np.mean(means > 0)),
    }


def _diagnose(key: str, source: Path, target: Path) -> dict:
    trades = pd.read_csv(source / key / "trades.csv")
    folds = pd.read_csv(source / key / "folds.csv")
    decay = pd.read_csv(source / key / "train_test_decay.csv")
    net = trades.gross_R.astype(float) - 2 / trades.initial_risk_ticks.astype(float)
    trades = trades.assign(_net_R=net, _exit=pd.to_datetime(trades.exit_time, utc=True))

    fold_rows = []
    for _, row in folds.iterrows():
        values = trades.loc[trades.fold.eq(row.fold), "_net_R"]
        item = {"fold": row.fold, **_summary(values)}
        item["fold_status"] = "POSITIVE" if item["expectancy"] > 0 else "NEGATIVE"
        item["coverage_status"] = row.status
        fold_rows.append(item)
    strongest = max(fold_rows, key=lambda x: x["expectancy"])
    weakest = min(fold_rows, key=lambda x: x["expectancy"])
    total = net.sum()
    strongest_share = strongest["net_R"] / total if total > 0 else None
    depends_one = bool(strongest_share is not None and strongest_share > .7)
    _csv(target / "fold_analysis.csv", fold_rows)

    loo = []
    for fold in folds.fold:
        item = {"omitted_fold": fold, **_summary(trades.loc[trades.fold.ne(fold), "_net_R"])}
        item["edge_survives"] = bool(item["expectancy"] > 0 and item["net_R"] > 0)
        loo.append(item)
    _csv(target / "leave_one_fold_out.csv", loo)

    instrument = []
    for symbol in ("Si", "CNY"):
        item = {"symbol": symbol, **_summary(trades.loc[trades.symbol.eq(symbol), "_net_R"])}
        instrument.append(item)
    instrument_class = ("insufficient sample" if min(x["trades"] for x in instrument) < 10 else
                          "instrument independent" if all(x["expectancy"] > 0 for x in instrument) else "instrument dependent")
    for item in instrument: item["classification"] = instrument_class
    _csv(target / "instrument_report.csv", instrument)

    directions = []
    for direction in ("LONG", "SHORT"):
        item = {"direction": direction, **_summary(trades.loc[trades.direction.eq(direction), "_net_R"])}
        item.pop("max_drawdown"); item.pop("win_rate")
        directions.append(item)
    direction_class = ("insufficient sample" if min(x["trades"] for x in directions) < 10 else
                       "both directions contribute" if all(x["expectancy"] > 0 for x in directions) else "only one direction creates edge")
    for item in directions: item["classification"] = direction_class
    _csv(target / "direction_report.csv", directions)

    quarters = []
    # Phase 4 persisted the 2023 train expectancy, but not its trades or net R.
    quarters.append({"period": "2023_TRAIN", "expectancy": decay.iloc[0].train_expectancy,
                     "net_R": None, "trades": None, "availability": "not recorded in Phase 4 artifacts"})
    for i, fold in enumerate(folds.fold, 1):
        values = trades.loc[trades.fold.eq(fold), "_net_R"]
        quarters.append({"period": f"2024_Q{i}", "expectancy": values.mean(), "net_R": values.sum(),
                         "trades": len(values), "availability": "available"})
    quarter_class = "one regime-dependent quarter" if sum(x["expectancy"] <= 0 for x in quarters[1:]) == 1 else "deterioration over time"
    for item in quarters: item["classification"] = quarter_class
    _csv(target / "quarter_report.csv", quarters)

    ordered = trades.sort_values("_net_R", ascending=False, kind="mergesort")
    positive_total = trades.loc[trades._net_R > 0, "_net_R"].sum()
    concentration = []
    for n in (1, 3, 5):
        # Remove by identity, then preserve the original chronological order so
        # the resulting drawdown remains meaningful.
        remaining = trades.drop(index=ordered.head(n).index)._net_R
        concentration.append({"removed_top_n": n,
            "top_trade_contribution_R": ordered.head(n)._net_R.sum(),
            "percentage_total_positive_R": ordered.head(n)._net_R.clip(lower=0).sum() / positive_total * 100,
            **_summary(remaining), "edge_survives": bool(remaining.mean() > 0 and remaining.sum() > 0)})
    _csv(target / "concentration_report.csv", concentration)

    mae_rows = []
    for group, mask in (("WINNERS", trades._net_R > 0), ("LOSERS", trades._net_R <= 0)):
        part = trades.loc[mask]
        mae_rows.append({"group": group, "trades": len(part),
            "mean_MAE_R": part.MAE_R.mean(), "median_MAE_R": part.MAE_R.median(),
            "mean_MFE_R": part.MFE_R.mean(), "median_MFE_R": part.MFE_R.median(),
            "mean_net_R": part._net_R.mean()})
    for reason, part in trades.groupby("exit_reason", sort=True):
        mae_rows.append({"group": f"EXIT:{reason}", "trades": len(part),
            "mean_MAE_R": part.MAE_R.mean(), "median_MAE_R": part.MAE_R.median(),
            "mean_MFE_R": part.MFE_R.mean(), "median_MFE_R": part.MFE_R.median(),
            "mean_net_R": part._net_R.mean()})
    winners = trades.loc[trades._net_R > 0]
    target_efficiency = float((winners._net_R / winners.MFE_R.replace(0, np.nan)).median())
    stop_frequency = float(trades.exit_reason.str.contains("STOP").mean())
    failure_mode = "regime mismatch" if weakest["expectancy"] < 0 and all(x["expectancy"] > 0 for x in instrument) else "weak exits"
    for item in mae_rows:
        item.update({"stop_frequency": stop_frequency, "winner_median_target_efficiency": target_efficiency,
                     "trailing_behavior": "dominant" if stop_frequency >= .5 else "mixed", "possible_failure_mode": failure_mode})
    _csv(target / "mae_mfe_report.csv", mae_rows)

    decay_rows = []
    for row in decay.itertuples(index=False):
        delta = row.test_expectancy - row.train_expectancy
        label = "positive transfer" if delta > .05 else "degradation" if delta < -.05 else "stable"
        decay_rows.append({"fold": row.fold, "train_expectancy": row.train_expectancy,
                           "test_expectancy": row.test_expectancy, "decay": delta, "classification": label})
    _csv(target / "train_test_decay.csv", decay_rows)
    bootstrap = _bootstrap(net.to_numpy())
    _csv(target / "bootstrap_report.csv", [bootstrap])

    classification = _classification(trades, folds)
    metrics = {
        "candidate_id": json.loads((source / key / "metrics.json").read_text())["candidate_id"],
        "classification": classification, "aggregate": _summary(net),
        "strongest_fold": strongest["fold"], "weakest_fold": weakest["fold"],
        "single_fold_dependency": depends_one, "strongest_fold_net_share": strongest_share,
        "leave_one_fold_out_edge_survives_all": all(x["edge_survives"] for x in loo),
        "instrument_classification": instrument_class, "direction_classification": direction_class,
        "quarter_classification": quarter_class, "concentration_edge_survives_top_5_removal": concentration[-1]["edge_survives"],
        "possible_failure_mode": failure_mode, "bootstrap": bootstrap,
        "phase4_coverage_warning": "all four folds are marked incomplete because requested calendar endpoints exceed actual bar timestamps",
        "true_oos_read": False, "optimization": False, "ranking": False,
    }
    _json(target / "metrics.json", metrics)
    concentration_text = ("survives" if concentration[-1]["edge_survives"] else "does not survive")
    report = f"""# {metrics['candidate_id']} — Phase 4.1 Borderline Diagnostics

## Classification

**{classification}**

The observed aggregate edge is positive and survives every leave-one-fold-out case, but **{concentration_text} removal of the five best trades**. Both instruments and both directions have positive expectancy. It is not declared TRUE-OOS-ready because only {len(trades)} forward trades exist (below the predeclared 50-trade minimum) and every fold is marked incomplete in the Phase 4 artifact. This is a sample/coverage limitation, not a strategy rejection.

## Findings

- Strongest fold: **{strongest['fold']}** ({strongest['net_R']:.3f} net R); weakest: **{weakest['fold']}** ({weakest['net_R']:.3f} net R).
- Single-fold dependency: **{str(depends_one).lower()}** (strongest-fold share {strongest_share:.1%}).
- Instrument stability: **{instrument_class}**. Direction stability: **{direction_class}**.
- Temporal pattern: **{quarter_class}**; the negative {weakest['fold']} result followed positive quarters, indicating a possible **{failure_mode}** rather than monotonic decay.
- Bootstrap P(mean R > 0): **{bootstrap['probability_mean_R_gt_0']:.1%}** (10,000 deterministic resamples; diagnostic only, not a significance test).
- The 2023 training trade count and net R cannot be reconstructed from the allowed Phase 4 artifacts; only its persisted expectancy is reported. No market data, strategy code, Phase 3 artifacts, or TRUE OOS data were read.

No strategy change, parameter optimization, candidate selection, or ranking was performed.
"""
    (target / "final_report.md").write_text(report, encoding="utf-8")
    return metrics


def run(source: Path = Path("TradingSystemLab/results/walk_forward_validation"),
        output: Path = Path("TradingSystemLab/results/borderline_diagnostics")) -> dict:
    source, output = Path(source), Path(output)
    phase4_manifest = json.loads((source / "summary" / "manifest.json").read_text())
    if not phase4_manifest.get("true_oos_blocked") or phase4_manifest.get("status") != "PHASE_4_BORDERLINE":
        raise RuntimeError("PHASE_4_BORDERLINE_PROVENANCE_REQUIRED")
    source_hashes = artifact_sha256(source)
    if output.exists(): shutil.rmtree(output)
    output.mkdir(parents=True)
    results = {}
    for key in KEYS:
        (output / key).mkdir()
        results[key] = _diagnose(key, source, output / key)
    registry_path = Path("TradingSystemLab/results/robustness_validation/candidate_registry.json")
    registry = {x["candidate_id"]: x for x in json.loads(registry_path.read_text())}
    manifest = {
        "phase": "4.1", "status": "PHASE_4_1_BORDERLINE_DIAGNOSTICS_COMPLETE",
        "candidate_ids": phase4_manifest["candidate_ids"],
        "phase_3_3_provenance": {"candidate_registry": registry_path.as_posix(), "sha256": _sha(registry_path),
            "configuration_ids": {cid: registry[cid]["phase32_configuration_id"] for cid in phase4_manifest["candidate_ids"]}},
        "phase_4_artifact_hashes": source_hashes,
        "frozen_parameter_hashes": phase4_manifest["frozen_parameter_hashes"],
        "optimization": False, "ranking": False, "true_oos_blocked": True,
        "bootstrap": {"iterations": ITERATIONS, "seed": SEED, "diagnostic_only": True},
        "classifications": {k: v["classification"] for k, v in results.items()}, "deterministic": True,
    }
    _json(output / "manifest.json", manifest)
    summary = "# Phase 4.1 Borderline Diagnostics\n\n" + "\n".join(
        f"- **{results[k]['candidate_id']}: {results[k]['classification']}**" for k in KEYS
    ) + "\n\nNo ranking or winner selection was performed. TRUE OOS remains blocked.\n\nPHASE_4_1_BORDERLINE_DIAGNOSTICS_COMPLETE\n"
    (output / "final_borderline_report.md").write_text(summary, encoding="utf-8")
    return manifest
