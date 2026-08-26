# Research safety contract

This repository is governed by **ZERO LOOK-AHEAD**. No target leakage is
permitted: information may be used only after it became observable. In
particular, higher-timeframe alignment is causal and an M5 candle is available
only after it closes (an M5 close at 10:15 is unavailable at 10:14).

Day and session boundaries must be explicit. Future rolling features reset at
the trading-day boundary unless their name and documentation explicitly say
that they cross days. Processing, ordering, and tie-breaking must be
deterministic and reproducible.

Development and out-of-sample data are strictly separated. Calendar year 2025
is locked TRUE OOS: it must not be read during ingestion, feature engineering,
discovery, optimization, or strategy selection. Never optimize on TRUE OOS.

Future backtests must include configurable transaction costs and slippage.
Never chase profit factor (PF), search parameters to inflate it, or omit costs.
Source market data is read-only and must never be copied into this repository.

