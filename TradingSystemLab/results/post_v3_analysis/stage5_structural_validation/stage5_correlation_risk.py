"""Stage 5.6 correlation and simultaneous-position diagnostics.

This module is deliberately descriptive.  It neither selects pairs nor applies a
portfolio rule.  Intervals are source-local, offset-aware, half-open intervals.
"""
from __future__ import annotations

import csv, hashlib, math, statistics
from collections import defaultdict
from datetime import datetime
from itertools import combinations
from pathlib import Path
from typing import Any, Iterable

HERE=Path(__file__).resolve().parent; ROOT=HERE.parents[3]
STAGE2=HERE.parent/"stage2_portfolio_diversification"; STAGE3=HERE.parent/"stage3_trade_anatomy"
NORMALIZED=tuple(f"normalized_trades_{g}_{life}.csv" for g in ("v2","v3") for life in ("baseline","walk_forward","true_oos"))
EXPECTED={("v2","baseline"):4449,("v2","walk_forward"):746,("v2","true_oos"):1759,("v3","baseline"):1124,("v3","walk_forward"):515,("v3","true_oos"):1101}
TOL=1e-7; STATUS="STAGE5_5_6_CORRELATION_SIMULTANEOUS_RISK_DIAGNOSTICS_COMPLETE"
FAIL_INPUT="CORRELATION_RISK_INPUT_AUTHENTICATION_FAILED"; FAIL_CANONICAL="CORRELATION_RISK_CANONICAL_RECONCILIATION_FAILED"
FAIL_TIME="CORRELATION_RISK_TIME_INTERVAL_CONTRACT_FAILED"; FAIL_MONTHLY="CORRELATION_RISK_MONTHLY_CORRELATION_RECONCILIATION_FAILED"
FAIL_OVERLAP="CORRELATION_RISK_OVERLAP_RECONCILIATION_FAILED"; FAIL_CONCURRENCY="CORRELATION_RISK_CONCURRENCY_RECONCILIATION_FAILED"
FAIL_SCOPE="CORRELATION_RISK_SCOPE_VIOLATION"; FAIL_DETERMINISM="CORRELATION_RISK_DETERMINISM_FAILED"

def sha(p:Path)->str:return hashlib.sha256(p.read_bytes()).hexdigest()
def read_csv(p:Path):
    with p.open(newline="",encoding="utf-8") as f:return list(csv.DictReader(f))
def _fmt(v):
    if isinstance(v,bool):return str(v).lower()
    if isinstance(v,float):return format(v,".12g")
    return v
def write_csv(p:Path,rows:list[dict],fields=None):
    fields=fields or (list(rows[0]) if rows else [])
    with p.open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=fields,lineterminator="\n");w.writeheader();w.writerows({k:_fmt(r.get(k,"")) for k in fields} for r in rows)
def groups(rows:Iterable[dict],keys:list[str]):
    out=defaultdict(list)
    for r in rows:out[tuple(r[k] for k in keys)].append(r)
    return out
def parse_time(v:str)->datetime:
    try:x=datetime.fromisoformat(v)
    except (ValueError,TypeError) as e:raise ValueError(FAIL_TIME) from e
    if x.tzinfo is None or x.utcoffset() is None or x.utcoffset().total_seconds()!=10800:raise ValueError(FAIL_TIME)
    return x
def interval_overlap(a,b)->float:
    return max(0.0,(min(a[1],b[1])-max(a[0],b[0])).total_seconds())
def union_intervals(items):
    out=[]
    for start,end in sorted(items):
        if not out or start>out[-1][1]:out.append([start,end])
        elif end>out[-1][1]:out[-1][1]=end
    return [(a,b) for a,b in out]
def duration(items):return sum((b-a).total_seconds() for a,b in items)
def shared_duration(a,b):
    i=j=0;total=0.0
    while i<len(a) and j<len(b):
        total+=max(0.0,(min(a[i][1],b[j][1])-max(a[i][0],b[j][0])).total_seconds())
        if a[i][1]<=b[j][1]:i+=1
        else:j+=1
    return total
