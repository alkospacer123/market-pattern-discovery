# Data inventory

## Workspace finding

No historical source OHLCV files for CNYRUBF, IMOEXF, GLDRUBF, BR, or GOLD were found. Existing repository CSV files are generated result/report artifacts, not market datasets, and were deliberately excluded. Thus no instrument/timeframe availability or date range can truthfully be reported here.

| Source path | Filename | Symbol | TF | Format | Delimiter | Encoding | Timestamp format | First | Last | Rows | Columns | TZ | SHA256 | Parse |
|---|---|---|---|---|---|---|---|---|---|---:|---|---|---|---|
| — | — | — | — | — | — | — | — | — | — | 0 | — | — | — | no datasets |

Run locally (PowerShell line continuation is supported by the shell):

```powershell
python -m bbw_system.data_cli audit `
  --data-root "D:\path\to\read-only-market-data" `
  --output "D:\BBW\audit"
```

The runner discovers CSV/TXT files, recognizes generic and Finam layouts, inventories hashes and parsing, then normalizes/audits only files whose symbol and timeframe can be identified and whose passport supplies explicit timezone/session metadata.
