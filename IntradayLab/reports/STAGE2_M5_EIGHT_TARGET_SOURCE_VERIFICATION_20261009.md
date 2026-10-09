# Stage 2 M5: primary-CSV check of eight unresolved entry targets (2026-10-09)

**Verdict:** `STAGE2_M5_BASELINE_NEEDS_FIX_RESEARCH_COMPLETENESS`. This is source-data evidence, **not** an execution fill/flat proof, profitability PASS, rerun, parameter revision, or authority to merge #443/#444/#445.

## Immutable authorities and scope

- Data repository: `alkospacer123/market-pattern-data` at `f8486b446cf3d5f9f3cba6dfec32bdef8fd184c8`; only **2023** rows were used in the M5/M15 arithmetic.
- Execution under review: unmerged PR #443, `0da11cf86169d5cedf3386549ebe244ca5204fd0`, `IntradayLab/tools/m5_baseline.py`; separate draft audit PR #445 (`9b404949767356a8b58ca25758d99dfce014f482`).
- M5 blob IDs: USD `2b621e1c0aa9a84838d95d4c139257889b6f825e`; CNY `01d667868daaa5610cc8794bf90fe0f276e33686`; GLD `4b1f36bce33b0eeb684edb04f9faf51a636f240d`; IMOEXF `41b83b109b177d4522e53486950104845d357d99`.
- M15 blob IDs: USD `6d4f7691c1c6bfbad59b62a6f5d613a4ed1e984e`; CNY `a5ff61bbdd9bb6659a0f4fea7141b04b5e8bc35e`; GLD `726c9242a025e75de4d0e93a2c215cc2778b9a9`; IMOEXF `23d8e02920684a1a55e50b222271faaa81be5120`.
- Path template: `forever/{SYMBOL}/{SYMBOL}_M5.csv` and `_M15.csv`. Fields: `Ticker;Datetime;Open;High;Low;Close;Volume`. Timestamps are read as FINAM-exported **MSK bar-start labels**, not shifted to UTC.
- Source row counts for 2023 M5: USD 42,576; CNY 39,362; GLD 18,428; IMOEXF 4,429 (total 104,795); consistent with frozen PR #443 input manifest. This review did not calculate any 2024/2025+ trading metrics.
- **Source-access limitation:** GitHub's large-file Contents fetch transmitted complete multi-year CSV payloads to the inspection tool, unlike PR #443's prefix-budget reader. Only rows tagged 2023 were selected for these M5/M15 checks; no 2024/2025+ strategy metrics, signals, selection or economic results were computed. This independent inspection must NOT claim that future-year bytes were physically unread.

## Direct, exact-time verification

The following **eight exact 2023 M5 timestamps have NO physical row** in their respective source CSV. Both adjacent rows exist (unless noted). Corresponding M15 volumes equal the sum of only the existing M5 volumes in their 15-minute slot; M15 high/low also equal the extrema of the available M5 sub-bars.

| Strategy | Instrument | Missing M5 start (MSK 2023) | Immediate previous M5 | Immediate next M5 | Covering M15 start | M15 volume | Existing M5 volume sum | Delta |
|:--|:--|:--|:--|:--|:--|--:|--:|--:|
| VWAP | USDRUBF | 02-02 15:40 | 15:35 | 15:45 | 15:30 | 48 | 48 | 0 |
| VWAP | CNYRUBF | 01-06 17:15 | 17:05 | 17:25 | 17:15 | 131 | 131 | 0 |
| VWAP | GLDRUBF | 08-17 16:00 | 15:55 | 16:05 | 16:00 | 18 | 18 | 0 |
| VWAP | IMOEXF | 11-30 17:20 | 17:15 | 17:25 | 17:15 | 14 | 14 | 0 |
| Momentum | USDRUBF | 02-03 16:15 | 16:10 | 16:20 | 16:15 | 227 | 227 | 0 |
| Momentum | CNYRUBF | 01-19 15:25 | 15:20 | 15:30 | 15:15 | 346 | 346 | 0 |
| Momentum | GLDRUBF | 07-12 11:40 | 11:35 | 11:55 | 11:30 | 57 | 57 | 0 |
| Momentum | IMOEXF | 11-15 16:25 | 16:20 | 16:30 | 16:15 | 18 | 18 | 0 |

