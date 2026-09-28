"""Stage 5.6 causal interval and independent-certification contracts."""
from __future__ import annotations
import csv,json,shutil
from datetime import datetime,timedelta
import pytest
from TradingSystemLab.results.post_v3_analysis.stage5_structural_validation import stage5_correlation_risk as cr
from TradingSystemLab.results.post_v3_analysis.stage5_structural_validation import run_stage5_correlation_risk as runner

def _dt(s):return datetime.fromisoformat(s)
def test_half_open_overlap_contract():
    a=(_dt("2020-01-01T10:00:00+03:00"),_dt("2020-01-01T11:00:00+03:00"))
    assert cr.interval_overlap(a,(a[1],a[1]+timedelta(hours=1)))==0
    assert cr.interval_overlap(a,(a[1]-timedelta(seconds=1),a[1]+timedelta(hours=1)))==1
def test_timestamp_contract():
    assert cr.parse_time("2020-01-01T10:00:00+03:00").utcoffset().total_seconds()==10800
    for bad in ("bad","2020-01-01T10:00:00","2020-01-01T10:00:00Z"):
      with pytest.raises(ValueError,match=cr.FAIL_TIME):cr.parse_time(bad)
def test_union_does_not_double_count_and_touching_merges():
    a=_dt("2020-01-01T10:00:00+03:00");u=cr.union_intervals([(a,a+timedelta(hours=2)),(a+timedelta(hours=1),a+timedelta(hours=3)),(a+timedelta(hours=3),a+timedelta(hours=4))]);assert cr.duration(u)==14400
def test_corrected_c1_contract():
    assert cr.corrected_single_c1({"net_R":"-1.2","cost_R":".2"},"T3")==pytest.approx(-1)
    assert cr.corrected_single_c1({"net_R":"-1.2","cost_R":".2"},"T2")==pytest.approx(-1.2)
@pytest.mark.parametrize("field",runner.SCOPE_TOKENS)
def test_forbidden_scope_schema(field):assert not runner.audit_scope({field:1})

@pytest.fixture(scope="module")
def certified(tmp_path_factory):
    out=tmp_path_factory.mktemp("correlation-risk");manifest=runner.run(out,True);return out,manifest
def test_certification_and_outputs(certified):
    out,m=certified;a=json.loads((out/"correlation_risk_audit.json").read_text());assert m["status"]==a["status"]==cr.STATUS;assert set(a["checks"].values())=={"PASS"};assert m["determinism"]["byte_identical"]
    required={"Correlation_Simultaneous_Risk_Diagnostics_Report.md","manifest_correlation_risk.json","correlation_risk_audit.json","correlation_risk_reconciliation.csv","corrected_monthly_instrument_matrix.csv","corrected_pairwise_monthly_correlation.csv","correlation_overlap_bridge.csv","portfolio_instrument_overlap_report.csv","same_instrument_cross_stream_overlap_report.csv","entry_concurrency_context.csv","entry_concurrency_report.csv","concurrency_distribution_report.csv","concurrency_summary_report.csv","wf_concurrency_report.csv","wf_instrument_overlap_report.csv"};assert required<={p.name for p in out.iterdir()}
def _mutate(certified,tmp_path,file,field,amount=1):
    target=tmp_path/"copy";shutil.copytree(certified[0],target);p=target/file;rows=list(csv.DictReader(p.open()));old=rows[0][field];value=float(old)+amount;rows[0][field]=str(int(value)) if "." not in old and "e" not in old.lower() else str(value)
    with p.open("w",newline="") as f:w=csv.DictWriter(f,fieldnames=rows[0]);w.writeheader();w.writerows(rows)
    return runner._audit_build(target)
@pytest.mark.parametrize(("file","field","status"),[("corrected_monthly_instrument_matrix.csv","net_R",cr.FAIL_MONTHLY),("corrected_pairwise_monthly_correlation.csv","corrected_pearson_monthly_R",cr.FAIL_MONTHLY),("corrected_pairwise_monthly_correlation.csv","corrected_covariance_monthly_R",cr.FAIL_MONTHLY),("corrected_pairwise_monthly_correlation.csv","corrected_both_negative_months",cr.FAIL_MONTHLY),("entry_concurrency_context.csv","open_positions_before_entry",cr.FAIL_CONCURRENCY),("correlation_risk_reconciliation.csv","duration_identity_delta",cr.FAIL_CONCURRENCY),("correlation_overlap_bridge.csv","both_final_negative_pairs",cr.FAIL_OVERLAP),("portfolio_instrument_overlap_report.csv","overlap_jaccard",cr.FAIL_OVERLAP)])
def test_artifact_mutations_fail(certified,tmp_path,file,field,status):assert _mutate(certified,tmp_path,file,field)["status"]==status
def test_independent_auditor_never_calls_producer_helpers(certified,monkeypatch):
    for name in ("corrected_single_c1","interval_overlap","union_intervals","shared_duration","sweep","correlation","pair_metrics","monthly_matrix"):
      monkeypatch.setattr(cr,name,lambda *_a,**_k:(_ for _ in ()).throw(AssertionError(name)))
    assert runner._audit_build(certified[0])["status"]==cr.STATUS
def test_pair_partitions_and_symmetry(certified):
    for name in ("correlation_overlap_bridge.csv","portfolio_instrument_overlap_report.csv","same_instrument_cross_stream_overlap_report.csv"):
      rows=list(csv.DictReader((certified[0]/name).open()))
      for r in rows:
       n=int(r["overlapping_trade_pairs"]);assert sum(int(r[x]) for x in ("both_final_negative_pairs","both_final_positive_pairs","opposite_final_sign_pairs","zero_involved_pairs"))==n;assert int(r["same_direction_overlapping_pairs"])+int(r["opposite_direction_overlapping_pairs"])==n
def test_missing_implementation_hash_fails(certified,tmp_path):
    target=tmp_path/"copy";shutil.copytree(certified[0],target);p=target/"manifest_correlation_risk.json";m=json.loads(p.read_text());m["implementation_file_hashes"].pop(runner.IMPLEMENTATION_PATHS[0]);p.write_text(json.dumps(m));assert runner._audit_build(target)["status"]==cr.FAIL_INPUT
