"""Independent, fail-closed audit of the Stage 5 canonical comparator.

This file deliberately duplicates the small amount of orchestration needed by
the audit.  In particular, it does not import any Stage 5 producer module.  The
only executable objects shared with the producer are the frozen v2/v3 runners
which are the objects under audit.
"""
from __future__ import annotations

import ast
import copy
import csv
import hashlib
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import pandas as pd

from TradingSystemLab import baseline_v2, perpetual_v3_baseline
from TradingSystemLab.true_oos.phase5_v2 import run as run_v2_oos
from TradingSystemLab.true_oos.perpetual_v3_phase5 import run as run_v3_oos
from TradingSystemLab.walk_forward import phase4_v2 as wf_v2
from TradingSystemLab.walk_forward import perpetual_v3_phase4 as wf_v3

RESULTS = ROOT / "TradingSystemLab/results"
STAGE4 = HERE.parent / "stage4_structural_hypotheses"
RESULT_FILE = HERE / "canonical_comparator_audit_result.json"
DATA_COMMIT = "50f1fd2178c18b7ab3bd969be82ad01f47a34745"
TOLERANCE = 1e-9
TICK = "0.001"
EXPECTED_HASHES = {
    "T2": "376df085cfda85eefccb31343aad40ed4fbb1078f1314496472a3a4ac9507774",
    "T3": "840dd3b2cda43fa00259445cd0a22ace6d82e677f4c793028ccc8126f9ad9a8c",
}
STAGE4_HASHES = {
    "manifest_stage4.json": "00dcb2141602dd6813f194a57b8539aca79ce807de98a6c2f85093c664741abf",
    "audit_stage4_result.json": "7a764cd15975835d7469d0cae58634fd7751a54db79e1bf62aec59f5d8593863",
    "structural_hypothesis_registry.csv": "584a7c89dcb9e8985b4a0a9c5e432264b2c549675e2d45df9402cc12fb699fc8",
    "structural_hypothesis_evidence.csv": "c25f9d7f8fe551a8ebdf6e7d044f3468c0f6cae7a2b067af64dc9f22f90ce30f",
    "structural_hypothesis_validation_contract.csv": "5d5da406fdbd34aaaee005f4a9736ef7b8b4c56873919dfe2e7ac21f03bc00ac",
}
INSTRUMENTS = {
    "v2_quarterly": tuple(baseline_v2.INSTRUMENTS),
    "v3_perpetual": tuple(perpetual_v3_baseline.INSTRUMENTS),
}
TOTALS = {
    ("v2_quarterly", "baseline"): 4449,
    ("v2_quarterly", "walk_forward"): 746,
    ("v2_quarterly", "historical_true_oos"): 1759,
    ("v3_perpetual", "baseline"): 1124,
    ("v3_perpetual", "walk_forward"): 515,
    ("v3_perpetual", "historical_true_oos"): 1101,
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def validate_stage4(audit: dict[str, Any], manifest: dict[str, Any],
                    actual: dict[str, str]) -> None:
    """Validate independently supplied Stage 4 evidence (also used by mutations)."""
    if actual != STAGE4_HASHES:
        raise RuntimeError("STAGE4_FROZEN_HASH")
    if audit["status"] != "POST_V3_STAGE_4_STRUCTURAL_HYPOTHESIS_SET_AUDIT_PASSED":
        raise RuntimeError("STAGE4_AUDIT_STATUS")
    if audit["stage4_status"] != "POST_V3_STAGE_4_STRUCTURAL_HYPOTHESIS_SET_CLOSED":
        raise RuntimeError("STAGE4_CLOSED_STATUS")
    if manifest["audit_status"] != audit["status"] or manifest["final_status"] != audit["stage4_status"]:
        raise RuntimeError("STAGE4_STATUS_DISAGREEMENT")


def authenticate_stage4() -> dict[str, str]:
    """Authenticate Stage 4 directly, never through the Stage 5 manifest."""
    audit_path = STAGE4 / "audit_stage4_result.json"
    audit = json.loads(audit_path.read_text(encoding="utf-8"))
    manifest = json.loads((STAGE4 / "manifest_stage4.json").read_text(encoding="utf-8"))
    actual = {name: sha256(STAGE4 / name) for name in STAGE4_HASHES}
    validate_stage4(audit, manifest, actual)
    return actual


def resolve_data_root() -> Path:
    """Audit-owned implementation of the documented data-root precedence."""
    choices: list[Path] = []
    if os.environ.get("MARKET_PATTERN_DATA_ROOT"):
        choices.append(Path(os.environ["MARKET_PATTERN_DATA_ROOT"]))
    choices.extend((ROOT.parent / "market-pattern-data", Path("/workspace/market-pattern-data")))
    for candidate in choices:
        if candidate.is_dir():
            return candidate.resolve()
    raise RuntimeError("MARKET_DATA_ROOT_NOT_FOUND")


def validate_data_repo(root: Path, head: str) -> None:
    if head != DATA_COMMIT:
        raise RuntimeError("MARKET_DATA_COMMIT")
    for directory in ("futures_quarterly", "forever"):
        if not (root / directory).is_dir():
            raise RuntimeError(f"MARKET_DATA_DIRECTORY:{directory}")


def authenticate_data_repo(root: Path) -> str:
    head = subprocess.run(
        ["git", "-C", str(root), "rev-parse", "HEAD"], check=True,
        text=True, capture_output=True,
    ).stdout.strip()
    validate_data_repo(root, head)
    return head


def _candidates(generation: str) -> dict[tuple[str, str], dict[str, Any]]:
    path = RESULTS / ("phase3_candidate_freeze/candidate_registry.json" if generation == "v2_quarterly"
                      else "perpetual_v3/phase3_candidate_freeze/candidate_registry.json")
    return {(x["strategy"], x["timeframe"]): x for x in json.loads(path.read_text())["candidates"]}


def reconstruct_registry(data_root: Path) -> list[dict[str, str]]:
    """Reconstruct every registry field from canonical, pre-Stage-5 evidence."""
    answer: list[dict[str, str]] = []
    specs = (
        ("v2_quarterly", "futures_quarterly", "2020-01-01", "2024-12-31 23:59:59", wf_v2.SCHEDULE),
        ("v3_perpetual", "forever", "2023-01-01", "2024-12-31 23:59:59", wf_v3.SCHEDULE),
    )
    for generation, universe, dev_start, dev_end, schedule in specs:
        candidates = _candidates(generation)
        for lifecycle in ("baseline", "walk_forward", "historical_true_oos"):
            folds = schedule if lifecycle == "walk_forward" else (("", "", "", dev_start, dev_end),)
            for fold, train_start, train_end, start, end in folds:
                if lifecycle == "historical_true_oos":
                    start, end = "2025-01-01", "2026-09-16 23:59:59"
                for strategy in ("T2", "T3"):
                    for timeframe in ("M30", "H1"):
                        candidate = candidates[(strategy, timeframe)]
                        identity = (f"{strategy}_{timeframe}_baseline_defaults" if lifecycle == "baseline"
                                    else candidate["candidate_id"])
                        parameter_hash = (baseline_v2.stable_hash(baseline_v2.BASELINE_PARAMETERS[strategy])
                                          if lifecycle == "baseline" else candidate["parameter_hash"])
                        for instrument in INSTRUMENTS[generation]:
                            first, last = start, end
                            if lifecycle == "baseline":
                                path = (RESULTS / "baseline_v2" / strategy / instrument / timeframe / "manifest.json"
                                        if generation == "v2_quarterly" else RESULTS / "perpetual_v3/baseline" / strategy / timeframe / instrument / "manifest.json")
                                baseline = json.loads(path.read_text())
                                first = baseline.get("actual_first_available_close", baseline.get("actual_first_bar"))
                                last = baseline.get("actual_last_development_close", baseline.get("actual_last_bar"))
                            elif lifecycle == "historical_true_oos":
                                path = RESULTS / ("true_oos_v2/summary/manifest.json" if generation == "v2_quarterly"
                                                  else "perpetual_v3/true_oos/summary/manifest.json")
                                coverage = json.loads(path.read_text())["coverage"][timeframe][instrument]
                                first, last = coverage["first_admitted_oos_close"], coverage["last_admitted_oos_close"]
                            relative = f"{universe}/{instrument}/{instrument}_{timeframe}.csv"
                            source = data_root / relative
                            if not source.is_file():
                                raise RuntimeError(f"SOURCE_DATA_MISSING:{relative}")
                            answer.append({
                                "generation": generation, "lifecycle": lifecycle, "fold_id": fold,
                                "strategy": strategy, "timeframe": timeframe, "instrument": instrument,
                                "start_timestamp": first, "end_timestamp": last,
                                "train_start_timestamp": train_start, "train_end_timestamp": train_end,
                                "candidate_config_identity": identity,
                                "strategy_parameter_hash": parameter_hash,
                                "source_market_data_identity": f"{DATA_COMMIT}:{relative}:{sha256(source)}",
                                "cost_contract": "C1", "tick_size": TICK, "cold_start": "true",
                                "evidence_label": "RETROSPECTIVE_CAUSAL_VALIDATION",
                            })
    return answer


def authenticate_registry(data_root: Path) -> tuple[list[dict[str, str]], dict[str, str]]:
    committed = read_csv(HERE / "canonical_lifecycle_registry.csv")
    expected = reconstruct_registry(data_root)
    validate_registry(committed, expected)
    identities = validate_source_identities(expected, data_root)
    return expected, identities


def validate_registry(committed: list[dict[str, str]], expected: list[dict[str, str]]) -> None:
    """Require an exact registry; inputs make the proof surface mutation-testable."""
    key = lambda row: tuple(row[name] for name in row)
    if sorted(committed, key=key) != sorted(expected, key=key):
        raise RuntimeError("LIFECYCLE_REGISTRY_NOT_EXACT")


def validate_source_identities(rows: list[dict[str, str]], data_root: Path,
                               hash_fn: Any = sha256) -> dict[str, str]:
    identities: dict[str, str] = {}
    for row in rows:
        commit, relative, digest = row["source_market_data_identity"].split(":", 2)
        if commit != DATA_COMMIT or digest != hash_fn(data_root / relative):
            raise RuntimeError("SOURCE_DATA_IDENTITY")
        identities[relative] = digest
    return dict(sorted(identities.items()))


def _run_wf(module: Any, generation: str, data_root: Path, output: Path) -> None:
    """Fresh-state, audit-owned WF01--WF04 orchestration."""
    candidates = _candidates(generation)
    instruments = INSTRUMENTS[generation]
    loader = baseline_v2.load_development if generation == "v2_quarterly" else perpetual_v3_baseline.load_development
    for strategy, timeframe in (("T2", "M30"), ("T2", "H1"), ("T3", "M30"), ("T3", "H1")):
        frames = {instrument: loader(data_root, instrument, timeframe)[0] for instrument in instruments}
        pieces = []
        for fold, _train_start, _train_end, start, end in module.SCHEDULE:
            trades = module._execute(strategy, candidates[(strategy, timeframe)]["parameters"], frames, start, end)
            trades["fold"], trades["fold_start_state"] = fold, "FLAT"
            pieces.append(trades)
        target = output / strategy / timeframe
        target.mkdir(parents=True)
        pd.concat(pieces, ignore_index=True).sort_values(
            ["exit_time", "symbol", "trade_id"], kind="mergesort"
        ).to_csv(target / "trades.csv", index=False, lineterminator="\n", float_format="%.12g", na_rep="")


def execute_independently(data_root: Path, output: Path) -> None:
    """Invoke all six frozen lifecycle runners without Stage 5 producer code."""
    baseline_v2.run(data_root / "futures_quarterly", output / "baseline_v2")
    _run_wf(wf_v2, "v2_quarterly", data_root / "futures_quarterly", output / "walk_forward_v2")
    run_v2_oos(data_root / "futures_quarterly", output / "true_oos_v2")
    perpetual_v3_baseline.run(data_root / "forever", output / "perpetual_v3/baseline")
    _run_wf(wf_v3, "v3_perpetual", data_root / "forever", output / "perpetual_v3/walk_forward")
    run_v3_oos(data_root / "forever", output / "perpetual_v3/true_oos")


def _ledger(root: Path, generation: str, lifecycle: str, strategy: str, timeframe: str) -> pd.DataFrame:
    if lifecycle == "baseline":
        base = root / ("baseline_v2" if generation == "v2_quarterly" else "perpetual_v3/baseline")
        paths = [(base / strategy / i / timeframe / "trades.csv" if generation == "v2_quarterly"
                  else base / strategy / timeframe / i / "trades.csv") for i in INSTRUMENTS[generation]]
        return pd.concat([pd.read_csv(path) for path in paths], ignore_index=True)
    base = root / (("walk_forward_v2" if lifecycle == "walk_forward" else "true_oos_v2")
                   if generation == "v2_quarterly" else
                   ("perpetual_v3/walk_forward" if lifecycle == "walk_forward" else "perpetual_v3/true_oos"))
    return pd.read_csv(base / strategy / timeframe / "trades.csv")


def _net(frame: pd.DataFrame) -> pd.Series:
    column = "net_R_C1" if "net_R_C1" in frame else "net_R"
    return pd.to_numeric(frame[column], errors="raise").astype(float)


def metrics(frame: pd.DataFrame) -> dict[str, float]:
    values = _net(frame)
    curve = pd.concat([pd.Series([0.0]), values.reset_index(drop=True).cumsum()])
    losses = values[values < 0].sum()
    return {"trades": float(len(values)), "net_R": float(values.sum()),
            "expectancy_R": float(values.mean()) if len(values) else 0.0,
            "PF": float(values[values > 0].sum() / abs(losses)) if losses else 0.0,
            "win_rate": float((values > 0).mean()) if len(values) else 0.0,
            "max_DD": float((curve - curve.cummax()).min())}


TRADE_FIELDS = ("symbol", "direction", "entry_time", "exit_time", "entry_price", "exit_price", "exit_reason")


def validate_trade_frames(reference: pd.DataFrame, observed: pd.DataFrame) -> None:
    """Reject any trade-level difference, including the independently selected C1 R."""
    if len(reference) != len(observed):
        raise RuntimeError("INDEPENDENT_RECONCILIATION")
    for field in TRADE_FIELDS:
        if not reference[field].astype(str).reset_index(drop=True).equals(
                observed[field].astype(str).reset_index(drop=True)):
            raise RuntimeError("INDEPENDENT_RECONCILIATION")
    if (_net(reference).reset_index(drop=True) - _net(observed).reset_index(drop=True)).abs().gt(TOLERANCE).any():
        raise RuntimeError("INDEPENDENT_RECONCILIATION")


def validate_producer_metrics(producer: dict[str, Any], observed: dict[str, float]) -> None:
    """Compare values, deliberately ignoring any producer-authored PASS flag."""
    if int(producer["actual_trades"]) != int(observed["trades"]):
        raise RuntimeError("PRODUCER_AUDITOR_TRADE_COUNT")
    mapping = {"net_R": "actual_net_R", "expectancy_R": "actual_expectancy_R",
               "PF": "actual_PF", "win_rate": "actual_win_rate", "max_DD": "actual_max_DD"}
    if any(abs(float(producer[column]) - observed[name]) > TOLERANCE for name, column in mapping.items()):
        raise RuntimeError("PRODUCER_AUDITOR_METRICS")


def reconcile(actual_root: Path) -> tuple[list[dict[str, Any]], int, float, int]:
    producer = read_csv(HERE / "canonical_comparator_reconciliation.csv")
    producer_index = {(r["generation"], r["lifecycle"], r["fold_id"], r["strategy"], r["timeframe"]): r for r in producer}
    studies, mismatch_count, maximum, rows_total = [], 0, 0.0, 0
    for generation in INSTRUMENTS:
        for lifecycle in ("baseline", "walk_forward", "historical_true_oos"):
            for strategy in ("T2", "T3"):
                for timeframe in ("M30", "H1"):
                    reference = _ledger(RESULTS, generation, lifecycle, strategy, timeframe).reset_index(drop=True)
                    observed = _ledger(actual_root, generation, lifecycle, strategy, timeframe).reset_index(drop=True)
                    rows_total += len(observed)
                    mismatch_count += abs(len(reference) - len(observed))
                    for field in TRADE_FIELDS:
                        mismatch_count += int((reference[field].iloc[:len(observed)].astype(str).reset_index(drop=True)
                                               != observed[field].iloc[:len(reference)].astype(str).reset_index(drop=True)).sum())
                    mismatch_count += int((_net(reference).iloc[:len(observed)].reset_index(drop=True)
                                           - _net(observed).iloc[:len(reference)].reset_index(drop=True)).abs().gt(TOLERANCE).sum())
                    folds = sorted(reference["fold"].unique()) if lifecycle == "walk_forward" else [""]
                    for fold in folds:
                        left = reference[reference["fold"] == fold] if fold else reference
                        right = observed[observed["fold"] == fold] if fold else observed
                        lm, rm = metrics(left), metrics(right)
                        delta = max(abs(lm[name] - rm[name]) for name in lm)
                        maximum = max(maximum, delta)
                        key = (generation, lifecycle, fold, strategy, timeframe)
                        p = producer_index[key]
                        validate_producer_metrics(p, rm)
                        studies.append({"key": key, "metrics": rm})
    totals = {(g, lifecycle): sum(int(s["metrics"]["trades"]) for s in studies
                              if s["key"][0] == g and s["key"][1] == lifecycle)
              for g in INSTRUMENTS for lifecycle in ("baseline", "historical_true_oos")}
    # WF studies have four rows each, so sum directly over fold metrics.
    totals.update({(g, "walk_forward"): sum(int(s["metrics"]["trades"]) for s in studies
                                             if s["key"][0] == g and s["key"][1] == "walk_forward") for g in INSTRUMENTS})
    if totals != TOTALS or rows_total != 9694 or mismatch_count or maximum > TOLERANCE:
        raise RuntimeError("INDEPENDENT_RECONCILIATION")
    return studies, mismatch_count, maximum, rows_total


def verify_t3_causality(loader: str | None = None, strategy: str | None = None) -> dict[str, bool]:
    """Inspect exact called loader/strategy functions and their AST invariants."""
    loader_path = ROOT / "TradingSystemLab/core/data_loader.py"
    strategy_path = ROOT / "TradingSystemLab/strategies/trend/T3_MTF_Trend.py"
    loader = loader_path.read_text() if loader is None else loader
    strategy = strategy_path.read_text() if strategy is None else strategy
    loader_tree, strategy_tree = ast.parse(loader), ast.parse(strategy)
    calls = {n.func.attr for n in ast.walk(loader_tree) if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)}
    completed = "if len(block) != 4" in loader and "continue" in loader
    day_reset = "groupby" in calls and ".index.normalize()" in loader
    shifted = any(isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr == "shift"
                  and n.args and isinstance(n.args[0], ast.Constant) and n.args[0].value == 1 for n in ast.walk(strategy_tree))
    entry_excluded = shifted and "PriorHigh" in strategy and "PriorLow" in strategy
    separate = "h1.copy(), h4.copy()" in strategy and "calculate_indicators(self, h1:" in strategy
    answer = {"separate_causal_context": separate, "four_completed_execution_bars": completed,
              "incomplete_block_exclusion": completed, "local_trading_day_reset": day_reset,
              "donchian_shift_1": shifted, "entry_candle_excluded": entry_excluded}
    if not all(answer.values()):
        raise RuntimeError(f"T3_CAUSALITY:{answer}")
    return answer


