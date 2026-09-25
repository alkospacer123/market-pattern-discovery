"""Independent, read-only, fail-closed audit of committed v3 perpetual Phase 5 evidence.

This module deliberately does not import the Phase 5 runner.  Its calculations
are a second implementation over committed CSV/JSON artifacts only.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any, Mapping

import numpy as np
import pandas as pd


OUTPUT_ROOT = Path("TradingSystemLab/results/perpetual_v3/true_oos")
REGISTRY_PATH = Path("TradingSystemLab/results/perpetual_v3/phase3_candidate_freeze/candidate_registry.json")
TRUE_OOS_START = pd.Timestamp("2025-01-01", tz="Europe/Moscow")
STUDIES = (("T2", "M30"), ("T2", "H1"), ("T3", "M30"), ("T3", "H1"))
INSTRUMENTS = ("USDRUBF", "CNYRUBF", "GLDRUBF", "IMOEXF")
BOOTSTRAP_ITERATIONS = 10_000
BOOTSTRAP_SEED = 5_102_025
PHASE5_MERGE = "d5aa616186c2750d5f0b0b9c60eddbf5d096c98f"
STRATEGY_HASHES = {
    "T2": "376df085cfda85eefccb31343aad40ed4fbb1078f1314496472a3a4ac9507774",
    "T3": "840dd3b2cda43fa00259445cd0a22ace6d82e677f4c793028ccc8126f9ad9a8c",
}
PROTECTED = (
    ("f8ee11841eedb11cb6ec98debc74ad8bc8c0c8a9", "TradingSystemLab/results/perpetual_v3/baseline"),
    ("272eabd5a4261a18a763356964b82b4b5b5673ea", "TradingSystemLab/results/perpetual_v3/optimization"),
    ("f123f1468c6b5f1f0719154aba73d4635e6de0ea", "TradingSystemLab/results/perpetual_v3/phase3_candidate_freeze"),
    ("d684bfb7f321c2183eab36159c77fa687bd6092b", "TradingSystemLab/results/perpetual_v3/robustness"),
    ("d5aa616186c2750d5f0b0b9c60eddbf5d096c98f", "TradingSystemLab/results/perpetual_v3/walk_forward"),
)
REQUIRED = {"trades.csv", "yearly_report.csv", "quarterly_report.csv", "instrument_report.csv",
            "direction_report.csv", "monthly_report.csv", "concentration_report.csv", "mae_mfe_report.csv",
            "bootstrap_report.csv", "metrics.json", "manifest.json", "final_report.md"}
STALE_CURRENT_CLAIMS = (
    "Phase 5 TRUE OOS is the next permitted action",
    "Phase 5 TRUE OOS is the next permitted stage",
    "Execute Phase 5 TRUE OOS",
    "TRUE OOS 2025+ remains sealed",
    "Phase 5 was not executed",
)


def req(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def close(actual: Any, expected: Any) -> bool:
    return bool((pd.isna(actual) and pd.isna(expected)) or
                np.isclose(float(actual), float(expected), rtol=1e-8, atol=1e-10))


def independent_summary(values: pd.Series) -> dict[str, Any]:
    """Reconstruct original unified R metrics without production helpers."""
    x = pd.Series(values, dtype=float).reset_index(drop=True)
    winners, losers = x[x > 0], x[x < 0]
    gains, losses = float(winners.sum()), float(-losers.sum())
    curve = pd.concat([pd.Series([0.0]), x.cumsum()], ignore_index=True)
    drawdown = float((curve - curve.cummax()).min())
    net = float(x.sum())
    return {
        "total_trades": len(x),
        "PF": gains / losses if losses else None,
        "expectancy": float(x.mean()) if len(x) else None,
        "net_R": net,
        "max_drawdown": drawdown,
        "win_rate": float((x > 0).mean()) if len(x) else None,
        "average_win": float(winners.mean()) if len(winners) else None,
        "average_loss": float(losers.mean()) if len(losers) else None,
        "recovery_factor": net / abs(drawdown) if drawdown else None,
    }


def independent_bootstrap(values: pd.Series) -> dict[str, Any]:
    """Reconstruct the predeclared IID bootstrap with a local deterministic RNG."""
    x = np.asarray(values, dtype=float)
    req(len(x) > 0, "BOOTSTRAP_EMPTY")
    means = np.random.default_rng(BOOTSTRAP_SEED).choice(
        x, size=(BOOTSTRAP_ITERATIONS, len(x)), replace=True).mean(axis=1)
    quantiles = np.quantile(means, [.025, .05, .50, .95, .975])
    return {"iterations": BOOTSTRAP_ITERATIONS, "seed": BOOTSTRAP_SEED, "trades": len(x),
            "mean_R_2.5%": quantiles[0], "mean_R_5%": quantiles[1],
            "mean_R_50%": quantiles[2], "mean_R_95%": quantiles[3],
            "mean_R_97.5%": quantiles[4],
            "probability_mean_R_gt_0": float((means > 0).mean())}


def independent_concentration(values: pd.Series) -> dict[str, Any]:
    """Directly remove the best positive trades and recompute affected metrics."""
    x = pd.Series(values, dtype=float)
    positive = x[x > 0].sort_values(ascending=False)
    total_positive = float(positive.sum())
    result: dict[str, Any] = {"total_positive_R": total_positive}
    for n in (1, 3, 5, 10):
        result[f"top_{n}_positive_R_share"] = (
            float(positive.head(n).sum() / total_positive) if total_positive else None)
    for n, label in ((1, "best_trade"), (3, "top3"), (5, "top5")):
        remaining = x.drop(positive.head(n).index)
        rebuilt = independent_summary(remaining)
        result[f"net_R_without_{label}"] = rebuilt["net_R"]
        result[f"PF_R_C1_without_{label}"] = rebuilt["PF"]
        result[f"expectancy_C1_without_{label}"] = rebuilt["expectancy"]
    return result


def independent_classify(overall: Mapping[str, Any], probability: float, observed: int,
                         positive: int, instrument_gate: bool, direction_gate: bool,
                         net_without_top5: float) -> str:
    passed = (overall["total_trades"] >= 50 and overall["expectancy"] > 0 and
              probability >= .95 and observed > 0 and positive / observed >= .60 and
              instrument_gate and direction_gate and net_without_top5 > 0)
    failed = overall["expectancy"] <= 0 or probability <= .50
    return "PASS" if passed else ("FAIL" if failed else "BORDERLINE")


def _compare_summary(actual: Mapping[str, Any], expected: Mapping[str, Any], label: str) -> None:
    for key, value in expected.items():
        req(key in actual and close(actual[key], value), f"{label}:{key}")


def _git_tree_checks() -> None:
    for commit, path in PROTECTED:
        result = subprocess.run(["git", "diff", "--quiet", commit, "--", path], check=False)
        req(result.returncode == 0, f"PROTECTED_TREE_CHANGED:{path}")


def _documentation_checks() -> None:
    for path in (Path("TradingSystemLab/CURRENT_STATE.md"),
                 Path("TradingSystemLab/PROJECT_CONTEXT.md"), Path("TradingSystemLab/ROADMAP.md")):
        text = path.read_text(encoding="utf-8")
        for stale in STALE_CURRENT_CLAIMS:
            req(stale.lower() not in text.lower(), f"STALE_DOCUMENTATION:{path}:{stale}")
        req("complete as a procedure" in text.lower(), f"INCOMPLETE_DOCUMENTATION:{path}")


def audit(root: Path = OUTPUT_ROOT, *, check_git_trees: bool = True) -> dict[str, Any]:
    """Audit artifacts without writing files, loading market data, or running a strategy."""
    root = Path(root)
    if check_git_trees:
        _git_tree_checks()
    _documentation_checks()
    registry_raw = REGISTRY_PATH.read_bytes()
    candidates = json.loads(registry_raw)["candidates"]
    req([(x["strategy"], x["timeframe"]) for x in candidates] == list(STUDIES),
        "FOUR_FROZEN_IDENTITIES_INVALID")

    manifest = json.loads((root / "summary/manifest.json").read_text(encoding="utf-8"))
    req(manifest["status"] in ("PENDING_AUDIT", "V3_PERPETUAL_PHASE_5_TRUE_OOS_COMPLETE"), "PHASE5_STATUS_INVALID")
    req(manifest["candidate_registry_sha256"] == hashlib.sha256(registry_raw).hexdigest(),
        "REGISTRY_HASH_INVALID")
    req(manifest["candidate_count"] == 4 and manifest["development_rows_admitted"] == 0 and
        manifest["cold_start"] and manifest["start_state"] == "FLAT", "OOS_LIFECYCLE_INVALID")
    req(manifest["C1_only"] and manifest["normalized_research_tick"] == .001 and
        not any(manifest[x] for x in ("optimization", "ranking", "candidate_replacement")),
        "RESEARCH_CONTRACT_INVALID")

    for strategy, source in (("T2", Path("TradingSystemLab/strategies/trend/T2_Trend_Pullback.py")),
                             ("T3", Path("TradingSystemLab/strategies/trend/T3_MTF_Trend.py"))):
        req(hashlib.sha256(source.read_bytes()).hexdigest() == STRATEGY_HASHES[strategy],
            f"STRATEGY_HASH_INVALID:{strategy}")

    classes: dict[str, str] = {}
    for item in candidates:
        strategy, timeframe = item["strategy"], item["timeframe"]
        target = root / strategy / timeframe
        req({p.name for p in target.iterdir()} == REQUIRED, f"ARTIFACT_SET_INVALID:{strategy}/{timeframe}")
        trades = pd.read_csv(target / "trades.csv")
        metrics = json.loads((target / "metrics.json").read_text(encoding="utf-8"))
        study = json.loads((target / "manifest.json").read_text(encoding="utf-8"))
        req(not trades.trade_id.duplicated().any(), f"DUPLICATE_TRADE_ID:{strategy}/{timeframe}")
        req(pd.to_datetime(trades.entry_time, utc=True).ge(TRUE_OOS_START.tz_convert("UTC")).all(),
            f"PRE_OOS_ENTRY:{strategy}/{timeframe}")
        req(pd.to_datetime(trades.exit_time, utc=True).ge(TRUE_OOS_START.tz_convert("UTC")).all(),
            f"PRE_OOS_EXIT:{strategy}/{timeframe}")
        expected_context = "none" if strategy == "T2" else (
            f"four completed non-overlapping {timeframe} bars; local-day reset")
        req(study["candidate_id"] == item["candidate_id"] and
            study["phase2_configuration_id"] == item["phase2_configuration_id"] and
            study["frozen_parameter_hash"] == item["parameter_hash"],
            f"FROZEN_IDENTITY_INVALID:{strategy}/{timeframe}")
        req(study["cold_start"] and study["start_state"] == "FLAT" and
            study["development_rows_admitted"] == 0 and not study["development_state_reused"] and
            study["C1_only"] and study["normalized_research_tick"] == .001 and
            not any(study[x] for x in ("optimization", "ranking", "candidate_replacement")) and
            study["execution_context"] == expected_context, f"STUDY_CONTRACT_INVALID:{strategy}/{timeframe}")

        overall = independent_summary(trades.net_R_C1)
        _compare_summary(metrics["aggregate"], overall, f"AGGREGATE:{strategy}/{timeframe}")
        exits = pd.to_datetime(trades.exit_time, utc=True)
        exit_quarters = exits.dt.tz_localize(None).dt.to_period("Q").astype(str)
        grouping = (("yearly_report.csv", "year", exits.dt.year, sorted(exits.dt.year.unique())),
                    ("quarterly_report.csv", "quarter", exit_quarters, sorted(exit_quarters.unique())),
                    ("monthly_report.csv", "month", exits.dt.tz_localize(None).dt.to_period("M").astype(str), sorted(exits.dt.tz_localize(None).dt.to_period("M").astype(str).unique())),
                    ("instrument_report.csv", "symbol", trades.symbol, list(INSTRUMENTS)),
                    ("direction_report.csv", "direction", trades.direction, ["LONG", "SHORT"]))
        reports: dict[str, pd.DataFrame] = {}
        for filename, column, keys, expected_order in grouping:
            report = pd.read_csv(target / filename)
            reports[filename] = report
            req(report[column].tolist() == expected_order, f"GROUP_ORDER:{filename}:{strategy}/{timeframe}")
            for _, row in report.iterrows():
                rebuilt = independent_summary(trades.loc[keys.eq(row[column]), "net_R_C1"])
                _compare_summary(row, rebuilt, f"{filename}:{row[column]}:{strategy}/{timeframe}")

        concentration = independent_concentration(trades.net_R_C1)
        concentration_row = pd.read_csv(target / "concentration_report.csv").iloc[0]
        for key in concentration_row.index:
            req(key in concentration and close(concentration_row[key], concentration[key]),
                f"CONCENTRATION:{key}:{strategy}/{timeframe}")
        req(close(metrics["net_R_without_top5"], concentration["net_R_without_top5"]),
            f"METRICS_TOP5:{strategy}/{timeframe}")

        boot = independent_bootstrap(trades.net_R_C1)
        boot_row = pd.read_csv(target / "bootstrap_report.csv").iloc[0]
        for key, value in boot.items():
            req(close(boot_row[key], value), f"BOOTSTRAP:{key}:{strategy}/{timeframe}")
        req(close(metrics["bootstrap_probability_mean_R_gt_0"], boot["probability_mean_R_gt_0"]),
            f"METRICS_BOOTSTRAP:{strategy}/{timeframe}")

        quarterly = reports["quarterly_report.csv"]
        instruments = reports["instrument_report.csv"]
        directions = reports["direction_report.csv"]
        observed = int((quarterly.total_trades > 0).sum())
        positive = int(((quarterly.total_trades > 0) & (quarterly.expectancy > 0)).sum())
        instrument_gate = bool((instruments.loc[instruments.total_trades > 0, "expectancy"] >= 0).all())
        direction_gate = bool((directions.loc[directions.total_trades > 0, "expectancy"] >= 0).all())
        req(metrics["observed_quarters"] == observed and
            metrics["positive_observed_quarters"] == positive and
            close(metrics["positive_quarter_share"], positive / observed) and
            metrics["instrument_gate"] == instrument_gate and
            metrics["direction_gate"] == direction_gate,
            f"CLASSIFICATION_INPUT_INVALID:{strategy}/{timeframe}")
        verdict = independent_classify(overall, boot["probability_mean_R_gt_0"], observed, positive,
                                       instrument_gate, direction_gate,
                                       concentration["net_R_without_top5"])
        req(verdict == metrics["classification"] == study["classification"],
            f"CLASSIFICATION_INVALID:{strategy}/{timeframe}")
        classes[f"{strategy}/{timeframe}"] = verdict

    expected_classes = {"T2/M30":"BORDERLINE","T2/H1":"BORDERLINE","T3/M30":"PASS","T3/H1":"PASS"}
    req(classes == expected_classes and manifest["classifications"] == expected_classes,
        "ROOT_CLASSIFICATIONS_INVALID")
    hashes = {path: hashlib.sha256((root / path).read_bytes()).hexdigest()
              for path in manifest["artifact_sha256"]}
    req(hashes == manifest["artifact_sha256"], "ARTIFACT_HASH_INVALID")
    return {"status": "V3_PERPETUAL_PHASE_5_TRUE_OOS_AUDIT_PASSED", "classifications": classes}


if __name__ == "__main__":
    print(json.dumps(audit(), sort_keys=True))
