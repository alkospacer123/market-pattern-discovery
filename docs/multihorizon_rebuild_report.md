# Multi-Horizon Research Engine rebuild report

## Architecture

The production research path is now:

`ResearchCell -> MarketDataLoader -> CausalContextEngine -> features -> KNOWN/UNKNOWN -> evidence-gated PatternEffect -> ResearchIntelligence -> ResearchMemory`

The timeframe registry defines M1, M5, M15, M30, H1, and D1 using the Finam
period values present in the source files. The loader normalizes CNY/CNYRUBF
and Si/USDRUBF into one schema, exposes only the permitted 2026 development
interval, and never writes or resamples source data. Higher-timeframe values
are joined by candle close time with a runtime no-lookahead assertion.

Research profiles describe Scalping, Intraday, and Medium-term spaces without
asserting profitability. Deterministic scheduling covers both symbols and both
KNOWN and unrestricted UNKNOWN tracks. Effects exist only for qualifying,
observed evidence. Research Intelligence converts that evidence into positive,
negative, or unresolved knowledge—not trading rules.

Research attempts and `KnowledgeRecord` objects are canonical JSONL,
append-only, restart-safe, deterministically identified, and idempotent. Legacy
memory files and APIs remain unchanged.

## Principal files

- `src/market_pattern_discovery/data/timeframes.py`: timeframe registry.
- `src/market_pattern_discovery/data/loader.py`: canonical Finam loader.
- `src/market_pattern_discovery/research/cells.py`: profiles, cells, scheduler.
- `src/market_pattern_discovery/features/context.py`: causal context alignment.
- `src/market_pattern_discovery/research/execution.py`: unified tracks/attempts.
- `src/market_pattern_discovery/research/intelligence.py`: effect lifecycle and conclusions.
- `src/market_pattern_discovery/research/memory.py`: persistent attempts and knowledge.
- `src/market_pattern_discovery/orchestration/multihorizon.py`: bounded runner.
- `scripts/run_multihorizon_research.py`: CLI requiring `--cycles`.

## Tests

Focused tests cover strict loading, all six registry entries, profile validation,
deterministic scheduling, close-time causality for M15/H1/D1, shared track data
contracts, unrestricted UNKNOWN dispatch, effect qualification, all three
conclusions, knowledge restart/deduplication, and bounded runner restarts.

The full suite result was **307 passed, 1 environment failure**. The failure is
`test_phase1b_entry_point_launches_from_project_root`: this container returned
I/O error from `ensurepip` while that legacy test created a temporary virtual
environment. All repository test assertions that ran passed.

## Real-data restart smoke

Data root: `/workspace/market-pattern-data` (read-only use). Memory root was an
ephemeral `/tmp/multihorizon-smoke-memory`, not the repository.

1. Process 1: `--cycles 5 --budget 2` completed five bounded cycles, each with
   two planned and two recorded cells. Memory grew from 0 to 10 attempts and 16
   knowledge records.
2. Process 2 restarted against exactly the same memory and ran another
   `--cycles 5 --budget 2`. Memory grew to 20 attempts and 34 knowledge records.
3. There were 20 unique attempt identifiers for 20 attempts (zero duplicates).
4. Persisted coverage included CNY and Si; Scalping, Intraday, and Medium-term;
   M1, M5, M15, M30, H1, and D1; and KNOWN and UNKNOWN.

No 2025 row was exposed, no candle was synthesized, no source file was changed,
and no strategy construction or optimization was performed.

## Verdict

**READY FOR 20-CYCLE VALIDATION**
