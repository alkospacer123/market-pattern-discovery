"""Final, pre-registered M5 Session + EMA50 NORMAL TRUE-OOS replay.

The primary OOS tree is an immutable input.  All pre-OOS provenance and the
primary snapshot are verified before any market data is opened.
"""
from __future__ import annotations

from dataclasses import replace
import json
from pathlib import Path
import shutil
from typing import Any, Mapping

import pandas as pd

from . import m5 as primary
from ..core.backtester import Backtester
from ..core.data_loader import DataLoader
from ..core.indicators import ema
from ..core.instrument_specs import get_instrument_spec
from ..core.portfolio import FixedRiskPortfolio
from ..multitimeframe.phase71 import APPROVED_DATA_ROOT, COST_TICKS_PER_SIDE
from ..multitimeframe.phase73 import hash_tree
from ..optimization.phase32 import PARAMETERS, _normalize_backtester
from ..timeframe_analysis.m5_overextension_session_candidate import OUTPUT as EMA_RESEARCH
from ..timeframe_validation.m5_baseline import INSTRUMENTS, TRADE_COLUMNS, causal_four_bar_context

OUTPUT = Path("TradingSystemLab/results/true_oos_validation/M5_EXPERIMENTAL_EMA50_NORMAL")
PRIMARY = primary.OUTPUT
STATUS = "PHASE_M5_EXPERIMENTAL_EMA50_NORMAL_TRUE_OOS_COMPLETE"
CLASSIFICATION = "EXPERIMENTAL_PRE_REGISTERED_COMPARATOR"
CANDIDATE_ID = "M5_SESSION_EMA50_NORMAL"
EMA_DEFINITION = {"normalization": "absolute_close_minus_ema50_divided_by_atr14",
                  "near": "<=0.5", "normal": ">0.5 and <=1.5", "extended": ">1.5"}


def _normal(bar: pd.Series) -> bool:
    """Frozen close-labelled rule; the signal candle is observable at entry."""
    if pd.isna(bar.get("EMA50")) or pd.isna(bar.get("ATR")) or float(bar.ATR) <= 0:
        return False
    distance = abs(float(bar.Close) - float(bar.EMA50)) / float(bar.ATR)
    return .5 < distance <= 1.5


class _ExperimentalT2(primary._OOST2):
    def is_confirmation(self, bar: pd.Series, previous: pd.Series, direction: str) -> bool:
        return primary._eligible(bar.name) and _normal(bar) and super().is_confirmation(bar, previous, direction)


class _ExperimentalT3(primary._SessionT3):
    def calculate_indicators(self, low: pd.DataFrame, high: pd.DataFrame):
        low_result, high_result = super().calculate_indicators(low, high)
        low_result["EMA50"] = ema(low_result.Close, 50)
        return low_result, high_result

    def generate_signal(self, bar: pd.Series, regime: str | None) -> str | None:
        return super().generate_signal(bar, regime) if _normal(bar) else None