def corrected_single_c1(raw,strategy):return float(raw["net_R_C1"] if "net_R_C1" in raw else raw["net_R"])+(float(raw.get("cost_R") or 0) if strategy=="T3" else 0)

def canonical_rows():
    result=[];cache={}; ids=set()
    for name in NORMALIZED:
      for m in read_csv(STAGE3/name):
        source=ROOT/m["source_path"]
        if source not in cache:cache[source]=read_csv(source)
        raw=cache[source][int(m["source_row_number"])-2]
        identity=(raw.get("trade_id"),raw.get("symbol"),raw.get("direction"),raw.get("entry_time"),raw.get("exit_time"))
        expected=(m["source_trade_id"],m["instrument"],m["direction"],m["entry_time"],m["exit_time"])
        if identity!=expected:raise RuntimeError(FAIL_CANONICAL)
        entry,exit=parse_time(m["entry_time"]),parse_time(m["exit_time"])
        if exit<=entry:raise RuntimeError(FAIL_TIME)
        value=corrected_single_c1(raw,m["strategy"]); reference=float(m["canonical_C1_R"])+(float(raw.get("cost_R") or 0) if m["strategy"]=="T3" else 0)
        if abs(value-reference)>TOL:raise RuntimeError(FAIL_CANONICAL)
        row={**m,"lifecycle":m["lifecycle_stage"],"fold_id":raw.get("fold",""),"net_R":value,"entry":entry,"exit":exit}
        ids.add(m["canonical_trade_key"]);result.append(row)
    counts={k:len(v) for k,v in groups(result,["generation","lifecycle"]).items()}
    if len(result)!=9694 or len(ids)!=9694 or counts!=EXPECTED:raise RuntimeError(FAIL_CANONICAL)
    return result

def monthly_matrix(rows):
    historical=read_csv(STAGE2/"monthly_instrument_matrix.csv"); sums=defaultdict(list)
    for r in rows:
        month_dt=r["entry"] if r["exit"].hour==0 else r["exit"]
        sums[(r["generation"],r["lifecycle"],r["strategy"],r["timeframe"],month_dt.strftime("%Y-%m"),r["instrument"])].append(r["net_R"])
    out=[]
    for h in historical:
        key=(h["generation"],h["lifecycle_stage"],h["strategy"],h["timeframe"],h["YYYY-MM"],h["instrument"]); vals=sums.get(key,[])
        available=h["instrument_available"].lower()=="true"; net=math.fsum(vals) if available else 0.0; trades=len(vals) if available else 0
        out.append({**h,"trades":trades,"net_R":net,"positive_month":available and net>0,"negative_month":available and net<0,"zero_month":available and net==0,
                    "economic_contract":"CORRECTED_SINGLE_C1_CURRENT_AUTHORITY"})
    return out
def correlation(x,y):
    if len(x)<2:return 0.0,0.0
    mx,my=statistics.mean(x),statistics.mean(y);cov=math.fsum((a-mx)*(b-my) for a,b in zip(x,y))/(len(x)-1)
    sx=statistics.stdev(x);sy=statistics.stdev(y);return (cov/(sx*sy) if sx and sy else 0.0),cov
