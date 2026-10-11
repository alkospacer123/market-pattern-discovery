# Independent audit — Optimization Level Rejection M5 2023

Status: **PASS**. A separately tasked auditor implemented a standard-library-only raw-M5 oracle.

The oracle independently rebuilds all 72 configurations × 3 instruments, immediate six-bar levels, directional cooldown, confirmed signals, waiting, scalar-Open admission, structural Stop, full-net C1 Take, Stop-first, no entry-bar Take, deadlines, SKIP and EXCLUDED paths. Exact CLOSED-only metrics, all 12 months, both directions, coverage, parameter neighbors, every failed gate and fixed ranking are checked.

Checked field counts: {"accepted_ID_checks": 72211, "baseline_comparison_fields": 7648, "baseline_oracle_fields": 46795, "baseline_replay_fields": 554431, "baseline_report_fields": 24, "baseline_signal_oracle_fields": 283084, "common_baseline_fields": 45840, "common_metric_fields": 6365, "coverage_fields": 877824, "data_gap_skips_fields": 36554, "data_quality_exclusions_fields": 232456, "day_fields": 637056, "direction_fields": 12096, "funnel_fields": 2592, "index_fields": 1512, "metric_fields": 11232, "monthly_fields": 90720, "neighbor_fields": 5160, "provenance_fields": 24, "rejected_nonfill_fields": 15605418, "selection_checks": 30, "signals_fields": 19830210, "trades_fields": 3440817}.

Protected prior files and committed freeze dependencies are byte checked. Original Baseline engine replay matches its frozen ledgers; independent raw paths verify original confirmed CLOSED and common V2 closures. Policy differences remain explicit. Zero 2024+ candle bytes read; annual account returns are unavailable. No external human reviewer signoff is claimed.