def verify_provenance(walk_forward: Path = primary.WALK_FORWARD,
                      primary_oos: Path = PRIMARY,
                      ema_research: Path = EMA_RESEARCH) -> dict[str, Any]:
    """Verify the frozen branch without opening a TRUE-OOS source file."""
    wf_path, oos_path, ema_path = (Path(walk_forward) / "manifest.json",
                                   Path(primary_oos) / "manifest.json",
                                   Path(ema_research) / "manifest.json")
    if not all(p.is_file() for p in (wf_path, oos_path, ema_path)):
        raise RuntimeError("M5_EXPERIMENTAL_FROZEN_PROVENANCE_MISSING")
    wf, oos, research = [json.loads(p.read_text(encoding="utf-8")) for p in (wf_path, oos_path, ema_path)]
    if wf.get("status") != "PHASE_M5_WALK_FORWARD_COMPLETE":
        raise RuntimeError("M5_WALK_FORWARD_PROVENANCE_INVALID")
    if oos.get("status") != "PHASE_M5_TRUE_OOS_COMPLETE":
        raise RuntimeError("M5_PRIMARY_TRUE_OOS_PROVENANCE_INVALID")
    definition = wf.get("candidate_identities", {}).get(CANDIDATE_ID)
    expected = {"weekdays": "Monday-Friday", "entry_start_inclusive": "10:00",
                "entry_end_exclusive": "17:00", "ema50_distance_classification": "normal"}
    if definition != expected or not (Path(walk_forward) / "session_ema50_normal_candidate").is_dir():
        raise RuntimeError("M5_EXPERIMENTAL_COMPARATOR_NOT_FROZEN")
    frozen_ema = research.get("candidate_definitions", {}).get("ema50_distance")
    if frozen_ema != EMA_DEFINITION:
        raise RuntimeError("M5_EMA50_NORMAL_PROVENANCE_CHANGED")
    if wf.get("underlying_candidate_ids") != primary.CANDIDATES or oos.get("underlying_candidate_ids") != primary.CANDIDATES:
        raise RuntimeError("M5_EXPERIMENTAL_CANDIDATE_IDENTITY_MISMATCH")
    frozen = primary.verify_provenance(walk_forward=Path(walk_forward))
    if oos.get("frozen_parameter_hashes") != frozen["parameter_hashes"] or oos.get("strategy_hashes") != frozen["strategy_hashes"]:
        raise RuntimeError("M5_EXPERIMENTAL_FROZEN_HASH_MISMATCH")
    return {**frozen, "wf_manifest": wf, "primary_manifest": oos,
            "ema_research_hash": hash_tree(Path(ema_research)),
            "ema_classification_hash": primary._canonical(frozen_ema),
            "primary_manifest_hash": primary._sha(oos_path),
            "primary_tree_hash": hash_tree(Path(primary_oos)), "definition": expected}


def validate_snapshot(data_root: Path, snapshot: list[dict[str, Any]]) -> dict[str, tuple[pd.DataFrame, list[Path]]]:
    root = Path(data_root).resolve()
    if root != APPROVED_DATA_ROOT.resolve():
        raise ValueError("UNAPPROVED_MARKET_DATA_ROOT")
    loaded = {}
    loader = DataLoader(forbid_true_oos=False)
    for source in snapshot:
        paths = [root / "2026" / source["alias"] / item["name"] for item in source["files"]]
        if any(not p.is_file() for p in paths) or any(primary._sha(p) != item["sha256"] for p, item in zip(paths, source["files"])):
            raise RuntimeError("TRUE_OOS_SOURCE_SNAPSHOT_MISMATCH")
        opened = pd.concat([loader._read(path) for path in paths])
        if not opened.index.is_monotonic_increasing or opened.index.has_duplicates:
            raise ValueError("M5_CANDLE_ORDER_OR_DUPLICATE_VIOLATION")
        bars = loader.close_index(opened, "5min")
        primary.validate_true_oos_candles(bars)
        if (len(bars) != source["bars"] or bars.index.min().isoformat() != source["first_close"] or
                bars.index.max().isoformat() != source["last_close"]):
            raise RuntimeError("TRUE_OOS_SOURCE_COVERAGE_MISMATCH")
        loaded[source["alias"]] = (bars, paths)
    return loaded


def _execute(key: str, registry: dict, alias: str, bars: pd.DataFrame) -> pd.DataFrame:
    params = replace(PARAMETERS[key], **registry["parameters"])
    tick = get_instrument_spec(alias).price_precision
    if key == "T2":
        raw = _ExperimentalT2(params).run(bars, alias, tick_size=tick)
    else:
        raw = Backtester(FixedRiskPortfolio(), cost_ticks_per_side=0, tick_size=tick,
                         allow_true_oos=True).run(_ExperimentalT3(params), alias, bars,
                                                  causal_four_bar_context(bars)).trades
        raw = _normalize_backtester(raw, key)
    if raw.empty:
        return pd.DataFrame(columns=TRADE_COLUMNS)
    frame = raw.copy()
    frame["instrument"] = "USDRUBF" if alias == "Si" else "CNYRUBF"
    frame["strategy"], frame["timeframe"] = key, "M5"
    frame["net_R"] = frame.gross_R.astype(float) - 2 * COST_TICKS_PER_SIDE / frame.initial_risk_ticks.astype(float)
    frame["trade_id"] = [f"{key}-M5-OOS-EMA50-NORMAL-{alias}-{n:06d}" for n in range(1, len(frame) + 1)]
    if not pd.to_datetime(frame.entry_time).map(primary._eligible).all():
        raise RuntimeError("EXPERIMENTAL_SESSION_ENTRY_VIOLATION")
    return frame.sort_values(["exit_time", "instrument", "trade_id"], kind="mergesort").reset_index(drop=True)


