"""Stage 5.7 artifact-only authentication and closeout tests."""
from __future__ import annotations
import csv
import importlib.util
import json
import shutil
from pathlib import Path
import pytest

ROOT=Path(__file__).resolve().parents[2]
SOURCE=ROOT/"TradingSystemLab/results/post_v3_analysis/stage5_structural_validation/stage5_closeout.py"
spec=importlib.util.spec_from_file_location("stage5_closeout_under_test",SOURCE); closeout=importlib.util.module_from_spec(spec); spec.loader.exec_module(closeout)

def _copy_inputs(tmp_path:Path)->Path:
    target=tmp_path/"stage5_structural_validation"
    shutil.copytree(closeout.HERE,target)
    return target

def test_authoritative_inputs_authenticate():
    counters,_=closeout.authenticate_inputs()
    assert not any(counters.values())

@pytest.mark.parametrize("relative",["canonical_comparator_manifest.json","../stage4_structural_hypotheses/structural_hypothesis_registry.csv"])
def test_authority_byte_mutation_fails(tmp_path,monkeypatch,relative):
    base=_copy_inputs(tmp_path); stage4=tmp_path/"stage4_structural_hypotheses"; shutil.copytree(closeout.STAGE4,stage4)
    monkeypatch.setattr(closeout,"STAGE4",stage4)
    path=(base/relative).resolve()
    if path.suffix==".json":
        value=json.loads(path.read_text()); value["trade_rows_reconciled"]=1; path.write_text(json.dumps(value))
    else: path.write_bytes(path.read_bytes()+b"mutation")
    with pytest.raises(RuntimeError): closeout.authenticate_inputs(base)

def test_missing_component_manifest_fails(tmp_path,monkeypatch):
    base=_copy_inputs(tmp_path); stage4=tmp_path/"stage4_structural_hypotheses"; shutil.copytree(closeout.STAGE4,stage4); monkeypatch.setattr(closeout,"STAGE4",stage4)
    (base/"trail1/manifest_trail1.json").unlink()
    with pytest.raises(RuntimeError,match="INPUT_AUTHENTICATION_FAILED"): closeout.authenticate_inputs(base)

def test_altered_component_audit_status_fails(tmp_path,monkeypatch):
    base=_copy_inputs(tmp_path); stage4=tmp_path/"stage4_structural_hypotheses"; shutil.copytree(closeout.STAGE4,stage4); monkeypatch.setattr(closeout,"STAGE4",stage4)
    path=base/"session_time/session_time_audit.json"; value=json.loads(path.read_text()); value["status"]="FAIL"; path.write_text(json.dumps(value))
    with pytest.raises(RuntimeError,match="COMPONENT_STATUS"): closeout.authenticate_inputs(base)

def test_final_status_authority_and_stage4_preserved():
    rows={x["component_id"]:x for x in closeout.status_rows()}
    assert rows["H4_01_PROFIT_PROTECTION_BE1"]["research_status"]=="MIXED_RETROSPECTIVE_EVIDENCE"
    assert "FORMAL_LABEL_LEFT_FOR_REVIEW_NO_FROZEN_RULE" not in json.dumps(rows)
    assert rows["H4_02_PROFIT_PROTECTION_TRAIL1"]["research_status"]=="SUPPORTED_RETROSPECTIVELY"
    risk=rows["H4_03_TOTAL_OPEN_RISK_CAP"]; assert risk["formal_research_verdict"]=="NOT_ASSIGNED" and risk["terminal_censoring"]=="true"
    assert sum(x[3]=="ADMITTED" for x in closeout.COMPONENTS)==3
    assert "H4_04" not in json.dumps(closeout.COMPONENTS)
    assert all(x[3]=="NOT_ADMITTED" for x in closeout.COMPONENTS[3:])

def test_closeout_tables_and_scope():
    rows=closeout.status_rows(); assert len(rows)==len({r["component_id"] for r in rows})==6
    unresolved=closeout.unresolved_rows(); assert len(unresolved)==1 and unresolved[0]["component"]=="H4_03_TOTAL_OPEN_RISK_CAP"
    assert all(r["automatic_production_inclusion"]==r["automatic_production_exclusion"]=="false" for r in closeout.downstream_rows())
    for key in closeout.FORBIDDEN_KEYS: assert not closeout.audit_scope({key:None})
    assert closeout.audit_scope({"artifact_only":True})

def test_source_and_implementation_hash_mutations_fail(tmp_path,monkeypatch):
    base=_copy_inputs(tmp_path); stage4=tmp_path/"stage4_structural_hypotheses"; shutil.copytree(closeout.STAGE4,stage4); monkeypatch.setattr(closeout,"STAGE4",stage4)
    report=base/"minimum_hold/Minimum_Hold_Diagnostics_Report.md"; original=report.read_bytes(); report.write_text("mutated")
    with pytest.raises(RuntimeError,match="PROTECTED_SOURCE_MUTATION"): closeout.authenticate_inputs(base)
    report.write_bytes(original)
    manifest=base/"minimum_hold/manifest_minimum_hold.json"; value=json.loads(manifest.read_text()); value["implementation_file_hashes"][next(iter(value["implementation_file_hashes"]))]="0"*64; manifest.write_text(json.dumps(value))
    with pytest.raises(RuntimeError,match="PROTECTED_SOURCE_MUTATION"): closeout.authenticate_inputs(base)

