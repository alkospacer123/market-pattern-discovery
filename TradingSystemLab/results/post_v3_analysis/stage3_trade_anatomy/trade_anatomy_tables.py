#!/usr/bin/env python3
"""Build deterministic, aggregate-only Stage 3B trade-anatomy tables."""

from __future__ import annotations

import csv
import hashlib
import json
import math
import os
import statistics
from collections import defaultdict
from pathlib import Path

STAGE = Path(__file__).resolve().parent
OUT = Path(os.environ.get("STAGE3B_OUTPUT_DIR", STAGE))
INPUTS = [
    "normalized_trades_v1.csv", "normalized_trades_v2_baseline.csv",
    "normalized_trades_v2_walk_forward.csv", "normalized_trades_v2_true_oos.csv",
    "normalized_trades_v3_baseline.csv", "normalized_trades_v3_walk_forward.csv",
    "normalized_trades_v3_true_oos.csv",
]
TABLES = {
    "anatomy_by_generation.csv": ["generation", "futures_type", "lifecycle_stage", "strategy", "timeframe"],
    "anatomy_by_strategy_timeframe.csv": ["generation", "lifecycle_stage", "strategy", "timeframe"],
    "anatomy_by_instrument.csv": ["generation", "lifecycle_stage", "strategy", "timeframe", "instrument"],
    "anatomy_by_direction.csv": ["generation", "lifecycle_stage", "strategy", "timeframe", "direction"],
    "anatomy_by_exit_reason.csv": ["generation", "lifecycle_stage", "strategy", "timeframe", "exit_reason_raw"],
    "anatomy_by_holding_bucket.csv": ["generation", "lifecycle_stage", "strategy", "timeframe", "holding_bucket"],
    "anatomy_by_entry_weekday.csv": ["generation", "lifecycle_stage", "strategy", "timeframe", "entry_weekday"],
    "anatomy_by_entry_hour.csv": ["generation", "lifecycle_stage", "strategy", "timeframe", "entry_hour"],
}
COMMON = ["trades", "winners", "losers", "win_rate", "net_R", "expectancy_R", "PF", "avg_win_R", "avg_loss_R", "median_R", "std_R", "best_trade_R", "worst_trade_R", "average_holding_hours", "median_holding_hours", "average_MAE_R", "median_MAE_R", "average_MFE_R", "median_MFE_R", "small_sample_flag"]
FINAL_A4 = "POST_V3_STAGE_3A4_V3_CORE_NORMALIZATION_AUDIT_PASSED"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def num(value: str) -> float | None:
    try:
        x = float(value)
        return x if math.isfinite(x) else None
    except (TypeError, ValueError):
        return None


def fmt(value: object) -> object:
    if value is None:
        return "NA"
    if isinstance(value, float):
        return format(value, ".15g")
    if isinstance(value, bool):
        return str(value).lower()
    return value


def mean(values: list[float]) -> float | None:
    return sum(values) / len(values) if values else None


def med(values: list[float]) -> float | None:
    return statistics.median(values) if values else None


def metrics(rows: list[dict[str, str]]) -> dict[str, object]:
    returns = [float(r["canonical_C1_R"]) for r in rows]
    wins, losses = [x for x in returns if x > 0], [x for x in returns if x < 0]
    holding = [x for r in rows if (x := num(r["holding_hours"])) is not None]
    mae = [x for r in rows if (x := num(r["MAE_R"])) is not None]
    mfe = [x for r in rows if (x := num(r["MFE_R"])) is not None]
    gross_profit, gross_loss = sum(wins), -sum(losses)
    return {
        "trades": len(rows), "winners": len(wins), "losers": len(losses),
        "win_rate": len(wins) / len(rows), "net_R": sum(returns),
        "expectancy_R": mean(returns), "PF": gross_profit / gross_loss if gross_loss else None,
        "avg_win_R": mean(wins), "avg_loss_R": mean(losses), "median_R": med(returns),
        "std_R": statistics.pstdev(returns) if returns else None,
        "best_trade_R": max(returns), "worst_trade_R": min(returns),
        "average_holding_hours": mean(holding), "median_holding_hours": med(holding),
        "average_MAE_R": mean(mae), "median_MAE_R": med(mae),
        "average_MFE_R": mean(mfe), "median_MFE_R": med(mfe),
        "small_sample_flag": len(rows) < 30,
    }


def holding_bucket(text: str) -> str:
    x = num(text)
    if x is None: return "UNAVAILABLE"
    if x < 1: return "<1h"
    if x < 3: return "1–3h"
    if x < 6: return "3–6h"
    if x < 12: return "6–12h"
    if x < 24: return "12–24h"
    if x < 48: return "24–48h"
    if x <= 96: return "48–96h"
    return ">96h"


