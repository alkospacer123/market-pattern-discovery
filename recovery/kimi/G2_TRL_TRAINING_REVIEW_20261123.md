# G2.3A — Kimi Chat TRL deep training review

**Review date:** 2026-11-23 (operator screenshot 21:06 UTC+03). **State:** `TRL_G2_3A_TRAINING_ACCEPTED`, formative reviewer score **97/100**; **not** `TRL_CHAT_EXAM_PASS`, `TRL_CODE_PRACTICAL_PASS`, `REPLAYED_BY_KIMI`, `RESEARCH_APPROVED`, `INSTALLED_VERIFIED` or `LIVE_AUTHORIZED`.

## Evidence and source controls

- Operator provided ~399-line G2.3A Kimi Chat report containing 16 required sections and 55 manifest entries (50 paths on discovery, 1 main ref on data, 4 data CSV). Exact source report retained in operator handoff; no sensitive Intel/FINAM data supplied.
- Actual verified discovery main: `e05bbd24db88f127a52f0ff1b7282d7c6919cd81`. Actual verified data main: `f8486b446cf3d5f9f3cba6dfec32bdef8fd184c8`.
- Independently fetched and matched all **54/54 Git blob SHA** in the report (S01–S50, S52–S55); independent HEAD checks matched both repositories. This verifies **source identity**, not code execution, downloaded binary ZIP/XLSX or CSV content equality to historical R060 inputs.
- GPT separately inspected actual textual sources: `TradingResearchLab/evolution/2026-11-12-r060-exact-cash-parity-and-filters.md`, `TRL-R089-HOLD5-WITHOUT-EXT2-ORIGINAL-20261118.md`, `TRL-R097-FULL-CAPITAL-2023-2026.md`, `TRL-R098-CONDITIONAL-ALLOCATION-20261119.md`, `TRL-NOV-2026-FINAL-CLOSEOUT.md`, and `TRL-NOV-2026-ARTIFACT-MANIFEST.md`. Source spot-check supports reported R060 `1473 / +422224.10 / PF1.914428`, R086 EXT2 ON `1386 / +486684.60 / PF2.12691` as quoted in R089, R089 EXT2 OFF `1424 / +459798.10 / PF2.015588`, R097 capital trade-offs, 2025 PF failure, and decision to keep `60/30/45 TP6+Protect3+HOLD5 EXT2 OFF` despite `75/30/30` leading modeled Net/PF.
- Source audit and the learner both correctly distinguish source Markdown from verified binary bytes, current GitHub source from installed/live, old 2018–2026 data from untouched true OOS, modeled OHLCV/C1/GO from broker execution, and manual FINAM statements from CC heartbeat. Original R060/R097 ZIP and R087 raw TXT **not available to current Kimi GitHub-only task**; no clean replay performed.

## Observed gaps / follow-up

1. **Date discrepancy:** Kimi report header reads `Дата аналитического среза: 24.11.2026`, yet user's Kimi Pro screenshot/report were submitted on **2026-11-23 21:06 UTC+03**. The only defensible present review timestamp is 23 Nov; learner should correct future provenance, not silently rewrite the uploaded report.
2. **Proposed forward hypothesis** uses sample-size and PF/bootstrap criteria (e.g. 100–150 trades and PF>=1.3) without power/calibration evidence. It is an explicitly **unapproved `PROPOSED_NOT_TESTED / HOLD_DATA` idea**, not a statistically validated new strategy or authority to launch.
3. Only historical Markdown is currently accessible; original data, logs, ZIP/XLSX byte equality, exact 2026 quotations and the full ledger have **not** been independently replayed. This limits evidence; **Kimi explicitly declared NOT_REPLAYED**, so it is not an integrity violation.
4. Strong areas: R060→R086→R089→R097→R098→owner closeout causal timeline, output parity ≠ byte-equivalent original R051, +245 ₽ R086 caveat, R090–R096 provisional nonparity, 2025 PF<1.7, no automatic EXT2 reinstatement, negative research preservation, data snooping/TRUE OOS caution, large-capacity unrealism, independent reviewer under GPT outage.

## Usage ledger

Operator screenshot `2026-11-23 21:06`: Kimi Pro **17.88%** monthly used, five-hour Code **0%**, Extra Usage OFF, next monthly reset 2026-12-23 11:28. Previous snapshot 20:06 monthly 14.84%; **+3.04 percentage points across screenshots**, **not** independently established cost of G2.3A alone.

## Next gates

