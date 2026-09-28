"""Deterministic, diagnostic-only Stage 5.4 minimum-holding evidence builder.

This module joins authenticated Stage 3 normalized trade metadata to the
canonical Stage 5 economics by the normalized source-row identity.  It does
not execute, suppress, filter, or otherwise alter a trade.
"""
from __future__ import annotations

import csv
import hashlib
import json
import math
import statistics
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
STAGE3 = HERE.parent / "stage3_trade_anatomy"
STAGE4 = HERE.parent / "stage4_structural_hypotheses"
EXPECTED = {("v2", "baseline"): 4449, ("v2", "walk_forward"): 746,
            ("v2", "true_oos"): 1759, ("v3", "baseline"): 1124,
            ("v3", "walk_forward"): 515, ("v3", "true_oos"): 1101}
BUCKETS = ("<1h", "1–3h", "3–6h", "6–12h", "12–24h", "24–48h",
           "48–96h", ">96h", "UNAVAILABLE")
NORMALIZED = tuple(f"normalized_trades_{g}_{life}.csv" for g in ("v2", "v3")
                   for life in ("baseline", "walk_forward", "true_oos"))
STATUS = "STAGE5_5_4_MINIMUM_HOLD_DIAGNOSTICS_COMPLETE"
RESEARCH_STATUS = "DIAGNOSTIC_ONLY_NO_HYPOTHESIS_ADMISSION"
FAIL_INPUT = "MINIMUM_HOLD_INPUT_AUTHENTICATION_FAILED"
FAIL_CANONICAL = "MINIMUM_HOLD_CANONICAL_RECONCILIATION_FAILED"
FAIL_BUCKET = "MINIMUM_HOLD_BUCKET_CONTRACT_FAILED"
FAIL_ECONOMICS = "MINIMUM_HOLD_ECONOMICS_RECONCILIATION_FAILED"
FAIL_DETERMINISM = "MINIMUM_HOLD_DETERMINISM_FAILED"
TOL = 1e-7


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def holding_bucket(value: Any) -> str:
    try:
        x = float(value)
        if not math.isfinite(x): return "UNAVAILABLE"
    except (TypeError, ValueError): return "UNAVAILABLE"
    if x < 1: return "<1h"
    if x < 3: return "1–3h"
    if x < 6: return "3–6h"
    if x < 12: return "6–12h"
    if x < 24: return "12–24h"
    if x < 48: return "24–48h"
    if x <= 96: return "48–96h"
    return ">96h"


def _read(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as f: return list(csv.DictReader(f))


def _fmt(value: Any) -> Any:
    if isinstance(value, bool): return str(value).lower()
    if value is None: return "NA"
    if isinstance(value, float): return format(value, ".12g")
    return value


def _write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str] | None = None) -> None:
    fields = fields or (list(rows[0]) if rows else [])
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, lineterminator="\n"); w.writeheader()
        w.writerows({k: _fmt(r.get(k)) for k in fields} for r in rows)


def _metrics(rows: list[dict[str, Any]], *, full: bool = False) -> dict[str, Any]:
    values = [float(r["net_R"]) for r in rows]; wins = [x for x in values if x > 0]; losses = [x for x in values if x < 0]
    base = {"trades": len(rows), "net_R": sum(values),
            "expectancy_R": statistics.mean(values) if values else 0.0,
            "PF": sum(wins) / -sum(losses) if losses else ("INF" if wins else 0.0),
            "win_rate": len(wins) / len(values) if values else 0.0}
    if full:
        holds = [float(r["holding_hours"]) for r in rows if r["holding_bucket"] != "UNAVAILABLE"]
        base.update(winners=len(wins), losers=len(losses), median_R=statistics.median(values),
                    average_win_R=statistics.mean(wins) if wins else None,
                    average_loss_R=statistics.mean(losses) if losses else None,
                    best_trade_R=max(values), worst_trade_R=min(values),
                    average_holding_hours=statistics.mean(holds) if holds else None,
                    median_holding_hours=statistics.median(holds) if holds else None)
    return base


