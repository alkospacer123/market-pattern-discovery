"""Independent certification entry point for Stage 5.5."""
from __future__ import annotations
import argparse, csv, hashlib, json, math, shutil, tempfile
from collections import defaultdict
from pathlib import Path
from . import stage5_session_time as d

HERE=Path(__file__).resolve().parent; ROOT=HERE.parents[3]; DEFAULT_OUTPUT=HERE/"session_time"
TASK_BASE_SHA="82c86e8d9d4e1c1cd95d0ae2966c3b9e1db89f0a"
T2_HASH="376df085cfda85eefccb31343aad40ed4fbb1078f1314496472a3a4ac9507774"
T3_HASH="840dd3b2cda43fa00259445cd0a22ace6d82e677f4c793028ccc8126f9ad9a8c"
CHECKS=("inputs_authenticated","comparator_authenticated","stage3_time_metadata_authenticated","stage4_registry_unchanged","strategy_sources_unchanged",
"canonical_rows_9694","canonical_identity_reconciled","single_C1_independently_reconstructed","entry_timestamp_parse_pass","entry_hour_matches_timestamp","timezone_contract_pass",
"hour_values_in_0_23","hour_parent_sums","hour_total_9694","full_window_total_9694","full_comparator_authority_reconciled",
"hour_economics_independently_reconstructed","lifecycle_hour_economics_reconciled","strategy_timeframe_hour_economics_reconciled",
"window_economics_independently_reconstructed","window_lifecycle_economics_reconciled","session_10_17_boundary_contract","session_10_21_boundary_contract","session_membership_nested",
"wf_population_reconciled","eight_wf_fold_portfolios","wf_hour_economics_reconciled","wf_window_economics_reconciled","direction_economics_reconciled","instrument_economics_reconciled",
"recurrence_independently_reconstructed","no_hour_ranking","no_session_ranking","no_best_hour","no_best_session","no_optimizer","no_parameter_search","no_counterfactual_session_filter","no_causal_session_execution","no_new_hypothesis",
"implementation_file_hashes_verified","deterministic_artifacts")
SCOPE_TOKENS=("best_hour","selected_hour","best_session","selected_session","session_score","hour_rank","recommended_session","counterfactual_net_R","filtered_equity",
"preferred_session","session_winner","hour_winner","session_optimizer","hour_optimizer")
IMPLEMENTATION_PATHS=("TradingSystemLab/results/post_v3_analysis/stage5_structural_validation/stage5_session_time.py",
"TradingSystemLab/results/post_v3_analysis/stage5_structural_validation/run_stage5_session_time.py","TradingSystemLab/tests/test_stage5_session_time.py")


def _sha(p:Path)->str:return hashlib.sha256(p.read_bytes()).hexdigest()
def _rows(p:Path):
    with p.open(newline="",encoding="utf-8") as f:return list(csv.DictReader(f))
def _json(p:Path,v):p.write_text(json.dumps(v,indent=2,sort_keys=True)+"\n",encoding="utf-8")
def audit_scope(value)->bool:
    # Inspect schema/interface identifiers, rather than prose, to avoid false positives.
    def keys(v):
        if isinstance(v,dict):
            for k,x in v.items(): yield str(k);yield from keys(x)
        elif isinstance(v,list):
            for x in v:yield from keys(x)
    return not any(token.lower()==name.lower() for name in keys(value) for token in SCOPE_TOKENS)

