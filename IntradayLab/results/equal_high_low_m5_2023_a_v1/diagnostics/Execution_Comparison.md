# ENTRY_CLOSE_ORACLE vs ENTRY_NEXT_OPEN

**Oracle is an idealized diagnostic. It never contributes to Baseline status or economic PASS.**

Both scenarios use the same completed signals and structural Stop/limits. Oracle uses signal Close; the trade ledger uses the immediately next Open. Each has its own position occupancy and UNKNOWN path. Entry-bar Take is disabled in both. Prices/Net are never pooled across instruments.

| Instrument | Next fills | Next CLOSED | Next UNKNOWN | Oracle fills | Oracle CLOSED | Oracle UNKNOWN | Next Net R | Oracle diagnostic Net R |
|---|---|---|---|---|---|---|---|---|
| USDRUBF | 237 | 235 | 4 | 251 | 249 | 2 | -81.066667 | -84.700000 |
| CNYRUBF | 297 | 234 | 111 | 339 | 270 | 69 | -138.516667 | -184.383333 |
| GLDRUBF | 12 | 9 | 10 | 12 | 10 | 2 | 18.200000 | 2.866667 |
| IMOEXF | 16 | 13 | 6 | 27 | 23 | 4 | -11.316667 | -16.650000 |

Full paired directional candidates, refused entries and conditional outcomes: entry_comparison.csv. Oracle profits are hypothetical, and cannot rescue a failed NEXT_OPEN Baseline.
