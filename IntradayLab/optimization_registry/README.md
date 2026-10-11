# Frozen-result registry

Start with [REGISTRY_REPORT.md](REGISTRY_REPORT.md), [policy](OPTIMIZATION_POLICY.json) and [queue](OPTIMIZATION_QUEUE.md). MASTER_STRATEGY_REGISTRY.csv has one record per family definition or configuration/instrument; historical summaries without instrument attribution retain NOT_AVAILABLE. Configuration IDs distinguish studies and variants, not new strategies. STUDY_CATALOG.json stores exact ref/path/selector mappings; SOURCE_FILE_INVENTORY.json stores read-source SHA-256 values. Every unavailable field has a reason in not_available_reasons.

Reproduce the core CSV/JSON extraction (Python stdlib only):

```sh
python IntradayLab/optimization_registry/build_registry.py
python IntradayLab/optimization_registry/audit_registry.py
```

Git must contain the refs recorded in DISCOVERY_SNAPSHOT.json, including the exact base, ORB #463, Bollinger #472, PR460/462, early pre-correction e38e018 and autonomous 728d23e. The scripts use Git objects only; they do not open the data checkout, execute strategies or model trades. Markdown reports and the companion candidate/coverage indexes are frozen review documents; numerical CSV/JSON outputs are deterministic. Missing finite PF with no losses is NOT_AVAILABLE, not infinity or zero. Calendar days/months use known CLOSED entry dates; month signs use closure dates and the documented Decimal reporting tolerance. Full annual/account metrics remain unavailable.

ELIGIBLE is not economic PASS, permission to run Optimization, an independence claim or an annual profitability claim. Every future family Optimization needs separate authorization and a pre-P&L frozen grid/budget/configuration. STOP here.
