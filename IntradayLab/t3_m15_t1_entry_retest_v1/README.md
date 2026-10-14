# T1 / ATR trail 3.5 / N4 — independent entry retest v1

Exactly `T1_SIGNAL_CLOSE_TRAIL_3p5` (IDEALIZED_SIGNAL_CLOSE) and
`T1_NEXT_OPEN_TRAIL_3p5` (CAUSAL_NEXT_OPEN). No optimization or other models.
Russian findings: [results/REPORT_RU.md](results/REPORT_RU.md).

Use Python 3.11/3.12 with the pinned requirements, pandas 2.2.3 and numpy 2.3.5.
Only these packages and the standard library are needed. Scratch files go outside
the repository. Original source M15 is never copied or changed.

```bash
python -m pip install -r IntradayLab/t3_m15_t1_entry_retest_v1/requirements.txt
git fetch origin main
git fetch origin refs/pull/514/head:refs/remotes/origin/pr514 refs/pull/517/head:refs/remotes/origin/pr517
git -C /workspace/market-pattern-data rev-parse HEAD
python IntradayLab/t3_m15_t1_entry_retest_v1/test_causal.py
python IntradayLab/t3_m15_t1_entry_retest_v1/repeat.py --data-root /workspace/market-pattern-data --scratch /workspace/work
```

Data HEAD must be `f8486b446cf3d5f9f3cba6dfec32bdef8fd184c8` and clean.
Run from a complete clone, retaining code-freeze and source commits. Both PR
references are pinned by full SHA in SPEC.json; no live branch code is imported.
All source bars precede 14 October 2026, so the study includes every available bar.
The older PR514 cutoff (13 October) yields the same data interval.

For one full run into a fresh scratch directory:

```bash
python IntradayLab/t3_m15_t1_entry_retest_v1/run.py --data-root /workspace/market-pattern-data --output /workspace/work/t1-single-reproduction
```

`run.py` checks the immutable new-code freeze, runs causal tests, verifies raw
source hashes, computes new primary signals and both position trajectories,
reopens source in the independent scalar verifier, verifies reporting arithmetic,
writes the completion marker, and only then opens selected published journals.
It does not execute any other strategy or import a frozen trading engine.

`repeat.py` runs the entire procedure three times in fresh processes. It compares
all output files by direct bytes and SHA-256, including gzip (mtime=0), audits,
source receipts and the Russian report. Existing committed results are compared
to fresh output without changing them. `repeatability.json` and FULL_RUN_LOG.txt
record the complete gate. SHA256SUMS covers all deliverable files except itself;
Git commits anchor the full versioned tree.

Main journals: `results/signal_close_trades.csv`, `results/next_open_trades.csv`.
All signal decisions and stop transitions are retained in compressed CSV. Reports
use exit-candle Close timestamps and the frozen tie order, with `math.fsum` and
1e-8 tolerances. NO_COVERAGE is blank, not a zero-return observation. Source-gap
slots include scheduled closures; no exchange calendar is inferred.

The user explicitly authorizes historical 2023–2026 replication and gross-only
reporting and prohibits FINAM cost simulation; these instructions take precedence
over the general AGENTS.md cost/OOS-development defaults. No strategy discovery,
selection or new TRUE OOS claim is performed. TradingSystemLab, production H1,
server tasks, source data and old journals stay outside the diff. One Draft PR,
no merge/auto-merge, no LIVE, STOP for the user's separate decision.
