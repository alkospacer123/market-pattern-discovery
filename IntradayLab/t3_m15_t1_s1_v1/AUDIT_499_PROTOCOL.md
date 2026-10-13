# Independent external audit of PR #499 — FIRST GATE PASS

GROSS_ONLY / COSTS_DEFERRED / NOT_LIVE_READY

2023–2024: DEVELOPMENT_EXPOSED. Historical signal-Close fill remains an unverified assumption.

This new implementation does not import or execute the #499 engine, its metrics, its internal auditor, or any prior executable research. `independent.py` uses Python standard-library parsing, scalar recursive EWM state, forward H1 publication, prior-20 slice extrema and a separate position state machine. `audit_499.py` reads frozen outputs only as comparison targets. The audit author is the current research agent, separate from the authoring session of #499; this is a computational audit, not an independent human review or evidence of live execution.

Remote main is exactly 249a9f58a726416bee9d3efd259a9824d348e292. Pinned M15 source is f8486b446cf3d5f9f3cba6dfec32bdef8fd184c8. All source blobs, opaque full-byte SHA256 values and historical-prefix hashes match #499. Numerical parsing stops before the OHLC suffix of the first 2025+ row. Late GLD/IMOEX starts are preserved; data is not copied into this package.

CONTROL: BASELINE 741 CLOSED +1 OPEN, OPTIMIZED 701 CLOSED +1 OPEN; all gross common fields against #490/#495 and both OPEN files match. T1: 568/549 CLOSED +1 OPEN each. T2: 729/694 CLOSED +1 OPEN each. All original trade, Stop, entry, gap and month-end OPEN fields are compared, including prices, timestamps, immutable initial risk, MAE/MFE, trailing updates, H1 availability/previous context, occupancy and same-Close re-entry.

T1 uses completed signal Close in Europe/Moscow, 10:00 inclusive and 18:00 exclusive. T2 uses the previous actually observed completed bar, strictly greater than 15 minutes, and blocks only the first bar after each observed gap. Missing predecessor is separately classified. Both entry rules leave holding and protective processing active outside permitted entries.

Causality: daily ordinal H1 blocks require four consecutive observed completed M15 bars and publish only at their last Close. Incomplete/gapped blocks are skipped. Recursive H1 indicators and M15 ATR cross sessions; Donchian is prior 20 observed bars excluding the current bar, across sessions, exactly as frozen. Old active Stop is settled first, adverse Open gaps fill at Open, exit-bar favorable OHLC does not enter MFE/activation, and ratcheting applies from the next observed bar. Fixtures cover LONG/SHORT, exact boundaries, UTC, weekends/year transfer, holding, occupancy and prefix invariance. 25 fixtures PASS.

Independently recomputed all gross PF/R/expectancy/CLOSED-R drawdown, all 24 calendar months including pre-start NO_COVERAGE, both years, instruments, LONG/SHORT, November sensitivity, losing month/trade streaks, top5/top10 and values without top winners. Independently reconstructed all entry lineage, lost >=2R winners, new trades/losses, occupancy chronology, entry funnels and holding/frequency diagnostics.

2,580,630 fields compared; zero discrepancies above absolute 1e-8. Exact maxima and per-table counts are in audit_499/AUDIT_RESULT.json; audit_499/DISCREPANCIES.csv has only a header. This PASS authorizes the next preregistration stage under the user's instruction. No combination has been calculated at this gate.

Pre-result freeze e8feb7ac351c9548d61abee0e06462485e852fc1: all seven Python files and specification are byte-identical to merged #499; no result directory at freeze. Pre-variant CONTROL/tests gate precedes final result commit. PR #499 has exactly 60 added files, all inside IntradayLab/t3_m15_session_entry_v1/. Its artifact and frozen-reference inventories are verified from Git objects.

Reproduce: PYTHONDONTWRITEBYTECODE=1 python IntradayLab/t3_m15_t1_s1_v1/audit_499.py --data-root /workspace/market-pattern-data --output IntradayLab/t3_m15_t1_s1_v1/work/audit_fresh

The existing local checkout predates remote main. It is kept untouched. Git objects are fetched/read without materializing older research changes. A separate index inside this package's ignored work directory builds commits on verified remote main; only this new directory is added. No TradingSystemLab, robot, prior research, ROADMAP or market-pattern-data files are modified.
