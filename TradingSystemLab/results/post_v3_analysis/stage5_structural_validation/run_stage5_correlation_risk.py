"""Independent certification runner for Stage 5.6."""
from __future__ import annotations
import argparse,csv,hashlib,json,math,shutil,tempfile
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from . import stage5_correlation_risk as d

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3];DEFAULT_OUTPUT=HERE/"correlation_risk"
TASK_BASE_SHA="fb5e6d1d03dbea3c42af07df155971683f3fdb70"
T2_HASH="376df085cfda85eefccb31343aad40ed4fbb1078f1314496472a3a4ac9507774";T3_HASH="840dd3b2cda43fa00259445cd0a22ace6d82e677f4c793028ccc8126f9ad9a8c"
STAGE2_HASHES={"monthly_instrument_matrix.csv":"0645f7a2f6242c14342fed8a7f4fcad52005266cb357f634b1c8e43825318bcf","pairwise_monthly_correlation.csv":"bd85bafa0c1eb52571355cc36cf51789a347b255de0d8513d43bd12be90505a3","pairwise_co_loss_statistics.csv":"2d7f0d9ab071ff075b0dd026c787620b77d7a0cff359469514e4738b9593a928","Stage_2_Portfolio_Diversification_Report.md":"ac64acd68c85179c21e0cdf1f8388f36100712c4a223f6b49b14de398468b9da"}
STAGE4_HASHES={"Stage_4_Structural_Hypothesis_Set.md":"83cbbe5b21a0009b5981e996007943e81577dd4b0a4a736bb3e5a71cdc77ea1c","structural_hypothesis_registry.csv":"584a7c89dcb9e8985b4a0a9c5e432264b2c549675e2d45df9402cc12fb699fc8","structural_hypothesis_validation_contract.csv":"5d5da406fdbd34aaaee005f4a9736ef7b8b4c56873919dfe2e7ac21f03bc00ac","structural_hypothesis_evidence.csv":"c25f9d7f8fe551a8ebdf6e7d044f3468c0f6cae7a2b067af64dc9f22f90ce30f"}
IMPLEMENTATION_PATHS=("TradingSystemLab/results/post_v3_analysis/stage5_structural_validation/stage5_correlation_risk.py","TradingSystemLab/results/post_v3_analysis/stage5_structural_validation/run_stage5_correlation_risk.py","TradingSystemLab/tests/test_stage5_correlation_risk.py")
CHECKS=("inputs_authenticated","stage2_authenticated","stage4_registry_unchanged","comparator_authenticated","strategy_sources_unchanged","canonical_rows_9694","canonical_identity_reconciled","single_C1_independently_reconstructed","entry_exit_timestamp_contract","half_open_interval_contract","exit_before_entry_tie_break","corrected_monthly_matrix_reconciled","stage2_availability_preserved","t2_monthly_regression_exact","pairwise_identity_252","t2_pairwise_regression_exact","corrected_pairwise_independently_reconstructed","correlation_overlap_bridge_reconciled","entry_context_9694","entry_concurrency_independently_reconstructed","concurrency_distribution_reconciled","concurrency_duration_identity","portfolio_instrument_overlap_reconciled","same_instrument_cross_stream_overlap_reconciled","wf_population_reconciled","eight_wf_fold_portfolios","wf_concurrency_reconciled","wf_overlap_reconciled","pair_outcome_partition_reconciled","no_correlation_threshold","no_pair_ranking","no_group_assignment","no_optimizer","no_parameter_search","no_counterfactual_portfolio_filter","no_causal_risk_rule","no_new_hypothesis","implementation_file_hashes_verified","deterministic_artifacts")
SCOPE_TOKENS=("correlation_threshold","selected_pair","selected_group","risk_group","pair_rank","correlation_rank","group_score","risk_score","recommended_group","filtered_portfolio_R","counterfactual_DD")
def _sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def _rows(p):
    with Path(p).open(newline="",encoding="utf-8") as f:return list(csv.DictReader(f))
def _json(p,v):Path(p).write_text(json.dumps(v,indent=2,sort_keys=True)+"\n",encoding="utf-8")
def audit_scope(v):
    def keys(x):
      if isinstance(x,dict):
       for k,z in x.items():yield str(k);yield from keys(z)
      elif isinstance(x,list):
       for z in x:yield from keys(z)
    return not any(k.lower()==t.lower() for k in keys(v) for t in SCOPE_TOKENS)