def test_build_is_byte_deterministic(tmp_path):
    one,two=tmp_path/"one",tmp_path/"two"; closeout.build(one,True); closeout.build(two,True)
    assert {p.name:p.read_bytes() for p in one.iterdir()}=={p.name:p.read_bytes() for p in two.iterdir()}
    audit=json.loads((one/"audit_stage5_closeout.json").read_text()); assert audit["status"]==closeout.STATUS and all(v=="PASS" for v in audit["checks"].values())

def test_documentation_handoff_semantics():
    paths=[ROOT/"TradingSystemLab/CURRENT_STATE.md",ROOT/"TradingSystemLab/PROJECT_CONTEXT.md",ROOT/"TradingSystemLab/ROADMAP.md",closeout.HERE/"README.md"]
    combined="\n".join(p.read_text() for p in paths)
    for phrase in ("Stage 5 CLOSED","Stage 6 Production Assembly Decision: NEXT","MIXED_RETROSPECTIVE_EVIDENCE","SUPPORTED_RETROSPECTIVELY","FORMAL_RESEARCH_VERDICT_NOT_ASSIGNED","Minimum Hold = NOT_ADMITTED","Session = NOT_ADMITTED","Correlated-risk grouping = NOT_ADMITTED"): assert phrase in combined
    roadmap=paths[2].read_text(); assert roadmap.index("Stage 5")<roadmap.index("Stage 6")

def test_no_execution_or_backtest_interfaces():
    source=SOURCE.read_text()
    for token in ("run_strategy", "simulate_trade", "load_market_data", "optimizer", "parameter_grid", "rank_candidates", "select_portfolio"):
        assert token not in source

@pytest.mark.parametrize("component,field,value",[
    ("H4_01_PROFIT_PROTECTION_BE1","research_status","SUPPORTED_RETROSPECTIVELY"),
    ("H4_02_PROFIT_PROTECTION_TRAIL1","research_status","MIXED_RETROSPECTIVE_EVIDENCE"),
    ("H4_03_TOTAL_OPEN_RISK_CAP","research_status","SUPPORTED_RETROSPECTIVELY"),
    ("MINIMUM_HOLD","stage4_admission_status","ADMITTED"),
    ("SESSION_TIME_OF_DAY","stage4_admission_status","ADMITTED"),
    ("CORRELATION_SIMULTANEOUS_RISK","stage4_admission_status","ADMITTED"),
])
def test_signed_producer_status_bug_is_independently_rejected(tmp_path,monkeypatch,component,field,value):
    original=closeout.status_rows
    def bad_rows():
        rows=original()
        next(r for r in rows if r["component_id"]==component)[field]=value
        return rows
    monkeypatch.setattr(closeout,"status_rows",bad_rows)
    with pytest.raises(RuntimeError,match="COMPONENT_STATUS_RECONCILIATION_FAILED"):
        closeout.build(tmp_path/"out",True)

@pytest.mark.parametrize("component,field,value",[
    ("H4_01_PROFIT_PROTECTION_BE1","automatic_production_inclusion","true"),
    ("H4_02_PROFIT_PROTECTION_TRAIL1","automatic_production_exclusion","true"),
    ("MINIMUM_HOLD","requires_new_hypothesis_before_rule_use","false"),
])
def test_signed_producer_downstream_bug_is_rejected(tmp_path,monkeypatch,component,field,value):
    original=closeout.downstream_rows
    def bad_rows():
        rows=original(); next(r for r in rows if r["component_id"]==component)[field]=value; return rows
    monkeypatch.setattr(closeout,"downstream_rows",bad_rows)
    with pytest.raises(RuntimeError,match="TABLE_RECONCILIATION_FAILED"): closeout.build(tmp_path/"out",True)

@pytest.mark.parametrize("mutation",["missing","extra","claim","blocking"])
def test_signed_producer_unresolved_bug_is_rejected(tmp_path,monkeypatch,mutation):
    def bad_rows():
        rows=closeout.unresolved_rows_original()
        if mutation=="missing": return []
        if mutation=="extra": return rows+[{**rows[0],"component":"H4_99_FAKE"}]
        rows[0]["production_validation_claim_allowed" if mutation=="claim" else "stage5_blocking"]="true"
        return rows
    monkeypatch.setattr(closeout,"unresolved_rows_original",closeout.unresolved_rows,raising=False)
    monkeypatch.setattr(closeout,"unresolved_rows",bad_rows)
    with pytest.raises(RuntimeError,match="TABLE_RECONCILIATION_FAILED"): closeout.build(tmp_path/"out",True)

def test_producer_constants_are_not_audit_authority(tmp_path,monkeypatch):
    wrong=[tuple("ADMITTED" if i==3 else x for i,x in enumerate(row)) for row in closeout.COMPONENTS]
    monkeypatch.setattr(closeout,"COMPONENTS",wrong)
    with pytest.raises(RuntimeError,match="COMPONENT_STATUS_RECONCILIATION_FAILED"): closeout.build(tmp_path/"out",True)

@pytest.mark.parametrize("branch",["be1","trail1","risk_cap","minimum_hold","session_time","correlation_risk"])
def test_each_protected_component_tree_detects_byte_mutation(tmp_path,monkeypatch,branch):
    base=_copy_inputs(tmp_path); stage4=tmp_path/"stage4_structural_hypotheses"; shutil.copytree(closeout.STAGE4,stage4)
    target=next(p for p in (base/branch).iterdir() if p.is_file()); target.write_bytes(target.read_bytes()+b"\nmutation")
    assert closeout.protected_source_mismatches(base,stage4)>=1
