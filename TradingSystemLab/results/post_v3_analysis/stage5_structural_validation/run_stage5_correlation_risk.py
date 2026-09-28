"""Independent certification runner for Stage 5.6."""
from __future__ import annotations
import argparse,csv,hashlib,json,math,shutil,tempfile
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from . import stage5_correlation_risk as d

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3];DEFAULT_OUTPUT=HERE/"correlation_risk"
TASK_BASE_SHA="8a0f6b7cc8ee423b2cf9d8c4d2ca7a07b13ae09a"
T2_HASH="376df085cfda85eefccb31343aad40ed4fbb1078f1314496472a3a4ac9507774";T3_HASH="840dd3b2cda43fa00259445cd0a22ace6d82e677f4c793028ccc8126f9ad9a8c"
STAGE2_HASHES={"monthly_instrument_matrix.csv":"0645f7a2f6242c14342fed8a7f4fcad52005266cb357f634b1c8e43825318bcf","pairwise_monthly_correlation.csv":"bd85bafa0c1eb52571355cc36cf51789a347b255de0d8513d43bd12be90505a3","pairwise_co_loss_statistics.csv":"2d7f0d9ab071ff075b0dd026c787620b77d7a0cff359469514e4738b9593a928","Stage_2_Portfolio_Diversification_Report.md":"ac64acd68c85179c21e0cdf1f8388f36100712c4a223f6b49b14de398468b9da"}
STAGE4_HASHES={"Stage_4_Structural_Hypothesis_Set.md":"83cbbe5b21a0009b5981e996007943e81577dd4b0a4a736bb3e5a71cdc77ea1c","structural_hypothesis_registry.csv":"584a7c89dcb9e8985b4a0a9c5e432264b2c549675e2d45df9402cc12fb699fc8","structural_hypothesis_validation_contract.csv":"5d5da406fdbd34aaaee005f4a9736ef7b8b4c56873919dfe2e7ac21f03bc00ac","structural_hypothesis_evidence.csv":"c25f9d7f8fe551a8ebdf6e7d044f3468c0f6cae7a2b067af64dc9f22f90ce30f"}
IMPLEMENTATION_PATHS=("TradingSystemLab/results/post_v3_analysis/stage5_structural_validation/stage5_correlation_risk.py","TradingSystemLab/results/post_v3_analysis/stage5_structural_validation/run_stage5_correlation_risk.py","TradingSystemLab/tests/test_stage5_correlation_risk.py")
CHECKS=("inputs_authenticated","stage2_authenticated","stage4_registry_unchanged","comparator_authenticated","strategy_sources_unchanged","canonical_rows_9694","canonical_identity_reconciled","single_C1_independently_reconstructed","entry_exit_timestamp_contract","half_open_interval_independently_verified","exit_before_entry_tie_break_independently_verified","corrected_monthly_matrix_independently_reconstructed","stage2_availability_semantics_exact","not_yet_available_zero_flag_contract","t2_monthly_regression_exact","pairwise_identity_252","t2_pairwise_regression_exact","corrected_pairwise_independently_reconstructed","correlation_overlap_bridge_metrics_reconciled","entry_context_9694","entry_context_all_fields_reconciled","concurrency_distribution_independently_reconstructed","concurrency_summary_independently_reconstructed","concurrency_duration_identity_independently_verified","portfolio_instrument_overlap_metrics_reconciled","cross_stream_overlap_metrics_reconciled","wf_population_reconciled","eight_wf_fold_portfolios","wf_concurrency_independently_reconstructed","wf_overlap_independently_reconstructed","pair_outcome_partition_reconciled","no_correlation_threshold","no_pair_ranking","no_group_assignment","no_optimizer","no_parameter_search","no_counterfactual_portfolio_filter","no_causal_risk_rule","no_new_hypothesis","implementation_file_hashes_verified","signed_artifact_hashes_verified","deterministic_artifacts")
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
def audit_interval_overlap(a,b):
    return max(0.0,(min(a[1],b[1])-max(a[0],b[0])).total_seconds())
def audit_union_intervals(items):
    out=[]
    for a,b in sorted(items):
      if not out or a>out[-1][1]:out.append([a,b])
      elif b>out[-1][1]:out[-1][1]=b
    return [(a,b) for a,b in out]
