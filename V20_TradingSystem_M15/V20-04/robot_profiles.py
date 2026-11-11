"""V20-04: inert three-account profiles; no broker imports or live execution.

One configuration type for three strategy instances. This is NOT a trading
engine and does not alter the running H1 or M15 systems.
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from pathlib import PureWindowsPath

N4 = ("USDRUBF", "CNYRUBF", "GLDRUBF", "IMOEXF")
RISK_PROVISIONAL = Decimal("0.015")  # Not LIVE-approved.
TIMEFRAME = "M15"
INITIAL_STOP_ATR = 2
EXIT_BEFORE_OBSERVED_SESSION = 3
SOURCES = {
    "SHALLOW_PULLBACK": "research_original_v20/run.py",
    "OBV_PRESSURE": "research_original_v20/run.py",
    "INSIDE_DAY_RELEASE": "research_original_v20/legacy_v4/study_v4.py",
}
SLOTS = {
    "SHALLOW_PULLBACK": "shallow",
    "OBV_PRESSURE": "obv",
    "INSIDE_DAY_RELEASE": "inside",
}


@dataclass(frozen=True)
class RobotProfile:
    strategy: str
    slot: str
    root: PureWindowsPath
    task_name: str
    account_env: str
    token_ref_env: str
    state_path: PureWindowsPath
    audit_path: PureWindowsPath
    symbols: tuple[str, ...] = N4
    timeframe: str = TIMEFRAME
    max_new_entries_session: int = 2
    max_new_entries_instrument_session: int = 1
    max_open_positions_instrument: int = 1
    risk_fraction_provisional: Decimal = RISK_PROVISIONAL
    initial_stop_atr: int = INITIAL_STOP_ATR
    exit_before_observed_session: int = EXIT_BEFORE_OBSERVED_SESSION
    live_enabled: bool = False
    execution_mode: str = "OFFLINE_ONLY"

    def __post_init__(self) -> None:
        if self.strategy not in SOURCES or self.slot != SLOTS[self.strategy]:
            raise ValueError("V20_PROFILE_STRATEGY_MISMATCH")
        if self.live_enabled is not False or self.execution_mode != "OFFLINE_ONLY":
            raise ValueError("V20_LIVE_NOT_AUTHORIZED")
        if self.symbols != N4 or self.timeframe != "M15":
            raise ValueError("V20_FROZEN_UNIVERSE_OR_TIMEFRAME")
        if (self.max_new_entries_session, self.max_new_entries_instrument_session,
            self.max_open_positions_instrument, self.initial_stop_atr,
            self.exit_before_observed_session) != (2, 1, 1, 2, 3):
            raise ValueError("V20_FROZEN_EXECUTION_LIMITS")
        if self.risk_fraction_provisional != Decimal("0.015"):
            raise ValueError("V20_PROVISIONAL_RISK_MISMATCH")
        if (self.state_path.parent != self.root or self.audit_path.parent != self.root
            or self.state_path == self.audit_path):
            raise ValueError("V20_STATE_AUDIT_NOT_ISOLATED")

    @property
    def frozen_signal_source(self) -> str:
        return SOURCES[self.strategy]


def profiles(server_root: str = r"C:\V20Lab") -> dict[str, RobotProfile]:
    root = PureWindowsPath(server_root)
    if not root.is_absolute():
        raise ValueError("V20_ROOT_MUST_BE_ABSOLUTE_WINDOWS_PATH")
    out = {}
    for strategy, slot in SLOTS.items():
        robot_root = root / slot
        prefix = "V20_" + slot.upper()
        out[strategy] = RobotProfile(
            strategy=strategy,
            slot=slot,
            root=robot_root,
            task_name="v20-" + slot,
            account_env=prefix + "_FINAM_ACCOUNT_ID",
            token_ref_env=prefix + "_FINAM_TOKEN_REF",
            state_path=robot_root / "state.sqlite3",
            audit_path=robot_root / "audit.jsonl",
        )
    for attr in ("task_name", "account_env", "token_ref_env", "state_path", "audit_path", "root"):
        if len({getattr(p, attr) for p in out.values()}) != 3:
            raise ValueError("V20_CROSS_ACCOUNT_ISOLATION_FAILURE:" + attr)
    return out
