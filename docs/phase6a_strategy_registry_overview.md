# Strategy Candidate Registry v1.0

The tracked JSON registry contains 59 preregistered, architecture-only `KNOWN`
families. JSON was selected because the project already validates JSON without a
YAML parser. Every family has three explicitly separated parameter groups,
small interpretable domains, objective closed-candle language, risks, status,
and a canonical SHA-256 fingerprint. `promoted` and `frozen` are deliberately
unused. Round grids preserve CNYRUBF `0.001/0.05` and USDRUBF/Si `0.01/0.10`
tick/step semantics. These entries are hypotheses, not results.

Enumeration must call `estimate_candidates` before computation. Its stable
family ordering reports parameter, instrument, timeframe, and total counts and
hard-fails per-family or registry limits.
