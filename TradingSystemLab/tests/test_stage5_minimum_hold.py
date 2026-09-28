"""Focused contracts for Stage 5.4 minimum-holding diagnostics."""
from __future__ import annotations

import csv
import json
import random
import shutil
from pathlib import Path

import pytest

from TradingSystemLab.results.post_v3_analysis.stage5_structural_validation import stage5_minimum_hold as mh
from TradingSystemLab.results.post_v3_analysis.stage5_structural_validation import run_stage5_minimum_hold as runner


@pytest.mark.parametrize(("value", "expected"), [
    ("0.999", "<1h"), ("1", "1–3h"), ("3", "3–6h"), ("6", "6–12h"),
    ("12", "12–24h"), ("24", "24–48h"), ("48", "48–96h"),
    ("96", "48–96h"), ("96.001", ">96h"), ("", "UNAVAILABLE"),
])
def test_exact_frozen_bucket_boundaries(value, expected):
    assert mh.holding_bucket(value) == expected


def _population():
    rows=[]
    for (generation,lifecycle), count in mh.EXPECTED.items():
        rows.extend({"generation":generation,"lifecycle_stage":lifecycle,
                     "canonical_trade_key":f"{generation}-{lifecycle}-{i}"} for i in range(count))
    return rows


def _trade(key, exit_time, value, entry_time="2020-01-01 00:00:00"):
    return {"canonical_trade_key": key, "entry_time": entry_time,
            "exit_time": exit_time, "net_R": value}


def test_canonical_9694_hard_gate_and_parent_counts():
    rows=_population(); mh.validate_population(rows)
    assert len(rows) == sum(mh.EXPECTED.values()) == 9694


def test_duplicate_and_unmatched_population_fail_closed():
    rows=_population(); rows[-1]["canonical_trade_key"]=rows[0]["canonical_trade_key"]
    with pytest.raises(RuntimeError, match=mh.FAIL_CANONICAL): mh.validate_population(rows)
    with pytest.raises(RuntimeError, match=mh.FAIL_CANONICAL): mh.validate_population(_population()[:-1])


def test_old_double_c1_cannot_pass_reconciliation():
    raw={"net_R":"-1.2","cost_R":"0.2"}
    assert mh.corrected_single_c1(raw,"T3") == pytest.approx(-1.0)
    assert mh.corrected_single_c1(raw,"T3") != float(raw["net_R"])


def test_chronological_dd_differs_from_physical_row_order():
    rows=[_trade("a","2020-01-01 02:00:00",-4), _trade("b","2020-01-01 01:00:00",5), _trade("c","2020-01-01 03:00:00",-4)]
    chronological=mh._maxdd(rows)[0]
    physical=mh._maxdd([{**r,"exit_time":f"2020-01-01 0{i}:00:00"} for i,r in enumerate(rows,1)])[0]
    assert chronological == -8 and physical == -4


def test_shuffling_cannot_change_chronological_dd():
    rows=[_trade(str(i),f"2020-01-01 0{i}:00:00",v) for i,v in enumerate((2,-4,3),1)]
    shuffled=rows[:]; random.Random(42).shuffle(shuffled)
    assert mh._maxdd(rows) == mh._maxdd(shuffled)


def test_exit_time_order_and_tie_break_are_deterministic():
    # Same exit and entry: canonical identity a realizes the loss before b.
    rows=[_trade("b","2020-01-01 02:00:00",5), _trade("a","2020-01-01 02:00:00",-3)]
    assert mh._maxdd(rows) == (-3, pytest.approx(2/3))
    assert mh._maxdd(rows[::-1]) == mh._maxdd(rows)


def test_recovery_uses_chronological_dd():
    rows=[_trade("a","2020-01-01 01:00:00",5),_trade("b","2020-01-01 02:00:00",-2),_trade("c","2020-01-01 03:00:00",1)]
    assert mh._maxdd(rows) == (-2, 2)


def test_be1_is_not_canonical_dd_authority():
    source=Path(mh.__file__).read_text()
    assert "be1_c1_corrected_lifecycle_report.csv" not in source


@pytest.fixture(scope="module")
def certified(tmp_path_factory):
    output=tmp_path_factory.mktemp("minimum-hold")
    manifest=runner.run(output,certify=True)
    return output, manifest


def _copy(certified, tmp_path):
    output,_=certified; target=tmp_path/"evidence"; shutil.copytree(output,target); return target


def _audit(path, deterministic=True):
    return runner._audit_build(path,{"canonical_rows":9694},deterministic)