def write_csv(name: str, fields: list[str], rows: list[dict[str, object]]) -> None:
    with (OUT / name).open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows({k: fmt(r[k]) for k in fields} for r in rows)


def load_and_authenticate() -> tuple[list[dict[str, str]], dict[str, str]]:
    audit_path, manifest_path = STAGE / "audit_stage3a4_v3_result.json", STAGE / "manifest_stage3a4_v3.json"
    audit, manifest = json.loads(audit_path.read_text()), json.loads(manifest_path.read_text())
    if audit.get("status") != FINAL_A4 or audit.get("core_normalization_status") != "STAGE_3A_CORE_NORMALIZATION_CLOSED" or manifest.get("audit_status") != FINAL_A4:
        raise RuntimeError("Stage 3A canonical closeout is not authenticated")
    if sha(manifest_path) != audit["output_hashes"]["manifest_stage3a4_v3.json"]:
        raise RuntimeError("Stage 3A.4 manifest authentication failed")
    expected = dict(audit["prerequisite_normalized_hashes"])
    expected.update(manifest["partition_hashes"])
    for name in INPUTS:
        if sha(STAGE / name) != expected.get(name):
            raise RuntimeError(f"prerequisite hash mismatch: {name}")
    rows: list[dict[str, str]] = []
    for name in INPUTS:
        with (STAGE / name).open(newline="", encoding="utf-8") as stream:
            rows.extend(csv.DictReader(stream))
    if len(rows) != 10993 or len({r["canonical_trade_key"] for r in rows}) != 10993:
        raise RuntimeError("normalized population/key contract failed")
    return rows, expected


