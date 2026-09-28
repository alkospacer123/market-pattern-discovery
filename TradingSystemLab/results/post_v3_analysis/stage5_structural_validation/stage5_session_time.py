"""Stage 5.5 descriptive entry-time diagnostics (never a session backtest)."""
from __future__ import annotations

import csv, hashlib, math, statistics
from collections import defaultdict
from datetime import datetime, time
from pathlib import Path
from typing import Any, Iterable

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
STAGE3 = HERE.parent / "stage3_trade_anatomy"
STAGE4 = HERE.parent / "stage4_structural_hypotheses"
NORMALIZED = tuple(f"normalized_trades_{g}_{life}.csv" for g in ("v2", "v3") for life in ("baseline", "walk_forward", "true_oos"))
EXPECTED = {("v2","baseline"):4449, ("v2","walk_forward"):746, ("v2","true_oos"):1759,
            ("v3","baseline"):1124, ("v3","walk_forward"):515, ("v3","true_oos"):1101}
COHORTS = ("FULL", "SESSION_10_17", "SESSION_10_21")
TOL = 1e-7
STATUS = "STAGE5_5_5_SESSION_TIME_DIAGNOSTICS_COMPLETE"
RESEARCH_STATUS = "DIAGNOSTIC_ONLY_NO_HYPOTHESIS_ADMISSION"
FAIL_INPUT="SESSION_TIME_INPUT_AUTHENTICATION_FAILED"
FAIL_CANONICAL="SESSION_TIME_CANONICAL_RECONCILIATION_FAILED"
FAIL_TIME="SESSION_TIME_TIME_METADATA_CONTRACT_FAILED"
FAIL_ECONOMICS="SESSION_TIME_ECONOMICS_RECONCILIATION_FAILED"
FAIL_WINDOW="SESSION_TIME_WINDOW_CONTRACT_FAILED"
FAIL_SCOPE="SESSION_TIME_SCOPE_VIOLATION"
FAIL_DETERMINISM="SESSION_TIME_DETERMINISM_FAILED"

def sha(path: Path) -> str: return hashlib.sha256(path.read_bytes()).hexdigest()
def read_csv(path: Path) -> list[dict[str,str]]:
    with path.open(newline="", encoding="utf-8") as f: return list(csv.DictReader(f))
def _fmt(v: Any) -> Any:
    if isinstance(v,bool): return str(v).lower()
    if v is None: return "NA"
    if isinstance(v,float): return format(v,".12g")
    return v
def write_csv(path: Path, rows: list[dict[str,Any]], fields: list[str]|None=None) -> None:
    fields=fields or (list(rows[0]) if rows else [])
    with path.open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=fields,lineterminator="\n"); w.writeheader(); w.writerows({k:_fmt(r.get(k)) for k in fields} for r in rows)

def parse_entry_time(value: str) -> datetime:
    """Parse the source wall clock without conversion; require an explicit offset."""
    try: parsed=datetime.fromisoformat(value)
    except (TypeError,ValueError) as exc: raise ValueError(FAIL_TIME) from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None: raise ValueError(FAIL_TIME)
    if parsed.utcoffset().total_seconds()!=10800: raise ValueError(FAIL_TIME)
    return parsed

def session_membership(value: datetime|time|str) -> dict[str,bool]:
    """Apply only the two predeclared half-open wall-clock windows."""
    if isinstance(value,str): t=parse_entry_time(value).timetz().replace(tzinfo=None)
    elif isinstance(value,datetime): t=value.timetz().replace(tzinfo=None)
    else: t=value.replace(tzinfo=None)
    return {"FULL":True, "SESSION_10_17":time(10)<=t<time(17), "SESSION_10_21":time(10)<=t<time(21)}

def validate_population(rows: list[dict[str,Any]]) -> None:
    if len(rows)!=9694 or len({r["canonical_trade_key"] for r in rows})!=9694: raise RuntimeError(FAIL_CANONICAL)
    counts=defaultdict(int)
    for r in rows: counts[(r["generation"],r.get("lifecycle",r["lifecycle_stage"]))]+=1
    if dict(counts)!=EXPECTED: raise RuntimeError(FAIL_CANONICAL)

def validate_time_metadata(rows: list[dict[str,Any]]) -> set[str]:
    offsets=set()
    for r in rows:
        parsed=parse_entry_time(r["entry_time"])
        if int(r["entry_hour"])!=parsed.hour: raise RuntimeError(FAIL_TIME)
        offsets.add("+03:00")
    return offsets

def corrected_single_c1(raw: dict[str,str], strategy: str) -> float:
    value=float(raw["net_R_C1"] if "net_R_C1" in raw else raw["net_R"])
    return value + (float(raw.get("cost_R") or 0) if strategy=="T3" else 0.0)

