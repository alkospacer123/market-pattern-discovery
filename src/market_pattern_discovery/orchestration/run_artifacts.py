"""Persistent, deterministic and self-verifying autonomous-run bundles."""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
from datetime import datetime, timezone
from dataclasses import asdict, is_dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping


DEFAULT_ARTIFACT_ROOT = Path("/workspace/market-pattern-artifacts")
ARTIFACT_FILES = (
    "hypotheses.jsonl", "strategies.jsonl", "signals.jsonl", "backtests.jsonl",
    "validations.jsonl", "rankings.jsonl",
)
DIAGNOSTIC_FILES = ("audit_metadata.json", "direction_bias_report.json", "horizon_report.json")
RUN_REGISTRY = "runs_registry.json"
REQUIRED_BUNDLE_FILES = (*ARTIFACT_FILES, "audit_metadata.json", "source_commit.txt",
                         "data_manifest.sha256")


def _canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _write_atomic(path: Path, payload: str) -> None:
    temporary = path.with_name(f".{path.name}.tmp")
    temporary.write_text(payload, encoding="utf-8")
    os.replace(temporary, path)


def _dict(value: Any) -> dict[str, Any]:
    if hasattr(value, "to_dict"):
        return value.to_dict()
    if is_dataclass(value):
        return asdict(value)
    return dict(value)


def _direction(value: Any) -> str | None:
    raw = value.get("direction") if isinstance(value, Mapping) else getattr(value, "direction", None)
    return getattr(raw, "value", raw)


def _direction_stage(rows: Iterable[Any], *, trades: bool = False) -> dict[str, Any]:
    directions: list[str] = []
    for row in rows:
        values = getattr(row, "trades", ()) if trades else (row,)
        directions.extend(direction for item in values if (direction := _direction(item)) in {"LONG", "SHORT"})
    total = len(directions)
    return {"total": total, "LONG": directions.count("LONG"), "SHORT": directions.count("SHORT"),
            "LONG_percent": 100 * directions.count("LONG") / total if total else 0.0,
            "SHORT_percent": 100 * directions.count("SHORT") / total if total else 0.0}


