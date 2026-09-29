"""Materialize the frozen corrected A--F TRAIL1 replay as an additive ledger."""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path

import pandas as pd

from . import generate_reassessment as frozen

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
STARTING_MAIN_SHA = "c38a7cea0328d0eac89d986a77f45466733ef67a"
FLOAT_FORMAT = "%.12g"
LEDGER = "trail1_authoritative_trades.csv"
MANIFEST = "trail1_authoritative_ledger_manifest.json"
YEARLY_REC = "trail1_authoritative_B_D_F_reconciliation.csv"
MONTHLY_REC = "trail1_authoritative_monthly_reconciliation.csv"
BDF = {key: frozen.BASKETS[key] for key in "BDF"}
PROTECTED_AF = tuple(sorted(json.loads((HERE / "audit_manifest.json").read_text())["artifact_hashes"]))
PROTECTED_STAGE_DIRS = (
    "stage5_structural_validation", "stage6_exit_on_opposite_regime",
    "stage6_imoexf_decision_tests", "stage6_lock1_after_2r",
    "stage6_one_bar_breakout_confirmation", "stage6_production_assembly",
    "stage6_session_10_21_causal", "stage6_structural_stack",
)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def protected_hashes() -> dict[str, str]:
    base = HERE.parent
    result = {f"stage6_fixed_basket_reassessment/{name}": sha(HERE / name) for name in PROTECTED_AF}
    for dirname in PROTECTED_STAGE_DIRS:
        for path in sorted((base / dirname).rglob("*")):
            if path.is_file() and "__pycache__" not in path.parts and path.suffix != ".pyc":
                result[str(path.relative_to(base))] = sha(path)
    return result


def ledger_event_hash(frame: pd.DataFrame) -> str:
    ordered = frame.sort_values(["lifecycle", "fold_id", "exit_time", "instrument", "trade_id"], kind="mergesort").reset_index(drop=True)
    return frozen.event_sha(ordered)


