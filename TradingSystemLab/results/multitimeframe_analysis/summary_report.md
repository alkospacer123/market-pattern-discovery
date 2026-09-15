# Phase 7.2 Multi-Timeframe Analysis

Analytical classification of Phase 7.1 saved trades only. No market data, strategy execution, parameter search, ranking, validation, or TRUE OOS was used.

## Decisions

| Strategy | Instrument | Timeframe | Status | Reason |
|---|---|---|---|---|
| T2 | USDRUBF | M30 | ROBUST_TIMEFRAME_CANDIDATE | All fixed trade-count, expectancy, net-R, drawdown, concentration, year, direction, and instrument gates passed. |
| T2 | CNYRUBF | M30 | RESEARCH_ONLY | 2023/2024 results are not both positive; LONG/SHORT results are not both positive |
| T2 | USDRUBF | H1 | RESEARCH_ONLY | high or unavailable top-5 concentration; LONG/SHORT results are not both positive |
| T2 | CNYRUBF | H1 | ROBUST_TIMEFRAME_CANDIDATE | All fixed trade-count, expectancy, net-R, drawdown, concentration, year, direction, and instrument gates passed. |
| T2 | USDRUBF | H4 | RESEARCH_ONLY | insufficient trade count; high or unavailable top-5 concentration |
| T2 | CNYRUBF | H4 | RESEARCH_ONLY | insufficient trade count; high or unavailable top-5 concentration; 2023/2024 results are not both positive; LONG/SHORT results are not both positive |
| T2 | USDRUBF | D1 | RESEARCH_ONLY | insufficient trade count; non-positive expectancy; non-positive net R; high or unavailable top-5 concentration; 2023/2024 results are not both positive; LONG/SHORT results are not both positive |
| T2 | CNYRUBF | D1 | RESEARCH_ONLY | insufficient trade count; high or unavailable top-5 concentration; 2023/2024 results are not both positive; LONG/SHORT results are not both positive; paired instrument result is not positive |
| T3 | USDRUBF | M30 | ROBUST_TIMEFRAME_CANDIDATE | All fixed trade-count, expectancy, net-R, drawdown, concentration, year, direction, and instrument gates passed. |
| T3 | CNYRUBF | M30 | ROBUST_TIMEFRAME_CANDIDATE | All fixed trade-count, expectancy, net-R, drawdown, concentration, year, direction, and instrument gates passed. |
| T3 | USDRUBF | H1 | ROBUST_TIMEFRAME_CANDIDATE | All fixed trade-count, expectancy, net-R, drawdown, concentration, year, direction, and instrument gates passed. |
| T3 | CNYRUBF | H1 | ROBUST_TIMEFRAME_CANDIDATE | All fixed trade-count, expectancy, net-R, drawdown, concentration, year, direction, and instrument gates passed. |
| T3 | USDRUBF | H4 | RESEARCH_ONLY | insufficient trade count; high or unavailable top-5 concentration; LONG/SHORT results are not both positive |
| T3 | CNYRUBF | H4 | RESEARCH_ONLY | insufficient trade count; high or unavailable top-5 concentration; 2023/2024 results are not both positive; LONG/SHORT results are not both positive |
| T3 | USDRUBF | D1 | RESEARCH_ONLY | insufficient trade count; non-positive expectancy; non-positive net R; high or unavailable top-5 concentration; 2023/2024 results are not both positive; LONG/SHORT results are not both positive; paired instrument result is not positive |
| T3 | CNYRUBF | D1 | RESEARCH_ONLY | insufficient trade count; non-positive expectancy; non-positive net R; high or unavailable top-5 concentration; 2023/2024 results are not both positive; LONG/SHORT results are not both positive; paired instrument result is not positive |


## Limitations

All results describe 2023–2024 development artifacts. A candidate status is permission for future research, not strategy selection.

PHASE_7_2_MULTITIMEFRAME_ANALYSIS_COMPLETE
