# V20_TradingSystem_M15 — V20-04: три независимых робота

Актуальный результат — [PF_DIAGNOSTIC_REPORT_RU.md](V20-03/comparison/PF_DIAGNOSTIC_REPORT_RU.md), [методологические эффекты](V20-03/comparison/METHODOLOGY_EFFECTS_RU.md) и [решение о разработке](V20-03/comparison/DEVELOPMENT_DECISION_RU.md). V20-03 принят владельцем с сохранением PARTIAL-ограничений, PR #565 предназначен для разрешённого merge. Roadmap **ровно V20-01–V20-08**, **V20-04 = разработка H1/M15**; денежный replay, GO/HOLD/NO-GO и Shadow не являются самостоятельными этапами.

**Текущее решение владельца:** разработать все три — Shallow, OBV, Inside — на едином H1/M15 исполнительном каркасе. **V20-04 IN PROGRESS / OFFLINE ONLY.** Прежняя аналитическая рекомендация B сохранена в V20-03 как историческая оценка разной надёжности, но не ограничивает разработку OBV. LIVE и реальное брокерское исполнение запрещены до отдельного разрешения. См. [решение от 21.10.2026](docs/DECISION_V20_03_CLOSE_20261021_RU.md). Статус полной сопоставимости PARTIAL; исходные 14 PASS / 4 FAIL не переписываются.

| Стратегия | PF C1 2023–2026 | PF C1 2018–2022 |
|---|---:|---:|
| Shallow Pullback | 1.911 | 1.266 |
| OBV Pressure | 1.718 | 1.168 |
| Inside Day Release | 2.265 | 1.583 |
| Арифметическая сводка трёх счетов | 1.874 | 1.266 |

**Дополнение по котировкам:** найдена асимметрия gap/reset. Один необходимый диагностический late replay с существующим V1 дал PF Shallow **1.835**, OBV **1.630**, Inside **2.471**, общий **1.828** вместо 1.874; старый общий 1.266. Это отдельный диагностический набор, исходные сделки не заменены. Простая фильтрация 86 late gap-trades давала 1.691 и не измеряла полный reset.

Исполненные USD+индекс прокси: **1.823529 против 1.285412**. Это фильтрация полного журнала, не независимый двухинструментный replay. Частота выигрышей и средний выигрыш ниже; средний убыток немного меньше. Состав уменьшает описательный разрыв PF на 11.45%; тип фьючерса/режим/эффект отбора причинно не разделены.

Оригинальный поздний журнал 1589 и offline ZIP сейчас отсутствуют. Поздние разрезы рассчитаны одним ограниченным воспроизведением трёх frozen-стратегий на SHA256-идентичных исходных котировках; PF/net/counts/exit counts совпали, row parity с оригиналом NOT VERIFIED. Старые 1004+12 сделок и все 18 результатов сохранены побайтово. Пользователь предоставил оригинальный 2018-2022.zip: все 43 quarterly CSV совпали SHA256. Старые траектории и рыночные годы теперь проверены; все 1016 старых наблюдаемых model-выходов совпали с котировками. Причинное разделение режима/типа контракта остаётся NOT VERIFIED.

- [Периоды/стратегии](V20-03/comparison/PERIOD_STRATEGY_COMPARISON.csv), [инструменты и ATR](V20-03/comparison/INSTRUMENT_COMPARISON.csv), [выходы/траектории](V20-03/comparison/TRADE_DISTRIBUTION.csv), [годовая устойчивость](V20-03/comparison/YEARLY_STABILITY.csv).
- [Построчные траектории и V1 diagnostic trades](V20-03/comparison/QUOTE_PATH_DIAGNOSTICS.csv), [расчёт по котировкам](V20-03/comparison/quote_diagnostics.py).
- [Проверки и источники](V20-03/comparison/VERIFICATION.json), [производный диагностический журнал](V20-03/comparison/DIAGNOSTIC_REPLAY_TRADES.csv), [расчёт](V20-03/comparison/build_diagnostics.py).
- [Предыдущий отчёт](V20-03/REPORT_RU.md), [сохранённый stress-результат](V20-03/STRESS_REPORT_RU.md), [условия публикации](V20-03/PUBLICATION_RU.md).
- [Roadmap из 8 этапов](docs/ROADMAP_RU.md), [tracker](docs/TASK_TRACKER.csv), [паспорт](docs/PROJECT_SPEC_RU.md).

`docs/CODEX_V20_03_DRAFT_PR_PUBLICATION_RU.md`, `evidence/archive_original/`, старые acceptance/verification и V20-02 — **исторические оригиналы**. Упоминания 10/12 этапов в них архивные и не определяют текущий roadmap.

Проверка публикации из папки проекта:

```bash
sha256sum -c PUBLICATION_MANIFEST_SHA256.txt
python V20-03/offline/verify_publication.py
```

Короткая проверка не выполняет replay. Quote-генератор отдельно требует внешние исходные perpetual CSV и присланный quarterly ZIP; инструкция — V20-03/README_RUN_RU.md. Текущие диагностические проверки 24 PASS /1 FAIL /2 NOT VERIFIED: отсутствует оригинальный late reference ledger, не отделены чистый тип/период и PnL двухинструментного контрфакта. Source market data и ZIP не помещаются в Git по AGENTS.md. H1/M15, FINAM, токены, задачи, заявки, main и production не изменяются.
