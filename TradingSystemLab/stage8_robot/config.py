"""Operational configuration; LIVE cannot be selected in Stage 8."""
from dataclasses import dataclass
from enum import Enum
import os
from pathlib import Path
class RuntimeMode(str,Enum):
    DRY_RUN="DRY_RUN"; FINAM_DEMO="DEMO"; FINAM_REAL_READONLY="REAL_READONLY"; LIVE="LIVE"
def _explicit_true(name): return os.getenv(name,"").strip().lower()=="true"
@dataclass(frozen=True)
class RuntimeConfig:
    persistence_path:Path; audit_log_path:Path; starting_equity:str|None; finam_endpoint:str="https://api.finam.ru"
    mode:RuntimeMode=RuntimeMode.DRY_RUN; new_entries_disabled:bool=False; account_id:str|None=None
    @property
    def dry_run(self): return self.mode is RuntimeMode.DRY_RUN
    @property
    def live_trading_enabled(self): return False
    @classmethod
    def from_environment(cls):
        raw=os.getenv("FINAM_MODE","DRY_RUN").strip().upper()
        if raw=="LIVE": raise RuntimeError("LIVE_TRADING_NOT_AUTHORIZED")
        modes={"DRY_RUN":RuntimeMode.DRY_RUN,"DEMO":RuntimeMode.FINAM_DEMO,"FINAM_DEMO":RuntimeMode.FINAM_DEMO,
               "REAL_READONLY":RuntimeMode.FINAM_REAL_READONLY,"FINAM_REAL_READONLY":RuntimeMode.FINAM_REAL_READONLY}
        if raw not in modes: raise RuntimeError("FINAM_MODE_INVALID")
        mode=modes[raw]
        account=(os.getenv("FINAM_DEMO_ACCOUNT_ID") if mode is RuntimeMode.FINAM_DEMO else
                 os.getenv("FINAM_REAL_ACCOUNT_ID") if mode is RuntimeMode.FINAM_REAL_READONLY else None)
        if mode is RuntimeMode.FINAM_DEMO and (not account or os.getenv("FINAM_ACCOUNT_ID") not in (None,"",account)): raise RuntimeError("DEMO_ACCOUNT_EXPLICIT_BINDING_REQUIRED")
        if mode is RuntimeMode.FINAM_REAL_READONLY and (not account or os.getenv("FINAM_DEMO_ACCOUNT_ID") not in (None,"")): raise RuntimeError("REAL_ACCOUNT_EXPLICIT_BINDING_REQUIRED")
        starting=os.getenv("STARTING_REALIZED_EQUITY")
        if mode is not RuntimeMode.FINAM_REAL_READONLY and not starting: raise RuntimeError("STARTING_REALIZED_EQUITY_REQUIRED")
        return cls(Path(os.getenv("ROBOT_STATE_PATH","stage8-state.sqlite3")),Path(os.getenv("ROBOT_AUDIT_LOG","stage8-audit.jsonl")),starting,os.getenv("FINAM_API_ENDPOINT","https://api.finam.ru"),mode,_explicit_true("NEW_ENTRIES_DISABLED"),account)
