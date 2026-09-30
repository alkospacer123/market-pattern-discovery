"""Operational configuration only; frozen strategy parameters are deliberately absent."""
from dataclasses import dataclass
import os
from pathlib import Path
def _explicit_true(name:str)->bool: return os.getenv(name,"").strip().lower()=="true"
@dataclass(frozen=True)
class RuntimeConfig:
    persistence_path:Path; audit_log_path:Path; starting_equity:str; finam_endpoint:str
    dry_run:bool=True; live_trading_enabled:bool=False; new_entries_disabled:bool=False
    @classmethod
    def from_environment(cls):
        live=_explicit_true("LIVE_TRADING_ENABLED")
        return cls(Path(os.getenv("ROBOT_STATE_PATH","stage8-state.sqlite3")),Path(os.getenv("ROBOT_AUDIT_LOG","stage8-audit.jsonl")),os.environ["STARTING_REALIZED_EQUITY"],os.getenv("FINAM_API_ENDPOINT","UNCONFIGURED"),not live,live,_explicit_true("NEW_ENTRIES_DISABLED"))
