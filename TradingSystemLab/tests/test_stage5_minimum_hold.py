"""Focused contracts for Stage 5.4 minimum-holding diagnostics."""
from __future__ import annotations

import csv
import json
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


def test_canonical_9694_hard_gate_and_parent_counts():
    rows=_population(); mh.validate_population(rows)
    assert len(rows) == 9694
    assert sum(mh.EXPECTED.values()) == 9694


def test_duplicate_and_unmatched_population_fail_closed():
    rows=_population(); rows[-1]["canonical_trade_key"]=rows[0]["canonical_trade_key"]
    with pytest.raises(RuntimeError, match=mh.FAIL_CANONICAL): mh.validate_population(rows)
    with pytest.raises(RuntimeError, match=mh.FAIL_CANONICAL): mh.validate_population(_population()[:-1])


def test_old_double_c1_cannot_pass_reconciliation():
    raw={"net_R":"-1.2","cost_R":"0.2"}
    assert mh.corrected_single_c1(raw,"T3") == pytest.approx(-1.0)
    assert mh.corrected_single_c1(raw,"T3") != float(raw["net_R"])


def test_certified_outputs_have_no_selection_and_mirror_audit(tmp_path):
    manifest=runner.run(tmp_path,certify=True)
    audit=json.loads((tmp_path/"minimum_hold_audit.json").read_text())
    assert manifest["status"] == audit["status"] == mh.STATUS
    assert manifest["determinism"]["status"] == "PASS"
    assert manifest["canonical_rows"] == manifest["matched_holding_rows"] == 9694
    assert manifest["no_parameter_search"] and manifest["no_counterfactual_execution"]
    forbidden={"selected_duration","best_duration","selected_cutoff","ranking","score"}
    assert forbidden.isdisjoint(manifest)
    for path in tmp_path.glob("*.csv"):
        with path.open(newline="") as f: assert forbidden.isdisjoint(next(csv.reader(f)))


def test_manifest_status_is_derived_from_audit():
    audit=runner._audit_build(Path("unused"),{"canonical_rows":9694},False)
    assert audit["status"] == mh.FAIL_DETERMINISM


def test_input_authentication_failure_is_fail_closed(monkeypatch):
    monkeypatch.setattr(runner, "_sha", lambda path: "tampered")
    with pytest.raises(RuntimeError, match=mh.FAIL_INPUT): runner.authenticate()