def _wf_metrics(walk_forward: Path, key: str) -> dict[str, Any]:
    ledgers = [pd.read_csv(walk_forward / "session_ema50_normal_candidate" / fold / "test_trades.csv")
               for fold in ("WF01", "WF02", "WF03")]
    combined = pd.concat(ledgers, ignore_index=True)
    return primary._metrics(combined if key == "COMBINED" else combined.loc[combined.strategy.eq(key)])


def _report(output: Path, coverage: dict, summaries: dict[str, dict]) -> None:
    combined = summaries["COMBINED"]
    decay = pd.read_csv(output / "COMBINED" / "decay_report.csv").iloc[0]
    lines = ["# M5 Experimental EMA50 NORMAL TRUE OOS", "",
        f"Classification: `{CLASSIFICATION}`", "", f"Coverage: {coverage['start']} through {coverage['end']}.", "",
        "This is the final evaluation of the comparator frozen before primary TRUE OOS. It is not candidate selection and cannot replace the historical primary candidate.", "",
        "## Factual answers", "",
        f"1. Profitable: **{'yes' if combined['net_R'] > 0 else 'no'}** (net {combined['net_R']} R).",
        f"2. Positive expectancy: **{'yes' if combined['expectancy_R'] > 0 else 'no'}** ({combined['expectancy_R']} R).",
        f"3. PF changed from {decay.walk_forward_PF} in walk forward to {decay.true_oos_PF} in TRUE OOS.",
        f"4. Maximum drawdown changed from {decay.walk_forward_max_drawdown_R} R to {decay.true_oos_max_drawdown_R} R.",
        "5–9. Persistence by year, instrument, direction, T2, and T3 is reported without sub-group selection in the adjacent CSV reports.",
        f"10. Top-1/top-5 positive-R shares were {combined['top_1_positive_R_concentration']} / {combined['top_5_positive_R_concentration']}; after removing the top five, net R was {combined['net_R_without_top5']} and PF was {combined['PF_without_top5']}.",
        f"11. The hypothesis **{'survived' if combined['net_R'] > 0 and combined['expectancy_R'] > 0 else 'did not survive'}** unseen data by the factual profitability/expectancy criterion.", "",
        "No optimization, ranking, EMA threshold change, or candidate reselection occurred. The primary M5 result remains unchanged.", "", STATUS, "", "M5 RESEARCH IS CLOSED.", ""]
    (output / "experimental_true_oos_report.md").write_text("\n".join(lines), encoding="utf-8")