def pairwise_monthly(matrix):
    hist=read_csv(STAGE2/"pairwise_monthly_correlation.csv"); lookup={(r["generation"],r["lifecycle_stage"],r["strategy"],r["timeframe"],r["YYYY-MM"],r["instrument"]):r for r in matrix};out=[]
    for h in hist:
      base=(h["generation"],h["lifecycle_stage"],h["strategy"],h["timeframe"]); months=sorted({k[4] for k in lookup if k[:4]==base}); pairs=[];partial=0
      for month in months:
        a,b=lookup[base+(month,h["instrument_a"])],lookup[base+(month,h["instrument_b"])]
        if a["instrument_available"]=="true" and b["instrument_available"]=="true":pairs.append((float(a["net_R"]),float(b["net_R"])));partial+=a["partial_coverage_month"]=="true" or b["partial_coverage_month"]=="true"
      x=[p[0] for p in pairs];y=[p[1] for p in pairs];pear,cov=correlation(x,y)
      out.append({**{k:h[k] for k in ("generation","lifecycle_stage","strategy","timeframe","instrument_a","instrument_b")},"lifecycle":h["lifecycle_stage"],"overlapping_months":len(pairs),"partial_overlap_months":partial,
       "stage2_historical_pearson_monthly_R":float(h["pearson_monthly_R"]),"corrected_pearson_monthly_R":pear,"pearson_delta":pear-float(h["pearson_monthly_R"]),
       "stage2_historical_covariance_monthly_R":float(h["covariance_monthly_R"]),"corrected_covariance_monthly_R":cov,"covariance_delta":cov-float(h["covariance_monthly_R"]),
       "corrected_same_sign_months":sum(a*b>0 for a,b in pairs),"corrected_opposite_sign_months":sum(a*b<0 for a,b in pairs),"corrected_both_negative_months":sum(a<0 and b<0 for a,b in pairs),"corrected_both_positive_months":sum(a>0 and b>0 for a,b in pairs),
       "sample_flag":"LOW_SAMPLE" if len(pairs)<6 else "ADEQUATE","economic_contract":"CORRECTED_SINGLE_C1_CURRENT_AUTHORITY"})
    return out

def sweep(rows):
    events=defaultdict(lambda:{"exit":[],"entry":[]})
    for r in rows:events[r["exit"]]["exit"].append(r);events[r["entry"]]["entry"].append(r)
    open_={};contexts=[];distribution=defaultdict(lambda:[0,0.0]);previous=None
    for stamp in sorted(events):
        if previous is not None and open_:
            distribution[len(open_)][0]+=1;distribution[len(open_)][1]+=(stamp-previous).total_seconds()
        for r in sorted(events[stamp]["exit"],key=lambda x:x["canonical_trade_key"]):open_.pop(r["canonical_trade_key"])
        for r in sorted(events[stamp]["entry"],key=lambda x:x["canonical_trade_key"]):
            values=list(open_.values());same_i=sum(x["instrument"]==r["instrument"] for x in values);same_d=sum(x["direction"]==r["direction"] for x in values)
            item={k:r[k] for k in ("canonical_trade_key","generation","lifecycle","fold_id","strategy","timeframe","instrument","direction","entry_time","exit_time","net_R")}
            item.update(open_positions_before_entry=len(values),open_positions_after_entry=len(values)+1,same_instrument_open_before=same_i,same_direction_open_before=same_d,
              same_instrument_same_direction_open_before=sum(x["instrument"]==r["instrument"] and x["direction"]==r["direction"] for x in values),same_instrument_opposite_direction_open_before=sum(x["instrument"]==r["instrument"] and x["direction"]!=r["direction"] for x in values),nominal_initial_R_units_before=len(values),nominal_initial_R_units_after=len(values)+1)
            contexts.append(item);open_[r["canonical_trade_key"]]=r
        previous=stamp
    if open_:raise RuntimeError(FAIL_CONCURRENCY)
    return contexts,distribution

