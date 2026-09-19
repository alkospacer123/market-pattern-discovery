# D1 Baseline Research

Frozen H1 candidates on causal D1 execution candles over full 2023–2024 development data.

| Strategy | Trades | PF | Expectancy R | Net R | Max DD R |
|---|---:|---:|---:|---:|---:|
| T2 | 5 | 0.15481193472217664 | -0.5860820992494725 | -2.9304104962473625 | -3.4671697538512944 |
| T3 | 4 | 0.10221688504312515 | -0.37138898566927836 | -1.4855559426771134 | -1.4855559426771134 |

T2 ran directly on D1. T3 used four completed D1 bars per causal 4D context candle.
H1 C1: one tick per side; no additional slippage. No optimization, ranking, or selection.

## Historical Phase 7.1 parity

- T2 CNYRUBF: standalone 2, historical 2 — MATCH
- T2 USDRUBF: standalone 3, historical 3 — MATCH
- T3 CNYRUBF: standalone 2, historical 2 — MATCH
- T3 USDRUBF: standalone 2, historical 2 — MATCH

PHASE_D1_BASELINE_COMPLETE
