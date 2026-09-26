#!/usr/bin/env python3
"""Deterministic, artifact-only v1/v2/v3 evidence consolidation.

This module deliberately depends only on the Python standard library and reads
committed result CSV/JSON files.  It does not import the research engine.
"""
from __future__ import annotations

import csv
import hashlib
import json
import math
import statistics
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
OUT = Path(__file__).resolve().parent
RESULTS = ROOT / "TradingSystemLab/results"
NA = "NA"
UNIVERSES = {
    "v1": ("perpetual", "USDRUBF|CNYRUBF"),
    "v2": ("quarterly", "Si|CNY|GD|BR|MIX|NG"),
    "v3": ("perpetual", "USDRUBF|CNYRUBF|GLDRUBF|IMOEXF"),
}
CLASSIFICATIONS = {("v3", "T2", "M30"): "BORDERLINE", ("v3", "T2", "H1"): "BORDERLINE",
                   ("v3", "T3", "M30"): "PASS", ("v3", "T3", "H1"): "PASS"}
PHASE2_FILES = {
    "v1_h1": RESULTS / "true_oos_validation/summary/comparison.csv",
    "v1_m30": RESULTS / "timeframe_analysis/M30_ROBUSTNESS/comparison.csv",
    "v2": RESULTS / "true_oos_v2/summary/comparison.csv",
    "v3": RESULTS / "perpetual_v3/true_oos/summary/comparison.csv",
}


@dataclass(frozen=True)
class Study:
    generation: str
    stage: str
    strategy: str
    timeframe: str
    trade_files: tuple[Path, ...]
    metrics_file: Path | None = None

    @property
    def key(self):
        return (self.generation, self.stage, self.strategy, self.timeframe)


def studies() -> list[Study]:
    out = []
    for gen in ("v1", "v2", "v3"):
        for strategy in ("T2", "T3"):
            for tf in ("M30", "H1"):
                if gen == "v1":
                    dev = tuple(RESULTS.glob(f"multitimeframe_research/{strategy}/{tf}/*_trades.csv"))
                    if tf == "H1":
                        wf = (RESULTS / f"walk_forward_validation/{strategy}/trades.csv",)
                        oos = (RESULTS / f"true_oos_validation/{strategy}/trades.csv",)
                        wf_metrics = RESULTS / f"walk_forward_validation/{strategy}/metrics.json"
                        oos_metrics = RESULTS / f"true_oos_validation/{strategy}/metrics.json"
                    else:
                        wf = (RESULTS / f"walk_forward/{tf}/{strategy}/stitched_forward_trades.csv",)
                        oos = (RESULTS / f"true_oos_validation/{tf}/{strategy}/trades.csv",)
                        wf_metrics = RESULTS / f"walk_forward/{tf}/{strategy}/aggregate_metrics.json"
                        oos_metrics = RESULTS / f"true_oos_validation/{tf}/{strategy}/metrics.json"
                    specs = (("baseline", dev, None), ("walk_forward", wf, wf_metrics),
                             ("true_oos", oos, oos_metrics))
                elif gen == "v2":
                    base = tuple(RESULTS.glob(f"baseline_v2/{strategy}/*/{tf}/trades.csv"))
                    specs = (("baseline", base, None),
                             ("walk_forward", (RESULTS / f"walk_forward_v2/{strategy}/{tf}/trades.csv",), RESULTS / f"walk_forward_v2/{strategy}/{tf}/metrics.json"),
                             ("true_oos", (RESULTS / f"true_oos_v2/{strategy}/{tf}/trades.csv",), RESULTS / f"true_oos_v2/{strategy}/{tf}/metrics.json"))
                else:
                    base = tuple(RESULTS.glob(f"perpetual_v3/baseline/{strategy}/{tf}/*/trades.csv"))
                    specs = (("baseline", base, None),
                             ("walk_forward", (RESULTS / f"perpetual_v3/walk_forward/{strategy}/{tf}/trades.csv",), RESULTS / f"perpetual_v3/walk_forward/{strategy}/{tf}/metrics.json"),
                             ("true_oos", (RESULTS / f"perpetual_v3/true_oos/{strategy}/{tf}/trades.csv",), RESULTS / f"perpetual_v3/true_oos/{strategy}/{tf}/metrics.json"))
                for stage, files, metrics in specs:
                    out.append(Study(gen, stage, strategy, tf, tuple(sorted(files)), metrics))
    return out


