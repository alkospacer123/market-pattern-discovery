# Stage 5 — Separate structural validation

Status: **OPEN — comparator-only checkpoint**.

The initial fail-closed gate was intentional. The committed normalized ledgers
expose final MAE and MFE, but not the ordered completed bars at which a frozen
trigger first became observable. Using those extrema to rewrite outcomes would
introduce look-ahead. The runner therefore authenticates Stage 4, both strategy
sources, and the external market-data repository at its frozen commit before
any market-data byte is opened.

The independent-authentication checkpoint followed that initial checkpoint and
preserved its history. Its auditor owns a deliberately duplicated
implementation and does not import the Stage 5 runner or execution adapter.

The canonical-comparator reconstruction checkpoint delegates to the actual
v2/v3 baseline, fold-level walk-forward, and historical TRUE OOS runners. It
writes no duplicate canonical ledgers and reconciles freshly executed ledgers
against the existing canonical files. No MFE/MAE outcome rewriting is used.
The separate comparator auditor likewise imports neither the runner nor the
adapter.

The reconstruction evidence is labelled only
`RETROSPECTIVE_CAUSAL_VALIDATION`; it is not new, fresh, or unseen OOS evidence.
Its successful status is `STAGE5_CANONICAL_COMPARATOR_RECONCILIATION_PASSED`
and `STAGE5_COMPARATOR_ONLY_CHECKPOINT_COMPLETE`. BE1, TRAIL1, and
TOTAL_OPEN_RISK_CAP remain disabled and unexecuted. No hypothesis
classification or final Stage 5 manifest exists: **Stage 5 remains OPEN**.
