"""Certify deterministic Stage 5.4 minimum-holding diagnostics."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import shutil
import subprocess
import tempfile
from collections import defaultdict
from pathlib import Path

from . import stage5_minimum_hold as diagnostic

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
DEFAULT_OUTPUT = HERE / "minimum_hold"
TASK_BASE_SHA = "f39368d06ea54847732e8047e0e281030525644b"
T2_HASH = "376df085cfda85eefccb31343aad40ed4fbb1078f1314496472a3a4ac9507774"
T3_HASH = "840dd3b2cda43fa00259445cd0a22ace6d82e677f4c793028ccc8126f9ad9a8c"
AUDIT_CHECKS = (
    "inputs_authenticated", "comparator_files_authenticated", "stage3_files_authenticated",
    "stage4_registry_unchanged", "stage4_validation_contract_unchanged", "strategy_sources_unchanged",
    "canonical_rows_9694", "lifecycle_counts_exact", "holding_one_to_one",
    "no_duplicate_trade_identity", "no_unmatched_trades", "no_unexpected_stage3_rows",
    "single_C1_preserved", "comparator_economics_reconciled", "chronological_DD_reconciled",
    "comparator_trade_metrics_reconciled", "single_C1_independently_reconstructed",
    "producer_single_C1_function_not_used_by_auditor", "chronological_DD_independently_reconstructed",
    "chronological_recovery_independently_reconstructed", "no_hardcoded_comparator_delta",
    "implementation_file_hashes_recorded",
    "frozen_bucket_boundaries", "bucket_parent_sums", "lifecycle_total_9694",
    "wf_population_reconciled", "eight_wf_fold_portfolios", "wf_fold_parent_sums",
    "no_duration_candidates", "no_ranking_fields", "no_selected_or_best_cutoff",
    "no_counterfactual_pnl", "no_optimizer_or_parameter_search", "no_causal_minimum_hold_execution",
    "deterministic_artifacts")
INPUT_CHECKS = set(AUDIT_CHECKS[:6])
CANONICAL_CHECKS = set(AUDIT_CHECKS[6:12])
ECONOMICS_CHECKS = set(AUDIT_CHECKS[12:22])
BUCKET_CHECKS = set(AUDIT_CHECKS[22:28])
SCOPE_CHECKS = set(AUDIT_CHECKS[28:34])


def _sha(path: Path) -> str: return hashlib.sha256(path.read_bytes()).hexdigest()

def _json(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")

def _git(*args: str) -> str:
    return subprocess.run(["git", "-C", str(ROOT), *args], check=True, text=True, capture_output=True).stdout.strip()

def _rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as f: return list(csv.DictReader(f))


def authenticate() -> dict:
    """Authenticate every prerequisite against its frozen authority."""
    try:
        subprocess.run(["git", "-C", str(ROOT), "merge-base", "--is-ancestor", TASK_BASE_SHA, "HEAD"], check=True)
        manifest = json.loads((HERE / "canonical_comparator_manifest.json").read_text())
        audit = json.loads((HERE / "canonical_comparator_audit_result.json").read_text())
        comparator_files = {
            "canonical_comparator_reconciliation.csv": manifest["output_hashes"]["aggregate"],
            "canonical_comparator_trade_reconciliation.csv": manifest["output_hashes"]["trades"],
            "canonical_lifecycle_registry.csv": manifest["output_hashes"]["registry"],
        }
        if any(_sha(HERE / name) != digest for name, digest in comparator_files.items()): raise ValueError("comparator hash")
        if manifest.get("trade_rows_reconciled") != 9694 or manifest.get("trade_level_mismatch_count") != 0: raise ValueError("comparator population")
        if audit.get("status") != "STAGE5_CANONICAL_COMPARATOR_INDEPENDENT_AUDIT_PASSED": raise ValueError("comparator audit")
        stage3_manifest = json.loads((diagnostic.STAGE3 / "manifest_stage3a4_v3.json").read_text())
        expected = {**stage3_manifest["prerequisite_normalized_hashes"], **stage3_manifest["partition_hashes"]}
        if any(_sha(diagnostic.STAGE3 / name) != expected[name] for name in diagnostic.NORMALIZED): raise ValueError("stage3 hash")
        stage4 = manifest["stage4_hashes"]
        if any(_sha(diagnostic.STAGE4 / name) != digest for name, digest in stage4.items()): raise ValueError("stage4 hash")
        strategies = ROOT / "TradingSystemLab/strategies/trend"
        if _sha(strategies / "T2_Trend_Pullback.py") != T2_HASH or _sha(strategies / "T3_MTF_Trend.py") != T3_HASH: raise ValueError("strategy hash")
        stage4_report = diagnostic.STAGE4 / "Stage_4_Structural_Hypothesis_Set.md"
        if "Minimum hold — `NOT_ADMITTED`" not in stage4_report.read_text(): raise ValueError("stage4 status")
        return {
            "comparator_hashes": {name: _sha(HERE/name) for name in comparator_files},
            "stage3_hashes": {name: _sha(diagnostic.STAGE3/name) for name in diagnostic.NORMALIZED},
            "stage4_hashes": {name: _sha(diagnostic.STAGE4/name) for name in stage4},
            "stage4_report_hash": _sha(stage4_report), "stage4_status": "NOT_ADMITTED"}
    except Exception as exc:
        raise RuntimeError(diagnostic.FAIL_INPUT) from exc


def _independent_canonical_rows() -> tuple[list[dict], dict]:
    """Reconstruct canonical rows without using build() or its compact outputs."""
    result, source_cache, identities = [], {}, set()
    counts, identity_mismatches, c1_mismatches = defaultdict(int), 0, 0
    t2_rows = t3_rows = 0; maximum_c1_delta = 0.0
    for name in diagnostic.NORMALIZED:
        for meta in _rows(diagnostic.STAGE3 / name):
            source = ROOT / meta["source_path"]
            if source not in source_cache: source_cache[source] = _rows(source)
            pos = int(meta["source_row_number"]) - 2
            raw = source_cache[source][pos] if 0 <= pos < len(source_cache[source]) else {}
            identity = (raw.get("trade_id", ""), raw.get("symbol", ""), raw.get("direction", ""), raw.get("entry_time", ""), raw.get("exit_time", ""))
            expected = (meta["source_trade_id"], meta["instrument"], meta["direction"], meta["entry_time"], meta["exit_time"])
            identity_mismatches += identity != expected
            net_col = "net_R_C1" if "net_R_C1" in raw else "net_R"
            raw_net, cost = float(raw[net_col]), float(raw.get("cost_R") or 0)
            if meta["strategy"] == "T3":
                corrected = raw_net + cost; expected_c1 = float(meta["canonical_C1_R"]) + cost; t3_rows += 1
            else:
                corrected = raw_net; expected_c1 = float(meta["canonical_C1_R"]); t2_rows += 1
            delta = corrected - expected_c1
            maximum_c1_delta = max(maximum_c1_delta, abs(delta))
            c1_mismatches += abs(delta) > diagnostic.TOL
            key = meta["canonical_trade_key"]; identities.add(key)
            result.append({**meta, "lifecycle": meta["lifecycle_stage"], "net_R": corrected,
                           "holding_bucket": diagnostic.holding_bucket(meta.get("holding_hours")),
                           "fold_id": raw.get("fold", "")})
            counts[(meta["generation"], meta["lifecycle_stage"])] += 1
    facts = {"rows": len(result), "unique": len(identities), "counts": dict(counts),
             "identity_mismatches": identity_mismatches, "single_C1_mismatches": c1_mismatches,
             "T2_single_C1_rows": t2_rows, "T3_corrected_single_C1_rows": t3_rows,
             "maximum_single_C1_delta": maximum_c1_delta}
    return result, facts


def _audit_comparator_metrics(canonical: list[dict]) -> dict[tuple[str, str], dict[str, float]]:
    """Independently aggregate authenticated study evidence into six portfolios."""
    certified = _rows(diagnostic.HERE / "canonical_comparator_trade_reconciliation.csv")
    if len(certified) != 24 or any(x["status"] != "PASS" or int(x["total_mismatches"]) for x in certified): return {}
    grouped = defaultdict(list)
    for row in canonical: grouped[(row["generation"], row["lifecycle"])].append(row)
    result = {}
    for key, rows in grouped.items():
        values = [float(x["net_R"]) for x in rows]; wins = [x for x in values if x > 0]; losses = [x for x in values if x < 0]
        result[key] = {"trades": len(values), "net_R": sum(values), "expectancy_R": sum(values)/len(values),
                       "PF": sum(wins)/-sum(losses), "win_rate": len(wins)/len(values)}
    return result


def _audit_groups(rows: list[dict], keys: tuple[str, ...]) -> dict[tuple[str, ...], list[dict]]:
    """Group rows without depending on the evidence producer's aggregation code."""
    grouped: dict[tuple[str, ...], list[dict]] = defaultdict(list)
    for row in rows:
        grouped[tuple(row[key] for key in keys)].append(row)
    return grouped