def pair_metrics(a,b):
    ua=union_intervals([(r["entry"],r["exit"]) for r in a]);ub=union_intervals([(r["entry"],r["exit"]) for r in b]);da,db=duration(ua),duration(ub);shared=shared_duration(ua,ub);union=da+db-shared
    counts=defaultdict(int);idsa=set();idsb=set()
    for x in a:
      for y in b:
        if interval_overlap((x["entry"],x["exit"]),(y["entry"],y["exit"]))>0:
          counts["overlapping_trade_pairs"]+=1;idsa.add(x["canonical_trade_key"]);idsb.add(y["canonical_trade_key"])
          counts["same_direction_overlapping_pairs" if x["direction"]==y["direction"] else "opposite_direction_overlapping_pairs"]+=1
          vx,vy=x["net_R"],y["net_R"]
          counts["zero_involved_pairs" if vx==0 or vy==0 else "both_final_negative_pairs" if vx<0 and vy<0 else "both_final_positive_pairs" if vx>0 and vy>0 else "opposite_final_sign_pairs"]+=1
    return {"active_duration_A_hours":da/3600,"active_duration_B_hours":db/3600,"shared_active_duration_hours":shared/3600,"union_active_duration_hours":union/3600,
      "overlap_share_A":shared/da if da else 0,"overlap_share_B":shared/db if db else 0,"overlap_jaccard":shared/union if union else 0,"unique_A_trades_with_overlap":len(idsa),"unique_B_trades_with_overlap":len(idsb),
      **{k:counts[k] for k in ("overlapping_trade_pairs","same_direction_overlapping_pairs","opposite_direction_overlapping_pairs","both_final_negative_pairs","both_final_positive_pairs","opposite_final_sign_pairs","zero_involved_pairs")}}