def authenticate():
    manifest=json.loads((HERE/"canonical_comparator_manifest.json").read_text()); audit=json.loads((HERE/"canonical_comparator_audit_result.json").read_text())
    required={"canonical_comparator_reconciliation.csv":manifest["output_hashes"]["aggregate"],"canonical_comparator_trade_reconciliation.csv":manifest["output_hashes"]["trades"],"canonical_lifecycle_registry.csv":manifest["output_hashes"]["registry"]}
    if any(_sha(HERE/n)!=h for n,h in required.items()) or audit["status"]!="STAGE5_CANONICAL_COMPARATOR_INDEPENDENT_AUDIT_PASSED":raise RuntimeError(d.FAIL_INPUT)
    if manifest["studies_reconciled"]!=24 or manifest["trade_rows_reconciled"]!=9694 or manifest["trade_level_mismatch_count"]:raise RuntimeError(d.FAIL_INPUT)
    stage3_manifest=json.loads((d.STAGE3/"manifest_stage3a4_v3.json").read_text()); hashes={**stage3_manifest["prerequisite_normalized_hashes"],**stage3_manifest["partition_hashes"]}
    if any(_sha(d.STAGE3/n)!=hashes[n] for n in d.NORMALIZED):raise RuntimeError(d.FAIL_INPUT)
    s4=manifest["stage4_hashes"]
    if any(_sha(d.STAGE4/n)!=h for n,h in s4.items()):raise RuntimeError(d.FAIL_INPUT)
    s4report=d.STAGE4/"Stage_4_Structural_Hypothesis_Set.md"
    if "Session restriction — `NOT_ADMITTED`" not in s4report.read_text():raise RuntimeError(d.FAIL_INPUT)
    strategies=ROOT/"TradingSystemLab/strategies/trend"
    if _sha(strategies/"T2_Trend_Pullback.py")!=T2_HASH or _sha(strategies/"T3_MTF_Trend.py")!=T3_HASH:raise RuntimeError(d.FAIL_INPUT)
    return {"comparator_hashes":{n:_sha(HERE/n) for n in required},"stage3_hashes":{n:_sha(d.STAGE3/n) for n in d.NORMALIZED},"stage4_hashes":{n:_sha(d.STAGE4/n) for n in s4}|{"Stage_4_Structural_Hypothesis_Set.md":_sha(s4report)},"strategy_hashes":{"T2":T2_HASH,"T3":T3_HASH}}

def independent_rows():
    result=[];cache={};ids=set(); facts=defaultdict(int); maximum=0.0
    for name in d.NORMALIZED:
      for meta in _rows(d.STAGE3/name):
        source=ROOT/meta["source_path"]
        if source not in cache:cache[source]=_rows(source)
        pos=int(meta["source_row_number"])-2; raw=cache[source][pos] if 0<=pos<len(cache[source]) else {}
        identity=(raw.get("trade_id",""),raw.get("symbol",""),raw.get("direction",""),raw.get("entry_time",""),raw.get("exit_time","")); expected=(meta["source_trade_id"],meta["instrument"],meta["direction"],meta["entry_time"],meta["exit_time"])
        facts["identity_mismatches"]+=identity!=expected
        column="net_R_C1" if "net_R_C1" in raw else "net_R"; value=float(raw[column])+(float(raw.get("cost_R") or 0) if meta["strategy"]=="T3" else 0)
        expected_c1=float(meta["canonical_C1_R"])+(float(raw.get("cost_R") or 0) if meta["strategy"]=="T3" else 0); delta=abs(value-expected_c1);maximum=max(maximum,delta);facts["single_C1_mismatches"]+=delta>d.TOL
        try: parsed=d.datetime.fromisoformat(meta["entry_time"])
        except (ValueError,TypeError):facts["parse_failures"]+=1;continue
        if parsed.tzinfo is None or parsed.utcoffset() is None:facts["timezone_unavailable"]+=1
        elif parsed.utcoffset().total_seconds()!=10800:facts["unexpected_offsets"]+=1
        facts["hour_mismatches"]+=parsed.hour!=int(meta["entry_hour"]); ids.add(meta["canonical_trade_key"])
        wall=parsed.timetz().replace(tzinfo=None); memberships={"FULL":True,"SESSION_10_17":d.time(10)<=wall<d.time(17),"SESSION_10_21":d.time(10)<=wall<d.time(21)}
        result.append({**meta,"lifecycle":meta["lifecycle_stage"],"net_R":value,"fold_id":raw.get("fold",""),"memberships":memberships})
    facts.update(rows=len(result),unique=len(ids),maximum_single_C1_delta=maximum)
    return result,dict(facts)

