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
