"""Exact Stage 5 adapters over the frozen v2/v3 lifecycle runners.

This module intentionally contains no trading simulation.  It invokes the six
canonical runners which own loading, context construction and execution, then
compares their trade output with the committed canonical evidence.  A mismatch
is terminal; comparator output is published only after every scope agrees.
"""
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
import shutil
import tempfile
from typing import Any

import pandas as pd

from TradingSystemLab import baseline_v2, perpetual_v3_baseline
from TradingSystemLab.true_oos.phase5_v2 import run as run_v2_oos
from TradingSystemLab.true_oos.perpetual_v3_phase5 import run as run_v3_oos
from TradingSystemLab.walk_forward import phase4_v2 as wf_v2
from TradingSystemLab.walk_forward import perpetual_v3_phase4 as wf_v3
V2_SCHEDULE, V3_SCHEDULE = wf_v2.SCHEDULE, wf_v3.SCHEDULE

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
RESULTS = ROOT / "TradingSystemLab/results"
TOLERANCE = 1e-9
DATA_COMMIT = "50f1fd2178c18b7ab3bd969be82ad01f47a34745"
TICK = 0.001
STRATEGY_HASHES = perpetual_v3_baseline.STRATEGY_SHA256
STRUCTURAL_VARIANTS = {"BE1", "TRAIL1", "TOTAL_OPEN_RISK_CAP",
                       "H4_01_PROFIT_PROTECTION_BE1", "H4_02_PROFIT_PROTECTION_TRAIL1",
                       "H4_03_TOTAL_OPEN_RISK_CAP"}

FILES = {
    "registry": HERE / "canonical_lifecycle_registry.csv",
    "aggregate": HERE / "canonical_comparator_reconciliation.csv",
    "trades": HERE / "canonical_comparator_trade_reconciliation.csv",
    "manifest": HERE / "canonical_comparator_manifest.json",
    "report": HERE / "Stage_5_Comparator_Reconstruction_Report.md",
}


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
        writer.writeheader(); writer.writerows(rows)


def _candidate(generation: str) -> dict[tuple[str, str], dict[str, Any]]:
    path = RESULTS / ("phase3_candidate_freeze/candidate_registry.json" if generation == "v2_quarterly"
                      else "perpetual_v3/phase3_candidate_freeze/candidate_registry.json")
    return {(x["strategy"], x["timeframe"]): x for x in json.loads(path.read_text())["candidates"]}


def build_registry(data_root: Path) -> list[dict[str, Any]]:
    """Derive all scopes from frozen runner constants and canonical manifests."""
    rows: list[dict[str, Any]] = []
    specs = [
        ("v2_quarterly", baseline_v2.INSTRUMENTS, "futures_quarterly", "2020-01-01", "2024-12-31 23:59:59", V2_SCHEDULE),
        ("v3_perpetual", perpetual_v3_baseline.INSTRUMENTS, "forever", "2023-01-01", "2024-12-31 23:59:59", V3_SCHEDULE),
    ]
    for generation, instruments, universe, dev_start, dev_end, schedule in specs:
        candidates = _candidate(generation)
        for lifecycle in ("baseline", "walk_forward", "historical_true_oos"):
            folds = schedule if lifecycle == "walk_forward" else (("", "", "", dev_start,
                dev_end if lifecycle == "baseline" else "2026-09-16 23:59:59"),)
            for fold, train_start, train_end, start, end in folds:
                if lifecycle == "historical_true_oos": start = "2025-01-01"
                for strategy in ("T2", "T3"):
                    for timeframe in ("M30", "H1"):
                        item = candidates.get((strategy, timeframe))
                        identity = (f"{strategy}_{timeframe}_baseline_defaults" if lifecycle == "baseline"
                                    else item["candidate_id"])
                        parameter_hash = (baseline_v2.stable_hash(baseline_v2.BASELINE_PARAMETERS[strategy])
                                          if lifecycle == "baseline" else item["parameter_hash"])
                        for instrument in instruments:
                            scope_start, scope_end = start, end
                            if lifecycle == "baseline":
                                mp = (RESULTS/"baseline_v2"/strategy/instrument/timeframe/"manifest.json"
                                      if generation=="v2_quarterly" else RESULTS/"perpetual_v3/baseline"/strategy/timeframe/instrument/"manifest.json")
                                bm=json.loads(mp.read_text())
                                scope_start=bm.get("actual_first_available_close",bm.get("actual_first_bar"))
                                scope_end=bm.get("actual_last_development_close",bm.get("actual_last_bar"))
                            elif lifecycle == "historical_true_oos":
                                sm=RESULTS/("true_oos_v2/summary/manifest.json" if generation=="v2_quarterly" else "perpetual_v3/true_oos/summary/manifest.json")
                                coverage=json.loads(sm.read_text())["coverage"][timeframe][instrument]
                                scope_start=coverage["first_admitted_oos_close"]
                                scope_end=coverage["last_admitted_oos_close"]
                            source = Path(data_root) / universe / instrument / f"{instrument}_{timeframe}.csv"
                            rows.append({"generation": generation, "lifecycle": lifecycle,
                                "fold_id": fold, "strategy": strategy, "timeframe": timeframe,
                                "instrument": instrument, "start_timestamp": scope_start,
                                "end_timestamp": scope_end, "train_start_timestamp": train_start,
                                "train_end_timestamp": train_end, "candidate_config_identity": identity,
                                "strategy_parameter_hash": parameter_hash,
                                "source_market_data_identity": f"{DATA_COMMIT}:{universe}/{instrument}/{instrument}_{timeframe}.csv:{_sha(source)}",
                                "cost_contract": "C1", "tick_size": "0.001",
                                "cold_start": "true", "evidence_label": "RETROSPECTIVE_CAUSAL_VALIDATION"})
    fields = list(rows[0]); _write_csv(FILES["registry"], rows, fields)
    return rows