def build(output:Path):
    output.mkdir(parents=True,exist_ok=True);rows=canonical_rows();matrix=monthly_matrix(rows);corr=pairwise_monthly(matrix)
    contexts=[];dist_rows=[];summaries=[];recon=[]
    for key,part in sorted(groups(rows,["generation","lifecycle"]).items()):
      ctx,dist=sweep(part);contexts+=ctx;active=sum(v[1] for v in dist.values());individual=sum((r["exit"]-r["entry"]).total_seconds() for r in part);integrated=sum(k*v[1] for k,v in dist.items())
      for level,(segments,seconds) in sorted(dist.items()):dist_rows.append({"generation":key[0],"lifecycle":key[1],"concurrency_level":level,"segment_count":segments,"duration_seconds":seconds,"duration_hours":seconds/3600,"share_of_active_portfolio_time":seconds/active,"nominal_initial_R_units":level})
      summaries.append({"generation":key[0],"lifecycle":key[1],"trades":len(part),"portfolio_active_duration_hours":active/3600,"sum_individual_trade_duration_hours":individual/3600,"time_weighted_mean_open_positions":integrated/active,"max_open_positions":max(dist),"entries_with_any_open_before":sum(x["open_positions_before_entry"]>0 for x in ctx),"share_entries_with_any_open_before":sum(x["open_positions_before_entry"]>0 for x in ctx)/len(ctx),"entries_with_same_instrument_open_before":sum(x["same_instrument_open_before"]>0 for x in ctx),"share_entries_with_same_instrument_open_before":sum(x["same_instrument_open_before"]>0 for x in ctx)/len(ctx),"entries_with_same_instrument_same_direction_open_before":sum(x["same_instrument_same_direction_open_before"]>0 for x in ctx),"entries_with_same_instrument_opposite_direction_open_before":sum(x["same_instrument_opposite_direction_open_before"]>0 for x in ctx),"max_nominal_initial_R_units":max(dist)})
      recon.append({"generation":key[0],"lifecycle":key[1],"trades":len(part),"unique_trade_ids":len({x['canonical_trade_key'] for x in part}),"entry_parse_failures":0,"exit_parse_failures":0,"timezone_violations":0,"invalid_intervals":0,"corrected_C1_mismatches":0,"individual_duration_seconds":individual,"integrated_open_position_seconds":integrated,"duration_identity_delta":integrated-individual,"entry_events":len(part),"exit_events":len(part),"final_open_positions":0,"status":"PASS" if integrated==individual else "FAIL"})
    entry_report=[]
    for key,part in sorted(groups(contexts,["generation","lifecycle","open_positions_before_entry"]).items()):
      vals=[float(x["net_R"]) for x in part];wins=[x for x in vals if x>0];loss=[x for x in vals if x<0]
      entry_report.append({"generation":key[0],"lifecycle":key[1],"open_positions_before_entry":key[2],"trades":len(part),"trade_share":len(part)/EXPECTED[key[:2]],"net_R":math.fsum(vals),"expectancy_R":math.fsum(vals)/len(vals),"PF":math.fsum(wins)/-math.fsum(loss) if loss else "INF","win_rate":len(wins)/len(vals),"small_sample_flag":len(vals)<30})
    bridge=[]
    by_stream=groups(rows,["generation","lifecycle","strategy","timeframe","instrument"])
    for c in corr:
      base=(c["generation"],c["lifecycle"],c["strategy"],c["timeframe"]);m=pair_metrics(by_stream[base+(c["instrument_a"],)],by_stream[base+(c["instrument_b"],)])
      bridge.append({k:c[k] for k in ("generation","lifecycle","strategy","timeframe","instrument_a","instrument_b","overlapping_months","stage2_historical_pearson_monthly_R","corrected_pearson_monthly_R","pearson_delta")}|m|{"sample_flag":c["sample_flag"]})
    portfolio=[]
    for key,part in sorted(groups(rows,["generation","lifecycle"]).items()):
      by=groups(part,["instrument"])
      for a,b in combinations(sorted(x[0] for x in by),2):portfolio.append({"generation":key[0],"lifecycle":key[1],"instrument_a":a,"instrument_b":b}|pair_metrics(by[(a,)],by[(b,)]))
    cross=[]
    for key,part in sorted(groups(rows,["generation","lifecycle","instrument"]).items()):
      by=groups(part,["strategy","timeframe"]);streams=sorted(by)
      for a,b in combinations(streams,2):cross.append({"generation":key[0],"lifecycle":key[1],"instrument":key[2],"stream_a":"|".join(a),"stream_b":"|".join(b)}|pair_metrics(by[a],by[b]))
    wf=[r for r in rows if r["lifecycle"]=="walk_forward"];wf_summary=[];wf_overlap=[]
    for key,part in sorted(groups(wf,["generation","fold_id"]).items()):
      ctx,di=sweep(part);active=sum(v[1] for v in di.values());individual=sum((r["exit"]-r["entry"]).total_seconds() for r in part);integrated=sum(k*v[1] for k,v in di.items())
      wf_summary.append({"generation":key[0],"fold_id":key[1],"trades":len(part),"portfolio_active_duration_hours":active/3600,"sum_individual_trade_duration_hours":individual/3600,"time_weighted_mean_open_positions":integrated/active,"max_open_positions":max(di),"entries_with_any_open_before":sum(x["open_positions_before_entry"]>0 for x in ctx),"share_entries_with_any_open_before":sum(x["open_positions_before_entry"]>0 for x in ctx)/len(ctx),"entries_with_same_instrument_open_before":sum(x["same_instrument_open_before"]>0 for x in ctx)})
      by=groups(part,["instrument"])
      for a,b in combinations(sorted(x[0] for x in by),2):
        m=pair_metrics(by[(a,)],by[(b,)]);wf_overlap.append({"generation":key[0],"fold_id":key[1],"instrument_a":a,"instrument_b":b,**{k:m[k] for k in ("shared_active_duration_hours","overlap_share_A","overlap_share_B","overlap_jaccard","overlapping_trade_pairs","both_final_negative_pairs","opposite_final_sign_pairs")}})
    reports={"corrected_monthly_instrument_matrix.csv":matrix,"corrected_pairwise_monthly_correlation.csv":corr,"correlation_overlap_bridge.csv":bridge,"portfolio_instrument_overlap_report.csv":portfolio,"same_instrument_cross_stream_overlap_report.csv":cross,"entry_concurrency_context.csv":contexts,"entry_concurrency_report.csv":entry_report,"concurrency_distribution_report.csv":dist_rows,"concurrency_summary_report.csv":summaries,"wf_concurrency_report.csv":wf_summary,"wf_instrument_overlap_report.csv":wf_overlap,"correlation_risk_reconciliation.csv":recon}
    for n,v in reports.items():write_csv(output/n,v)
    return {"rows":len(rows),"monthly_rows":len(matrix),"pair_rows":len(corr),"bridge_rows":len(bridge),"wf_rows":len(wf),"wf_portfolios":len(wf_summary)}