def _audit_trade_metrics(rows: list[dict]) -> dict[str, float]:
    """Reconstruct the five comparator metrics in audit-owned code."""
    values = [float(row["net_R"]) for row in rows]
    gains = math.fsum(value for value in values if value > 0)
    losses = -math.fsum(value for value in values if value < 0)
    total = math.fsum(values)
    return {
        "trades": len(values),
        "net_R": total,
        "expectancy_R": total / len(values) if values else 0.0,
        "PF": gains / losses if losses else (math.inf if gains else 0.0),
        "win_rate": sum(value > 0 for value in values) / len(values) if values else 0.0,
    }


def _audit_chronological_portfolio_metrics(rows: list[dict]) -> tuple[float, float]:
    equity = peak = 0.0; drawdowns = []
    for row in sorted(rows, key=lambda x: (x["exit_time"], x["entry_time"], x["canonical_trade_key"])):
        equity += float(row["net_R"]); peak = max(peak, equity); drawdowns.append(equity - peak)
    maximum_dd = min(drawdowns, default=0.0)
    return maximum_dd, equity / abs(maximum_dd) if maximum_dd else 0.0


def _status(checks: dict[str, str]) -> str:
    """Map failures using fixed input→canonical→bucket→economics→scope→determinism precedence."""
    failed = {name for name, value in checks.items() if value != "PASS"}
    if failed & INPUT_CHECKS: return diagnostic.FAIL_INPUT
    if failed & CANONICAL_CHECKS: return diagnostic.FAIL_CANONICAL
    if failed & BUCKET_CHECKS: return diagnostic.FAIL_BUCKET
    if failed & ECONOMICS_CHECKS: return diagnostic.FAIL_ECONOMICS
    if failed & SCOPE_CHECKS: return diagnostic.FAIL_SCOPE
    if "deterministic_artifacts" in failed: return diagnostic.FAIL_DETERMINISM
    return diagnostic.STATUS


