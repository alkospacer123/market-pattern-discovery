from __future__ import annotations
from dataclasses import asdict, is_dataclass
import json
from pathlib import Path
import pandas as pd

SETUP_DIAGNOSTIC_FIELDS = ("setup_id", "symbol", "direction", "compression_time", "bbw",
    "bbw_threshold", "range_start", "range_end", "range_bars", "range_high", "range_low",
    "range_width", "range_width_atr", "range_width_pct", "ema", "ema_slope",
    "setup_bar_open_time", "setup_bar_close_time", "breakout_known_at",
    "first_allowed_retest_bar", "breakout_time", "breakout_level", "breakout_distance",
    "retest_start", "retest_end", "retest_bars", "retest_depth_price",
    "retest_depth_ticks", "retest_depth_range_pct", "confirmation_time",
    "confirmation_range_atr", "confirmation_body_atr", "planned_entry_time", "actual_entry",
    "entry_extension_atr", "entry_extension_range_pct", "structural_stop",
    "stop_distance_price", "stop_distance_ticks", "stop_atr", "stop_range_ratio",
    "rejection_reason")


class DiagnosticWriter:
    FILES = ("events", "setups", "rejected_setups", "trades")

    def __init__(self):
        self.rows: dict[str, list[dict]] = {name: [] for name in self.FILES}

    def append(self, table: str, **row) -> None:
        if table not in self.rows:
            raise KeyError(table)
        normalized = ({key: None for key in SETUP_DIAGNOSTIC_FIELDS}
                      if table in {"setups", "rejected_setups"} else {})
        normalized.update({key: asdict(value) if is_dataclass(value) else value for key, value in row.items()})
        self.rows[table].append(normalized)

    def transition(self, timestamp, setup_id: str, from_state: str, to_state: str, reason: str, **extra) -> None:
        self.append("events", timestamp=timestamp, datetime=timestamp, setup_id=setup_id,
                    from_state=from_state, to_state=to_state, reason=reason, **extra)

    def write(self, directory: str | Path) -> None:
        root = Path(directory)
        root.mkdir(parents=True, exist_ok=True)
        for name in self.FILES:
            frame = pd.DataFrame(self.rows[name])
            frame.to_csv(root / f"{name}.csv", index=False)
        (root / "execution_policy.json").write_text(json.dumps({"intrabar_fallback": "STOP_FIRST", "note": "Lower-timeframe paths may override fallback when explicitly supplied."}, indent=2), encoding="utf-8")
