# BBW local real-data freeze (Windows Intel)

This procedure audits data only. It does **not** calculate BBW signals, trades, performance, or optimization. Keep source data and the large output outside the repository.

## Run

1. Update the repository (`git pull`) on the Intel Windows machine.
2. Activate the repository Python environment and install the project if needed (`python -m pip install -e .`).
3. Complete and verify the instrument passports in `bbw_system/config/instruments` (especially source/exchange timezones and session bounds). Never guess these values.
4. From the repository root run:

   ```powershell
   .\bbw_system\scripts\run_bbw_data_freeze.ps1 `
       -DataRoot "C:\TradingBacktest" `
       -OutputRoot "C:\TradingBacktest\BBW_DATA_FREEZE" `
       -InstrumentConfigRoot ".\bbw_system\config\instruments"
   ```

   `-InstrumentConfigRoot` is optional and defaults relative to the repository. `DataRoot` is searched recursively for `.csv` and `.txt` files. Only target instruments (including passport aliases) and D1/H1/M30/M15/M5/M1 are normalized.
5. Check `$LASTEXITCODE` is `0`. Individual unrecognized or invalid files are recorded without aborting the batch.
6. Find the compact bundle in `C:\TradingBacktest\BBW_DATA_FREEZE\evidence`.

## Outputs and handoff

`large_local_output` contains normalized OHLCV, row-level diagnostics, and cache space. It stays on the local machine and must never be committed or copied into the repository.

Return only these seven files from `evidence` into `bbw_system/data_freeze/` for review:

* `FREEZE_MANIFEST.json`
* `DATA_INVENTORY.md`
* `DATA_QUALITY.md`
* `DATA_COVERAGE.csv`
* `LIQUIDITY_SUMMARY.csv`
* `ROLLOVER_SUMMARY.csv`
* `DATA_READINESS.md`

Review local source paths before sharing if they are sensitive. The portable IDs remain usable if local path text is redacted. Do not proceed to baseline merely because an instrument is `READY_FOR_METADATA_FREEZE`.
