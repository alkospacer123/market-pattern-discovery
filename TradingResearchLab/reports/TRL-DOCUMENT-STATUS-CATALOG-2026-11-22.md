# TRL — полный реестр статусов документов и исходных файлов

**Контрольный pin:** `main=0e569be6cb3c7cce1f7224e7f1fef6be38f6ba52`, TRL subtree `a5764c5e693f43cbb09469badf26c8dbe3fd3fa9`, `truncated=false`. Этот реестр перечисляет **все 169 Git blob** внутри `TradingResearchLab/` на контрольный SHA (включая .md/.json/.csv/.py). Это **структурная классификация**, не сертификат результата каждого исторического эксперимента.

**Приоритет:** [корневой документационный authority](../../recovery/DOCUMENTATION_AUTHORITY_2026-11-22.md) → [проектный AGENTS](../AGENTS.md) → [Kimi Start Here](TRL-NOV-2026-KIMI-START-HERE.md) / [final Closeout](TRL-NOV-2026-FINAL-CLOSEOUT.md). Исследовательская классификация `SUPERSEDED` означает **старую рекомендацию**, но её численные результаты остаются частью истории и не удаляются.

## Статусная карта

| Статус | Количество | Назначение |
|---|---:|---|
| `CURRENT` | 14 | Действующая навигация/регламент/последний выбор владельца |
| `HISTORICAL` | 74 | Сохранённый снимок прежнего состояния, исследовательский дневник и архивные материалы |
| `RESEARCH` | 47 | Первичный исторический исследовательский отчёт; не действующая инструкция LIVE |
| `SOURCE_EVIDENCE` | 30 | Код, frozen-протокол, CSV/JSON или манифест; не гарантирует автономной воспроизводимости |
| `SUPERSEDED` | 4 | Ранние рекомендации, переопределённые новым решением; сохранять для provenance |
| `UNKNOWN` | 0 | Для присвоения статуса недостаточно информации |

**Важно:** здесь нет статуса `REPRODUCIBLE_VERIFIED`; статусы этой таблицы — **класс документа**, а не результат независимого replay. Подробные data/code/replay gaps см. в [реестре исследований](TRL-RESEARCH-REGISTRY-2026-11-22.md).

## Полный индекс