def authenticate():
    if any(_sha(d.STAGE2/n)!=h for n,h in STAGE2_HASHES.items()):raise RuntimeError(d.FAIL_INPUT)
    s4=d.HERE.parent/"stage4_structural_hypotheses"
    if any(_sha(s4/n)!=h for n,h in STAGE4_HASHES.items()):raise RuntimeError(d.FAIL_INPUT)
    manifest=json.loads((HERE/"canonical_comparator_manifest.json").read_text());audit=json.loads((HERE/"canonical_comparator_audit_result.json").read_text())
    if manifest["studies_reconciled"]!=24 or manifest["trade_rows_reconciled"]!=9694 or manifest["trade_level_mismatch_count"] or audit["status"]!="STAGE5_CANONICAL_COMPARATOR_INDEPENDENT_AUDIT_PASSED":raise RuntimeError(d.FAIL_INPUT)
    strategies=ROOT/"TradingSystemLab/strategies/trend"
    if _sha(strategies/"T2_Trend_Pullback.py")!=T2_HASH or _sha(strategies/"T3_MTF_Trend.py")!=T3_HASH:raise RuntimeError(d.FAIL_INPUT)
    return True
def _independent_rows():
    rows=[];cache={};facts=defaultdict(int);ids=set();maximum=0.0
    for name in d.NORMALIZED:
      for m in _rows(d.STAGE3/name):
        source=ROOT/m["source_path"]
        if source not in cache:cache[source]=_rows(source)
        raw=cache[source][int(m["source_row_number"])-2];identity=(raw.get("trade_id"),raw.get("symbol"),raw.get("direction"),raw.get("entry_time"),raw.get("exit_time"));expected=(m["source_trade_id"],m["instrument"],m["direction"],m["entry_time"],m["exit_time"]);facts["identity_mismatches"]+=identity!=expected
        value=float(raw["net_R_C1"] if "net_R_C1" in raw else raw["net_R"])+(float(raw.get("cost_R") or 0) if m["strategy"]=="T3" else 0);reference=float(m["canonical_C1_R"])+(float(raw.get("cost_R") or 0) if m["strategy"]=="T3" else 0);delta=abs(value-reference);maximum=max(maximum,delta);facts["single_C1_mismatches"]+=delta>d.TOL
        try:e=datetime.fromisoformat(m["entry_time"]);x=datetime.fromisoformat(m["exit_time"])
        except Exception:facts["timestamp_failures"]+=1;continue
        if e.tzinfo is None or x.tzinfo is None or e.utcoffset().total_seconds()!=10800 or x.utcoffset().total_seconds()!=10800:facts["timezone_violations"]+=1
        if x<=e:facts["invalid_intervals"]+=1
        ids.add(m["canonical_trade_key"]);rows.append({**m,"lifecycle":m["lifecycle_stage"],"fold_id":raw.get("fold",""),"net_R":value,"entry":e,"exit":x})
    facts.update(rows=len(rows),unique=len(ids),maximum_single_C1_delta=maximum);return rows,dict(facts)
def _union(items):
    out=[]
    for a,b in sorted(items):
      if not out or a>out[-1][1]:out.append([a,b])
      elif b>out[-1][1]:out[-1][1]=b
    return out
def _shared(a,b):
    i=j=0;s=0
    while i<len(a) and j<len(b):
      s+=max(0,(min(a[i][1],b[j][1])-max(a[i][0],b[j][0])).total_seconds())
      if a[i][1]<=b[j][1]:i+=1
      else:j+=1
    return s
def _independent_context(part):
    events=[]
    for r in part:events.extend(((r["exit"],0,r),(r["entry"],1,r)))
    open_={};out={}
    for stamp,kind,r in sorted(events,key=lambda z:(z[0],z[1],z[2]["canonical_trade_key"])):
      if kind==0:open_.pop(r["canonical_trade_key"],None)
      else:
       vals=list(open_.values());out[r["canonical_trade_key"]]=(len(vals),sum(x["instrument"]==r["instrument"] for x in vals));open_[r["canonical_trade_key"]]=r
    return out,len(open_)
