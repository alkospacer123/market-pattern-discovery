# T3 INITIAL STOP FORENSICS V1

Read [REPORT_RU.md](REPORT_RU.md), [PROTOCOL_RU.md](PROTOCOL_RU.md),
[AUDIT.json](AUDIT.json) and [REPEATABILITY.json](REPEATABILITY.json).

Only H1 CONTROL2.5/2.0/1.5 ATR and M15 CONTROL2.0/1.5 ATR; no selection,
new filters, risk changes, production execution, broker calls or money proxy.

## Reproduction

All commands from the repository root. Python3.12, requirements.txt versions.
Use a clean read-only data repo at `/workspace/market-pattern-data`, HEAD
`f8486b446cf3d5f9f3cba6dfec32bdef8fd184c8`, with H1 data commit
`50f1fd2178c18b7ab3bd969be82ad01f47a34745` present in its object database.
H1 source is read from those older git blobs in memory; it is not read from
current H1 checkout. No raw OHLCV files are copied into this repository.
Only explicitly requested per-position High/Low observations are retained.

Fetch archived PR557 if absent (read-only object download):

```sh
git fetch origin 5836971e7ff8e472d8128c675c4f837b40a036ef
python -B audit_only/t3_initial_stop_forensics_v1/test_synthetic.py
python -B audit_only/t3_initial_stop_forensics_v1/repeat.py --prefix fresh
```

`repeat.py` runs three fresh source-to-report processes (first + two repeats)
and compares every generated file's bytes and SHA256. It writes only ignored
`work/fresh_*` and its receipt. It does not change published artifacts unless
`--publish` is explicitly passed for this authorized audit directory.
No parameter CLI exists. Existing run output directories must be empty.

## Lineage

common.py and engines.py are adapted from PR557, whose execution was already
causally audited. Frozen source features and historical lifecycle registry are
reused. `ENGINE_LINEAGE.patch` shows exact changes; no strategy rewrite.
`gate.py` authenticates PR557 and PR518 SHA256SUMS, frozen main code/data blobs,
then reconciles every CONTROL trade/signal/stop/mark before alternatives.
Ready trade CSVs are reference journals only; no alternative uses them as input.

Separate verifier source and receipts are in `verifier/`: scalar execution,
archived independent M15 feature calculation, retrospective arithmetic and fresh
CSV/Decimal calendar/summary reconciliation. No primary execution/accounting
helpers imported by scalar verifier. Frozen feature authority is shared for H1.
No external human review is asserted. Every WF fold is separate; no double count.

Frozen code and protocol hashes are checked at the start of each full run.
SHA256SUMS covers user-facing code and evidence, excluding itself and ignored
work/bytecode. REPEATABILITY excludes itself to avoid a self-referential hash.
