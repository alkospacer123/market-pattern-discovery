"""R070 OFFLINE candidate entry boundary: frozen M15 signal -> checked EXT2.

No FINAM commands, positions, risk or SQLite. The historical prefix must be
built by the separately tested SHA/calendar/overlap bridge. This gate also
compares its latest M15 bars against independently read live FINAM M15 to
prevent a stale or unrelated data source from authorizing an entry.
"""
from __future__ import annotations

from datetime import datetime, timedelta
from decimal import Decimal, InvalidOperation
import pandas as pd

from .ext2_r060 import (
    APPLIES_TO, SYMBOLS, FULL_N4, EXT2Decision, ext2_signal_gate,
)
from .frozen_adapter import validate_completed_history
from .offline_planner import FrozenSignal, ProposedEntry, STEP


def evaluate_r070_candidate_ext2(
    *, robot: str, symbol: str, frozen_signal: FrozenSignal,
    finam_completed: pd.DataFrame, verified_full_history: pd.DataFrame | None,
) -> EXT2Decision:
    """A failed proof blocks ONLY a new EXT2 entry, never an open position.

    finam_completed is the existing frozen-signal M15 observation.
    verified_full_history must be previously stitched and calendar-checked.
    The last 4 completed FINAM bars MUST match the long-run history exactly,
    including volume, even when historical source comes from terminal CSV.
    """
    if robot not in {"v20-shallow", "v20-obv", "v20-inside"} or symbol not in FULL_N4:
        return EXT2Decision(True, False, "EXT2_CANDIDATE_IDENTITY_INVALID")
    if (not isinstance(frozen_signal, FrozenSignal)
            or frozen_signal.symbol != symbol
            or frozen_signal.side not in (-1, 1)
            or not isinstance(frozen_signal.signal_bar_open, datetime)
            or frozen_signal.signal_bar_open.tzinfo is not None):
        return EXT2Decision(True, False, "EXT2_FROZEN_SIGNAL_INVALID")
    if robot not in APPLIES_TO or symbol not in SYMBOLS:
        return EXT2Decision(False, True, "EXT2_NOT_APPLICABLE")
    if verified_full_history is None:
        return EXT2Decision(True, False, "EXT2_CERTIFIED_HISTORY_MISSING")
    try:
        signal_open = frozen_signal.signal_bar_open
        observed = signal_open + timedelta(minutes=15)
        recent = validate_completed_history(symbol, finam_completed, observed_at=observed)
        full = validate_completed_history(symbol, verified_full_history, observed_at=observed)
        if (len(recent) < 4 or len(full) < 4
                or recent.Datetime.iloc[-1] != pd.Timestamp(signal_open)
                or full.Datetime.iloc[-1] != pd.Timestamp(signal_open)):
            return EXT2Decision(True, False, "EXT2_RECENT_COMPLETED_M15_MISSING")
        window = recent.tail(4).reset_index(drop=True)
        subset = full.loc[full.Datetime.isin(window.Datetime)].reset_index(drop=True)
        if (len(subset) != 4
                or not subset.Datetime.equals(window.Datetime)):
            return EXT2Decision(True, False, "EXT2_HISTORY_FINAM_TIMESTAMPS_MISMATCH")
        for col in ("Open", "High", "Low", "Close", "Volume"):
            if any(Decimal(str(a)) != Decimal(str(b))
                   for a, b in zip(subset[col], window[col])):
                return EXT2Decision(True, False, "EXT2_HISTORY_FINAM_OHLCV_MISMATCH")
        return ext2_signal_gate(
            robot=robot, symbol=symbol, side=frozen_signal.side,
            signal_open_msk=signal_open, completed_bars=full)
    except (ValueError, TypeError, ArithmeticError, InvalidOperation, KeyError):
        return EXT2Decision(True, False, "EXT2_CANDIDATE_INPUT_UNVERIFIED")


