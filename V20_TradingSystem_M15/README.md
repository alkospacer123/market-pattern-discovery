# V20_TradingSystem_M15 — V20-03: диагностика PF

Актуальный результат — [PF_DIAGNOSTIC_REPORT_RU.md](V20-03/comparison/PF_DIAGNOSTIC_REPORT_RU.md), [методологические эффекты](V20-03/comparison/METHODOLOGY_EFFECTS_RU.md) и [решение о разработке](V20-03/comparison/DEVELOPMENT_DECISION_RU.md). Работа в Draft PR #565 без merge. Roadmap **ровно V20-01–V20-08**, **V20-04 = разработка H1/M15**; денежный replay, GO/HOLD/NO-GO и Shadow не являются самостоятельными этапами.

По доступным данным рекомендуем вариант B: offline-разработка Shallow первой и Inside второй конфигурацией, OBV HOLD. Это заключение V20-03, не разрешение LIVE и не запуск V20-04. Статус полной сопоставимости PARTIAL; исходные 14 PASS / 4 FAIL не переписываются.

| Стратегия | PF C1 2023–2026 | PF C1 2018–2022 |
|---|---:|---:|
| Shallow Pullback | 1.911 | 1.266 |
| OBV Pressure | 1.718 | 1.168 |
| Inside Day Release | 2.265 | 1.583 |
| Арифметическая сводка трёх счетов | 1.874 | 1.266 |

Исполненные USD+индекс прокси: **1.823529 против 1.285412**. Это фильтрация полного журнала, не независимый двухинструментный replay. Частота выигрышей и средний выигрыш ниже; средний убыток немного меньше. Состав уменьшает описательный разрыв PF на 11.45%; тип фьючерса/режим/эффект отбора причинно не разделены.

Оригинальный поздний журнал 1589 и offline ZIP сейчас отсутствуют. Поздние разрезы рассчитаны одним ограниченным воспроизведением трёх frozen-стратегий на SHA256-идентичных исходных котировках; PF/net/counts/exit counts совпали, row parity с оригиналом NOT VERIFIED. Старые 1004+12 сделок и все 18 результатов сохранены побайтово. Quarterly M15 сейчас отсутствуют; старые траектории/рыночные режимы NOT VERIFIED.

- [Периоды/стратегии](V20-03/comparison/PERIOD_STRATEGY_COMPARISON.csv), [инструменты и ATR](V20-03/comparison/INSTRUMENT_COMPARISON.csv), [выходы/траектории](V20-03/comparison/TRADE_DISTRIBUTION.csv), [годовая устойчивость](V20-03/comparison/YEARLY_STABILITY.csv).
- [Проверки и источники](V20-03/comparison/VERIFICATION.json), [производный диагностический журнал](V20-03/comparison/DIAGNOSTIC_REPLAY_TRADES.csv), [расчёт](V20-03/comparison/build_diagnostics.py).
- [Предыдущий отчёт](V20-03/REPORT_RU.md), [сохранённый stress-результат](V20-03/STRESS_REPORT_RU.md), [условия публикации](V20-03/PUBLICATION_RU.md).
- [Roadmap из 8 этапов](docs/ROADMAP_RU.md), [tracker](docs/TASK_TRACKER.csv), [паспорт](docs/PROJECT_SPEC_RU.md).

`docs/CODEX_V20_03_DRAFT_PR_PUBLICATION_RU.md`, `evidence/archive_original/`, старые acceptance/verification и V20-02 — **исторические оригиналы**. Упоминания 10/12 этапов в них архивные и не определяют текущий roadmap.

Проверка публикации из папки проекта:

```bash
sha256sum -c PUBLICATION_MANIFEST_SHA256.txt
python V20-03/offline/verify_publication.py
```

Короткая проверка не выполняет replay. Генератор диагностики отдельно требует внешние исходные perpetual CSV; инструкция в его docstring. Source market data и ZIP не помещаются в Git по AGENTS.md. H1/M15, FINAM, токены, задачи, заявки, main и production не изменяются.
