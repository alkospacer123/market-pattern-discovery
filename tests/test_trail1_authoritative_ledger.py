import json
from pathlib import Path

import pandas as pd
import pytest

from TradingSystemLab.results.post_v3_analysis.stage6_fixed_basket_reassessment import audit_trail1_authoritative_ledger as audit
from TradingSystemLab.results.post_v3_analysis.stage6_fixed_basket_reassessment import materialize_trail1_authoritative_ledger as producer
from TradingSystemLab.results.post_v3_analysis.stage6_fixed_basket_reassessment import generate_reassessment as frozen

HERE = producer.HERE


def ledger():
    return pd.read_csv(HERE / producer.LEDGER, keep_default_na=False)


def test_committed_ledger_rebuilds_frozen_bdf():
    year, month = audit.independently_rebuild(ledger())
    expected_year = pd.read_csv(HERE / "basket_yearly_metrics.csv").query("basket in ['B','D','F']").reset_index(drop=True)
    expected_month = pd.read_csv(HERE / "basket_monthly_metrics.csv").query("basket in ['B','D','F']").reset_index(drop=True)
    audit._equal_frame(year, expected_year, "YEAR")
    audit._equal_frame(month, expected_month, "MONTH")


@pytest.mark.parametrize("column,value", [
    ("net_R_C1", 999.0), ("instrument", "MUTATED"), ("lifecycle", "MUTATED"),
    ("exit_time", "1999-01-01T00:00:00Z"), ("trade_id", "MUTATED"),
])
def test_trade_mutations_change_authenticated_event_hash(column, value):
    frame = ledger(); original = producer.ledger_event_hash(frame); frame.loc[0, column] = value
    assert producer.ledger_event_hash(frame) != original


def test_removed_trade_changes_authenticated_event_hash():
    frame = ledger(); assert producer.ledger_event_hash(frame.iloc[1:]) != producer.ledger_event_hash(frame)


@pytest.mark.parametrize("key", ["trail1_implementation_sha", "parameter_sha"])
def test_identity_mutations_are_not_expected_identity(key):
    manifest = json.loads((HERE / producer.MANIFEST).read_text()); manifest[key] = "0" * 64
    expected = {"trail1_implementation_sha": frozen.TRAIL_SHA, "parameter_sha": frozen.PARAM_SHA}
    assert manifest[key] != expected[key]


def test_membership_and_frozen_result_mutations_detected():
    frame = ledger(); year, month = audit.independently_rebuild(frame)
    expected = pd.read_csv(HERE / "basket_yearly_metrics.csv").query("basket in ['B','D','F']").reset_index(drop=True)
    mutated = expected.copy(); mutated.loc[0, "net_R"] += 1
    with pytest.raises(RuntimeError): audit._equal_frame(year, mutated, "YEAR")
    mutated_month = pd.read_csv(HERE / "basket_monthly_metrics.csv").query("basket in ['B','D','F']").reset_index(drop=True)
    mutated_month.loc[0, "net_R"] += 1
    with pytest.raises(RuntimeError): audit._equal_frame(month, mutated_month, "MONTH")