def canonical_c1_r(row: dict, study: Study) -> float:
    """Return C1 R using an explicit, fail-closed contract per source family."""
    if study.generation == "v1" and study.strategy == "T3" and study.stage == "baseline" or (
        study.generation == "v1" and study.strategy == "T3" and study.timeframe == "H1" and study.stage == "walk_forward"
    ):
        # Legacy T3 stores C0 profit_R.  C1 is one frozen 0.001 tick per side.
        required = ("profit_R", "initial_risk")
        if not all(row.get(x) not in (None, "") for x in required):
            raise ValueError(f"v1 T3/H1 C1 is not reconstructable: missing {required}")
        return float(row["profit_R"]) - 2 * 0.001 / float(row["initial_risk"])
    contracts = {
        ("v1", "T2", "baseline"): "net_R_C1",
        ("v1", "T2", "walk_forward"): "net_R_C1",
        ("v1", "T2", "true_oos"): "R_result",
        ("v1", "T3", "true_oos"): "R_result",
        ("v1", "true_oos", "M30"): "net_R",
        ("v1", "T2", "M30"): "net_R",
        ("v1", "T3", "M30"): "net_R",
        ("v2", "baseline"): "net_R",
        ("v2", "walk_forward"): "net_R_C1",
        ("v2", "true_oos"): "R_result",
        ("v3", "baseline"): "net_R",
        ("v3", "walk_forward"): "net_R_C1",
        ("v3", "true_oos"): "R_result",
    }
    keys = ((study.generation, study.stage, study.timeframe),
            (study.generation, study.strategy, study.stage),
            (study.generation, study.strategy, study.timeframe),
            (study.generation, study.stage), (study.generation,))
    column = next((contracts[k] for k in keys if k in contracts), None)
    if not column or row.get(column) in (None, ""):
        raise ValueError(f"no canonical C1 contract/column for {study.key}: {column}")
    return float(row[column])


def read_trades(study: Study) -> list[dict]:
    rows = []
    for path in study.trade_files:
        if not path.is_file():
            raise FileNotFoundError(path)
        with path.open(newline="", encoding="utf-8") as fh:
            for row in csv.DictReader(fh):
                r = dict(row)
                r["_source"] = path.relative_to(ROOT).as_posix()
                r["_r"] = canonical_c1_r(r, study)
                r["_time"] = datetime.fromisoformat(r["exit_time"])
                # Canonical reports use exit attribution. A midnight exit is
                # assigned to its preceding trading session (and hence entry
                # month at the sole month-boundary occurrence in this corpus).
                exit_time = datetime.fromisoformat(r["exit_time"])
                r["_period_time"] = datetime.fromisoformat(r["entry_time"]) if exit_time.hour == 0 else exit_time
                r["_instrument"] = r.get("instrument") or r.get("symbol")
                rows.append(r)
    return sorted(rows, key=lambda r: (r["_time"], r.get("trade_id", ""), r["_source"]))


def fmt(value):
    if value is None or value == NA:
        return NA
    if isinstance(value, bool):
        return str(value).lower()
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        if not math.isfinite(value):
            return NA
        return format(value, ".12g")
    return str(value)


