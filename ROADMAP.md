# Trading Systems — Roadmap / состояние на 22.11.2026 после R7

**Порядок:** (I) упорядоченный безопасный GitHub → (II) фактическая адаптация Kimi Chat **и отдельно** Kimi Code → (III) автономный backup и физический cold restore. **MAIN ≠ INSTALLED ≠ LIVE ≠ RESEARCH ≠ ARCHIVE**.

## I. Упорядоченный GitHub — CLOSEOUT

- [x] [#583](https://github.com/alkospacer123/market-pattern-discovery/pull/583): из рабочего дерева выведено 11 594 исторических A/B/C + BBW файла с сохранением Git history.
- [x] [#585](https://github.com/alkospacer123/market-pattern-discovery/pull/585), [#586](https://github.com/alkospacer123/market-pattern-discovery/pull/586): канонические паспорта и генеральная уборка root legacy (233 удалённых файла), защищённые проекты и архив сохранены. Зафиксирован исторический 45 PASS / 1 FAIL, не подменён зелёным тестом.
- [x] [#587](https://github.com/alkospacer123/market-pattern-discovery/pull/587) MERGED `8a1c6618f8d3c9f33de9de6cb3f6efae13fe29f0`: Kimi R1.2 и классификация H1/M15 / retained studies.
- [x] [#588](https://github.com/alkospacer123/market-pattern-discovery/pull/588) MERGED `bb8c46c1db89ca2b5311f22c755bb4e51ce8f7d6`: Git scanner/checkpoint, synthetic tests 10/10. **Не реальный offsite backup / cold restore**.
- [x] Старые Draft [#580](https://github.com/alkospacer123/market-pattern-discovery/pull/580), [#581](https://github.com/alkospacer123/market-pattern-discovery/pull/581) закрыты **без Merge**, исходные branches и unique source provenance сохранены.
- [x] H1/M15/V20/ControlCenter/TRL сохранены как исходные проекты, необходимые зависимости и research. Проверенные исходные Git trees по [retained register](recovery/RETAINED_RESEARCH_CLASSIFICATION_2026-11-22.md); никакого удаления из этих пяти каталогов.
- [x] Завершающий R7 пакет: **16 файлов исторического H1 STOP/TICK GRID** выведены из рабочего дерева после byte-exact Git archive parity, ограниченного dependency/link CI и явного разрешения владельца. [Архивный паспорт](recovery/H1_STOP_TICK_GRID_ARCHIVE_20261012.md). Исторический audit код не был LIVE.
- [ ] Только при необходимости будущего функционального полного replay: проверить неизвестных внешних consumers и три больших ранее пропущенных metadata файла. **Это остаточные документированные ограничения, а не право удалять ещё что-либо.**

## II. Полная адаптация Kimi — IN PROGRESS

- [ ] [PR #589](https://github.com/alkospacer123/market-pattern-discovery/pull/589) — source-pinned входы для трёх **логических** Kimi projects (V20, CC, TRL), экзамен и GPT↔Kimi handoff. Принятие документации ≠ создание проектов в Kimi.
- [ ] Фактически создать и настроить три Kimi Chat knowledge projects **из одного GitHub**, проверить источники/SHA и ответы, ограничения доступов и отсутствие секретов.
- [ ] Отдельно подключить **Kimi Code**, проверить права, pinned Git HEAD/blob SHA, запуск синтетических/offline тестов в sandbox и отказ от LIVE.
- [ ] Провести независимый экзамен V20 R088 + 9-patch, CC-08, TRL R089/R097/R098; затем совместный ограниченный Draft PR, GPT review, Kimi corrections, handoff и решение оператора. Никакого auto Merge, deploy, re-arm.

## III. Независимый Recovery — ONLY AFTER KIMI

- [ ] Новый автономный сохранённый комплект V20, CC, TRL, оригинальных исследований/ZIP/XLSX, данных OHLCV, Git history/refs/PR/Issues/CI/provenance, приватных пользовательских сведений через безопасные независимые носители.
- [ ] Настоящий изолированный **cold restore вне Intel, основного SSD, GitHub и обоих ИИ**; SHA, воспроизводимость и offline тесты, без реальной торговли. Горизонт 10–30 лет.

**Приёмка:** GitHub CI, Git refs и ZIP SHA сами по себе **не** доказывают LIVE, FINAM SLTP, Kimi access или холодное восстановление. Фактически не проверенное = UNKNOWN.