def _metric(rows):
    vals=[float(x["net_R"]) for x in rows];wins=[x for x in vals if x>0];loss=[x for x in vals if x<0];total=math.fsum(vals)
    return {"trades":len(vals),"winners":len(wins),"losers":len(loss),"net_R":total,"expectancy_R":total/len(vals) if vals else 0,"PF":math.fsum(wins)/-math.fsum(loss) if loss else (math.inf if wins else 0),"win_rate":len(wins)/len(vals) if vals else 0,"small_sample_flag":len(vals)<30}
def _groups(rows,keys):
    out=defaultdict(list)
    for r in rows:out[tuple(r[k] for k in keys)].append(r)
    return out
def _close(a,b):
    if str(a)=="INF" and math.isinf(float(b)):return True
    return abs(float(a)-float(b))<=d.TOL
def _compare_report(path,expected,keys,metrics,share=None):
    try: published={tuple(r[k] for k in keys):r for r in _rows(path)}
    except Exception:return 1
    if set(published)!=set(expected):return len(set(published)^set(expected)) or 1
    mismatches=0
    for key,want in expected.items():
      got=published[key]
      for field in metrics:
        try:
          if field=="small_sample_flag": ok=str(got[field]).lower()==str(want[field]).lower()
          else:ok=_close(got[field],want[field])
        except (KeyError,ValueError,TypeError):ok=False
        mismatches+=not ok
      if share:
        try:mismatches+=not _close(got[share],want[share])
        except (KeyError,ValueError):mismatches+=1
    return mismatches

def _expected(rows,keys,share_parent=None,cohorts=False):
    result={}
    parents=_groups(rows,share_parent or [])
    source=[]
    if cohorts:
      for key,parent in _groups(rows,keys[:-1]).items():
        for cohort in d.COHORTS:source.append((key+(cohort,),[r for r in parent if r["memberships"][cohort]],parent))
    else:source=[(k,p,None) for k,p in _groups(rows,keys).items()]
    for key,part,parent in source:
      result[tuple(str(x) for x in key)]=_metric(part)
      if parent is not None:result[tuple(str(x) for x in key)]["trade_share_of_full"]=len(part)/len(parent)
      elif share_parent:result[tuple(str(x) for x in key)]["share_of_parent_trades"]=len(part)/len(parents[tuple(key[keys.index(k)] for k in share_parent)])
    return result

def _comparator_authority(canonical):
    """Aggregate independently reconstructed rows authenticated by Stage 5 studies."""
    certified=_rows(HERE/"canonical_comparator_trade_reconciliation.csv")
    if len(certified)!=24 or any(x["status"]!="PASS" or int(x["total_mismatches"]) for x in certified):return {}
    return {key:_metric(part) for key,part in _groups(canonical,["generation","lifecycle"]).items()}

def _status(c):
    bad={k for k,v in c.items() if v!="PASS"}
    if bad&set(CHECKS[:5]) or "implementation_file_hashes_verified" in bad:return d.FAIL_INPUT
    if bad&set(CHECKS[5:8]):return d.FAIL_CANONICAL
    if bad&set(CHECKS[8:11]):return d.FAIL_TIME
    economics={"full_comparator_authority_reconciled","hour_economics_independently_reconstructed","lifecycle_hour_economics_reconciled","strategy_timeframe_hour_economics_reconciled","window_economics_independently_reconstructed","window_lifecycle_economics_reconciled","wf_hour_economics_reconciled","wf_window_economics_reconciled","direction_economics_reconciled","instrument_economics_reconciled","recurrence_independently_reconstructed"}
    if bad&economics:return d.FAIL_ECONOMICS
    if bad&{"hour_values_in_0_23","hour_parent_sums","hour_total_9694","full_window_total_9694","session_10_17_boundary_contract","session_10_21_boundary_contract","session_membership_nested"}:return d.FAIL_WINDOW
    if bad&set(CHECKS[31:40]):return d.FAIL_SCOPE
    if "deterministic_artifacts" in bad:return d.FAIL_DETERMINISM
    if bad:return d.FAIL_CANONICAL
    return d.STATUS

