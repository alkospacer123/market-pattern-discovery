# BBW canonical data contract v1

This layer performs **data diagnostics only** and never reads locked 2025 data for research or optimization. Source files remain read-only.

## Schema

Required columns, in canonical order, are `timestamp`, `open`, `high`, `low`, `close`, `volume`, `symbol`, and `timeframe`. Optional columns are `contract`, `open_interest`, `source`, `trading_date`, `roll_flag`, and `session_id`; normalization may retain `source_timestamp`, `status`, and `reason_code` for traceability.

`timestamp` is the bar close timestamp. It must be timezone-aware in the explicitly configured exchange timezone, monotonic, and unique within symbol/timeframe. Naive source timestamps require a verified `source_timezone`; no timezone is inferred. M5 data becomes observable only at its close.

OHLC must be numeric and non-null for tradable bars, volume must be non-negative, `high >= max(open, close, low)`, and `low <= min(open, close, high)`. Status is one of `RAW`, `VALID`, `EXCLUDED`, `ERROR`. Excluded/error rows are retained with a reason: `WEEKEND`, `OUTSIDE_SESSION`, `DUPLICATE`, `INVALID_OHLC`, `HOLIDAY`, `DATA_GAP`, `ROLLOVER`, or `OTHER`.

## Sessions and calendars

Weekends are excluded before any BBW input can be produced. Session start/end, anchor and breaks are passport inputs. Holidays are never inferred from weekdays. `holiday_dates`, `shortened_session_dates`, and `special_session_dates` are explicit external calendar inputs. Trading-day coverage resets by `trading_date`.

## Futures continuity

`series_type` is exactly one of `individual_contract`, `continuous_unadjusted`, `continuous_adjusted`, or `unknown`, and requires evidence rather than filename inference. `roll_flag` is preserved. Price jumps are diagnostics only and never automatically declared rollovers. Default `reject_crossing_setup` blocks windows containing a marked roll; unknown continuity remains a baseline blocker. `allow_adjusted_series` is valid only for verified adjusted data; `individual_contract_only` rejects all other types.

## Reproducibility

Every normalized dataset manifest records both hashes, absolute source path, symbol/TF, bounds, raw/valid/excluded/error counts, and normalization version. Ordering and CSV serialization are deterministic. Normalized outputs and raw market data are Git-ignored.