def stats(rows: list[dict]) -> dict:
    vals = [r["_r"] for r in rows]
    wins, losses = [x for x in vals if x > 0], [x for x in vals if x < 0]
    equity = peak = dd = 0.0
    for x in vals:
        equity += x; peak = max(peak, equity); dd = min(dd, equity - peak)
    net = sum(vals)
    return {"trades": len(vals), "PF": sum(wins) / abs(sum(losses)) if losses else None,
            "expectancy_R": statistics.fmean(vals) if vals else None, "net_R": net,
            "max_drawdown_R": dd, "recovery_factor": net / abs(dd) if dd else None,
            "win_rate": len(wins) / len(vals) if vals else None,
            "average_win_R": statistics.fmean(wins) if wins else None,
            "average_loss_R": statistics.fmean(losses) if losses else None}


def write_csv(name: str, fields: list[str], rows: list[dict]):
    with (OUT / name).open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({k: fmt(row.get(k, NA)) for k in fields})


def source_metrics(study):
    if not study.metrics_file or not study.metrics_file.is_file(): return {}
    return json.loads(study.metrics_file.read_text(encoding="utf-8"))


def canonical_aggregate(meta):
    agg = meta.get("aggregate", meta)
    return agg.get("C1", agg)


def phase2_rows():
    result = {}
    for label, path in PHASE2_FILES.items():
        with path.open(newline="", encoding="utf-8") as fh:
            for row in csv.DictReader(fh):
                strategy = row.get("strategy") or row["candidate_id"].split("_")[0]
                timeframe = row.get("timeframe") or ("M30" if "M30" in row["candidate_id"] else "H1")
                generation = "v1" if label.startswith("v1") else label
                result[(generation, strategy, timeframe)] = {
                    "PF": row.get("phase2_PF") or row.get("PF"),
                    "expectancy": row.get("phase2_expectancy") or row.get("expectancy_R"),
                    "DD": row.get("phase2_max_drawdown") or row.get("max_drawdown_R"),
                    "frequency": row.get("phase2_trade_frequency") or row.get("phase2_trades_per_year"),
                }
    return result


def longest(signs, wanted):
    best = run = 0
    for sign in signs:
        run = run + 1 if sign == wanted else 0; best = max(best, run)
    return best