MUTATIONS = (
    "wrong Stage 4 registry SHA", "wrong Stage 4 status", "wrong data repo HEAD",
    "wrong source market-data SHA", "altered baseline start", "altered baseline end",
    "altered WF start", "altered WF end", "altered train bound", "swapped WF fold",
    "omitted instrument", "added v1", "C0", "tick 0.01", "T2 source hash",
    "T3 source hash", "incomplete T3 context block", "no local-day reset",
    "unshifted Donchian", "changed entry time", "changed exit time", "changed entry price",
    "changed exit price", "changed exit reason", "changed C1 R", "changed PF",
    "changed max DD", "producer reconciliation falsely says PASS",
    "hypothesis execution true", "Stage 6 work flag",
)


MUTATION_GUARDS = (
        "STAGE4_FROZEN_HASH", "STAGE4_AUDIT_STATUS", "MARKET_DATA_COMMIT", "SOURCE_DATA_IDENTITY",
        "LIFECYCLE_REGISTRY_NOT_EXACT", "LIFECYCLE_REGISTRY_NOT_EXACT", "LIFECYCLE_REGISTRY_NOT_EXACT",
        "LIFECYCLE_REGISTRY_NOT_EXACT", "LIFECYCLE_REGISTRY_NOT_EXACT", "LIFECYCLE_REGISTRY_NOT_EXACT",
        "LIFECYCLE_REGISTRY_NOT_EXACT", "LIFECYCLE_REGISTRY_NOT_EXACT", "LIFECYCLE_REGISTRY_NOT_EXACT",
        "LIFECYCLE_REGISTRY_NOT_EXACT", "STRATEGY_HASH", "STRATEGY_HASH", "T3_CAUSALITY",
        "T3_CAUSALITY", "T3_CAUSALITY", "INDEPENDENT_RECONCILIATION", "INDEPENDENT_RECONCILIATION",
        "INDEPENDENT_RECONCILIATION", "INDEPENDENT_RECONCILIATION", "INDEPENDENT_RECONCILIATION",
        "INDEPENDENT_RECONCILIATION", "PRODUCER_AUDITOR_METRICS", "PRODUCER_AUDITOR_METRICS",
        "PRODUCER_AUDITOR_METRICS", "SCOPE_GUARD", "SCOPE_GUARD",
)


