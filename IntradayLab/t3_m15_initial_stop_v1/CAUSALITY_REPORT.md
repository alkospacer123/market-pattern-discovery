# Causality and execution assumptions

**GROSS_ONLY / COSTS_DEFERRED / NOT_LIVE_READY**.

- Signal, signal-candle extreme, causal Donchian20 shift(1), signal ATR and H1
  context are available only on the completed signal M15 close. Original
  H1 daily ordinal blocks of four contiguous M15 closes are preserved; an
  incomplete block contributes no context. Continuous cross-day indicator
  history remains the frozen T3 convention.
- Historical Close entry is explicitly unverified execution, not proof of a
  fill at that same observed Close. There is no future-open entry substitution.
- A pre-existing protective Stop is checked before current favorable High/Low.
  An adverse Open gap fills at Open. Survived completed candles update the
  favorable extreme and ATR trail for the next candle only. The exit candle's
  favorable range is excluded from historical MFE; MAE includes the adverse fill.
- Initial risk is fixed at accepted entry, never resized after trailing. A
  nonpositive/nonfinite candidate risk skips an unoccupied entry, records its
  reason, and never substitutes CONTROL. Busy signals also retain validity
  diagnostics. No buffers, new multipliers, rounded stops or filters are added.
- Signals are processed even after the same candle's protective exit, preserving
  the original Close re-entry convention. A busy position blocks new entries.
  Separate full replays preserve all changed occupancy, entries and exits.
- Positions cross sessions and years. Year-end states are diagnostic snapshots,
  not liquidation. Terminal OPEN contributes neither CLOSED PF nor CLOSED R.
  CLOSED year/month attribution preserves historical exit-bar close labels in MSK.
- Both byte parsers inspect the timestamp before the first 2025+ OHLC and stop.
  Synthetic poison tests verify this; only opaque source-byte hashes span the
  whole pinned CSV. No future OHLC is parsed, used in indicators, or selected.
- Prefix tests change/omit future bars and confirm invariant prior indicators,
  signal sequence and Stop decisions. Synthetic cases cover both directions,
  all stop formulas, zero/nonfinite risks, gaps, stop-first ordering, delayed
  trailing, fixed risk, occupancy/reentry, terminal OPEN, year crossing and
  dated CNY ticks. The full independent raw-prefix auditor checks actual paths.
- 2023 and 2024 are development-exposed. There is no Optimization, Robustness,
  Walk Forward, TRUE OOS or LIVE claim. Narrow-risk, top-winner and November
  subsets are descriptive diagnostics and do not feed entry decisions.
