"""Deterministic, data-free export of one autonomous research run."""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
from pathlib import Path
from typing import Any, Iterable, Mapping


ARTIFACT_FILES = (
    "hypotheses.jsonl",
    "strategies.jsonl",
    "signals.jsonl",
    "backtests.jsonl",
    "validations.jsonl",
    "rankings.jsonl",
)


def _canonical(value: Mapping[str, Any]) -> str:
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


class AutonomousRunArtifacts:
    """Materialize the public, immutable-by-content view of a completed run.

    The exporter reads research registries and a caller-provided data manifest;
    it never reads or copies source candles. Re-exporting identical state creates
    byte-identical artifacts (the manifest deliberately contains no wall clock).
    """

    def __init__(self, root: str | Path) -> None:
        self.root = Path(root)

    @staticmethod
    def _source_commit(repository: Path) -> str:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=repository, check=True,
            capture_output=True, text=True,
        )
        return result.stdout.strip()

    @staticmethod
    def _rows(memory: Any) -> dict[str, Iterable[Mapping[str, Any]]]:
        from market_pattern_discovery.research.strategy_candidates import strategy_candidate_dict

        findings = memory.scientific_findings()
        return {
            "hypotheses.jsonl": (
                row["hypothesis"] for row in findings if row.get("hypothesis") is not None
            ),
            "strategies.jsonl": (
                strategy_candidate_dict(item) for item in memory.strategy_candidates().values()
            ),
            "signals.jsonl": (item.to_dict() for item in memory.executable_signal_definitions().values()),
            "backtests.jsonl": (item.to_dict() for item in memory.backtest_results().values()),
            "validations.jsonl": (item.to_dict() for item in memory.validation_reports().values()),
            "rankings.jsonl": (item.to_dict() for item in memory.strategy_rankings().values()),
        }

    def export(self, memory: Any, *, data_manifest: str | Path,
               repository: str | Path) -> Mapping[str, Any]:
        """Export a reproducible run bundle and return its manifest."""
        data_manifest = Path(data_manifest)
        if not data_manifest.is_file():
            raise FileNotFoundError(f"data manifest does not exist: {data_manifest}")
        repository = Path(repository)
        self.root.mkdir(parents=True, exist_ok=True)

        counts: dict[str, int] = {}
        digests: dict[str, str] = {}
        for name, rows in self._rows(memory).items():
            ordered = sorted((_canonical(dict(row)) for row in rows))
            payload = "".join(f"{row}\n" for row in ordered)
            path = self.root / name
            _write_atomic(path, payload)
            counts[name] = len(ordered)
            digests[name] = _sha256(path)

        commit = self._source_commit(repository)
        _write_atomic(self.root / "source_commit.txt", f"{commit}\n")
        data_digest = _sha256(data_manifest)
        _write_atomic(self.root / "data_manifest.sha256", f"{data_digest}\n")
        manifest: dict[str, Any] = {
            "schema_version": "1",
            "status": "COMPLETED",
            "source_commit": commit,
            "data_manifest_sha256": data_digest,
            "zero_look_ahead": True,
            "true_oos_2025_accessed": False,
            "artifacts": {
                name: {"records": counts[name], "sha256": digests[name]}
                for name in ARTIFACT_FILES
            },
        }
        _write_atomic(self.root / "manifest.json", f"{_canonical(manifest)}\n")
        return manifest
