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
    durable_audit, broker_ownership=None, verified_history_refresh=None,
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
    # Optional rolling source. The caller owns the pinned starting history,
    # digest and independently proved exchange calendar. The refresher only
    # consumes the second observed GET M15; no extra broker history request.
    # Never mix supplied full history with a refresh callback.
    if verified_history_refresh is not None:
        from .ext2_history_bridge import m15_history_sha256
        if verified_full_history is not None or not callable(verified_history_refresh):
            raise V20FinamBlocked("R070_EXT2_HISTORY_SOURCE_AMBIGUOUS")
        try:
            verified_full_history, new_sha = verified_history_refresh(
                finam_recent=observed.completed,
                signal_open_msk=signal.signal_bar_open,
                observed_at_msk=observed.at_msk,
            )
            if (not isinstance(verified_full_history, pd.DataFrame)
                    or m15_history_sha256(verified_full_history) != new_sha):
                raise V20FinamBlocked("R070_EXT2_REFRESH_SHA_UNVERIFIED")
        except V20FinamBlocked:
            raise
        except Exception as exc:
            raise V20FinamBlocked("R070_EXT2_REFRESH_NOT_VERIFIED") from exc
    return stage_r070_after_frozen_proposal(
        robot=reader.robot_id, symbol=symbol, frozen_draft=frozen,
        finam_completed=observed.completed,
        verified_full_history=verified_full_history,
        durable_audit=durable_audit,
    )


def admit_r070_frozen_draft_pre_intent(
    *, sender, journal, reader, symbol: str, frozen_draft: tuple | None,
    from_utc: datetime, now: datetime,
) -> tuple | None:
    """Candidate ONLY: EXT2 between frozen proposal and H1 durable ENTRY intent.

    Does not fetch trading balances, create an ENTRY intent or send POST.
    Only Shallow/OBV USD/CNY/GLD are gated; Inside and IMOEXF keep frozen flow.
    A trusted long-history provider must be attached explicitly for staged
    tests. No production source is auto-connected, thus this candidate
    MUST NOT be installed in LIVE without a separately accepted source.
    """
    from .ext2_history_bridge import m15_history_sha256
    from .finam_execution import V20FinamBlocked, read_finam_m15_boundary
    if frozen_draft is None:
        return None
    if (symbol not in FULL_N4
            or reader.robot_id not in {"v20-shallow", "v20-obv", "v20-inside"}
            or journal.robot_id != reader.robot_id):
        raise V20FinamBlocked("R070_EXT2_ACCOUNT_OR_SYMBOL_INVALID")
    if reader.robot_id not in APPLIES_TO or symbol not in SYMBOLS:
        return frozen_draft
    signal, candidate, _, _ = frozen_draft
    if (not isinstance(signal, FrozenSignal)
            or not isinstance(candidate, ProposedEntry)
            or signal.symbol != symbol or candidate.symbol != symbol):
        raise V20FinamBlocked("R070_EXT2_DRAFT_UNVERIFIED")
    key = "r070_ext2_decision:" + symbol + ":" + candidate.entry_bar_open.isoformat()

    def record(decision):
        journal.store.put(key, {
            "robot": reader.robot_id, "symbol": symbol,
            "signal_msk": signal.signal_bar_open.isoformat(),
            "entry_msk": candidate.entry_bar_open.isoformat(),
            "permit": decision.permit, "reason": decision.reason,
        })
        return True

    provider = getattr(sender, "r070_verified_history_provider", None)
    refresh = getattr(sender, "r070_verified_history_refresh", None)
    # Exactly one SHA-verified source. A rolling checkpoint refresher may
    # use ONLY the existing independent second FINAM M15 witness below.
    if (provider is not None and not callable(provider)) or (
            refresh is not None and not callable(refresh)):
        raise V20FinamBlocked("R070_EXT2_HISTORY_PROVIDER_INVALID")
    if callable(provider) and callable(refresh):
        raise V20FinamBlocked("R070_EXT2_HISTORY_SOURCE_AMBIGUOUS")
    if not callable(provider) and not callable(refresh):
        record(EXT2Decision(True, False, "EXT2_VERIFIED_HISTORY_PROVIDER_MISSING"))
        return None

    def witnessed_m15():
        seen = read_finam_m15_boundary(
            reader, symbol=symbol, from_utc=from_utc, now=now)
        if (seen.symbol != symbol
                or seen.at_msk != candidate.entry_bar_open
                or seen.witnessed_open != candidate.reference_entry
                or seen.completed.empty
                or seen.completed.Datetime.iloc[-1] !=
                pd.Timestamp(signal.signal_bar_open)):
            raise V20FinamBlocked("R070_EXT2_SECOND_WITNESS_DIVERGED")
        return seen

    # Rolling source must be brought forward with real completed bars,
    # before the source can be used to authorize the frozen draft.
    observed = witnessed_m15() if callable(refresh) else None
    try:
        if callable(refresh):
            source, source_sha = refresh(
                robot=reader.robot_id, symbol=symbol,
                signal_open_msk=signal.signal_bar_open,
                finam_recent=observed.completed,
                observed_at_msk=observed.at_msk)
        else:
            source, source_sha = provider(
                robot=reader.robot_id, symbol=symbol,
                signal_open_msk=signal.signal_bar_open)
        if (not isinstance(source, pd.DataFrame)
                or not isinstance(source_sha, str)
                or m15_history_sha256(source) != source_sha):
            raise V20FinamBlocked("R070_EXT2_HISTORY_SHA_UNVERIFIED")
    except V20FinamBlocked:
        raise
    except Exception as exc:
        raise V20FinamBlocked("R070_EXT2_HISTORY_UNAVAILABLE") from exc
    if observed is None:
        observed = witnessed_m15()
    return stage_r070_after_frozen_proposal(
        robot=reader.robot_id, symbol=symbol,
        frozen_draft=frozen_draft,
        finam_completed=observed.completed,
        verified_full_history=source,
        durable_audit=lambda **kw: record(kw["decision"]),
    )
