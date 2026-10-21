# V20_TradingSystem_M15 — V20-03 PARTIAL/HOLD

Публикация уже рассчитанного offline stress 2018–2022 для рассмотрения в Draft PR существующего репозитория. Replay, оптимизация, поиск параметров и новый расчёт сигналов при публикации не выполнялись. Roadmap строго **V20-01–V20-10**. V20-03 остаётся **PARTIAL/HOLD**, следующие этапы не запущены.

Основной [русский аналитический отчёт по ТЗ](V20-03/REPORT_RU.md) и [сохранённый подробный stress-отчёт](V20-03/STRESS_REPORT_RU.md) содержит методику, идентичности контрактов, CNY tick change, causal roll, разрезы, концентрацию, ограничения и 14 PASS / 4 FAIL. [Условия публикации](V20-03/PUBLICATION_RU.md) отличают новое размещение от прежних проверок replay. [Машинная приёмка расчёта](V20-03/ACCEPTANCE_V20_03.json) сохранена без изменений.

| Независимый счёт | Сделки основной выборки | C1 PF / net R / DD R | C2 PF / net R | STRICT PF / net R |
|---|---:|---|---|---|
| Shallow Pullback | 568 | 1.266 / +113.395 / 26.909 | 1.210 / +92.860 | 1.110 / +51.792 |
| OBV Pressure | 328 | 1.168 / +44.710 / 39.495 | 1.107 / +29.591 | 0.998 / −0.647 |
| Inside Day Release | 108 | 1.583 / +47.350 / 23.354 | 1.510 / +43.077 | 1.380 / +34.532 |
| Арифметическая сводка трёх счетов | 1004 | 1.266 / +205.454 / 58.766 | 1.206 / +165.528 | 1.099 / +85.676 |

**C1 — единственный основной сценарий рассмотрения; C2/STRICT сохранены справочно и не являются обязательным критерием GO/HOLD. Все PF условны.** C1/C2/STRICT — 1/2/4 тика на сторону, не фактические комиссии. DD относится к закрытым нормированным R, не RUB/MTM. Сводка не является единым исполняемым счётом. Ещё 12 наблюдаемо закрытых сделок исключены из основной статистики по фиксированному критерию разрывов; открытых позиций 0, forced close нет.

GLD отсутствует, CNY только с 21.04.2022, архив заканчивается 15.12.2022; квартальные Si/MIX/CNY — экономические прокси, не perpetual N4. Таймзона/агрегация экспортера и историческая идентичность каждого выпуска полностью не подтверждены. Полный N4 и независимый OOS не заявляются.

## Данные для рассмотрения

- [По стратегиям](V20-03/publication/STATISTICS_BY_STRATEGY.csv), [по годам](V20-03/publication/STATISTICS_BY_YEAR.csv), [по инструментам](V20-03/publication/STATISTICS_BY_INSTRUMENT.csv), [по месяцам](V20-03/publication/STATISTICS_MONTHLY.csv).
- [Все исходные статистические разрезы CSV](V20-03/results/STATISTICS.csv) и [JSON](V20-03/publication/STATISTICS_ALL.json): PF, net/gross R, DD, число сделок, wins, статус условности.
- [Закрытые сделки](V20-03/results/CLOSED_TRADES.csv), [все наблюдаемые выходы](V20-03/results/ALL_OBSERVED_CLOSED.csv), [исключённые](V20-03/results/CENSORED_CLOSED.csv), [входы](V20-03/results/ENTRIES.csv).
- [Концентрация](V20-03/results/CONCENTRATION.csv), [лучшие месяцы](V20-03/results/BEST_MONTHS.csv), [effective coverage](V20-03/results/EFFECTIVE_COVERAGE.csv), [roll decisions](V20-03/results/ROLL_DECISIONS.csv).
- [Карта контрактов](V20-03/CONTRACT_MAP.csv), [единственная frozen roll policy](V20-03/ROLL_POLICY_LOCKED_V1.md), [источники MOEX](V20-03/evidence/SOURCES_RU.md).
- [Ранее выполненная причинность](V20-03/verification/CAUSALITY.json), [повтор 18 файлов](V20-03/verification/REPEAT.json), [SHA256 исходной архивной поставки](V20-03/publication/ARCHIVE_FILE_INDEX.json).
- [Roadmap: ровно 10 этапов](docs/ROADMAP_RU.md), [tracker](docs/TASK_TRACKER.csv).

## Проверка публикации без replay

Из корня этой папки:

```bash
sha256sum -c PUBLICATION_MANIFEST_SHA256.txt
python V20-03/offline/verify_publication.py
```

Проверяется целостность опубликованных файлов, 18 неизменённых результатов, frozen source hashes, согласованность уже рассчитанных агрегатов, ограничения входов и отсутствие исходных свечей/ZIP. Скрипт не импортирует signal/replay modules и не читает исходные рыночные данные. Исторические журналы replay не являются новыми CI-проверками этой ветки.

В соответствии с корневым `AGENTS.md` исходные рыночные CSV, signal grids `.csv.gz` и ZIP **не помещаются в Git**. Оба оригинальных ZIP и полный offline-архив сохранены в прежней рабочей области вне репозитория. Для нового replay нужен полный архив во внешней рабочей папке; в этой задаче новый replay не требуется и не выполняется. Подробности — [README_RUN_RU.md](V20-03/README_RUN_RU.md).

Изменения ограничены этой новой папкой. H1/M15, FINAM, действующие Windows Tasks, корневые workflow/конфигурации и main не изменяются. Draft PR требует рассмотрения и не означает разрешения на merge или последующие этапы.
