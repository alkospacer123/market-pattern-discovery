# M30 Baseline Research

H1-only methodology; frozen H1 candidates on full 2023–2024 M30 data.

| Strategy | Trades | PF | Expectancy R | Net R | Max DD R |
|---|---:|---:|---:|---:|---:|
| T2 | 178 | 1.4875514967448944 | 0.22257128076651778 | 39.617687976440166 | -15.0847664713036 |
| T3 | 235 | 2.002689330888746 | 0.425920854548717 | 100.09140081894849 | -17.864697983339333 |

T2 ran directly on M30. T3 used causal non-overlapping four-M30 context via DataLoader.h4_from_h1 semantics.
H1 C1: one tick per side; no additional slippage. No optimization, ranking, or selection.

PHASE_M30_BASELINE_COMPLETE