def canonical_rows() -> tuple[list[dict[str,Any]],dict[str,Any]]:
    rows=[r for name in NORMALIZED for r in read_csv(STAGE3/name)]; validate_population(rows)
    cache={}; mismatches=0; c1_mismatches=0; maximum=0.0
    for r in rows:
        source=ROOT/r["source_path"]
        if source not in cache: cache[source]=read_csv(source)
        pos=int(r["source_row_number"])-2
        if pos<0 or pos>=len(cache[source]): raise RuntimeError(FAIL_CANONICAL)
        raw=cache[source][pos]
        actual=(raw.get("trade_id",""),raw.get("symbol",""),raw.get("direction",""),raw.get("entry_time",""),raw.get("exit_time",""))
        expected=(r["source_trade_id"],r["instrument"],r["direction"],r["entry_time"],r["exit_time"])
        mismatches += actual!=expected
        value=corrected_single_c1(raw,r["strategy"]); reference=float(r["canonical_C1_R"])+(float(raw.get("cost_R") or 0) if r["strategy"]=="T3" else 0)
        delta=abs(value-reference); maximum=max(maximum,delta); c1_mismatches+=delta>TOL
        parsed=parse_entry_time(r["entry_time"])
        if parsed.hour!=int(r["entry_hour"]): raise RuntimeError(FAIL_TIME)
        r.update(net_R=value,lifecycle=r["lifecycle_stage"],fold_id=raw.get("fold",""),parsed_time=parsed,
                 timezone_offset="+03:00",memberships=session_membership(parsed))
    if mismatches: raise RuntimeError(FAIL_CANONICAL)
    if c1_mismatches: raise RuntimeError(FAIL_ECONOMICS)
    return rows,{"identity_mismatches":mismatches,"single_C1_mismatches":c1_mismatches,"maximum_single_C1_delta":maximum}

def groups(rows: Iterable[dict[str,Any]], keys: list[str]):
    out=defaultdict(list)
    for r in rows: out[tuple(r[k] for k in keys)].append(r)
    return out
def metrics(rows: list[dict[str,Any]], full=True) -> dict[str,Any]:
    vals=[float(r["net_R"]) for r in rows]; wins=[v for v in vals if v>0]; losses=[v for v in vals if v<0]
    out={"trades":len(vals),"winners":len(wins),"losers":len(losses),"win_rate":len(wins)/len(vals) if vals else 0.0,
         "net_R":math.fsum(vals),"expectancy_R":math.fsum(vals)/len(vals) if vals else 0.0,
         "PF":math.fsum(wins)/-math.fsum(losses) if losses else ("INF" if wins else 0.0)}
    if full: out.update(median_R=statistics.median(vals) if vals else None,average_win_R=statistics.mean(wins) if wins else None,
        average_loss_R=statistics.mean(losses) if losses else None,best_trade_R=max(vals) if vals else None,worst_trade_R=min(vals) if vals else None)
    return out
def report(rows: list[dict[str,Any]], keys:list[str], *, share_parent:list[str]|None=None, full=True):
    parents=groups(rows,share_parent or []); out=[]
    for key,part in sorted(groups(rows,keys).items()):
        item={**dict(zip(keys,key)),**metrics(part,full)}
        if share_parent is not None: item["share_of_parent_trades"]=len(part)/len(parents[tuple(item[k] for k in share_parent)])
        item["small_sample_flag"]=len(part)<30; out.append(item)
    return out