class AutonomousRunArtifacts:
    """Write runs below a stable storage root and fail closed on verification."""

    def __init__(self, root: str | Path = DEFAULT_ARTIFACT_ROOT) -> None:
        self.storage_root = Path(root)

    @staticmethod
    def _source_commit(repository: Path) -> str:
        result = subprocess.run(["git", "rev-parse", "HEAD"], cwd=repository, check=True,
                                capture_output=True, text=True)
        return result.stdout.strip()

    @staticmethod
    def _collections(memory: Any) -> dict[str, list[Any]]:
        return {
            "findings": list(memory.scientific_findings()),
            "trading": list(memory.trading_candidates().values()) if hasattr(memory, "trading_candidates") else [],
            "strategies": list(memory.strategy_candidates().values()),
            "signals": list(memory.executable_signal_definitions().values()),
            "backtests": list(memory.backtest_results().values()),
            "validations": list(memory.validation_reports().values()),
            "rankings": list(memory.strategy_rankings().values()),
        }

    @staticmethod
    def _rows(items: Mapping[str, list[Any]]) -> dict[str, Iterable[Mapping[str, Any]]]:
        from market_pattern_discovery.research.strategy_candidates import strategy_candidate_dict
        return {
            "hypotheses.jsonl": (row["hypothesis"] for row in items["findings"] if row.get("hypothesis")),
            "strategies.jsonl": (strategy_candidate_dict(row) for row in items["strategies"]),
            "signals.jsonl": (_dict(row) for row in items["signals"]),
            "backtests.jsonl": (_dict(row) for row in items["backtests"]),
            "validations.jsonl": (_dict(row) for row in items["validations"]),
            "rankings.jsonl": (_dict(row) for row in items["rankings"]),
        }

    @staticmethod
    def _diagnostics(items: Mapping[str, list[Any]]) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
        strategies = [_dict(row) for row in items["strategies"]]
        signals = [_dict(row) for row in items["signals"]]
        backtests = [_dict(row) for row in items["backtests"]]
        signal_by_strategy = {row["source_strategy_candidate_id"]: row for row in signals}
        strategy_diagnostics = []
        for row in strategies:
            signal = signal_by_strategy.get(row["strategy_id"], {})
            risk, exit_rule = row.get("risk", {}), row.get("exit", {})
            strategy_diagnostics.append({
                "strategy_id": row["strategy_id"], "symbol": row.get("symbol"),
                "horizon": row.get("horizon"), "execution_timeframe": row.get("execution_timeframe"),
                "context_timeframes": row.get("context_timeframes", []), "direction": row.get("direction"),
                "signal_type": signal.get("signal_type"), "entry_logic": row.get("entry"),
                "exit_logic": exit_rule, "stop_loss": risk, "take_profit": exit_rule,
                "risk_reward": {"risk": risk, "reward": exit_rule},
            })
        trade_diagnostics = []
        for row in backtests:
            trades = row.get("trades", [])
            trade_diagnostics.append({key: row.get(key) for key in (
                "strategy_id", "total_trades", "win_rate", "profit_factor", "expectancy", "max_drawdown",
                "average_holding_time") } | {
                "LONG_trades": sum(t.get("direction") == "LONG" for t in trades),
                "SHORT_trades": sum(t.get("direction") == "SHORT" for t in trades),
            })
        funnel = {"research_hypotheses": sum(bool(row.get("hypothesis")) for row in items["findings"]),
                  "pattern_effects": sum(bool(row.get("pattern_effect")) for row in items["findings"]),
                  "trading_candidates": len(items["trading"]), "strategy_candidates": len(strategies),
                  "signals": len(signals), "backtests": len(backtests),
                  "validation": len(items["validations"]), "ranking": len(items["rankings"])}
        audit = {"strategy_diagnostics": strategy_diagnostics, "trade_diagnostics": trade_diagnostics,
                 "pipeline_funnel": funnel}
        effects = []
        for finding in items["findings"]:
            if effect := finding.get("pattern_effect"):
                effects.append({"direction": "LONG" if effect["effect"] > 0 else "SHORT" if effect["effect"] < 0 else None})
        bias = {"PatternEffect": _direction_stage(effects), "TradingCandidate": _direction_stage(items["trading"]),
                "StrategyCandidate": _direction_stage(items["strategies"]),
                "ExecutableSignal": _direction_stage(items["signals"]),
                "Backtest trades": _direction_stage(items["backtests"], trades=True)}
        profiles = {"SCALPING": {"execution": ["M1", "M5"], "context": ["M15"]},
                    "INTRADAY": {"execution": ["M5", "M15", "M30"], "context": ["H1", "D1"]},
                    "MEDIUM TERM": {"execution": ["H1", "D1"], "context": ["H1", "D1"]}}
        created = {(row.get("horizon"), row.get("execution_timeframe")) for row in strategies}
        traded_ids = {row.get("strategy_id") for row in backtests}
        traded = {(row.get("horizon"), row.get("execution_timeframe")) for row in strategies if row.get("strategy_id") in traded_ids}
        horizon = {name: {"expected_execution_timeframes": spec["execution"],
                          "expected_context_timeframes": spec["context"],
                          "created": sorted(tf for h, tf in created if h == name),
                          "traded": sorted(tf for h, tf in traded if h == name),
                          "missing": sorted(set(spec["execution"]) - {tf for h, tf in created if h == name})}
                   for name, spec in profiles.items()}
        return audit, bias, horizon

    def export(self, memory: Any, *, data_manifest: str | Path, repository: str | Path,
               run_id: str | None = None, seed: int | None = None) -> Mapping[str, Any]:
        data_manifest, repository = Path(data_manifest), Path(repository)
        if not data_manifest.is_file():
            raise FileNotFoundError(f"data manifest does not exist: {data_manifest}")
        commit, data_digest = self._source_commit(repository), _sha256(data_manifest)
        run_id = run_id or hashlib.sha256(f"{commit}:{data_digest}:{seed}".encode()).hexdigest()[:20]
        if not run_id or Path(run_id).name != run_id:
            raise ValueError("run_id must be one safe path component")
        root = self.storage_root / run_id
        root.mkdir(parents=True, exist_ok=True)
        items = self._collections(memory)
        for name, rows in self._rows(items).items():
            _write_atomic(root / name, "".join(f"{row}\n" for row in sorted(_canonical(dict(r)) for r in rows)))
        audit, bias, horizon = self._diagnostics(items)
        for name, value in zip(DIAGNOSTIC_FILES, (audit, bias, horizon)):
            _write_atomic(root / name, f"{_canonical(value)}\n")
        _write_atomic(root / "source_commit.txt", f"{commit}\n")
        _write_atomic(root / "data_manifest.sha256", f"{data_digest}\n")
        inventory = (*ARTIFACT_FILES, *DIAGNOSTIC_FILES, "source_commit.txt", "data_manifest.sha256")
        manifest = {"schema_version": "2", "run_id": run_id, "status": "VERIFYING",
                    "source_commit": commit, "data_manifest_sha256": data_digest, "seed": seed,
                    "zero_look_ahead": True, "true_oos_2025_accessed": False,
                    "artifacts": {name: {"records": sum(1 for _ in (root / name).open()) if name.endswith(".jsonl") else None,
                                                   "sha256": _sha256(root / name)} for name in inventory}}
        _write_atomic(root / "manifest.json", f"{_canonical(manifest)}\n")
        manifest["status"] = "READY_FOR_AUDIT"
        _write_atomic(root / "manifest.json", f"{_canonical(manifest)}\n")
        try:
            self.verify(root)
        except Exception:
            manifest["status"] = "FAILED"
            _write_atomic(root / "manifest.json", f"{_canonical(manifest)}\n")
            raise
        self._register(manifest)
        return manifest

    def _register(self, manifest: Mapping[str, Any]) -> None:
        """Publish a verified run so a later process can discover it by run id."""
        self.storage_root.mkdir(parents=True, exist_ok=True)
        path = self.storage_root / RUN_REGISTRY
        registry = json.loads(path.read_text(encoding="utf-8")) if path.is_file() else {
            "schema_version": "1", "runs": []}
        runs = [row for row in registry.get("runs", []) if row.get("run_id") != manifest["run_id"]]
        runs.append({"run_id": manifest["run_id"], "status": "READY_FOR_AUDIT",
                     "source_commit": manifest["source_commit"],
                     "registered_at": datetime.now(timezone.utc).isoformat()})
        registry["runs"] = sorted(runs, key=lambda row: (row["registered_at"], row["run_id"]))
        _write_atomic(path, f"{_canonical(registry)}\n")

    def latest(self) -> Path:
        """Find the latest registered run without requiring its bundle path."""
        path = self.storage_root / RUN_REGISTRY
        if not path.is_file():
            raise FileNotFoundError(f"artifact run registry missing: {path}")
        registry = json.loads(path.read_text(encoding="utf-8"))
        runs = registry.get("runs", [])
        if not runs:
            raise FileNotFoundError(f"artifact run registry is empty: {path}")
        run = max(runs, key=lambda row: (row["registered_at"], row["run_id"]))
        root = self.storage_root / run["run_id"]
        self.verify(root)
        return root

    @staticmethod
    def verify(run_root: str | Path) -> Mapping[str, Any]:
        root = Path(run_root)
        if not root.is_dir() or not (root / "manifest.json").is_file():
            raise FileNotFoundError(f"persistent run or manifest missing: {root}")
        manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
        artifacts = manifest.get("artifacts")
        if manifest.get("status") != "READY_FOR_AUDIT" or not isinstance(artifacts, dict):
            raise ValueError("run is not READY_FOR_AUDIT with an artifact inventory")
        missing = set(REQUIRED_BUNDLE_FILES) - set(artifacts)
        if missing:
            raise ValueError(f"required artifacts absent from manifest: {sorted(missing)}")
        if not manifest.get("source_commit") or not manifest.get("data_manifest_sha256"):
            raise ValueError("commit or data-manifest hash missing")
        for name, expected in artifacts.items():
            path = root / name
            if not isinstance(expected, dict) or not expected.get("sha256"):
                raise ValueError(f"artifact hash missing: {name}")
            if not path.is_file() or _sha256(path) != expected["sha256"]:
                raise ValueError(f"artifact missing or hash mismatch: {name}")
            if name.endswith(".jsonl"):
                with path.open(encoding="utf-8") as stream:
                    count = sum(1 for line in stream if json.loads(line) is not None)
                if count != expected["records"]:
                    raise ValueError(f"JSONL record mismatch: {name}")
        return manifest