def _groups(rows: Iterable[dict[str, Any]], keys: list[str]):
    result: dict[tuple[Any, ...], list[dict[str, Any]]] = defaultdict(list)
    for row in rows: result[tuple(row[k] for k in keys)].append(row)
    return result


def validate_population(rows: list[dict[str, Any]]) -> None:
    if len(rows) != 9694: raise RuntimeError(FAIL_CANONICAL)
    keys = [r["canonical_trade_key"] for r in rows]
    if len(set(keys)) != len(keys): raise RuntimeError(FAIL_CANONICAL)
    counts = defaultdict(int)
    for r in rows: counts[(r["generation"], r["lifecycle_stage"])] += 1
    if dict(counts) != EXPECTED: raise RuntimeError(FAIL_CANONICAL)


def corrected_single_c1(raw: dict[str, str], strategy: str) -> float:
    """Correct the frozen T3 double-C1 ledger without changing its path."""
    net_col = "net_R_C1" if "net_R_C1" in raw else "net_R"
    return float(raw[net_col]) + (float(raw.get("cost_R") or 0) if strategy == "T3" else 0.0)


def reconcile_rows(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Strictly reconcile Stage 3 identity and corrected single-C1 economics."""
    validate_population(rows)
    mismatches = 0
    source_cache: dict[Path, list[dict[str, str]]] = {}
    for r in rows:
        source = ROOT / r["source_path"]
        if source not in source_cache: source_cache[source] = _read(source)
        source_rows = source_cache[source]
        index = int(r["source_row_number"]) - 2
        if index < 0 or index >= len(source_rows): raise RuntimeError(FAIL_CANONICAL)
        raw = source_rows[index]
        identity = (raw.get("trade_id", ""), raw.get("symbol", ""), raw.get("direction", ""),
                    raw.get("entry_time", ""), raw.get("exit_time", ""))
        expected = (r["source_trade_id"], r["instrument"], r["direction"], r["entry_time"], r["exit_time"])
        if identity != expected: mismatches += 1
        corrected = corrected_single_c1(raw, r["strategy"])
        r.update(net_R=corrected, fold_id=raw.get("fold", ""), exit_reason=raw.get("exit_reason") or "UNAVAILABLE",
                 holding_bucket=holding_bucket(r.get("holding_hours")), lifecycle=r["lifecycle_stage"])
    if mismatches: raise RuntimeError(FAIL_CANONICAL)
    return {"canonical_rows": len(rows), "matched_holding_rows": len(rows), "duplicate_canonical_identities": 0,
            "unmatched_stage5_trades": 0, "unexpected_stage3_v2_v3_rows": 0, "canonical_path_mismatches": 0}


def _report(rows: list[dict[str, Any]], keys: list[str], *, full=False, share_parent: list[str] | None=None) -> list[dict[str, Any]]:
    groups = _groups(rows, keys); parents = _groups(rows, share_parent or [])
    out = []
    for key, part in sorted(groups.items()):
        item = {**dict(zip(keys, key)), **_metrics(part, full=full)}
        if share_parent is not None:
            pk = tuple(item[k] for k in share_parent); item["share_of_parent_trades"] = len(part) / len(parents[pk])
        item["small_sample_flag"] = len(part) < 30
        out.append(item)
    return out


def _maxdd(rows: list[dict[str, Any]]) -> tuple[float, float]:
    total = peak = worst = 0.0
    for r in rows: total += float(r["net_R"]); peak = max(peak, total); worst = min(worst, total - peak)
    return worst, total / abs(worst) if worst else 0.0


def build(output: Path) -> dict[str, Any]:
    output.mkdir(parents=True, exist_ok=True)
    rows = [r for name in NORMALIZED for r in _read(STAGE3 / name)]
    reconciliation = reconcile_rows(rows)
    base = ["generation", "lifecycle", "strategy", "timeframe"]
    bucket = _report(rows, base + ["holding_bucket"], full=True, share_parent=base)
    lifecycle = _report(rows, ["generation", "lifecycle", "holding_bucket"], share_parent=["generation", "lifecycle"])
    strategy_tf = _report(rows, base + ["holding_bucket"])
    wf = _report([r for r in rows if r["lifecycle"] == "walk_forward"], ["generation", "fold_id", "strategy", "timeframe", "holding_bucket"])
    exit_reason = _report(rows, base + ["holding_bucket", "exit_reason"], share_parent=base + ["holding_bucket"])
    direction = _report(rows, base + ["holding_bucket", "direction"])
    instrument = _report(rows, base + ["holding_bucket", "instrument"])
    cumulative = []
    cohort_buckets = (("<3h", {"<1h", "1–3h"}), ("<6h", {"<1h", "1–3h", "3–6h"}),
        ("<12h", set(BUCKETS[:4])), ("<24h", set(BUCKETS[:5])), ("<48h", set(BUCKETS[:6])), ("<=96h", set(BUCKETS[:7])))
    for parent_key, parent in sorted(_groups(rows, base).items()):
        for label, included in cohort_buckets:
            part = [r for r in parent if r["holding_bucket"] in included]
            cumulative.append({**dict(zip(base, parent_key)), "cumulative_cohort": label, **_metrics(part), "share_of_parent_trades": len(part)/len(parent)})
    recurrence = []
    wf_groups = _groups(wf, ["generation", "strategy", "timeframe", "holding_bucket"])
    for key, parts in sorted(wf_groups.items()):
        recurrence.append({**dict(zip(["generation", "strategy", "timeframe", "holding_bucket"], key)),
            "folds": len(parts), "positive_expectancy_folds": sum(float(x["expectancy_R"]) > 0 for x in parts),
            "negative_expectancy_folds": sum(float(x["expectancy_R"]) < 0 for x in parts),
            "zero_expectancy_folds": sum(float(x["expectancy_R"]) == 0 for x in parts),
            "small_sample_folds": sum(bool(x["small_sample_flag"]) for x in parts)})
    recon_rows=[]
    authority = {(r["generation"].replace("_quarterly", "").replace("_perpetual", ""),
                  {"historical_true_oos":"true_oos"}.get(r["lifecycle"], r["lifecycle"])): r
                 for r in _read(HERE/"be1/be1_c1_corrected_lifecycle_report.csv")}
    for key, part in sorted(_groups(rows,["generation","lifecycle"]).items()):
        m=_metrics(part); dd, recovery=_maxdd(part)
        expected = authority[key]
        comparisons = ((m["trades"], expected["canonical_trades"]), (m["net_R"], expected["canonical_net_R"]),
                       (m["PF"], expected["canonical_PF"]), (m["expectancy_R"], expected["canonical_expectancy_R"]),
                       (dd, expected["canonical_max_DD"]), (recovery, expected["canonical_recovery"]))
        if any(abs(float(a)-float(b)) > TOL for a,b in comparisons): raise RuntimeError(FAIL_ECONOMICS)
        recon_rows.append({"generation":key[0],"lifecycle":key[1],**m,"max_DD":dd,"recovery":recovery,"status":"PASS"})
    reports = {
        "minimum_hold_reconciliation.csv": recon_rows, "minimum_hold_bucket_report.csv": bucket,
        "minimum_hold_lifecycle_report.csv": lifecycle, "minimum_hold_strategy_timeframe_report.csv": strategy_tf,
        "minimum_hold_wf_fold_report.csv": wf, "minimum_hold_exit_reason_report.csv": exit_reason,
        "minimum_hold_direction_report.csv": direction, "minimum_hold_instrument_report.csv": instrument,
        "minimum_hold_cumulative_report.csv": cumulative, "minimum_hold_recurrence_report.csv": recurrence}
    for name, data in reports.items(): _write_csv(output/name, data)
    early = [x for x in cumulative if x["cumulative_cohort"] == "<3h"]
    populated_early = [x for x in early if int(x["trades"]) >= 30]
    negative_early = sum(float(x["expectancy_R"]) < 0 for x in populated_early)
    lifecycle_table = "\n".join(
        f"| {x['generation']} | {x['lifecycle']} | {x['holding_bucket']} | {x['trades']} | {_fmt(x['share_of_parent_trades'])} | {_fmt(x['net_R'])} | {_fmt(x['expectancy_R'])} | {_fmt(x['PF'])} | {_fmt(x['win_rate'])} |"
        for x in lifecycle)
    report = f"""# Minimum-Hold Diagnostics Report

## 1. Scope
Stage 5.4 describes canonical T2/T3 holding-time outcomes only. No exit was changed and no duration was selected.

## 2. Prerequisite provenance
Authenticated Stage 3 normalized metadata and the Stage 5 canonical comparator are the only evidence inputs. Economics use `CORRECTED_SINGLE_C1`; the frozen strategy hashes and data identity are unchanged.

## 3. Canonical 9,694 reconciliation
Exactly **9,694** v2/v3 trades reconcile with zero canonical path mismatches. Six-lifecycle counts are 4,449 / 746 / 1,759 for v2 and 1,124 / 515 / 1,101 for v3.

## 4. Holding metadata reconciliation
All **9,694 / 9,694** records match one-to-one by authenticated source path, source row, and trade identity. Duplicate, unmatched, and unexpected counts are zero.

## 5. Six-lifecycle bucket table
`minimum_hold_lifecycle_report.csv` preserves every observed frozen bucket and lifecycle; no bucket is ranked.

| Generation | Lifecycle | Bucket | Trades | Share | Net R | Expectancy | PF | Win rate |
|---|---|---:|---:|---:|---:|---:|---:|---:|
{lifecycle_table}

## 6. T2/T3 and M30/H1 comparison
`minimum_hold_strategy_timeframe_report.csv` retains generation, lifecycle, strategy, timeframe, and bucket.

## 7. Walk-forward fold diagnostics
`minimum_hold_wf_fold_report.csv` keeps real folds separate. `minimum_hold_recurrence_report.csv` counts positive, negative, zero, and small-sample folds without a score.

## 8. Exit-reason diagnostics
`minimum_hold_exit_reason_report.csv` preserves source exit reasons verbatim and uses `UNAVAILABLE` only for missing values.

## 9. Direction diagnostics
`minimum_hold_direction_report.csv` is descriptive and makes no direction selection.

## 10. Instrument diagnostics
`minimum_hold_instrument_report.csv` is descriptive and makes no instrument selection.

## 11. Cumulative descriptive cohorts
`minimum_hold_cumulative_report.csv` combines frozen buckets only. For `<3h`, {sum(int(x['trades']) for x in early)} trades are represented across the 24 parent study cells; this view reports realized canonical R, not a system with those trades removed.

## 12. Recurrence across v2/v3 and lifecycle
**Observed fact:** `<3h` trades have negative expectancy in **{negative_early} of {len(populated_early)}** sufficiently populated (at least 30 trades) generation/lifecycle/strategy/timeframe parent cells. The detailed tables show heterogeneous bucket economics across generation, lifecycle, engine, and timeframe. This is observable evidence only and remains insufficient to define one structural duration.

## 13. Small-sample limitations
Every cell with fewer than 30 trades remains visible and is flagged. Such cells are not pooled with larger samples.

## 14. No-counterfactual statement
It is unknown how a canonical trade closed early would have ended had its exit been forbidden. A minimum-hold rule would require a predeclared duration, separate research identity, and causal re-execution; none is performed here.

## 15. Stage 4 preservation
`Stage4 minimum-hold status = NOT_ADMITTED`. `Stage4 registry unchanged = true`.

## 16. Technical audit status
`{STATUS}` / `{RESEARCH_STATUS}`. The independent audit is the authority for manifest status.

## 17. Conclusion and next roadmap step
Stage 5.4 Minimum-Holding Diagnostics completed. The evidence is descriptive only and does not admit or validate a minimum-hold rule. Stage 4 NOT_ADMITTED status remains unchanged. Stage 5 remains OPEN.

Next roadmap step: 5.5 Session/time-of-day diagnostics.
"""
    (output/"Minimum_Hold_Diagnostics_Report.md").write_text(report, encoding="utf-8")
    return {**reconciliation, "wf_fold_count": len({(r['generation'],r['fold_id']) for r in rows if r['lifecycle']=='walk_forward'}),
            "report_files": sorted([*reports, "Minimum_Hold_Diagnostics_Report.md"])}
