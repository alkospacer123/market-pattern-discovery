#!/usr/bin/env python3
"""Build the compact Stage 3A.1 schema/provenance inventory.

Trade rows are read only long enough to validate and aggregate them.  This
program deliberately has no code path that writes a trade-level data set.
"""
from __future__ import annotations

import csv
import hashlib
import json
import math
import statistics
import subprocess
from collections import defaultdict
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
OUT = Path(__file__).resolve().parent
RESULTS = ROOT / "TradingSystemLab/results"
STAGE1 = RESULTS / "post_v3_analysis/stage1_master_evidence"
STAGE2 = RESULTS / "post_v3_analysis/stage2_portfolio_diversification"
S1_COMMIT = "05e2cdb30ba8ec341403583d37e02712d179a6a7"
S2_COMMIT = "c90e519f2fd4ee6720d9b0da0b1a11ac28cc0c05"
S1_STATUS = "POST_V3_STAGE_1_MASTER_EVIDENCE_AUDIT_PASSED"
S2_STATUS = "POST_V3_STAGE_2_PORTFOLIO_DIVERSIFICATION_AUDIT_PASSED"
TOL = 1e-9
NA = "NA"

INVENTORY_FIELDS = ["generation", "futures_type", "lifecycle_stage", "strategy", "timeframe",
    "instrument_scope", "source_family", "source_path", "source_sha256", "source_schema_id",
    "canonical_c1_field", "trade_count", "first_entry_time", "last_exit_time", "column_count",
    "has_trade_id", "has_direction", "has_entry_time", "has_exit_time", "has_MAE", "has_MFE",
    "has_exit_reason", "has_entry_price", "has_exit_price", "has_stop_field", "has_holding_field",
    "has_cost_field", "has_gross_R_field"]
REGISTRY_FIELDS = ["source_schema_id", "generation", "source_family", "lifecycle_stage",
    "canonical_c1_field", "instrument_field", "direction_field", "entry_time_field", "exit_time_field",
    "trade_id_field", "MAE_field", "MFE_field", "exit_reason_field", "entry_price_field",
    "exit_price_field", "stop_field", "holding_field", "gross_R_field", "cost_R_field",
    "MAE_sign_convention", "timezone_semantics", "normalization_supported"]
AVAIL_FIELDS = ["generation", "lifecycle_stage", "strategy", "timeframe", "source_schema_id",
    "trade_count", "MAE_count", "MAE_coverage_share", "MFE_count", "MFE_coverage_share",
    "exit_reason_count", "exit_reason_coverage_share", "entry_price_count", "exit_price_count",
    "stop_field_count", "holding_field_count", "gross_R_count", "cost_R_count", "coverage_class_MAE",
    "coverage_class_MFE", "coverage_class_exit_reason", "coverage_class_stop", "coverage_class_holding"]
STUDY_FIELDS = ["generation", "futures_type", "lifecycle_stage", "strategy", "timeframe",
    "expected_trade_count", "reconstructed_trade_count", "trade_count_match", "Stage1_net_R",
    "reconstructed_net_R", "net_R_delta", "Stage1_expectancy_R", "reconstructed_expectancy_R",
    "expectancy_delta", "Stage1_PF", "reconstructed_PF", "PF_delta", "Stage1_win_rate",
    "reconstructed_win_rate", "win_rate_delta", "status"]


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git_has(commit: str) -> bool:
    return subprocess.run(["git", "cat-file", "-e", f"{commit}^{{commit}}"], cwd=ROOT).returncode == 0


def audit_status(path: Path) -> str:
    obj = json.loads(path.read_text(encoding="utf-8"))
    return obj.get("status") or obj.get("audit_status") or ""


def source_specs():
    """Return all and only the ledgers used by Stage 1's 36 studies."""
    specs = []
    for gen in ("v1", "v2", "v3"):
        for strategy in ("T2", "T3"):
            for tf in ("M30", "H1"):
                if gen == "v1":
                    base = sorted(RESULTS.glob(f"multitimeframe_research/{strategy}/{tf}/*_trades.csv"))
                    wf = [RESULTS / (f"walk_forward/{tf}/{strategy}/stitched_forward_trades.csv" if tf == "M30" else f"walk_forward_validation/{strategy}/trades.csv")]
                    oos = [RESULTS / (f"true_oos_validation/{tf}/{strategy}/trades.csv" if tf == "M30" else f"true_oos_validation/{strategy}/trades.csv")]
                elif gen == "v2":
                    base = sorted(RESULTS.glob(f"baseline_v2/{strategy}/*/{tf}/trades.csv"))
                    wf = [RESULTS / f"walk_forward_v2/{strategy}/{tf}/trades.csv"]
                    oos = [RESULTS / f"true_oos_v2/{strategy}/{tf}/trades.csv"]
                else:
                    base = sorted(RESULTS.glob(f"perpetual_v3/baseline/{strategy}/{tf}/*/trades.csv"))
                    wf = [RESULTS / f"perpetual_v3/walk_forward/{strategy}/{tf}/trades.csv"]
                    oos = [RESULTS / f"perpetual_v3/true_oos/{strategy}/{tf}/trades.csv"]
                for stage, paths in (("baseline", base), ("walk_forward", wf), ("true_oos", oos)):
                    for path in paths:
                        specs.append((gen, stage, strategy, tf, path))
    return specs