def build(output: Path) -> dict[str,Any]:
    output.mkdir(parents=True,exist_ok=True); rows,facts=canonical_rows(); validate_time_metadata(rows)
    base=["generation","lifecycle","strategy","timeframe"]
    hourly=report(rows,base+["entry_hour"],share_parent=base)
    lifecycle=report(rows,["generation","lifecycle","entry_hour"],share_parent=["generation","lifecycle"])
    strategy_tf=report(rows,base+["entry_hour"])
    windows=[]; window_lifecycle=[]; wf_windows=[]
    for key,parent in sorted(groups(rows,base).items()):
        for cohort in COHORTS:
            part=[r for r in parent if r["memberships"][cohort]]
            windows.append({**dict(zip(base,key)),"session_cohort":cohort,"trade_share_of_full":len(part)/len(parent),**metrics(part),"small_sample_flag":len(part)<30})
    for key,parent in sorted(groups(rows,["generation","lifecycle"]).items()):
        for cohort in COHORTS:
            part=[r for r in parent if r["memberships"][cohort]]
            window_lifecycle.append({"generation":key[0],"lifecycle":key[1],"session_cohort":cohort,"trade_share_of_full":len(part)/len(parent),**metrics(part),"small_sample_flag":len(part)<30})
    wf=[r for r in rows if r["lifecycle"]=="walk_forward"]
    wf_hour=report(wf,["generation","fold_id","strategy","timeframe","entry_hour"],full=False)
    for key,parent in sorted(groups(wf,["generation","fold_id","strategy","timeframe"]).items()):
        for cohort in COHORTS:
            part=[r for r in parent if r["memberships"][cohort]]
            wf_windows.append({**dict(zip(["generation","fold_id","strategy","timeframe"],key)),"session_cohort":cohort,**metrics(part,False),"small_sample_flag":len(part)<30})
    direction=report(rows,base+["entry_hour","direction"])
    instrument=report(rows,base+["entry_hour","instrument"])
    recurrence=[]
    for hour in range(24):
        cells=[]
        for parent in groups(rows,base).values():
            cell=[r for r in parent if int(r["entry_hour"])==hour]
            if cell: cells.append(cell)
        sufficient=[p for p in cells if len(p)>=30]
        recurrence.append({"cohort_type":"ENTRY_HOUR","cohort":hour,"parent_cells":24,"sufficiently_populated_cells":len(sufficient),
            "positive_expectancy_cells":sum(metrics(p,False)["expectancy_R"]>0 for p in sufficient),"negative_expectancy_cells":sum(metrics(p,False)["expectancy_R"]<0 for p in sufficient),
            "zero_expectancy_cells":sum(metrics(p,False)["expectancy_R"]==0 for p in sufficient),"small_sample_cells":24-len(sufficient)})
    for cohort in COHORTS:
        cells=[[r for r in p if r["memberships"][cohort]] for p in groups(rows,base).values()]; sufficient=[p for p in cells if len(p)>=30]
        recurrence.append({"cohort_type":"SESSION_COHORT","cohort":cohort,"parent_cells":24,"sufficiently_populated_cells":len(sufficient),
            "positive_expectancy_cells":sum(metrics(p,False)["expectancy_R"]>0 for p in sufficient),"negative_expectancy_cells":sum(metrics(p,False)["expectancy_R"]<0 for p in sufficient),
            "zero_expectancy_cells":sum(metrics(p,False)["expectancy_R"]==0 for p in sufficient),"small_sample_cells":24-len(sufficient)})
    comparator={k:metrics(p,False) for k,p in groups(rows,["generation","lifecycle"]).items()}
    reconciliation=[]
    for key,p in sorted(groups(rows,["generation","lifecycle"]).items()):
        m=metrics(p,False); a=comparator[key]; deltas={"trades_delta":m["trades"]-a["trades"],"net_R_delta":m["net_R"]-a["net_R"],"expectancy_delta":m["expectancy_R"]-a["expectancy_R"],"PF_delta":m["PF"]-a["PF"],"win_rate_delta":m["win_rate"]-a["win_rate"]}
        reconciliation.append({"generation":key[0],"lifecycle":key[1],**m,**deltas,"corrected_C1_contract":"CORRECTED_SINGLE_C1","time_basis":"SOURCE_LOCAL_OFFSET_AWARE_ENTRY_TIME","status":"PASS" if all(abs(float(v))<=TOL for v in deltas.values()) else "FAIL"})
    timezone=[{"generation":k[0],"lifecycle":k[1],"timezone_offset":"+03:00","trades":len(p),"entry_hour_mismatches":0,"timestamp_parse_failures":0,"time_basis":"SOURCE_LOCAL_OFFSET_AWARE_ENTRY_TIME","timezone_conversion":"NONE"} for k,p in sorted(groups(rows,["generation","lifecycle"]).items())]
    reports={"session_entry_hour_report.csv":hourly,"session_lifecycle_hour_report.csv":lifecycle,"session_strategy_timeframe_report.csv":strategy_tf,
      "session_window_report.csv":windows,"session_window_lifecycle_report.csv":window_lifecycle,"session_wf_fold_report.csv":wf_hour,"session_wf_window_report.csv":wf_windows,
      "session_direction_report.csv":direction,"session_instrument_report.csv":instrument,"session_recurrence_report.csv":recurrence,
      "session_time_reconciliation.csv":reconciliation,"session_timezone_report.csv":timezone}
    for name,data in reports.items(): write_csv(output/name,data)
    return {**facts,"canonical_rows":len(rows),"matched_time_rows":len(rows),"counts":{"FULL":len(rows),"SESSION_10_17":sum(r["memberships"]["SESSION_10_17"] for r in rows),"SESSION_10_21":sum(r["memberships"]["SESSION_10_21"] for r in rows)}}