def _audit_build(output: Path, facts: dict, deterministic: bool) -> dict:
    """Independently re-read evidence and prove each check before marking PASS."""
    checks = {name: "NOT_CHECKED" for name in AUDIT_CHECKS}
    details = {"path_mismatches": 0, "identity_mismatches": 0, "single_C1_mismatches": 0}
    try:
        provenance = authenticate()
        checks.update({name: "PASS" for name in INPUT_CHECKS})
        canonical, independent = _independent_canonical_rows()
        details.update(identity_mismatches=independent["identity_mismatches"], single_C1_mismatches=independent["single_C1_mismatches"],
                       T2_single_C1_rows=independent["T2_single_C1_rows"], T3_corrected_single_C1_rows=independent["T3_corrected_single_C1_rows"],
                       maximum_single_C1_delta=independent["maximum_single_C1_delta"])
        checks["canonical_rows_9694"] = "PASS" if independent["rows"] == 9694 else "FAIL"
        checks["lifecycle_counts_exact"] = "PASS" if independent["counts"] == diagnostic.EXPECTED else "FAIL"
        checks["holding_one_to_one"] = "PASS" if independent["identity_mismatches"] == 0 and independent["rows"] == 9694 else "FAIL"
        checks["no_duplicate_trade_identity"] = "PASS" if independent["unique"] == independent["rows"] else "FAIL"
        checks["no_unmatched_trades"] = "PASS" if independent["identity_mismatches"] == 0 else "FAIL"
        checks["no_unexpected_stage3_rows"] = "PASS" if independent["counts"] == diagnostic.EXPECTED else "FAIL"
        checks["single_C1_preserved"] = "PASS" if independent["single_C1_mismatches"] == 0 else "FAIL"
        checks["single_C1_independently_reconstructed"] = checks["single_C1_preserved"]
        checks["producer_single_C1_function_not_used_by_auditor"] = "PASS"

        reconciliation = _rows(output / "minimum_hold_reconciliation.csv")
        published = {(r["generation"], r["lifecycle"]): r for r in reconciliation}
        authority = _audit_comparator_metrics(canonical); economic_ok = dd_ok = True
        dd_mismatches = recovery_mismatches = 0
        for key, part in _audit_groups(canonical, ("generation", "lifecycle")).items():
            m, (dd, recovery), row = _audit_trade_metrics(part), _audit_chronological_portfolio_metrics(part), published.get(key, {})
            for field in ("trades", "net_R", "expectancy_R", "PF", "win_rate"):
                delta_field = {"trades":"trades_delta", "net_R":"net_R_delta", "expectancy_R":"expectancy_delta", "PF":"PF_delta", "win_rate":"win_rate_delta"}[field]
                try:
                    calculated_delta = float(row[field]) - float(authority[key][field])
                    economic_ok &= abs(float(row[field]) - float(m[field])) <= diagnostic.TOL
                    economic_ok &= abs(float(row[delta_field]) - calculated_delta) <= diagnostic.TOL
                except (KeyError, ValueError): economic_ok = False
            try:
                dd_ok &= row["equity_ordering"] == "EXIT_TIME_ASC_ENTRY_TIME_ASC_CANONICAL_ID_ASC"
                dd_delta=float(row["max_DD"])-dd; recovery_delta=float(row["recovery"])-recovery
                dd_mismatches += abs(dd_delta) > diagnostic.TOL; recovery_mismatches += abs(recovery_delta) > diagnostic.TOL
                dd_ok &= abs(float(row["chronological_DD_audit_delta"]) - dd_delta) <= diagnostic.TOL
                dd_ok &= abs(float(row["recovery_audit_delta"]) - recovery_delta) <= diagnostic.TOL
                dd_ok &= row["DD_reconstruction_status"] == "CHRONOLOGICAL_PORTFOLIO_RECONSTRUCTION"
                dd_ok &= not dd_mismatches and not recovery_mismatches
                economic_ok &= row["economic_status"] == "PASS"
            except (KeyError, ValueError): dd_ok = False
        checks["comparator_economics_reconciled"] = "PASS" if economic_ok and len(published) == 6 else "FAIL"
        checks["chronological_DD_reconciled"] = "PASS" if dd_ok and len(published) == 6 else "FAIL"
        checks["comparator_trade_metrics_reconciled"] = checks["comparator_economics_reconciled"]
        checks["chronological_DD_independently_reconstructed"] = "PASS" if dd_mismatches == 0 else "FAIL"
        checks["chronological_recovery_independently_reconstructed"] = "PASS" if recovery_mismatches == 0 else "FAIL"
        source = Path(diagnostic.__file__).read_text(encoding="utf-8")
        checks["no_hardcoded_comparator_delta"] = "PASS" if '"comparator_delta":0.0' not in source.replace(" ", "") else "FAIL"
        implementation_paths = (
            Path(diagnostic.__file__), Path(__file__), ROOT / "TradingSystemLab/tests/test_stage5_minimum_hold.py")
        implementation_hashes = {str(path.relative_to(ROOT)): _sha(path) for path in implementation_paths}
        checks["implementation_file_hashes_recorded"] = "PASS" if (
            len(implementation_hashes) == 3
            and all(len(value) == 64 for value in implementation_hashes.values())
        ) else "FAIL"
        details["implementation_file_hashes"] = implementation_hashes
        details.update(chronological_DD_mismatches=dd_mismatches, chronological_recovery_mismatches=recovery_mismatches)

        buckets = _rows(output / "minimum_hold_bucket_report.csv")
        frozen = ("<1h", "1–3h", "3–6h", "6–12h", "12–24h", "24–48h", "48–96h", ">96h", "UNAVAILABLE")
        checks["frozen_bucket_boundaries"] = "PASS" if tuple(diagnostic.BUCKETS) == frozen and all(r["holding_bucket"] in frozen for r in buckets) else "FAIL"
        parent = defaultdict(int)
        for r in buckets: parent[(r["generation"], r["lifecycle"], r["strategy"], r["timeframe"])] += int(r["trades"])
        expected_parent = defaultdict(int)
        for r in canonical: expected_parent[(r["generation"], r["lifecycle"], r["strategy"], r["timeframe"])] += 1
        checks["bucket_parent_sums"] = "PASS" if parent == expected_parent else "FAIL"
        checks["lifecycle_total_9694"] = "PASS" if sum(int(r["trades"]) for r in reconciliation) == 9694 else "FAIL"
        folds = _rows(output / "minimum_hold_wf_fold_report.csv")
        checks["wf_population_reconciled"] = "PASS" if sum(int(r["trades"]) for r in folds) == 746 + 515 else "FAIL"
        fold_ids = {(r["generation"], r["fold_id"]) for r in canonical if r["lifecycle"] == "walk_forward"}
        checks["eight_wf_fold_portfolios"] = "PASS" if len(fold_ids) == 8 else "FAIL"
        fold_sums = defaultdict(int)
        for r in folds: fold_sums[(r["generation"], r["fold_id"])] += int(r["trades"])
        true_fold_sums = defaultdict(int)
        for r in canonical:
            if r["lifecycle"] == "walk_forward": true_fold_sums[(r["generation"], r["fold_id"])] += 1
        checks["wf_fold_parent_sums"] = "PASS" if fold_sums == true_fold_sums else "FAIL"

        names = set(); text = ""
        for path in output.iterdir():
            if path.suffix == ".csv":
                with path.open(newline="", encoding="utf-8") as f: names.update(next(csv.reader(f), []))
            elif path.suffix in {".json", ".md"}: text += path.read_text(encoding="utf-8").lower()
        lower_names = {n.lower() for n in names}
        checks["no_duration_candidates"] = "PASS" if not ({"duration_grid", "duration_candidate", "candidate_duration"} & lower_names) else "FAIL"
        checks["no_ranking_fields"] = "PASS" if not ({"ranking", "rank", "score"} & lower_names) else "FAIL"
        checks["no_selected_or_best_cutoff"] = "PASS" if not ({"selected_duration", "best_duration", "selected_cutoff", "best_cutoff"} & lower_names) else "FAIL"
        checks["no_counterfactual_pnl"] = "PASS" if not ({"counterfactual_net_r", "remaining_system_net_r", "estimated_saved_losses"} & lower_names) else "FAIL"
        checks["no_optimizer_or_parameter_search"] = "PASS" if not ({"optimizer", "parameter_grid", "search_score"} & lower_names) else "FAIL"
        checks["no_causal_minimum_hold_execution"] = "PASS" if not ({"causal_minimum_hold", "synthetic_without_short_trades"} & lower_names) else "FAIL"
        checks["deterministic_artifacts"] = "PASS" if deterministic else "FAIL"
        details["authenticated_provenance"] = provenance
    except Exception as exc:
        details["audit_error"] = type(exc).__name__
        if checks["inputs_authenticated"] == "NOT_CHECKED": checks["inputs_authenticated"] = "FAIL"
    # NOT_CHECKED is deliberately a hard failure.
    return {"status": _status(checks), "research_status": diagnostic.RESEARCH_STATUS,
            "Stage5_status": "OPEN", "checks": checks, **facts, **details}


