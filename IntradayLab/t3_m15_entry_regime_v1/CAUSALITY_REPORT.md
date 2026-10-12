# Causality and execution contract

`GROSS_ONLY / COSTS_DEFERRED / NOT_LIVE_READY`. Historical 2023–2024 research exposure is explicit; this is not independent Walk Forward.

| Event | Earliest availability / action |
|---|---|
| Raw M15 | Open labels localized Europe/Moscow; OHLC available only at Open +15 minutes |
| Donchian | Prior 20 observed bars only, rolling maximum/minimum shifted one; explicitly crosses dates |
| H1 | Original daily ordinal blocks of four consecutive completed M15; incomplete/gapped blocks skipped, never repacked across dates |
| H1 indicators | EMA(75), slope vs EMA five completed blocks earlier, ADX(14), ATR(14)/ATRMean(20); recursive indicator state explicitly crosses days |
| H1 predecessor | Shifted on completed H1 series BEFORE forward alignment to M15; never an M15-forward-filled predecessor |
| M15 ATR predecessor | Previous observed completed M15, before current completed signal; no future bar |
| Entry | Original T3 raw signal at signal Close, then one optional entry filter; original same-close re-entry after exit retained |
| Initial Stop | Original 2 ATR at entry; first protective test on subsequent observed bar |
| Trailing | Test carried Stop first; only surviving completed bar can ratchet; ratchet effective next observed bar |
| A1 | First complete post-entry observed M15 only; if alive and Close on/behind original level, queue next actual Open exit |
| A2 | First four post-entry complete observed M15 only; two consecutive wrong-side closes; correct-side reset; trigger on fourth executes on fifth Open |
| Queued exit vs Stop | At next observed Open, protective gap/touch takes priority at unfavorable Open; otherwise queued exit fills Open before subsequent intrabar extrema |
| Missing next bar | Wait for actual observed next Open across session gaps; no synthetic fill; terminal pending position remains open |

On a signal candle Close, completed features may be observed, but obtaining that exact Close as a real fill is not established. This inherited convention is preserved solely as the historical control oracle. No new tick-grid repair is introduced: Stop remains continuous, with separate H1 engineering ownership.

When no new exit is queued, the historical conservative OHLC Stop model fills LONG at min(Open, active Stop) and SHORT at max(Open, active Stop) if the protective level is hit. It excludes the exit candle's favorable extrema from recorded MFE. Stop `exit_time` is the original candle Close label; exact intrabar time is unknown. New next-Open exits record that Open as `exit_time`, both candle endpoints, the prior decision time and active Stop. This timestamp convention is disclosed and used consistently in every calendar report. The new exit is already completed at Open; giving a later intrabar Stop priority would use information unavailable at Open. No comparison of alternative future fills chooses the more profitable price.

All subsequent signals and position occupancy are replayed from scratch. Accepted and blocked signal opportunities are recorded. A queued exit can free a position for a later signal Close on that candle; an entry filter can keep an earlier position open or change subsequent entries. Therefore results are not deletions from the original CSV.

Gross outcomes, MFE, calendar carry, winners, original >=2R trend winners and November-removal sensitivity are used **only after** replay for diagnostic reports. They are not decision inputs. Fixed top-5/10 original-winner cohorts and exact-entry matching expose both lost trends and new losses; absence of a matching original entry is not proof that its entire market move was absent from the new path.

The source parser checks only timestamp of the first 2025+ row and stops before its OHLC suffix. Full-file hashes are opaque byte integrity operations, not feature ingestion. No OHLC 2025+ is parsed, no performance beyond 2024 is evaluated.

Verification: prefix/future-mutation feature equality, incomplete/gapped H1 blocks, original Donchian exclusion, H1 predecessor alignment, LONG/SHORT, first-bar-only A1, A2 reset/window expiration/fourth-bar trigger, adverse gap, Stop-first ordering, pending Open before later Low, missing-next-Open and terminal-open tests. Separate standard-library replay verifies every saved entry, exit, initial/active Stop, trailing count, Gross R, rule decision and raw-signal occupancy event. Numerical tolerance is absolute 1e-8; same event identities and timestamps must match exactly.