def schema_contract(gen, stage, strategy, tf):
    """Explicit fail-closed schema and C1 mapping; order is intentional."""
    if gen == "v1":
        if stage == "baseline" and strategy == "T2": return "V1_T2_MTF_BASELINE", "net_R_C1"
        if stage == "baseline" and strategy == "T3": return "V1_T3_MTF_BASELINE_C1_DERIVED", "profit_R-2*0.001/initial_risk"
        if stage == "walk_forward" and tf == "M30" and strategy == "T2": return "V1_T2_M30_WF", "net_R"
        if stage == "walk_forward" and tf == "M30" and strategy == "T3": return "V1_T3_M30_WF", "net_R"
        if stage == "walk_forward" and tf == "H1" and strategy == "T2": return "V1_T2_H1_WF_LEGACY", "net_R_C1"
        if stage == "walk_forward" and tf == "H1" and strategy == "T3": return "V1_T3_H1_WF_LEGACY_C1_DERIVED", "profit_R-2*0.001/initial_risk"
        if stage == "true_oos" and tf == "M30" and strategy == "T2": return "V1_T2_M30_TRUE_OOS", "net_R"
        if stage == "true_oos" and tf == "M30" and strategy == "T3": return "V1_T3_M30_TRUE_OOS", "net_R"
        if stage == "true_oos" and tf == "H1": return "V1_H1_TRUE_OOS", "R_result"
    if gen in {"v2", "v3"}:
        prefix = gen.upper()
        suffix = {"baseline": "BASELINE", "walk_forward": "WF", "true_oos": "TRUE_OOS"}[stage]
        c1 = {"baseline": "net_R", "walk_forward": "net_R_C1", "true_oos": "R_result"}[stage]
        # TRUE OOS has one physical schema for T2 and T3; development schemas
        # differ by strategy and therefore retain separate identifiers.
        return (f"{prefix}_{suffix}" if stage == "true_oos" else f"{prefix}_{strategy}_{suffix}"), c1
    raise ValueError(f"unknown schema: {(gen, stage, strategy, tf)}")