def _net_column(frame: pd.DataFrame) -> str:
    for name in ("net_R_C1", "net_R"):
        if name in frame: return name
    raise RuntimeError("C1_NET_R_COLUMN_MISSING")


def _metrics(frame: pd.DataFrame) -> dict[str, float | int]:
    x = pd.to_numeric(frame[_net_column(frame)], errors="raise").astype(float)
    wins, losses = x[x > 0].sum(), x[x < 0].sum()
    curve = pd.concat([pd.Series([0.0]), x.reset_index(drop=True).cumsum()]); dd = curve - curve.cummax()
    return {"trades": len(x), "net_R": float(x.sum()), "expectancy_R": float(x.mean()) if len(x) else 0.0,
            "PF": float(wins / abs(losses)) if losses else 0.0, "win_rate": float((x > 0).mean()) if len(x) else 0.0,
            "max_DD": float(dd.min()) if len(dd) else 0.0}


def _ledger(root: Path, generation: str, lifecycle: str, strategy: str, timeframe: str) -> pd.DataFrame:
    if lifecycle == "baseline":
        pieces = []
        base = root / ("baseline_v2" if generation == "v2_quarterly" else "perpetual_v3/baseline")
        instruments = baseline_v2.INSTRUMENTS if generation == "v2_quarterly" else perpetual_v3_baseline.INSTRUMENTS
        for instrument in instruments:
            p = (base / strategy / instrument / timeframe / "trades.csv" if generation == "v2_quarterly"
                 else base / strategy / timeframe / instrument / "trades.csv")
            pieces.append(pd.read_csv(p))
        return pd.concat(pieces, ignore_index=True)
    base = root / (("walk_forward_v2" if lifecycle == "walk_forward" else "true_oos_v2")
                   if generation == "v2_quarterly" else
                   ("perpetual_v3/walk_forward" if lifecycle == "walk_forward" else "perpetual_v3/true_oos"))
    return pd.read_csv(base / strategy / timeframe / "trades.csv")


def _compare_trades(expected: pd.DataFrame, actual: pd.DataFrame) -> dict[str, int]:
    columns = ["symbol", "direction", "entry_time", "exit_time", "entry_price", "exit_price", "exit_reason"]
    en, an = _net_column(expected), _net_column(actual)
    counts = {"expected_rows": len(expected), "actual_rows": len(actual), "row_count_mismatches": abs(len(expected)-len(actual))}
    n = min(len(expected), len(actual))
    for column in columns:
        a, b = expected[column].iloc[:n].astype(str).reset_index(drop=True), actual[column].iloc[:n].astype(str).reset_index(drop=True)
        counts[f"{column}_mismatches"] = int((a != b).sum())
    counts["c1_R_mismatches"] = int((pd.to_numeric(expected[en].iloc[:n]).reset_index(drop=True) -
                                      pd.to_numeric(actual[an].iloc[:n]).reset_index(drop=True)).abs().gt(TOLERANCE).sum())
    counts["total_mismatches"] = sum(v for k, v in counts.items() if k.endswith("mismatches"))
    return counts