def stage_r070_after_frozen_proposal(
    *, robot: str, symbol: str, frozen_draft: tuple | None,
    finam_completed: pd.DataFrame,
    verified_full_history: pd.DataFrame | None,
    durable_audit,
) -> tuple | None:
    """OFFLINE-only R070 gate at existing V20 pre-intent boundary.

    Existing propose_finam_m15_next_open() has already computed the frozen
    signal and an unpersisted draft, including its provisional H1 risk/GO.
    The returned draft MUST pass this gate and produce durable audit evidence
    BEFORE any journal.prepare_entry() / submit_entry_once() may be called.
    This wrapper itself cannot submit orders or alter production SQLite.
    """
    if frozen_draft is None:
        return None
    if (not isinstance(frozen_draft, tuple) or len(frozen_draft) != 4
            or not isinstance(frozen_draft[0], FrozenSignal)
            or not isinstance(frozen_draft[1], ProposedEntry)):
        raise ValueError("R070_FROZEN_DRAFT_UNVERIFIED")
    signal, candidate, _authority, _snapshot = frozen_draft
    if (candidate.symbol != symbol
            or signal.symbol != symbol
            or candidate.strategy != signal.strategy
            or candidate.direction != ("LONG" if signal.side == 1 else "SHORT")
            or candidate.entry_bar_open != signal.signal_bar_open + STEP):
        raise ValueError("R070_FROZEN_DRAFT_SCOPE_MISMATCH")
    if not callable(durable_audit):
        raise ValueError("R070_EXT2_DURABLE_AUDIT_REQUIRED")
    decision = evaluate_r070_candidate_ext2(
        robot=robot, symbol=symbol, frozen_signal=signal,
        finam_completed=finam_completed,
        verified_full_history=verified_full_history,
    )
    try:
        ok = durable_audit(
            robot=robot, symbol=symbol, signal_open_msk=signal.signal_bar_open,
            entry_open_msk=candidate.entry_bar_open, decision=decision)
    except Exception as exc:
        raise ValueError("R070_EXT2_AUDIT_NOT_PROVEN") from exc
    if ok is not True:
        raise ValueError("R070_EXT2_AUDIT_NOT_PROVEN")
    return frozen_draft if decision.permit else None


def propose_r070_readonly_candidate(
    reader, *, symbol: str, from_utc: datetime, now: datetime,
    cost_per_contract: Decimal, verified_full_history: pd.DataFrame | None,
    durable_audit, broker_ownership=None,
) -> tuple | None:
    """Use frozen FINAM proposer without modifying the SHA-pinned LIVE worker.

    A second GET of M15 is made ONLY IF a frozen signal exists: the pinned
    proposer does not return its M15 bars. Both observations must agree on
    the M15 boundary and NEXT_OPEN reference before EXT2 can permit a
    candidate. No SQLite, order, cancellation or SLTP method is called.
    This is NOT an approved LIVE execution entrypoint.
    """
    from .finam_execution import (
        V20FinamReadAdapter, V20FinamBlocked,
        propose_finam_m15_next_open, read_finam_m15_boundary,
    )
    if not isinstance(reader, V20FinamReadAdapter):
        raise V20FinamBlocked("R070_READER_SCOPE_INVALID")
    frozen = propose_finam_m15_next_open(
        reader, symbol=symbol, from_utc=from_utc, now=now,
        cost_per_contract=cost_per_contract, broker_ownership=broker_ownership,
    )
    if frozen is None:
        return None
    signal, candidate, _, _ = frozen
    observed = read_finam_m15_boundary(
        reader, symbol=symbol, from_utc=from_utc, now=now,
    )
    if (observed.symbol != symbol
            or observed.at_msk != candidate.entry_bar_open
            or observed.witnessed_open != candidate.reference_entry
            or observed.completed.empty
            or observed.completed.Datetime.iloc[-1] != pd.Timestamp(signal.signal_bar_open)):
        raise V20FinamBlocked("R070_SECOND_M15_WITNESS_DIVERGED")
    return stage_r070_after_frozen_proposal(
        robot=reader.robot_id, symbol=symbol, frozen_draft=frozen,
        finam_completed=observed.completed,
        verified_full_history=verified_full_history,
        durable_audit=durable_audit,
    )
