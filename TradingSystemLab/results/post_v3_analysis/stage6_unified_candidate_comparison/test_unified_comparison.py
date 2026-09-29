import csv
from pathlib import Path

import pytest

from .generate_unified_comparison import HERE, VARIANTS, generate, inspect


def test_exact_variant_universe():
    assert tuple(VARIANTS) == ("CANONICAL", "TRAIL1", "SESSION_10_21", "LOCK1_AFTER_2R", "STRUCTURAL_STACK_V1")


def test_missing_trail1_trade_ledger_fails_closed(tmp_path: Path):
    assert inspect(VARIANTS["TRAIL1"])["source_status"] == "SOURCE_INCOMPLETE"
    with pytest.raises(RuntimeError, match="SOURCE_INCOMPLETE.*TRAIL1"):
        generate(tmp_path)
    with (tmp_path / "variant_source_registry.csv").open(newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == 5
    assert next(r for r in rows if r["variant"] == "TRAIL1")["trade_count"] == "0"


def test_summaries_are_not_accepted_as_trade_ledgers():
    digest = HERE.parent / "stage5_structural_validation/trail1/trail1_trade_digest.csv"
    assert digest.exists()
    assert inspect(digest)["source_status"] == "SOURCE_INCOMPLETE"
