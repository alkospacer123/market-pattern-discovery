import csv
import importlib.util
import json
import shutil
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parents[1] / "results/post_v3_analysis/stage6_production_assembly"
SPEC = importlib.util.spec_from_file_location("stage6", HERE / "stage6_production_assembly.py")
stage6 = importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(stage6)


@pytest.fixture()
def built(tmp_path):
    stage6.build(tmp_path)
    return tmp_path


def mutate_csv(path, mutate):
    with path.open(newline="") as f: rows=list(csv.DictReader(f)); fields=list(rows[0])
    mutate(rows, fields)
    with path.open("w",newline="") as f:
        w=csv.DictWriter(f,fieldnames=fields,lineterminator="\n"); w.writeheader(); w.writerows(rows)


def counter(path, name): return stage6.independent_audit(path)["counters"][name]


def test_canonical_build_passes_and_contract_is_simple(built):
    audit=stage6.independent_audit(built)
    assert audit["status"] == stage6.AUDIT_STATUS
    assert all(v == 0 for v in audit["counters"].values())
    assembly=stage6.read_csv(built/"production_assembly_decision.csv")
    assert len(assembly)==3
    assert {(r["generation"],r["strategy"],r["timeframe"],r["structural_overlay"]) for r in assembly} == {("v3","T3","H1","TRAIL1")}


@pytest.mark.parametrize("field,value",[("true_oos_classification","FAIL"),("wf_expectancy_R","-1"),("oos_net_R","-1"),("oos_monthly_equity_DD","-999"),("oos_net_R_without_top5","-1")])
def test_parent_evidence_mutations_fail(built,field,value):
    mutate_csv(built/"production_parent_evidence.csv",lambda rows,_: rows[0].__setitem__(field,value))
    assert counter(built,"parent_evidence_mismatches") > 0


@pytest.mark.parametrize("mode",["missing","extra"])
def test_parent_population_mutations_fail(built,mode):
    def change(rows,fields): rows.pop() if mode=="missing" else rows.append(dict(rows[0]))
    mutate_csv(built/"production_parent_evidence.csv",change)
    assert counter(built,"parent_evidence_mismatches") > 0


@pytest.mark.parametrize("mode",["two","zero","wrong"])
def test_parent_decision_mutations_fail(built,mode):
    def change(rows,_):
        if mode=="two": rows[0]["decision"]="SELECTED"
        elif mode=="zero":
            for r in rows: r["decision"]="NOT_SELECTED"
        else:
            for r in rows: r["decision"]="SELECTED" if (r["generation"],r["strategy"],r["timeframe"])==("v2","T2","M30") else "NOT_SELECTED"
    mutate_csv(built/"production_parent_decision.csv",change)
    assert counter(built,"parent_selection_violations") > 0


@pytest.mark.parametrize("field,value",[("wf_net_R","-1"),("wf_PF","1"),("oos_expectancy_R","-1")])
def test_instrument_evidence_mutations_fail(built,field,value):
    mutate_csv(built/"production_instrument_evidence.csv",lambda rows,_: rows[0].__setitem__(field,value))
    assert counter(built,"instrument_evidence_mismatches") > 0


@pytest.mark.parametrize("mode",["one","four","outside","generation","strategy","timeframe"])
def test_assembly_contract_mutations_fail(built,mode):
    p=built/"production_assembly_decision.csv"
    def change(rows,_):
        if mode=="one": del rows[1:]
        elif mode=="four": rows.append(dict(rows[0],instrument="USDRUBF"))
        elif mode=="outside": rows[0]["instrument"]="BR"
        elif mode=="generation": rows[0]["generation"]="v2"
        elif mode=="strategy": rows[0]["strategy"]="T2"
        else: rows[0]["timeframe"]="M30"
    mutate_csv(p,change)
    assert counter(built,"instrument_selection_violations") > 0


@pytest.mark.parametrize("component",["MINIMUM_HOLD","SESSION","CORRELATED_RISK_GROUP"])
def test_not_admitted_overlay_cannot_be_selected(built,component):
    def change(rows,_):
        for r in rows: r["decision"]="SELECTED" if r["component"]==component else "NOT_SELECTED"
    mutate_csv(built/"structural_overlay_decision.csv",change)
    assert counter(built,"overlay_status_mismatches") > 0


def test_combined_exit_overlay_fails(built):
    mutate_csv(built/"production_assembly_decision.csv",lambda rows,_: [r.__setitem__("structural_overlay","BE1+TRAIL1") for r in rows])
    assert counter(built,"instrument_selection_violations") > 0


def test_risk_cap_cannot_be_labeled_validated(built):
    def change(rows,_):
        next(r for r in rows if "RISK_CAP" in r["component"])["decision"]="VALIDATED_PRODUCTION_OVERLAY"
    mutate_csv(built/"structural_overlay_decision.csv",change)
    assert counter(built,"overlay_status_mismatches") > 0


@pytest.mark.parametrize("file,field,counter_name",[("selected_assembly_monthly_series.csv","portfolio_R","selected_monthly_mismatches"),("selected_assembly_summary.csv","positive_months","selected_summary_mismatches"),("selected_assembly_summary.csv","monthly_R_std","selected_summary_mismatches"),("selected_assembly_summary.csv","worst_month_R","selected_summary_mismatches"),("selected_assembly_summary.csv","monthly_equity_max_DD_R","selected_summary_mismatches")])
def test_portfolio_mutations_fail(built,file,field,counter_name):
    mutate_csv(built/file,lambda rows,_: rows[0].__setitem__(field,"999"))
    assert counter(built,counter_name)>0


@pytest.mark.parametrize("column",["weighted_score","rank","objective_function","all_subsets","optimizer"])
def test_forbidden_schema_contamination_fails(built,column):
    def change(rows,fields):
        fields.append(column)
        for r in rows:r[column]="x"
    mutate_csv(built/"production_parent_decision.csv",change)
    assert counter(built,"scope_violations")>0


def test_two_fresh_builds_are_byte_identical(tmp_path):
    a,b=tmp_path/"a",tmp_path/"b"; stage6.build(a); stage6.build(b)
    for p in a.iterdir():
        if p.suffix in {".csv",".json",".md"} and p.name!="manifest_stage6.json": assert p.read_bytes()==(b/p.name).read_bytes()