def run(data_root: Path = APPROVED_DATA_ROOT, output: Path = OUTPUT, *, market_data: Mapping[str, pd.DataFrame] | None = None) -> dict[str, Any]:
    frozen = verify_provenance()
    primary_before = frozen["primary_tree_hash"]
    snapshot = frozen["primary_manifest"]["true_oos_source_hashes"]
    if market_data is None:
        loaded = validate_snapshot(Path(data_root), snapshot)
        bars = {alias: value[0] for alias, value in loaded.items()}
    else:
        bars = {alias: market_data[alias].copy() for _, alias in INSTRUMENTS}
        for frame in bars.values(): primary.validate_true_oos_candles(frame)
    first, last = min(x.index.min() for x in bars.values()), max(x.index.max() for x in bars.values())
    coverage = {"start": first.isoformat(), "end": last.isoformat()}
    if market_data is None and coverage != frozen["primary_manifest"]["true_oos_coverage"]:
        raise RuntimeError("TRUE_OOS_COVERAGE_DIFFERS_FROM_PRIMARY")
    frames = {}
    for key in primary.CANDIDATES:
        frames[key] = pd.concat([_execute(key, frozen["registries"][key], alias, bars[alias])
                                 for _, alias in INSTRUMENTS], ignore_index=True).sort_values(
                                     ["exit_time", "instrument", "trade_id"], kind="mergesort").reset_index(drop=True)
    frames["COMBINED"] = pd.concat([frames["T2"], frames["T3"]], ignore_index=True).sort_values(
        ["exit_time", "strategy", "instrument", "trade_id"], kind="mergesort").reset_index(drop=True)
    output = Path(output)
    if output.exists(): shutil.rmtree(output)
    output.mkdir(parents=True)
    days = max(1., (last - first).total_seconds() / 86400 + 1)
    summaries, comparison = {}, []
    for key in ("T2", "T3", "COMBINED"):
        summaries[key] = primary._write_reports(output / key, frames[key], key, CANDIDATE_ID, None, days)
        wf, metric = _wf_metrics(primary.WALK_FORWARD, key), summaries[key]
        wf_frequency, oos_frequency = wf["trades"] / (365.25 * 1.5) * 365.2425, metric["trades"] / days * 365.2425
        primary._csv(output / key / "decay_report.csv", [{
            "walk_forward_expectancy_R": wf["expectancy_R"], "true_oos_expectancy_R": metric["expectancy_R"], "expectancy_decay_R": metric["expectancy_R"] - wf["expectancy_R"],
            "walk_forward_PF": wf["PF"], "true_oos_PF": metric["PF"], "PF_decay": metric["PF"] - wf["PF"],
            "walk_forward_max_drawdown_R": wf["max_drawdown_R"], "true_oos_max_drawdown_R": metric["max_drawdown_R"], "drawdown_expansion_R": abs(metric["max_drawdown_R"]) - abs(wf["max_drawdown_R"]),
            "walk_forward_trades_per_year": wf_frequency, "true_oos_trades_per_year": oos_frequency, "trade_frequency_decay_per_year": oos_frequency - wf_frequency}])
        comparison.append({"candidate": CANDIDATE_ID, "scope": key, **metric})
    primary._csv(output / "comparison.csv", comparison)
    _report(output, coverage, summaries)
    if hash_tree(PRIMARY) != primary_before:
        raise RuntimeError("PRIMARY_M5_TRUE_OOS_ARTIFACTS_MODIFIED")
    flags = {name: False for name in ("primary_candidate", "production_candidate_selection", "optimization_performed", "ranking_performed", "parameter_change", "strategy_change", "session_change", "ema_threshold_change", "candidate_reselection", "true_oos_used_for_training", "true_oos_used_for_optimization", "true_oos_used_for_selection", "primary_m5_true_oos_artifacts_modified")}
    manifest = {"phase": "M5_EXPERIMENTAL_EMA50_NORMAL_TRUE_OOS", "status": STATUS, "timeframe": "M5",
        "classification": CLASSIFICATION, "candidate_id": CANDIDATE_ID, "candidate_definition": frozen["definition"],
        "ema50_normal_provenance": EMA_DEFINITION, "frozen_ema_classification_hash": frozen["ema_classification_hash"],
        "underlying_candidate_ids": primary.CANDIDATES, "candidate_hashes": frozen["registry_hashes"],
        "parameter_hashes": frozen["parameter_hashes"], "strategy_hashes": frozen["strategy_hashes"],
        "m5_walk_forward_artifact_hash": frozen["walk_forward_hash"], "primary_m5_true_oos_manifest_hash": frozen["primary_manifest_hash"],
        "primary_m5_true_oos_tree_hash_before_and_after": primary_before,
        "true_oos_source_hashes": snapshot, "true_oos_coverage": coverage,
        "transaction_cost_model": frozen["primary_manifest"]["transaction_cost_model"], "deterministic": True,
        "pre_registered_before_true_oos": True, **flags}
    manifest["artifact_tree_sha256"] = primary.artifact_sha256(output, {"manifest.json"})
    primary._json(output / "manifest.json", manifest)
    return {"status": STATUS, "coverage": coverage, "summaries": summaries,
            "artifact_tree_sha256": manifest["artifact_tree_sha256"], "primary_tree_hash": primary_before}