def validate_strategy_hash(strategy: str, digest: str) -> None:
    if digest != EXPECTED_HASHES[strategy]:
        raise RuntimeError("STRATEGY_HASH")


def validate_scope(manifest: dict[str, Any]) -> None:
    if (manifest["hypothesis_execution"] or not manifest["no_stage6"] or
            manifest["C1_contract"]["name"] != "C1" or str(manifest["frozen_tick_size"]) != TICK):
        raise RuntimeError("SCOPE_GUARD")


def _failure_code(action: Any) -> str | None:
    try:
        action()
    except RuntimeError as error:
        return str(error).split(":", 1)[0]
    return None


def mutation_tests(*, disabled_guard: str | None = None) -> dict[str, Any]:
    """Apply each isolated mutation and execute the production validation primitive."""
    assert len(MUTATION_GUARDS) == len(MUTATIONS) == 30
    audit = json.loads((STAGE4 / "audit_stage4_result.json").read_text())
    stage4_manifest = json.loads((STAGE4 / "manifest_stage4.json").read_text())
    actual_hashes = {name: sha256(STAGE4 / name) for name in STAGE4_HASHES}
    registry = read_csv(HERE / "canonical_lifecycle_registry.csv")
    loader = (ROOT / "TradingSystemLab/core/data_loader.py").read_text()
    strategy = (ROOT / "TradingSystemLab/strategies/trend/T3_MTF_Trend.py").read_text()
    manifest = json.loads((HERE / "canonical_comparator_manifest.json").read_text())
    trade = pd.DataFrame([{"symbol": "X", "direction": "long", "entry_time": "2024-01-01",
                           "exit_time": "2024-01-02", "entry_price": 1.0, "exit_price": 2.0,
                           "exit_reason": "target", "net_R_C1": 1.0}])
    observed_metrics = metrics(trade)
    producer = {"actual_trades": 1, "actual_net_R": 1.0, "actual_expectancy_R": 1.0,
                "actual_PF": 0.0, "actual_win_rate": 1.0, "actual_max_DD": 0.0, "status": "PASS"}
    actions: list[tuple[str, Any]] = []

    bad_hashes = dict(actual_hashes); bad_hashes["structural_hypothesis_registry.csv"] = "0" * 64
    actions.append(("stage4_hashes.structural_hypothesis_registry.csv",
                    lambda: validate_stage4(audit, stage4_manifest, bad_hashes)))
    bad_audit = dict(audit); bad_audit["status"] = "WRONG"
    actions.append(("stage4_audit.status", lambda: validate_stage4(bad_audit, stage4_manifest, actual_hashes)))
    temporary = tempfile.TemporaryDirectory(prefix="stage5-mutations-")
    data_root = Path(temporary.name)
    (data_root / "futures_quarterly").mkdir(); (data_root / "forever").mkdir()
    actions.append(("data_repo_commit", lambda: validate_data_repo(data_root, "0" * 40)))
    bad_source = copy.deepcopy(registry); bad_source[0]["source_market_data_identity"] = bad_source[0]["source_market_data_identity"][:-1] + "0"
    canonical_digests = {r["source_market_data_identity"].split(":", 2)[1]:
                         r["source_market_data_identity"].split(":", 2)[2] for r in registry}
    actions.append(("registry.source_market_data_identity", lambda: validate_source_identities(
        bad_source, data_root, lambda path: canonical_digests[str(path.relative_to(data_root))])))

    registry_changes = [
        ("registry.baseline.start_timestamp", lambda rows: rows[0].__setitem__("start_timestamp", "1900-01-01")),
        ("registry.baseline.end_timestamp", lambda rows: rows[0].__setitem__("end_timestamp", "1900-01-02")),
        ("registry.WF.start_timestamp", lambda rows: next(r for r in rows if r["lifecycle"] == "walk_forward").__setitem__("start_timestamp", "1900-01-01")),
        ("registry.WF.end_timestamp", lambda rows: next(r for r in rows if r["lifecycle"] == "walk_forward").__setitem__("end_timestamp", "1900-01-02")),
        ("registry.WF.train_start_timestamp", lambda rows: next(r for r in rows if r["lifecycle"] == "walk_forward").__setitem__("train_start_timestamp", "1900-01-01")),
        ("registry.WF.fold_id", lambda rows: next(r for r in rows if r["fold_id"] == "WF01").__setitem__("fold_id", "WF02")),
        ("registry.instrument", lambda rows: rows.pop()),
        ("registry.generation", lambda rows: rows.append({**rows[0], "generation": "v1"})),
        ("registry.cost_contract", lambda rows: rows[0].__setitem__("cost_contract", "C0")),
        ("registry.tick_size", lambda rows: rows[0].__setitem__("tick_size", "0.01")),
    ]
    for mutated_object, mutate in registry_changes:
        rows = copy.deepcopy(registry); mutate(rows)
        actions.append((mutated_object, lambda rows=rows: validate_registry(rows, registry)))
    actions.extend([
        ("T2.source_hash", lambda: validate_strategy_hash("T2", "0" * 64)),
        ("T3.source_hash", lambda: validate_strategy_hash("T3", "0" * 64)),
        ("T3.loader.incomplete_block", lambda: verify_t3_causality(loader.replace("if len(block) != 4", "if False"), strategy)),
        ("T3.loader.local_day_reset", lambda: verify_t3_causality(loader.replace(".index.normalize()", ".index"), strategy)),
        ("T3.strategy.donchian_shift", lambda: verify_t3_causality(loader, strategy.replace(".shift(1)", ".shift(0)"))),
    ])
    for field, value in (("entry_time", "X"), ("exit_time", "X"), ("entry_price", 9.0),
                         ("exit_price", 9.0), ("exit_reason", "X"), ("net_R_C1", 9.0)):
        changed = trade.copy(); changed.loc[0, field] = value
        actions.append((f"trade.{field}", lambda changed=changed: validate_trade_frames(trade, changed)))
    for field in ("actual_PF", "actual_max_DD"):
        changed = dict(producer); changed[field] = 99.0
        actions.append((f"producer.{field}", lambda changed=changed: validate_producer_metrics(changed, observed_metrics)))
    false_pass = dict(producer); false_pass["actual_net_R"] = 99.0; false_pass["status"] = "PASS"
    actions.append(("producer.false_PASS_with_wrong_value", lambda: validate_producer_metrics(false_pass, observed_metrics)))
    hypothesis = copy.deepcopy(manifest); hypothesis["hypothesis_execution"] = True
    actions.append(("manifest.hypothesis_execution", lambda: validate_scope(hypothesis)))
    stage6 = copy.deepcopy(manifest); stage6["no_stage6"] = False
    actions.append(("manifest.no_stage6", lambda: validate_scope(stage6)))

    results = []
    for number, ((mutated_object, action), name, expected) in enumerate(zip(actions, MUTATIONS, MUTATION_GUARDS), 1):
        actual = None if expected == disabled_guard else _failure_code(action)
        rejected = actual is not None
        results.append({"mutation_id": f"M{number:02d}", "mutation_name": name,
                        "mutated_object": mutated_object, "expected_guard": expected,
                        "actual_guard": actual, "rejected": rejected,
                        "pass": rejected and actual == expected})
    passed = sum(row["pass"] for row in results)
    temporary.cleanup()
    return {"mode": "EXECUTABLE_ADVERSARIAL", "passed": passed, "total": len(results),
            "all_rejected_as_expected": passed == len(results), "results": results}