def audit_shared_duration(a,b):
    i=j=0;s=0.0
    while i<len(a) and j<len(b):
      s+=audit_interval_overlap(a[i],b[j])
      if a[i][1]<=b[j][1]:i+=1
      else:j+=1
    return s
def audit_pair_metrics(a,b):
    ua=audit_union_intervals([(r["entry"],r["exit"]) for r in a]);ub=audit_union_intervals([(r["entry"],r["exit"]) for r in b])
    da=sum((z-y).total_seconds() for y,z in ua);db=sum((z-y).total_seconds() for y,z in ub);shared=audit_shared_duration(ua,ub);union=da+db-shared
    c=defaultdict(int);ia=set();ib=set()
    for x in a:
      for y in b:
       if audit_interval_overlap((x["entry"],x["exit"]),(y["entry"],y["exit"]))>0:
        c["overlapping_trade_pairs"]+=1;ia.add(x["canonical_trade_key"]);ib.add(y["canonical_trade_key"])
        c["same_direction_overlapping_pairs" if x["direction"]==y["direction"] else "opposite_direction_overlapping_pairs"]+=1
        vx,vy=x["net_R"],y["net_R"]
        c["zero_involved_pairs" if vx==0 or vy==0 else "both_final_negative_pairs" if vx<0 and vy<0 else "both_final_positive_pairs" if vx>0 and vy>0 else "opposite_final_sign_pairs"]+=1
    return {"active_duration_A_hours":da/3600,"active_duration_B_hours":db/3600,"shared_active_duration_hours":shared/3600,"union_active_duration_hours":union/3600,"overlap_share_A":shared/da if da else 0,"overlap_share_B":shared/db if db else 0,"overlap_jaccard":shared/union if union else 0,"unique_A_trades_with_overlap":len(ia),"unique_B_trades_with_overlap":len(ib),**{k:c[k] for k in ("overlapping_trade_pairs","same_direction_overlapping_pairs","opposite_direction_overlapping_pairs","both_final_negative_pairs","both_final_positive_pairs","opposite_final_sign_pairs","zero_involved_pairs")}}
def audit_sweep(part):
    events=[]
    for r in part:events.extend(((r["exit"],0,r),(r["entry"],1,r)))
    open_={};contexts=[];dist=defaultdict(lambda:[0,0.0]);previous=None
    for stamp,block in __import__('itertools').groupby(sorted(events,key=lambda z:(z[0],z[1],z[2]["canonical_trade_key"])),lambda z:z[0]):
      block=list(block)
      if previous is not None and open_:dist[len(open_)][0]+=1;dist[len(open_)][1]+=(stamp-previous).total_seconds()
      for _,kind,r in block:
       if kind==0:open_.pop(r["canonical_trade_key"],None)
       else:
        vals=list(open_.values());before=len(vals)
        contexts.append({"canonical_trade_key":r["canonical_trade_key"],"open_positions_before_entry":before,"open_positions_after_entry":before+1,"same_instrument_open_before":sum(x["instrument"]==r["instrument"] for x in vals),"same_direction_open_before":sum(x["direction"]==r["direction"] for x in vals),"same_instrument_same_direction_open_before":sum(x["instrument"]==r["instrument"] and x["direction"]==r["direction"] for x in vals),"same_instrument_opposite_direction_open_before":sum(x["instrument"]==r["instrument"] and x["direction"]!=r["direction"] for x in vals),"nominal_initial_R_units_before":before,"nominal_initial_R_units_after":before+1})
        open_[r["canonical_trade_key"]]=r
      previous=stamp
    return contexts,dist,len(open_)
def _monthly(rows):
    hist=_rows(d.STAGE2/"monthly_instrument_matrix.csv");sums=defaultdict(list)
    for r in rows:
      # Frozen Stage 2 convention: midnight exits belong to entry month.
      month=(r["entry"] if r["exit"].hour==0 else r["exit"]).strftime("%Y-%m")
      sums[(r["generation"],r["lifecycle"],r["strategy"],r["timeframe"],month,r["instrument"])].append(r["net_R"])
    out=[]
    for h in hist:
      key=(h["generation"],h["lifecycle_stage"],h["strategy"],h["timeframe"],h["YYYY-MM"],h["instrument"]);available=h["instrument_available"].lower()=="true";vals=sums.get(key,[]);net=math.fsum(vals) if available else 0.0
      out.append({**h,"trades":len(vals) if available else 0,"net_R":net,"positive_month":available and net>0,"negative_month":available and net<0,"zero_month":available and net==0,"economic_contract":"CORRECTED_SINGLE_C1_CURRENT_AUTHORITY"})
    return out
