# Phase 3.1 — Bounded Optimization Framework

This directory contains the deterministic compatibility artifacts for the
bounded optimization framework. The framework separates experiment definition,
finite parameter spaces, explicit constraints, validation, execution, and
text-only artifact writing from the frozen strategy implementations.

This is infrastructure **for** future optimization, not an optimization run.
Phase 3.1 executes only the frozen unified baseline, delegates metrics to the
Phase 2 unified metrics output, and performs no parameter search or strategy
selection. Every candidate value in a future experiment must be enumerated in a
finite typed list, and the runner blocks a grid larger than 5,000 combinations
before any strategy execution.

There is no “best config”: an objective, fitness function, leaderboard, and
winner selection are intentionally outside this framework. TRUE OOS data from
2025 onward remains hard-blocked.

The next planned stage is **Phase 3.2 — T2 bounded optimization**.
