# Intel execution (Windows PowerShell)

Run from the repository checkout; replace both example roots with the actual local paths:

```powershell
cd C:\MarketAI\market-pattern-discovery
git pull
python -m TradingSystemLab.run_t3_extended_validation `
  --data-root C:\MarketAI\data\market-pattern-data 2>&1 | Tee-Object T3_extended_validation.log
```

Inspect `parity_report.json` first, followed by `data_inventory.csv`, `common_coverage.json`, `data_manifest.csv`, `manifest.json`, and `final_report.md`. A `DATA_BLOCKED` verdict means common pre-2023 Si/CNY H1 files must be added as specified in `required_data.md`; it is not an extended-validation result.

For a determinism check, copy the result directory, repeat the identical command, and compare text-file hashes with `Get-FileHash -Algorithm SHA256`. Do not download data, expose TRUE OOS, or change parameters.
