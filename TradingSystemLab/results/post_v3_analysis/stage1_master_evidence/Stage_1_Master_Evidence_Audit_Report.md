# Stage 1 Master Evidence — Independent Audit Closeout

## Scope and source contract

This audit is restricted to artifact reconciliation for the 36 Stage 1 studies. It reads only committed v1, v2, and v3 result artifacts: immutable baseline trade ledgers; Walk Forward and TRUE OOS metrics; Phase 2 comparison tables; and available instrument, direction, monthly, quarterly, and yearly reports. It does not import research, strategy, optimizer, backtester, market-data, or generator code.

## Independent checks

- **C1:** all 12 baselines were independently reconstructed from trade ledgers. All 24 Walk Forward/TRUE OOS aggregates were compared with authoritative metrics. The v1 T3/H1 Walk Forward C1 PF is `3.3803276720178377`; the old C0 PF `3.49197193021` is explicitly rejected.
- **Phase 2 and decisions:** all 12 candidate comparisons, all 12 Walk Forward verdicts, and all 12 TRUE OOS classifications reconcile to their canonical source artifacts and anti-regression expectations.
- **Breakdowns:** 10 instrument reports, 10 direction reports, 6 monthly reports, 10 quarterly reports, and 10 yearly reports were reconciled row-by-row. Internal trade and net-R totals reconcile for all 36 studies.
- **Manifest:** all 106 unique source SHA-256 entries and all 11 deterministic output SHA-256 entries were independently verified. Manifest counts reconcile to 36 study, 144 instrument, 72 direction, and 789 chronological-month rows.
- **Mutation controls:** in-memory corruptions of C1 PF, Phase 2 PF, verdict, classification, instrument/direction/month net R, source SHA, and output SHA are rejected.
- **Determinism:** only after the initial semantic and hash audit passed, `generate.py` was launched in a separate Python subprocess. All 11 generator-owned deterministic evidence outputs remained byte-identical, then the complete independent audit passed again.

## Closeout ownership and hashing

`audit.py` alone writes `audit_status` and `audit_result.json` after every check succeeds. `audit_result.json` and this report are operational closeout records and intentionally do not participate in `manifest["artifacts"]`; this avoids circular self-hashing. The 11 generator-owned deterministic evidence artifacts remain exactly the manifest artifact set.

## Scope protection

No strategy, backtest, optimization, market-data load, candidate change, historical trade change, ranking, portfolio construction, or Stage 2 analysis was performed. Frozen source evidence and protected research trees were not modified.

## Final status

`POST_V3_STAGE_1_MASTER_EVIDENCE_AUDIT_PASSED`
