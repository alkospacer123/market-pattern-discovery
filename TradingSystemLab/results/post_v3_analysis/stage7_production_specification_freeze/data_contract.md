# Data contract

Input is strictly increasing, unique, timezone-aware Europe/Moscow H1 close timestamps with finite positive Open, High, Low, Close and valid OHLC geometry. A bar is usable only after close. Duplicate, conflicting, missing/stale, or non-monotonic data blocks new entries; accepted historical behavior does not synthesize missing bars. Context consists of complete same-local-day groups of four H1 bars and never crosses a day.

Warm-up is validity-based: ATR14, shifted Donchian20, context EMA100 (plus source-computed EMA50/EMA200), EMA100 slope lookback 5, ADX14, context ATR14 and ATRMean20 must all be non-null. Because pandas EWM indicators seed causally, no invented fixed bar count replaces this rule. No signal is permitted until every field used by `regime` and `generate_signal` is available.