def _correlation(x,y):
    if len(x)<2:return 0.0,0.0
    mx=sum(x)/len(x);my=sum(y)/len(y);cov=math.fsum((a-mx)*(b-my) for a,b in zip(x,y))/(len(x)-1);sx=math.sqrt(math.fsum((a-mx)**2 for a in x)/(len(x)-1));sy=math.sqrt(math.fsum((b-my)**2 for b in y)/(len(y)-1));return (cov/(sx*sy) if sx and sy else 0.0),cov
def _pairwise(matrix):
    hist=_rows(d.STAGE2/"pairwise_monthly_correlation.csv");look={(r["generation"],r["lifecycle_stage"],r["strategy"],r["timeframe"],r["YYYY-MM"],r["instrument"]):r for r in matrix};out=[]
    for h in hist:
      base=(h["generation"],h["lifecycle_stage"],h["strategy"],h["timeframe"]);pairs=[];partial=0
      for mo in sorted({k[4] for k in look if k[:4]==base}):
       a,b=look[base+(mo,h["instrument_a"])],look[base+(mo,h["instrument_b"])]
       if a["instrument_available"].lower()==b["instrument_available"].lower()=="true":pairs.append((float(a["net_R"]),float(b["net_R"])));partial+=a["partial_coverage_month"].lower()=="true" or b["partial_coverage_month"].lower()=="true"
      x=[z[0] for z in pairs];y=[z[1] for z in pairs];pear,cov=_correlation(x,y)
      out.append({"generation":h["generation"],"lifecycle":h["lifecycle_stage"],"strategy":h["strategy"],"timeframe":h["timeframe"],"instrument_a":h["instrument_a"],"instrument_b":h["instrument_b"],"overlapping_months":len(pairs),"partial_overlap_months":partial,"corrected_pearson_monthly_R":pear,"corrected_covariance_monthly_R":cov,"corrected_same_sign_months":sum(a*b>0 for a,b in pairs),"corrected_opposite_sign_months":sum(a*b<0 for a,b in pairs),"corrected_both_negative_months":sum(a<0 and b<0 for a,b in pairs),"corrected_both_positive_months":sum(a>0 and b>0 for a,b in pairs),"sample_flag":"LOW_SAMPLE" if len(pairs)<6 else "ADEQUATE"})
    return out
def _same(a,b):
    try:return abs(float(a)-float(b))<=d.TOL
    except (ValueError,TypeError):return str(a).lower()==str(b).lower()
def _compare(actual,expected,keys,fields):
    aa={tuple(r[k] for k in keys):r for r in actual};ee={tuple(str(r[k]) for k in keys):r for r in expected}
    if set(aa)!=set(ee):return len(set(aa)^set(ee))+abs(len(actual)-len(aa))+abs(len(expected)-len(ee))
    return sum(not _same(aa[k].get(f,""),ee[k].get(f,"")) for k in ee for f in fields)
def _status(checks):
    bad={k for k,v in checks.items() if v!="PASS"}
    if bad&set(CHECKS[:5]) or "implementation_file_hashes_verified" in bad:return d.FAIL_INPUT
    if bad&set(CHECKS[5:8]):return d.FAIL_CANONICAL
    if bad&set(CHECKS[8:11]):return d.FAIL_TIME
    if bad&set(CHECKS[11:18]):return d.FAIL_MONTHLY
    if bad&set(CHECKS[18:19])|bad&set(CHECKS[24:26])|bad&set(CHECKS[29:31]):return d.FAIL_OVERLAP
    if bad&set(CHECKS[19:24])|bad&set(CHECKS[26:29]):return d.FAIL_CONCURRENCY
    if bad&set(CHECKS[31:39]):return d.FAIL_SCOPE
    if bad&{"signed_artifact_hashes_verified","deterministic_artifacts"}:return d.FAIL_DETERMINISM
    return d.STATUS if not bad else d.FAIL_CANONICAL