| Файл относительно `TradingResearchLab/` | Git blob SHA1 | Статус |
|---|---|---|
| [`AGENTS.md`](../AGENTS.md) | `65c585b1e34015882b66aef393947e4541844c13` | `CURRENT` |
| [`evolution/2026-11-12-r051-45-months-obv-portfolio-comparison.md`](../evolution/2026-11-12-r051-45-months-obv-portfolio-comparison.md) | `16f9eacfb3b27c9fd48fba427be68ccf621d44b8` | `RESEARCH` |
| [`evolution/2026-11-12-r056-gld-shallow-obv-late-entry-stop-cluster.md`](../evolution/2026-11-12-r056-gld-shallow-obv-late-entry-stop-cluster.md) | `a329a0a516e056366677647e3eef94c003edb561` | `RESEARCH` |
| [`evolution/2026-11-12-r057-v20-loss-attribution-and-pullback.md`](../evolution/2026-11-12-r057-v20-loss-attribution-and-pullback.md) | `84819115e3ea977861a088dfe54a104e1fb8d0e0` | `RESEARCH` |
| [`evolution/2026-11-12-r058-all-stop-loss-forensics.md`](../evolution/2026-11-12-r058-all-stop-loss-forensics.md) | `57cedd47dd273ff07cc25b293bf1006c339fcac2` | `RESEARCH` |
| [`evolution/2026-11-12-r059-v20-entry-quality-gld-obv.md`](../evolution/2026-11-12-r059-v20-entry-quality-gld-obv.md) | `46853601f5f8c408d9cbda62f9d70b8f63a0ab2d` | `RESEARCH` |
| [`evolution/2026-11-12-r060-exact-cash-parity-and-filters.md`](../evolution/2026-11-12-r060-exact-cash-parity-and-filters.md) | `431b6e73eb78b28d1b8a9c7908e93fa7c9afa7e3` | `RESEARCH` |
| [`evolution/2026-11-12-r061-shallow-inside-8050-and-level-retest.md`](../evolution/2026-11-12-r061-shallow-inside-8050-and-level-retest.md) | `ca4cf4149b340f4761dcdc2a81b68ec366224b6c` | `RESEARCH` |
| [`evolution/2026-11-12-r062-new-m15-validation-and-retest.md`](../evolution/2026-11-12-r062-new-m15-validation-and-retest.md) | `5cf5f60d5b171c2000963dd034fe5159f5efbc3e` | `RESEARCH` |
| [`evolution/2026-11-12-r063-frozen-454545-m15-retest.md`](../evolution/2026-11-12-r063-frozen-454545-m15-retest.md) | `52bde1c54b02ffaa6fe991907d6149a8c656e5bb` | `RESEARCH` |
| [`evolution/2026-11-12-r064-multitimeframe-swing-retest.md`](../evolution/2026-11-12-r064-multitimeframe-swing-retest.md) | `3b7a266699f508d61d4943305617915954bd031b` | `RESEARCH` |
| [`evolution/2026-11-12-r065-swing-three-architectures.md`](../evolution/2026-11-12-r065-swing-three-architectures.md) | `2918c7b11fa88beeb1002796c8615c7ca9eaa1d9` | `RESEARCH` |
| [`evolution/2026-11-12-r066-assembly-selection-limit-entry-m5-precheck.md`](../evolution/2026-11-12-r066-assembly-selection-limit-entry-m5-precheck.md) | `9788cf7a3a14f0b017fd5ed21a6d02f43d13a03f` | `RESEARCH` |
| [`evolution/2026-11-12-r067-limit-entry-full-m5-cash-replay.md`](../evolution/2026-11-12-r067-limit-entry-full-m5-cash-replay.md) | `62596088694aeac9312b50d44807f867482c5176` | `RESEARCH` |
| [`evolution/2026-11-12-v20-assembly-selection.md`](../evolution/2026-11-12-v20-assembly-selection.md) | `e1f2b973b08058412cd3ae3bc1ebe1dff091540f` | `RESEARCH` |
| [`evolution/2026-11-13-r068-early-trend-capture-negative.md`](../evolution/2026-11-13-r068-early-trend-capture-negative.md) | `6655f879062754c5325154d2bb39576f6cb817c2` | `RESEARCH` |
| [`evolution/2026-11-13-r069-first-impulse-forensics.md`](../evolution/2026-11-13-r069-first-impulse-forensics.md) | `eecd57d2a3eb227a97a457701941729d1d10b49a` | `RESEARCH` |
| [`evolution/2026-11-15-r070-final-v20-assembly-and-live-handoff.md`](../evolution/2026-11-15-r070-final-v20-assembly-and-live-handoff.md) | `e3033fac1365f75bb79eeb76cdaf0e0dbb820d74` | `SUPERSEDED` |
| [`evolution/2026-11-15-r071-monthly-performance-capital-ratio.md`](../evolution/2026-11-15-r071-monthly-performance-capital-ratio.md) | `c4e2c86e98974c6d2e35d9a577c40ffe917258a6` | `RESEARCH` |
| [`evolution/2026-11-16-r073-ext2-vs-noext2-tp6-protect3.md`](../evolution/2026-11-16-r073-ext2-vs-noext2-tp6-protect3.md) | `471ceeb76d834105287ce17c8c5d2c8b4327fa96` | `RESEARCH` |
| [`evolution/2026-11-16-r074-ext2-imoex-inside-direct-replay.md`](../evolution/2026-11-16-r074-ext2-imoex-inside-direct-replay.md) | `28a23e12414659af2800356d1e39ed2fc4d71a74` | `RESEARCH` |
| [`evolution/2026-11-16-r075-imoex-ext2-new-data.md`](../evolution/2026-11-16-r075-imoex-ext2-new-data.md) | `c54012b490097f68c2a4231dfab7cd613e282df9` | `RESEARCH` |
| [`evolution/2026-11-16-r076-mom8-imoex-direct-test.md`](../evolution/2026-11-16-r076-mom8-imoex-direct-test.md) | `2eb2e4b7f4151fb87549326e84c2df32b91cb2e3` | `RESEARCH` |
| [`evolution/2026-11-18-r079-trailing-stops-n4.md`](../evolution/2026-11-18-r079-trailing-stops-n4.md) | `1eca93dad8bd71af5f41f182174af32bed079690` | `RESEARCH` |
| [`evolution/2026-11-18-r080-no-time-no-tp-trail.md`](../evolution/2026-11-18-r080-no-time-no-tp-trail.md) | `88ff4cf8dbf9b887020f9b934818b74e25d3e2f1` | `RESEARCH` |
| [`evolution/archive-2026-11/R090-Allocation-Findings-From-Three-Sources-20261119.md`](../evolution/archive-2026-11/R090-Allocation-Findings-From-Three-Sources-20261119.md) | `eea950de4bed25c636466e9b211157ae113b7878` | `HISTORICAL` |
| [`evolution/archive-2026-11/R091-Capital-Allocation-Research-20261119.md`](../evolution/archive-2026-11/R091-Capital-Allocation-Research-20261119.md) | `2de90e7b3935f6c436572216a4c69ad63a8e8c00` | `HISTORICAL` |
| [`evolution/archive-2026-11/R092-Capital-Margin-Frontier-20261119.md`](../evolution/archive-2026-11/R092-Capital-Margin-Frontier-20261119.md) | `fdf1484e11a74453aefa2ddc1004e5a2af1d8bf9` | `HISTORICAL` |
| [`evolution/archive-2026-11/R093-Source-Exposure-Audit-20261119.md`](../evolution/archive-2026-11/R093-Source-Exposure-Audit-20261119.md) | `bcd9b8e741545daeca73af5baf004c6f69277e8b` | `HISTORICAL` |
| [`evolution/archive-2026-11/R094-Capital-Reserve-20261119.md`](../evolution/archive-2026-11/R094-Capital-Reserve-20261119.md) | `7012587458848373b0e2a101d9a8d0aa772e5d03` | `HISTORICAL` |
| [`evolution/archive-2026-11/R095-Capital-Scale-Research-20261119.md`](../evolution/archive-2026-11/R095-Capital-Scale-Research-20261119.md) | `aa490282b26353893248a6521b806b5dce1a90c9` | `HISTORICAL` |
| [`evolution/archive-2026-11/R096-Research-Decision-20261119.md`](../evolution/archive-2026-11/R096-Research-Decision-20261119.md) | `839086f557d7ef957d5432440b0e7fff6e335a96` | `HISTORICAL` |
| [`evolution/archive-2026-11/README.md`](../evolution/archive-2026-11/README.md) | `7fdf8c7e2bf94113bb9c692dc363fbba40145eae` | `HISTORICAL` |
| [`evolution/artifacts/r051-v20-603045-vs-sh-inside-8154-monthly-2023-2026.csv`](../evolution/artifacts/r051-v20-603045-vs-sh-inside-8154-monthly-2023-2026.csv) | `650c858ebb8b22b7420f5d1e412cad6e8e8fbdd1` | `SOURCE_EVIDENCE` |
| [`evolution/MANUAL_FINAM_MONTHLY_INPUT.md`](../evolution/MANUAL_FINAM_MONTHLY_INPUT.md) | `1d3ddc6bf9a11080267c553855775a9598b5601e` | `CURRENT` |
| [`evolution/README.md`](../evolution/README.md) | `54753a79e9417b4b7ba5a0ba31bec13a3ef17c5c` | `CURRENT` |
| [`evolution/TRL-R086-HOLD5-SESSION-SWEEP-20261118.md`](../evolution/TRL-R086-HOLD5-SESSION-SWEEP-20261118.md) | `1612293538973130c08c7204ab73f4aa8fe85da0` | `RESEARCH` |
| [`evolution/TRL-R089-HOLD5-WITHOUT-EXT2-DIGEST-20261118.md`](../evolution/TRL-R089-HOLD5-WITHOUT-EXT2-DIGEST-20261118.md) | `bfb02168decd2357386d39e129c997ed3564be0e` | `RESEARCH` |
| [`evolution/TRL-R089-HOLD5-WITHOUT-EXT2-ORIGINAL-20261118.md`](../evolution/TRL-R089-HOLD5-WITHOUT-EXT2-ORIGINAL-20261118.md) | `7c3f7f5a8ebaa6ecf99351a5137845ba35dd7e9e` | `RESEARCH` |
| [`evolution/TRL-R097-FULL-CAPITAL-2023-2026.md`](../evolution/TRL-R097-FULL-CAPITAL-2023-2026.md) | `b9db9c956d2ec69f2c27a469ce7125baf8dcc78d` | `RESEARCH` |
| [`evolution/TRL-R098-CONDITIONAL-ALLOCATION-20261119.md`](../evolution/TRL-R098-CONDITIONAL-ALLOCATION-20261119.md) | `8f022f818b5b7f64ef5e50ae33e25c3726825fbd` | `SUPERSEDED` |
| [`journal/2026-10-31-trl-00-closeout.md`](../journal/2026-10-31-trl-00-closeout.md) | `4644f24243f2c5775e87eb9298447441b9fc4022` | `HISTORICAL` |
| [`journal/2026-10-31-trl-00-followup.md`](../journal/2026-10-31-trl-00-followup.md) | `1e283c9614e33a579e29d0c08ff57800f72eb59b` | `HISTORICAL` |
| [`journal/2026-10-31-trl-00-start.md`](../journal/2026-10-31-trl-00-start.md) | `589237eafd757ec1122cc58d300f88f32195a272` | `HISTORICAL` |
| [`journal/2026-10-31-trl-00-structure.md`](../journal/2026-10-31-trl-00-structure.md) | `16d055172793f4a9df78888a70cc9908487036c7` | `HISTORICAL` |
| [`journal/2026-10-31-trl-00-tester-reproducibility.md`](../journal/2026-10-31-trl-00-tester-reproducibility.md) | `fcde1633d96692f80beee3dd07aaee4be9049f07` | `HISTORICAL` |
| [`journal/2026-10-31-trl-01-manual-finam.md`](../journal/2026-10-31-trl-01-manual-finam.md) | `2856bbfc17b391052a94074d1eeb5a5dbedeb3d3` | `HISTORICAL` |
| [`journal/2026-10-31-trl-01-priority-handoff.md`](../journal/2026-10-31-trl-01-priority-handoff.md) | `ef1b6a83639f410268de8b7af6ccadf2b39a62a2` | `HISTORICAL` |
| [`journal/2026-10-31-trl-01-start.md`](../journal/2026-10-31-trl-01-start.md) | `c02a2d724a3193f227ca7f24a5d4ca2886ce27a8` | `HISTORICAL` |
| [`journal/2026-10-31-trl-calendar-approved.md`](../journal/2026-10-31-trl-calendar-approved.md) | `ee2c228f9811892b5d28126957240ca76546ff9c` | `HISTORICAL` |
| [`journal/2026-11-11-sts-formation.md`](../journal/2026-11-11-sts-formation.md) | `bcbc2e44b888e7bbe45099c6c7b16dd953d7d3a1` | `HISTORICAL` |
| [`journal/2026-11-11-sts-r040-three-accounts.md`](../journal/2026-11-11-sts-r040-three-accounts.md) | `9ef8ba7b42c9219e25a4998d3072a40b629af2a6` | `HISTORICAL` |
| [`journal/2026-11-11-sts-r041.md`](../journal/2026-11-11-sts-r041.md) | `4084762fcde2e2b2f130db43870967d2a50fa3a2` | `HISTORICAL` |
| [`journal/2026-11-11-sts-r042.md`](../journal/2026-11-11-sts-r042.md) | `984b863fab218fab1844bec8cf74bf4fb0683c62` | `HISTORICAL` |
| [`journal/2026-11-11-sts-r043.md`](../journal/2026-11-11-sts-r043.md) | `801b01fca8a363cf0d014d7f112bb60804ab3a5a` | `HISTORICAL` |
| [`journal/2026-11-11-sts-r044-risk-parity.md`](../journal/2026-11-11-sts-r044-risk-parity.md) | `376af76abf1bcdb4da3d11a42260b2aab2bd60b7` | `HISTORICAL` |
| [`journal/2026-11-11-sts-r045-v20-shallow-mtm.md`](../journal/2026-11-11-sts-r045-v20-shallow-mtm.md) | `e71649faddf88ed6eb1d899c1913fd20f6d46dac` | `HISTORICAL` |
| [`journal/2026-11-11-sts-r046-inside-missed-trends.md`](../journal/2026-11-11-sts-r046-inside-missed-trends.md) | `38cb823d21de5241136c759343a8350c61a94c75` | `HISTORICAL` |
| [`journal/2026-11-11-sts-r047-missed-trends.md`](../journal/2026-11-11-sts-r047-missed-trends.md) | `c07218cc279e64caf67e648cdd379dfa17818718` | `HISTORICAL` |
| [`journal/2026-11-11-sts-r048-early-quality.md`](../journal/2026-11-11-sts-r048-early-quality.md) | `65f87bd667e2d9b0c4f0b52318cac8a752f7037d` | `HISTORICAL` |
| [`journal/2026-11-11-sts-r049-compression.md`](../journal/2026-11-11-sts-r049-compression.md) | `d40c449ab7d1f6ff865361bdd6a70512d05d8433` | `HISTORICAL` |
| [`journal/2026-11-11-sts-r050-trend-start-attempts.md`](../journal/2026-11-11-sts-r050-trend-start-attempts.md) | `faa0fce33770d13ef56acf8c9b34e44a3d9ffaf4` | `HISTORICAL` |
| [`journal/2026-11-11-sts-r051-monthly-portfolio-gld.md`](../journal/2026-11-11-sts-r051-monthly-portfolio-gld.md) | `96159f1699ddac99aaffab787b208e5a441987ed` | `HISTORICAL` |
| [`journal/2026-11-11-sts-r051-portfolio-monthly-gld.md`](../journal/2026-11-11-sts-r051-portfolio-monthly-gld.md) | `95c2ca172fbf251856e3d88145739578e702d063` | `HISTORICAL` |
| [`journal/2026-11-12-r051-obv-45-month-portfolio-evidence.md`](../journal/2026-11-12-r051-obv-45-month-portfolio-evidence.md) | `47fbc5b349f2dd88b0466ecca7eac1e58c67ed1e` | `HISTORICAL` |
| [`journal/2026-11-12-r056-gld-joint-shallow-obv-exhaustion.md`](../journal/2026-11-12-r056-gld-joint-shallow-obv-exhaustion.md) | `802e0c19d5701031d3bb20b04793e45b28e8a6e2` | `HISTORICAL` |
| [`journal/2026-11-12-r057-v20-loss-quality-atr-pullback.md`](../journal/2026-11-12-r057-v20-loss-quality-atr-pullback.md) | `c4e6886ff81c88d0036a0ee8e04476ea15d085bf` | `HISTORICAL` |
| [`journal/2026-11-12-r058-first-stop-loss-forensics.md`](../journal/2026-11-12-r058-first-stop-loss-forensics.md) | `9a823cb35a06e172dd0b578df0b034aaa7592c13` | `HISTORICAL` |
| [`journal/2026-11-12-r059-v20-entry-quality-gld-obv.md`](../journal/2026-11-12-r059-v20-entry-quality-gld-obv.md) | `f5f218bad583eadd5ed4bcf5e0347115e54f6e5b` | `HISTORICAL` |
| [`journal/2026-11-12-r060-cash-parity-and-forward-hold.md`](../journal/2026-11-12-r060-cash-parity-and-forward-hold.md) | `3f01b9a42102a1f35d14f2f4c69ed0768784a4f5` | `HISTORICAL` |
| [`journal/2026-11-12-r061-8050-structural-retest-decision.md`](../journal/2026-11-12-r061-8050-structural-retest-decision.md) | `d9144aa381c83eab46391ed0c3050b7cd2120a51` | `HISTORICAL` |
| [`journal/2026-11-12-r062-new-m15-ext2-mom8-h4.md`](../journal/2026-11-12-r062-new-m15-ext2-mom8-h4.md) | `b5a4360e1f99762a4f634b42ca7fb28b36c95dbe` | `HISTORICAL` |
| [`journal/2026-11-12-r063-original-454545-m15-retest.md`](../journal/2026-11-12-r063-original-454545-m15-retest.md) | `0d7333bc5ceacfd46d7d1c4f91af4e72ca90f123` | `HISTORICAL` |
| [`journal/2026-11-12-r064-swing-m15-m30-h1-h4.md`](../journal/2026-11-12-r064-swing-m15-m30-h1-h4.md) | `5d7ddab35bc7fd272b0ced536ed6f129436c66cf` | `HISTORICAL` |
| [`journal/2026-11-12-r065-swing-independent-account-decision.md`](../journal/2026-11-12-r065-swing-independent-account-decision.md) | `517286da38bf81114e691f0d47f1e677efa9d6ae` | `HISTORICAL` |
| [`journal/2026-11-12-r066-assembly-and-limits-research-gate.md`](../journal/2026-11-12-r066-assembly-and-limits-research-gate.md) | `8a9018dd5b6383740a97216d1da9e0658cfc6504` | `HISTORICAL` |
| [`journal/2026-11-12-r067-limit-execution-market-retained.md`](../journal/2026-11-12-r067-limit-execution-market-retained.md) | `2c16eb53796a63fb2adaf592b92c098da4116179` | `HISTORICAL` |
| [`journal/2026-11-12-sts-r052-independence-limit-shallow.md`](../journal/2026-11-12-sts-r052-independence-limit-shallow.md) | `ab0aa817315fb029b5ed6096ff231e1a6db96fb4` | `HISTORICAL` |
| [`journal/2026-11-12-sts-r053-three-shallow-limits.md`](../journal/2026-11-12-sts-r053-three-shallow-limits.md) | `0433939e34366403aa4a671e68264ad82153a0ff` | `HISTORICAL` |
| [`journal/2026-11-12-sts-r054-gated-risk-parity.md`](../journal/2026-11-12-sts-r054-gated-risk-parity.md) | `32d869e1ce3826d5f10bf42c353d3477de46673a` | `HISTORICAL` |
| [`journal/2026-11-12-sts-r055-physical-pullbacks-finam-limits.md`](../journal/2026-11-12-sts-r055-physical-pullbacks-finam-limits.md) | `9eda8b12ed9da9c4dc853d0b10a2b1cd20ee3c3f` | `HISTORICAL` |
| [`journal/2026-11-12-v20-research-portfolio-and-execution.md`](../journal/2026-11-12-v20-research-portfolio-and-execution.md) | `06ad5ad5f94e86e214f84cddbea04eff91268d64` | `HISTORICAL` |
| [`journal/2026-11-13-r068-early-trend-capture.md`](../journal/2026-11-13-r068-early-trend-capture.md) | `0bb9910c5c1b18f4736f1fb6aefca68c2ff771ca` | `HISTORICAL` |
| [`journal/2026-11-13-r069-early-impulse-forensics.md`](../journal/2026-11-13-r069-early-impulse-forensics.md) | `7675847be02348077f4bbf4b7d4dfa70576bb2a8` | `HISTORICAL` |
| [`journal/2026-11-15-r070-final-v20-research-selection.md`](../journal/2026-11-15-r070-final-v20-research-selection.md) | `33d4d39e94cd916c25a6894b5c19f39e5bd89f94` | `HISTORICAL` |
| [`journal/2026-11-15-r071-monthly-performance-capital-guide.md`](../journal/2026-11-15-r071-monthly-performance-capital-guide.md) | `c5e430cd23a9da1a315955a758b1681baff36f8b` | `HISTORICAL` |
| [`journal/2026-11-16-ext2-monthly-monitor-decision.md`](../journal/2026-11-16-ext2-monthly-monitor-decision.md) | `d55bdeb6a5c97b89b1f9aed06b0008d91d851d13` | `HISTORICAL` |
| [`journal/2026-11-16-r072-tp6-vs-protection.md`](../journal/2026-11-16-r072-tp6-vs-protection.md) | `690a2b3977f8e949f4dc946050026af92de96635` | `HISTORICAL` |
| [`journal/2026-11-16-r073-ext2-without-ext2.md`](../journal/2026-11-16-r073-ext2-without-ext2.md) | `26d1aaa57135227f7f3195d5aca5d8d7d7fa6a77` | `HISTORICAL` |
| [`journal/2026-11-16-r074-imoex-causal-interpretation-addendum.md`](../journal/2026-11-16-r074-imoex-causal-interpretation-addendum.md) | `c1d760dfb83126ac87166b62d04832cdd4e59301` | `HISTORICAL` |
| [`journal/2026-11-16-r074-imoex-inside-ext2.md`](../journal/2026-11-16-r074-imoex-inside-ext2.md) | `c84efc58228fbda25f842bc7e511db78729612ef` | `HISTORICAL` |
| [`journal/2026-11-16-r075-imoex-ext2-new-data.md`](../journal/2026-11-16-r075-imoex-ext2-new-data.md) | `b5e8710f96125e9334cd7584b1b66172974bf863` | `HISTORICAL` |
| [`journal/2026-11-16-r076-mom8-imoex.md`](../journal/2026-11-16-r076-mom8-imoex.md) | `b7f4469c2a43d9161ea0c2c52168b40bb739533e` | `HISTORICAL` |
| [`journal/2026-11-18-r079-trailing-stops.md`](../journal/2026-11-18-r079-trailing-stops.md) | `6976c172f6dc3caa8eb91551ce8513fee80582e0` | `HISTORICAL` |
| [`journal/2026-11-18-r080-trailing-no-time-decision.md`](../journal/2026-11-18-r080-trailing-no-time-decision.md) | `03b8444c6aad8f9ac6459b7de306b9bd4df2eb4a` | `HISTORICAL` |
| [`journal/2026-11-19-november-closeout.md`](../journal/2026-11-19-november-closeout.md) | `1c79bc67af478380032006091ef2a8e52623dd35` | `HISTORICAL` |
| [`journal/2026-11-19-r098-closeout.md`](../journal/2026-11-19-r098-closeout.md) | `9af1ebc7c0517bad2e59c0cf6577225fb9ac1430` | `HISTORICAL` |
| [`OPERATING_CYCLE.md`](../OPERATING_CYCLE.md) | `c0c77b19797348b1267b009f441e013abb091846` | `CURRENT` |
| [`README.md`](../README.md) | `0e71cb7fb3d09148c8a225c6a252878c7487fcd0` | `CURRENT` |
| [`reports/artifacts/trl-00-tester-reproducibility-2026-10-31/AUDIT_RESULTS.json`](../reports/artifacts/trl-00-tester-reproducibility-2026-10-31/AUDIT_RESULTS.json) | `3fed078280c82933aea3976ed3802a5166af4e79` | `SOURCE_EVIDENCE` |
| [`reports/artifacts/trl-00-tester-reproducibility-2026-10-31/METRICS.csv`](../reports/artifacts/trl-00-tester-reproducibility-2026-10-31/METRICS.csv) | `70a6ee12fb9446444b2d4863547cbbe676173217` | `SOURCE_EVIDENCE` |
| [`reports/artifacts/trl-00-tester-reproducibility-2026-10-31/OFFLINE-RUNBOOK.md`](../reports/artifacts/trl-00-tester-reproducibility-2026-10-31/OFFLINE-RUNBOOK.md) | `48144e870efb0335bef4d2a880cfb3faf7cae39b` | `SOURCE_EVIDENCE` |
| [`reports/artifacts/trl-00-tester-reproducibility-2026-10-31/OPEN_POSITIONS.json`](../reports/artifacts/trl-00-tester-reproducibility-2026-10-31/OPEN_POSITIONS.json) | `0660370e3f1c97772d12354c47b1e7fc65605234` | `SOURCE_EVIDENCE` |
| [`reports/artifacts/trl-00-tester-reproducibility-2026-10-31/REPRODUCTION_DETAIL.json`](../reports/artifacts/trl-00-tester-reproducibility-2026-10-31/REPRODUCTION_DETAIL.json) | `a65b3cfccff44b14407d20f02db7bbd03d81fcd2` | `SOURCE_EVIDENCE` |
| [`reports/artifacts/trl-00-tester-reproducibility-2026-10-31/SOURCE_MANIFEST.json`](../reports/artifacts/trl-00-tester-reproducibility-2026-10-31/SOURCE_MANIFEST.json) | `53629b387c629c57896f868d0cd369368b5ed11d` | `SOURCE_EVIDENCE` |
| [`reports/artifacts/trl-00-tester-reproducibility-2026-10-31/VERIFICATION.json`](../reports/artifacts/trl-00-tester-reproducibility-2026-10-31/VERIFICATION.json) | `3c59233606bbf021503a2a43b2255bafe98e2ed9` | `SOURCE_EVIDENCE` |
| [`reports/PERIODIC_REPORT_TEMPLATE.md`](../reports/PERIODIC_REPORT_TEMPLATE.md) | `ade1915e32d39a7e5b3a8736116dc1bcd7de74d2` | `CURRENT` |
| [`reports/TRL-00-CLOSEOUT-2026-10-31.md`](../reports/TRL-00-CLOSEOUT-2026-10-31.md) | `277f910b1f29d2541ea920d0ca45108f40ad8db8` | `HISTORICAL` |
| [`reports/TRL-00-DATA-COVERAGE-2026-10-31.md`](../reports/TRL-00-DATA-COVERAGE-2026-10-31.md) | `bb549c92aebeee74e1900d8320f17599303775c7` | `HISTORICAL` |
| [`reports/TRL-00-INVENTORY-2026-10-31.md`](../reports/TRL-00-INVENTORY-2026-10-31.md) | `441718d5c37e2174947a5f003fe60654122d36f1` | `HISTORICAL` |
| [`reports/TRL-00-TESTER-MAP-2026-10-31.md`](../reports/TRL-00-TESTER-MAP-2026-10-31.md) | `19a554be9d2d9437ca05ed9f57e082977ec0a10a` | `HISTORICAL` |
| [`reports/TRL-00-TESTER-REPRODUCIBILITY-2026-10-31.md`](../reports/TRL-00-TESTER-REPRODUCIBILITY-2026-10-31.md) | `948b28a4f4799915f8cb8415b9fd9568b053df59` | `HISTORICAL` |
| [`reports/TRL-00-V1-V24-REGISTRY-2026-10-31.md`](../reports/TRL-00-V1-V24-REGISTRY-2026-10-31.md) | `204eaf4762b4abd895a5520d3f018ef16ef8f6cd` | `HISTORICAL` |
| [`reports/TRL-01-START-2026-10-31.md`](../reports/TRL-01-START-2026-10-31.md) | `6b3d37d4feed8b6efc5e2d7886eae3c574492251` | `HISTORICAL` |
| [`reports/TRL-CALENDAR-2027.md`](../reports/TRL-CALENDAR-2027.md) | `fabaf269c48811ebce4ac38b98a0c4ce40546485` | `CURRENT` |
| [`reports/TRL-DEC-2026-HANDOFF.md`](../reports/TRL-DEC-2026-HANDOFF.md) | `e54ac1262d9cbb20363b5f69f51631cf00cda673` | `CURRENT` |
| [`reports/TRL-MERGE-AUDIT-2026-11-20.md`](../reports/TRL-MERGE-AUDIT-2026-11-20.md) | `5875cb95d0303077244f2f0d4e37fe57a6a0a8e4` | `HISTORICAL` |
| [`reports/TRL-NOV-2026-ARTIFACT-MANIFEST.md`](../reports/TRL-NOV-2026-ARTIFACT-MANIFEST.md) | `9c56376e087ce40bfd070fcf8056bd81f3ce44c4` | `SOURCE_EVIDENCE` |
| [`reports/TRL-NOV-2026-FINAL-CLOSEOUT.md`](../reports/TRL-NOV-2026-FINAL-CLOSEOUT.md) | `ec06839fd233f9909eead53e82b9b7d1d7868fb8` | `CURRENT` |
| [`reports/TRL-NOV-2026-KIMI-START-HERE.md`](../reports/TRL-NOV-2026-KIMI-START-HERE.md) | `3c0dd263e21d68cb07bf5a2df2a2a919fa3418b5` | `CURRENT` |
| [`reports/TRL-NOV-PROGRESS-2026-11-12.md`](../reports/TRL-NOV-PROGRESS-2026-11-12.md) | `c4d6678f43b9d6a1eccda7819179e3d95edca15e` | `SUPERSEDED` |
| [`reports/V20_READONLY_SOURCE_REQUIREMENTS.md`](../reports/V20_READONLY_SOURCE_REQUIREMENTS.md) | `2094ac0e860dd9a48c304cd549853125f74d7517` | `CURRENT` |
| [`research/RESEARCH_CARD_TEMPLATE.md`](../research/RESEARCH_CARD_TEMPLATE.md) | `04330f30ce8a0a9670786da6aa9b86d74a387977` | `CURRENT` |
| [`research/sts/EVIDENCE_REGISTER.md`](../research/sts/EVIDENCE_REGISTER.md) | `087566b83f171736e5cf1992d4d6c1db6048b324` | `RESEARCH` |
| [`research/sts/EXPERIMENT_001_INITIAL_CASH_BENCHMARK.md`](../research/sts/EXPERIMENT_001_INITIAL_CASH_BENCHMARK.md) | `f2d77280adb5b7a241c8f7aa5a4b4766fb066b4d` | `RESEARCH` |
| [`research/sts/experiments/R041_FROZEN_PROTOCOL.md`](../research/sts/experiments/R041_FROZEN_PROTOCOL.md) | `3dce397c690cdcb488b7dbc3601ef7ad63dc50db` | `SOURCE_EVIDENCE` |
| [`research/sts/experiments/r042/FROZEN_PROTOCOL.md`](../research/sts/experiments/r042/FROZEN_PROTOCOL.md) | `4bbe4b0e322427edbcc34a19020034e2e7b2a084` | `SOURCE_EVIDENCE` |
| [`research/sts/experiments/r043/audit_r043.py`](../research/sts/experiments/r043/audit_r043.py) | `ee8349126bc594e31f97f9ed73452b3f78bbf676` | `SOURCE_EVIDENCE` |
| [`research/sts/experiments/r043/FROZEN_PROTOCOL.md`](../research/sts/experiments/r043/FROZEN_PROTOCOL.md) | `b4efd8b32ba7cd7fb7cd5853a14ff6858499f787` | `SOURCE_EVIDENCE` |
| [`research/sts/experiments/r043/run_r043.py`](../research/sts/experiments/r043/run_r043.py) | `8e23f1252d3b5f533c9ab451695cd4ba26464316` | `SOURCE_EVIDENCE` |
| [`research/sts/experiments/r045/FROZEN_PROTOCOL.md`](../research/sts/experiments/r045/FROZEN_PROTOCOL.md) | `269d6dd2cab88fa88e9cf06471811cb3d385884b` | `SOURCE_EVIDENCE` |
| [`research/sts/experiments/r045/REPRODUCE_RU.md`](../research/sts/experiments/r045/REPRODUCE_RU.md) | `0c3b88a8b9f398b146e2f5e970a421408ffd4f16` | `SOURCE_EVIDENCE` |
| [`research/sts/experiments/r046/FROZEN_PROTOCOL.md`](../research/sts/experiments/r046/FROZEN_PROTOCOL.md) | `4de980a5ff3fe88f085c03f9970ad2eca23b31c4` | `SOURCE_EVIDENCE` |
| [`research/sts/experiments/r047/audit_r047.py`](../research/sts/experiments/r047/audit_r047.py) | `6c66a6d160f03b98acb8f3f435ed819a9d773804` | `SOURCE_EVIDENCE` |
| [`research/sts/experiments/r047/FROZEN_PROTOCOL.md`](../research/sts/experiments/r047/FROZEN_PROTOCOL.md) | `d9559a301b61d94161be298f76fbfe15e265cc3e` | `SOURCE_EVIDENCE` |
| [`research/sts/experiments/r047/REPRODUCE_RU.md`](../research/sts/experiments/r047/REPRODUCE_RU.md) | `6a80b742b60002a79d43e8790dd0b550c321dd1a` | `SOURCE_EVIDENCE` |
| [`research/sts/experiments/r047/run_r047.py`](../research/sts/experiments/r047/run_r047.py) | `7679c18893b5d390fd81689dde01a409c62d3e73` | `SOURCE_EVIDENCE` |
| [`research/sts/experiments/r048/FROZEN_PROTOCOL.md`](../research/sts/experiments/r048/FROZEN_PROTOCOL.md) | `01e67dc6375df2b2d159fb4f5a0ed592a17daddf` | `SOURCE_EVIDENCE` |
| [`research/sts/experiments/r048/REPRODUCE_RU.md`](../research/sts/experiments/r048/REPRODUCE_RU.md) | `6c9e2ae5e0dc1917f54bbdcd828bc86e263b1fbb` | `SOURCE_EVIDENCE` |
| [`research/sts/experiments/r049/FROZEN_PROTOCOL.md`](../research/sts/experiments/r049/FROZEN_PROTOCOL.md) | `4b7afcfcbfe51bba2c343cef3ec76abee7a23c86` | `SOURCE_EVIDENCE` |
| [`research/sts/experiments/r050/FROZEN_PROTOCOL.md`](../research/sts/experiments/r050/FROZEN_PROTOCOL.md) | `0c44a5a50c394699cc5ed200bd891890050ab420` | `SOURCE_EVIDENCE` |
| [`research/sts/experiments/r052/FROZEN_PROTOCOL.md`](../research/sts/experiments/r052/FROZEN_PROTOCOL.md) | `f9717f309415978dcf94353ca5d22f706577eac4` | `SOURCE_EVIDENCE` |
| [`research/sts/experiments/r053/FROZEN_PROTOCOL.md`](../research/sts/experiments/r053/FROZEN_PROTOCOL.md) | `7582da7d529aa70c8bd7c8625b4076f02cfb3774` | `SOURCE_EVIDENCE` |
| [`research/sts/experiments/r054/PROTOCOL_CORRECTION.md`](../research/sts/experiments/r054/PROTOCOL_CORRECTION.md) | `f248fd5097bcb2c34667dd193df235168420c161` | `SOURCE_EVIDENCE` |
| [`research/sts/experiments/r055/FROZEN_PROTOCOL.md`](../research/sts/experiments/r055/FROZEN_PROTOCOL.md) | `00858f5617108b5339fd541442a65617553d035a` | `SOURCE_EVIDENCE` |
| [`research/sts/experiments/sts_exp_001_replay.py`](../research/sts/experiments/sts_exp_001_replay.py) | `bb26ad13c2eec0292ac358c8ead6195c71001372` | `SOURCE_EVIDENCE` |
| [`research/sts/README.md`](../research/sts/README.md) | `93b709c98b254561df40a6daaa78c2662d5eff41` | `HISTORICAL` |
| [`research/sts/STS_CONCEPT.md`](../research/sts/STS_CONCEPT.md) | `3c28f5c6708b801a1214f97349dfb7497a74b5f8` | `HISTORICAL` |
| [`research/sts/STS_R044_Risk_Parity_2026-11-11.md`](../research/sts/STS_R044_Risk_Parity_2026-11-11.md) | `ba7dda7aefd16bc90f4926c58921c1be9d93578f` | `RESEARCH` |
| [`research/sts/STS_ROADMAP.md`](../research/sts/STS_ROADMAP.md) | `4bdaf7c69ba910405872ac917b046b5a990fb950` | `SUPERSEDED` |
| [`research/sts/STS_TEST_PROTOCOL.md`](../research/sts/STS_TEST_PROTOCOL.md) | `7ca0f9a92869859213a4a02856c977c55da61274` | `RESEARCH` |
| [`research/sts/TRL_R_2026_040_STS_Three_Accounts_Research.md`](../research/sts/TRL_R_2026_040_STS_Three_Accounts_Research.md) | `261503f914aa28a4811e6225b2a2ef82987d5967` | `RESEARCH` |
| [`research/sts/TRL_R_2026_041_STS_OBV_Inside_New_Modules_Research.md`](../research/sts/TRL_R_2026_041_STS_OBV_Inside_New_Modules_Research.md) | `e0bd911fe71291932070bc1bda090d19fbdc2c6a` | `RESEARCH` |
| [`research/sts/TRL_R_2026_042_STS_New_Modules_Research.md`](../research/sts/TRL_R_2026_042_STS_New_Modules_Research.md) | `69d80b82b7780b8a005794b5ee11a7104baf5b7d` | `RESEARCH` |
| [`research/sts/TRL_R_2026_043_STS_MTF_Staircase_Research.md`](../research/sts/TRL_R_2026_043_STS_MTF_Staircase_Research.md) | `502adc7c34f174ce277fac29ff01c759762cdf1c` | `RESEARCH` |
| [`research/sts/TRL_R_2026_045_V20_vs_Shallow_MTM_Research.md`](../research/sts/TRL_R_2026_045_V20_vs_Shallow_MTM_Research.md) | `4527dd6bf88bfdf3c1648439ea27bcb60c5422ae` | `RESEARCH` |
| [`research/sts/TRL_R_2026_046_Inside_and_Missed_Trends_Research.md`](../research/sts/TRL_R_2026_046_Inside_and_Missed_Trends_Research.md) | `9ea2af45be9470071aff8a20041b23b3f5a39192` | `RESEARCH` |
| [`research/sts/TRL_R_2026_047_Missed_Trend_Opportunities.md`](../research/sts/TRL_R_2026_047_Missed_Trend_Opportunities.md) | `42803a6e8925195c2e06cfe84056d041f699db48` | `RESEARCH` |
| [`research/sts/TRL_R_2026_048_Early_Trend_Quality_Research.md`](../research/sts/TRL_R_2026_048_Early_Trend_Quality_Research.md) | `e343788389d2dce4e6a7cf149faed755c2e356c6` | `RESEARCH` |
| [`research/sts/TRL_R_2026_049_Compression_Release_Research.md`](../research/sts/TRL_R_2026_049_Compression_Release_Research.md) | `dc447dda6a1241d47f9e6985a1e6d5add8ab9f5c` | `RESEARCH` |
| [`research/sts/TRL_R_2026_050_Trend_Start_Attempts_Research.md`](../research/sts/TRL_R_2026_050_Trend_Start_Attempts_Research.md) | `bba49d4baa0d4ee3851b43fa2d243097fa6ee938` | `RESEARCH` |
| [`research/sts/TRL_R_2026_051_Monthly_Portfolio_Allocation_GLD.md`](../research/sts/TRL_R_2026_051_Monthly_Portfolio_Allocation_GLD.md) | `fb9b2622b20c83cef2602cc5e559fc5d0d61b20f` | `RESEARCH` |
| [`research/sts/TRL_R_2026_051_V20_Monthly_Allocation_GLD_Research.md`](../research/sts/TRL_R_2026_051_V20_Monthly_Allocation_GLD_Research.md) | `caa7992d245b9f650ad608cdab5e1f718485d2ff` | `RESEARCH` |
| [`research/sts/TRL_R_2026_052_V20_Independence_Limits_Shallow_Variants.md`](../research/sts/TRL_R_2026_052_V20_Independence_Limits_Shallow_Variants.md) | `2e50333663df316ba6b1cb3bf8d1fdafaf6d2af5` | `RESEARCH` |
| [`research/sts/TRL_R_2026_053_Three_Shallow_and_Limits_Research.md`](../research/sts/TRL_R_2026_053_Three_Shallow_and_Limits_Research.md) | `7cb800d6ec78193bf86307cc2890dd27d45c9eef` | `RESEARCH` |
| [`research/sts/TRL_R_2026_054_Shallow_Gated_Risk_Parity_Report.md`](../research/sts/TRL_R_2026_054_Shallow_Gated_Risk_Parity_Report.md) | `85dfe29ad7353aeb4dfdf0ba2d298ebb5e740a53` | `RESEARCH` |
| [`research/sts/TRL_R_2026_055_Physical_Pullbacks_and_Limit_Orders.md`](../research/sts/TRL_R_2026_055_Physical_Pullbacks_and_Limit_Orders.md) | `efe93e731c6678f655a903e6ea337c5776845772` | `RESEARCH` |
| [`STATUS.md`](../STATUS.md) | `4c31d8268f66800aeda123c311af69ce3efcaf8a` | `CURRENT` |
| [`TRL_Roadmap_1_1.md`](../TRL_Roadmap_1_1.md) | `406e492117ecf10fff540cfa8ea3b123a6711710` | `CURRENT` |

## Известные коллизии и сохранение истории

- `evolution/TRL-R089-HOLD5-WITHOUT-EXT2-DIGEST-20261118.md` — сводка, а `...ORIGINAL...` — более подробный первичный документ: это **не удаляемые дубликаты**; для доказательства использовать оригинал.
- `evolution/TRL-R098-CONDITIONAL-ALLOCATION-20261119.md` — **SUPERSEDED как рекомендация**, но не как таблица ранее полученных результатов; решение владельца находится в ноябрьском Closeout.
- `reports/TRL-NOV-PROGRESS-2026-11-12.md` и `evolution/2026-11-15-r070-final-v20-assembly-and-live-handoff.md` — исторические interim рекомендации; не переписывать задним числом.
- `research/sts/` — архив отдельной исследовательской программы; frozen-протоколы и отрицательные результаты сохранять. Наличие Python не гарантирует наличие внешних R038/R039/OHLCV.
- `reports/artifacts/trl-00-...` — доказательная история тестера TRL-00, не полная текущая база R060–R098.
- `TRL_Roadmap_1_1.md` — актуальный график; Roadmap 1.0 в Project является исторической исходной редакцией.
- Старые Git SHA в датированных документах — pin на их дату, не текущий HEAD.
