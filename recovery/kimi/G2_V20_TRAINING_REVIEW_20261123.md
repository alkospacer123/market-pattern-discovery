# Kimi Chat G2.1 — V20 R088 training map, GPT review

**Date:** 2026-11-23. **Status:** `TRAINING_SOURCE_AUDIT_ACCEPTED`, **not** `V20_EXAM_PASS`, `CODE_TEST_PASS`, `INSTALLED_VERIFIED` or `LIVE_ARMED`. Operator provided complete ~904-line V20 knowledge-map report; independent GPT reviewed the report and verified selected source files against GitHub.

## Evidence and scoring

- Kimi main HEAD observed: `e05bbd24db88f127a52f0ff1b7282d7c6919cd81`, matching GitHub independently checked during review.
- GPT independently verified **19/19 selected Git blob SHA** (root authority, V20 passport and START HERE, R088 architecture/exam/release, BASE modules, frozen adapter, H1 execution grid, CC-08 etc.) at the pinned HEAD. This is a targeted sample, not independent proof every `SOURCE READ` claim in the 904-line report.
- Source-verified: frozen `SHALLOW_PULLBACK` and `OBV_PRESSURE` formulas in `research_original_v20/run.py`; runtime `frozen_adapter.py` immediate NEXT_OPEN; HOLD5 witness/session design; offline TP6 / Protect3 arithmetic; BASE+9 patch stack, historical DERIVED hashes, FINAM and broker truth distinctions. No tests were run by GPT or Kimi in G2.1.
- **GPT formative score: 96/100** — credible detailed architecture and safety knowledge, with noncritical gaps around exhaustive code provenance, source-vs-installed validation and operational precision. This **does not replace** the separate fixed V20 exam minimum 90/100 plus isolated offline pass.
- Kimi report self-classified `MAIN SOURCE REVIEW COMPLETE`, `INSTALLED HISTORY ONLY`, `LIVE UNKNOWN`, `TESTS NOT RUN`, `EXAM PASS NOT GRANTED`. Correctly no claimed V20 arm or current FINAM proof.
- Training includes source/patch logic, frozen signal formulas, NEXT_OPEN, 1.5%/6%, GO, VWAP/fills, TP6, Protect3 cancel-first and unprotected interval, HOLD5 fifth/sixth observed session, PREPOST strict never-posted orphan and UNKNOWN POST fail-closed, exit, CC limits, and R088 historical incident open questions.

## Verified documentation drift, candidate joint Chat/Code first Draft PR

In `V20_TradingSystem_M15/R088_ARCHITECTURE_AND_SAFETY_20261122.md`, the **CC-08** and **Control Center README** Git blob SHA references are stale:
- CC-08 document referenced `51781e013f68fc323a4740701ae84e066ef86926`, but `ControlCenter/docs/V20_CC08_OPERATIONS.md` at pinned HEAD is `18be465651d3747abe99f669967e374cde616252`.
- CC README referenced `707080ee4daf1b2cf3a754c078a67e78f6612aae`, but `ControlCenter/README.md` at pinned HEAD is `3c01b427b8b9a2bdaff9679dbafa32427428ed37`.
- The later `recovery/kimi/CONTROL_CENTER.md` already correctly points to newer blobs. This is **documentation/provenance drift**, not a proven runtime defect.
- **No correction performed in main or on Intel.** Candidate for user-authorized Kimi docs-only task branch, Draft PR and independent GPT review at G7 (or sooner via an explicitly authorized supervised exercise), preserving dated historical statements as dated.

## Targeted gaps before examination

1. Explicitly distinguish task/process **Running** from kill switch **HALTED**: existing-position follow-up is possible only while an appropriate worker is running and functional. HALTED alone proves neither FLAT nor working SLTP.
2. Explain the concrete role and uncertainty of missing source/binary data, historical CI and exact derived module checks; `SOURCE READ` without independent SHA is weaker than a validated content proof.
3. Reconcile line-by-line FINAM UNKNOWN entry / stop / cancel with PREPOST and Protect3 restart; no automatic repeats or broker operations during exam.
4. Understand completion, session key and missed-open witness in HOLD5; avoid conflating five sessions with calendar days.
5. Demonstrate code skills *later* via separate approved isolation (not C: folder alone). Any scenario involving current FINAM/SLTP proof remains out-of-scope until explicit live observation gate.