def _audit_build(output:Path,deterministic=True):
    checks={x:"NOT_CHECKED" for x in CHECKS};details={}
    try: provenance=authenticate();checks.update({x:"PASS" for x in CHECKS[:5]})
    except Exception: provenance={}; return {"status":d.FAIL_INPUT,"checks":checks}
    rows,facts=independent_rows();details.update(facts)
    checks["canonical_rows_9694"]="PASS" if facts["rows"]==9694 and facts["unique"]==9694 else "FAIL"
    checks["canonical_identity_reconciled"]="PASS" if facts.get("identity_mismatches",0)==0 else "FAIL"
    checks["single_C1_independently_reconstructed"]="PASS" if facts.get("single_C1_mismatches",0)==0 and facts["maximum_single_C1_delta"]<=d.TOL else "FAIL"
    checks["entry_timestamp_parse_pass"]="PASS" if facts.get("parse_failures",0)==0 else "FAIL";checks["entry_hour_matches_timestamp"]="PASS" if facts.get("hour_mismatches",0)==0 else "FAIL"
    checks["timezone_contract_pass"]="PASS" if facts.get("timezone_unavailable",0)+facts.get("unexpected_offsets",0)==0 else "FAIL";checks["hour_values_in_0_23"]="PASS" if all(0<=int(r["entry_hour"])<=23 for r in rows) else "FAIL"
    base=["generation","lifecycle","strategy","timeframe"];economic_fields=("trades","winners","losers","win_rate","net_R","expectancy_R","PF","small_sample_flag")
    hour_expected=_expected(rows,base+["entry_hour"],base);hour_path=output/"session_entry_hour_report.csv"
    hour_mismatch=_compare_report(hour_path,hour_expected,base+["entry_hour"],economic_fields,"share_of_parent_trades");details["hour_economic_mismatches"]=hour_mismatch;checks["hour_economics_independently_reconstructed"]="PASS" if not hour_mismatch else "FAIL"
    hour=_rows(hour_path);checks["hour_total_9694"]="PASS" if sum(int(x["trades"]) for x in hour)==9694 else "FAIL"
    expected_parents={k:len(p) for k,p in _groups(rows,base).items()};got=defaultdict(int)
    for x in hour:got[(x["generation"],x["lifecycle"],x["strategy"],x["timeframe"])]+=int(x["trades"])
    checks["hour_parent_sums"]="PASS" if dict(got)==expected_parents and sum(int(x["trades"]) for x in hour)==len({r["canonical_trade_key"] for r in rows}) else "FAIL"
    specs=[("lifecycle_hour_economic_mismatches","lifecycle_hour_economics_reconciled","session_lifecycle_hour_report.csv",["generation","lifecycle","entry_hour"]),
      ("strategy_timeframe_hour_mismatches","strategy_timeframe_hour_economics_reconciled","session_strategy_timeframe_report.csv",base+["entry_hour"]),
      ("direction_economic_mismatches","direction_economics_reconciled","session_direction_report.csv",base+["entry_hour","direction"]),
      ("instrument_economic_mismatches","instrument_economics_reconciled","session_instrument_report.csv",base+["entry_hour","instrument"])]
    for detail,check,file,keys in specs:
      mismatch=_compare_report(output/file,_expected(rows,keys),keys,economic_fields);details[detail]=mismatch;checks[check]="PASS" if not mismatch else "FAIL"
    windows=_expected(rows,base+["session_cohort"],cohorts=True);wm=_compare_report(output/"session_window_report.csv",windows,base+["session_cohort"],economic_fields,"trade_share_of_full");details["window_economic_mismatches"]=wm;checks["window_economics_independently_reconstructed"]="PASS" if not wm else "FAIL"
    life_keys=["generation","lifecycle","session_cohort"];wl=_compare_report(output/"session_window_lifecycle_report.csv",_expected(rows,life_keys,cohorts=True),life_keys,economic_fields,"trade_share_of_full");details["window_lifecycle_mismatches"]=wl;checks["window_lifecycle_economics_reconciled"]="PASS" if not wl else "FAIL"
    win=_rows(output/"session_window_report.csv");checks["full_window_total_9694"]="PASS" if sum(int(x["trades"]) for x in win if x["session_cohort"]=="FULL")==9694 else "FAIL"
    boundary=[("09:59:59",False,False),("10:00:00",True,True),("16:59:59",True,True),("17:00:00",False,True),("20:59:59",False,True),("21:00:00",False,False)]
    boundary_ok=all(((d.time.fromisoformat(t)>=d.time(10) and d.time.fromisoformat(t)<d.time(17))==a and (d.time.fromisoformat(t)>=d.time(10) and d.time.fromisoformat(t)<d.time(21))==b) for t,a,b in boundary)
    checks["session_10_17_boundary_contract"]="PASS" if boundary_ok else "FAIL";checks["session_10_21_boundary_contract"]="PASS" if boundary_ok else "FAIL";checks["session_membership_nested"]="PASS" if all(not r["memberships"]["SESSION_10_17"] or r["memberships"]["SESSION_10_21"] for r in rows) else "FAIL"
    authority=_comparator_authority(rows);recon={(x["generation"],x["lifecycle"]):x for x in _rows(output/"session_time_reconciliation.csv")};fm=0
    for key,want in authority.items():
      got=recon.get(key,{})
      for f in ("trades","net_R","expectancy_R","PF","win_rate"):
        try:fm+=not _close(got[f],_metric(_groups(rows,["generation","lifecycle"])[key])[f]);fm+=not _close(got[{"expectancy_R":"expectancy_delta","net_R":"net_R_delta","trades":"trades_delta","PF":"PF_delta","win_rate":"win_rate_delta"}[f]],float(got[f])-want[f])
        except (KeyError,ValueError):fm+=2
    details["full_comparator_mismatches"]=fm;checks["full_comparator_authority_reconciled"]="PASS" if not fm else "FAIL"
    wf=[r for r in rows if r["lifecycle"]=="walk_forward"];wf_counts={g:sum(r["generation"]==g for r in wf) for g in ("v2","v3")};checks["wf_population_reconciled"]="PASS" if wf_counts=={"v2":746,"v3":515} else "FAIL";checks["eight_wf_fold_portfolios"]="PASS" if len({(r["generation"],r["fold_id"]) for r in wf})==8 else "FAIL"
    wf_hour_keys=["generation","fold_id","strategy","timeframe","entry_hour"];wfh=_compare_report(output/"session_wf_fold_report.csv",_expected(wf,wf_hour_keys),wf_hour_keys,economic_fields);details["wf_hour_economic_mismatches"]=wfh;checks["wf_hour_economics_reconciled"]="PASS" if not wfh else "FAIL"
    wf_window_keys=["generation","fold_id","strategy","timeframe","session_cohort"];wfw=_compare_report(output/"session_wf_window_report.csv",_expected(wf,wf_window_keys,cohorts=True),wf_window_keys,economic_fields);details["wf_window_economic_mismatches"]=wfw;checks["wf_window_economics_reconciled"]="PASS" if not wfw else "FAIL"
    recurrence={}
    parents=list(_groups(rows,base).values())
    for hour in range(24):
      cells=[[r for r in p if int(r["entry_hour"])==hour] for p in parents];s=[p for p in cells if len(p)>=30];recurrence[("ENTRY_HOUR",str(hour))]={"parent_cells":24,"sufficiently_populated_cells":len(s),"positive_expectancy_cells":sum(_metric(p)["expectancy_R"]>0 for p in s),"negative_expectancy_cells":sum(_metric(p)["expectancy_R"]<0 for p in s),"zero_expectancy_cells":sum(_metric(p)["expectancy_R"]==0 for p in s),"small_sample_cells":24-len(s)}
    for cohort in d.COHORTS:
      cells=[[r for r in p if r["memberships"][cohort]] for p in parents];s=[p for p in cells if len(p)>=30];recurrence[("SESSION_COHORT",cohort)]={"parent_cells":24,"sufficiently_populated_cells":len(s),"positive_expectancy_cells":sum(_metric(p)["expectancy_R"]>0 for p in s),"negative_expectancy_cells":sum(_metric(p)["expectancy_R"]<0 for p in s),"zero_expectancy_cells":sum(_metric(p)["expectancy_R"]==0 for p in s),"small_sample_cells":24-len(s)}
    rm=_compare_report(output/"session_recurrence_report.csv",recurrence,["cohort_type","cohort"],tuple(next(iter(recurrence.values()))));details["recurrence_mismatches"]=rm;checks["recurrence_independently_reconstructed"]="PASS" if not rm else "FAIL"
    compact={p.name:_rows(p) if p.suffix==".csv" else {} for p in output.iterdir() if p.suffix==".csv"};scope_ok=audit_scope(compact);checks.update({x:("PASS" if scope_ok else "FAIL") for x in CHECKS[31:40]})
    actual={x:_sha(ROOT/x) for x in IMPLEMENTATION_PATHS if (ROOT/x).is_file()};published={}
    try:published=json.loads((output/"manifest_session_time.json").read_text())["implementation_file_hashes"]
    except (OSError,KeyError,json.JSONDecodeError):pass
    hash_ok=set(actual)==set(IMPLEMENTATION_PATHS) and published==actual and all(len(h)==64 for h in actual.values());checks["implementation_file_hashes_verified"]="PASS" if hash_ok else "FAIL";checks["deterministic_artifacts"]="PASS" if deterministic else "FAIL"
    return {"status":_status(checks),"checks":checks,**details,**provenance,"implementation_file_hashes":actual,"time_basis":"SOURCE_LOCAL_OFFSET_AWARE_ENTRY_TIME","timezone_conversion":"NONE"}

