"""Canonical artifact writers and SHA-256 inventory."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import pandas as pd


def write_csv(path: Path, frame: pd.DataFrame) -> None:
    frame.to_csv(path, index=False, lineterminator="\n", float_format="%.12g", na_rep="")


def write_json(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def artifact_hashes(root: Path, exclude: set[str] | None = None) -> dict[str, str]:
    excluded = exclude or set()
    return {p.relative_to(root).as_posix(): sha256(p) for p in sorted(root.iterdir())
            if p.is_file() and p.name not in excluded}