## Pro quota ledger

- Prior operator screenshot at 2026-11-23 15:29: **3.51%** monthly usage; Code rolling 5h **0%**.
- After G2.1 screenshot at 2026-11-23 16:06: **6.66%** monthly usage; Code rolling 5h **0%**.
- Difference **+3.15 percentage points** is *cumulative usage between snapshots*, not guaranteed spend attributable only to G2.1. Kimi G2.1 elapsed duration not provided; no absolute credit counts were shown.
- Extra paid usage remained OFF in screenshots. Next monthly reset shown 2026-12-23 11:28 in the UI.

**Next:** address the targeted gaps with new source-backed scenarios; then administer the separately approved V20 theory exam (and later isolated Code practical). Continue CC/TRL training independently. Keep bots HALTED until the owner's distinct decision; this training report does not authorize ARM, FINAM, secrets, or production file modification.

## G2.1B — targeted safety reasoning (23 Nov 2026)

**Status:** `TRAINING_G2_1B_PASS` **only**; standalone V20 exam theory/practice remain `NOT_TESTED`. Operator supplied a ~783-line READONLY Kimi Chat analysis of six challenging scenarios. GPT independently checked current main SHA and **12/12 selected Git blob SHA**, inspected actual `r070_linked_sltp.py`, PREPOST patch, HOLD5 implementation and protected recovery tests. **Formative technical review score: 98/100** (not an official theory score). Review is targeted, not a full static proof of every runtime branch or an exported Kimi tool-call log.

Source-supported findings:

1. `Task=Stopped` does not run normal Scheduled Task cycles; `Running/HALTED` can reconcile existing positions before the new-entry HALT. **Important exception:** `stage_r070_protect3_cancel_first_once` requires `Switch=ARMED` and fails `R070_PROTECT3_SWITCH_NOT_ARMED` before cancellation. Therefore do not say all Protect3 stop replacement remains available when switch is HALTED. Actual process/FINAM status on Intel is not proven from docs.
2. Protect3 cancel-first retains durable `NEW_POST_OUTCOME_UNKNOWN` before broker POST and `PROTECT3_UNPROTECTED_OR_UNKNOWN` on exception; no blind duplicate POST, and restart recognition is GET-only. ACK does not equal active SLTP.
3. PREPOST `_resolve_never_posted_entry` requires multiple durable and broker negative proofs, including no submission marker, no `live_post`, `PREPARED_ONLY_NO_POST`; UNKNOWN POST is not treated as never-posted.
4. HOLD5 counts observed sessions including entry, session key (MSK minus 9 hours). No late market substitute if first sixth-session Open was missed. Broker history and LIVE timing are separately `UNKNOWN`.
5. Partial fill: offline fake test observes position quantity growth with same stop while explicitly asserting `h1_stop_growth_physically_proven=False`. Percent-of-position future fill coverage by FINAM is not proven.
6. Two stale CC SHA in `R088_ARCHITECTURE_AND_SAFETY_20261122.md` independently verified, with current blobs `18be465651d3747abe99f669967e374cde616252` and `3c01b427b8b9a2bdaff9679dbafa32427428ed37`. No main fix or production change applied; candidate supervised docs-only Kimi PR later.

**Limitations:** Kimi did not run tests (prohibited), did not compare installed derived bytes, did not observe LIVE or FINAM, did not produce full independently verified code-call logs, and did not examine broker reality. These are boundaries, **not failed requests in the READONLY training exercise**. A running Windows Task does not guarantee successful active worker cycles, and a stopped Task alone cannot rule out other running processes; current process facts require separate permitted observation.

**Pro usage checkpoint:** operator mobile screenshot at 23 Nov 17:04 shows cumulative **8.26%** monthly (up **+1.60 p.p.** since 16:06 6.66%), five-hour Code **0%**, extra paid quota OFF, monthly reset 2026-12-23. Delta may include work beyond G2.1B; not isolated per-task cost. Mobile 5-hour reset clock differs from desktop, likely display timezone — no quota reset inference made.

**Next:** give the **12-question independent V20 R088 theory exam** in a **new project Chat** (60 max, 5/question); first answer without access to coaching messages, cite primary GitHub sources. Do not claim full `V20_EXAM_PASS` until four practical tasks (40 max) in approved isolated executor and combined >=90/100, no critical failures. G2 CC and TRL training remain required.
