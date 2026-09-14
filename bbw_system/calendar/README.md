# Frozen MOEX calendar input

The 03B-2B audit accepts an external, read-only calendar snapshot with
`--calendar PATH`. Calendar files are evidence inputs and **must not** be
constructed from observed bars or weekday assumptions. No market data or
calendar dates are stored in this directory.

The JSON artifact uses schema `bbw.moex-calendar.v1` and contains provenance
fields `artifact_id`, `source_url`, and `retrieved_at`. Its nonempty `days`
array must explicitly provide every field below for every calendar date touched
by the frozen bars:

* `calendar_date` and its exchange-assigned `trading_date`;
* `working_day` and `weekend_session` booleans;
* `special_session` and `shortened_session` booleans;
* `exchange_regime` matching the effective-dated instrument passport;
* `trading_intervals` and `clearing_intervals` as `[start, end]` pairs.

Missing provenance, fields, days, or regime coverage fails closed. In
particular, the loader does not generate holidays, infer working days, or use a
Monday-to-Friday fallback.