def read(path):
    with path.open(newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        return reader.fieldnames or [], list(reader)


def present(row, field):
    return field != NA and row.get(field) not in (None, "")


def fields_for(header):
    def choose(*names):
        hits = [x for x in names if x in header]
        return hits[0] if hits else NA
    return {"instrument_field": choose("instrument", "symbol"), "direction_field": choose("direction"),
        "entry_time_field": choose("entry_time"), "exit_time_field": choose("exit_time"),
        "trade_id_field": choose("trade_id"), "MAE_field": choose("MAE_R"), "MFE_field": choose("MFE_R"),
        "exit_reason_field": choose("exit_reason"), "entry_price_field": choose("entry_price"),
        "exit_price_field": choose("exit_price"), "stop_field": choose("initial_stop"),
        "holding_field": choose("holding_time", "bars_held"), "gross_R_field": choose("gross_R"),
        "cost_R_field": choose("cost_R", "cost_R_C1")}


def c1_value(row, contract):
    if contract == "profit_R-2*0.001/initial_risk":
        if not present(row, "profit_R") or not present(row, "initial_risk"):
            raise ValueError("derived C1 inputs absent")
        return float(row["profit_R"]) - 2 * 0.001 / float(row["initial_risk"])
    if contract not in row or not present(row, contract):
        raise ValueError(f"canonical C1 field absent: {contract}")
    return float(row[contract])


def fmt(value):
    if isinstance(value, bool): return str(value).lower()
    if isinstance(value, float): return format(value, ".15g")
    return str(value)


def write_csv(name, fields, rows):
    with (OUT / name).open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for row in rows: writer.writerow({k: fmt(row.get(k, NA)) for k in fields})


def coverage(n, total):
    share = n / total if total else 0.0
    return share, "AVAILABLE" if n == total and total else "UNAVAILABLE" if n == 0 else "PARTIAL"


def build():
    if not git_has(S1_COMMIT) or not git_has(S2_COMMIT): raise RuntimeError("canonical closeout commit missing")
    if audit_status(STAGE1 / "audit_result.json") != S1_STATUS: raise RuntimeError("Stage 1 audit status mismatch")
    if audit_status(STAGE2 / "audit_result.json") != S2_STATUS: raise RuntimeError("Stage 2 audit status mismatch")
    with (STAGE1 / "master_study_comparison.csv").open(newline="", encoding="utf-8") as fh:
        refs = {(r["generation"], r["lifecycle_stage"], r["strategy"], r["timeframe"]): r for r in csv.DictReader(fh)}
    if len(refs) != 36: raise AssertionError(f"expected 36 Stage 1 identities, got {len(refs)}")

    inventory, registry, grouped, values = [], {}, defaultdict(list), defaultdict(list)
    directions, invalid_ts = set(), 0
    for gen, stage, strategy, tf, path in source_specs():
        if not path.is_file(): raise FileNotFoundError(path)
        sid, c1 = schema_contract(gen, stage, strategy, tf)
        header, rows = read(path); fmap = fields_for(header)
        required = [fmap[x] for x in ("instrument_field", "direction_field", "entry_time_field", "exit_time_field")]
        if NA in required: raise ValueError(f"unsupported required fields in {path}")
        relative_parts = path.relative_to(RESULTS).parts
        source_family = "/".join(relative_parts[:2]) if relative_parts[0] == "perpetual_v3" else relative_parts[0]
        reg = dict(source_schema_id=sid, generation=gen, source_family=source_family,
            lifecycle_stage=stage, canonical_c1_field=c1, **fmap, MAE_sign_convention="UNKNOWN",
            timezone_semantics="source ISO-8601 offset preserved", normalization_supported="true")
        if sid in registry and registry[sid] != reg: raise ValueError(f"schema ID collision: {sid}")
        registry[sid] = reg
        first, last = [], []
        for row in rows:
            d = row[fmap["direction_field"]].upper(); directions.add(row[fmap["direction_field"]])
            if d not in {"LONG", "SHORT"}: raise ValueError(f"unknown direction {d!r}")
            try:
                entry, exit_ = datetime.fromisoformat(row[fmap["entry_time_field"]]), datetime.fromisoformat(row[fmap["exit_time_field"]])
                if exit_ < entry: raise ValueError("exit before entry")
            except (ValueError, TypeError): invalid_ts += 1; continue
            first.append(entry); last.append(exit_); values[(gen, stage, strategy, tf)].append(c1_value(row, c1))
        if invalid_ts: raise ValueError(f"invalid timestamps: {invalid_ts}")
        key = (gen, stage, strategy, tf, sid); grouped[key].extend(rows)
        flags = {"has_trade_id": fmap["trade_id_field"] != NA, "has_direction": True, "has_entry_time": True,
            "has_exit_time": True, "has_MAE": fmap["MAE_field"] != NA, "has_MFE": fmap["MFE_field"] != NA,
            "has_exit_reason": fmap["exit_reason_field"] != NA, "has_entry_price": fmap["entry_price_field"] != NA,
            "has_exit_price": fmap["exit_price_field"] != NA, "has_stop_field": fmap["stop_field"] != NA,
            "has_holding_field": fmap["holding_field"] != NA, "has_cost_field": fmap["cost_R_field"] != NA,
            "has_gross_R_field": fmap["gross_R_field"] != NA}
        inventory.append(dict(generation=gen, futures_type="quarterly" if gen == "v2" else "perpetual",
            lifecycle_stage=stage, strategy=strategy, timeframe=tf,
            instrument_scope={"v1":"USDRUBF|CNYRUBF","v2":"Si|CNY|GD|BR|MIX|NG","v3":"USDRUBF|CNYRUBF|GLDRUBF|IMOEXF"}[gen],
            source_family=reg["source_family"], source_path=path.relative_to(ROOT).as_posix(), source_sha256=sha(path),
            source_schema_id=sid, canonical_c1_field=c1, trade_count=len(rows),
            first_entry_time=min(first).isoformat(), last_exit_time=max(last).isoformat(), column_count=len(header), **flags))

    availability = []
    totals = defaultdict(int)
    for (gen, stage, strategy, tf, sid), rows in sorted(grouped.items()):
        reg = registry[sid]; total = len(rows)
        counts = {name: sum(present(r, reg[field]) for r in rows) for name, field in
            (("MAE", "MAE_field"), ("MFE", "MFE_field"), ("exit_reason", "exit_reason_field"),
             ("entry_price", "entry_price_field"), ("exit_price", "exit_price_field"), ("stop_field", "stop_field"),
             ("holding_field", "holding_field"), ("gross_R", "gross_R_field"), ("cost_R", "cost_R_field"))}
        for k, v in counts.items(): totals[k] += v
        rec = dict(generation=gen, lifecycle_stage=stage, strategy=strategy, timeframe=tf, source_schema_id=sid, trade_count=total)
        for name in ("MAE", "MFE", "exit_reason"):
            share, cls = coverage(counts[name], total); rec[f"{name}_count"] = counts[name]; rec[f"{name}_coverage_share"] = share; rec[f"coverage_class_{name}"] = cls
        for name in ("entry_price", "exit_price", "stop_field", "holding_field", "gross_R", "cost_R"): rec[f"{name}_count"] = counts[name]
        for name, source in (("stop", "stop_field"), ("holding", "holding_field")):
            rec[f"coverage_class_{name}"] = coverage(counts[source], total)[1]
        availability.append(rec)

    study_rows, max_delta = [], 0.0
    for key in sorted(refs):
        ref, vals = refs[key], values[key]
        wins, losses = [v for v in vals if v > 0], [v for v in vals if v < 0]
        calc = {"trades": len(vals), "net": sum(vals), "expectancy": statistics.fmean(vals),
            "PF": sum(wins) / abs(sum(losses)), "win_rate": len(wins) / len(vals)}
        expected = {"trades": int(ref["total_trades"]), "net": float(ref["net_R"]), "expectancy": float(ref["expectancy_R"]),
            "PF": float(ref["PF"]), "win_rate": float(ref["win_rate"])}
        delta = {k: calc[k] - expected[k] for k in ("net", "expectancy", "PF", "win_rate")}; max_delta = max(max_delta, *(abs(x) for x in delta.values()))
        ok = calc["trades"] == expected["trades"] and all(math.isclose(calc[k], expected[k], rel_tol=TOL, abs_tol=TOL) for k in delta)
        if not ok: raise AssertionError(f"Stage 1 reconciliation failed {key}: {calc} != {expected}")
        gen, stage, strategy, tf = key
        study_rows.append(dict(generation=gen, futures_type="quarterly" if gen == "v2" else "perpetual", lifecycle_stage=stage,
            strategy=strategy, timeframe=tf, expected_trade_count=expected["trades"], reconstructed_trade_count=calc["trades"], trade_count_match=True,
            Stage1_net_R=expected["net"], reconstructed_net_R=calc["net"], net_R_delta=delta["net"], Stage1_expectancy_R=expected["expectancy"],
            reconstructed_expectancy_R=calc["expectancy"], expectancy_delta=delta["expectancy"], Stage1_PF=expected["PF"], reconstructed_PF=calc["PF"],
            PF_delta=delta["PF"], Stage1_win_rate=expected["win_rate"], reconstructed_win_rate=calc["win_rate"], win_rate_delta=delta["win_rate"], status="PASS"))

    target = next(r for r in study_rows if (r["generation"],r["lifecycle_stage"],r["strategy"],r["timeframe"]) == ("v1","walk_forward","T3","H1"))
    canonical = {"trades":34,"PF":3.3803276720178377,"expectancy":0.9679913199721701,"net_R":32.91170487905379,"DD_reference":-5.038562132510952}
    if target["reconstructed_trade_count"] != 34 or not all(math.isclose(target[k], canonical[v], rel_tol=TOL, abs_tol=TOL) for k,v in (("reconstructed_PF","PF"),("reconstructed_expectancy_R","expectancy"),("reconstructed_net_R","net_R"))): raise AssertionError("v1 C1 anti-regression failed")
    if math.isclose(target["reconstructed_PF"], 3.49197193021, rel_tol=TOL, abs_tol=TOL): raise AssertionError("legacy C0 PF accepted")

    write_csv("trade_source_inventory.csv", INVENTORY_FIELDS, inventory)
    write_csv("trade_schema_registry.csv", REGISTRY_FIELDS, [registry[k] for k in sorted(registry)])
    write_csv("trade_field_availability.csv", AVAIL_FIELDS, availability)
    write_csv("study_expected_counts.csv", STUDY_FIELDS, study_rows)
    report = f"""# Stage 3A.1 Schema & Provenance Report

## 1. Scope
Compact, aggregate-only schema discovery over the canonical Stage 1 universe. **No normalized trade-level file was committed in this PR.**

## 2. Source families
The {len(inventory)} authenticated ledgers belong to `multitimeframe_research`, `walk_forward`, `walk_forward_validation`, `true_oos_validation`, `baseline_v2`, `walk_forward_v2`, `true_oos_v2`, `perpetual_v3/baseline`, `perpetual_v3/walk_forward`, and `perpetual_v3/true_oos`.

## 3. Schema IDs
{', '.join(f'`{x}`' for x in sorted(registry))}. Distinct physical schemas and C1 contracts are not merged.

## 4. Canonical C1 mappings
Each registry row specifies one exact field or the documented v1 legacy expression `profit_R-2*0.001/initial_risk`; missing and unknown contracts fail closed.

## 5. Field availability
The availability table contains {len(availability)} schema/study rows. Totals: MAE {totals['MAE']}, MFE {totals['MFE']}, exit reason {totals['exit_reason']}, stops {totals['stop_field']}, holding {totals['holding_field']}, entry prices {totals['entry_price']}, exit prices {totals['exit_price']}, gross R {totals['gross_R']}, and cost R {totals['cost_R']}.

## 6. v1 historical C1 protection
T3/H1 walk-forward reproduces 34 trades, PF 3.3803276720178377, expectancy 0.9679913199721701, net R 32.91170487905379, and records DD source reference -5.038562132510952. Legacy C0 PF 3.49197193021 is explicitly rejected.

## 7. Aggregate reconciliation
All 36 independent study identities pass trade count, net R, expectancy, PF, and win-rate reconciliation at 1e-9 tolerance. Maximum observed delta is {max_delta:.3g}.

## 8. Timestamp/direction validation
All entry/exit timestamps parse, all exits are at or after entries, and normalized directions are LONG/SHORT. Source values observed: {', '.join(sorted(directions))}. Invalid timestamps: 0; invalid directions: 0.

## 9. Diff-size control
Only four aggregate CSVs, two scripts, two JSON control records, and this report are permitted. No trade rows, anatomy tables, strategies, market data, optimization, ranking, or rule tests are produced.

## 10. Final status
Generator status: `POST_V3_STAGE_3A1_SCHEMA_PROVENANCE_COMPLETE`. Independent audit status is recorded only in `audit_stage3a1_result.json`.
"""
    (OUT / "Stage_3A1_Schema_Provenance_Report.md").write_text(report, encoding="utf-8")
    generated = ["trade_source_inventory.csv","trade_schema_registry.csv","trade_field_availability.csv","study_expected_counts.csv","Stage_3A1_Schema_Provenance_Report.md"]
    by_gen = {g: sum(len(v) for k,v in values.items() if k[0] == g) for g in ("v1","v2","v3")}
    manifest = {"status":"POST_V3_STAGE_3A1_SCHEMA_PROVENANCE_COMPLETE","audit_status":"PENDING_INDEPENDENT_AUDIT",
        "stage1_provenance":{"commit":S1_COMMIT,"status":S1_STATUS,"audit_sha256":sha(STAGE1/"audit_result.json"),"comparison_sha256":sha(STAGE1/"master_study_comparison.csv")},
        "stage2_provenance":{"commit":S2_COMMIT,"status":S2_STATUS,"audit_sha256":sha(STAGE2/"audit_result.json")},
        "source_ledgers":len(inventory),"source_hashes":{r["source_path"]:r["source_sha256"] for r in inventory},"schema_ids":sorted(registry),
        "study_count":len(study_rows),"total_source_trade_rows_scanned":sum(by_gen.values()),"counts_per_generation":by_gen,
        "field_coverage_totals":dict(sorted(totals.items())),"invalid_timestamp_count":0,"invalid_direction_count":0,
        "generated_output_hashes":{x:sha(OUT/x) for x in generated},"no_trade_level_artifact":True,"no_strategy_execution":True,
        "no_market_data_load":True,"no_optimization":True,"no_ranking":True,"no_rule_testing":True}
    (OUT / "manifest_stage3a1.json").write_text(json.dumps(manifest, indent=2, sort_keys=True)+"\n", encoding="utf-8")
    print(f"Stage 3A.1 generated: {len(inventory)} ledgers, {sum(by_gen.values())} rows scanned, 36 studies PASS")


if __name__ == "__main__": build()
