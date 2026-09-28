"""Contracts for Stage 5.5 session/time diagnostics."""
from __future__ import annotations
import csv, json, random, shutil
from datetime import datetime
import pytest
from TradingSystemLab.results.post_v3_analysis.stage5_structural_validation import stage5_session_time as st
from TradingSystemLab.results.post_v3_analysis.stage5_structural_validation import run_stage5_session_time as runner

@pytest.mark.parametrize(("stamp","a","b"),[("09:59:59",False,False),("10:00:00",True,True),("16:59:59",True,True),("17:00:00",False,True),("20:59:59",False,True),("21:00:00",False,False)])
def test_exact_boundaries(stamp,a,b):
    m=st.session_membership(f"2020-01-01 {stamp}+03:00");assert m=={"FULL":True,"SESSION_10_17":a,"SESSION_10_21":b}

def test_time_contract_is_offset_aware_source_local():
    parsed=st.parse_entry_time("2020-01-01 10:00:00+03:00");assert parsed.hour==10 and parsed.utcoffset().total_seconds()==10800
    for bad in ("2020-01-01 10:00:00","bad","2020-01-01 10:00:00+00:00"):
        with pytest.raises(ValueError,match=st.FAIL_TIME):st.parse_entry_time(bad)

def test_entry_hour_mismatch_fails():
    with pytest.raises(RuntimeError,match=st.FAIL_TIME):st.validate_time_metadata([{"entry_time":"2020-01-01 10:00:00+03:00","entry_hour":"11"}])

def _population():
    return [{"generation":g,"lifecycle_stage":life,"canonical_trade_key":f"{g}-{life}-{i}"} for (g,life),n in st.EXPECTED.items() for i in range(n)]

def test_population_and_duplicate_hard_gates():
    rows=_population();st.validate_population(rows);assert len(rows)==9694
    rows[-1]["canonical_trade_key"]=rows[0]["canonical_trade_key"]
    with pytest.raises(RuntimeError,match=st.FAIL_CANONICAL):st.validate_population(rows)
    with pytest.raises(RuntimeError,match=st.FAIL_CANONICAL):st.validate_population(_population()[:-1])

def test_double_c1_is_corrected():
    assert st.corrected_single_c1({"net_R":"-1.2","cost_R":"0.2"},"T3")==pytest.approx(-1.0)

@pytest.mark.parametrize("field",runner.SCOPE_TOKENS)
def test_forbidden_scope_fields_fail(field):assert not runner.audit_scope({field:1})

@pytest.fixture(scope="module")
def certified(tmp_path_factory):
    out=tmp_path_factory.mktemp("session-time");manifest=runner.run(out,True);return out,manifest

def test_certification_and_required_outputs(certified):
    out,manifest=certified;audit=json.loads((out/"session_time_audit.json").read_text())
    assert manifest["status"]==audit["status"]==st.STATUS;assert set(audit["checks"].values())=={"PASS"}
    assert manifest["canonical_rows"]==9694 and manifest["determinism"]["run1"]==manifest["determinism"]["run2"]

def _mutate(certified,tmp_path,file,field,amount=.01):
    target=tmp_path/"e";shutil.copytree(certified[0],target);p=target/file;rows=list(csv.DictReader(p.open()));rows[0][field]=str(float(rows[0][field])+amount)
    with p.open("w",newline="") as f:w=csv.DictWriter(f,fieldnames=rows[0]);w.writeheader();w.writerows(rows)
    return runner._audit_build(target)

@pytest.mark.parametrize("field",["net_R","PF","expectancy_R","win_rate"])
def test_full_economic_mutations_fail(certified,tmp_path,field):assert _mutate(certified,tmp_path,"session_time_reconciliation.csv",field)["status"]==st.FAIL_ECONOMICS

def test_independent_auditor_does_not_call_producer_helpers(certified,monkeypatch):
    monkeypatch.setattr(st,"session_membership",lambda *_:(_ for _ in ()).throw(AssertionError()))
    monkeypatch.setattr(st,"metrics",lambda *_args,**_kwargs:(_ for _ in ()).throw(AssertionError()))
    assert runner._audit_build(certified[0])["status"]==st.STATUS

def test_window_counts_nested_and_wf(certified):
    rows=list(csv.DictReader((certified[0]/"session_window_report.csv").open()));counts={c:sum(int(r["trades"]) for r in rows if r["session_cohort"]==c) for c in st.COHORTS}
    assert counts["FULL"]==9694 and counts["SESSION_10_17"]<=counts["SESSION_10_21"]
    audit=json.loads((certified[0]/"session_time_audit.json").read_text());assert audit["checks"]["eight_wf_fold_portfolios"]=="PASS"

def test_aggregate_is_order_invariant():
    rows=[{"generation":"v","net_R":x} for x in (1,-2,3)];shuffled=rows[:];random.Random(1).shuffle(shuffled)
    assert st.metrics(rows)==st.metrics(shuffled)