def authenticate_producer_outputs(manifest: dict[str, Any]) -> None:
    """Authenticate every committed producer artifact after reconciliation."""
    paths = {"registry": "canonical_lifecycle_registry.csv",
             "aggregate": "canonical_comparator_reconciliation.csv",
             "trades": "canonical_comparator_trade_reconciliation.csv",
             "report": "Stage_5_Comparator_Reconstruction_Report.md"}
    actual = {key: sha256(HERE / name) for key, name in paths.items()}
    if manifest.get("output_hashes") != actual:
        raise RuntimeError("PRODUCER_OUTPUT_HASH")
    trade_summary = read_csv(HERE / paths["trades"])
    if any(row["status"] != "PASS" or int(row["total_mismatches"]) for row in trade_summary):
        raise RuntimeError("PRODUCER_TRADE_SUMMARY")
    report = (HERE / paths["report"]).read_text(encoding="utf-8")
    for status in ("STAGE5_CANONICAL_COMPARATOR_RECONCILIATION_PASSED",
                   "STAGE5_COMPARATOR_ONLY_CHECKPOINT_COMPLETE"):
        if status not in report:
            raise RuntimeError("PRODUCER_REPORT_STATUS")


def clean_audit(actual_root: Path) -> dict[str, Any]:
    """Run the complete unmutated canonical audit once."""
    stage4 = authenticate_stage4()
    for strategy, filename in (("T2", "T2_Trend_Pullback.py"), ("T3", "T3_MTF_Trend.py")):
        validate_strategy_hash(strategy, sha256(ROOT / "TradingSystemLab/strategies/trend" / filename))
    data_root = resolve_data_root()
    head = authenticate_data_repo(data_root)
    registry, sources = authenticate_registry(data_root)
    causality = verify_t3_causality()
    manifest = json.loads((HERE / "canonical_comparator_manifest.json").read_text())
    validate_scope(manifest)
    authenticate_producer_outputs(manifest)
    studies, mismatches, maximum, trade_rows = reconcile(actual_root)
    return {
        "status": "STAGE5_CANONICAL_COMPARATOR_INDEPENDENT_AUDIT_PASSED",
        "stage4_authentication": {"status": "PASS", "hashes": stage4},
        "data_repo_authentication": {"status": "PASS", "commit": head},
        "source_data_hashes": sources,
        "lifecycle_registry_exact_match": True,
        "independent_execution": "PASS",
        "studies_reconciled": "24/24",
        "folds_reconciled": "32/32",
        "trade_rows_reconciled": trade_rows,
        "trade_level_mismatches": mismatches,
        "maximum_metric_delta": maximum,
        "producer_vs_auditor_match": True,
        "T3_causality": causality,
        "C1_contract": "C1",
        "frozen_tick": 0.001,
        "structural_hypothesis_execution": False,
        "Stage5_status": "OPEN",
        "registry_rows": len(registry),
    }