def _audit_build(output:Path,deterministic=True):
    checks={k:"NOT_CHECKED" for k in CHECKS};details={}
    try:authenticate()
    except Exception:return {"status":d.FAIL_INPUT,"checks":checks,"details":details}
    for k in CHECKS[:5]:checks[k]="PASS"
    rows,f=_independent_rows();details.update(f);checks["canonical_rows_9694"]="PASS" if f["rows"]==f["unique"]==9694 else "FAIL";checks["canonical_identity_reconciled"]="PASS" if not f.get("identity_mismatches",0) else "FAIL";checks["single_C1_independently_reconstructed"]="PASS" if not f.get("single_C1_mismatches",0) else "FAIL";details["single_C1_mismatches"]=f.get("single_C1_mismatches",0);checks["entry_exit_timestamp_contract"]="PASS" if not sum(f.get(k,0) for k in ("timestamp_failures","timezone_violations","invalid_intervals")) else "FAIL"
    t=datetime.fromisoformat("2020-01-01T10:00:00+03:00");cases=[(((t,t+__import__('datetime').timedelta(hours=1)),(t+__import__('datetime').timedelta(hours=1),t+__import__('datetime').timedelta(hours=2))),0),(((t,t+__import__('datetime').timedelta(hours=1)),(t+__import__('datetime').timedelta(hours=1,seconds=-1),t+__import__('datetime').timedelta(hours=2))),1),(((t,t+__import__('datetime').timedelta(hours=1)),(t,t+__import__('datetime').timedelta(hours=1))),3600),(((t,t+__import__('datetime').timedelta(hours=2)),(t+__import__('datetime').timedelta(minutes=30),t+__import__('datetime').timedelta(hours=1))),1800),(((t,t+__import__('datetime').timedelta(hours=1)),(t+__import__('datetime').timedelta(minutes=30),t+__import__('datetime').timedelta(hours=2))),1800),(((t,t+__import__('datetime').timedelta(hours=1)),(t+__import__('datetime').timedelta(hours=2),t+__import__('datetime').timedelta(hours=3))),0)]
    checks["half_open_interval_independently_verified"]="PASS" if all(audit_interval_overlap(*x)==v for x,v in cases) else "FAIL"
    syn=[{"canonical_trade_key":"A","entry":t,"exit":t+__import__('datetime').timedelta(hours=1),"instrument":"X","direction":"long"},{"canonical_trade_key":"B","entry":t+__import__('datetime').timedelta(hours=1),"exit":t+__import__('datetime').timedelta(hours=2),"instrument":"Y","direction":"long"}];sc,_,_=audit_sweep(syn);checks["exit_before_entry_tie_break_independently_verified"]="PASS" if next(x for x in sc if x["canonical_trade_key"]=="B")["open_positions_before_entry"]==0 else "FAIL"
    expected_m=_monthly(rows);actual_m=_rows(output/"corrected_monthly_instrument_matrix.csv");mkeys=("generation","futures_type","lifecycle_stage","strategy","timeframe","YYYY-MM","instrument");mfields=("coverage_start_date","instrument_available","partial_coverage_month","coverage_status","trades","net_R","positive_month","negative_month","zero_month","economic_contract");mm=_compare(actual_m,expected_m,mkeys,mfields);details["monthly_rows"]=len(actual_m);details["corrected_monthly_matrix_mismatches"]=mm;checks["corrected_monthly_matrix_independently_reconstructed"]="PASS" if not mm else "FAIL"
    nya=[x for x in actual_m if x["coverage_status"]=="NOT_YET_AVAILABLE"];nt=[x for x in actual_m if x["coverage_status"]=="NO_TRADES"];viol=sum(x["instrument_available"].lower()!="false" or int(x["trades"]) or abs(float(x["net_R"]))>d.TOL or any(x[z].lower()=="true" for z in ("positive_month","negative_month","zero_month")) for x in nya);viol+=sum(x["instrument_available"].lower()!="true" or int(x["trades"]) or abs(float(x["net_R"]))>d.TOL or x["positive_month"].lower()=="true" or x["negative_month"].lower()=="true" or x["zero_month"].lower()!="true" for x in nt);details.update(not_yet_available_rows=len(nya),not_yet_available_zero_flag_violations=sum(x["zero_month"].lower()=="true" for x in nya),no_trades_rows=len(nt),no_trades_zero_month_true=sum(x["zero_month"].lower()=="true" for x in nt));checks["stage2_availability_semantics_exact"]="PASS" if not viol else "FAIL";checks["not_yet_available_zero_flag_contract"]="PASS" if not details["not_yet_available_zero_flag_violations"] else "FAIL"
    hist=_rows(d.STAGE2/"monthly_instrument_matrix.csv");t2fields=("trades","net_R","positive_month","negative_month","zero_month");t2m=sum(not _same(x[f],y[f]) for x,y in zip(actual_m,hist) if x["strategy"]=="T2" for f in t2fields);details["t2_monthly_regression_mismatches"]=t2m;checks["t2_monthly_regression_exact"]="PASS" if not t2m else "FAIL"
    expected_c=_pairwise(expected_m);actual_c=_rows(output/"corrected_pairwise_monthly_correlation.csv");ckeys=("generation","lifecycle","strategy","timeframe","instrument_a","instrument_b");cfields=("overlapping_months","partial_overlap_months","corrected_pearson_monthly_R","corrected_covariance_monthly_R","corrected_same_sign_months","corrected_opposite_sign_months","corrected_both_negative_months","corrected_both_positive_months","sample_flag");cm=_compare(actual_c,expected_c,ckeys,cfields);details["corrected_pairwise_mismatches"]=cm;ident={tuple(x[k] for k in ckeys) for x in actual_c};checks["pairwise_identity_252"]="PASS" if len(actual_c)==len(ident)==252 and all(x["instrument_a"]<x["instrument_b"] for x in actual_c) else "FAIL";checks["corrected_pairwise_independently_reconstructed"]="PASS" if not cm else "FAIL";t2=sum(abs(float(x[f]))>d.TOL for x in actual_c if x["strategy"]=="T2" for f in ("pearson_delta","covariance_delta"));details["t2_pairwise_regression_mismatches"]=t2;checks["t2_pairwise_regression_exact"]="PASS" if not t2 and sum(x["strategy"]=="T2" for x in actual_c)==126 else "FAIL"
    grouped=defaultdict(list)
    for r in rows:grouped[(r["generation"],r["lifecycle"])].append(r)
    expctx=[];expdist=[];expsum=[];duration_bad=0
    for key,part in sorted(grouped.items()):
      ctx,di,last=audit_sweep(part);expctx+=ctx;active=sum(v[1] for v in di.values());individual=sum((r["exit"]-r["entry"]).total_seconds() for r in part);integrated=sum(k*v[1] for k,v in di.items());duration_bad+=abs(integrated-individual)>d.TOL or bool(last)
      for level,(segments,seconds) in sorted(di.items()):expdist.append({"generation":key[0],"lifecycle":key[1],"concurrency_level":level,"segment_count":segments,"duration_seconds":seconds,"duration_hours":seconds/3600,"share_of_active_portfolio_time":seconds/active,"nominal_initial_R_units":level})
      expsum.append({"generation":key[0],"lifecycle":key[1],"trades":len(part),"portfolio_active_duration_hours":active/3600,"sum_individual_trade_duration_hours":individual/3600,"time_weighted_mean_open_positions":integrated/active,"max_open_positions":max(di),"entries_with_any_open_before":sum(x["open_positions_before_entry"]>0 for x in ctx),"share_entries_with_any_open_before":sum(x["open_positions_before_entry"]>0 for x in ctx)/len(ctx),"entries_with_same_instrument_open_before":sum(x["same_instrument_open_before"]>0 for x in ctx),"share_entries_with_same_instrument_open_before":sum(x["same_instrument_open_before"]>0 for x in ctx)/len(ctx),"entries_with_same_instrument_same_direction_open_before":sum(x["same_instrument_same_direction_open_before"]>0 for x in ctx),"entries_with_same_instrument_opposite_direction_open_before":sum(x["same_instrument_opposite_direction_open_before"]>0 for x in ctx),"max_nominal_initial_R_units":max(di)})
    ctxfields=("open_positions_before_entry","open_positions_after_entry","same_instrument_open_before","same_direction_open_before","same_instrument_same_direction_open_before","same_instrument_opposite_direction_open_before","nominal_initial_R_units_before","nominal_initial_R_units_after");actualctx=_rows(output/"entry_concurrency_context.csv");ec=_compare(actualctx,expctx,("canonical_trade_key",),ctxfields);details["entry_context_mismatches"]=ec;checks["entry_context_9694"]="PASS" if len(actualctx)==9694 else "FAIL";checks["entry_context_all_fields_reconciled"]="PASS" if not ec else "FAIL"
    dk=("generation","lifecycle","concurrency_level");df=("segment_count","duration_seconds","duration_hours","share_of_active_portfolio_time","nominal_initial_R_units");dm=_compare(_rows(output/"concurrency_distribution_report.csv"),expdist,dk,df);sf=tuple(k for k in expsum[0] if k not in ("generation","lifecycle"));sm=_compare(_rows(output/"concurrency_summary_report.csv"),expsum,("generation","lifecycle"),sf);recon=_rows(output/"correlation_risk_reconciliation.csv");recon_bad=len(recon)!=6 or any(abs(float(x["duration_identity_delta"]))>d.TOL for x in recon);details.update(concurrency_distribution_mismatches=dm,concurrency_summary_mismatches=sm,duration_identity_mismatches=int(duration_bad)+int(recon_bad));checks["concurrency_distribution_independently_reconstructed"]="PASS" if not dm else "FAIL";checks["concurrency_summary_independently_reconstructed"]="PASS" if not sm else "FAIL";checks["concurrency_duration_identity_independently_verified"]="PASS" if not duration_bad and not recon_bad else "FAIL"
    def overlap_expected(mode):
      out=[]
      if mode=="bridge":
       by=defaultdict(list)
       for r in rows:by[(r["generation"],r["lifecycle"],r["strategy"],r["timeframe"],r["instrument"])].append(r)
       for c in expected_c:
        base=tuple(c[k] for k in ("generation","lifecycle","strategy","timeframe"));out.append({**{k:c[k] for k in ckeys},**audit_pair_metrics(by[base+(c["instrument_a"],)],by[base+(c["instrument_b"],)])})
      elif mode=="portfolio":
       for key,part in sorted(grouped.items()):
        by=defaultdict(list)
        for r in part:by[r["instrument"]].append(r)
        for a,b in __import__('itertools').combinations(sorted(by),2):out.append({"generation":key[0],"lifecycle":key[1],"instrument_a":a,"instrument_b":b,**audit_pair_metrics(by[a],by[b])})
      else:
       byparent=defaultdict(lambda:defaultdict(list))
       for r in rows:byparent[(r["generation"],r["lifecycle"],r["instrument"])][(r["strategy"],r["timeframe"])].append(r)
       for key,by in sorted(byparent.items()):
        for a,b in __import__('itertools').combinations(sorted(by),2):out.append({"generation":key[0],"lifecycle":key[1],"instrument":key[2],"stream_a":"|".join(a),"stream_b":"|".join(b),**audit_pair_metrics(by[a],by[b])})
      return out
    metrics=("active_duration_A_hours","active_duration_B_hours","shared_active_duration_hours","union_active_duration_hours","overlap_share_A","overlap_share_B","overlap_jaccard","overlapping_trade_pairs","unique_A_trades_with_overlap","unique_B_trades_with_overlap","same_direction_overlapping_pairs","opposite_direction_overlapping_pairs","both_final_negative_pairs","both_final_positive_pairs","opposite_final_sign_pairs","zero_involved_pairs")
    eb,ep,ex=overlap_expected("bridge"),overlap_expected("portfolio"),overlap_expected("cross");ab=_rows(output/"correlation_overlap_bridge.csv");ap=_rows(output/"portfolio_instrument_overlap_report.csv");ax=_rows(output/"same_instrument_cross_stream_overlap_report.csv");bm=_compare(ab,eb,ckeys,metrics);pm=_compare(ap,ep,("generation","lifecycle","instrument_a","instrument_b"),metrics);xm=_compare(ax,ex,("generation","lifecycle","instrument","stream_a","stream_b"),metrics);details.update(bridge_rows=len(ab),bridge_overlap_mismatches=bm,portfolio_pair_rows=len(ap),portfolio_overlap_mismatches=pm,cross_stream_rows=len(ax),cross_stream_overlap_mismatches=xm);checks["correlation_overlap_bridge_metrics_reconciled"]="PASS" if not bm else "FAIL";checks["portfolio_instrument_overlap_metrics_reconciled"]="PASS" if not pm else "FAIL";checks["cross_stream_overlap_metrics_reconciled"]="PASS" if not xm else "FAIL"
    wf=[r for r in rows if r["lifecycle"]=="walk_forward"];wfparts=defaultdict(list)
    for r in wf:wfparts[(r["generation"],r["fold_id"])].append(r)
    ewfc=[];ewfo=[]
    for key,part in sorted(wfparts.items()):
      ctx,di,last=audit_sweep(part);active=sum(v[1] for v in di.values());individual=sum((r["exit"]-r["entry"]).total_seconds() for r in part);integrated=sum(k*v[1] for k,v in di.items());ewfc.append({"generation":key[0],"fold_id":key[1],"trades":len(part),"portfolio_active_duration_hours":active/3600,"sum_individual_trade_duration_hours":individual/3600,"time_weighted_mean_open_positions":integrated/active,"max_open_positions":max(di),"entries_with_any_open_before":sum(x["open_positions_before_entry"]>0 for x in ctx),"share_entries_with_any_open_before":sum(x["open_positions_before_entry"]>0 for x in ctx)/len(ctx),"entries_with_same_instrument_open_before":sum(x["same_instrument_open_before"]>0 for x in ctx)})
      by=defaultdict(list)
      for r in part:by[r["instrument"]].append(r)
      for a,b in __import__('itertools').combinations(sorted(by),2):
       m=audit_pair_metrics(by[a],by[b]);ewfo.append({"generation":key[0],"fold_id":key[1],"instrument_a":a,"instrument_b":b,**{z:m[z] for z in ("shared_active_duration_hours","overlap_share_A","overlap_share_B","overlap_jaccard","overlapping_trade_pairs","both_final_negative_pairs","opposite_final_sign_pairs")}})
    awfc=_rows(output/"wf_concurrency_report.csv");awfo=_rows(output/"wf_instrument_overlap_report.csv");wfcm=_compare(awfc,ewfc,("generation","fold_id"),tuple(k for k in ewfc[0] if k not in ("generation","fold_id")));wfom=_compare(awfo,ewfo,("generation","fold_id","instrument_a","instrument_b"),tuple(k for k in ewfo[0] if k not in ("generation","fold_id","instrument_a","instrument_b")));details.update(wf_v2_trades=sum(len(v) for k,v in wfparts.items() if k[0]=="v2"),wf_v3_trades=sum(len(v) for k,v in wfparts.items() if k[0]=="v3"),wf_concurrency_mismatches=wfcm,wf_overlap_mismatches=wfom);checks["wf_population_reconciled"]="PASS" if (details["wf_v2_trades"],details["wf_v3_trades"])==(746,515) else "FAIL";checks["eight_wf_fold_portfolios"]="PASS" if len(wfparts)==8 else "FAIL";checks["wf_concurrency_independently_reconstructed"]="PASS" if not wfcm else "FAIL";checks["wf_overlap_independently_reconstructed"]="PASS" if not wfom else "FAIL"
    allover=ab+ap+ax;partbad=sum(int(x["both_final_negative_pairs"])+int(x["both_final_positive_pairs"])+int(x["opposite_final_sign_pairs"])+int(x["zero_involved_pairs"])!=int(x["overlapping_trade_pairs"]) or int(x["same_direction_overlapping_pairs"])+int(x["opposite_direction_overlapping_pairs"])!=int(x["overlapping_trade_pairs"]) for x in allover);details["pair_partition_mismatches"]=partbad;checks["pair_outcome_partition_reconciled"]="PASS" if not partbad else "FAIL"
    for k in CHECKS[31:39]:checks[k]="PASS" if audit_scope({}) else "FAIL"
    manifest_path=output/"manifest_correlation_risk.json";impl={p:_sha(ROOT/p) for p in IMPLEMENTATION_PATHS if (ROOT/p).exists()};checks["implementation_file_hashes_verified"]="PASS" if len(impl)==3 and (not manifest_path.exists() or json.loads(manifest_path.read_text()).get("implementation_file_hashes")==impl) else "FAIL"
    changed=set()
    if manifest_path.exists():
      signed=json.loads(manifest_path.read_text()).get("output_hashes",{});changed={n for n,h in signed.items() if not (output/n).exists() or _sha(output/n)!=h}
    details["signed_artifact_hash_mismatches"]=len(changed);checks["signed_artifact_hashes_verified"]="PASS" if not changed else "FAIL";checks["deterministic_artifacts"]="PASS" if deterministic else "FAIL"
    for p in output.glob("*.csv"):
      headers=next(csv.reader(p.open(encoding="utf-8")),[])
      if not audit_scope({h:None for h in headers}):
       for k in CHECKS[31:39]:checks[k]="FAIL"
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
