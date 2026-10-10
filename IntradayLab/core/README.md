# Independent historical Backtester

`Market Data → Indicators → Strategy → Backtester → Metrics → Reports`.
The core has no imports of candidate strategies, TradingSystemLab or brokerage
runtime. TradingSystemLab was read solely as a structural/methodology reference.

`data_loader.py` checks pinned Git identity and reads only exact, SHA-256-verified
development prefix bytes. Bars carry timezone-aware start labels and an explicit
availability time (`start + duration`). Duplicate/unsorted labels and malformed
numeric schemas fail validation; zero-volume/invalid geometry/grid rows are
diagnosed and cannot act as completed observations. They never provide fallback
prices. For an entry or scheduled exit the Open scalar is checked separately,
without consulting future High/Low/Close/Volume.

`Indicators` receives each actual completed source observation, including
available preceding days and observations outside entry windows. ATR14 is an
infrastructure helper, unused by ORB A BASE. Warm-up never fabricates bars. A
missing adjacent prior Close uses genuine current H-L; previous observed ranges
remain available across sessions. Strategies may choose explicit day/session
features through their own state, without changing shared execution.

Implement the `Strategy` protocol in `models.py`, pass a JSON parameter object
to its constructor, and register the candidate in the runner. The strategy only
receives immutable completed `Bar`/`Context` objects, not a source or future-row
handle. It emits SIGNAL intents with side, past Stop, gross target R and calendar
holding minutes, or reasoned diagnostic events. `begin_day`/`end_day` delimit
candidate state. The common engine supplies waiting, Open entry, dated costs,
one pending/open position, resident protection and intraday scheduled exits.
Simultaneous candidate events are sorted by signal_id, independent of callback
order. Synthetic `TimedStrategy` demonstrates a non-ORB candidate using the
same engine.

Only the explicitly approved M5 clock is implemented: completed signal M5,
then one full waiting M5, then model entry at the next interval Open. Stop-first
and adverse Stop gaps are shared; entry-bar Take is disabled for the frozen
candidate. Holding and session deadlines use exact Open with Stop-gap precedence.
Missing/invalid waiting observations reject before submission. Missing/invalid
entry Open is UNKNOWN possible fill; an unresolved exposed interval is UNKNOWN.
Unknown entry/exit prices and total net remain blank. Known entry cost is retained.

UNKNOWN blocks the current day. Subsequent research days assume FLAT explicitly;
all later trades retain the prior-UNKNOWN flag. This is not brokerage reconciliation
or proof of continuous portfolio equity. Missing-slot discovery is labelled at
the interval end; no missing price is replaced.

The canonical runner creates deterministic CSV/JSON/Markdown, per-instrument
price-unit PF and R-unit PF, closed-only diagnostics and null annual metrics
when coverage/outcomes are incomplete. It does not pool incompatible instrument
price units into a portfolio. `audit_canonical_baseline.py` uses its own source
reader, candidate slices, trade paths and metrics; it imports none of this core.

Reproduce from the repository root:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest IntradayLab.tests.test_universal_backtester IntradayLab.tests.test_canonical_audit -v
PYTHONDONTWRITEBYTECODE=1 python3 IntradayLab/tools/run_canonical_baseline.py --data-root /workspace/market-pattern-data --output IntradayLab/work/replay
PYTHONDONTWRITEBYTECODE=1 python3 IntradayLab/tools/audit_canonical_baseline.py --data-root /workspace/market-pattern-data --output IntradayLab/work/replay
```

Use the pinned, clean data checkout. No 2024/WF or 2025+/TRUE OOS data is read.
The result directory, including UNKNOWN diagnostics, is separate from every
historical frozen study. See `../results/orb_a_base_2023_canonical_v1/`.