def audit(*, write: bool = True) -> dict[str, Any]:
    data_root = resolve_data_root()
    with tempfile.TemporaryDirectory(prefix="stage5-independent-audit-") as directory:
        output = Path(directory) / "results"
        execute_independently(data_root, output)
        before = clean_audit(output)
        mutations = mutation_tests()
        if not mutations["all_rejected_as_expected"]:
            raise RuntimeError("MUTATION_SUITE_FAILED")
        after = clean_audit(output)
    if before != after:
        raise RuntimeError("MUTATION_ISOLATION_FAILED")
    result = dict(after)
    result.update({"clean_control_before": "PASS", "clean_control_after": "PASS",
                   "mutation_tests": mutations, "deterministic_audit_rerun": "PASS"})
    payload = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if write:
        RESULT_FILE.write_text(payload, encoding="utf-8")
    return result


def deterministic_audit() -> dict[str, Any]:
    """Execute twice and require byte-identical machine-independent evidence."""
    first = json.dumps(audit(write=False), indent=2, sort_keys=True) + "\n"
    second = json.dumps(audit(write=False), indent=2, sort_keys=True) + "\n"
    if first != second:
        raise RuntimeError("NONDETERMINISTIC_AUDIT")
    RESULT_FILE.write_text(first, encoding="utf-8")
    return json.loads(first)


if __name__ == "__main__":
    print(json.dumps(deterministic_audit(), sort_keys=True))
