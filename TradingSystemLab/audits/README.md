# TradingSystemLab audit archive

This directory stores completed human or AI audit reports.  It is not a place
for run artifacts, market data, informal task summaries, or fabricated
retrospective audits.  Existing reports elsewhere in `results/` remain in place
and retain their original provenance.

Recommended filename:

```text
YYYY-MM-DD_<phase>_audit.md
```

Each report must record:

- exact repository commit and working-tree state audited;
- every file actually opened and inspected;
- checks performed and reproducible commands/methods;
- values independently recomputed, including formula and tolerance, if any;
- discrepancies and failed or unavailable evidence;
- final audit status using the vocabulary in `../AUDIT_PROTOCOL.md`;
- unresolved issues and any prerequisite for a re-audit.

Do not claim a historical audit merely because a README, PR description, commit
message, or generated phase report says that an audit occurred.  Archive a
report only when its author actually performed and documented the inspection.