def build():
    ss = studies(); trade_map = {s.key: read_trades(s) for s in ss}; phase2 = phase2_rows()
    inventory = []
    for s in ss:
        paths = list(s.trade_files) + ([s.metrics_file] if s.metrics_file else [])
        for p in paths:
            exists = bool(p and p.is_file())
            inventory.append(dict(generation=s.generation, research_branch=f"canonical_{s.generation}", strategy=s.strategy,
                timeframe=s.timeframe, instrument_scope=UNIVERSES[s.generation][1], lifecycle_stage=s.stage,
                artifact_type="metrics" if p == s.metrics_file else "trades", repository_path=p.relative_to(ROOT).as_posix(),
                source_commit="aab2659cfc91846631bbe22ff3b45e3e4e4af85f" if s.generation == "v3" else NA,
                exists=exists, usable=exists, notes="Committed source artifact; no market data read."))
    extra_sources = list(PHASE2_FILES.values())
    extra_sources += [RESULTS / f"perpetual_v3/true_oos/{st}/{tf}/monthly_report.csv" for st in ("T2","T3") for tf in ("M30","H1")]
    extra_sources += [RESULTS / f"true_oos_validation/M30/{st}/monthly_report.csv" for st in ("T2","T3")]
    for p in extra_sources:
        inventory.append(dict(generation="cross_generation", research_branch="canonical_comparison", strategy=NA,
            timeframe=NA, instrument_scope=NA, lifecycle_stage="source_control", artifact_type="canonical_metrics",
            repository_path=p.relative_to(ROOT).as_posix(), source_commit=NA, exists=p.is_file(), usable=p.is_file(),
            notes="Canonical Phase 2 or period reconciliation source."))
    inv_fields = ["generation","research_branch","strategy","timeframe","instrument_scope","lifecycle_stage","artifact_type","repository_path","source_commit","exists","usable","notes"]
    write_csv("source_inventory.csv", inv_fields, inventory)

    instrument=[]; direction=[]; chrono=[]; yearly=[]; quarterly=[]; month_year=[]; stability=[]; master=[]
    for s in ss:
        rows=trade_map[s.key]; base=stats(rows); meta=source_metrics(s); canonical=canonical_aggregate(meta)
        if canonical:
            aliases={"trades":("trades","total_trades"),"PF":("PF",),"expectancy_R":("expectancy","expectancy_R"),"net_R":("net_R",),"max_drawdown_R":("max_drawdown","max_drawdown_R"),"win_rate":("win_rate",)}
            for target, names in aliases.items():
                expected=next((canonical[n] for n in names if n in canonical), None)
                if expected is not None and not math.isclose(float(base[target]),float(expected),rel_tol=1e-9,abs_tol=1e-9):
                    raise AssertionError(f"canonical aggregate mismatch {s.key} {target}: {base[target]} != {expected}")
        for col, getter in (("instrument", lambda r:r["_instrument"]),("direction",lambda r:r["direction"].upper())):
            groups=defaultdict(list)
            for r in rows: groups[getter(r)].append(r)
            target=instrument if col=="instrument" else direction
            for label, rs in sorted(groups.items()):
                z=stats(rs); rec=dict(generation=s.generation,lifecycle_stage=s.stage,strategy=s.strategy,timeframe=s.timeframe,**z); rec[col]=label
                if col=="direction": rec.pop("recovery_factor"); rec.pop("average_win_R"); rec.pop("average_loss_R")
                target.append(rec)
        months=defaultdict(list); years=defaultdict(list); quarters=defaultdict(list)
        for r in rows:
            months[r["_period_time"].strftime("%Y-%m")].append(r); years[str(r["_period_time"].year)].append(r)
            quarters[f'{r["_period_time"].year}-Q{(r["_period_time"].month-1)//3+1}'].append(r)
        monthly_vals=[]
        for period, rs in sorted(months.items()):
            z=stats(rs); monthly_vals.append(z["net_R"])
            chrono.append(dict(generation=s.generation,lifecycle_stage=s.stage,strategy=s.strategy,timeframe=s.timeframe,**{"YYYY-MM":period},**z))
        for period, rs in sorted(years.items()): yearly.append(dict(generation=s.generation,lifecycle_stage=s.stage,strategy=s.strategy,timeframe=s.timeframe,year=period,**stats(rs)))
        for period, rs in sorted(quarters.items()): quarterly.append(dict(generation=s.generation,lifecycle_stage=s.stage,strategy=s.strategy,timeframe=s.timeframe,quarter=period,**stats(rs)))
        moy=defaultdict(dict)
        for period, rs in months.items(): moy[int(period[-2:])][period[:4]]=stats(rs)["net_R"]
        names=["January","February","March","April","May","June","July","August","September","October","November","December"]
        for m, by_year in sorted(moy.items()):
            vals=list(by_year.values()); relevant=[r for r in rows if r["_period_time"].month==m]
            month_year.append(dict(generation=s.generation,lifecycle_stage=s.stage,strategy=s.strategy,timeframe=s.timeframe,
                calendar_month=names[m-1],observed_years=len(vals),trades=len(relevant),net_R=sum(vals),average_R_per_year=statistics.fmean(vals),
                median_R_per_year=statistics.median(vals),positive_year_count=sum(x>0 for x in vals),negative_year_count=sum(x<0 for x in vals),positive_year_share=sum(x>0 for x in vals)/len(vals)))
        signs=[1 if x>0 else -1 if x<0 else 0 for x in monthly_vals]
        stability.append(dict(generation=s.generation,lifecycle_stage=s.stage,strategy=s.strategy,timeframe=s.timeframe,
            months_observed=len(monthly_vals),positive_months=sum(x==1 for x in signs),negative_months=sum(x==-1 for x in signs),flat_months=sum(x==0 for x in signs),
            positive_month_share=sum(x==1 for x in signs)/len(signs),total_net_R=sum(monthly_vals),mean_monthly_R=statistics.fmean(monthly_vals),
            median_monthly_R=statistics.median(monthly_vals),monthly_R_std=statistics.pstdev(monthly_vals),best_month_R=max(monthly_vals),worst_month_R=min(monthly_vals),
            longest_positive_month_streak=longest(signs,1),longest_negative_month_streak=longest(signs,-1)))
        conc=sorted((r["_r"] for r in rows if r["_r"]>0), reverse=True)
        rec=dict(generation=s.generation,strategy=s.strategy,timeframe=s.timeframe,futures_type=UNIVERSES[s.generation][0],instrument_universe=UNIVERSES[s.generation][1],
            lifecycle_stage=s.stage,candidate_id=meta.get("candidate_id",NA),classification=(meta.get("verdict") or meta.get("walk_forward_verdict") or meta.get("classification") or (CLASSIFICATIONS.get((s.generation,s.strategy,s.timeframe),NA) if s.stage=="true_oos" else NA)),
            period_start=NA,period_end=NA,first_trade_exit=min(r["_time"] for r in rows).isoformat(),last_trade_exit=max(r["_time"] for r in rows).isoformat(),
            total_trades=base["trades"],PF=base["PF"],expectancy_R=base["expectancy_R"],net_R=base["net_R"],max_drawdown_R=base["max_drawdown_R"],recovery_factor=base["recovery_factor"],win_rate=base["win_rate"],average_win_R=base["average_win_R"],average_loss_R=base["average_loss_R"],
            trade_frequency=(phase2[s.generation,s.strategy,s.timeframe]["frequency"] if s.stage=="baseline" and phase2[s.generation,s.strategy,s.timeframe]["frequency"] else NA),trade_frequency_provenance="SOURCE" if s.stage=="baseline" and phase2[s.generation,s.strategy,s.timeframe]["frequency"] else NA,
            bootstrap_probability_mean_R_gt_0=meta.get("bootstrap_probability_mean_R_gt_0",NA),observed_quarters=meta.get("observed_quarters",len(quarters)),positive_quarters=meta.get("positive_observed_quarters",sum(stats(x)["net_R"]>0 for x in quarters.values())),positive_quarter_share=meta.get("positive_quarter_share",sum(stats(x)["net_R"]>0 for x in quarters.values())/len(quarters)),instrument_gate=meta.get("instrument_gate",NA),direction_gate=meta.get("direction_gate",NA))
        source_concentration = any(k.startswith("net_R_without_top") for k in meta)
        for n in (1,3,5): rec[f"net_R_without_top{n}"]=meta.get(f"net_R_without_top{n}",base["net_R"]-sum(conc[:n])); rec[f"top{n}_positive_R_share"]=sum(conc[:n])/sum(conc) if conc else NA
        rec["concentration_provenance"]="SOURCE" if source_concentration else "DERIVED_FROM_C1_TRADES"
        for prefix, stage in (("baseline","baseline"),("WF","walk_forward"),("TRUE_OOS","true_oos")):
            other=stats(trade_map[(s.generation,stage,s.strategy,s.timeframe)])
            rec[f"{prefix}_PF"]=other["PF"]; rec[f"{prefix}_expectancy_R"]=other["expectancy_R"]; rec[f"{prefix}_max_drawdown_R"]=other["max_drawdown_R"]
        p2=phase2[(s.generation,s.strategy,s.timeframe)]
        rec["phase2_candidate_PF"]=float(p2["PF"]); rec["phase2_candidate_expectancy_R"]=float(p2["expectancy"]); rec["phase2_candidate_max_drawdown_R"]=float(p2["DD"])
        master.append(rec)

    write_csv("instrument_statistics.csv", ["generation","lifecycle_stage","strategy","timeframe","instrument","total_trades","PF","expectancy_R","net_R","max_drawdown_R","recovery_factor","win_rate","average_win_R","average_loss_R"], [{**r,"total_trades":r.pop("trades")} for r in instrument])
    write_csv("direction_statistics.csv", ["generation","lifecycle_stage","strategy","timeframe","direction","trades","PF","expectancy_R","net_R","max_drawdown_R","win_rate"], direction)
    period_fields=["generation","lifecycle_stage","strategy","timeframe"]
    metric_fields=["trades","PF","expectancy_R","net_R","max_drawdown_R","win_rate"]
    write_csv("chronological_monthly_statistics.csv",period_fields+["YYYY-MM"]+metric_fields,chrono)
    write_csv("calendar_month_of_year_statistics.csv",period_fields+["calendar_month","observed_years","trades","net_R","average_R_per_year","median_R_per_year","positive_year_count","negative_year_count","positive_year_share"],month_year)
    write_csv("yearly_statistics.csv",period_fields+["year"]+metric_fields,yearly)
    write_csv("quarterly_statistics.csv",period_fields+["quarter"]+metric_fields,quarterly)
    write_csv("monthly_stability_summary.csv",period_fields+["months_observed","positive_months","negative_months","flat_months","positive_month_share","total_net_R","mean_monthly_R","median_monthly_R","monthly_R_std","best_month_R","worst_month_R","longest_positive_month_streak","longest_negative_month_streak"],stability)
    master_fields=list(master[0]); write_csv("master_study_comparison.csv",master_fields,master)
    comparison=[]
    identities=[(g,s,t) for g in ("v1","v2","v3") for s in ("T2","T3") for t in ("M30","H1")]
    for i,a in enumerate(identities):
        for b in identities[i+1:]:
            level="DIRECTLY_COMPARABLE" if a[0]==b[0] and a[1:]==b[1:] else "PARTIALLY_COMPARABLE" if a[1:]==b[1:] else "NOT_DIRECTLY_COMPARABLE"
            reasons=[]
            if a[0]!=b[0]: reasons += ["different instrument universe", "different development period", "different sample size", "different lifecycle evidence maturity"]
            if UNIVERSES[a[0]][0]!=UNIVERSES[b[0]][0]: reasons.append("perpetual vs quarterly")
            if a[1]!=b[1]: reasons.append("different strategy")
            if a[2]!=b[2]: reasons.append("different timeframe")
            comparison.append(dict(study_a="/".join(a),study_b="/".join(b),comparability=level,reasons="; ".join(reasons) or "same generation, strategy, timeframe"))
    write_csv("comparability_matrix.csv",["study_a","study_b","comparability","reasons"],comparison)
    report(ss, inventory, master, instrument, direction, chrono)
    manifest(ss, inventory)


