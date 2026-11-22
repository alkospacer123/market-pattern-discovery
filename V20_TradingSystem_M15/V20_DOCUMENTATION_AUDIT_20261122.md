# V20 documentation index — evidence-first audit, 22.11.2026

**Verified SOURCE snapshot**: `main@0e569be6cb3c7cce1f7224e7f1fef6be38f6ba52`, V20 subtree Git tree `08e4b1ff98f8599f662ee8724c2d11cea03d85d3`, `truncated=false`. Exact inventory: **441 files; 79 Markdown documents** inside V20, including the project README/AGENTS and nested archives. 2 additional `.txt` artifacts in V20-03 were previously counted with Markdown-like documents; do not call them Markdown. The table is the complete Markdown listing **from that original commit**, not the newly added PR docs.

Statuses are **document authority categories**, not broker or physical LIVE states. `CURRENT` = current entrypoint or confirmed dated release record; `HISTORICAL` = earlier stage; `SOURCE_EVIDENCE` = dated original decision/incident/acceptance; `RESEARCH` = non-production exploration; `SUPERSEDED` = old task/spec no longer authoritative; `UNKNOWN` = insufficient evidence. Classifications use paths, dates, declared purposes and targeted textual review of primary documents. They **do not** claim a fresh empirical re-run of every historical dataset.

## 1. Confirmed documentation issues / dispositions

| Exact source | Concrete conflict or ambiguity | Correct treatment |
|---|---|---|
| `README.md` | Top-level title V20-04 and older «IN PROGRESS / OFFLINE ONLY», despite R088 installed 20.11 | Update top navigation; preserve old body as dated history |
| `docs/PROJECT_SPEC_RU.md` | Early planned capital 3×500000 ₽, TIME3 | SUPERSEDED, do not rewrite frozen original |
| `docs/ROADMAP_RU.md`, `docs/ROADMAP_DETAILED_RU.md` | Dated 26–27.10 LIVE/state claims and Draft #567 | HISTORICAL state; preserve 8 phases / 24 subphases |
| `V20-08/R070_COMBINED_RELEASE_PACKAGE_20261117_RU.md` | References EXT2 in planned release | RESEARCH, final R088 **EXT2 OFF** |
| `V20-08/R088_HOLD5_OFFLINE_REPORT_20261118_RU.md` | Candidate/EXT2 and Draft claims reflect 18.11 only | RESEARCH snapshot, not 20.11 installed |
| `V20-04/SOURCE_MAP.md` | Earlier H1 source SHA and PR #567 Draft | SOURCE_EVIDENCE; new R088 map gives current source/patch provenance |
| `V20-08/RUNBOOK_08_5_RU.md` | 28.10 incident, earlier operator blob pins | HISTORICAL; safe current permissions in R088 architecture + canonical release |
| `V20-08/LIVE_RELEASE_R088_20261120_RU.md` | Cites 9 patches but a quick reader might assume only `finam_live.py` is rebuilt | New architecture explicitly maps **both** built modules and patch #7 |
| `R070_PROTECT3_M15_OR_FILL_UNVERIFIED` | 20.11 root condition not identified | `UNKNOWN`, no fix of trading logic in docs-only scope |
| Post-install Control Center / FINAM | Physical ARMED/SLTP on 22.11 not independently checked | `NOT VERIFIED`, do not infer from CI, Git Merge or heartbeat |
| V20/TRL 2025–2026 | Already used for research | Not untouched TRUE OOS, no backtested PF-as-proof |

## 2. Relative link audit and limits

All **79 existing Markdown files** were fetched from pinned `main` for a scoped inline Markdown-link check. **No missing link targets inside V20** were found. Link parser covers обычный синтаксис inline Markdown-ссылок and resolves file/directory membership against the untruncated V20 Git tree. It **does not** prove reference-style links, `#heading` anchors, HTML links, externally hosted URLs or links outside `V20_TradingSystem_M15/`. Those are `NOT VERIFIED`, not `PASS`. Root/recovery sources had a separate prior source-authority audit; this operation did not repeat global cleanup.

## 3. Full Markdown inventory (original HEAD before this Draft PR)

Counts: `CURRENT=3`, `SUPERSEDED=7`, `SOURCE_EVIDENCE=18`, `HISTORICAL=11`, `RESEARCH=40`. **Blob SHA is Git provenance only**, not installed Intel file hash. Existing historical texts remain unchanged.

