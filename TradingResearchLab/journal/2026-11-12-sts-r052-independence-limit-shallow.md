# TRL Journal — R052, 12.11.2026

V20 Shallow/OBV/Inside use different setups but shared trend/EMA environment and common technical dependencies; daily Shallow–Inside PnL correlation 0.098, Shallow–OBV 0.344. Separate accounts provide partial operator isolation, not a hedge against FINAM/market failures.

Frozen 4 variations of the same Shallow: FAST2 851 deals +204191 RUB PF1.814; LONG5 542 +139376 PF1.829; DEEP3 894 +225490 PF1.850; TIGHT3 486 +134604 PF1.848, vs Classic 736 +208507 PF1.961, all in 45k own-account GO Oct TP6. Classic+Deep3+Inside earns +480503 but closed DD19408 versus V20 +381608/DD11775: correlated risk.

Limit price-touch diagnostics: on 1449 baseline trades passive one-tick better than Open touched within entry bar 89.1% N4 /90.5% GLD and over the following four uninterrupted M15 bars before exit 71.5% N4 /73.1% GLD. This is NOT fill probability. Need L2 bid-ask queues, exact timestamps, partial fills and execution costs.

User has decided on future TP6+protect3 in separate LIVE domain; no TRL LIVE change. Decision: NO_NEW_SHALLOW_CORE, INSIDE_DIVERSIFIER, LIMIT_EXECUTION_DATA_REQUIRED, prospective verification. See R052 report.
