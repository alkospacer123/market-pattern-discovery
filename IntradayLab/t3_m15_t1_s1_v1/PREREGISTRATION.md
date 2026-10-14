# Preregistration: T3_M15_T1_S1_COMBINED_V1

GROSS_ONLY / COSTS_DEFERRED / NOT_LIVE_READY

2023–2024: DEVELOPMENT_EXPOSED.

FIRST GATE PASS is required before this specification. The sole new experiment combines T1_CORE_HOURS_ENTRY (#499) with S1_TRAIL_AFTER_1R (#496), unchanged, for two fixed configurations. All feature, signal, gap, holding and re-entry conventions are frozen; no additional mechanisms, thresholds, hours or parameter choices are permitted. BASELINE trailing 3.0 ATR, OPTIMIZED trailing 3.5 ATR; both initial Stop 2 ATR, EMA75, slope5, H1 ADX14>20, ATR14 and ATR mean20, prior20 Donchian. The name OPTIMIZED is inherited; no optimization is run.

T1 checks completed signal Close in Moscow, 10:00 inclusive /18:00 exclusive. S1 checks the immutable initial 1R threshold only on completed survived post-entry M15 bars after settling the old Stop. Until then the initial Stop stays fixed. On activation and later bars, original ATR trailing uses all accumulated favorable extrema since entry; the tightened Stop acts from the next actually observed candle. LONG/SHORT are symmetric, Stop never weakens. Entry candle extrema and exit candle extrema cannot activate or ratchet a Stop. Holding across sessions/year is unchanged.

All code, independent implementation, causal fixtures, report and byte-repeat routines, exact source SHA and evaluation conditions are included in this freeze commit before the first historical COMBINED calculation. Synthetic fixtures may exercise COMBINED before freeze, using no historical result. Mandatory full standalone CONTROL/S1/T1 replays must match all gross common trade fields and OPEN within absolute 1e-8, with CLOSED 741+701, 718+689 and 568+549. New results are forbidden until both benchmark reproduction and fixtures pass and the freeze exists in Git.

The full four-instrument, two-year Gross PF goal is >=2.0; subset success never satisfies it and full PF is not an automatic architecture PASS. Assess COMBINED against CONTROL/T1/S1 simultaneously for Gross R/expectancy, 2024, positive months/worst month/loss runs, CLOSED-R DD, >=2R winner preservation, new occupancy losses, breadth over instruments/directions, top5/top10 and November2024 dependence, duration/frequency/holding. No composite score or parameter search is introduced. Negative results are saved as calculated without rule changes.

The parser stops before any 2025+ OHLC suffix; full-source hashing is opaque integrity checking. Late GLD/IMOEX history is retained without backfill. No raw source files are copied. NO_COVERAGE months are marked and stay in the complete 24-calendar-month denominator. Trade exits are classified by original M15 Close in Moscow; terminal OPEN is excluded from CLOSED metrics. Drawdown uses deterministic exit-time/instrument/trade_id order and cumulative trade R, not portfolio equity.

Two fresh full-process primary replays must compare all generated artifacts by direct bytes and SHA256. Independent scalar indicators/replay and metrics must compare all common trading/journal/report fields. Final Git diff may contain only additions in IntradayLab/t3_m15_t1_s1_v1/. Existing checkout files remain untouched, and commits use a separate index built from verified remote main.

Historical signal-Close entry and Stop pricing remain unverified assumptions. No claim of actual fills, profitability after costs or robot readiness. One Draft PR, Auto-Merge off, no merge, STOP. No numerical Optimization, Robustness, Walk Forward, TRUE OOS or LIVE.