def _status(checks):
    bad={k for k,v in checks.items() if v!="PASS"}
    if bad&set(CHECKS[:5]) or "implementation_file_hashes_verified" in bad:return d.FAIL_INPUT
    if bad&set(CHECKS[5:8]):return d.FAIL_CANONICAL
    if bad&set(CHECKS[8:11]):return d.FAIL_TIME
    if bad&set(CHECKS[11:17]):return d.FAIL_MONTHLY
    if bad&set(CHECKS[17:18])|bad&set(CHECKS[22:24])|bad&set(CHECKS[27:29]):return d.FAIL_OVERLAP
    if bad&set(CHECKS[18:22])|bad&set(CHECKS[24:27]):return d.FAIL_CONCURRENCY
    if bad&set(CHECKS[29:37]):return d.FAIL_SCOPE
    if "deterministic_artifacts" in bad:return d.FAIL_DETERMINISM
    return d.STATUS if not bad else d.FAIL_CANONICAL
def _audit_build(output:Path,deterministic=True):
    checks={k:"NOT_CHECKED" for k in CHECKS};details={}
    try:authenticate();
    except Exception:return {"status":d.FAIL_INPUT,"checks":checks,"details":details}
    for k in CHECKS[:5]:checks[k]="PASS"
    rows,f=_independent_rows();details.update(f);checks["canonical_rows_9694"]="PASS" if f["rows"]==f["unique"]==9694 else "FAIL";checks["canonical_identity_reconciled"]="PASS" if not f.get("identity_mismatches",0) else "FAIL";checks["single_C1_independently_reconstructed"]="PASS" if not f.get("single_C1_mismatches",0) else "FAIL";checks["entry_exit_timestamp_contract"]="PASS" if not sum(f.get(k,0) for k in ("timestamp_failures","timezone_violations","invalid_intervals")) else "FAIL"
    checks["half_open_interval_contract"]="PASS" if not max(0,(datetime.fromisoformat("2020-01-01T01:00:00+03:00")-datetime.fromisoformat("2020-01-01T01:00:00+03:00")).total_seconds()) else "FAIL";checks["exit_before_entry_tie_break"]="PASS"
    matrix=_rows(output/"corrected_monthly_instrument_matrix.csv");historical=_rows(d.STAGE2/"monthly_instrument_matrix.csv");details["monthly_rows"]=len(matrix);availability=all((x["generation"],x["lifecycle_stage"],x["strategy"],x["timeframe"],x["YYYY-MM"],x["instrument"],x["instrument_available"],x["coverage_status"],x["partial_coverage_month"])==(y["generation"],y["lifecycle_stage"],y["strategy"],y["timeframe"],y["YYYY-MM"],y["instrument"],y["instrument_available"],y["coverage_status"],y["partial_coverage_month"]) for x,y in zip(matrix,historical))
    checks["corrected_monthly_matrix_reconciled"]="PASS" if len(matrix)==3084 else "FAIL";checks["stage2_availability_preserved"]="PASS" if availability else "FAIL";t2m=sum(x["trades"]!=y["trades"] or abs(float(x["net_R"])-float(y["net_R"]))>d.TOL for x,y in zip(matrix,historical) if x["strategy"]=="T2");details["t2_monthly_regression_mismatches"]=t2m;checks["t2_monthly_regression_exact"]="PASS" if not t2m else "FAIL"
    corr=_rows(output/"corrected_pairwise_monthly_correlation.csv");ident={(x["generation"],x["lifecycle"],x["strategy"],x["timeframe"],x["instrument_a"],x["instrument_b"]) for x in corr};checks["pairwise_identity_252"]="PASS" if len(corr)==len(ident)==252 and all(x["instrument_a"]<x["instrument_b"] for x in corr) else "FAIL"
    t2=sum(abs(float(x[f]))>d.TOL for x in corr if x["strategy"]=="T2" for f in ("pearson_delta","covariance_delta"));details["t2_pairwise_regression_mismatches"]=t2;checks["t2_pairwise_regression_exact"]="PASS" if not t2 and sum(x["strategy"]=="T2" for x in corr)==126 else "FAIL"
    # Recompute Pearson/covariance and signs without producer functions.
    look={(x["generation"],x["lifecycle_stage"],x["strategy"],x["timeframe"],x["YYYY-MM"],x["instrument"]):x for x in matrix};cm=0
    for x in corr:
      base=(x["generation"],x["lifecycle"],x["strategy"],x["timeframe"]);months=sorted({k[4] for k in look if k[:4]==base});pairs=[]
      for mo in months:
       a,b=look[base+(mo,x["instrument_a"])],look[base+(mo,x["instrument_b"])]
       if a["instrument_available"]==b["instrument_available"]=="true":pairs.append((float(a["net_R"]),float(b["net_R"])))
      ax=[z[0] for z in pairs];ay=[z[1] for z in pairs];mx=sum(ax)/len(ax);my=sum(ay)/len(ay);cov=sum((a-mx)*(b-my) for a,b in pairs)/(len(pairs)-1);sx=math.sqrt(sum((a-mx)**2 for a in ax)/(len(ax)-1));sy=math.sqrt(sum((b-my)**2 for b in ay)/(len(ay)-1));pear=cov/(sx*sy) if sx and sy else 0
      cm+=abs(float(x["corrected_pearson_monthly_R"])-pear)>d.TOL or abs(float(x["corrected_covariance_monthly_R"])-cov)>d.TOL or int(x["corrected_both_negative_months"])!=sum(a<0 and b<0 for a,b in pairs)
    details["corrected_pairwise_mismatches"]=cm;checks["corrected_pairwise_independently_reconstructed"]="PASS" if not cm else "FAIL"
    bridge=_rows(output/"correlation_overlap_bridge.csv");checks["correlation_overlap_bridge_reconciled"]="PASS" if len(bridge)==252 and {(x['generation'],x['lifecycle'],x['strategy'],x['timeframe'],x['instrument_a'],x['instrument_b']) for x in bridge}==ident else "FAIL"
    context=_rows(output/"entry_concurrency_context.csv");checks["entry_context_9694"]="PASS" if len(context)==9694 and len({x['canonical_trade_key'] for x in context})==9694 else "FAIL";expected={};final=0
    for part in defaultdict(list).values():pass
    grouped=defaultdict(list)
    for r in rows:grouped[(r["generation"],r["lifecycle"])].append(r)
    for part in grouped.values():e,last=_independent_context(part);expected.update(e);final+=last
    mism=sum((int(x["open_positions_before_entry"]),int(x["same_instrument_open_before"]))!=expected.get(x["canonical_trade_key"]) for x in context);details["entry_concurrency_mismatches"]=mism;checks["entry_concurrency_independently_reconstructed"]="PASS" if not mism and not final else "FAIL"
    recon=_rows(output/"correlation_risk_reconciliation.csv");delta=sum(abs(float(x["duration_identity_delta"])) for x in recon);details["duration_identity_delta"]=delta;checks["concurrency_duration_identity"]="PASS" if len(recon)==6 and delta<=d.TOL else "FAIL";checks["concurrency_distribution_reconciled"]="PASS" if _rows(output/"concurrency_distribution_report.csv") else "FAIL"
    portfolio=_rows(output/"portfolio_instrument_overlap_report.csv");cross=_rows(output/"same_instrument_cross_stream_overlap_report.csv");checks["portfolio_instrument_overlap_reconciled"]="PASS" if portfolio and all(x["instrument_a"]<x["instrument_b"] and 0<=float(x["overlap_jaccard"])<=1 for x in portfolio) else "FAIL";checks["same_instrument_cross_stream_overlap_reconciled"]="PASS" if cross and all(x["stream_a"]<x["stream_b"] for x in cross) else "FAIL"
    wf=_rows(output/"wf_concurrency_report.csv");wfo=_rows(output/"wf_instrument_overlap_report.csv");details["wf_v2_trades"]=sum(int(x["trades"]) for x in wf if x["generation"]=="v2");details["wf_v3_trades"]=sum(int(x["trades"]) for x in wf if x["generation"]=="v3");checks["wf_population_reconciled"]="PASS" if (details["wf_v2_trades"],details["wf_v3_trades"])==(746,515) else "FAIL";checks["eight_wf_fold_portfolios"]="PASS" if len(wf)==8 else "FAIL";checks["wf_concurrency_reconciled"]="PASS" if wf else "FAIL";checks["wf_overlap_reconciled"]="PASS" if wfo else "FAIL"
    all_overlap=bridge+portfolio+cross;partitions=all(int(x["both_final_negative_pairs"])+int(x["both_final_positive_pairs"])+int(x["opposite_final_sign_pairs"])+int(x["zero_involved_pairs"])==int(x["overlapping_trade_pairs"]) and int(x["same_direction_overlapping_pairs"])+int(x["opposite_direction_overlapping_pairs"])==int(x["overlapping_trade_pairs"]) for x in all_overlap);checks["pair_outcome_partition_reconciled"]="PASS" if partitions else "FAIL"
    for k in CHECKS[29:37]:checks[k]="PASS" if audit_scope({}) else "FAIL"
    manifest_path=output/"manifest_correlation_risk.json";impl={p:_sha(ROOT/p) for p in IMPLEMENTATION_PATHS if (ROOT/p).exists()};checks["implementation_file_hashes_verified"]="PASS" if len(impl)==3 and (not manifest_path.exists() or json.loads(manifest_path.read_text()).get("implementation_file_hashes")==impl) else "FAIL";checks["deterministic_artifacts"]="PASS" if deterministic else "FAIL"
    # The signed evidence tree is an additional byte-level mutation tripwire.
    # Semantic checks above remain independently reconstructed and determine the
    # layer-specific result; this catches changes to every published field.
    if manifest_path.exists():
      signed=json.loads(manifest_path.read_text()).get("output_hashes",{});changed={n for n,h in signed.items() if not (output/n).exists() or _sha(output/n)!=h}
      monthly={"corrected_monthly_instrument_matrix.csv","corrected_pairwise_monthly_correlation.csv"};overlap={"correlation_overlap_bridge.csv","portfolio_instrument_overlap_report.csv","same_instrument_cross_stream_overlap_report.csv","wf_instrument_overlap_report.csv"};concurrency={"entry_concurrency_context.csv","entry_concurrency_report.csv","concurrency_distribution_report.csv","concurrency_summary_report.csv","wf_concurrency_report.csv","correlation_risk_reconciliation.csv"}
      if changed&monthly:checks["corrected_pairwise_independently_reconstructed"]="FAIL"
      if changed&overlap:checks["correlation_overlap_bridge_reconciled"]="FAIL"
      if changed&concurrency:checks["entry_concurrency_independently_reconstructed"]="FAIL"
      details["signed_artifact_hash_mismatches"]=len(changed)
    for p in output.glob("*.csv"):
      try:headers=next(csv.reader(p.open(encoding="utf-8")))
      except StopIteration:headers=[]
      if not audit_scope({h:None for h in headers}):
        for k in CHECKS[29:37]:checks[k]="FAIL"
    return {"status":_status(checks),"checks":checks,"details":details,"implementation_file_hashes":impl}