- `G2.3B` extended source-based adversarial TRL training: cross-comparability, dishonest claims about missing binaries/OOS, ledger vs aggregate, nonparity and proposal statistical assumptions. GitHub READONLY only.
- `G2.3C` independent fresh-chat TRL exam under same evidence standards, with separately recorded score and explicit absence of real replay.
- Later **Kimi Code** isolated real reproducibility/practical exam using original SHA-verified archives only after secure access and user approval, distinct from Chat; independent GPT-outage and final docs revision after all three projects.
- No changes to V20, Control Center, TRL, FINAM, LIVE, brokerage, GitHub main or production files from this training review. Stage III independent Recovery/cold restore remains last.

## G2.3B — 12 advanced research scenarios, evidence and adjudication (2026-11-23 local UTC+03)

**Outcome:** \`TRL_G2_3B_TRAINING_ACCEPTED\`, formative **98/100**, \`0\` critical source/safety mistakes observed in checked answer. **NOT** independent G2.3C Chat examination, Kimi Code replay, broker evidence, or qualification for LIVE.

Operator attached 438-line Kimi Chat report \`TRL_G2_3B_сложные_исследовательские_сценарии.md\` and Pro quota screenshot at 23 Nov 2026 22:03 UTC+03. GPT checked current \`market-pattern-discovery/main=e05bbd24db88f127a52f0ff1b7282d7c6919cd81\` and \`market-pattern-data/main=f8486b446cf3d5f9f3cba6dfec32bdef8fd184c8\`; **25/25 unique Git blob SHA** named by report at the pinned discovery commit and **4/4 CSV Git blob SHA** at the data commit matched source. Git SHA proves content identity, not original R060 R097 archive equality or execution. These were targeted source reads, not exhaustive code audit.

**Primary source substantive spot-check:** R097 MAIN/100-lot portfolio figures, 75/30/30 historical Net/PF leader vs owner-selected 60/30/45, 2025 PF below 1.7; R060 1473/+422224.10/PF1.914428; R086 reconstructed TIME3 +245 RUB caveat; R089 new-quote EXT2 ON vs OFF; R090/R091 54/64 vs 53/64 lot parity; R047 hindsight ex-post PF3.111 vs causal full results; R048 no profitable C4 variants; artifact manifest missing binaries. Arithmetic in the compared 10m 100-lot table is consistent. G2.3B correctly rejected aggregate-only parity, assumed liquidity and inflation of TRL evidence into LIVE. **No actual replay or tests performed**; that was prohibited for Chat.

**Known nuance on dates — reviewer correction:** Kimi says its "analytical date" was 24 Nov, while the operator uploaded the report at **23 Nov 22:03 UTC+03**. These dates can both be true: 22:03 UTC+03 equals **03:03 on 24 Nov UTC+08**. Therefore earlier reviewer assertion that \`24.11.2026\` was conclusively a Kimi error was **premature**. Defensible observation is **time zone/source omitted; precise Kimi generation time NOT_VERIFIED**. Do not record as a proven model hallucination without establishing stated time zone/time source. User screenshot date is a valid operator-local timestamp, but cannot by itself establish Kimi's timezone. Update KDR-003 accordingly and preserve this correction.

**Other limited concerns:** broad source claims were sampled against primary Markdown, not recomputed from raw R060/R097 files; no access to missing R087 TXT; real broker SLTP/FINAM/GO/costs absent; G2.3A forward threshold not validated by power analysis, but Kimi explicitly self-critiqued it. These are **evidence gaps / proposals**, not hidden execution failures.

**Pro quota:** operator screenshot at 2026-11-23 22:03 UTC+03 shows monthly \`20.14%\` used (remaining \`79.86%\`), 5-hour Code \`0%\`, extra usage OFF. Previous 21:06 screenshot \`17.88%\`; **+2.26 percentage points across screenshots**, not certified per-task usage; monthly reset 2026-12-23 11:28.

**Next:** independent **G2.3C** fresh TRL Chat exam with **canonical 40-point phase A / >=36/40**, rather than reusing the 12 training questions; the canonical Code phase B remains 60 points / >=54/60 and 0 critical, with actual binaries needed for replay. Do not provide KDR journal and corrective answers to candidate until G2.3C completes. Subsequently direct postmortem and hidden follow-up. Enhanced V20/TRL practical acceptance requirements: [V20_TRL_ENHANCED_PRACTICAL_ACCEPTANCE_20261123.md](V20_TRL_ENHANCED_PRACTICAL_ACCEPTANCE_20261123.md).