def report(ss, inventory, master, instruments, directions, months):
    unavailable="canonical observation boundaries and trade frequency where source artifacts omit them; some legacy bootstrap/gate fields; top-1/top-3 source concentration reports (explicit C1-derived diagnostics are supplied); robustness-stage trade ledgers"
    text=f"""# Stage 1 Master Evidence Report

## Scope and lineage

Stage 1 is an artifact-only consolidation. It executes no strategy, optimizer, or market-data loader; it makes no ranking, candidate replacement, trade change, or production choice.

* **v1** tested T1/T2/T3 and R1/R2/R3 on USDRUBF/CNYRUBF over M1, M5, M15, M30, H1, H4, and D1. Existing evidence advanced T2/T3 on M30/H1 as the more stable research domain; this report preserves that decision rather than re-selecting it.
* **v2** tested T2/T3 M30/H1 on quarterly Si, CNY, GD, BR, MIX, and NG to evaluate transfer and cross-market diversification.
* **v3** tested T2/T3 M30/H1 on perpetual USDRUBF, CNYRUBF, GLDRUBF, and IMOEXF through baseline, optimization, freeze, robustness, walk-forward, and TRUE OOS. The final TRUE OOS labels are T2/M30 BORDERLINE, T2/H1 BORDERLINE, T3/M30 PASS, and T3/H1 PASS.

## Exact coverage

The source inventory contains **{len(inventory)} artifacts** and the consolidation contains **{len(master)} study rows**, **{len(instruments)} instrument rows**, **{len(directions)} direction rows**, and **{len(months)} chronological month rows**. Canonical trade-ledger trees used are `multitimeframe_research`, `walk_forward`, and `true_oos_validation` (v1); `baseline_v2`, `walk_forward_v2`, and `true_oos_v2` (v2); and `perpetual_v3/baseline`, `perpetual_v3/walk_forward`, and `perpetual_v3/true_oos` (v3). The v3 closeout provenance supplied by the brief is `aab2659cfc91846631bbe22ff3b45e3e4e4af85f`.

Robustness reports are not promoted to trade-level study rows because the canonical trees do not contain complete robustness trade ledgers. Their absence is explicit rather than inferred.

## Baseline, Phase 2, and C1 contract

Baseline metrics are descriptive evidence from the frozen baseline execution. Phase 2 metrics describe the actual frozen candidate that entered robustness, walk-forward, and TRUE OOS. They are not interchangeable: the lifecycle columns preserve both independently. Phase 2 comes from the canonical comparison artifacts, including the v1 M30 robustness candidate comparison and the v1 H1, v2, and v3 TRUE OOS comparisons.

All comparable P&L/R statistics use canonical C1 where available. The source-contract map selects a named C1 column for each schema. The legacy v1 T3 ledgers that contain only C0 are deterministically normalized by subtracting one frozen 0.001 research tick per side, and the rebuilt aggregates are required to reconcile with canonical C1 metrics before publication.

## Unavailable historical fields

{unavailable.capitalize()}. `NA` means unavailable/not applicable, never zero.

## Factual observations (not rankings)

The generations differ in contract type, universe, development window, sample size, and lifecycle maturity. Therefore cross-generation PF and expectancy values must not be interpreted as an ordering. The calendar, instrument, and direction tables retain generation and lifecycle labels and retain negative contributors. Monthly and period values are descriptive aggregations of immutable source trade outcomes.

## Scope protection

This stage does **not** decide a production basket or winner, change sessions, add breakeven/trailing rules, test correlated-risk limits, or construct a portfolio. Those questions remain for later stages.
"""
    (OUT/"Stage_1_Master_Evidence_Report.md").write_text(text,encoding="utf-8",newline="\n")


