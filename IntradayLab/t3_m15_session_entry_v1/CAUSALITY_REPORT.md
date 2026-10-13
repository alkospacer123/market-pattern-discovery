# Causality contract

**GROSS_ONLY / COSTS_DEFERRED / NOT_LIVE_READY**

- Data pinned at f8486b446cf3d5f9f3cba6dfec32bdef8fd184c8. Only actual 2023–2024
  M15 closes are used, including late GLD/IMOEX starts. Timestamp-first parsers
  stop before first 2025+ OHLC; full SHA reads are opaque integrity checks.
- Existing #490 indicator implementation is read-only. Original daily ordinal H1
  aggregation remains unchanged: four consecutive observed M15 closes, full blocks
  only, timestamp alignment via completed Close. No interpolated gap bars.
- Original ATR, Donchian, EMA, slope and ADX cross days as before; no reset is added.
- T1 uses current completed signal Close in Europe/Moscow. 10:00 allowed;
  18:00 forbidden. It is not an official MOEX session definition.
- T2 uses current and previous actual completed Close, including non-signal bars.
  Gap >15 minutes blocks exactly current entry; next continuous Close allowed.
  Missing previous Close has its own reason. No future timestamp or invented bar.
- All variants replay the original complete chronology independently. Rule failure
  only prevents a new entry; it cannot close a position or change its active Stop.
  Every original signal is evaluated again after the variant's exit/occupancy state.
- Old active Stop first, adverse gap at observed Open, then survived-bar trailing
  ratchet at Close for next bar. Exit-bar favorable extremes excluded from MFE.
  Both LONG and SHORT use the original 2 ATR risk and 3.0/3.5 ATR trailing.
- Protective exit and same-Close re-entry are independent decisions: a new entry
  requires that bar's rule permission. No forced liquidation at session/day/year.
- Logs label protective exits by original exit-bar Close. Open gap execution occurs
  at its recorded Open, and exit_at_open/exit_bar_open_time disclose that distinction.
- Month/year OPEN snapshots use the last actually observed Close before each
  boundary, with no flattening. Terminal OPEN excluded from CLOSED R/PF.
- Observed overnight gap diagnostic: gap >15 minutes and different local dates of
  corresponding source bar Opens (Close minus 15 minutes). This handles a final
  00:00 Close and is not evidence of an official exchange break.
- Winner >=2R, duration, future cross-midnight and November/top-winner exclusions
  are descriptive only, never input to entry selection. Full variant economics
  include newly available entries/losses and lost trends.
- Historical entry at completed signal Close is retained for comparability.
  Real Close-fill execution, tick-safe orders and live profitability are not claimed.
- 2023–2024 development-exposed. No independent WF/OOS, numerical optimization,
  robustness phase, future OHLC, combinations, LIVE or automatic next experiment.

Pre-result fixture tests, CONTROL gate, independently derived record-level audit,
full byte repeats and source/scope SHA checks provide computational evidence.
Same author produced both implementations; external audit remains PENDING.