def build_reconciliations(ledger: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    paths = {"TRAIL1": ledger}
    # These functions derive every field from trades; existing artifacts are only comparators.
    mon = frozen.monthly(paths | {"canonical": ledger})
    year = frozen.yearly(paths | {"canonical": ledger}, mon)
    return year[year.basket.isin(BDF)].reset_index(drop=True), mon[mon.basket.isin(BDF)].reset_index(drop=True)


def _assert_matches_frozen(year: pd.DataFrame, mon: pd.DataFrame) -> None:
    expected_y = pd.read_csv(HERE / "basket_yearly_metrics.csv").query("basket in ['B','D','F']").reset_index(drop=True)
    expected_m = pd.read_csv(HERE / "basket_monthly_metrics.csv").query("basket in ['B','D','F']").reset_index(drop=True)
    for actual, expected, name in ((year, expected_y, "YEARLY"), (mon, expected_m, "MONTHLY")):
        if list(actual.columns) != list(expected.columns) or actual.shape != expected.shape:
            raise RuntimeError(f"{name}_SCHEMA_OR_ROWS_MISMATCH")
        for col in actual.columns:
            if pd.api.types.is_numeric_dtype(expected[col]):
                if not __import__("numpy").allclose(actual[col], expected[col], atol=1e-10, rtol=0, equal_nan=True):
                    raise RuntimeError(f"{name}_{col}_MISMATCH")
            elif not actual[col].fillna("").astype(str).equals(expected[col].fillna("").astype(str)):
                raise RuntimeError(f"{name}_{col}_MISMATCH")


def execute(data_root: Path, destination: Path = HERE) -> dict:
    before = protected_hashes()
    auth = frozen.authenticate(data_root)
    paths, replay_hashes = frozen.raw_replays(data_root)
    ledger = paths["TRAIL1"].sort_values(["lifecycle", "fold_id", "exit_time", "instrument", "trade_id"], kind="mergesort").reset_index(drop=True)
    required = {"lifecycle", "fold_id", "strategy", "timeframe", "instrument", "direction", "entry_time", "exit_time", "entry_price", "exit_price", "exit_reason", "trade_id", "net_R_C1"}
    if not required.issubset(ledger.columns):
        raise RuntimeError(f"LEDGER_SCHEMA_MISSING: {sorted(required-set(ledger.columns))}")
    year, mon = build_reconciliations(ledger)
    _assert_matches_frozen(year, mon)
    destination.mkdir(parents=True, exist_ok=True)
    ledger.to_csv(destination / LEDGER, index=False, lineterminator="\n", float_format=FLOAT_FORMAT)
    year.to_csv(destination / YEARLY_REC, index=False, lineterminator="\n", float_format=FLOAT_FORMAT)
    mon.to_csv(destination / MONTHLY_REC, index=False, lineterminator="\n", float_format=FLOAT_FORMAT)
    after = protected_hashes()
    if before != after:
        raise RuntimeError("PROTECTED_EVIDENCE_CHANGED")
    reg_path = HERE.parent / "stage5_structural_validation/canonical_lifecycle_registry.csv"
    af_hashes = {k: v for k, v in before.items() if k.startswith("stage6_fixed")}
    manifest = {
        "status": "AUTHORITATIVE_TRAIL1_LEDGER_MATERIALIZED_AND_RECONCILED",
        "starting_main_sha": STARTING_MAIN_SHA,
        "source_commit": subprocess.check_output(["git", "-C", str(ROOT), "rev-parse", "HEAD"], text=True).strip(),
        "data_commit": frozen.DATA_COMMIT, "t3_sha": frozen.T3_SHA, "parameter_sha": frozen.PARAM_SHA,
        "trail1_implementation_sha": frozen.TRAIL_SHA, "lifecycle_registry_sha": sha(reg_path),
        "corrected_af_generator_sha": sha(HERE / "generate_reassessment.py"),
        "corrected_af_audit_manifest_sha": sha(HERE / "audit_manifest.json"),
        "stage5_manifest_sha": sha(HERE.parent / "stage5_structural_validation/trail1/manifest_trail1.json"),
        "raw_h1_source_hashes": auth["source_hashes"], "row_count": len(ledger),
        "event_hash": ledger_event_hash(ledger), "repeated_replay_hashes": replay_hashes["TRAIL1"],
        "committed_file_sha256": sha(destination / LEDGER),
        "first_entry": str(pd.to_datetime(ledger.entry_time, utc=True).min()),
        "last_exit": str(pd.to_datetime(ledger.exit_time, utc=True).max()),
        "instruments": sorted(ledger.instrument.unique()),
        "lifecycle_coverage": sorted(ledger.lifecycle.unique()),
        "trade_counts_by_instrument_lifecycle": ledger.groupby(["instrument", "lifecycle"]).size().rename("trades").reset_index().to_dict("records"),
        "b_d_f_reconciliation_status": "PASSED", "existing_af_hashes_before": af_hashes,
        "existing_af_hashes_after": {k: v for k, v in after.items() if k.startswith("stage6_fixed")},
        "protected_stage5_and_stage6_1_to_6_5_hashes": {k: v for k, v in before.items() if not k.startswith("stage6_fixed")},
        "old_trail1_reconciliation_used": False, "trail1_digest_used": False, "stage7_executed": False,
    }
    (destination / MANIFEST).write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(); parser.add_argument("--data-root", type=Path); parser.add_argument("--output-dir", type=Path, default=HERE)
    args = parser.parse_args()
    if args.data_root is None:
        from TradingSystemLab.results.post_v3_analysis.stage5_structural_validation.run_stage5_trail1 import resolve_data_root
        args.data_root, _ = resolve_data_root()
    print(json.dumps(execute(args.data_root.resolve(), args.output_dir.resolve()), sort_keys=True))

if __name__ == "__main__": main()