| Relative path | Git blob SHA-1 | Status | Purpose / issue | Resolution |
|---|---|---|---|---|
| [`AGENTS.md`](AGENTS.md) | `f3222c7d633b4b9451bee72e66bc18bf0144dd50` | CURRENT | Project governance + R088 | Maintain |
| [`docs/CODEX_V20_03_DRAFT_PR_PUBLICATION_RU.md`](docs/CODEX_V20_03_DRAFT_PR_PUBLICATION_RU.md) | `04f57d93a98d7e92737853490dbc4dd6364ce8ab` | SUPERSEDED | Older drafting instructions | No implicit authority |
| [`docs/DECISION_V20_03_CLOSE_20261021_RU.md`](docs/DECISION_V20_03_CLOSE_20261021_RU.md) | `3d33eb365130d89f03b2db435a3f5c7849ff5c82` | SOURCE_EVIDENCE | Decision at earlier date | Preserve |
| [`docs/PROJECT_SPEC_RU.md`](docs/PROJECT_SPEC_RU.md) | `6da1f074775114aef1009f471e2e681da513ce37` | SUPERSEDED | Old 3x500k/TIME3 spec | Do not treat as R088 |
| [`docs/ROADMAP_DETAILED_RU.md`](docs/ROADMAP_DETAILED_RU.md) | `d1af045ef415e04985e16cedb4dba0fd24bfb165` | HISTORICAL | 8/24 stage roadmap with dated status | Keep structure; see R088 current |
| [`docs/ROADMAP_RU.md`](docs/ROADMAP_RU.md) | `7b379528c3d668d335aafb4a223572e9fd1118cc` | HISTORICAL | 8/24 stage roadmap with dated status | Keep structure; see R088 current |
| [`README.md`](README.md) | `fa219c6bf9d236e74a6d2695bc76f12636c7b5ad` | CURRENT | Entry point + historical V20-04 | Update heading/navigation |
| [`research_original_v20/legacy_v4/PROTOCOL.md`](research_original_v20/legacy_v4/PROTOCOL.md) | `632a6502601d0b03f24826985830eb9d5e8361f4` | RESEARCH | Original strategy research | Preserve |
| [`research_original_v20/PROTOCOL_RU.md`](research_original_v20/PROTOCOL_RU.md) | `179fc161f2ea330f3f61e0b8efebfa45b12a0fa8` | RESEARCH | Original strategy research | Preserve |
| [`V20-02_AUDIT/V20_02_REPORT_RU.md`](V20-02_AUDIT/V20_02_REPORT_RU.md) | `99e239d106c4d403ae928bde0d3cf439bc747902` | HISTORICAL | Early audit | Keep dated |
| [`V20-03/comparison/DEVELOPMENT_DECISION_RU.md`](V20-03/comparison/DEVELOPMENT_DECISION_RU.md) | `2adb31f5df6451dea1b5d8763b5afddd4b7414f1` | SOURCE_EVIDENCE | Historical V20-03 PF/parity/evidence | Not current R088 / not untouched OOS |
| [`V20-03/comparison/METHODOLOGY_EFFECTS_RU.md`](V20-03/comparison/METHODOLOGY_EFFECTS_RU.md) | `478e99c00e3ebf70901f6f136db6f4c7675dd76b` | RESEARCH | Historical V20-03 PF/parity/evidence | Not current R088 / not untouched OOS |
| [`V20-03/comparison/PF_DIAGNOSTIC_REPORT_RU.md`](V20-03/comparison/PF_DIAGNOSTIC_REPORT_RU.md) | `f47297435a888cc2982f393f5bf82ea6d81dce82` | RESEARCH | Historical V20-03 PF/parity/evidence | Not current R088 / not untouched OOS |
| [`V20-03/evidence/archive_original/docs/ROADMAP_RU.md`](V20-03/evidence/archive_original/docs/ROADMAP_RU.md) | `33fc47d44a0435b947709a4a47a8182505c857f2` | SOURCE_EVIDENCE | Historical V20-03 PF/parity/evidence | Not current R088 / not untouched OOS |
| [`V20-03/evidence/archive_original/V20-03/README_RUN_RU.md`](V20-03/evidence/archive_original/V20-03/README_RUN_RU.md) | `839cd4605607bcc2718e713a480ee2cf53bc7d93` | SOURCE_EVIDENCE | Historical V20-03 PF/parity/evidence | Not current R088 / not untouched OOS |
| [`V20-03/evidence/archive_original/V20-03/STRESS_REPORT_RU.md`](V20-03/evidence/archive_original/V20-03/STRESS_REPORT_RU.md) | `ff70179c6a740ae84108161a62b4e30e37fa1a80` | SOURCE_EVIDENCE | Historical V20-03 PF/parity/evidence | Not current R088 / not untouched OOS |
| [`V20-03/evidence/SOURCES_RU.md`](V20-03/evidence/SOURCES_RU.md) | `893046cd9cd0176045468c086a0fea2419adf870` | SOURCE_EVIDENCE | Historical V20-03 PF/parity/evidence | Not current R088 / not untouched OOS |
| [`V20-03/PUBLICATION_RU.md`](V20-03/PUBLICATION_RU.md) | `241716e8ef7eab79d2445685caa340bda2ac47ab` | SOURCE_EVIDENCE | Historical V20-03 PF/parity/evidence | Not current R088 / not untouched OOS |
| [`V20-03/README_RUN_RU.md`](V20-03/README_RUN_RU.md) | `2afbd3c395fd3b802b67b0632218cc9e1eec75b8` | RESEARCH | Historical V20-03 PF/parity/evidence | Not current R088 / not untouched OOS |
| [`V20-03/REPORT_RU.md`](V20-03/REPORT_RU.md) | `bcec167b86844b686cd589c1f330d65ed96edab0` | RESEARCH | Historical V20-03 PF/parity/evidence | Not current R088 / not untouched OOS |
| [`V20-03/ROLL_POLICY_LOCKED_V1.md`](V20-03/ROLL_POLICY_LOCKED_V1.md) | `9f3af33ee440b4ca2ee494c58d85bb6b5fe7825a` | SOURCE_EVIDENCE | Historical V20-03 PF/parity/evidence | Not current R088 / not untouched OOS |
| [`V20-03/ROLL_POLICY.md`](V20-03/ROLL_POLICY.md) | `9f3af33ee440b4ca2ee494c58d85bb6b5fe7825a` | RESEARCH | Historical V20-03 PF/parity/evidence | Not current R088 / not untouched OOS |
| [`V20-03/STRESS_REPORT_RU.md`](V20-03/STRESS_REPORT_RU.md) | `cbe952c276a7ee47560d2e66432cfe76586c816e` | RESEARCH | Historical V20-03 PF/parity/evidence | Not current R088 / not untouched OOS |
| [`V20-04/CAP4_VS_CAP2_RESEARCH_20261103_RU.md`](V20-04/CAP4_VS_CAP2_RESEARCH_20261103_RU.md) | `f950e0a0ce974c96434be0cd6b1941d1a734a4c1` | RESEARCH | Market/regime/capital experiments | Keep historical, not LIVE |
| [`V20-04/CASH_AWARE_N4_FULL_REPLAY_20261104_RU.md`](V20-04/CASH_AWARE_N4_FULL_REPLAY_20261104_RU.md) | `621735c94b93d124d1025556958a782611a410d4` | RESEARCH | Market/regime/capital experiments | Keep historical, not LIVE |
| [`V20-04/CODEX_FINAL_TASK_SINGLE_INSTRUMENT_CARD_RU.md`](V20-04/CODEX_FINAL_TASK_SINGLE_INSTRUMENT_CARD_RU.md) | `0345a6f55338e0b0ebab1613e028d43faf2d7e72` | SUPERSEDED | Historical Codex task | Do not execute as current |
| [`V20-04/CODEX_TASK_CARD_HISTORICAL_EPOCHS_RU.md`](V20-04/CODEX_TASK_CARD_HISTORICAL_EPOCHS_RU.md) | `d8b4181d05a92184e550a77a927b8e2a3dfbcf0f` | SUPERSEDED | Historical Codex task | Do not execute as current |
| [`V20-04/CODEX_TASK_MARKET_CARD_04_2_RU.md`](V20-04/CODEX_TASK_MARKET_CARD_04_2_RU.md) | `f0f37c75cf81c85aab1b9331a38ef21111aaa9ee` | SUPERSEDED | Historical Codex task | Do not execute as current |
| [`V20-04/CODEX_TASK_MARKET_CARD_RANGES_FINAL_RU.md`](V20-04/CODEX_TASK_MARKET_CARD_RANGES_FINAL_RU.md) | `b20d6639629efb552aae39451516eae305cdd3dd` | SUPERSEDED | Historical Codex task | Do not execute as current |
| [`V20-04/CODEX_TASK_ROLLING_RAW_INSTRUMENT_CARD_RU.md`](V20-04/CODEX_TASK_ROLLING_RAW_INSTRUMENT_CARD_RU.md) | `3000687bf6d66823b16e674be77c54be59d896c7` | SUPERSEDED | Historical Codex task | Do not execute as current |
| [`V20-04/DECISION_MARKET_CARD_MINIMALISM_20261022_RU.md`](V20-04/DECISION_MARKET_CARD_MINIMALISM_20261022_RU.md) | `c82f99ca3ea544f63754ce7b3e9dcf91107d9dff` | RESEARCH | Market/regime/capital experiments | Keep historical, not LIVE |
| [`V20-04/FIXED_RISK_BASE_COLLATERAL_20261103_RU.md`](V20-04/FIXED_RISK_BASE_COLLATERAL_20261103_RU.md) | `b8f4e9794c6d5d2f47f754b3302720b927eae50a` | RESEARCH | Market/regime/capital experiments | Keep historical, not LIVE |
| [`V20-04/FROZEN_PARITY_PROGRESS_RU.md`](V20-04/FROZEN_PARITY_PROGRESS_RU.md) | `e006e05ed689075cd06d4da009856a221cbf7eff` | SOURCE_EVIDENCE | Dated source/risk/decision evidence | New R088 map is authoritative |
| [`V20-04/GO_EQUAL_RISK_N4_RESEARCH_20261103_RU.md`](V20-04/GO_EQUAL_RISK_N4_RESEARCH_20261103_RU.md) | `be88db0f9d72677bb8bed98da3c27b2910da64a2` | RESEARCH | Market/regime/capital experiments | Keep historical, not LIVE |
| [`V20-04/INSTRUMENT_REGIME_RELIABILITY_RU.md`](V20-04/INSTRUMENT_REGIME_RELIABILITY_RU.md) | `5875f3d3bbce108079552b226a5569ab3990f814` | RESEARCH | Market/regime/capital experiments | Keep historical, not LIVE |
| [`V20-04/MARKET_CARD_FINAL_ACCEPTANCE_RU.md`](V20-04/MARKET_CARD_FINAL_ACCEPTANCE_RU.md) | `b120456e0a1c2f3dcfc318c3d0ba72990435bbc6` | RESEARCH | Market/regime/capital experiments | Keep historical, not LIVE |
| [`V20-04/MARKET_CARD_RANGES_FINAL_RU.md`](V20-04/MARKET_CARD_RANGES_FINAL_RU.md) | `828019374c999dd099f1c0f0746e06ee2947d449` | RESEARCH | Market/regime/capital experiments | Keep historical, not LIVE |
| [`V20-04/MARKET_CARD_RANGES_PROTOCOL_RU.md`](V20-04/MARKET_CARD_RANGES_PROTOCOL_RU.md) | `240fa1f4d78e00703fef4eddd9642a8feb8e5834` | RESEARCH | Market/regime/capital experiments | Keep historical, not LIVE |
| [`V20-04/MARKET_CARD_RESEARCH_V2_RU.md`](V20-04/MARKET_CARD_RESEARCH_V2_RU.md) | `a55308801b9b3b7629b3b756d88805e768fa6609` | RESEARCH | Market/regime/capital experiments | Keep historical, not LIVE |
| [`V20-04/MARKET_EPOCH_COMPARISON_RU.md`](V20-04/MARKET_EPOCH_COMPARISON_RU.md) | `3bba02a64eeb245c5d6dcd61ff33e7aae340e398` | RESEARCH | Market/regime/capital experiments | Keep historical, not LIVE |
| [`V20-04/MARKET_OUTCOME_EXPLORATORY_RU.md`](V20-04/MARKET_OUTCOME_EXPLORATORY_RU.md) | `acb16814aac3553437b73e5dd5baf1fee2a4e394` | RESEARCH | Market/regime/capital experiments | Keep historical, not LIVE |
| [`V20-04/MARKET_PHASE_CAUSAL_PROBE_RU.md`](V20-04/MARKET_PHASE_CAUSAL_PROBE_RU.md) | `bcfe8a1e9fc2d1640858feda8cb061aeec96953b` | RESEARCH | Market/regime/capital experiments | Keep historical, not LIVE |
| [`V20-04/MARKET_REFERENCE_2023_2026_RU.md`](V20-04/MARKET_REFERENCE_2023_2026_RU.md) | `6bf55b220da262d7ee554d4a7f533830e8588c76` | RESEARCH | Market/regime/capital experiments | Keep historical, not LIVE |
| [`V20-04/MARKET_SUITABILITY_CARD_RU.md`](V20-04/MARKET_SUITABILITY_CARD_RU.md) | `66be54700b4df524cb5d27496b16b13378158c3e` | RESEARCH | Market/regime/capital experiments | Keep historical, not LIVE |
| [`V20-04/README_RU.md`](V20-04/README_RU.md) | `0f8e091ab49813e7dea52de161b45a3ac8b5f30f` | HISTORICAL | Stage V20-04 research chronology | Superseded as LIVE status |
| [`V20-04/REGIME_CURRENT_CONFIRMATION_RU.md`](V20-04/REGIME_CURRENT_CONFIRMATION_RU.md) | `429148d29878a73588a0288575c88c15b6dc4955` | RESEARCH | Market/regime/capital experiments | Keep historical, not LIVE |
| [`V20-04/REGIME_FINAL_COMPARISON_PROTOCOL_RU.md`](V20-04/REGIME_FINAL_COMPARISON_PROTOCOL_RU.md) | `ebc9c51dd63961def854d35adb5298a3faf5d004` | RESEARCH | Market/regime/capital experiments | Keep historical, not LIVE |
| [`V20-04/REGIME_FINAL_COMPARISON_RU.md`](V20-04/REGIME_FINAL_COMPARISON_RU.md) | `9ccacb3c56bbca90089027f3ab844e272e8915b3` | RESEARCH | Market/regime/capital experiments | Keep historical, not LIVE |
| [`V20-04/REGIME_RELIABILITY_FOLLOWUP_RU.md`](V20-04/REGIME_RELIABILITY_FOLLOWUP_RU.md) | `ee641ba664f05a3264e41a05819351b327695233` | RESEARCH | Market/regime/capital experiments | Keep historical, not LIVE |
| [`V20-04/REGIME_RESEARCH_PROTOCOL_RU.md`](V20-04/REGIME_RESEARCH_PROTOCOL_RU.md) | `f2b4fe7ffe2ecfc894a307765b22fc161af1cabd` | RESEARCH | Market/regime/capital experiments | Keep historical, not LIVE |
| [`V20-04/REGIME_RESEARCH_RU.md`](V20-04/REGIME_RESEARCH_RU.md) | `74ff02926a48f02bb5d9f99c3353445d1ebadf6b` | RESEARCH | Market/regime/capital experiments | Keep historical, not LIVE |
| [`V20-04/RESEARCH_ARCHIVE_DECISIONS_20261023_RU.md`](V20-04/RESEARCH_ARCHIVE_DECISIONS_20261023_RU.md) | `ec46dedc04068d1f0faa842acec7c7cc441106a0` | SOURCE_EVIDENCE | Dated source/risk/decision evidence | New R088 map is authoritative |
| [`V20-04/RISK_04_4_PROGRESS_RU.md`](V20-04/RISK_04_4_PROGRESS_RU.md) | `6502dcd149037d793ccf3b8d4e768d0cad2b7486` | SOURCE_EVIDENCE | Dated source/risk/decision evidence | New R088 map is authoritative |
| [`V20-04/ROLLING_RAW_CARD_ACCEPTANCE_RU.md`](V20-04/ROLLING_RAW_CARD_ACCEPTANCE_RU.md) | `52f736507a45b923dced369d165b2089c4ee4ac8` | RESEARCH | Market/regime/capital experiments | Keep historical, not LIVE |
| [`V20-04/SOURCE_MAP.md`](V20-04/SOURCE_MAP.md) | `bd7ba19442f86d0e69aaefe37a27553b9b2b54f2` | SOURCE_EVIDENCE | Dated source/risk/decision evidence | New R088 map is authoritative |
| [`V20-04/V20_2012_2026_FINAL_RU.md`](V20-04/V20_2012_2026_FINAL_RU.md) | `aaa8676ce27d7fac5e518e692ae7c36b081b731d` | RESEARCH | Market/regime/capital experiments | Keep historical, not LIVE |
| [`V20-04/V20_2012_MONITORING_PROTOCOL_RU.md`](V20-04/V20_2012_MONITORING_PROTOCOL_RU.md) | `71023bc6583849d0f7ee0173d51e98cdbec83826` | RESEARCH | Market/regime/capital experiments | Keep historical, not LIVE |
| [`V20-04/V20_CALENDAR_REVIEW_FINAL_RU.md`](V20-04/V20_CALENDAR_REVIEW_FINAL_RU.md) | `24eab96552c5f87a9171586e598925002a7340df` | RESEARCH | Market/regime/capital experiments | Keep historical, not LIVE |
| [`V20-04/V20_CALENDAR_REVIEW_PROTOCOL_RU.md`](V20-04/V20_CALENDAR_REVIEW_PROTOCOL_RU.md) | `94f9be6f07d39e6455b0dbc92c759544690e4cf0` | RESEARCH | Market/regime/capital experiments | Keep historical, not LIVE |
| [`V20-04/V20_SUITABILITY_FINAL_RU.md`](V20-04/V20_SUITABILITY_FINAL_RU.md) | `19b39c4e7a114165eb82ef9fd3a631fa7aaec7a0` | RESEARCH | Market/regime/capital experiments | Keep historical, not LIVE |
| [`V20-04/V20_SUITABILITY_PROTOCOL_RU.md`](V20-04/V20_SUITABILITY_PROTOCOL_RU.md) | `09aa292ad24118fcf5eca768abb72b9e36712daf` | RESEARCH | Market/regime/capital experiments | Keep historical, not LIVE |
| [`V20-05/REPORT_RU.md`](V20-05/REPORT_RU.md) | `4994143ed8ae4e436d53923fad0723444a543654` | HISTORICAL | Dated stage V20-05/06/07 | Not current broker state |
| [`V20-06/README_RU.md`](V20-06/README_RU.md) | `a1fabd4d945ff329e1af8dd0e196e279082bbbb4` | HISTORICAL | Dated stage V20-05/06/07 | Not current broker state |
| [`V20-07/README_RU.md`](V20-07/README_RU.md) | `60dab5019661a92bcc00905f094d1a579ceb6fcb` | HISTORICAL | Dated stage V20-05/06/07 | Not current broker state |
| [`V20-08/ACCEPTANCE_08_3_RU.md`](V20-08/ACCEPTANCE_08_3_RU.md) | `932ea61deabbb7e2a9d303b0cd3dfdd01ffc2cbc` | SOURCE_EVIDENCE | Dated incident / acceptance evidence | Keep past SHA/date |
| [`V20-08/CONTROL_CENTER_HANDOFF_20261027_RU.md`](V20-08/CONTROL_CENTER_HANDOFF_20261027_RU.md) | `e4e858727092f7f8a0ebe0bab9a5796274f0f456` | HISTORICAL | V20-08 dated README/runbook/handoff | Use installed R088 manifest first |
| [`V20-08/H1_EXECUTION_CONFORMANCE_20261027.md`](V20-08/H1_EXECUTION_CONFORMANCE_20261027.md) | `62e875e6d1bae0e92dc22ddc9a302b23017d9f5f` | SOURCE_EVIDENCE | Dated incident / acceptance evidence | Keep past SHA/date |
| [`V20-08/IMPLEMENTATION_08_1_RU.md`](V20-08/IMPLEMENTATION_08_1_RU.md) | `e31e4ddbb673b072c7a87b0bc589b7b49310e5ce` | HISTORICAL | V20-08 dated README/runbook/handoff | Use installed R088 manifest first |
| [`V20-08/LIVE_RELEASE_R088_20261120_RU.md`](V20-08/LIVE_RELEASE_R088_20261120_RU.md) | `d61b0ac5b30ff706534f4b5c65e523705aa04d3b` | CURRENT | Verified R088 20-Nov install snapshot | Not fresh ARMED |
| [`V20-08/R070_COMBINED_RELEASE_PACKAGE_20261117_RU.md`](V20-08/R070_COMBINED_RELEASE_PACKAGE_20261117_RU.md) | `af3a2dd85753624c560e9d48ea3547652f0e1b64` | RESEARCH | Pre-final candidate, sometimes EXT2 ON | Do not install/activate |
| [`V20-08/R070_FINAM_M15_SOURCE_AUDIT_20261116_RU.md`](V20-08/R070_FINAM_M15_SOURCE_AUDIT_20261116_RU.md) | `c4961802583902fd147b99da2e99da9988dafa73` | SOURCE_EVIDENCE | Dated incident / acceptance evidence | Keep past SHA/date |
| [`V20-08/R070_FINAM_SLTP_SUPPORT_REQUEST_RU.md`](V20-08/R070_FINAM_SLTP_SUPPORT_REQUEST_RU.md) | `69b203a795f7f441befd351aa517271a696dd07e` | RESEARCH | Pre-final candidate, sometimes EXT2 ON | Do not install/activate |
| [`V20-08/R070_LIVE_HALT_INCIDENT_20261117_RU.md`](V20-08/R070_LIVE_HALT_INCIDENT_20261117_RU.md) | `ad0cd9932de1df1f0b537c0f3a9d968282cbc8ec` | SOURCE_EVIDENCE | Dated incident / acceptance evidence | Keep past SHA/date |
| [`V20-08/R070_N4_M15_EXPORT_PARITY_20261117_RU.md`](V20-08/R070_N4_M15_EXPORT_PARITY_20261117_RU.md) | `16f128a0db8add8d0217ea945538bd572ce43068` | SOURCE_EVIDENCE | Dated incident / acceptance evidence | Keep past SHA/date |
| [`V20-08/R070_STAGING_STATUS_20261115_RU.md`](V20-08/R070_STAGING_STATUS_20261115_RU.md) | `96ed4e569e0183b93b4b09890f25ca968e904f2e` | RESEARCH | Pre-final candidate, sometimes EXT2 ON | Do not install/activate |
| [`V20-08/R070_TRADE_LEDGER_M15_PARITY_20261116_RU.md`](V20-08/R070_TRADE_LEDGER_M15_PARITY_20261116_RU.md) | `953b6d7c3913f43b342a544ce7d2de0349d3a264` | SOURCE_EVIDENCE | Dated incident / acceptance evidence | Keep past SHA/date |
| [`V20-08/R088_HOLD5_OFFLINE_REPORT_20261118_RU.md`](V20-08/R088_HOLD5_OFFLINE_REPORT_20261118_RU.md) | `6b00eb1253cb7ff3e28cd120ab33acad85b2f20d` | RESEARCH | Pre-final candidate, sometimes EXT2 ON | Do not install/activate |
| [`V20-08/README_RU.md`](V20-08/README_RU.md) | `086c9a102c47cb509bf21f1317eccb195fe1062f` | HISTORICAL | V20-08 dated README/runbook/handoff | Use installed R088 manifest first |
| [`V20-08/RUNBOOK_08_5_RU.md`](V20-08/RUNBOOK_08_5_RU.md) | `08df395d09284f17a06b5ab2eeda4452e522bba4` | HISTORICAL | V20-08 dated README/runbook/handoff | Use installed R088 manifest first |

## 4. Important non-Markdown artifacts / boundaries

- `PUBLICATION_MANIFEST_SHA256.txt`, V20-03 SHA files, `docs/TASK_TRACKER.csv`, stage JSON/CSV, original outcomes — retained `SOURCE_EVIDENCE` or `RESEARCH`, **not** current installed runtime or automatic LIVE authorization.
- `v20_runtime/*.py`, `v20_runtime/tests/*.py`, nine `V20-08/*.patch`, pinned PowerShell and `.github/workflows/v20-08-live-windows.yml` are technical **SOURCE**, mapped with exact SHA in [R088 ARCHITECTURE](R088_ARCHITECTURE_AND_SAFETY_20261122.md).
- Private SQLite, DPAPI, FINAM, operator JSONL, active position/SLTP, Task/CC state = **NOT READ / NOT VERIFIED**. Cold restore and new Kimi offline exam also pending, per project phase II/III.
- Original research and negative outcomes preserved, no old figures amended; no change to H1, old IntradayLab, Control Center, TRL or root recovery.