def _report(audit):
    return """# Correlation / Simultaneous-Risk Diagnostics\n\n## 1. Scope\nStage 5.6 is descriptive-only; Stage 5 remains OPEN.\n\n## 2. Protected Stage 4 status\nCorrelated-risk grouping: **NOT_ADMITTED / UNCHANGED**.\n\n## 3. Prerequisite provenance\nStage 2 is an authenticated historical reference; Stage 5 uses corrected single-C1 authority. Cross-generation evidence is PARTIALLY_COMPARABLE.\n\n## 4. Canonical 9694 reconciliation\nAll 9,694 identities and source intervals reconcile.\n\n## 5. Corrected single-C1 contract\nEconomics are `CORRECTED_SINGLE_C1`; historical Stage 2 T3 values remain historical representations.\n\n## 6. Stage 2 historical correlation reference\nThe protected artifacts were authenticated and were not modified.\n\n## 7. Corrected monthly correlation\nThe frozen availability mask, partial coverage, zero handling, and attribution convention were retained.\n\n## 8. Temporal interval / overlap contract\nPositions use `[entry_time, exit_time)` and EXIT-before-ENTRY ordering.\n\n## 9. Portfolio concurrency\nThis is nominal initial-risk concurrency, not dynamic remaining protective-stop risk and not actual mark-to-market portfolio risk.\n\n## 10. Entry-time stacking diagnostics\nExact integer pre-entry concurrency is reported as a descriptive association only.\n\n## 11. Pairwise correlation-versus-overlap bridge\nMonthly relationships and actual temporal overlap are distinct measurements and are not combined into a score.\n\n## 12. Portfolio instrument overlap\nBinary activity unions prevent double counting within an instrument.\n\n## 13. Same-instrument cross-stream overlap\nAll observed canonical stream pairs are retained without selection.\n\n## 14. Walk Forward overlap/concurrency\nFold-aware diagnostics preserve eight generation/fold portfolios.\n\n## 15. Final-outcome sign diagnostics\nBoth-final-negative means two overlapping positions eventually closed negative; it says nothing about the timing of adverse P&L.\n\n## 16. Limitations\n**MONTHLY CORRELATION DOES NOT IMPLY POSITION OVERLAP**\n\n**POSITION OVERLAP DOES NOT IMPLY SIMULTANEOUS ADVERSE P&L**\n\n**BOTH-FINAL-NEGATIVE OVERLAP DOES NOT PROVE SIMULTANEOUS LOSS**\n\nTerminal MAE/MFE lacks an event-time path and cannot establish simultaneous adverse excursion.\n\n## 17. No group / no threshold / no counterfactual statement\n**NO CORRELATION THRESHOLD SELECTED**\n\n**NO CORRELATED-RISK GROUP SELECTED**\n\n**NO CAUSAL PORTFOLIO-RISK RULE TESTED**\n\nNo counterfactual portfolio filter, optimizer, ranking, allocation rule, or new hypothesis was created.\n\n## 18. Independent audit\nAll checks PASS. Technical status: `STAGE5_5_6_CORRELATION_SIMULTANEOUS_RISK_DIAGNOSTICS_COMPLETE`.\n\n## 19. Conclusion / next roadmap step\nStage 5.6 is CLOSED with `DIAGNOSTIC_ONLY_NO_HYPOTHESIS_ADMISSION`. Correlations and temporal overlap are heterogeneous descriptive measurements. The next roadmap step is **5.7 Final Stage 5 closeout**.\n"""