def grouped(rows: list[dict[str, str]], keys: list[str]) -> list[dict[str, object]]:
    groups: dict[tuple[str, ...], list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        groups[tuple(row[k] for k in keys)].append(row)
    output = []
    for key in sorted(groups):
        output.append({**dict(zip(keys, key)), **metrics(groups[key])})
    return output


def percentile(values: list[float], q: float) -> float | None:
    if not values: return None
    values = sorted(values); pos = (len(values) - 1) * q; lo = int(pos); hi = math.ceil(pos)
    return values[lo] if lo == hi else values[lo] + (values[hi] - values[lo]) * (pos - lo)


def mae_mfe(rows: list[dict[str, str]]) -> list[dict[str, object]]:
    keys = ["generation", "lifecycle_stage", "strategy", "timeframe"]
    groups: dict[tuple[str, ...], list[dict[str, str]]] = defaultdict(list)
    for row in rows: groups[tuple(row[k] for k in keys)].append(row)
    output = []
    for key in sorted(groups):
        rs = groups[key]; mae = [x for r in rs if (x := num(r["MAE_R"])) is not None]; mfe = [x for r in rs if (x := num(r["MFE_R"])) is not None]
        wins = [r for r in rs if float(r["canonical_C1_R"]) > 0]; losses = [r for r in rs if float(r["canonical_C1_R"]) < 0]
        vals = lambda subset, field: [x for r in subset if (x := num(r[field])) is not None]
        output.append({**dict(zip(keys, key)), "trades": len(rs), "trades_with_MAE": len(mae), "trades_with_MFE": len(mfe),
            "avg_MAE": mean(mae), "median_MAE": med(mae), "p25_MAE": percentile(mae, .25), "p75_MAE": percentile(mae, .75),
            "avg_MFE": mean(mfe), "median_MFE": med(mfe), "p25_MFE": percentile(mfe, .25), "p75_MFE": percentile(mfe, .75),
            "winner_avg_MAE": mean(vals(wins, "MAE_R")), "loser_avg_MAE": mean(vals(losses, "MAE_R")),
            "winner_avg_MFE": mean(vals(wins, "MFE_R")), "loser_avg_MFE": mean(vals(losses, "MFE_R"))})
    return output


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    rows, input_hashes = load_and_authenticate()
    for row in rows:
        row["exit_reason_raw"] = row["exit_reason_raw"] or "UNAVAILABLE"
        row["holding_bucket"] = holding_bucket(row["holding_hours"])
        row["entry_weekday"] = row["entry_weekday"] or "UNAVAILABLE"
        row["entry_hour"] = row["entry_hour"] or "UNAVAILABLE"
    table_rows = {}
    for name, keys in TABLES.items():
        data = grouped(rows, keys)
        if name == "anatomy_by_exit_reason.csv":
            parent = defaultdict(int)
            for r in rows: parent[(r["generation"], r["lifecycle_stage"], r["strategy"], r["timeframe"])] += 1
            for item in data: item["share_of_trades"] = item["trades"] / parent[tuple(item[k] for k in TABLES[name][:-1])]
            fields = keys + ["trades", "share_of_trades"] + COMMON[1:]
        else: fields = keys + COMMON
        write_csv(name, fields, data); table_rows[name] = len(data)
    summary = mae_mfe(rows)
    mae_fields = list(summary[0])
    write_csv("anatomy_mae_mfe_summary.csv", mae_fields, summary)
    table_rows["anatomy_mae_mfe_summary.csv"] = len(summary)
    report = """# Stage 3B Trade Anatomy Report

## 1. Scope
Aggregate-only descriptive diagnostics for T2/T3, M30/H1, and separately labelled baseline, walk-forward, and TRUE OOS lifecycles. No strategy execution or selection was performed.

## 2. Canonical normalized dataset
The authenticated Stage 3A closed population contains 10,993 uniquely keyed trades across 36 studies. All seven normalized partitions are inputs; no raw market data is read.

## 3. T2 vs T3
The strategy/timeframe table exposes descriptive return, holding, and excursion differences while retaining generation and lifecycle labels. It defines no selection score.

## 4. M30 vs H1
Timeframe comparisons remain stratified by generation, lifecycle, and strategy. Different sample sizes must be kept visible.

## 5. Instrument anatomy
Instrument rows are not merged. In particular, quarterly v2 Si/CNY constructions remain distinct from perpetual USDRUBF/CNYRUBF constructions.

## 6. Direction anatomy
LONG and SHORT anatomy is reported without filtering or prescriptive interpretation.

## 7. Exit-reason anatomy
Source values are preserved verbatim; missing values, if any, are the explicit `UNAVAILABLE` category. Shares are calculated within each study.

## 8. Holding-time anatomy
Fixed, predeclared buckets are `<1h`, `1–3h`, `3–6h`, `6–12h`, `12–24h`, `24–48h`, `48–96h`, and `>96h`; missing values use `UNAVAILABLE`. Boundaries were not fitted to outcomes.

## 9. Entry weekday
Normalized weekday values (0=Monday through 6=Sunday) are retained without causal claims.

## 10. Entry hour
Normalized hours are retained without timezone conversion, session construction, or rule testing.

## 11. MAE/MFE anatomy
Coverage and quartiles are reported without imputation or alteration of the Stage 3A sign convention, which remains UNKNOWN. **MAE_MFE_ORDER_UNAVAILABLE**: the normalized records do not establish intratrade event ordering.

## 12. Repeated patterns across lifecycle
The tables permit side-by-side inspection only. Lifecycle stages are never pooled, and recurrence is not a selection criterion.

## 13. Cross-generation observations
v1 and v3 perpetual results and v2 quarterly results are presented descriptively. Periods, universes, constructions, and sample sizes differ, so no causal superiority claim is supported.

## 14. Limitations
This is descriptive evidence organization: no significance tests, path reconstruction, threshold-event inference, recommendations, ranking, optimization, or small-sample suppression. Aggregate MAE/MFE does not reveal which excursion occurred first.

## 15. Handoff to Stage 3C
No Stage 3C work is performed. Any later threshold-event analysis requires separately declared exact inference rules and ordered-path evidence.
"""
    (OUT / "Stage_3B_Trade_Anatomy_Report.md").write_text(report, encoding="utf-8")
    outputs = list(TABLES) + ["anatomy_mae_mfe_summary.csv", "Stage_3B_Trade_Anatomy_Report.md"]
    manifest = {
        "status": "POST_V3_STAGE_3B_TRADE_ANATOMY_TABLES_COMPLETE", "audit_status": "PENDING_INDEPENDENT_AUDIT",
        "stage3a_canonical_closeout_commit": "65e9a702f60d11636c1e78a29a47b576b9f22c27",
        "prerequisite_hashes": input_hashes, "normalized_row_count": len(rows), "unique_trade_keys": len({r["canonical_trade_key"] for r in rows}),
        "table_row_counts": table_rows, "output_hashes": {name: sha(OUT / name) for name in outputs},
        "no_trade_level_output": True, "no_strategy_execution": True, "no_optimization": True, "no_ranking": True,
        "no_rule_testing": True, "no_stage3c": True, "no_stage4": True,
    }
    (OUT / "manifest_stage3b.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("POST_V3_STAGE_3B_TRADE_ANATOMY_TABLES_COMPLETE / PENDING_INDEPENDENT_AUDIT")


if __name__ == "__main__":
    main()