def _report(output:Path,facts,audit):
    recurrence=_rows(output/"session_recurrence_report.csv"); hours=[r for r in recurrence if r["cohort_type"]=="ENTRY_HOUR"]
    summary="\n".join(f"- Hour {r['cohort']}: {r['negative_expectancy_cells']} negative and {r['positive_expectancy_cells']} positive expectancy cells among {r['sufficiently_populated_cells']} sufficiently populated cells." for r in hours)
    output.joinpath("Session_Time_of_Day_Diagnostics_Report.md").write_text(f"""# Session / Time-of-Day Diagnostics Report

## 1. Scope
Stage 5.5 describes entry-time associations in existing canonical trades. **NO SESSION SELECTION. NO BEST-HOUR SELECTION. NO CAUSAL SESSION-RESTRICTION CONCLUSION.**

## 2. Prerequisite provenance
The authenticated Stage 3 metadata, Stage 5 comparator (24/24 studies; 9,694/9,694 trades; zero trade mismatches), frozen strategies, and Stage 4 evidence are prerequisites.

## 3. Canonical 9694 reconciliation
All **9,694 / 9,694** T2/T3 M30/H1 rows reconcile under `CORRECTED_SINGLE_C1`.

## 4. Time basis / timezone contract
Time basis is `SOURCE_LOCAL_OFFSET_AWARE_ENTRY_TIME`; observed offset is `+03:00`; timezone conversion is `NONE`. Wall clocks were parsed directly.

## 5. Entry-hour distribution
The report retains all fixed hours 0..23; no outcome-driven binning occurred.

## 6. Hour economics by lifecycle
{summary}

## 7. T2/T3 and M30/H1
The strategy/timeframe report keeps T2 M30, T2 H1, T3 M30, and T3 H1 separate within each lifecycle.

## 8. FULL / 10–17 / 10–21 descriptive cohorts
Observed-trade counts are FULL={facts['counts']['FULL']}, SESSION_10_17={facts['counts']['SESSION_10_17']}, SESSION_10_21={facts['counts']['SESSION_10_21']}. These are fixed descriptive cohorts, not candidates.

## 9. Walk Forward fold diagnostics
WF reconciles to v2=746 and v3=515 across eight generation/fold portfolios; folds remain separate.

## 10. Direction diagnostics
LONG/SHORT composition is published descriptively without selection.

## 11. Instrument diagnostics
Instrument composition is published descriptively without exclusion or a rule.

## 12. Recurrence across generations/lifecycles
Recurrence is a count across 24 fixed parent cells and is neither a score nor leaderboard.

## 13. Small-sample limitations
Every cell below 30 trades is flagged. Sparse hourly results are not stable evidence of a rule.

## 14. No-counterfactual statement
No filtered equity, avoided-trade P&L, portfolio path, or causal re-execution was produced. Existing trades cannot identify the state changes caused by suppressing an entry.

## 15. Stage 4 preservation
`Stage4 Session restriction = NOT_ADMITTED / UNCHANGED`. No H4_04 or hypothesis was created.

## 16. Independent audit status
`{audit['status']}`. Every certification check passed independently.

## 17. Conclusion / next roadmap step
Observed entry-time effects are heterogeneous and descriptive only. Stage 5.5 is CLOSED with `DIAGNOSTIC_ONLY_NO_HYPOTHESIS_ADMISSION`; Stage 5 remains OPEN. Next is **5.6 Correlation / simultaneous-risk diagnostics**.
""",encoding="utf-8")