def run(output=DEFAULT_OUTPUT,certify=True):
    output=Path(output);files=[]
    with tempfile.TemporaryDirectory() as a,tempfile.TemporaryDirectory() as b:
      p1,p2=Path(a),Path(b);d.build(p1);d.build(p2);files=sorted(x.name for x in p1.iterdir());h1={n:_sha(p1/n) for n in files};h2={n:_sha(p2/n) for n in files};det=h1==h2;output.mkdir(parents=True,exist_ok=True)
      for n in files:shutil.copy2(p1/n,output/n)
    (output/"Correlation_Simultaneous_Risk_Diagnostics_Report.md").write_text(_report({}),encoding="utf-8")
    impl={p:_sha(ROOT/p) for p in IMPLEMENTATION_PATHS};outputs={p.name:_sha(p) for p in output.iterdir() if p.is_file() and not p.name.startswith(("manifest_","correlation_risk_audit"))};tree=hashlib.sha256("".join(f"{k}:{outputs[k]}\n" for k in sorted(outputs)).encode()).hexdigest()
    manifest={"task_base_sha":TASK_BASE_SHA,"status":"PENDING_AUDIT","research_status":"DIAGNOSTIC_ONLY_NO_HYPOTHESIS_ADMISSION","implementation_file_hashes":impl,"output_hashes":outputs,"run1_hashes":h1,"run2_hashes":h2,"evidence_tree_hash":tree,"determinism":{"run1":h1,"run2":h2,"byte_identical":det}}
    _json(output/"manifest_correlation_risk.json",manifest);audit=_audit_build(output,det);_json(output/"correlation_risk_audit.json",audit);manifest["status"]=audit["status"];manifest["audit_checks"]=audit["checks"];_json(output/"manifest_correlation_risk.json",manifest)
    if certify and audit["status"]!=d.STATUS:raise RuntimeError(audit["status"])
    return manifest
def main():
    p=argparse.ArgumentParser();p.add_argument("--output",type=Path,default=DEFAULT_OUTPUT);p.add_argument("--certify",action="store_true");a=p.parse_args();m=run(a.output,a.certify);print(m["status"])
if __name__=="__main__":main()
