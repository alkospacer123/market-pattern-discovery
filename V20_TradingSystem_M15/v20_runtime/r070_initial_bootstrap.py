"""R070 candidate first-time M15 history bootstrap using pinned real exports.

Only OFFLINE inputs and a separately verified MOEX futures calendar; no
trade requests, no LIVE SQLite, no Windows Task changes. Must be called
explicitly from an isolated candidate operator, never by current V20.
"""
from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd

from .ext2_history_bridge import (
    EXT2HistoryBlocked, load_finam_terminal_csv, load_r060_pinned_csv,
    m15_history_sha256, stitch_verified_m15,
)
from .r070_m15_checkpoint import PINNED_TERMINAL_SHA256
from .r070_m15_candidate_state import R070CandidateCheckpointState
from .r070_moex_calendar import fetch_moex_futures_calendar


def prepare_r070_initial_m15(
    *, symbol: str, r060_seed_csv: str | Path,
    finam_terminal_csv: str | Path,
    signal_open_msk: datetime, observed_at_msk: datetime,
) -> tuple[pd.DataFrame, str]:
    """Require two original pinned files and authoritative MOEX day flags.

    The terminal CSV can contain newer bars. Only completed bars up to the
    requested signal open are admitted; reject attempts to infer any M15.
    This is a preflight, not an exchange-trading permission.
    """
    if symbol not in PINNED_TERMINAL_SHA256:
        raise EXT2HistoryBlocked("R070_BOOTSTRAP_SYMBOL_INVALID")
    if (not isinstance(signal_open_msk, datetime)
            or signal_open_msk.tzinfo is not None
            or not isinstance(observed_at_msk, datetime)
            or observed_at_msk.tzinfo is not None
            or observed_at_msk < signal_open_msk + timedelta(minutes=15)):
        raise EXT2HistoryBlocked("R070_BOOTSTRAP_SIGNAL_NOT_COMPLETED")
    old = load_r060_pinned_csv(r060_seed_csv, symbol=symbol)
    recent = load_finam_terminal_csv(
        finam_terminal_csv,
        expected_sha256=PINNED_TERMINAL_SHA256[symbol])
    recent = recent.loc[recent.Datetime <= pd.Timestamp(signal_open_msk)].copy()
    if (recent.empty
            or recent.Datetime.iloc[-1] != pd.Timestamp(signal_open_msk)):
        raise EXT2HistoryBlocked("R070_BOOTSTRAP_SIGNAL_M15_NOT_IN_EXPORT")
    first_day = recent.Datetime.iloc[0].date()
    last_day = signal_open_msk.date()
    if first_day.year != last_day.year:
        raise EXT2HistoryBlocked("R070_BOOTSTRAP_MOEX_CALENDAR_YEAR_SCOPE")
    official_days = fetch_moex_futures_calendar(
        date_from=first_day, date_till=last_day)
    merged = stitch_verified_m15(
        seed=old, finam_recent=recent,
        signal_open_msk=signal_open_msk,
        observed_at_msk=observed_at_msk,
        verified_open_days=official_days,
    )
    return merged, m15_history_sha256(merged)


def bootstrap_r070_candidate(
    *, candidate: R070CandidateCheckpointState, symbol: str,
    r060_seed_csv: str | Path, finam_terminal_csv: str | Path,
    signal_open_msk: datetime, observed_at_msk: datetime,
) -> dict:
    """One-off candidate-only install of a *verified* source checkpoint.

    An independent current FINAM completed M15 witness is STILL mandatory
    before a subsequent EXT2 entry; the bootstrap itself never permits one.
    """
    if not isinstance(candidate, R070CandidateCheckpointState):
        raise EXT2HistoryBlocked("R070_BOOTSTRAP_CANDIDATE_STATE_REQUIRED")
    if candidate.verified_cursor(symbol) is not None:
        raise EXT2HistoryBlocked("R070_BOOTSTRAP_ALREADY_PRESENT")
    full, digest = prepare_r070_initial_m15(
        symbol=symbol, r060_seed_csv=r060_seed_csv,
        finam_terminal_csv=finam_terminal_csv,
        signal_open_msk=signal_open_msk,
        observed_at_msk=observed_at_msk)
    return candidate.bootstrap(
        symbol=symbol, verified_history=full,
        expected_history_sha256=digest)