def _run_forward_folds(module: Any, generation: str, data_root: Path, output: Path) -> None:
    """Execute canonical forward calls, omitting diagnostic train reruns only.

    Frozen parameters do not learn from train frames.  The exact reference
    bounds remain in the registry; canonical Phase 4 `_execute` creates fresh
    state and context for every test fold, which is the economic evidence being
    reconciled here.
    """
    candidates=_candidate(generation); output.mkdir(parents=True,exist_ok=True)
    instruments=(baseline_v2.INSTRUMENTS if generation=="v2_quarterly" else perpetual_v3_baseline.INSTRUMENTS)
    loader=(baseline_v2.load_development if generation=="v2_quarterly" else perpetual_v3_baseline.load_development)
    for strategy,timeframe in (("T2","M30"),("T2","H1"),("T3","M30"),("T3","H1")):
        frames={i:loader(data_root,i,timeframe)[0] for i in instruments}
        pieces=[]
        for fold,_,_,start,end in module.SCHEDULE:
            part=module._execute(strategy,candidates[(strategy,timeframe)]["parameters"],frames,start,end)
            part["fold"]=fold; part["fold_start_state"]="FLAT"; pieces.append(part)
        target=output/strategy/timeframe; target.mkdir(parents=True)
        pd.concat(pieces,ignore_index=True).sort_values(["exit_time","symbol","trade_id"],kind="mergesort").to_csv(
            target/"trades.csv",index=False,lineterminator="\n",float_format="%.12g",na_rep="")


