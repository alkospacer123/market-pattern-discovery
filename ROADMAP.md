# Trading Systems — Roadmap (фактический R7 closeout, 22.11.2026)

**OPERATING CHECKPOINT 23.11.2026:** После финальных документационных Merge #592–#595 source MAIN проверен: `1413273a1a312802a0ced7a06a4eb73f050d2ec3` до принятия последующих PR. Оператор подтвердил локальную исходную копию на `C:\KimiSandbox\market-pattern-discovery` (тот же HEAD, required files PASS, clean PASS); это не допуск исполнения на Intel. Правила работы и критерии покупки месячного Pro в [Windows gate](recovery/kimi/WINDOWS_WORKSPACE_AND_ACCESS.md). После каждого Merge повторно проверять новый MAIN.


**Обязательный порядок:** (I) безопасно упорядоченный GitHub → (II) полная адаптация Kimi Chat **и отдельно** Kimi Code → (III) независимый backup и доказанный cold restore. **MAIN ≠ INSTALLED ≠ LIVE ≠ RESEARCH ≠ ARCHIVE**.

## I. Упорядоченный GitHub — завершён в проверенном объёме

- [x] [#583](https://github.com/alkospacer123/market-pattern-discovery/pull/583): массовое выведение 11 594 исторических A/B/C и BBW файлов из рабочего `main` с сохранением Git history.
- [x] [#585](https://github.com/alkospacer123/market-pattern-discovery/pull/585) → [#586](https://github.com/alkospacer123/market-pattern-discovery/pull/586): канонические README/AGENTS/паспорта, реальная очистка старого самостоятельного root (233 удаления), five active/dependency trees untouched и два защищённых архивных Git ref. Старый архивный тест **45 PASS / 1 known FAIL**, исторический дефект не скрыт.
- [x] [#587](https://github.com/alkospacer123/market-pattern-discovery/pull/587) MERGED: карта актуальных источников/Kimi R1.2 и классификация H1/M15. Commit `8a1c6618f8d3c9f33de9de6cb3f6efae13fe29f0`.
- [x] [#588](https://github.com/alkospacer123/market-pattern-discovery/pull/588) MERGED: source-preserving offline Git scanner/checkpoint; 10/10 synthetic PASS. Commit `bb8c46c1db89ca2b5311f22c755bb4e51ce8f7d6`. **Это не финальный Recovery и не проверка текущего LIVE.**
- [x] Draft [#580](https://github.com/alkospacer123/market-pattern-discovery/pull/580) и [#581](https://github.com/alkospacer123/market-pattern-discovery/pull/581) закрыты без Merge после переноса уникальных материалов; исходные ветки/PR/SHA сохранены.
- [x] **Контроль `audit_only/stop_tick_grid_20261012`**: [#590](https://github.com/alkospacer123/market-pattern-discovery/pull/590) попытался безопасно вывести 16 исторических файлов, но новый CI доказал прямые H1 research dependencies; **FAIL → CLOSED WITHOUT MERGE**. Файлы оставлены, protected H1/V20/CC/TRL/M15 не изменены. [Финальный акт](recovery/R7_STAGE_I_FINAL_ACCEPTANCE_20261122.md).
- [x] Финальная классификация: V20 и CC — ACTIVE, TRL — RESEARCH; H1/M15 — SHARED DEPENDENCY + historical research; `audit_only` — H1 offline research dependency, не LIVE. [Реестр](recovery/RETAINED_RESEARCH_CLASSIFICATION_2026-11-22.md).

**Граница приёмки I:** исходные ZIP/XLSX/другие внешние потребители, три больших ранее пропущенных metadata, все динамические imports и автономное восстановление не проверены полностью. Без последующего разрешения не удалять H1/M15/audit исходники. Такое сохранение **не мешает** начать Kimi и не подменяет этап III.

[Матрица действующих, датированных и архивных инструкций](recovery/DOCUMENTATION_AUTHORITY_2026-11-22.md) определяет приоритет документов, чтобы старый README/PR не переопределял R088, CC-08 или TRL closeout.

## II. Полная адаптация Kimi — переход к выполнению

- [x] [#589](https://github.com/alkospacer123/market-pattern-discovery/pull/589) **MERGED** обычным merge commit `41d0b48c1d33db29bc1b19497d558748b3db8fb4`: три отдельные логические базы знаний V20/CC/TRL, правила Kimi Chat и **отдельного** Kimi Code, экзамен и GPT↔Kimi handoff. Принятие GitHub-документов ≠ реальные проекты Kimi, экзамен или доступ.
- [ ] **Kimi Chat**: создать три отдельных проекта на стороне Kimi из одного GitHub, проверить доступ к исходникам, SHA, версии, грамотность и изоляцию знаний; исключить FINAM/DPAPI/приватные сведения.
- [ ] **Kimi Code**: отдельное подключение к GitHub с минимальными правами, независимая сверка commit/blob SHA, sandbox, реальные безопасные offline tests с stdout/exit; никакого реального брокера, LIVE-кнопок или автоматического Merge.
- [ ] Экзамены V20 R088 base+9 patches, CC-08 командный fail-closed, TRL R089/R097/R098 и отсутствующие оригиналы; затем совместная ограниченная задача GPT↔Kimi, Draft PR, независимый review/rework/handoff и решение оператора.

## III. Независимый Recovery — последним, после II

- [ ] Полный автономный актуальный комплект V20, CC, TRL, H1/M15-зависимостей, рыночных данных, оригинальных ZIP/XLSX/OHLCV, Git history/refs/PR/Issues/CI, проектных знаний и безопасно отделённой приватной конфигурации. Хранить вне Intel, основного SSD, GitHub и обоих ИИ, горизонт 10–30 лет.
- [ ] Настоящий offline cold restore всех трёх систем на изолированном оборудовании: SHA, БД, исходники/зависимости, unit/regression, доступность знаний и операторский акт. До отдельного LIVE-разрешения никаких реальных заявок.

**Не доказывается самим GitHub:** сегодняшние FINAM positions/orders/SLTP, ARMED или установленная на Intel версия, Kimi Chat/Code access, автономный backup/cold restore.

## Phase-II Windows preparation addendum — 23.11.2026

- [x] Kimi account authenticated for Chat/Work/Code according to operator; Kimi Code `Always Ask` confirmed. Kimi GitHub OAuth authorized; **actual Kimi data access untested**.
- [x] Two Kimi Chat knowledge projects available before subscription; Control Center third project awaits paid limit.
- [x] Temporary Git clone on external Expansion D: was created/read-verified and then removed by operator; **D: is not the permanent workspace**.
- [x] **Operator-verified 23.11:** one NTFS source checkout on Intel at `C:\KimiSandbox\market-pattern-discovery`, `HEAD=1413273a1a312802a0ced7a06a4eb73f050d2ec3`, required files PASS, clean worktree PASS. **Not execution isolation.**
- [ ] Verify a working Kimi Work per-action approval path (if supported), or keep PC/browser automation ungranted for LIVE; design an independent no-secret execution environment before agent-run offline tests.
- [ ] Purchase **one-month Kimi Pro** after preparatory acceptance; measure quality, monthly and five-hour Code limits, then decide annual Pro or Max. No annual contract before pilot results.
- [ ] Complete three Chat projects, real GitHub reads, separate Kimi Code source/tests, V20/CC/TRL exams, GPT↔Kimi Draft PR/handoff, operator acceptance. Then and only then begin Stage III Recovery.

Execution, on-host privilege and post-exam expansion rules: [Kimi Windows workspace/access policy](recovery/kimi/WINDOWS_WORKSPACE_AND_ACCESS.md). Original dated Roadmap and decisions above are not replaced.

## Детализация этапа II — квалификация Kimi, 23.11.2026

После безопасной подготовки GitHub и Kimi source-копии владелец выбрал **полную последовательную** квалификацию, без ускоренного запуска LIVE и без привязки ARMED к оплате Pro. [Программа квалификации, оценки качества, измерения Pro и go/no-go](recovery/kimi/PHASE_II_QUALIFICATION_AND_PRO_LIMITS_20261123.md) — надстройка над профильными экзаменами. Gate G0–G9 охватывают Chat/Work/Code, SHA и доказательные источники, реальный GitHub, изолированную практику, проверку safety/контекста, handoff GPT↔Kimi, последующее контролируемое read-only LIVE-наблюдение и только отдельное операторское решение о ARMED. **Покупка Pro не означает сдачи экзамена, автономных прав на Intel или запуска роботов.** Тариф на год — Pro/Max/MORE_PILOT/NO_GO по фактическим измерениям месячного пилота.

**Уточнение ролей Kimi Chat/Work/Code (23.11):** Chat в браузере и мобильном приложении — тоже потенциально полноценный агент с GitHub MCP, а не только теория. Для каждого режима обязательны отдельные реальные тесты GitHub, permissions, качества и стоимости; Work не является необходимым посредником для каждой GitHub-задачи. Сравнительный сценарий и проверка mobile/web parity включены в [G1/G2 qualification](recovery/kimi/PHASE_II_QUALIFICATION_AND_PRO_LIMITS_20261123.md). До проверки инструментов нельзя обещать одинаковые возможности на всех устройствах.

## Усиление этапа II — дефекты, независимый ретест и Kimi GPT-OUTAGE (решение 23.11.2026)

**Это актуальный addendum к датированным статусам выше, не ретроактивная правка исторических чекбоксов.** Оператор утвердил усиление без ускорения G0–G9, без снижения профильных экзаменационных порогов и без переноса финального Recovery раньше этапа III.

- **Реально подтверждено в Chat/Work:** три Kimi Chat проекта с инструкциями и двумя прикреплёнными документами каждый; три sandbox Work-проекта и их видимость в Remote Control; Kimi Pro месяц; GitHub source audits; V20 fresh-chat theory **59/60** и CC fresh-chat theory **58/60**; TRL G2.3A training **97/100**, G2.3B выполняется, независимый TRL экзамен впереди. Chat/Work доказали чтение GitHub, **Code practical / installed LIVE / independent GPT-OUTAGE пока NOT TESTED**. Точные свидетельства — [индекс этапа II](recovery/kimi/README.md).
- [x] Открыт [журнал недостатков Kimi](recovery/kimi/KIMI_DEFECTS_AND_REMEDIATION_REGISTER.md) в Draft PR #597: различать KIMI_ERROR, EVIDENCE_GAP, SOURCE_DOC_DRIFT, исследовательскую гипотезу и непроверенный safety gate. Повторное упущение Protect3 при HALTED — отдельный HIGH пункт и обязательный отрицательный тест после организации реальной изоляции.
- [ ] **После независимого TRL экзамена** прямо обсудить с Kimi все подтверждённые ошибки: его независимая оценка причин, возражения на основе исходников, предложения улучшений, план new blind retests; не закрывать проблему на основании обещания или новой инструкции.
- [ ] Утвердить отдельный no-secret, broker-egress-denied executor; провести Kimi Code инженерные практики V20/CC/TRL, неожиданные сбои, negative tests, branch/Draft PR, двусторонний review GPT↔Kimi, проверку remote/mobile approvals и контекстной устойчивости.
- [ ] После практики — строгий **свежий GPT-OUTAGE** без ответов GPT, с независимым ревью или корректным STOP при невозможности review; затем отдельная READONLY эксплуатационная квалификация только по разрешению оператора.
- [ ] **Лишь после всех этих испытаний** финально обновить все Kimi Chat/Work/Code AGENTS/README/паспорта/runbook, снять противоречия и устаревшие SHA, проверить fresh-context bootstrap по новой документации и принять операторами. Этап III — автономный backup и cold restore — строго последним.

Детальные условия и рубрики: [Phase II qualification §9](recovery/kimi/PHASE_II_QUALIFICATION_AND_PRO_LIMITS_20261123.md). **Draft #597 ≠ main; LIVE и решение об ARMED остаются отдельной полномочностью владельца.**

## Приоритетная усиленная приёмка V20 и TRL — решение 23.11.2026 (после G2.3B)

**Уточнение владельца:** при неизменном порядке G0–G9, без ускорения или ослабления LIVE, **первый приоритет практической сложности — V20 Trading System и Trading Research Lab**. Control Center остаётся под полным исходным экзаменом и общесистемными safety gates. Подробный [сводный контроль V20/TRL](recovery/kimi/V20_TRL_ENHANCED_PRACTICAL_ACCEPTANCE_20261123.md) — обязательный addendum; скрытые задачи и expected outputs до экзамена не публиковать в доступном Kimi GitHub.

- [x] **TRL G2.3B обучение:** 12 исследовательских сценариев приняты как учебный source-audit, **98/100** формирующая оценка; 25/25 discovery blob SHA, 4/4 data CSV blob SHA, исторические численные выводы сверены выборочно с первоисточниками. Не означает TRL G2.3C, Code или самостоятельный replay. [Протокол](recovery/kimi/G2_TRL_TRAINING_REVIEW_20261123.md).
- [ ] **V20 HIGH-safety практический gate:** R088 BASE+9 patches, SHA/derived, frozen signals/NEXT_OPEN, risk/GO, partial fill/SLTP, защита при HALTED, Protect3, PREPOST/UNKNOWN, HOLD5 по наблюдаемым сессиям, минимум два новых слепых сценария, full negative+regression test log. Отдельно закрыть повторно проявившийся KDR-001 на синтетическом исполняемом тесте и при смене контекста.
- [ ] **TRL HIGH-science практический gate:** source intake оригинальных R060/R087/R097 ZIP/XLSX/OHLCV с SHA256/manifest, независимый ограниченный replay, aggregate+ledger+signal+GO parity, R051/R086/R090 исторические несоответствия, no lookahead/TRUE OOS, costs/liquidity, отрицательные исследования, новый неизвестный исследовательский дефект и независимый reviewer. Если исходников нет — честный BLOCKED_EXTERNAL, не REPLAY_PASS.
- [ ] **Не изменять критерии профильных экзаменов:** V20 >=90/100 (теория 60, практика 40), TRL Chat >=36/40 и Code >=54/60, 0 critical. По TRL G2.3C использовать **каноническую 40-балльную Chat-рубрику**, не подменять её 12 вопросами текущего обучения.
- [ ] После TRL G2.3C открыть Kimi [журнал недостатков](recovery/kimi/KIMI_DEFECTS_AND_REMEDIATION_REGISTER.md) и провести двустороннюю техническую самокритику. Исправления в инструкциях проверять новыми слепыми кейсами, не считать самоотчёт закрытием. По KDR-003 уточнить timezone: 24.11 у Kimi может быть правильным UTC+08 при 23.11 22:03 UTC+03 у оператора — **замечание GPT реклассифицировано как EVIDENCE_GAP**, не доказанная ошибка Kimi.
- [ ] G4–G9: сначала реальная OS/runner isolation и deny-tests, затем полноценная практика Code, двусторонний review GPT↔Kimi, GPT-OUTAGE, отдельный READONLY installed/broker acceptance и финальная ревизия документации. Любое ARM/HALT/LIVE — только отдельное разрешение владельца; Recovery — последним этапом III.

## G2.3C TRL — независимый экзамен пройден 23.11.2026

- [x] **TRL Kimi Chat**: независимый новый чат, канонические 5 задач по 8 баллов, **39/40 PASS** при пороге >=36/40 и 0 критических нарушений; **26/26 Git blob SHA discovery и 4/4 Git blob SHA data проверены независимо**. Источник: [TRL G2.3C exam review](recovery/kimi/G2_TRL_INDEPENDENT_EXAM_REVIEW_20261123.md). Исходный 627-строчный Kimi-ответ приложен к разговору, не объявлять его сохранённым в репозитории.
- [x] **Теоретическая квалификация всех трёх Kimi Chat-проектов:** V20 59/60, Control Center 58/60, TRL 39/40. Это допуск к дальнейшей проверяемой инженерной подготовке, **не** квалификация Code, не автономный GPT-OUTAGE, не изменение INSTALLED и не LIVE.
- [ ] **KDR-001 остаётся OPEN:** при ответе TRL на Protect3 не выделен \`Switch=ARMED\` gate исходной функции cancel-first; HALTED-сценарий отдельно не задавался, поэтому только минус 1 балл, не critical. Доказать знание в свежих V20/CC-контекстах и синтетическим Code negative test; запрещено «закрыть» по высокой суммарной оценке.
- [ ] **Следующий подпункт этапа II:** прямой postmortem Kimi с [журналом недостатков](recovery/kimi/KIMI_DEFECTS_AND_REMEDIATION_REGISTER.md), признанием/оспариванием фактов, планом измеримого исправления и отдельными скрытыми ретестами. Затем — OS-isolated Kimi Code onboarding, V20+TRL elevated practical exams, совместный GPT↔Kimi, GPT-OUTAGE, финальная документация, и **только потом** этап III Recovery.
- [x] Pro usage screenshot 23.11 22:45 UTC+03: **21.52%** месячной квоты (осталось 78.48%), Code 5h 0%; это не прогноз достаточности тарифа при реальном Code.

## Усиление G4–G9 по итогам прямого postmortem Kimi (23.11.2026)

- [x] Прямой Kimi Chat G2.POSTMORTEM завершён: Kimi принял неполноту Protect3 (KDR-001), не пытался удалить ARMED gate, привёл план реальных negative tests и аргументированно оспорил неверное обвинение о дате (KDR-003, часовой пояс не установлен). **Postmortem — не Code-практика и не PASS исправления.**
- [x] Независимая проверка GPT и [10 дополнительных механизмов надёжности](recovery/kimi/KIMI_RELIABILITY_IMPROVEMENTS_20261123.md): hazard-first side-effect trace, branch-reachability-positive/negative/mutation proof, source/derived/installed witness, hidden independent test oracle, TRL ledger + metamorphic causal checks, preregistration null/research attempts, реальная OS isolation/deny, delayed cross-mode retention, non-GPT reviewer.
- [ ] **До Kimi Code исполнения** отдельно утвердить runner без FINAM, токенов, DPAPI, production mounts и broker egress; проверить отказ доступа и независимый holdout. \`C:\KimiSandbox\` — учебная копия, не гипервизор. Нельзя ради настройки перезагружать работающий Intel без согласования владельца.
- [ ] **V20 приоритет:** принудительно доказать reachability проверки ARMED в live-shaped HALTED negative test, пара ARMED positive с идентичным fixture, mutation красный, отсутствие cancel/post, отдельные unknown cancel/post, восстановление BASE+9 DERIVED SHA и reviewer. \`KDR-001=REMEDIATION_PROPOSED, OPEN\`.
- [ ] **TRL приоритет:** оригинальные SHA256 ZIP/XLSX/OHLCV прежде чем replay, полный chronological rejected-signals/GO/lot/cash ledger, first divergence, метаморфические no-lookahead controls, верифицируемая negative hypothesis/preregistered sampling без повторного подбора по 2025; правильный \`BLOCKED_EXTERNAL\` при отсутствии оригиналов.
- [ ] Ревьюер вне авторства Kimi выполняет непубликуемые заранее blind fixtures на втором чистом runner; фиксируются first attempt, after-feedback, delayed blind retest, score, critical count, Git SHA и operator decision. Не засчитывать объяснение или прохождение теста с неверной авторизацией как gate coverage.
- [ ] После контролируемых G4–G8 — GPT-OUTAGE и финальные instructions/README/passports/runbook с новым bootstrap-test; только затем отдельный Stage III Recovery. Никаких автоматических ARM/Merge/FINAM изменений.

## G4.0 — согласованный входной этап Kimi Code 24.11.2026

- [x] Kimi G2.RELIABILITY_PLAN_REVIEW: **RLI 7 ACCEPT / 3 MODIFY / 0 REJECT**, приняты технические уточнения RLI-03 (hazard-directed conformance matrix вместо параллельной state-machine), RLI-06 (причинные метаморфические изменения только после frozen cutoff без разрушения календаря), RLI-08 (безопасные canary/config deny-tests **без** реальных FINAM/DPAPI/секретов).
- [x] [G4 engineering consensus + безопасный вход](recovery/kimi/G4_RELIABILITY_CONSENSUS_AND_CODE_ENTRY_GATE_20261124.md): provenance → reachability → reason/side-effect witness → positive/negative pair → mutation sensitivity → independent oracle → reality boundary. Нет одиночного self-authored test PASS.
- [ ] **G4.0 Kimi Code source-only:** разрешить только чтение из \`C:\KimiSandbox\market-pattern-discovery\` / GitHub с manual approvals; не давать script/shell/PowerShell/Python, git checkout/fetch/commit, installers, tests, writes, production roots, FINAM/DPAPI. \`Always Ask\` — операторский контроль, **не OS sandbox**. Кандидат должен представить SHA/current sources, call paths и нужные тестовые точки, а не менять код.
- [ ] **G4.1 isolation before execution:** выбрать независимый disposable runner, доказать отсутствие secrets, broker egress, production mounts с контролируемыми canaries и пассивной проверкой policy. Никаких реальных попыток к FINAM/DPAPI для демонстрации блокировки. Установка Windows Sandbox/Hyper-V/WSL на Intel, если требует restart/admin, — только отдельное разрешение; пользователю не нужно торопиться.
- [ ] После изоляции выполнить enhanced V20 P0 tests (KDR-001 OPEN), TRL original-data/replay or BLOCKED_EXTERNAL, CC standard tests, hidden independent tests, двусторонний handoff и GPT-OUTAGE. Полная финальная документация Kimi, затем Stage III Recovery.
- [x] Kimi Pro screenshot 24.11 06:15: месячная квота 23.72%, 5h Code 0%, extra OFF; это не доказательство экономической достаточности при будущих практических задачах.

## M&S — Kimi Memory & Skills Qualification (решение владельца 24.11.2026)

**Дополнительный сквозной Gate этапа II, параллельно G4.0.** [Актуальная политика минимальной долговременной памяти (M01–M10 отменены), пять проектных Skills и критерии приёмки](recovery/kimi/MEMORY_AND_SKILLS_QUALIFICATION_20261124.md).

- [x] Утверждён **план включения** Memory Space + MyKimi Self-growth + Kimi Skills; это **не свидетельство фактической записи памяти** или применения Skills в аккаунте.
- [ ] **MS-01 Inventory:** в Kimi Settings → Personalization → Chat memory проверить доступную версию, включённое состояние, имеющиеся entries и дубли. Новый Memory Space с октября 2026 поэтапный; 50 элементов × 500 символов — исторический формат, а не гарантированный предел нового опыта.
- [ ] **MS-02 Minimal Memory:** прежний набор M01–M10 и технические записи о R088/Protect3/TRL результатах **отменены**. Ничего пока не импортировать. Допустить только 0–3 коротких записи о долговременных ролях V20, CC, TRL после одобрения владельца; текущие настройки, ошибки, релизы, статусы, даты и исходники хранить только в актуализируемых проектных документах/KDR/Skills.
- [ ] **MS-03 Memory transfer:** fresh Chat, 3 профильных Chat-проекта, Work, Code и мобильное приложение; проверка реального использования, исправления, устаревшего значения против нового GitHub ref и экспорта. Нельзя предполагать, что память автоматически работает в Code.
- [ ] **MS-04 Self-growth:** проверить MyKimi Саморазвитие; разрешать анализ рабочих привычек и **предложения** навыков, но любой автоматически созданный Skill проходит ручную проверку, версионирование и fail-closed gate. Нет автоматических LIVE полномочий.
- [ ] **MS-05 Skills:** создать первый \`github-source-audit\` в формате \`SKILL.md\` как READONLY; прогнать два безопасных кейса и конфликтный negative case, сохранить source/author/version, проверить \`/\` invocation в Chat/Work, отдельно Code import/transfer. Затем \`v20-safety-analysis\`, \`trl-reproducibility-review\`, \`control-center-incident-audit\`, \`gpt-kimi-handoff\`.
- [ ] **MS-06 Final:** после G4–G9 и GPT-OUTAGE включить только испытанные навыки в обновлённые AGENTS/паспорта/инструкции и провести fresh-context bootstrap. Экспорт Memory/Skills для документального handoff не является преждевременным Stage III Recovery; независимый cold restore — в самом конце.

**Главный принцип:** Memory помогает вспомнить контекст; Skill задаёт процесс; текущая правда подтверждается Git SHA, source, независимыми тестами/брокером; права на исполнение определяются operator approval и технической изоляцией. \`C:\KimiSandbox\` — не OS sandbox, G4.0 остаётся source-only.

## Memory & Skills — состояние UI на 24.11.2026

- [x] **MyKimi Self-growth UI enabled:** пользователь включил «Саморазвитие», скриншот MyKimi показывает «Самообучение включено». Это включает механизм обучения предпочтениям/рабочим привычкам, но **не доказывает создания или проверки Skills**.
- [x] **Memory settings UI available:** пользователь открыл \`Settings → Personalization → Memory\`; screenshot показывает синее включённое переключение и диалог «Импорт из другого ИИ в пространство для запомненного». Это подтверждает доступность нового **Memory Space import** UI, но ещё **не** импорт и не результат записи.
- [x] **Memory import, user-reported 24.11:** владелец сообщил об успешном сохранении собственной сокращённой редакции: общий safety/source contract, роли V20/CC/TRL (Research/Evolution/Journal) и две предпочтительные инженерные установки; **без релизов, SHA, банковских/FINAM данных**. Точный состав — предоставленный пользователем экспорт, без публикации личных сведений. Не приравнивать ответ Kimi к независимому подтверждению UI структуры памяти.
- [ ] **Verify actual stored entries:** выполнить Import, затем пересмотреть сохранённые Memory Space items, проверить даты/версии, исключить дубли и устаревший SHA; выполнить fresh Chat/Work/Code memory visibility checks по [контракту](recovery/kimi/MEMORY_AND_SKILLS_QUALIFICATION_20261124.md).
- [ ] **Skills:** отдельно проверить библиотеку Skills / автоматически предложенные MyKimi навыки; ни один Skill не получает доверия или права исполнения без проверки \`SKILL.md\`/действительных инструментов и независимого ретеста.

## Долговечность Memory — коррекция владельца 24.11.2026

- [x] Исправлена архитектурная ошибка первоначального плана: Memory не должна стать долгоживущей копией меняющихся технических паспортов. Примеры R088, +9 patches, текущий ARMED/HALTED, FINAM, локальные пути, параметры, номер KDR-001 и исторические результаты **запрещены для персональной памяти**, поскольку могут устареть через месяцы.
- [x] M01–M10 отменены как рекомендуемый импорт. Memory — **опциональный минимальный указатель**, не технический контракт. Источник актуальности — GitHub/оригиналы/installed/broker evidence; исправления ошибок — KDR + ревизуемый Skill + retest.
- [x] Владелец самостоятельно выбрал и импортировал **6 долговечных записей** (общая инструкция, V20, CC, TRL, две preferences), расширив предварительный ориентир «0–3». Предыдущие M01–M10 и техпаспортные импорты не используются. При смене роли/архитектуры потребуется ревизия памяти; Stage III cold restore остаётся последним.

## Memory Qualification — TRL fresh-chat source audit, 24.11.2026

- [x] Kimi presented `MEMORY_TRL_RECALL_AND_SOURCE_CHECK`: correctly described Research / Evolution / Journal, auxiliary Reports, append-only as policy, staged decisions and the no-LIVE boundary.
- [x] GPT independently read GitHub ref and 3/3 quoted Git blob SHA — **MATCH**; checked additional research/evolution/AGENTS docs. Scope = factual source-consistency review, not audited Kimi connector logs or research replay.
- [ ] **Memory Space retrieval still UNPROVEN:** Kimi explicitly said its pre-GitHub recap came from text supplied at the beginning of that dialog, not from independently inspected memory store. Need separate unseeded fresh-Chat test; then Work, Code, three projects, mobile checks. Do not ask Kimi to claim hidden retrieval without evidence.
- [ ] Skill creation/review unchanged; no LIVE authorization, no GitHub Merge, no Code execution on Intel.

## TRL Research — явная таксономия стратегий (24.11.2026)

- [x] В ответе Kimi `MEMORY_TRL_RECALL_AND_SOURCE_CHECK` корректно выявлен пробел: в канонических Research документах не были **явно** перечислены три типа — трендовые, импульсные, волатильные стратегии. Это **документационное уточнение по запросу владельца**, не ошибка Kimi и не доказанный новый торговый edge.
- [x] В Draft PR #597 обновлены `TradingResearchLab/README.md`, `research/RESEARCH_METHODOLOGY.md`, `OPERATING_CYCLE.md` и `research/RESEARCH_CARD_TEMPLATE.md`: перечисление направлений, определение исследовательского scope, необязательная классификация гипотез, отсутствие квот, допуск других подходов, no-LIVE.
- [ ] Независимое docs-only review перед любым Merge; не объявлять новые исследования/тесты выполненными. Не менять frozen V20, FINAM или running Intel.

## Memory Qualification — независимый пустой Chat, фактический FAIL (24.11.2026)

- [x] Владелец выполнил следующий **unseeded fresh non-project Kimi Chat** тест без вставленного списка V20/CC/TRL и без GitHub/файлов. Kimi ответил, что в доступном контексте **нет никаких сведений** о долгосрочных технических проектах; отказался угадывать, не обращался к инструментам и не заявлял о доступе к Memory Space.
- [x] **Memory recall gate FAIL (observed), honesty/uncertainty PASS**: 0/3 названий проектов и 0/3 внутренних блоков TRL восстановлены. Ответ в другом чате с успешным TRL GitHub аудитом **не был независимым Memory PASS** — Kimi прямо указал, что получил начальное описание из текста того диалога.
- [ ] **Диагностический gate:** открыть Settings → Personalization → Chat memory → Memory Space (тот же аккаунт), проверить enabled, фактические сохранённые записи и время последнего обновления; записать факт импорта против наличия записей. Новое Memory Space может обновляться с задержкой и выбирать релевантную информацию не для каждого ответа (официальный FAQ). Не объявлять память сломанной технически до UI проверки.
- [ ] При наличии записей провести один новый контекстный memory recall тест *после обновления* с нормальным вопросом о направлениях работы, проверить citation indicator, если он доступен. Не заставлять Kimi притворяться, что видит внутреннее хранилище. При отсутствии записей — выяснить результат Import UI и возможное pending/error; не создавать дубли массово.
- [ ] Work / Code / профильные Chat и мобильный перенос контекста — независимо и после диагностического gate; не связывать этот FAIL с технической квалификацией Code G4.0 и LIVE.

## Memory UI screenshot — empty visible Memory Space (24.11.2026)

- [x] Пользователь предоставил два скриншота Kimi Settings → Personalization → Memory (24.11, 10:21). **Создавать записи из чатов = ON**. Карточка «Пространство для запомненного» показывает пустой стартовый текст «Продолжайте общаться — Kimi знакомится с вашим миром», **ни одной записи в предоставленном UI не видно**. Диалог «Импорт из другого ИИ» открыт повторно, поле ввода пустое — само по себе **не** свидетельство об отсутствии прежнего отправленного импорта.
- [ ] Установить фактический persisted state: подтверждение импорта/UI saved entries/async processing или ошибка, затем fresh Chat retest. Не делать массовый повторный импорт до диагностики.
- [x] Проверена официальная документация Kimi: `https://www.kimi.ai/help/features/memory-space` и `https://www.kimi.ai/ru/help/features/memory-tips`: новую информацию систематизируют в Memory Space после начала нового чата, обновление может занять время; сохранённые записи и время обновления должны отображаться в Memory Space после обработки. Memory Space vs past chats — разные источники. Project memory parity не обещана. **Не утверждать, что записи утрачены, без проверки.**

## Контрольная сверка Roadmap — 24.11.2026 (current checkpoint, Draft PR #597)

Этот раздел — актуальный сводный указатель статусов на дату сверки, а не замена исторических чекбоксов или критериев приёмки выше. Источники: [полная программа G0–G9, включая обязательные mobile routes](recovery/kimi/PHASE_II_QUALIFICATION_AND_PRO_LIMITS_20261123.md), [G1 Chat/Work](recovery/kimi/G1_CHAT_WORK_READONLY_SCORECARD_20261123.md), [G4.0 final closeout/I0–I4](recovery/kimi/G4_RELIABILITY_CONSENSUS_AND_CODE_ENTRY_GATE_20261124.md), [Memory & Skills](recovery/kimi/MEMORY_AND_SKILLS_QUALIFICATION_20261124.md), [KDR](recovery/kimi/KIMI_DEFECTS_AND_REMEDIATION_REGISTER.md). MAIN verified at `e05bbd24db88f127a52f0ff1b7282d7c6919cd81`. Stage I accepted in approved scope; Stage II active; Stage III final autonomous backup/cold restore not started. Historic captures are not recovery acceptance.

| Gate | Current evidence/status | Remaining |
|---|---|---|
| G0 account/setup | Pro monthly, three Chat projects with instructions/attachments, three Work training projects visible remotely, Code authenticated, designated Intel source checkout; operator evidence | Verify each surface's actual approval/deny and access boundaries; fresh local HEAD/clean status only via authorized means; no production access |
| G1 source | PASS scoped: Work G1.1 5/5 blobs, G1.2 9/9 / 96/100, Chat G1.3 98/100 reported/reviewed | Mobile Chat GitHub parity and independent action evidence |
| G2 knowledge/theory | PASS: V20 59/60, CC 58/60, TRL 39/40; postmortem complete, RLI 7 ACCEPT / 3 MODIFY | Delayed blind retention and targeted KDR retests; practical grades separate |
| G3 Work | PARTIAL: GitHub-only audits and folder/project visibility PASS | Fresh phone-initiated local source task, approvals, stop/reconnect/revoke, comparative Work value |
| G4.0 Code Desktop | SOURCE_ONLY_ACCEPTED: 18/18 independent blob match, review 96/100, full supplement accepted | No repeat; no executable test or technical isolation inferred |
| G4.0-RC | NEXT / NOT_TESTED | Actual new Code task from phone in designated source checkout, tool evidence, scope, quota |
| G4.0-W | NEXT / NOT_TESTED | Actual new Work task from mobile, compare with Code/Chat; no shell/writes |
| G4.1 | PLANNING ONLY / BLOCKED EXECUTION | Approved isolated executor I0–I4; verify mounts/secrets/egress/least privilege, harmless canaries and approval/deny, no disruption to Intel |
| G5 | NOT_TESTED | V20 BASE+9 build, synthetic positives/negatives and blind fixes; TRL original bytes/ledger replay or BLOCKED_EXTERNAL; CC command and telemetry synthetic cases |
| G6 | PARTIAL preparation (M5 simulated stale-source test PASS, RLI agreed) | New blind retention, injection, conflicting evidence, unknown result, safety/remote failure tests; independent KDR closeouts |
| G7 | NOT_TESTED as formal gate | Both author/reviewer directions, approved isolated test/docs branch, Draft PR, review/rework/test evidence |
| GPT-OUTAGE | NOT_TESTED, mandatory | New operator-assigned work covering three projects without GPT prompts/review/runtime dependency; mobile route; independent non-GPT evidence and owner decision, STOP/DEFER if risky gate missing |
| G8 | NOT_TESTED | After required exams and separate approval: sanitized dated read-only operational observations, not ARM/broker commands |
| G9 | NOT_TESTED | Full cross-surface acceptance, final docs/knowledge/runbook, open issues, scope of approved capabilities, monthly Pro decision, owner signoff; no auto-Merge or LIVE authorization |

### Parallel tracks

- Memory: M0/M1 basic config/storage and reported fresh-chat canary recall; M2 project map recall PASS after earlier failure; M5 simulated conflict PASS. Original import provenance and UI source attribution not fully verified. M3 project-context/attachment checks, M4 Work/Code/mobile visibility, delayed retention, export and targeted test-record cleanup remain; do not bulk re-import.
- Skills: KMS-01 original draft integrity/source reviewed, GPT candidate [1.0.1-rc.1](recovery/kimi/skills/github-source-audit/SKILL.md) awaiting Kimi review and owner approval; NOT installed/qualified. Then S1 fresh READONLY cases, S2 actual transfer/use and S3 maintenance/export. KMS-02 V20, KMS-03 TRL, KMS-04 CC, KMS-05 GPT↔Kimi handoff not yet authored/accepted; sequential development and independent testing, no automatic execution.
- KDR: 001–009 remain open in latest register; prioritize 006 isolation before execution, 001 Protect3 negative/positive + delayed blind retests, 005 TRL original bytes, 008 remote safety, 009 independent operation. 002 docs drift, 003 timezone evidence (not a confirmed Kimi error), 004 research methodology and 007 action/cross-surface evidence remain. Keep findings distinct from model errors. No closure by explanation alone.
- Capacity: latest supplied screenshot 24.11 11:34, 28.5% monthly / 51.41% 5h Code used; Extra Usage OFF. Mixed intervals include interrupted/restarted tasks and parallel work; not clean per-task costs. Continue monthly pilot, no annual Pro/Max decision yet.

### Work queue (single current pointer)

1. Now: G4.0-RC via Code Desktop phone route; in parallel receive KMS-01 revision review. Use existing Intel source checkout only, no repeat of full G4.0.
2. G4.0-W via Work mobile route; short Chat web/mobile parity and scoped cross-surface Memory checks. Record actual tools, before/after quota and failures.
3. Review/approve/install KMS-01 as READONLY candidate only, run independent tests; continue KMS-02–05 in order; not a prerequisite to source-only remote tests.
4. Prepare and separately authorize G4.1 executor, pass I0–I4; locate/privacy-check original TRL artifacts for approved transfer. No code execution until this gate.
5. G5 V20 then TRL then CC (prioritize V20/TRL), G6 independent blind/safety retests and G7 reciprocal handoff; complete required Skills/retention/transfer tests.
6. Mandatory GPT-OUTAGE, then G8 separately approved read-only operational observation, G9 full documented acceptance and subscription decision. If a mandatory gate cannot be verified, state BLOCKED/NOT_TESTED, not PASS.
7. Only after Stage II acceptance and required separate permissions: Stage III independent complete backup and genuine offline cold restore.

No arbitrary overall progress percentage: setup, theory, source review, execution and autonomy are not equally weighted. A completed source gate is not operational qualification. Current production status remains UNKNOWN; no new LIVE access, no deployment, no Merge.
