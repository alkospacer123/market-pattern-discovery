param([Parameter(Mandatory=$true)][string]$DataRoot)
python -m TradingSystemLab.run_t3_extended_validation --data-root $DataRoot
exit $LASTEXITCODE
