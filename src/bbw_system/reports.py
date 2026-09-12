from __future__ import annotations
from dataclasses import asdict, is_dataclass
import json
from pathlib import Path
import pandas as pd


class DiagnosticWriter:
    FILES = ("events", "setups", "rejected_setups", "trades")

    def __init__(self):
        self.rows: dict[str, list[dict]] = {name: [] for name in self.FILES}

    def append(self, table: str, **row) -> None:
        if table not in self.rows:
            raise KeyError(table)
        self.rows[table].append({key: asdict(value) if is_dataclass(value) else value for key, value in row.items()})

    def write(self, directory: str | Path) -> None:
        root = Path(directory)
        root.mkdir(parents=True, exist_ok=True)
        for name in self.FILES:
            frame = pd.DataFrame(self.rows[name])
            frame.to_csv(root / f"{name}.csv", index=False)
        (root / "execution_policy.json").write_text(json.dumps({"intrabar_fallback": "STOP_FIRST", "note": "Lower-timeframe paths may override fallback when explicitly supplied."}, indent=2), encoding="utf-8")
