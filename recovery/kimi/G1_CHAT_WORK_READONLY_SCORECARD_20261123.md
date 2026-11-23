# Kimi Pro qualification — G1.1 / G1.2 / G1.3 source audits (23.11.2026)

**Status: REPORT-BASED SOURCE ACCEPTANCE, NOT RUNTIME / LIVE / FULL EXAM PASS.** This scorecard records the operator-provided Kimi outputs and independent GPT GitHub SHA spot checks, not a full exported Kimi tool-call transcript. Do not infer installed, FINAM or execution states from this file. The canonical GitHub main during these trials was `e05bbd24db88f127a52f0ff1b7282d7c6919cd81`; current HEAD must always be re-fetched for future work.

## Audit results

| Test | Agent mode | Scope | Measured time | Evaluated source accuracy | GPT assessment |
| --- | --- | --- | --- | --- | --- |
| G1.1 | Kimi Work, **without local folder** | Current main and five Git blob SHA; MAIN/INSTALLED/LIVE | 7 min 41 sec (operator) | 5/5 Git blobs and HEAD confirmed independently | `PASS`, limited GitHub source baseline |
| G1.2 | Kimi Work, **without local folder** | Nine docs, V20 R088, CC-07/08, TRL R060–R098, dependencies, historical contradictions | 13 min 47 sec (operator) | 9/9 mandatory blobs and source descriptions independently checked | `PASS`, technical score 96/100, report-based |
| G1.3 | **Kimi Chat** within V20 knowledge project | Same nine docs, detailed original signals, BASE + nine patches, CC and TRL source audit, GitHub tools | **NOT RECORDED** | 9/9 mandatory docs, 9/9 R088 patches, 18/18 selected docs/runtime SHA exact; key assertions source-checked | `PASS` within requested READONLY scope; preliminary technical score 98/100 |

**G1.3 self-reported `PARTIAL`** because it did not replay tests or verify INSTALLED/LIVE. Those operations were **explicitly prohibited in the G1.3 scope**; they remain `NOT_TESTED` and are NOT score deductions for the READONLY source test. No compiled R088 derived SHA, actual broker positions, working stop or LIVE operation is independently proven. Source-content and Git blob evidence checks are not a substitute for access logs or full code review.

**G1.3 report highlights:** BASE TIME3 vs R088 HOLD5 via nine patches; R088 derived `finam_live.py=5d30270d3936fb52f58a61aa3abbf070d7df6b57` and `finam_execution.py=0fc4c454d55f37e4e87fd74e3370cbc1ad83b53f` are historical documented hashes, *not freshly recomputed*. EXT2 OFF; 60/30/45 approved versus 75/30/30 research leader; 2025 not untouched OOS; Control Center manual refresh distinct from CC-07 command actions and `FAILED_UNKNOWN` no retry; R060/R097 ZIP/XLSX not present as bytes in the GitHub-only audit. Report lists a search_code HTTP 429 recovered and zero incomplete search results not treated as proof of missing imports. Exactly how tool approvals and retries occurred has not been independently reconstructed from platform logs.

**Known comparability limits:** G1.3 Chat project contained custom project instructions mentioning V20 terminology, source paths and current strategy decisions. The trial still required direct GitHub blob proofs and extra source checks, but it was not fully *context-blind* versus no-folder Work. G1.3 user-side elapsed duration was not reported. The 96 and 98 scores are scoped qualitative reviews, not precise statistically valid model-performance deltas. Further tests should be blinded and use new tasks under equal evidence constraints.

## Subscription usage ledger — operator screenshots (cumulative percentages)

| Snapshot | Date/time shown | Kimi Pro monthly usage | Rolling five-hour Code |
| --- | --- | --- | --- |
| Initial | 23 Nov, 12:16 | 0% (UI-rounded) | 0% |
| After G1.1 | 23 Nov, 12:58 | 0.19% | 0% |
| After G1.2 | 23 Nov, 14:24 | 1.35% | 0% |
| After G1.3 | 23 Nov, 14:57 | 3.46% | 0% |

Cumulative deltas between the three nonzero screenshots: `+1.16` and `+2.11` percentage points. **These are changes between timestamps, not certified per-task token or credit usage.** The UI does not disclose absolute credit counts in these screenshots. The next monthly reset shown is 2026-12-23 11:28 (interface clock). Extra paid usage is OFF.

## Next qualification steps

1. G0: attach concise canonical source passport and START HERE documents to each of the three Chat knowledge projects after independent source trial; project instructions were added by operator, attachments still need explicit confirmation.
2. Run a short fresh-session **Chat browser/mobile GitHub read-only parity** task (distinct new file, no answer leakage). Record availability of plugin and approval prompts on mobile.
3. G2: dedicated **V20 / Control Center / TRL** theoretical exams in the corresponding Chat projects, with hidden/new questions and real source links. Do not confuse G1 GitHub architecture audits with passing the three project exams.
4. G3/G4/G5: test Work and Code for their distinct value and execute synthetic tests only in an approved isolated no-secret executor. The local folder `C:\KimiSandbox\market-pattern-discovery` is not an OS sandbox.
5. G7: GPT↔Kimi branch/Draft-PR handoff requires separate operator permission; G8: read-only actual LIVE observation requires full exams and explicit operator decision. **ARMED, broker orders/SLTP, tasks and current LIVE remain separately gated.**
6. G9: annual Pro/Max decision only on actual representative quality, short-window and monthly capacity measurements, not from three source audits.

This document is part of Draft PR #597; **do not merge without explicit operator approval.**
