# Trading Systems — Roadmap (актуализирован 22.11.2026)

Порядок обязателен: **(I) безопасно упорядоченный GitHub → (II) Kimi Chat + Kimi Code → (III) независимый backup и настоящий cold restore**. MAIN ≠ INSTALLED ≠ LIVE ≠ RESEARCH ≠ ARCHIVE.

## I. Упорядоченный GitHub

- [x] [#583](https://github.com/alkospacer123/market-pattern-discovery/pull/583): из main удалены 11 594 проверенных исторических A/B/C+BBW paths с сохранением Git history.
- [x] [#585](https://github.com/alkospacer123/market-pattern-discovery/pull/585): Merge канонических README/AGENTS, трёх паспортов и dependency retention.
- [x] [#586](https://github.com/alkospacer123/market-pattern-discovery/pull/586): один пакет реальной уборки старой root платформы — 233 удаления / 6 изменений / 4 добавления, CI R7 7/7 + Windows CC03 + Main Admission SUCCESS на exact HEAD, protected trees и archive refs сохранены. Merge commit `4f118ee1cdeced15406136401faabe4fdc3bb847`.
- [ ] Принять проверенные post-R7 статусные документы и карту Kimi R1.2; не переписывать старые отчёты задним числом.
- [ ] Разобрать уникальное из Draft #581: только проверенные standalone read-only scanner/checkpoint tools, тесты и source provenance; **не Merge исторический 82-commit stack**, не запускать удаление H1/M15.
- [ ] Закрыть устаревшие #580/#581 только **после переноса уникальных материалов и проверки**; не удалять ветки/архивы без разрешения.
- [x] Проверена структура H1/M15/V20/CC/TRL и `audit_only` по точным Git tree SHA; [классификация retained research](recovery/RETAINED_RESEARCH_CLASSIFICATION_2026-11-22.md). Это **не** доказательство полной внешней dependency closure.
- [ ] Дальнейший перенос исторических файлов, включая 16 audit_only, только после отдельного доказательного gate и разрешения; пока **KEEP**.

## II. Полная адаптация Kimi

- [ ] Три отдельных логических knowledge projects V20/CC/TRL из **одного** `market-pattern-discovery/main`; роль H1/M15 как общих зависимостей, а не новых LIVE.
- [ ] Отдельное подключение **Kimi Code** с проверкой source/permissions/SHA, sandbox и offline-only тестами, без токенов FINAM.
- [ ] Практический экзамен R1.2–R1.4, совместная безопасная задача GPT ↔ Kimi, кодовый PR и peer-review/handoff; никакого автоматического Merge или LIVE.

## III. Автономный Recovery — только последним

- [ ] После всех GitHub/Kimi работ: полный версионированный backup V20, CC, TRL, provenance, оригинальных исследований, Git refs/PR/Issues/CI и приватных данных в безопасной форме на независимых носителях.
- [ ] Настоящий изолированный cold restore без Intel, основного SSD, GitHub и обеих ИИ с SHA, офлайн-тестами и операторским актом; горизонт сохранения 10–30 лет.

**Границы R7:** GitHub CI не доказательство FINAM/SLTP; historical archived 45 PASS/1 FAIL не исправлен, 3 крупных metadata пропущены; Git history не заменяет backup. [Current state](recovery/REPOSITORY_CURRENT_STATE.md).