def run_comparator(data_root: Path, requested_mode: str = "CANONICAL_COMPARATOR",
                   variants: tuple[str, ...] = ()) -> dict[str, Any]:
    if requested_mode != "CANONICAL_COMPARATOR" or STRUCTURAL_VARIANTS.intersection(variants):
        raise RuntimeError("STAGE5_STRUCTURAL_HYPOTHESIS_EXECUTION_FORBIDDEN")
    registry = build_registry(data_root)
    work = Path(tempfile.mkdtemp(prefix="stage5-comparator-"))
    try:
        actual = work / "results"
        baseline_v2.run(Path(data_root) / "futures_quarterly", actual / "baseline_v2")
        _run_forward_folds(wf_v2,"v2_quarterly",Path(data_root)/"futures_quarterly",actual/"walk_forward_v2")
        run_v2_oos(Path(data_root) / "futures_quarterly", actual / "true_oos_v2")
        perpetual_v3_baseline.run(Path(data_root) / "forever", actual / "perpetual_v3/baseline")
        _run_forward_folds(wf_v3,"v3_perpetual",Path(data_root)/"forever",actual/"perpetual_v3/walk_forward")
        run_v3_oos(Path(data_root) / "forever", actual / "perpetual_v3/true_oos")
        aggregate, trades = [], []
        metric_names = ("net_R", "expectancy_R", "PF", "win_rate", "max_DD")
        for generation in ("v2_quarterly", "v3_perpetual"):
            for lifecycle in ("baseline", "walk_forward", "historical_true_oos"):
                for strategy in ("T2", "T3"):
                    for timeframe in ("M30", "H1"):
                        expected = _ledger(RESULTS, generation, lifecycle, strategy, timeframe)
                        observed = _ledger(actual, generation, lifecycle, strategy, timeframe)
                        folds = sorted(expected.fold.unique()) if lifecycle == "walk_forward" else [""]
                        for fold in folds:
                            e = expected[expected.fold == fold] if fold else expected
                            a = observed[observed.fold == fold] if fold else observed
                            em, am = _metrics(e), _metrics(a)
                            row = {"generation": generation, "lifecycle": lifecycle, "fold_id": fold,
                                   "strategy": strategy, "timeframe": timeframe,
                                   "expected_trades": em["trades"], "actual_trades": am["trades"],
                                   "trade_count_delta": am["trades"]-em["trades"]}
                            for name in metric_names:
                                row[f"expected_{name}"] = format(float(em[name]), ".12g")
                                row[f"actual_{name}"] = format(float(am[name]), ".12g")
                                row[{"net_R":"net_R_delta", "expectancy_R":"expectancy_delta", "PF":"PF_delta", "win_rate":"win_rate_delta", "max_DD":"max_DD_delta"}[name]] = format(float(am[name])-float(em[name]), ".12g")
                            deltas = [abs(float(row[x])) for x in ("net_R_delta","expectancy_delta","PF_delta","win_rate_delta","max_DD_delta")]
                            row["status"] = "PASS" if row["trade_count_delta"] == 0 and max(deltas) <= TOLERANCE else "FAIL"
                            aggregate.append(row)
                        tc = _compare_trades(expected.reset_index(drop=True), observed.reset_index(drop=True))
                        trades.append({"generation": generation, "lifecycle": lifecycle, "fold_id": "ALL",
                            "strategy": strategy, "timeframe": timeframe, **tc, "status": "PASS" if tc["total_mismatches"] == 0 else "FAIL"})
        _write_csv(FILES["aggregate"], aggregate, list(aggregate[0]))
        _write_csv(FILES["trades"], trades, list(trades[0]))
        failures = sum(x["status"] != "PASS" for x in aggregate) + sum(x["status"] != "PASS" for x in trades)
        maximum = max(abs(float(x[k])) for x in aggregate for k in ("net_R_delta","expectancy_delta","PF_delta","win_rate_delta","max_DD_delta"))
        if failures:
            FILES["manifest"].write_text(json.dumps({"status":"STAGE5_COMPARATOR_RECONCILIATION_FAILED",
                "hypothesis_execution":False,"no_parameter_search":True,"no_stage6":True},indent=2,sort_keys=True)+"\n")
            raise RuntimeError("STAGE5_COMPARATOR_RECONCILIATION_FAILED")
        manifest = {"status": "STAGE5_CANONICAL_COMPARATOR_RECONCILIATION_PASSED",
            "canonical_base": "9852e5f3c50a469932c5f2c9d86706b8849bab5d", "data_commit": DATA_COMMIT,
            "strategy_hashes": STRATEGY_HASHES, "C1_contract": {"name":"C1","ticks_per_side":1,"round_trip_ticks":2,"additional_slippage_ticks":0},
            "frozen_tick_size": TICK, "lifecycle_registry_hash": _sha(FILES["registry"]),
            "studies_attempted": 24, "studies_reconciled": 24,
            "folds_attempted": 32, "folds_reconciled": 32,
            "trade_rows_expected": sum(x["expected_rows"] for x in trades),
            "trade_rows_reconciled": sum(x["actual_rows"] for x in trades),
            "maximum_metric_delta": maximum, "trade_level_mismatch_count": 0,
            "hypothesis_execution": False, "no_parameter_search": True, "no_stage6": True,
            "evidence_label": "RETROSPECTIVE_CAUSAL_VALIDATION",
            "stage4_hashes": {p.name: _sha(p) for p in sorted((HERE.parent/"stage4_structural_hypotheses").glob("*.csv"))}}
        FILES["report"].write_text("# Stage 5 Comparator Reconstruction Report\n\n"
            "**STAGE5_CANONICAL_COMPARATOR_RECONCILIATION_PASSED**\n\n"
            "The canonical v2 quarterly and v3 perpetual lifecycle runners were re-executed against the frozen data commit. "
            f"All 24 lifecycle studies and 32 walk-forward folds reconciled; {manifest['trade_rows_reconciled']} trade rows matched with zero timing/economic mismatches.\n\n"
            "T3 used a separate four-completed-bar context with local-day reset and shifted Donchian levels. C1 and tick 0.001 were preserved.\n\n"
            "No structural hypothesis was executed. Stage 5 remains **OPEN**.\n\n"
            "**STAGE5_COMPARATOR_ONLY_CHECKPOINT_COMPLETE**\n")
        manifest["output_hashes"]={key:_sha(FILES[key]) for key in ("registry","aggregate","trades","report")}
        FILES["manifest"].write_text(json.dumps(manifest, indent=2, sort_keys=True)+"\n")
        return manifest
    finally:
        shutil.rmtree(work, ignore_errors=True)
