# BBW data readiness matrix

No source dataset was available; all availability and history fields are therefore unknown, never inferred as absent market history. All instruments are blocked.

| Instrument | H1 | M15 | M5 | M1 | History years | TZ verified | Session verified | Tick size verified | Tick value verified | GO verified | Commission verified | Rollover type verified | Ready | Blocking reasons |
|---|---|---|---|---|---:|---|---|---|---|---|---|---|---|---|
| CNYRUBF | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | — | NO | NO | NO | NO | NO | NO | NO | NO | no data; timezone; session; tick; tick value; GO; commission; series type; strategy fields |
| IMOEXF | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | — | NO | NO | NO | NO | NO | NO | NO | NO | same blockers |
| GLDRUBF | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | — | NO | NO | NO | NO | NO | NO | NO | NO | same blockers |
| BR | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | — | NO | NO | NO | NO | NO | NO | NO | NO | same blockers; max width decision |
| GOLD | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | — | NO | NO | NO | NO | NO | NO | NO | NO | same blockers; max width decision |

## Parameter-level instrument blockers

All five instruments have unresolved stop-offset unit semantics (the phrase “4 points” is not converted to ticks), unresolved penetration point semantics (“3 points”; the separately specified 20% range is fixed), unresolved stop bounds, and unresolved entry-quality limits. CNYRUBF/IMOEXF/GLDRUBF preserve the supplied max widths of 0.5%/1.5%/1.0%; BR and GOLD remain `null` and require a decision.
