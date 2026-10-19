# SBER T3/H1/TRAIL1 — offline transfer study

Main: `38489db7e69336548a583f968f13aab49c20913b`.
Read [REPORT_RU.md](REPORT_RU.md) and [PROTOCOL_RU.md](PROTOCOL_RU.md).
This directory is isolated research, not a production integration or new roadmap phase.

Input: externally supplied `SBER_M60.csv`, SHA256
`888bf47b5030f362f2e83c018a18da6ec9ba49d1d9ded3fceed4293886cfd2a0`.
Keep it outside this Git checkout. No data download, broker connection, credentials,
account state, deployment or order API is used by this runner.

From repository root, create an external virtual environment and install
`audit_only/sber_t3_h1_transfer/requirements.txt`. Python 3.12 was used.

```bash
python -m venv /tmp/sber-env
/tmp/sber-env/bin/pip install -r audit_only/sber_t3_h1_transfer/requirements.txt
/tmp/sber-env/bin/python -m audit_only.sber_t3_h1_transfer.study develop \
  --data /absolute/external/SBER_M60.csv --out /tmp/sber-development
/tmp/sber-env/bin/python -m audit_only.sber_t3_h1_transfer.audit_results /tmp/sber-development
```

The original chronological workflow ran development, tests, `freeze`, then
`evaluate`; its immutable FREEZE.json and EVALUATION_ACCESS.json record that order.
`freeze` refuses to replace an existing freeze and `evaluate` refuses to reuse an
already opened output directory. To **verify the already frozen evaluation**
without refreezing or changing any parameter, use a fresh output directory:

```bash
/tmp/sber-env/bin/python -m audit_only.sber_t3_h1_transfer.study evaluate \
  --data /absolute/external/SBER_M60.csv --out /tmp/sber-verification
/tmp/sber-env/bin/python -m audit_only.sber_t3_h1_transfer.audit_results /tmp/sber-verification
```

Compare each `*_trades.csv` SHA256 with committed `results/evaluation/audit.json`.
The full combined ledger also exists as `all_trades.csv`. Per-position stop traces
contain only derived strategy state, not source OHLC candles. OPEN positions are
separate JSON and never appear as forced exits.

Run the exact pre-OOS offline test selection (the Stage7 module has local imports):

```bash
PYTHONPATH="$PWD/TradingSystemLab/results/post_v3_analysis/stage7_production_specification_freeze" \
  /tmp/sber-env/bin/python -m pytest \
  audit_only/sber_t3_h1_transfer/test_study.py \
  TradingSystemLab/results/post_v3_analysis/stage7_production_specification_freeze/test_production_specification.py \
  TradingSystemLab/stage8_robot/tests/test_stage8.py -q \
  -k 'test_study or FreezeTests or stage7_authentication or t3_long_short_signal or warmup_and_no_signal or trail1_direct_conformance or trail_never_triggers or position_stop_before_extreme or event_order_exit or context_blocks_reset or donchian_is_shifted_one or production_replay_has_no_research_shortcut'
```

Original freeze command (already executed, not needed for verification):

```bash
python -m audit_only.sber_t3_h1_transfer.study freeze \
  --out audit_only/sber_t3_h1_transfer/results/development --tests /path/to/pre_oos_tests.txt
```

`report.py` renders the frozen presentation and same-window normalized N4
comparison from recorded outputs. It does not run a strategy or select parameters.
For Markdown rendering, additionally install `report_requirements.txt` (tabulate
0.9.0). This presentation dependency was installed after the calculation freeze;
it does not affect the frozen code, indicators, costs or trade ledgers.
Render with `python -m audit_only.sber_t3_h1_transfer.presentation.render`.
The original frozen renderer remains unchanged; see
[PRESENTATION_CORRECTION_RU.md](PRESENTATION_CORRECTION_RU.md) for the documented
N4 composite-key validation correction and independent comparison audit.
`audit_results.py` checks ledger arithmetic, non-overlap, trigger/activation timing,
stop direction, stock diagnostic grid and every periodic summary independently
using the Python standard library. All audits were performed by one agent with
separate implementations; this is not an independent external expert review.