Additional missing sub-bars within these local M15 windows: CNY 01-06 17:10 and 17:20; GLD 07-12 11:45 and 11:50. M15 aggregate volumes in these surrounding windows likewise equal existing M5 volume sums. Neighboring valid 5-minute timestamps and nonempty volumes make a constant timezone offset or erroneous local-time parser an implausible explanation. The target windows fall inside the frozen nominal daytime windows (10:00–14:00; 14:05–18:50), not at the standard noon clearing boundary.

**Supported inference:** in all eight corresponding M15 aggregates, there is no residual reported volume or high/low excursion requiring an unrepresented M5 trade. This strongly supports **no recorded trades in these absent 5-minute slots**, rather than a CSV filter silently discarding recorded OHLCV. However both timeframes come from the same FINAM export: these are **not** an independent exchange trade tape, historical order book, or broker order ACK/fill report, and their agreement alone cannot certify that a hypothetical submitted order had no execution/counterfactual liquidity.

## Why 93.16% of signals are blocked, and why year statistics are incomplete

- In each of eight standalone strategy/instrument runs, a **valid precommitted order** was submitted for the strictly-later M5 target; the source OHLCV for that target is absent. `unknown_entries.csv` in PR #443 identifies the eight exact planned targets.
- PR #443 `Replay.missing_entry_target()` (approx. lines 230–259) assigns `UNRESOLVED_POSSIBLE_ENTRY_FILL`, keeps price, filled quantity, residual exposure and P&L as unknown, and requests cancellation too late to establish past nonfill.
- `Replay.decision()` (approx. lines 389–399) blocks all subsequent signals for that run while `unknown_entry` remains latched. There is **no independent broker order/fill ledger to release it**. By 2023 end: 7,279 / 7,813 signals blocked (93.16%); 6,032 otherwise pre-known eligible opportunities blocked. This explains zero later `MODELLED` entries; it does NOT demonstrate an absence of signals after January/February.
- Scheduled target chronology matches the source and model: signal bar-start +10 min observation/ready, target first M5 strictly later (nominal +15), missing target recognized when its OHLCV would have been observed at target+10. Known gaps preceding two targets do not establish that a timely cancellation arrived before any possible fill.
- A missing OHLCV slot is **not proof of hypothetical order nonfill**. Never rewrite canonical unknowns as `NONFILL`, retroactively set FLAT, splice independent trade sequences into a continuous equity curve or publish full-year PF. Carry `INCOMPLETE` / null unresolved economic metrics until a separate justified execution model with versioned assumptions or independent reconciliations is available.

## Separate verified boundary-timing defect (not the cause of eight missing M5 records)

Frozen manifest specifies: issue boundary close at B−20, confirm FLAT by B−10, OHLCV available at t+10. In PR #443 `close_request()`, a request issued at B−20 goes to `next_slot(ready)` = **B−15**, whose bar observation occurs at **B−5**. The first confirmation therefore arrives **five minutes after the B−10 target**. This is an execution-model inconsistency, NOT a reason to corrupt unchanged v1 results or to infer earlier confirmation. Correct only as a separately identified, causally tested versioned execution amendment; no stealth change to the frozen manifest.

## Next bounded Stage 2 decision

1. Retain source M5 CSV, frozen v1 manifest, PR #443 canonical results, unknown position latch, and research NEEDS FIX. No 2024 WF or 2025+ TRUE OOS selection.
2. Prefer genuinely independent 2023 historical exchange trade prints, bid/ask/order-book snapshots, venue session/no-trade reports or order-specific broker fills (if available) to classify unobserved execution feasibility. Cross-timeframe FINAM bars alone do not provide a broker execution verdict.
3. Any explicit `zero reported tape volume implies conditional NONFILL` counterfactual model must be **separately versioned and disclosed as a different simulation assumption**, never silently applied to v1 and never called a verified historical fill ledger.
4. Before relying on any annual strategy PF, correct B−20/B−10 causality as a separately versioned, frozen amendment with synthetic boundaries and time-delivery tests; rerun only 2023 and preserve incomplete cases wherever execution uncertainty remains.
5. Keep VWAP and Momentum, original ticks/C1, parameters and ROADMAP stage order unchanged pending justified quality gates. Do not mix with TradingSystemLab/ or BBW/.

**Audit scope:** Only a documentation report was added by this PR; no strategy/backtester, configs, original files or results were changed. No merges authorized.