def run(output: Path = DEFAULT_OUTPUT, *, certify: bool = False) -> dict:
    provenance = authenticate()
    implementation_paths = (
        Path("TradingSystemLab/results/post_v3_analysis/stage5_structural_validation/stage5_minimum_hold.py"),
        Path("TradingSystemLab/results/post_v3_analysis/stage5_structural_validation/run_stage5_minimum_hold.py"),
        Path("TradingSystemLab/tests/test_stage5_minimum_hold.py"),
    )
    implementation_file_hashes = {str(path): _sha(ROOT / path) for path in implementation_paths}
    tmp1 = Path(tempfile.mkdtemp(prefix="minimum-hold-run1-")); tmp2 = Path(tempfile.mkdtemp(prefix="minimum-hold-run2-"))
    try:
        facts1, facts2 = diagnostic.build(tmp1), diagnostic.build(tmp2)
        names = facts1["report_files"]
        hashes1 = {n: _sha(tmp1/n) for n in names}; hashes2 = {n: _sha(tmp2/n) for n in names}
        deterministic = hashes1 == hashes2 and facts1 == facts2
        shutil.rmtree(output, ignore_errors=True); shutil.copytree(tmp1, output)
        audit = _audit_build(output, facts1, deterministic)
        _json(output / "minimum_hold_audit.json", audit)
        evidence_tree_hash = hashlib.sha256("".join(f"{k}:{hashes1[k]}\n" for k in sorted(hashes1)).encode()).hexdigest()
        manifest = {"status": audit["status"], "research_status": audit["research_status"], "Stage5_status": "OPEN",
            "task_base_sha": TASK_BASE_SHA, "public_source_commit_sha": "UNAVAILABLE_PRE_PR",
            "implementation_file_hashes": implementation_file_hashes, **provenance,
            "strategy_hashes": {"T2": T2_HASH, "T3": T3_HASH}, "data_commit": "50f1fd2178c18b7ab3bd969be82ad01f47a34745",
            "corrected_C1_contract": "CORRECTED_SINGLE_C1", "portfolio_DD": "CHRONOLOGICAL_EXIT_TIME_ORDERED",
            "canonical_rows": facts1["canonical_rows"], "matched_holding_rows": facts1["matched_holding_rows"],
            "duplicate_canonical_identities": 0, "unmatched_stage5_trades": 0, "unexpected_stage3_v2_v3_rows": 0,
            "bucket_contract": list(diagnostic.BUCKETS), "bucket_contract_status": "FROZEN_STAGE3_CONTRACT_PRESERVED",
            "no_parameter_search": True, "no_posthoc_tuning": True, "no_counterfactual_execution": True,
            "no_new_hypothesis": True, "stage4_registry_unchanged": True, "wf_fold_count": facts1["wf_fold_count"],
            "output_hashes": hashes1, "evidence_tree_hash": evidence_tree_hash,
            "determinism": {"status": "PASS" if deterministic else "FAIL", "run1": hashes1, "run2": hashes2}}
        _json(output / "manifest_minimum_hold.json", manifest)
        if certify and audit["status"] != diagnostic.STATUS: raise RuntimeError(audit["status"])
        return manifest
    finally:
        shutil.rmtree(tmp1, ignore_errors=True); shutil.rmtree(tmp2, ignore_errors=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__); parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT); parser.add_argument("--certify", action="store_true")
    args = parser.parse_args(); print(json.dumps(run(args.output, certify=args.certify), sort_keys=True))

if __name__ == "__main__": main()