def test_certified_outputs_and_every_executed_check_pass(certified):
    output,manifest=certified; audit=json.loads((output/"minimum_hold_audit.json").read_text())
    assert manifest["status"] == audit["status"] == mh.STATUS
    assert set(audit["checks"]) == set(runner.AUDIT_CHECKS)
    assert set(audit["checks"].values()) == {"PASS"}
    assert audit["single_C1_mismatches"] == audit["identity_mismatches"] == 0
    assert manifest["determinism"]["run1"] == manifest["determinism"]["run2"]


def test_be1_dd_mutation_cannot_affect_audit(certified, tmp_path):
    # The evidence audit has no BE1 dependency; a copied build stays certified.
    assert _audit(_copy(certified,tmp_path))["checks"]["chronological_DD_reconciled"] == "PASS"


def test_single_c1_mutation_causes_economics_failure(certified, tmp_path):
    path=_copy(certified,tmp_path); rows=list(csv.DictReader((path/"minimum_hold_reconciliation.csv").open()))
    rows[0]["net_R"]=str(float(rows[0]["net_R"])+1)
    with (path/"minimum_hold_reconciliation.csv").open("w",newline="") as f:
        w=csv.DictWriter(f,fieldnames=rows[0]); w.writeheader(); w.writerows(rows)
    assert _audit(path)["status"] == mh.FAIL_ECONOMICS


def test_holding_identity_mutation_causes_canonical_failure(certified, monkeypatch):
    original=runner._independent_canonical_rows
    def mutated():
        rows,facts=original(); facts["identity_mismatches"]=1; return rows,facts
    monkeypatch.setattr(runner,"_independent_canonical_rows",mutated)
    assert _audit(certified[0])["status"] == mh.FAIL_CANONICAL


@pytest.mark.parametrize("target", ["structural_hypothesis_registry.csv","structural_hypothesis_validation_contract.csv"])
def test_stage4_protected_mutation_fails_input_authentication(monkeypatch,target):
    real=runner._sha
    monkeypatch.setattr(runner,"_sha",lambda path: "tampered" if path.name==target else real(path))
    with pytest.raises(RuntimeError,match=mh.FAIL_INPUT): runner.authenticate()


def test_strategy_hash_mutation_fails(monkeypatch):
    real=runner._sha
    monkeypatch.setattr(runner,"_sha",lambda path: "tampered" if path.name=="T2_Trend_Pullback.py" else real(path))
    with pytest.raises(RuntimeError,match=mh.FAIL_INPUT): runner.authenticate()


@pytest.mark.parametrize(("field", "check"), [
    ("selected_duration","no_selected_or_best_cutoff"), ("score","no_ranking_fields"),
    ("counterfactual_net_r","no_counterfactual_pnl"), ("duration_grid","no_duration_candidates")])
def test_scope_fields_fail_closed(certified,tmp_path,field,check):
    path=_copy(certified,tmp_path); report=path/"minimum_hold_reconciliation.csv"
    rows=list(csv.DictReader(report.open())); rows[0][field]="forbidden"
    with report.open("w",newline="") as f:
        w=csv.DictWriter(f,fieldnames=rows[0]); w.writeheader(); w.writerows(rows)
    audit=_audit(path)
    assert audit["checks"][check] == "FAIL" and audit["status"] == mh.FAIL_SCOPE


def test_status_precedence_and_determinism_only():
    checks={name:"PASS" for name in runner.AUDIT_CHECKS}
    checks["deterministic_artifacts"]="FAIL"; assert runner._status(checks)==mh.FAIL_DETERMINISM
    checks["comparator_economics_reconciled"]="FAIL"; assert runner._status(checks)==mh.FAIL_ECONOMICS
    checks["bucket_parent_sums"]="FAIL"; assert runner._status(checks)==mh.FAIL_BUCKET


def test_bucket_mutation_maps_to_bucket_status(certified,tmp_path):
    path=_copy(certified,tmp_path); report=path/"minimum_hold_bucket_report.csv"
    rows=list(csv.DictReader(report.open())); rows[0]["trades"]=str(int(rows[0]["trades"])+1)
    with report.open("w",newline="") as f:
        w=csv.DictWriter(f,fieldnames=rows[0]); w.writeheader(); w.writerows(rows)
    assert _audit(path)["status"] == mh.FAIL_BUCKET


def test_manifest_status_exactly_mirrors_audit(certified):
    output,manifest=certified
    assert manifest["status"] == json.loads((output/"minimum_hold_audit.json").read_text())["status"]