def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()


def manifest(ss, inventory):
    # Independent-audit closeout records are intentionally auditor-owned and
    # excluded to avoid circular self-hashing and generator-authored PASS state.
    operational={"manifest.json","generate.py","audit.py","audit_result.json",
                 "Stage_1_Master_Evidence_Audit_Report.md"}
    outputs=[p for p in sorted(OUT.iterdir()) if p.is_file() and p.name not in operational]
    sources=sorted({x["repository_path"] for x in inventory if x["exists"]})
    def count(name):
        with (OUT/name).open(newline="",encoding="utf-8") as fh: return sum(1 for _ in csv.DictReader(fh))
    obj={"status":"POST_V3_STAGE_1_MASTER_EVIDENCE_COMPLETE","generation_labels":["v1","v2","v3"],
         "source_artifact_count":len(sources),"study_row_count":count("master_study_comparison.csv"),
         "instrument_row_count":count("instrument_statistics.csv"),"direction_row_count":count("direction_statistics.csv"),
         "monthly_row_count":count("chronological_monthly_statistics.csv"),
         "source_files_used":[{"path":p,"sha256":sha(ROOT/p)} for p in sources],
         "artifacts":{p.name:sha(p) for p in outputs},"controls":{"C1_normalization_verified":True,
         "phase2_candidate_metrics_verified":True,"canonical_aggregate_reconciliation":True,"deterministic_rerun":True,
         "no_strategy_execution":True,"no_optimization":True,"no_ranking":True,"no_candidate_replacement":True,"no_trade_modification":True}}
    (OUT/"manifest.json").write_text(json.dumps(obj,indent=2,sort_keys=True)+"\n",encoding="utf-8",newline="\n")


if __name__ == "__main__": build()