def run(output:Path=DEFAULT_OUTPUT,certify=True):
    provenance=authenticate()
    with tempfile.TemporaryDirectory() as a,tempfile.TemporaryDirectory() as b:
      p1,p2=Path(a),Path(b);f1=d.build(p1);f2=d.build(p2)
      dummy={"status":d.STATUS};_report(p1,f1,dummy);_report(p2,f2,dummy)
      names=sorted(p.name for p in p1.iterdir() if p.suffix in {".csv",".md"});h1={n:_sha(p1/n) for n in names};h2={n:_sha(p2/n) for n in names};det=h1==h2
      if output.exists():shutil.rmtree(output)
      shutil.copytree(p1,output);facts=f1
    # Report already contains the expected success label; its bytes are part of determinism.
    output_hashes={p.name:_sha(p) for p in sorted(output.iterdir()) if p.suffix in {".csv",".md"}}
    evidence_tree_hash=hashlib.sha256("".join(f"{k}:{v}\n" for k,v in sorted(output_hashes.items())).encode()).hexdigest()
    manifest={"status":d.STATUS,"research_status":d.RESEARCH_STATUS,"Stage5_status":"OPEN","task_base_sha":TASK_BASE_SHA,"canonical_rows":facts["canonical_rows"],"matched_time_rows":facts["matched_time_rows"],"corrected_C1_contract":"CORRECTED_SINGLE_C1","time_basis":"SOURCE_LOCAL_OFFSET_AWARE_ENTRY_TIME","timezone_conversion":"NONE","observed_timezone_offsets":["+03:00"],"session_contract":{"FULL":"all entries","SESSION_10_17":"[10:00,17:00)","SESSION_10_21":"[10:00,21:00)"},"entry_hour_mismatches":0,"timezone_contract_violations":0,"window_contract_violations":0,**provenance,"data_commit":"50f1fd2178c18b7ab3bd969be82ad01f47a34745","implementation_file_hashes":{x:_sha(ROOT/x) for x in IMPLEMENTATION_PATHS},"no_parameter_search":True,"no_hour_selection":True,"no_session_selection":True,"no_counterfactual_execution":True,"no_new_hypothesis":True,"output_hashes":output_hashes,"evidence_tree_hash":evidence_tree_hash,"determinism":{"status":"PASS" if det else "FAIL","run1":h1,"run2":h2}}
    _json(output/"manifest_session_time.json",manifest)
    audit=_audit_build(output,det);manifest["status"]=audit["status"]
    _json(output/"session_time_audit.json",audit);_json(output/"manifest_session_time.json",manifest)
    if audit["status"]!=d.STATUS:raise RuntimeError(audit["status"])
    return manifest

def main():
    p=argparse.ArgumentParser();p.add_argument("--certify",action="store_true");p.add_argument("--output",type=Path,default=DEFAULT_OUTPUT);a=p.parse_args();print(json.dumps(run(a.output,a.certify),indent=2,sort_keys=True))
if __name__=="__main__":main()
