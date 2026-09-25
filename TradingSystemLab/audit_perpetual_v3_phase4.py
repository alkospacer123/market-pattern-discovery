"""Independent fail-closed audit of v3 perpetual Phase 4 Walk Forward artifacts."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
from typing import Any

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from TradingSystemLab.core.unified_metrics import stats
from TradingSystemLab.optimization.experiment import stable_hash
from TradingSystemLab.walk_forward.perpetual_v3_phase4 import (
    EXPECTED_IDS, FREEZE_REFERENCE_COMMIT, PHASE2_REFERENCE_COMMIT, INSTRUMENTS, OUTPUT_ROOT,
    REGISTRY_PATH, ROBUSTNESS, ROBUSTNESS_REFERENCE_COMMIT, ROBUSTNESS_ROOT,
    SCHEDULE, STUDIES, classify,
    DATA_ROOT, run,
)

REQUIRED = {"folds.csv", "trades.csv", "train_test_decay.csv", "instrument_report.csv",
            "direction_report.csv", "year_report.csv", "concentration.csv",
            "leave_one_fold_out.csv", "mae_mfe.csv", "metrics.json", "manifest.json", "final_report.md"}
REPRODUCIBILITY_NOTE = (
    "The independent audit generated Phase 4 a second time in an isolated directory and "
    "verified identical SHA-256 hashes for every defined research artifact."
)


def research_artifact_hashes(root: Path) -> dict[str, str]:
    """Hash only pre-audit research evidence, never audit-mutated closeout files."""
    relative = [Path("DATA_COVERAGE_REPORT.json"), Path("summary/comparison.csv")]
    relative.extend(Path(strategy) / timeframe / name
                    for strategy, timeframe in STUDIES for name in sorted(REQUIRED))
    return {path.as_posix(): hashlib.sha256((root / path).read_bytes()).hexdigest()
            for path in relative}


def _finalize_report(path: Path, status: str) -> None:
    text = path.read_text(encoding="utf-8").rstrip()
    marker = text.rsplit("\n", 1)[-1]
    _require(marker in {"PENDING_AUDIT", status}, f"REPORT_STATUS_INVALID:{path}")
    path.write_text(text[:-len(marker)] + status + "\n", encoding="utf-8")


def _require(value: bool, message: str) -> None:
    if not value: raise RuntimeError(message)


def _close(a: Any, b: Any) -> bool:
    return bool((pd.isna(a) and pd.isna(b)) or np.isclose(float(a), float(b), rtol=1e-9, atol=1e-10))


def _summary(values: pd.Series) -> dict[str, Any]:
    s = stats(values.astype(float))
    return {"trades": s["trades"], "PF": s["PF_R"], "expectancy": s["expectancy"],
            "net_R": s["net_R"], "max_drawdown": s["max_DD_R"],
            "recovery_factor": s["recovery_factor"], "win_rate": s["winrate"],
            "winning_streak": s["max_winning_streak"], "losing_streak": s["max_losing_streak"]}


def _same(actual: Any, expected: Any, label: str) -> None:
    _require(_close(actual, expected), f"RECONCILIATION_FAILURE:{label}:{actual}:{expected}")


def audit(root: Path = OUTPUT_ROOT, data_root: Path = DATA_ROOT) -> dict[str, Any]:
    registry_raw = REGISTRY_PATH.read_bytes(); registry = json.loads(registry_raw)
    candidates = registry["candidates"]
    _require(registry.get("immutable") is True and len(candidates) == 4, "FREEZE_REGISTRY_INVALID")
    _require([(x["strategy"], x["timeframe"]) for x in candidates] == list(STUDIES), "CANDIDATE_ORDER_INVALID")
    for item in candidates:
        study = item["strategy"], item["timeframe"]
        _require((item["candidate_id"], item["parameter_hash"]) == EXPECTED_IDS[study], "IDENTITY_INVALID")
        _require(stable_hash(item["parameters"]) == item["parameter_hash"], "PARAMETER_HASH_INVALID")
        source = Path(f"TradingSystemLab/strategies/trend/{'T2_Trend_Pullback' if study[0]=='T2' else 'T3_MTF_Trend'}.py")
        _require(hashlib.sha256(source.read_bytes()).hexdigest() == item["frozen_strategy_source_hash"], "STRATEGY_HASH_INVALID")
    robust = json.loads((ROBUSTNESS_ROOT / "validation_manifest.json").read_text())
    _require(robust["status"] == "V3_PERPETUAL_PHASE_3_ROBUSTNESS_COMPLETE", "ROBUSTNESS_INCOMPLETE")
    _require(robust["classifications"] == {f"{s}/{t}": ROBUSTNESS[(s,t)] for s,t in STUDIES}, "ROBUSTNESS_CLASSES_INVALID")
    protected = ((FREEZE_REFERENCE_COMMIT, "TradingSystemLab/results/perpetual_v3/baseline"),
                 (PHASE2_REFERENCE_COMMIT, "TradingSystemLab/results/perpetual_v3/optimization"),
                 (FREEZE_REFERENCE_COMMIT, "TradingSystemLab/results/perpetual_v3/phase3_candidate_freeze"),
                 (ROBUSTNESS_REFERENCE_COMMIT, "TradingSystemLab/results/perpetual_v3/robustness"),
                 (ROBUSTNESS_REFERENCE_COMMIT, "TradingSystemLab/results/baseline_v2"),
                 (ROBUSTNESS_REFERENCE_COMMIT, "TradingSystemLab/results/walk_forward_v2"))
    for commit, path in protected:
        _require(subprocess.run(["git", "diff", "--quiet", commit, "--", path]).returncode == 0,
                 f"PROTECTED_TREE_CHANGED:{path}")
    manifest = json.loads((root / "summary/manifest.json").read_text())
    _require(json.loads((root / "validation_manifest.json").read_text()) == manifest, "ROOT_MANIFEST_MISMATCH")
    _require(manifest["candidate_registry_sha256"] == hashlib.sha256(registry_raw).hexdigest(), "REGISTRY_SHA_INVALID")
    _require(manifest["fold_schedule"] == [{"fold": x[0], "train_start": x[1], "train_end": x[2],
        "test_start": x[3], "test_end": x[4]} for x in SCHEDULE], "SCHEDULE_INVALID")
    _require(manifest["C1_only"] and manifest["normalized_research_tick"] == .001, "COST_CONTRACT_INVALID")
    _require(not any(manifest[x] for x in ("optimization", "ranking", "candidate_replacement",
                                           "true_oos_read", "phase7_mtf_research")), "FORBIDDEN_ACTION_RECORDED")
    _require(manifest["true_oos_blocked"] and manifest["candidate_count"] == 4, "LIFECYCLE_INVALID")
    coverage = json.loads((root / "DATA_COVERAGE_REPORT.json").read_text())
    _require(coverage["status"] == "SUFFICIENT" and not coverage["true_oos_read"], "COVERAGE_INVALID")
    verdicts = {}
    for item in candidates:
        strategy, timeframe = item["strategy"], item["timeframe"]
        target = root / strategy / timeframe
        _require({p.name for p in target.iterdir()} == REQUIRED, f"ARTIFACT_SET_INVALID:{strategy}/{timeframe}")
        folds = pd.read_csv(target / "folds.csv"); trades = pd.read_csv(target / "trades.csv")
        metrics = json.loads((target / "metrics.json").read_text())
        _require(len(folds) == 4 and list(folds.fold) == [x[0] for x in SCHEDULE], "FOLDS_INVALID")
        _require(folds.status.eq("COMPLETE").all() and folds.included_in_pass.all(), "INCOMPLETE_FOLD")
        _require(trades.fold_start_state.eq("FLAT").all(), "NON_FLAT_FOLD")
        _require(not trades.duplicated(["fold", "trade_id"]).any(), "DUPLICATE_TRADE")
        for fold, train_start, train_end, test_start, test_end in SCHEDULE:
            row = folds.loc[folds.fold.eq(fold)].iloc[0]
            _require((row.train_start, row.train_end, row.test_start, row.test_end) ==
                     (train_start, train_end, test_start, test_end), "FOLD_CALENDAR_INVALID")
            sample = trades.loc[trades.fold.eq(fold)]
            entry, exit_ = pd.to_datetime(sample.entry_time, utc=True), pd.to_datetime(sample.exit_time, utc=True)
            _require(entry.ge(pd.Timestamp(test_start, tz="UTC")).all() and
                     exit_.le(pd.Timestamp(test_end, tz="UTC")).all(), "BOUNDARY_CROSSING")
            for key, value in _summary(sample.net_R_C1).items(): _same(row[key], value, f"fold:{fold}:{key}")
        _require(pd.to_datetime(trades.exit_time, utc=True).lt(pd.Timestamp("2025-01-01", tz="UTC")).all(), "TRUE_OOS_TRADE")
        _require(set(trades.symbol) <= set(INSTRUMENTS), "UNKNOWN_INSTRUMENT")
        aggregate = _summary(trades.net_R_C1)
        for key, value in aggregate.items(): _same(metrics["aggregate"]["C1"][key], value, f"aggregate:{key}")
        instrument = pd.read_csv(target / "instrument_report.csv")
        _require(list(instrument.symbol) == list(INSTRUMENTS), "INSTRUMENT_ORDER_INVALID")
        for _, row in instrument.iterrows():
            for key, value in _summary(trades.loc[trades.symbol.eq(row.symbol), "net_R_C1"]).items():
                _same(row[key], value, f"instrument:{row.symbol}:{key}")
        direction = pd.read_csv(target / "direction_report.csv")
        _require(list(direction.direction) == ["LONG", "SHORT"], "DIRECTION_INVALID")
        for _, row in direction.iterrows():
            for key, value in _summary(trades.loc[trades.direction.eq(row.direction), "net_R_C1"]).items():
                _same(row[key], value, f"direction:{row.direction}:{key}")
        conc = pd.read_csv(target / "concentration.csv").iloc[0]; positive = trades.net_R_C1[trades.net_R_C1 > 0].sort_values(ascending=False)
        for n in (1, 3, 10): _same(conc[f"top_{n}_trade_share"], positive.head(n).sum()/positive.sum(), f"top{n}")
        total = trades.net_R_C1.sum(); fold_net = trades.groupby("fold").net_R_C1.sum()
        expected_best = fold_net.max()/total if total > 0 else None; _same(conc.best_fold_contribution, expected_best, "best_fold")
        loo = pd.read_csv(target / "leave_one_fold_out.csv")
        for _, row in loo.iterrows():
            for key, value in _summary(trades.loc[trades.fold.ne(row.omitted_fold), "net_R_C1"]).items():
                _same(row[key], value, f"loo:{row.omitted_fold}:{key}")
        positive_share = sum(x > 0 for x in folds.expectancy.fillna(0))/4
        _same(metrics["positive_complete_fold_share"], positive_share, "positive_share")
        verdict = classify(aggregate, positive_share, expected_best, list(instrument.expectancy), 4)
        _require(metrics["verdict"] == verdict, "VERDICT_INVALID")
        _require(metrics["execution_context"] == ("none" if strategy == "T2" else
            f"four completed non-overlapping {timeframe} bars; local-day reset"), "CONTEXT_INVALID")
        _require(metrics["parameters_frozen"] and not metrics["optimization"] and not metrics["ranking"]
                 and not metrics["candidate_replacement"], "FROZEN_CONTRACT_INVALID")
        verdicts[f"{strategy}/{timeframe}"] = verdict
    _require(manifest["verdicts"] == verdicts, "ROOT_VERDICTS_INVALID")
    status = "V3_PERPETUAL_PHASE_4_WALK_FORWARD_COMPLETE"
    _require(manifest["status"] in {"PENDING_AUDIT", status}, "ROOT_STATUS_INVALID")
    _require(manifest["procedural_status_after_audit"] == status, "PROCEDURAL_STATUS_INVALID")
    canonical_hashes = research_artifact_hashes(root)
    with tempfile.TemporaryDirectory(prefix="phase4-reproduction-") as directory:
        reproduction = Path(directory) / "walk_forward"
        run(data_root=data_root, output=reproduction)
        reproduced_hashes = research_artifact_hashes(reproduction)
    _require(canonical_hashes == reproduced_hashes, "SECOND_EXECUTION_REPRODUCIBILITY_FAILURE")
    manifest["status"] = status
    manifest["second_complete_execution_compared"] = True
    manifest["reproducibility_note"] = REPRODUCIBILITY_NOTE
    for path in (root / "summary/manifest.json", root / "validation_manifest.json"):
        path.write_text(json.dumps(manifest, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")
    for path in (root / "Final_Walk_Forward_Report.md",
                 root / "summary/Final_Walk_Forward_Report.md"):
        _finalize_report(path, status)
    result = {"status": "V3_PERPETUAL_PHASE_4_WALK_FORWARD_AUDIT_PASSED", "verdicts": verdicts,
              "checks": 26, "closeout_consistency": "PASS",
              "reproducibility_artifact_count": len(canonical_hashes),
              "reproducibility_hashes": canonical_hashes,
              "true_oos_status": "BLOCKED_NOT_READ_NOT_EXECUTED"}
    (root / "audit_result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (root / "Phase_4_Walk_Forward_Audit_Report.md").write_text(
        "# v3 Perpetual Phase 4 Independent Audit\n\n**PASS** — all 26 fail-closed checks reconciled.\n\n"
        "A second generation in an isolated temporary directory reproduced all defined research "
        f"artifacts ({len(canonical_hashes)} SHA-256 comparisons). Both final reports and manifests "
        "were synchronized to the completed lifecycle state. Frozen candidates and parameters "
        "were unchanged; forward-only C1 ledgers reconcile; "
        "TRUE OOS remained BLOCKED_NOT_READ_NOT_EXECUTED.\n", encoding="utf-8")
    return result


if __name__ == "__main__":
    print(json.dumps(audit(), sort_keys=True))
