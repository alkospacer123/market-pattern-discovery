# Stage 1 — Perpetual futures dataset audit (pre-2025 only)

Date: 2026-10-08  
Status: **DATA QA PARTIAL PASS / STAGE 1 OPEN**. No strategy tests performed. TRUE OOS 2025+ was **not processed for signals, performance, statistics, or selection**.

## Reproducibility and scope

- Source repository: [alkospacer123/market-pattern-data](https://github.com/alkospacer123/market-pattern-data); inspected `main` at **f8486b446cf3d5f9f3cba6dfec32bdef8fd184c8**.
- Source path: `forever/{SYMBOL}/{SYMBOL}_{TF}.csv`.
- 16 CSV blobs were fetched read-only via GitHub Git blobs. For all row statistics below, the filter is strictly `Datetime < 2025-01-01`; later prices/volume were not analyzed.
- CSV schema observed: `Ticker;Datetime;Open;High;Low;Close;Volume`, semicolon separator, local-looking timestamps with **no documented timezone**. The session timezone and whether timestamps mark bar **start** must still be confirmed from provider/source metadata.
- OHLCV records were checked for parseable numerical fields, monotonic and unique timestamps, `high>=max(open,low,close)`, `low<=min(open,high,close)`, nonpositive volumes, and observed date range.
- Source file Git blob SHAs identify the exact files. Raw data was **not copied into IntradayLab**.

## Source inventory and pre-2025 findings

| Symbol | TF | Source blob SHA (short) | First audited bar | Last audited bar | Rows | Unique calendar dates | Parse/OHLC/duplicate/order/volume violations |
|---|---|---|---|---|---:|---:|---:|
| USDRUBF | M5 | 2b621e1c0aa9 | 2023-01-03 09:00 | 2024-12-30 23:45 | 84613 | 509 | 0 |
| USDRUBF | M15 | 6d4f7691c1c6 | 2023-01-03 09:00 | 2024-12-30 23:45 | 29890 | 509 | 0 |
| USDRUBF | M30 | 2330d3ed0f0c | 2022-04-26 10:00 | 2024-12-30 23:30 | 19768 | 683 | 0 |
| USDRUBF | H1 | e86c75bf49a3 | 2022-04-26 10:00 | 2024-12-30 23:00 | 10058 | 683 | 0 |
| CNYRUBF | M5 | 01d667868daa | 2023-01-03 09:00 | 2024-12-30 23:45 | 81664 | 509 | 0 |
| CNYRUBF | M15 | a5ff61bbdd9b | 2023-01-03 09:00 | 2024-12-30 23:45 | 29633 | 509 | 0 |
| CNYRUBF | M30 | d3013b00e1c8 | 2022-04-26 10:00 | 2024-12-30 23:30 | 19608 | 683 | 0 |
| CNYRUBF | H1 | 23150a3bf728 | 2022-04-26 10:00 | 2024-12-30 23:00 | 10023 | 683 | 0 |
| GLDRUBF | M5 | 4b1f36bce33b | 2023-07-11 10:00 | 2024-12-30 23:45 | 59709 | 380 | 0 |
| GLDRUBF | M15 | 726c9242a025 | 2023-07-11 10:00 | 2024-12-30 23:45 | 22189 | 380 | 0 |
| GLDRUBF | M30 | 1f08e677c407 | 2023-07-11 10:00 | 2024-12-30 23:30 | 11370 | 380 | 0 |
| GLDRUBF | H1 | ee5f325a00d6 | 2023-07-11 10:00 | 2024-12-30 23:00 | 5851 | 380 | 0 |
| IMOEXF | M5 | 41b83b109b17 | 2023-11-14 10:00 | 2024-12-30 23:45 | 44932 | 290 | 0 |
| IMOEXF | M15 | 23d8e0292068 | 2023-11-14 10:00 | 2024-12-30 23:45 | 16593 | 290 | 0 |
| IMOEXF | M30 | b6787cf6f33b | 2023-11-14 10:00 | 2024-12-30 23:30 | 8567 | 290 | 0 |
| IMOEXF | H1 | 774464f4f54f | 2023-11-14 10:00 | 2024-12-30 23:00 | 4398 | 290 | 0 |

Earlier M30/H1 bars for USD/CNY (2022) cannot create pre-2023 M5 trades and must not leak future context; paired coverage begins at the first available M5 bar. Common availability for all four **M5 instruments** starts **2023-11-14**. Do not arbitrarily discard longer histories when analyzing each symbol; determine chronological windows *before* any strategy results.

## Cross-timeframe data consistency

For each higher timeframe, M5 rows were bucketed at minute boundaries 00/15/30 for M15, 00/30 for M30 and top of the hour for H1. Comparison used the observed higher-timeframe timestamp against the M5-bucket's first open, max high, min low, last close and sum volume. **All fully populated M5 buckets matched exactly** by all five OHLCV fields, as follows:

| Symbol | M15 full matched | M30 full matched | H1 full matched |
|---|---:|---:|---:|
| USDRUBF | 26148 | 11618 | 4690 |
| CNYRUBF | 24274 | 10428 | 4049 |
| GLDRUBF | 17210 | 7216 | 2691 |
| IMOEXF | 12982 | 5489 | 2100 |

Not all buckets contain the expected 3/6/12 M5 candles. These are **partial buckets**, not automatically corrupt bars: sparse trading, session boundaries or missing data are possible. No zero-trade M5 bars were created to patch gaps. Do not substitute an assumed uninterrupted schedule for an actual exchange calendar.

**Specific unresolved anomaly:** IMOEXF M15 includes 20 bars with no corresponding M5 bucket, all between **2024-08-16 19:00 and 23:45**, at 15-minute intervals. Cross-check for the same date: IMOEXF M5 stops at **18:45**, M30 at **18:30**, H1 at **18:00**, while M15 alone continues to 23:45. Thus the unexplained evening segment is **isolated to M15** in the source data; do not silently import those extra M15 bars into MTF signals. Across all common IMOEXF M15 buckets, including partial buckets, OHLCV matched; the 20 exceptional M15 bars require investigation before using them for MTF. Preserve source data unmodified. Fail closed for bars with incomplete or inconsistent causality evidence.

The observed working Saturdays **2024-04-27, 2024-11-02 and 2024-12-28** agree with MOEX's official 2024 schedule; they are not bad timestamps. Source: https://www.moex.com/n64121.

## Tick checks and reference contract specification

All **pre-2025 M5** Open/High/Low/Close values were exact multiples of the currently published tick steps (zero mismatched price fields); all M5 timestamps were aligned to five-minute boundaries, and ticker codes matched file names.

| Contract | Tick step | Tick value (RUB) | Lot | Official source |
|---|---:|---:|---:|---|
| USDRUBF | 0.01 | 10 | 1000 | https://www.moex.com/ru/derivatives/perpetual-futures/USDRUBF |
| CNYRUBF | 0.001 | 1 | 1000 | https://www.moex.com/ru/derivatives/perpetual-futures/CNYRUBF |
| GLDRUBF | 0.1 | 0.1 | 1 | https://www.moex.com/ru/derivatives/perpetual-futures/GLDRUBF |
| IMOEXF | 0.5 | 5 | 10 | https://www.moex.com/ru/derivatives/perpetual-futures/IMOEXF |

These are **current reference specifications**, not proof of 2023–24 historical costs, margin, or change-free exchange rules.

## Execution model and remaining Stage 1 gates

1. **Timestamp/calendar:** confirm from source documentation that `Datetime` is Moscow time and the timestamp denotes **opening** of the bar; independently check 2023/2024 MOEX historical sessions, clearing breaks and nontrading intervals. Date consistency alone does not establish this.
2. **VWAP data:** OHLCV enables only an **approximated** session VWAP, e.g. `sum(((H+L+C)/3) * Volume) / sum(Volume)`. No transaction-level true VWAP or real bid/ask data is present. Document volume definition and anchored session/clearing resets.
3. **M5 fill limits:** completed M5 signals execute no earlier than the next available market opportunity. A stop and target both touched within one M5 candle have unknown ordering. Use explicitly conservative ordering/ambiguity reporting. **Do not invent M1 or tick-level precision.**
4. **Costs:** separately model current/historical relevant MOEX maker/taker fees, account-specific FINAM commission, trading spread, slippage, passive nonfill, lot/margin limits and fee stress. Do **not** import TradingSystemLab C1 or assume a broker tariff for a not-yet-opened new account. On 2026-06-26 FINAM published a *specific* FreeTrade tariff change to 0.03% of derivatives transaction notional (effective 2026-07-13); the future account's actual tariff is **unknown**. Source: https://www.finam.ru/publications/item/opublikovan-prikaz-ob-utverzhdenii-reglamenta-brokerskogo-obsluzhivaniya-v-redaktsii-2607-20260626-1108/ . MOEX tariff explanation: https://www.moex.com/a90.
5. **Perpetual funding:** MOEX explains that daily funding is reflected at clearing **23:50–00:30**, and does not apply to positions closed before that clearing. Explicitly define forced-flat timing and failure-to-flatten scenarios; if any holding crosses funding, account for funding, and where relevant, dividend adjustments. Source: https://www.moex.com/ru/derivatives/perpetual-futures .
6. **Research split:** define usable pre-2025 development/optimization/WF windows after this audit; historical coverage is shorter for GLDRUBF and particularly IMOEXF. Holdout 2025+ remains untouched until separately authorized TRUE OOS. Do not use post-2024 prices/volumes for parameter choice or cross-validation.

### Verdict

**Pre-2025 schema/basic price integrity: PASS. Full Stage 1 dataset/execution specification: NOT YET PASS.** The unresolved IMOEXF M15 evening segment, timestamp meaning, schedule validity, account-specific cost assumptions and robust M5 fill policy must be closed or explicitly bounded before Baseline is authorized.

This is a data audit only: **0 strategy backtests, 0 portfolio runs, 0 real orders**, no change to market-pattern-data or TradingSystemLab.
