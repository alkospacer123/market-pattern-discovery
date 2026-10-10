# ORB FALSE-BREAK FADE — Stage 2 v2 corrective retest

**STATUS: V2 CODE/FILTER FREEZE COMPLETE; HISTORICAL M5 REPLAY AND NEW TEST RUN NOT VERIFIED.**

## Independent investigation of prior PR #463

Frozen v1 remains exactly as committed: strict BASE 336 reclaim signals and 306 UNKNOWN_POSITION_BLOCK; ATR14 unready for 264 of 336 signals; M15 direction rejected 270 signals; D had only four modeled entries. The original strict backtest, trade ledger, configuration, report, and daywise-v1 diagnostic are unchanged.

V2 config was frozen as `IntradayLab/config/stage2_orb_false_break_fade_m5_v2_research.json` at commit `6843dbf8037a9df6eae6f88e8d1301c9f60e24bd` BEFORE any new v2 replay. V2 is **exploratory using the already-investigated 2023 dataset**, NOT untouched data validation and NOT evidence for Stage 3/WF.

## Explicit corrections; no parameter optimization

1. **UNKNOWN:** maintain original fail-closed trading model per day. For research only, start each *later* trading day independently from explicitly UNVERIFIED assumed flat. Unknown exposure in previous day remains unresolved forever in the original safety ledger, and each later conditional day/trade carries an assumption flag. All full-period account PF/Net/DD remain null.
2. **ATR14 (B/D):** same period and 0.30*ATR threshold as v1; compute 14 true ranges from actual completed M5 observations across the accessible historical 2023 prefix. Include out-of-window bars only for historical warmup; never create an order outside approved intraday windows. For nonconsecutive bars, TR=High-Low, not overnight gap against a distant close. Use only candles completed by sweep close. Do not insert synthetic bars.
3. **MTF (C/D):** latest exact completed M15 computed causally from raw M5. For SHORT veto only if latest completed M15 Close is beyond OR_HIGH; for LONG veto only if below OR_LOW. Missing context is explicitly NEUTRAL (allowed, counted), not a fabricated higher bar. No arbitrary M15 candle-color agreement with fade direction.
4. **Cost/Stop:** keep entry, structural Stop, 1.5 gross R Take, 60min hold, historical C1 and same-fill C2 unchanged. Add diagnostic risk bands <=2 ticks, >2<=5 ticks, >5 ticks and cost-to-risk ratio, no after-results hard threshold.
5. **Coverage:** all available 2023 M5, exactly four instruments. Source rows and known missing slots are reported, never backfilled. No M1, no 2024 WF, no 2025+ TRUE OOS.
6. **A baseline control:** A v2 must have byte-for-byte-equivalent economic identity (signals and modeled trade fields) to v1 DAYWISE research, not necessarily to v1 strict (which is permanently blocked after UNKNOWN).

## Run in the existing Codex Cloud PR #463 branch

```bash
git fetch origin main
python -m unittest discover -s IntradayLab/tests -v
python IntradayLab/tools/run_orb_false_break_fade_daywise.py --data-root /workspace/market-pattern-data
python IntradayLab/tools/run_orb_false_break_fade_v2.py --data-root /workspace/market-pattern-data
```

Adjust only the actual local path to the CLEAN pinned `market-pattern-data@f8486b446cf3d5f9f3cba6dfec32bdef8fd184c8` checkout; do not change any strategy threshold or research date.

The scripts must execute against genuine data before claiming results. Check 16 scenarios, 192 monthly rows, 4×12 = 48 architecture-by-month slices, fill-ledger and independent oracle, C1/C2, technical correctness, and strict-v1 frozen files. Commit NEW resulting artifacts under `IntradayLab/results/stage2_orb_false_break_fade_m5_v2_research/` only. Output numbers in the Codex completion summary and PR description, clearly labeled counterfactual daywise diagnostic. No claim of annual portfolio performance or actual fill.

Report historical `v1 strict` separately from `v1 daywise` and `v2 daywise` — **never attribute changes caused by both assumption reset and feature modifications to ATR/MTF alone.**

If tests or independent checks fail, fix code/tests without cherry-picking P&L; rerun checks, preserve detailed correction history. Stop at Draft PR #463, no merge or next strategy. Protected `TradingSystemLab/` and all other project trees must remain untouched.

The v2 mechanism was designed AFTER seeing v1's 2023 statistics. Thus even a strong v2 result is hypothesis-generating in-sample evidence, not out-of-sample robustness.
